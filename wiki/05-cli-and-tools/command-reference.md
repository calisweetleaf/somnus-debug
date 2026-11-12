# Command reference

This page is the full reference for every command-line surface in somnus-debug 0.1.0: the verbatim `--help` text, what the command does, what it prints, what it writes to disk, and how it exits. Flags are cross-indexed in [options-and-flags](options-and-flags.md), output formats in [input-output-contracts](input-output-contracts.md), and exit codes in [exit-codes](exit-codes.md).

Evidence base: help text was captured twice and compared byte for byte. Lane D captured it from an installed venv ([help-surfaces-raw.txt](../_evidence/agent-findings/lane-d-cli-tests/help-surfaces-raw.txt)). This page's writer re-captured all 13 dispatcher surfaces from the source tree with `PYTHONPATH=<repo>/src python3 -m somnus_debug.cli ...` (cwd `/tmp/w2/help`). All 13 exited 0 and every body was identical to the installed copy once the `SyntaxWarning` lines were removed. [VERIFIED] See [verification-results](../11-verification/verification-results.md#w2-runs) run W2-01.

## Surfaces at a glance

This section lists every way to invoke a tool and which backend function each one reaches.

| Invocation | Backend function | How argv reaches it |
|---|---|---|
| `somnus-debug <cmd> ...` | `somnus_debug.cli:main` -> `_run_subcommand` | Sets `sys.argv = ["somnus-debug <cmd>", *rest]`. Calls `entry(list(rest))`, except `pycache-clean`, which is called with no argument and reads `sys.argv` |
| `somnus-doctor ...` | `somnus_debug.doctor.core:main` | `sys.argv[1:]` |
| `somnus-structure ...` | `somnus_debug.structure.core:main` | `sys.argv[1:]` |
| `somnus-pycache-clean ...` | `somnus_debug.pycache_cleaner.core:main` | `argparse` reads `sys.argv`; returns `None` |
| no console script | `somnus_debug.test_harness.scaffold:main` | Reached as `somnus-debug init-test-harness` or `python -m somnus_debug.test_harness.scaffold`. `prog` is hard-coded as `somnus-debug init-test-harness` either way |
| `python -m somnus_debug.cli ...` | same as `somnus-debug` | the only `-m` form for the dispatcher. `python -m somnus_debug` has no `__main__` and exits 1 |

[SOURCE-CONFIRMED] `src/somnus_debug/cli.py:85-104`, `pyproject.toml` `[project.scripts]`, `src/somnus_debug/test_harness/scaffold.py:91-93`. [VERIFIED] The installed venv has exactly four `somnus-*` scripts and no `somnus-init-test-harness` (W2-02; lane D [install-vs-source.md](../_evidence/agent-findings/lane-d-cli-tests/install-vs-source.md) section 1). The `python -m somnus_debug` failure is lane D C04.

**Dispatcher vs standalone.** Each pair runs the same function. Help bodies differ only in the `usage:` program name, and every pair lane D tried had matching exit codes. [VERIFIED] [command-reference.md](../_evidence/agent-findings/lane-d-cli-tests/command-reference.md) section 0.

The one real difference is that the dispatcher imports all four tools when it loads (`src/somnus_debug/cli.py:55-58`). That has two consequences:

- `somnus-debug doctor` and `somnus-debug structure` fail without PyYAML (exit 1, `ModuleNotFoundError: No module named 'yaml'`).
- Any `somnus-debug` subcommand can print the pycache cleaner's `SyntaxWarning` from `pycache_cleaner/core.py:64`. The warning appears when the module is compiled without a cached `.pyc`, for example from source with `PYTHONDONTWRITEBYTECODE=1`.

