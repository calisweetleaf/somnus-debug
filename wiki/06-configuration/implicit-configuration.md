# Implicit configuration

This page lists the inputs that shape a run although nobody sets them as options: the working directory, the scanned project root, the interpreter, argv shape, the clock, process-wide logging, file encodings, the platform, and the location of the installed package.

## Working directory

This section lists everything that depends on the CWD a tool is started from.

| What | Tool | Effect | Evidence |
|---|---|---|---|
| `production_doctor.log` | doctor | created (append mode) in CWD on every call, `--help` included; stays empty on success | [VERIFIED W3 E10d, E10a/E10b 0 bytes; `src/somnus_debug/doctor/core.py:2181`] [D-10](../DISCOVERY-LEDGER.md#d-10) |
| `-c`, `-o`, `--json-output`, `init-config -o` | doctor | resolved against CWD | [VERIFIED W3 E5, O2] |
| bare `doctor` with no args, or with only flags | doctor | scans CWD (`scan .`) | [VERIFIED W3 L2: scanned the CWD's one file] |
| `sys.path[0]` under `python -m` | doctor | CWD modules resolve as third-party, hiding `missing_imports` | [VERIFIED W3 ENV1 vs ENV2] [D-26](../DISCOVERY-LEDGER.md#d-26) |
| `--config` default `config.yaml`, `roots`, `log_file` | pycache-clean | resolved against CWD; roots are not relative to the config file | [VERIFIED W3 P1, P10/P11] |
| `PROJECT_ROOT=""`, relative `SINGLE_TEST_OUTPUT_DIR` | run_test.py | resolved against CWD | [VERIFIED W3 R4b, R5] |
| `source`, `-o` | structure | resolved against CWD | [SOURCE-CONFIRMED `structure/core.py:326,340`] |
| `target` | init-test-harness | default `.` = CWD | [SOURCE-CONFIRMED `scaffold.py:100`] |
| onboard verification scan | onboard.py | runs from a throwaway temp CWD so the log stays out of the repo; the baseline scan runs with CWD `.somnus-debug/` | [SOURCE-CONFIRMED `onboard.py:505-509,520`; VERIFIED W3 OB3: `production_doctor.log` in `.somnus-debug/`] |

Practical rule: run doctor from a scratch directory and pass absolute paths (recipe R4 in [configuration-recipes.md](configuration-recipes.md)).

## The scanned project root

This section lists what is anchored to doctor's `project_root` argument rather than CWD.

- Default report location `<project_root>/<report_basename>.{md,json}` [VERIFIED W3 L1].
- State: `<project_root>/<state_dir>/state.sqlite3` and `<state_dir>/<reports_dir>/<run_id>/...`; `history` and `rollback` create this directory even when nothing was ever recorded [VERIFIED W3 E9b: `.python_doctor/` appeared after a `history` without `-c`].
- Module names: a file's module name is its path relative to project root, so the same package scanned from a parent directory gets different module names and different local-import resolution [SOURCE-CONFIRMED `core.py:954-961,984-992`]. A `src/` layout scanned at the repo root yields modules `src.<pkg>` [VERIFIED W3 ENV1]. [D-22](../DISCOVERY-LEDGER.md#d-22)
- Pattern matching: include and ignore globs are tested against the root-relative POSIX path and the basename [SOURCE-CONFIRMED `core.py:939-952`].

## The interpreter

This section lists interpreter properties that act as configuration.

| Property | Effect | Evidence |
|---|---|---|
| installed packages / active venv | `find_spec` decides third-party versus missing | [SOURCE-CONFIRMED `core.py:1050-1055`] |
| `sys.stdlib_module_names` (3.10+) | the standard-library list; on older interpreters the `getattr` default would be empty, but `requires-python >= 3.10` | [SOURCE-CONFIRMED `core.py:1001`, `pyproject.toml`] |
| `PyYAML` importable | required by the `somnus-debug` dispatcher for every subcommand (it imports all tools); `somnus-doctor` does not need it | [VERIFIED W3 NOYAML1/NOYAML2] [D-13](../DISCOVERY-LEDGER.md#d-13) |
| Python 3.12 compile warnings | pycache module docstring emits a `SyntaxWarning` on first compile | [VERIFIED lane B] |

## argv shape

This section lists how the shape of argv, not just its content, changes behavior.

- Dispatcher: `-h`, `--help`, `-V`, `--version` are honored only as the first argument; `somnus-debug doctor --version` becomes `scan . --version` and exits 2 [VERIFIED W3 L3; `cli.py:111-116`, `core.py:2174-2175`].
- Doctor legacy normalization: no args -> `scan .`; first arg starts with `-` -> `scan . <args>`; first arg not a subcommand -> `scan <args>` [VERIFIED W3 L1/L2; `core.py:2165-2176`]. A directory literally named `history` or `scan` cannot be scanned in the bare form [SOURCE-CONFIRMED].
- `--verbose` is detected by substring membership in raw argv before parsing, so it is honored anywhere and `-v` never is [SOURCE-CONFIRMED `core.py:2186`].
- The dispatcher rewrites `sys.argv` to `[prog, *rest]` around the call, so argparse usage lines say `somnus-debug doctor` [SOURCE-CONFIRMED `cli.py:95-103`].

## The clock

This section lists time-derived values.

- Doctor run IDs use `%Y%m%dT%H%M%SZ` in UTC at one-second resolution; two stateful scans of one root within a second share an ID and `INSERT OR REPLACE` overwrites the first [SOURCE-CONFIRMED `core.py:82,532,1975`; not reproduced]. [D-08](../DISCOVERY-LEDGER.md#d-08)
- `history` orders by the `completed_at` text column. In this sandbox `isoformat()` returned a localized string, so ordering was only checked within one day [CONDITIONAL, lane F sandbox caveat; W3 E9c output shows `Wed 2026-11-11 6:37 PM CST`].
- run_test.py run IDs add six random hex characters, so they do not collide [SOURCE-CONFIRMED `run_test.py:753-757`].
- onboard.py stamps PROFILE.md with the host-local date [VERIFIED lane F OB-7].

## Process-wide logging

This section lists logging state that one tool sets for the whole process.

- Doctor `main()` calls `logging.basicConfig(..., force=True)` with a file handler for `production_doctor.log`, replacing any handlers a host program installed [SOURCE-CONFIRMED `core.py:2181`]. [D-11](../DISCOVERY-LEDGER.md#d-11)
- pycache-clean calls `basicConfig` without `force`; if anything configured the root logger first (including its own warning about an unknown config key), its INFO output, `--verbose`, and `log_file` silently do nothing [VERIFIED W3 P9: only the WARNING line; log file 0 lines].

## File encoding and content

This section lists properties of the scanned files that change outcomes.

- structure reads its source as UTF-8 regardless of a PEP 263 cookie; a latin-1 file is an uncaught `UnicodeDecodeError` (traceback, exit 1) [VERIFIED lane B; `structure/core.py:326`].
- structure parses with `type_comments=True`, so a comment shaped like `# type: ...` in the wrong place, including the `#     type: "source-code"` line of a `somnus:metadata` header, is a `SyntaxError` (exit 2); the root duplicate `analyze_python_structure.py` parses the same file [VERIFIED W3 S5/S5b]. [D-01](../DISCOVERY-LEDGER.md#d-01)
- Doctor reads sources with declared-encoding support through its `SourceReader` [SOURCE-CONFIRMED `core.py:1058-1060`].

## Platform

This section lists platform-dependent behavior.

- Doctor uses `fnmatch.fnmatch`, which applies `os.path.normcase`: case-sensitive on POSIX (verified by lane B: `Build/k.py` not ignored by `build/*`), case-insensitive on Windows [SOURCE-CONFIRMED; Windows UNVERIFIED].
- pycache-clean uses `fnmatchcase` (always case-sensitive) [SOURCE-CONFIRMED `pycache_cleaner/core.py:263,270`]. Its docstring promises Windows `\\?\` long-path handling that no code implements [SOURCE-CONFIRMED absence; DISCREPANCY].

## Package location

This section covers settings derived from where the package is installed.

- `doctor self-check` scans the directory containing `doctor/core.py` and writes `self_check_report.{md,json}` and `.python_doctor/` into it, which is site-packages for an installed copy; on a read-only install it fails (exit 4) unless `-o` is given [VERIFIED lane B on a copy; `core.py:2123-2127`]. [D-10](../DISCOVERY-LEDGER.md#d-10)
- `init-test-harness` reads its templates with `importlib.resources` from the installed package [SOURCE-CONFIRMED `scaffold.py:58-59`].
- run_test.py derives its default project root from its own file location [VERIFIED W3 R1/R6].
- onboard.py and PROFILE.md embed absolute paths to the fieldkit and interpreter [VERIFIED lane F OB-6].

## Sources

This section lists the evidence behind this page.

- [`../_evidence/configuration-registry.tsv`](../_evidence/configuration-registry.tsv) (rows with surface `implicit`, `implicit file`, `implicit env`, `derived value`)
- [`../_evidence/agent-findings/lane-b-config/configuration-findings.md`](../_evidence/agent-findings/lane-b-config/configuration-findings.md) section 5
- [`../_evidence/agent-findings/lane-f-ext/fieldkit.md`](../_evidence/agent-findings/lane-f-ext/fieldkit.md) (sandbox caveat, OB-6, OB-7)
- [`../_evidence/agent-findings/lane-d-cli-tests/install-vs-source.md`](../_evidence/agent-findings/lane-d-cli-tests/install-vs-source.md) (type_comments)
- `src/somnus_debug/cli.py:95-116`, `src/somnus_debug/doctor/core.py:82,532,937-1060,1923-1975,2123-2186`, `src/somnus_debug/pycache_cleaner/core.py:263-334`, `src/somnus_debug/structure/core.py:210,326`, `src/somnus_debug/test_harness/scaffold.py:58-59`, `src/somnus_debug/test_harness/templates/run_test.py:747-760`
- W3 probes E5, E9b/E9c, E10, L1-L3, O2, P1, P9-P11, R1, R4b-R6, S5/S5b, ENV1-ENV2, NOYAML1/2, OB3
