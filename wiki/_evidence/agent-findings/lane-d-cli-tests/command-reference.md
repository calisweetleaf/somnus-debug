# Lane D: command reference (verbatim help, behavior, output contracts, artifacts)

Source: installed venv `/tmp/lane-d/venv` (built from this repo, non-editable) unless noted. The help text below is **verbatim** captured output. Every surface, with its exit code, is in `help-surfaces-raw.txt` (all exit 0, apart from the root `run_test.py --help` case described in §7). Experiment IDs (D01…, S01…) refer to `experiment-log.md` and `experiments.jsonl`.

## 0. Surfaces and wiring

| Invocation | Backend | argv handling |
|---|---|---|
| `somnus-debug <cmd> …` | `somnus_debug/cli.py:main` → `_run_subcommand` | Sets `sys.argv = ["somnus-debug <cmd>", *rest]`, then calls `entry(list(rest))`. `pycache-clean` is the exception: it calls `entry()`, which reads `sys.argv` (`cli.py:99`). Catches `SystemExit` and converts its code to an int; a non-int code becomes 1 (`cli.py:100-101`). Other exceptions propagate as tracebacks. |
| `somnus-doctor` | `doctor/core.py:main` (`:2184`) | Reads `sys.argv[1:]` |
| `somnus-structure` | `structure/core.py:main` (`:323`) | Reads `sys.argv[1:]` |
| `somnus-pycache-clean` | `pycache_cleaner/core.py:main` (`:349`) | `parse_args()` reads `sys.argv`. Returns `None`. |
| *(no script)* init-test-harness | `test_harness/scaffold.py:main` (`:112`) | `prog` is hardcoded as `somnus-debug init-test-harness` |
| root `python_production_doctor.py`, `analyze_python_structure.py`, `pycache_cleaner.py`, `run_test.py` | pre-packaging duplicates (see `install-vs-source.md` §4) | — |

**Dispatcher vs standalone (VERIFIED):** each pair runs the same backend function. Help bodies are identical except for the `usage:` prog name (`somnus-debug doctor` vs `somnus-doctor`). Exit codes matched on every pair I tried: help 0, D35/D36/D37 legacy positional scans 2, P03 standalone pycache 0. The one real difference is that the dispatcher eagerly imports **all four tools** (`cli.py:54-57`). A missing PyYAML therefore breaks `somnus-debug doctor` (F02b, exit 1). It also means the pycache-clean `SyntaxWarning` can surface on any subcommand.

---

## 1. `somnus-debug` (dispatcher)

```
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

- No args, `-h`, or `--help` → this text on stdout, exit 0. Anything after `--help` is ignored (C07).
- `-V` / `--version` → `0.1.0`, exit 0.
- Unknown command → `somnus-debug: unknown command 'x'` plus help on **stderr**, exit 2 (C01).
- `python -m somnus_debug` is unsupported (no `__main__`, exit 1, C04). Use `python -m somnus_debug.cli`.

## 2. `doctor`

```
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

### 2.1 `doctor scan`
```
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
### 2.2 `doctor init-config`
```
usage: somnus-debug doctor init-config [-h] [-o OUTPUT] [--force]

options:
  -h, --help            show this help message and exit
  -o OUTPUT, --output OUTPUT
                        configuration output path
  --force               replace existing configuration
```
### 2.3 `doctor history`
```
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
### 2.4 `doctor rollback`
```
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
### 2.5 `doctor self-check`
```
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

### Doctor behavior (VERIFIED unless marked)

- **argv normalization** (`normalize_argv`, `core.py:2165`):
  - no args → `scan .`
  - first token is a flag → `scan . <flags>`
  - first token is not a known subcommand → `scan <token> …`
  - `somnus-doctor --no-state …`, `somnus-doctor p …`, and `somnus-debug doctor p …` all scan (D35–D37).
  - `doctor --version` becomes `scan . --version`, and argparse errors with exit 2 (C02).