The direct module forms `python -m somnus_debug.doctor.core` and `python -m somnus_debug.structure.core` run under a PyYAML-less Python 3.13 (both exit 0, with a runpy `RuntimeWarning`). [VERIFIED] W2-05. See [D-13](../DISCOVERY-LEDGER.md#d-13).

## somnus-debug (dispatcher)

This section documents the router that fronts all four tools.

Verbatim (no arguments, `-h`, and `--help` print the same text):

```text
somnus-debug 0.1.0 -- Somnus Sovereign Systems Python developer toolkit

Usage:
    somnus-debug <command> [command args...]

Commands:
    doctor              Production-readiness diagnostics (AST-based).
    structure            Class/definition index for a single Python file.
    pycache-clean        Remove __pycache__/*.pyc/*.pyo across directory trees.
    init-test-harness    Scaffold the CONTRACT.md single-test harness into a repo.

Each command owns its own --help; run e.g. `somnus-debug doctor --help`.
Every command is also installed as its own script (somnus-doctor,
somnus-structure, somnus-pycache-clean).
```

Behavior:

- With no arguments, `-h`, or `--help` as the first token, it prints the text above to stdout and exits 0. Anything after `--help` is ignored. [VERIFIED] lane D C07.
- `-V` or `--version` as the first token prints `0.1.0` and exits 0. [VERIFIED] W2-01.
- An unknown command prints `somnus-debug: unknown command 'x'` and the help text to **stderr** and exits 2. [VERIFIED] lane D C01; `src/somnus_debug/cli.py:119-122`.
- A known command is routed to its tool. A `SystemExit` carrying an int becomes that exit code. A non-int `SystemExit` code becomes 1, a non-int return value becomes 0, and any other exception escapes as a traceback (exit 1). [SOURCE-CONFIRMED] `src/somnus_debug/cli.py:99-104`.
- It writes nothing to disk itself.

Programmatic form: `somnus_debug.cli.main(argv)` returns an int and restores `sys.argv` afterwards. [VERIFIED] W2-20 (`cli.main(["doctor","scan",...])` returned 1).

## doctor

This section covers the production-readiness scanner and its five subcommands.

`somnus-debug doctor --help`, verbatim:

```text
usage: somnus-debug doctor [-h]
                           {scan,init-config,history,rollback,self-check} ...

Python Production Doctor - production readiness diagnostics

positional arguments:
  {scan,init-config,history,rollback,self-check}
    scan                scan a Python project
    init-config         write default YAML configuration
    history             show scan history
    rollback            restore a previous report as latest
    self-check          scan the directory containing this doctor

options:
  -h, --help            show this help message and exit
```

The standalone form begins `usage: somnus-doctor [-h] {scan,init-config,history,rollback,self-check} ...`. [VERIFIED] W2-02.

### Behavior common to every doctor subcommand

This subsection lists what happens on every doctor invocation, before any subcommand runs.

1. **A log file is opened in the current working directory.** `setup_logging` runs before argument parsing and opens `production_doctor.log` in cwd, in append mode, with `logging.basicConfig(..., force=True)`. This happens on every call, including `--help` and argparse errors. The `force=True` also replaces any logging handlers the host process had already installed. [SOURCE-CONFIRMED] `src/somnus_debug/doctor/core.py:2179-2181`, `:2186`. [VERIFIED] W2-01 (help capture left a 0-byte `production_doctor.log` in `/tmp/w2/help`); W2-20 (an in-process host `StreamHandler` was replaced by a `FileHandler`). See [D-10](../DISCOVERY-LEDGER.md#d-10) and [D-11](../DISCOVERY-LEDGER.md#d-11).
2. **The log stays empty on success.** Only two calls in `main` write to it: the `DoctorError` render (exit 4, ERROR) and the unclassified-failure traceback (exit 5, CRITICAL). Across runs the file accumulates entries. [SOURCE-CONFIRMED] `:2192`, `:2196`. [VERIFIED] W2-08: two exit-4 runs appended two ERROR blocks to the same log.
3. **Legacy argv is normalized** (`normalize_argv`, `:2165-2176`):
   - no arguments -> `scan .`
   - `-h`/`--help` -> unchanged
   - a known subcommand -> unchanged
   - a first token starting with `-` -> `scan . <tokens>`
   - anything else -> `scan <tokens>`

   So `somnus-doctor p`, `somnus-doctor --no-state`, and `somnus-debug doctor p` are all scans. `doctor --version` becomes `scan . --version` and fails with argparse exit 2. [VERIFIED] lane D D35-D37, C02.
4. **Error tiers.**
   - `DoctorError` subclasses print a three-part render (`Doctor failure: ...`, `Remediation: ...`, `Context: {json}`) to stderr and exit 4.
   - `OSError`, `RuntimeError`, `TypeError`, `ValueError`, and `sqlite3.Error` print `Unclassified runtime failure: <Type>: <msg>` and exit 5.
   - Any other exception type escapes as a traceback.

   [SOURCE-CONFIRMED] `:2189-2201`.

### doctor scan

This subsection documents the main analysis command.

```text
usage: somnus-debug doctor scan [-h] [-c CONFIG] [-o OUTPUT]
                                [--json-output JSON_OUTPUT] [--no-state] [-v]
                                [project_root]

positional arguments:
  project_root          project root directory to scan

options:
  -h, --help            show this help message and exit
  -c CONFIG, --config CONFIG
                        YAML or JSON configuration path
  -o OUTPUT, --output OUTPUT
                        markdown output path
  --json-output JSON_OUTPUT
                        JSON output path
  --no-state            write reports without SQLite state tracking
  -v, --verbose         enable debug logging
```

What it does, in order (`run_scan`, `src/somnus_debug/doctor/core.py:2061-2093`):

1. **Loads config.** It reads `-c` if given, otherwise the in-code defaults. It **never** auto-discovers `python_doctor.yaml` in the project root or in cwd. [VERIFIED] lane D D27/D27b. See [D-02](../DISCOVERY-LEDGER.md#d-02).
2. **Opens SQLite state** under `<project_root>/<state_dir>` unless `--no-state` is given. If the database cannot be opened, it prints `Warning: local SQLite state is unavailable; continuing without history or rollback (...)` to stderr and carries on without state (`:2066-2075`). [VERIFIED] lane D D39.
3. **Scans.** It discovers files by `include_patterns`/`ignore_patterns`, analyzes each file's AST (the source is never imported), resolves imports, builds the dependency graph, and scores the result.
4. **Writes reports and prints the summary block** (see below).
5. **Exits by the severity gate** `severity_exit_level` (see [exit-codes](exit-codes.md)).

stdout contract (verbatim from a stateful run, W2-11):

```text
Scan complete: files=3, issues=7, critical=0, serious=2
Markdown report: /tmp/w2/qs/myproj/production_doctor_report.md
JSON report: /tmp/w2/qs/myproj/production_doctor_report.json
State latest markdown: /tmp/w2/qs/myproj/.python_doctor/reports/latest.md
Run ID: 20261112T003638Z
```

With `--no-state`, only the first three lines are printed. The first line is the stable machine hook. The fieldkit's `onboard.py` treats a run that lacks it as a failure (lane F [fieldkit.md](../_evidence/agent-findings/lane-f-ext/fieldkit.md) OB-2).

Artifacts written:

| Condition | Files |
|---|---|
| always | `production_doctor.log` in **cwd** (0 bytes on success) |
| no `-o` | `<project_root>/production_doctor_report.md` |
| no `--json-output` | the JSON goes next to the Markdown with the suffix swapped: `<md path>.with_suffix(".json")` |
| state on (the default) | `<project_root>/.python_doctor/state.sqlite3`, `.python_doctor/reports/<RUN_ID>/production_doctor_report.{md,json}`, `.python_doctor/reports/latest.{md,json}` |
| `-o X` | Markdown at `X`, parent directories created |

[SOURCE-CONFIRMED] `StateStore.report_paths`, `src/somnus_debug/doctor/core.py:1953-1960`. [VERIFIED] W2-10 (`--no-state`: exactly `production_doctor.log` plus the two root reports), W2-11 (stateful: plus five `.python_doctor/` files).

Pitfalls:

- `-o report.json` without `--json-output` writes the Markdown to `report.json` and then overwrites it with JSON, because the JSON path is derived as `report.json`. [VERIFIED] W2-23: both stdout lines named `/tmp/w2/probe/report.json` and the file holds JSON. See [D-25](../DISCOVERY-LEDGER.md#d-25).
- `-v` is accepted but has no effect. `setup_logging` only checks for the literal string `--verbose` (`:2186`). `--verbose` does set the root logger to DEBUG, but `doctor/core.py` contains no `logger.debug` calls, so nothing more is logged. [VERIFIED] W2-07: the log was 0 bytes with no flag, with `-v`, and with `--verbose`.
- Same-second scans share a run ID, and the second silently replaces the first in history (`INSERT OR REPLACE`, `:1975`). [VERIFIED] W2-17: two back-to-back scans both printed `Run ID: 20261112T003816Z`, and the `runs` table held 1 row. See [D-08](../DISCOVERY-LEDGER.md#d-08).
- The reports land in the scanned project root by default. A project under version control will see them as untracked files, unless its ignore file covers `*_report.md`/`*_report.json` (this repo's `.gitignore` does).

### doctor init-config

This subsection documents the default-config writer.

```text
usage: somnus-debug doctor init-config [-h] [-o OUTPUT] [--force]

options:
  -h, --help            show this help message and exit
  -o OUTPUT, --output OUTPUT
                        configuration output path
  --force               replace existing configuration
```

- It writes `ConfigManager.default_yaml()` to `-o`, which defaults to `python_doctor.yaml` **in cwd**, and prints `Wrote default configuration: <abs path>`. [VERIFIED] W2-13.
- If the target exists and `--force` is not given, it prints `Configuration file already exists.` with remediation `Use --force to replace it.` and exits 4. [VERIFIED] lane D D23/D24.
- It does not make the scan use the file. You must pass `-c <file>` to `scan`. [VERIFIED] lane B E1/E2 ([configuration-findings.md](../_evidence/agent-findings/lane-b-config/configuration-findings.md) section 1).

The full default YAML (99 lines) is reproduced in [first-project](../03-getting-started/first-project.md#step-2-generate-a-config-and-point-the-scan-at-it).

### doctor history

This subsection documents the run-history listing.

```text
usage: somnus-debug doctor history [-h] [-c CONFIG] [--limit LIMIT]
                                   [project_root]

positional arguments:
  project_root          project root directory

options:
  -h, --help            show this help message and exit
  -c CONFIG, --config CONFIG
                        YAML or JSON configuration path
  --limit LIMIT         maximum records to show
```

- It prints `Run history:` followed by two lines per run, newest first, up to `--limit` runs (default 10). [VERIFIED] W2-14:

  ```text
  Run history:
  - 20261112T003759Z | <completed_at> | files=3 | issues=8 | critical=0 | serious=3
    markdown=/tmp/w2/fp/calc/.python_doctor/reports/20261112T003759Z/production_doctor_report.md
    json=/tmp/w2/fp/calc/.python_doctor/reports/20261112T003759Z/production_doctor_report.json
  ```

  `<completed_at>` is stored as ISO-8601 UTC with microseconds and a `Z` suffix (for example `2026-11-12T00:36:08.553690Z`; checked with `od -c` on a report file, W2-12). The sandbox's display layer rewrites such strings into a local "Wed 2026-11-11 6:36 PM CST" form. That is a sandbox artifact, not doctor behavior.
- With no runs it prints `No recorded runs found.` and exits 0, and it **creates** `<root>/.python_doctor/state.sqlite3` as a side effect. [VERIFIED] lane D D12.
- If the database cannot be opened, it exits 4. [VERIFIED] lane D D40.
- The state location comes from `state_dir` in `-c`. Pass the same `-c` you scanned with, or history looks in `.python_doctor/`.

### doctor rollback

This subsection documents the latest-alias restore.

```text
usage: somnus-debug doctor rollback [-h] --run-id RUN_ID [-c CONFIG]
                                    [project_root]

positional arguments:
  project_root          project root directory

options:
  -h, --help            show this help message and exit
  --run-id RUN_ID       run identifier to restore
  -c CONFIG, --config CONFIG
                        YAML or JSON configuration path
```

- It copies the stored run's reports over `.python_doctor/reports/latest.{md,json}`, repoints the `latest` alias, and prints three lines. [VERIFIED] W2-16:

  ```text
  Rolled latest report state back to run 20261112T003752Z.
  Markdown report: /tmp/w2/fp/calc/.python_doctor/reports/20261112T003752Z/production_doctor_report.md
  JSON report: /tmp/w2/fp/calc/.python_doctor/reports/20261112T003752Z/production_doctor_report.json
  ```

- It does **not** touch `<project_root>/production_doctor_report.*`. After the rollback, `latest.json` had run ID `20261112T003752Z`, while the root report still had `20261112T003759Z`. [VERIFIED] W2-16. See [D-09](../DISCOVERY-LEDGER.md#d-09).
- The next stateful scan computes `state_delta` against the rolled-back run's file hashes. [VERIFIED] lane F C3g ([compositions.md](../_evidence/agent-findings/lane-f-ext/compositions.md)).
- An unknown ID prints `Doctor failure: Run ID does not exist in state history.` and exits 4. A missing `--run-id` is an argparse error, exit 2. [VERIFIED] W2-16; lane D D11.
- Source files are never changed.

### doctor self-check

This subsection documents the doctor's scan of its own package directory.

```text
usage: somnus-debug doctor self-check [-h] [-c CONFIG] [-o OUTPUT]
                                      [--json-output JSON_OUTPUT] [--no-state]

options:
  -h, --help            show this help message and exit
  -c CONFIG, --config CONFIG
                        YAML or JSON configuration path
  -o OUTPUT, --output OUTPUT
                        markdown output path
  --json-output JSON_OUTPUT
                        JSON output path
  --no-state            write reports without SQLite state tracking
```

- It scans `Path(doctor/core.py).parent`, which is the `doctor/` package directory only: 2 files. [SOURCE-CONFIRMED] `src/somnus_debug/doctor/core.py:2123-2127`.
- By default it writes `self_check_report.{md,json}` **and** `.python_doctor/` state into that directory. For an installed package, that is site-packages. [VERIFIED] lane D D14. With `-o`/`--json-output` plus `--no-state`, nothing is written to the package directory (lane D D15).
- On a read-only package directory, it warns about state and then fails with exit 4 unless `-o` is given. [VERIFIED] lane B ([configuration-findings.md](../_evidence/agent-findings/lane-b-config/configuration-findings.md) finding 11).
- On itself it reports `files=2 issues=78 critical=0 serious=17` and exits 1 under the default gate. [VERIFIED] lane D D14.
- It has no `project_root` and no `-v`.

## structure

This section documents the single-file class and definition indexer.

```text
usage: somnus-debug structure [-h] [-o OUTPUT | --update-doc PATH]
                              [--no-line-numbers]
                              [--source-label SOURCE_LABEL]
                              [--no-module-functions]
                              source

Index Python classes and their definitions without executing the module.

positional arguments:
  source                Python source file to analyze

options:
  -h, --help            show this help message and exit
  -o OUTPUT, --output OUTPUT
                        Write the generated index to this path
  --update-doc PATH     Regenerate an existing documentation/index file at
                        PATH
  --no-line-numbers     Omit source line spans from headings and definition
                        entries
  --source-label SOURCE_LABEL
                        Name shown in the generated heading instead of the
                        input filename
  --no-module-functions
                        Only emit classes and their methods
```

Behavior:

- It reads `source` as UTF-8, parses it with `ast.parse(..., type_comments=True)` (`src/somnus_debug/structure/core.py:210`), and renders a Markdown index.
- Without `-o`/`--update-doc`, the index goes to stdout. With either one, the file is written, parent directories are created, and **nothing is printed**. [VERIFIED] W2-22. The README quickstart shows a `written to CORE_INDEX.md` line that the code never prints (`src/somnus_debug/structure/core.py:337-343`).
- `--update-doc` creates the file even if it does not exist. `-o` and `--update-doc` are mutually exclusive (exit 2). [VERIFIED] lane D S12, S13.
- With `--no-module-functions`, module functions are left out of the body but are still counted in the `Definitions emitted` header line. [VERIFIED] lane D S10.

Real output on a three-function file (W2-15, exit 0):

```text
# Class Index for `core.py`

Generated by `analyze_python_structure.py` using Python's AST; the source is never imported or executed.

- Class declarations: 0 (0 top-level, 0 nested)
- Definitions emitted (module-level functions and class methods): 3

_No classes found._

## Module-level functions

- `def add(a: int, b: int) -> int:` (lines 6-8)
  - Return the sum of a and b.
- `def parse_count(text: str) -> int:` (lines 11-17)
  - Parse a count from text, falling back to zero.
- `def export_report(values: list[int]) -> str:` (lines 20-23)
  - Serialize values for a report.
```

The `Generated by analyze_python_structure.py` line is fixed text. It names the old root script even under `somnus-debug structure`.

Failure modes:

| Input | Result | Evidence |
|---|---|---|
| any file with a comment line shaped like a type comment, for example the `#     type: "source-code"` line in every `# somnus:metadata:v2` header | `error: invalid syntax (<file>, line N)`, exit 2 | [VERIFIED] W2-15: stamped copy, line 9. See [D-01](../DISCOVERY-LEDGER.md#d-01) |
| missing file, a directory, a real syntax error | `error: ...`, exit 2 | [VERIFIED] lane D S14, S15, S17 |
| non-UTF-8 file | **uncaught `UnicodeDecodeError` traceback, exit 1**. The handler only catches `OSError` and `SyntaxError` (`:333`) | [VERIFIED] W2-09 (new in this wave) |
| argparse error | exit 2 | [VERIFIED] lane D S13, S16 |

The root duplicate `analyze_python_structure.py` parses without `type_comments` and indexes stamped files (exit 0). [VERIFIED] W2-15.

## pycache-clean

This section documents the bytecode-cache remover.

```text
usage: somnus-debug pycache-clean [-h] [--config CONFIG] [--dry-run]
                                  [--verbose] [--max-depth MAX_DEPTH]
                                  [--follow-symlinks]

Remove Python bytecode caches across directory trees.

options:
  -h, --help            show this help message and exit
  --config CONFIG       Path to YAML configuration file (default: config.yaml)
  --dry-run             Perform a dry run without deleting anything
  --verbose             Enable verbose logging output
  --max-depth MAX_DEPTH
                        Maximum recursion depth (overrides config)
  --follow-symlinks     Follow symbolic links during traversal
```

Behavior:

- **There is no path argument.** Roots come only from `roots:` in the YAML config. The config defaults to `./config.yaml` relative to cwd. A missing config prints `Configuration file not found: <abs>` to stderr and exits 1. [SOURCE-CONFIRMED] `src/somnus_debug/pycache_cleaner/core.py:350-355`. [VERIFIED] lane D P04.
- It walks each root, deleting `__pycache__/` directories and loose `*.pyc`/`*.pyo` files. It skips directories whose **basename** matches an `exclude` entry.
- CLI flags can only switch settings on: `--dry-run`, `--verbose`, and `--follow-symlinks` force True, and `--max-depth` overrides the config value (`:356-364`).
- Logs go to **stdout**, and also to `log_file` if configured (append mode).
- **Dry-run wording matches a real run.** `--dry-run --verbose` prints `Removed directory ...`/`Removed file ...` and `Summary: deleted N directories, M files`, even though nothing is deleted. Only the `dry_run=True` header tells the two apart. [VERIFIED] W2-18: after the dry run all four files were still on disk; the real run then removed `pkg/__pycache__` and `pkg/loose.pyc` and kept `node_modules/x/__pycache__` (excluded) and `keep.py`.

Real dry-run output (W2-18, timestamps stripped, exit 0):

```text
[INFO] Starting pycache cleaner (dry_run=True)
[INFO] Scanning root: /tmp/w2/pc/tree
[DEBUG] Skipping excluded directory: /tmp/w2/pc/tree/node_modules
[DEBUG] Deleting directory: /tmp/w2/pc/tree/pkg/__pycache__ (0.00 MiB)
[INFO] Removed directory /tmp/w2/pc/tree/pkg/__pycache__
[DEBUG] Deleting file: /tmp/w2/pc/tree/pkg/loose.pyc (0.00 KiB)
[INFO] Removed file /tmp/w2/pc/tree/pkg/loose.pyc
[INFO] Summary: deleted 1 directories, 1 files; freed 0.00 MiB
```

Failure modes and hazards:

- A missing root logs `[ERROR] Root path does not exist...` and still exits 0. [VERIFIED] lane D P01.
- Malformed YAML or a top-level list produces an uncaught traceback, exit 1. `roots: []` produces a logged traceback, exit 1. [VERIFIED] lane D P05-P07.
- An unknown config key triggers `logging.warning` before logging is set up. That silences all later INFO/DEBUG output and leaves `log_file` empty, while files are still deleted. [VERIFIED] lane D P09; lane B P10.
- Values are not type-checked:
  - `dry_run: no` is YAML false and runs **live**.
  - `dry_run: "false"` is a non-empty string, so it is truthy and the run is dry.
  - `roots: tree` (a scalar) is iterated one character at a time.

  [VERIFIED] lane B ([configuration-findings.md](../_evidence/agent-findings/lane-b-config/configuration-findings.md) finding 9). See [D-14](../DISCOVERY-LEDGER.md#d-14).
- The module docstring claims Windows long-path support (`:64`). No code branches on `os.name` or adds `\\?\` prefixes (grep over the module finds only the docstring). [SOURCE-CONFIRMED]
- `--follow-symlinks` with a symlink loop has not been exercised. [UNVERIFIED]

Never point it at a real tree you care about without `--dry-run` first.

## init-test-harness

This section documents the test-harness scaffolder.

```text
usage: somnus-debug init-test-harness [-h] [--force] [--no-contract] [target]

Copy the CONTRACT.md single-test harness (run_test.py) into a target
repository.

positional arguments:
  target         Directory to write run_test.py (and CONTRACT.md) into
                 (default: current directory)

options:
  -h, --help     show this help message and exit
  --force        Overwrite existing files at the destination
  --no-contract  Only write run_test.py; skip copying CONTRACT.md alongside it
```

Behavior:

- It creates `target` if needed, writes `run_test.py` (and `CONTRACT.md` unless `--no-contract`) from package data, prints `wrote <abs path>` per file, then prints a `Next: edit TEST_NAME and execute_test() ...` hint. Exit 0. [VERIFIED] W2-19.
- If **any** destination exists, it prints `error: refusing to overwrite existing file(s) without --force: ...`, writes nothing, and exits 1. A target that is an existing file also exits 1. [VERIFIED] lane D H02, H05, H07; `src/somnus_debug/test_harness/scaffold.py:72-78`, `:114-118`.
- Both scaffolded files carry the template's own provenance header and artifact URN, so every target repo inherits the same IDs. [VERIFIED] lane D section 5.

**Placement trap.** The scaffolded `run_test.py` defaults `PROJECT_ROOT` to the parent of the directory containing it (`src/somnus_debug/test_harness/templates/run_test.py:749`). Scaffolding at a repo root, which is what the default target `.` and `docs/MANUAL.md:296-297` do, therefore makes artifacts land in `<repo>/../test-runs/`, outside the repo. [VERIFIED] W2-19: scaffolded at `/tmp/w2/hs/myproj`, artifacts went to `/tmp/w2/hs/test-runs/`. Scaffold into a subdirectory such as `tools/`, or set `PROJECT_ROOT`. See [D-15](../DISCOVERY-LEDGER.md#d-15).

## Scaffolded run_test.py (template)

This section documents the program that `init-test-harness` writes. It is not a package command.

- It has **no argument parser**. `python3 run_test.py --help` runs the test. [VERIFIED] lane D H09.
- Configuration is two environment variables:
  - `PROJECT_ROOT` (default: parent of the file's directory)
  - `SINGLE_TEST_OUTPUT_DIR` (default: `<project_root>/test-runs/`)

  [SOURCE-CONFIRMED] `templates/run_test.py:186-193`, `:590`, `:749`.
- The shipped `execute_test` is a project-specific Golden Path / `cargo` test. It FAILs unedited in any other repo (exit 1). [VERIFIED] W2-19.
- Human-readable logs go to stderr. A final JSON summary `{run_id, test_name, verdict, elapsed_s, artifacts{manifest, report, log}}` goes to stdout. Artifacts are written to `<output>/<RUN_ID>/{manifest.json, report.md, test.log}`. Exit 0 on PASS, 1 on FAIL. [VERIFIED] W2-19 (FAIL exit 1 unedited; PASS exit 0 after replacing `execute_test`).

## Fieldkit scripts (skills/somnus-debug-fieldkit/scripts/)

This section gives the verbatim help of the three agent-side scripts that ship in the repo but not in the wheel.

`python3 scripts/selftest.py --help` (exit 0, W2-24):

```text
usage: selftest.py [-h] [--python PYTHON]

Contract test: prove the installed somnus-debug still behaves the way this
skill says.

options:
  -h, --help       show this help message and exit
  --python PYTHON  interpreter with somnus-debug installed (runs python -m
                   somnus_debug.cli)
```

`python3 scripts/onboard.py --help` (exit 0, W2-24):

```text
usage: onboard.py [-h] [--apply] [--baseline] [--new-config] [--python PYTHON]
                  [repo]

Onboard a codebase onto somnus-debug with a verified, project-local profile.

positional arguments:
  repo             repository root (default: cwd)

options:
  -h, --help       show this help message and exit
  --apply          write .somnus-debug/ files that do not exist yet
  --baseline       record a stateful baseline scan into .somnus-debug/runs/
  --new-config     generate .somnus-debug/python_doctor.yaml even if a root
                   config exists
  --python PYTHON  interpreter that has somnus-debug installed (default:
                   project venv, then PATH)
```

`python3 scripts/delta.py --help` (exit 0, W2-24):

```text
usage: delta.py [-h] [--dispositions DISPOSITIONS] [--root ROOT] [--json]
                baseline latest

Compare two somnus-debug doctor JSON reports and gate on regressions.

positional arguments:
  baseline
  latest

options:
  -h, --help            show this help message and exit
  --dispositions DISPOSITIONS
                        JSON list of reviewed findings (category, file,
                        symbol?, reason)
  --root ROOT           project root for coverage checks (default: latest
                        report's project_root)
  --json                emit JSON instead of Markdown
```

Their behavior and exit codes (selftest 0/1/3; onboard 0/1/2/3; delta 0/1/2/3) are covered in [exit-codes](exit-codes.md#fieldkit-scripts) and in lane F [fieldkit.md](../_evidence/agent-findings/lane-f-ext/fieldkit.md).

## Root-level duplicate scripts

This section notes the pre-packaging copies at the repo root, which are not installed.

`python_production_doctor.py`, `analyze_python_structure.py`, `pycache_cleaner.py`, and `run_test.py` print the same help as their packaged counterparts, apart from the program name. They are not byte-equivalent in behavior:

- The root structure script indexes stamped files.
- The root doctor lacks the SQLite-unavailable fallback (`python_production_doctor.py:2066`).
- Root `run_test.py --help` executes the cargo test.

[VERIFIED] lane D [install-vs-source.md](../_evidence/agent-findings/lane-d-cli-tests/install-vs-source.md) sections 4 and 7. See [package-layout](../02-installation/package-layout.md).

## Sources

This section lists the code and evidence this page draws on.

- `src/somnus_debug/cli.py:54-128`
- `src/somnus_debug/doctor/core.py:81-83`, `:1916-1977`, `:2046-2203`
- `src/somnus_debug/structure/core.py:202-351`
- `src/somnus_debug/pycache_cleaner/core.py:64`, `:150-154`, `:323-375`
- `src/somnus_debug/test_harness/scaffold.py:62-129`; `src/somnus_debug/test_harness/templates/run_test.py:186-195`, `:749`
- `pyproject.toml` `[project.scripts]`
- [lane D command-reference.md](../_evidence/agent-findings/lane-d-cli-tests/command-reference.md), [help-surfaces-raw.txt](../_evidence/agent-findings/lane-d-cli-tests/help-surfaces-raw.txt), [experiment-log.md](../_evidence/agent-findings/lane-d-cli-tests/experiment-log.md), [install-vs-source.md](../_evidence/agent-findings/lane-d-cli-tests/install-vs-source.md)
- [lane B configuration-findings.md](../_evidence/agent-findings/lane-b-config/configuration-findings.md)
- [lane F fieldkit.md](../_evidence/agent-findings/lane-f-ext/fieldkit.md), [harness.md](../_evidence/agent-findings/lane-f-ext/harness.md), [compositions.md](../_evidence/agent-findings/lane-f-ext/compositions.md)
- W2 runs: [verification-results](../11-verification/verification-results.md#w2-runs)
