# Environment variables

This page lists every environment variable that changes somnus-debug's behavior, the ones it reads directly and the interpreter-level ones that change its results, and states plainly what it does not read.

## What was searched

This section records the search behind the "only two variables" claim.

`grep -rn "os.environ\|getenv\|environ" src/ skills/somnus-debug-fieldkit/scripts/` at baseline `034f46e` finds:

- `src/somnus_debug/test_harness/templates/run_test.py:590` (`SINGLE_TEST_OUTPUT_DIR`) and `:749` (`PROJECT_ROOT`).
- `skills/somnus-debug-fieldkit/scripts/onboard.py:106-109` (copies `os.environ`, extends `PYTHONPATH` for children).
- `skills/somnus-debug-fieldkit/scripts/selftest.py:199-200` (copies `os.environ`, sets `PYTHONPATH` for one check).

Nothing in `cli.py`, `doctor/core.py`, `pycache_cleaner/core.py`, `structure/core.py`, or `scaffold.py` reads the environment [VERIFIED by grep]. There is no `SOMNUS_*` variable anywhere.

## Variables the tools read directly

This section documents the two variables the scaffolded harness reads.

| Variable | Read by | Default when unset | Empty value | Relative value | Evidence |
|---|---|---|---|---|---|
| `PROJECT_ROOT` | `run_test.py` `main()` | parent of the directory holding `run_test.py` | `Path("")` = CWD | resolved against CWD; `~` expanded | [VERIFIED W3 R1, R2, R4b; `run_test.py:748-750`] |
| `SINGLE_TEST_OUTPUT_DIR` | `run_test.py` `_default_output_root()` | `<project_root>/test-runs` | treated as unset | resolved against **CWD**, not `PROJECT_ROOT`; `~` expanded | [VERIFIED W3 R3, R5; `run_test.py:589-593`] |

W3 runs (fixture `/tmp/w3/th/repo/run_test.py`, scaffolded with `init-test-harness repo`; the shipped test always fails, so every run exits 1 with verdict FAIL, but the artifact path is what matters):

| Run | Environment | cwd | Manifest written under |
|---|---|---|---|
| R1 | none | `/tmp/w3/th` | `/tmp/w3/th/test-runs/` (outside the repo) |
| R2 | `PROJECT_ROOT=/tmp/w3/th/repo` | `/tmp/w3/th` | `/tmp/w3/th/repo/test-runs/` |
| R3 | `SINGLE_TEST_OUTPUT_DIR=/tmp/w3/th/arts` | `/tmp/w3/th` | `/tmp/w3/th/arts/` |
| R4b | `PROJECT_ROOT=` and `SINGLE_TEST_OUTPUT_DIR=` (both empty) | `/tmp/w3/th/elsewhere` | `/tmp/w3/th/elsewhere/test-runs/` |
| R5 | `PROJECT_ROOT=/tmp/w3/th/repo SINGLE_TEST_OUTPUT_DIR=rel_arts` | `/tmp/w3/th` | `/tmp/w3/th/rel_arts/` |
| R6 | none, harness copied to `repo2/tools/run_test.py` | `/tmp/w3/th` | `/tmp/w3/th/repo2/test-runs/` |