- **Log file.** `setup_logging` (`:2179-2181`) opens `production_doctor.log` in **CWD** with `force=True` on every invocation, including argparse errors and `--help`. The file stays at **0 bytes** on successful scans (D01: 0 bytes). Doctor has only two logging calls, both in `main` (`:2192`, `:2196`): the DoctorError render (exit 4) and the critical traceback (exit 5).
- **Verbose flags do nothing.** `-v`/`--verbose` changes nothing observable: the log was 0 bytes with neither, `-v`, or `--verbose`. `setup_logging` only checks for the literal `"--verbose"`, so `-v` never sets DEBUG (SOURCE-CONFIRMED `:2186`), and there are no debug calls to emit anyway.
- **Report paths.**
  - Without `-o`/`--json-output`: `<project_root>/production_doctor_report.{md,json}`.
  - With state on: also `<project_root>/.python_doctor/state.sqlite3`, `.python_doctor/reports/<RUN_ID>/production_doctor_report.{md,json}`, and `.python_doctor/reports/latest.{md,json}`.
  - `-o` and `--json-output` set independently. Parent directories are created (D18, D43).
  - `--no-state` writes only the two report files (D02).
- **stdout contract** (scan):
  ```
  Scan complete: files=N, issues=N, critical=N, serious=N
  Markdown report: <path>
  JSON report: <path>
  State latest markdown: <path>     # only with state
  Run ID: YYYYMMDDTHHMMSSZ          # only with state
  ```
- **JSON report keys**: `config_hash, dependency_graph{cycles,edges,mermaid,missing_imports,nodes}, files[], finished_at, issues[], project_root, run_id, started_at, state_delta{new_files,modified_files,deleted_files,unchanged_files}, summary{critical_issues, dependency_cycles, files_scanned, info_issues, minor_issues, missing_imports, production_score, serious_issues, suspicious_short_classes, suspicious_short_functions, syntax_error_files, total_issues}`.
  - Issue keys: `category, column_offset, details, evidence, file_path, line_number, message, remediation, severity, symbol`.
  - Issues appear twice: top-level `issues[]` and per-file `files[].issues`.
- **Markdown report** opens with an inline `<style>` block and an HTML "terminal" div (`markdown_include_css: true`), then the Summary and Issue Categories tables.
- **Config.**
  - `-c` takes YAML (doctor's own minimal parser) or JSON.
  - **No auto-discovery**: a `python_doctor.yaml` in the project root or CWD is ignored (D27/D27b, gate `none` ignored, exit 2).
  - Partial configs merge over defaults (D28, D32).
  - Unknown keys are silently accepted (D29).
  - **Malformed YAML `schema_version: [` is silently accepted** and the scan proceeds with defaults (D30, exit 2). Malformed JSON → exit 4 (D33). A non-bool for a bool key → exit 4 (D34). Bad `severity_exit_level` → exit 4 (D26_bogus).
- **Gates** (`exit_code_for_summary`, `:2046`):
  - `none` → 0
  - `critical` → 2 if critical, else 0
  - `serious` (default) → 2 if critical, 1 if serious, else 0
  - `minor` and `info` → **1 even when critical findings exist** (D26_minor/info: critical=2 but exit 1)
- **init-config.**
  - Writes `python_doctor.yaml` in CWD by default (D25), or the `-o` path.
  - Refuses to overwrite: exit 4 with `Configuration file already exists.` and context remediation `Use --force` (D23). `--force` replaces (D24).
- **history.**
  - Prints `Run history:` lines `- <run_id> | <completed_at> | files= | issues= | critical= | serious=` plus `markdown=`/`json=` paths.
  - `No recorded runs found.` when empty, exit 0 (D12). That run also **creates** `<root>/.python_doctor/state.sqlite3` in the queried project as a side effect (observed under proj2 after D12).
- **rollback.**
  - Copies the stored run's reports over `.python_doctor/reports/latest.*` and updates the `latest` alias (D09).
  - Unknown id → exit 4 `Run ID does not exist in state history.` (D10). Missing `--run-id` → exit 2 (D11).
- **Run ID collision.** Run IDs are second-resolution (`RUN_ID_FORMAT = "%Y%m%dT%H%M%SZ"`, `:82`). Two scans in the same second got the same ID (D13). `INSERT OR REPLACE INTO runs` (`:1975`) **silently overwrote** the first. The DB held 1 row, and that second's report directory was overwritten. onboard reruns hit this too (O02/O03 both `run_id=20261112T001726Z`).
- **Corrupt or unopenable state DB.**
  - `scan` degrades: stderr `Warning: local SQLite state is unavailable; continuing without history or rollback (Unable to initialize state database.).` It still writes reports and exits on the gate (D39).
  - `history` and `rollback` → exit 4 (D40/D41).
- **self-check** scans `Path(doctor/core.py).parent`, i.e. only the **`doctor/` package dir**: 2 files.
  - Default output is `<that dir>/self_check_report.{md,json}`, plus `.python_doctor/` **inside the installed package directory** (site-packages) (D14).
  - On itself: `files=2 issues=78 critical=0 serious=17`, exit 1. Among those findings: `.core` relative import "unresolved" because the root is the doctor dir, 11 `silent_failures` on its own CLI-boundary handlers, and 2 `placeholder_returns`.
- **Path errors.** Nonexistent project root → exit 4 `Project root does not exist.` (D16). A file passed as root → exit 4 `Project root must be a directory.` (D18). Empty dir → `files=0`, exit 0 (D17, D38).
- **Unwritable output** → exit 4 `Unable to write artifact.` (D43).
- **Exit 5.** A 20k-term `1+1+…` expression in one file raises `RecursionError` in `ast.parse`. It is not contained per file: the **whole scan aborts**, exit 5, `Unclassified runtime failure: RecursionError …`, and the traceback lands in `production_doctor.log` (D44).

### Detector behavior on fixtures (VERIFIED, D01–D04, D02, D03)

| Category | Fixture trigger | Result |
|---|---|---|
| `syntax_errors` + `tokenization_errors` (critical) | `def oops(:` | both emitted, exit 2 |
| `analysis_read_errors` (critical) | latin-1 bytes file | emitted. **Counted in `summary.syntax_error_files`** (=1 with no syntax errors present) |
| `broad_exceptions` | bare `except:` / `except Exception:` | emitted |
| `silent_failures` | `except: return None`, `except ValueError: pass`, `obj.logger.error(...)`, `log.exception(...)` | all four flagged. `logger.exception(...); raise` not flagged. Matching is **name-sensitive**: only `logging.error/exception` and `logger.error/exception` count (`core.py:1486`) |
| `stubs` | `pass`+TODO, `raise NotImplementedError`, `...` | flagged. Also flags **`@abc.abstractmethod` with `...`**, **Protocol method `...`**, and **both `@overload` stubs** (lines 97, 99). Abstract methods whose body is only a docstring are *not* flagged |
| `duplicate_definitions` | two `def dup`, `@property`/`@value.setter`, 3× `ov` overloads | flagged. The property setter is flagged (`value`, line 81). For overloads only `lines[1]` is reported (`_check_duplicates`, `:1315`) |
| `placeholder_returns` (serious) | `return 1` | **flagged as placeholder.** `return 2` is not. Cause: `PLACEHOLDER_CONSTANTS = (None, False, True, 0, -1, "")` (`:513`) with an `in` test (`:1458`), and `1 == True` in Python. Any function whose sole statement is `return 1` (or `1.0`, `0.0`) is a serious finding |
| `todos` | TODO/FIXME/HACK/XXX/TEMP/WIP and lowercase `todo` | all flagged, case-insensitive (`:1557`). Message labels: `Action Required`, `Critical Fix Needed`, `Technical Debt`, `Urgent Review`, `Temporary Code`, `Work In Progress` |
| `security_risks` | `pickle.loads`, `subprocess.run(shell=True)`, `os.system`, `eval` | flagged by call name only (`SECURITY_CALLS`, `:514`). **Hardcoded secrets (`API_KEY = "sk-live-…"`, `password = "…"`) are not detected.** No secret detector exists |
| `print` | `print("debug output")` | **not a detector.** Only counts inside an except body as "silent" |
| `complexity` (minor) | if/elif chain, CC=16 > 12 | flagged |
| `suspicious_short_classes` | docstring-only class | flagged (serious) |
| `incomplete_methods` | same-file subclass missing an abstract method | flagged (`missing_methods: ["two"]`) |
| `dependency_cycles` | `import pkg.b` ↔ `import pkg.a` | detected (D03, exit 1) |
| `dependency_cycles` | `from pkg import b` ↔ `from pkg import a` | **missed.** Both edges resolve to `pkg/__init__.py`, not the submodule (D02: `cycles: []`) |
| `missing_imports` | src-layout `from mypkg.helpers import …` | flagged without `PYTHONPATH=src` (D01). Resolved with it (D04). Third-party resolution uses doctor's own interpreter (D05a/b) |
| `unused_imports` | `import totally_missing_module_xyz` | flagged (and missing) |
| `test_gaps` | — | **never emitted.** `severity_levels` and `detect_test_gaps` exist (`:493`, `:840`), but no producer calls `create("test_gaps", …)` (grep finds only the config lines) |
| stamped header file (`#   type: "source-code"`) | doctor | **no crash.** Doctor's `ast.parse` does not use `type_comments` |

## 3. `structure`

```
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

- **Output contract.** Markdown on stdout:
  - `# Class Index for \`<name>\``
  - a fixed line `Generated by \`analyze_python_structure.py\` …`, which still names the old script under `somnus-debug structure`
  - counts lines
  - `## class \`X\`(bases) (lines a-b)` with `**Doc**:` and a `- \`def sig\`` list (decorators and docstring summary as sub-bullets)
  - `## Module-level functions`
- **Writes.** It writes nothing unless `-o` or `--update-doc` is given. Both create parent directories.
  - `--update-doc` does **not** require the file to exist, despite "Regenerate an existing" (S12 created a new file). `-o` and `--update-doc` are mutually exclusive (exit 2, S13).
  - With `--no-module-functions`, module functions are omitted, but the header count still says `Definitions emitted …: 18` and includes them (S10).
- **Errors.** Missing file, directory, and syntax error all exit 2 with `error: …` (S14, S15, S17). Argparse errors are also exit 2 (S13, S16). Callers cannot tell usage errors from runtime errors.
- **Stamped files crash.** src, installed, and PyPI versions all crash on any file containing a header line `#   type: "…"` (`type_comments=True`, `structure/core.py:210`). The root duplicate does not. See `install-vs-source.md` §5.

## 4. `pycache-clean`

```
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

- **There is no root/path argument.** Roots come only from YAML `roots:`. Default config is `./config.yaml` relative to CWD. A missing config → stderr `Configuration file not found: <abs>`, exit 1 (P04).
- **Logging.** Log lines go to **stdout**, plus an optional `log_file` that is appended to (P01 created `clean.log`).
- **Dry-run wording.** In dry-run, verbose lines still say `Removed directory …` / `Removed file …`, and the summary says `Summary: deleted 2 directories, 2 files; freed 0.00 MiB`, even though nothing is deleted (P01/P02; verified nothing removed). Only the `Starting pycache cleaner (dry_run=True)` header distinguishes the two modes.
- **Real run (P03).** Removed `__pycache__/` dirs and loose `*.pyc`/`*.pyo`. Respected excludes `node_modules` and `.venv`, and kept `keep.py`.
- **Missing root.** A missing root is logged as `[ERROR] Root path does not exist…` and the run still **exits 0** (P01, P03).
- **Bad config.** `roots: []` → logged traceback on stdout, exit 1 (P05). Malformed YAML or a top-level list → **uncaught traceback**, exit 1 (P06/P07), because `from_yaml` runs outside the try.
- **Unknown config key silences all logging.** It triggers `logging.warning(...)` **before** `setup_logging`. That call auto-configures the root logger (stderr, WARNING). The later `basicConfig` (`:334`, no `force=True`) is then a no-op, so INFO/DEBUG output, `--verbose`, and `log_file` are all lost. P09 printed only `WARNING:root:Ignoring unknown config key 'bogus_key'` but still deleted files.
- **`--max-depth 0`** cleans only directory targets directly under the root (P09: `t/__pycache__` removed, `t/l1/l2/__pycache__` kept). Bad `--max-depth` → exit 2 (P08).
- **Returns None.** `main` returns `None`, so success is exit 0 through both the standalone script and the dispatcher.

## 5. `init-test-harness`

```
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

- **Writes.** Writes `run_test.py` (and `CONTRACT.md`), prints `wrote <abs path>` per file, then a `Next: edit TEST_NAME and execute_test()…` hint. Exit 0 (H01). Missing target directories are created (H04).
- **Refuses to overwrite.** If any destination exists: `error: refusing to overwrite existing file(s) without --force: …`, exit 1, nothing written (H02, H05). Target is a file → `error: [Errno 17] File exists`, exit 1 (H07).
- **Copies provenance headers.** Scaffolded files carry the template's own provenance header: `run_test.py` gets a `# somnus:metadata:v2` block and `CONTRACT.md` gets a YAML front-matter block with the template's artifact URN. Every target repo inherits the same URNs.

## 6. Scaffolded `run_test.py` (template) behavior

- **No argparse.** `--help` is ignored and the test executes (H09; root `run_test.py --help` too).
- **`PROJECT_ROOT` defaults to `Path(__file__).resolve().parent.parent`** (`templates/run_test.py:749`). `docs/MANUAL.md:296-297` shows `init-test-harness path/to/repo` and `.`, which put the file **at the repo root**. Artifacts then land in **`<repo>/../test-runs/`**, outside the repo (H08: `/tmp/lane-d/run/th/test-runs/…`). Placed at `<repo>/tools/run_test.py`, artifacts land in `<repo>/test-runs/` (H10).
- **Ships an unrunnable default test.** The default `execute_test` is the Golden Path / gp-cli **cargo** test, which fails without `cargo` (H08, exit 1, verdict FAIL).
- **Output contract.** stderr carries human logs. stdout carries the final JSON `{run_id, test_name, verdict, elapsed_s, artifacts{manifest,report,log}}`. Artifacts are `test-runs/<RUN_ID>/{manifest.json,report.md,test.log}`. Exit 0 on PASS (H10, after replacing `execute_test`), 1 on FAIL.

## 7. Root duplicates

The `--help` text of `python_production_doctor.py`, `analyze_python_structure.py`, and `pycache_cleaner.py` matches the packaged one except for the prog name. Root `pycache_cleaner.py` emits the `SyntaxWarning` on every run. Root `run_test.py --help` **executes the test**, and from the repo location it writes to `forge/test-runs/` (see `install-vs-source.md` §7).

## 8. Fieldkit scripts (`skills/somnus-debug-fieldkit/scripts/`, run from a /tmp copy)

| Script | Contract (docstring) | Verified |
|---|---|---|
| `selftest.py [--python PY]` | 0 all pass, 1 any fail, 3 CLI unavailable | 29/29 against the venv CLI (F01). Exit 3 with no CLI on PATH (F03). The `--python` mode **overwrites `PYTHONPATH`** in one check, so it only works with an interpreter that has the package *installed*: PYTHONPATH=src gave 28/29 (F02c) and a yaml-less interpreter 1/24 (F02) |
| `onboard.py [repo] [--apply] [--baseline] [--new-config] [--python]` | 0 ok, 1 usage, 2 coverage failure, 3 CLI unavailable | Plan (O01, 0), apply+baseline (O02, 0), rerun (O03, 0: keeps profile files but **overwrites `runs/baseline.*`**), repo copy plan mode adopts the root `python_doctor.yaml` → `files=0` → FAIL exit 2 (O04), no CLI → 3 (O05/O07), bad path → 1 (O06). `--apply` on an empty dir **writes the profile even though verification FAILS** (O08, exit 2). "Plan mode writes nothing", yet the plan-mode run on the git repo copy modified `.git/index` (git stat refresh, O04) |
| `delta.py BASE LATEST [--dispositions] [--root] [--json]` | 0 clean, 1 new serious/critical, 2 coverage regression, 3 input error | 0 (T01), 1 (T02), 0 with dispositions plus a stale-disposition section (T03), 2 on dropped file (T04) and zero files (T05 `--json`), 3 on missing, malformed, or invalid dispositions (T06–T08) |