Executed: yes (`/tmp/w3/th`, outputs above). Both variables are documented only in a comment in the template (`run_test.py:188-192`), not in `docs/MANUAL.md` [SOURCE-CONFIRMED]. The manifest records the resolved `project_root` under `environment` [VERIFIED W3 R2]. [D-15](../DISCOVERY-LEDGER.md#d-15)

## Interpreter variables that change doctor results

This section covers variables doctor never reads but whose effect shows up in its findings.

Doctor classifies an import as third-party when `importlib.util.find_spec(top_level)` succeeds in the interpreter running the scan (`src/somnus_debug/doctor/core.py:1050-1055`). Anything that changes that interpreter's `sys.path` changes `missing_imports`:

| Input | Effect | Evidence |
|---|---|---|
| `python -m somnus_debug.cli` | puts CWD on `sys.path`, so modules in CWD resolve | [VERIFIED W3 ENV1] |
| `python -P` or `PYTHONSAFEPATH=1` | removes CWD from `sys.path` | [VERIFIED W3 ENV2, ENV3] |
| `PYTHONPATH` | adds roots; adding a src-layout `src/` makes the project's own packages resolve | [VERIFIED W3 ENV4, recipe R8] |
| active virtualenv | decides which third-party packages exist | [SOURCE-CONFIRMED; lane F onboarding rationale `onboard.py:44-48`] |
| console script (`somnus-doctor`, `somnus-debug`) | like `-P`: the script directory, not CWD, is on `sys.path` | [HYPOTHESIS, reproduced by lane B with `python -P`; installed scripts not run in that lane] |

W3 probe (fixture `/tmp/w3/fx/srcl` with `src/calc/__init__.py` and `tests/test_c.py` importing `calc` and `zzlocalonly`; `zzlocalonly.py` sits in the CWD `/tmp/w3/envx`):

| Probe | Invocation | `missing_imports` |
|---|---|---|
| ENV1 | `PYTHONPATH=<repo>/src python3 -m somnus_debug.cli doctor scan ../fx/srcl --no-state -o o.md` | `calc` |
| ENV2 | same with `python3 -P` | `calc`, `zzlocalonly` |
| ENV3 | same with `PYTHONSAFEPATH=1` | `calc`, `zzlocalonly` |
| ENV4 | `python3 -P` with `PYTHONPATH=<repo>/src:/tmp/w3/fx/srcl/src` | `zzlocalonly` |

Executed: yes (`/tmp/w3/envx`). `calc` is missing in ENV1 because doctor indexes `src/calc/__init__.py` as module `src.calc`, so `import calc` is not local [SOURCE-CONFIRMED `core.py:984-992`]. [D-22](../DISCOVERY-LEDGER.md#d-22), [D-26](../DISCOVERY-LEDGER.md#d-26)

## Variables the fieldkit scripts use

This section covers the fieldkit's use of `PATH` and `PYTHONPATH`.

| Variable | Script | Use | Evidence |
|---|---|---|---|
| `PATH` | onboard.py, selftest.py | `shutil.which("somnus-debug")` is the last-resort runner; none found -> exit 3 | [VERIFIED W3 OB8; `onboard.py:256`, `selftest.py:326`] |
| `PATH` | onboard.py | `git` for `git status --ignored`, only when `<repo>/.git` exists; a non-zero git exit is ignored (empty list), but a missing `git` binary raises `FileNotFoundError` through `subprocess.run` | [SOURCE-CONFIRMED `onboard.py:149-158,187-188`] |
| `PYTHONPATH` | onboard.py | child processes get `<repo>/src` prepended for src layouts; inherited value kept after it | [SOURCE-CONFIRMED `onboard.py:104-110`] |
| `PYTHONPATH` | selftest.py | one check sets it to a fixture's `src/` to prove the src-layout rule | [SOURCE-CONFIRMED `selftest.py:199-201`] |

## Other variables with an indirect effect

This section lists variables that only matter through Python's own path handling.

| Variable | Where it matters | Evidence |
|---|---|---|
| `HOME` | `~` expansion in pycache `--config`, `roots`, `log_file`, and in `run_test.py` paths | [VERIFIED W3 P19: `~/nonexist-w3` -> `/home/sandbox/nonexist-w3`] |
| `PYTHONWARNINGS` | hides the `SyntaxWarning` from the pycache module docstring's invalid escape (`pycache_cleaner/core.py:64`) on first compile | [VERIFIED lane B; all W3 runs set `PYTHONWARNINGS=ignore`] |
| `PYTHONDONTWRITEBYTECODE` | keeps runs from writing `__pycache__` into the source tree; no tool reads it | [SOURCE-CONFIRMED (Python semantics)] |

## What is not expanded or read

This section lists environment features users might assume exist.

- `$VAR` in pycache `roots` is not expanded, although the module docstring says "Environment variables and ~ are expanded" [VERIFIED W3 P12: `$HOME/tree` became `/tmp/w3/pc/$HOME/tree`; DISCREPANCY with the pycache module docstring].
- Doctor config files get no variable interpolation of any kind [SOURCE-CONFIRMED `core.py:619-643`].
- No tool reads `NO_COLOR`, `CI`, `VIRTUAL_ENV`, or a log-level variable [VERIFIED by grep].

## Sources

This section lists the evidence behind this page.

- [`../_evidence/configuration-registry.tsv`](../_evidence/configuration-registry.tsv) rows `PROJECT_ROOT`, `SINGLE_TEST_OUTPUT_DIR`, `PYTHONPATH / PYTHONSAFEPATH / python -P / CWD on sys.path`, `PATH lookup of somnus-debug`, `PYTHONPATH extension (src layout)`
- [`../_evidence/agent-findings/lane-b-config/configuration-findings.md`](../_evidence/agent-findings/lane-b-config/configuration-findings.md) sections 2.5, 5.6
- [`../_evidence/agent-findings/lane-f-ext/harness.md`](../_evidence/agent-findings/lane-f-ext/harness.md)
- `src/somnus_debug/test_harness/templates/run_test.py:188-192,589-593,747-760`, `src/somnus_debug/doctor/core.py:984-1055`, `src/somnus_debug/pycache_cleaner/core.py:184-186`, `skills/somnus-debug-fieldkit/scripts/onboard.py:104-110,156-159,256`, `skills/somnus-debug-fieldkit/scripts/selftest.py:199-201,324-330`
- W3 probes R1-R7, ENV1-ENV4, P12, P19, OB8
