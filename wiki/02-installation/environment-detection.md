# Environment detection

This page records what each tool detects about the machine and the environment it runs in, and what it deliberately does not detect. That matters because results, especially doctor's import findings, change with the interpreter, the invocation form, and the cwd, even when the code under scan is identical.

## Summary

This section is the one-table answer.

| Signal | doctor | structure | pycache-clean | init-test-harness | run_test.py | fieldkit onboard.py |
|---|---|---|---|---|---|---|
| interpreter's `sys.path` / installed packages | **yes** (import resolution) | no | no | no | records `sys.executable` | yes (picks a runner) |
| stdlib module list | yes (`sys.stdlib_module_names`) | no | no | no | no | no |
| current working directory | yes (log location; on `sys.path` under `python -m`) | no | yes (default config path; relative roots) | yes (default target `.`) | no | default repo |
| environment variables | none read | none | none | none | `PROJECT_ROOT`, `SINGLE_TEST_OUTPUT_DIR` | `PATH` (finds the CLI) |
| OS / platform | not detected | no | not detected (despite the docstring) | no | recorded (`platform.platform()`) | no |
| git | no | no | no | no | no | yes (`git status --ignored`) |
| virtualenvs | no | no | no | no | no | yes (`pyvenv.cfg` anywhere) |
| config file discovery | **none** | n/a | `./config.yaml` only | n/a | n/a | adopts a root `python_doctor.yaml` |
| terminal / colour | no | no | no | no | no | no |

Sources: [SOURCE-CONFIRMED] grep for `os.environ|getenv|isatty|os.name|sys.platform|platform.` over `src/somnus_debug/{cli,doctor/core,structure/core,pycache_cleaner/core,test_harness/scaffold}.py` finds none of them. The only `os.environ` reads in the package are in `src/somnus_debug/test_harness/templates/run_test.py:590` and `:749`, and `platform.platform()` is at `:622`. Fieldkit: lane F [fieldkit.md](../_evidence/agent-findings/lane-f-ext/fieldkit.md) section 2.

## doctor: import resolution follows the running interpreter

This section explains the one detection that changes findings.

`ImportResolver.resolve` (`src/somnus_debug/doctor/core.py:1003-1016`) classifies each import in this order:

1. **local**: the module is a file in the scanned project index.
2. **standard_library**: the top-level name is in `sys.stdlib_module_names | sys.builtin_module_names` of the **running** interpreter (`:1001`).
3. **third_party**: `importlib.util.find_spec(top_level)` succeeds in the **running** interpreter (`:1050-1055`).
4. **missing**: otherwise. This is a serious `missing_imports` finding by default.

Consequences, all [VERIFIED]:

- **Interpreter.** The same `import pytest` is resolved under a venv that has pytest and missing under one without it (lane D D05a/D05b).
- **`PYTHONPATH`.** A src-layout package's own imports are missing without `PYTHONPATH=src` and `third_party` with it (W2-14). See [D-22](../DISCOVERY-LEDGER.md#d-22).
- **Invocation form and cwd.** `python -m ...` puts the cwd on `sys.path`, while a console script does not. In W2-25, a project file did `import cwdhelper`, and `cwdhelper.py` existed only in the cwd:

  | Invocation (cwd = directory containing `cwdhelper.py`) | Edge classification | Exit |
  |---|---|---:|
  | `somnus-debug doctor scan ../proj --no-state ...` | `('cwdhelper', 'missing')`, 1 serious | 1 |
  | `python -m somnus_debug.cli doctor scan ../proj --no-state ...` | `('cwdhelper', 'third_party')`, 0 issues | 0 |

  Pick one invocation form for CI and run it from a neutral cwd. See [D-26](../DISCOVERY-LEDGER.md#d-26).
- **Python version.** Stdlib membership is version-specific. For example, a module removed from the stdlib in 3.13 would be missing under 3.13 and stdlib under 3.12. [HYPOTHESIS] from `:1001`. In this wave's fixtures, results were identical on 3.10, 3.11, and 3.12 (W2-06).

The scanned code is never imported or executed. Only `find_spec` is called, on top-level names. `find_spec` can import parent packages for dotted names, but doctor only passes the top-level segment. [SOURCE-CONFIRMED] `:1012`, `:1050-1055`.

## doctor: what it does not look at

This section lists absent detection that users sometimes assume exists.

- **No config discovery.** Without `-c`, it does not read `python_doctor.yaml` in the root or the cwd, `pyproject.toml`, or a user-level file. [VERIFIED] lane D D27/D27b. See [D-02](../DISCOVERY-LEDGER.md#d-02).
- **No environment variables.** No `$VAR` expansion in config values, and no `SOMNUS_*` overrides. [SOURCE-CONFIRMED] grep above; lane B [configuration-findings.md](../_evidence/agent-findings/lane-b-config/configuration-findings.md) section 2.1.
- **No git awareness.** `.gitignore` is not honored. Only `ignore_patterns` is. [SOURCE-CONFIRMED] `:937-947`.
- **No CPU detection.** `max_workers` comes only from config (default 4), capped at the file count (`:1720`).
- **No timezone dependence in data.** Timestamps are UTC (`:525-539`). Run IDs are UTC strftime.

## pycache-clean: path and platform

This section covers the cleaner's environment assumptions.

- The config path defaults to `config.yaml` resolved against the **cwd**. Relative `roots` are also resolved against the cwd. There is no `$VAR` or `~` expansion in `roots`. [VERIFIED] lane B; see [D-14](../DISCOVERY-LEDGER.md#d-14).
- The module docstring promises Windows long-path (`\\?\`) normalization (`src/somnus_debug/pycache_cleaner/core.py:64`). No code implements it: there are no `os.name` or `sys.platform` branches. [SOURCE-CONFIRMED] Not testable here: the sandbox is Linux aarch64.

## run_test.py: environment captured, not detected

This section notes what the harness records about its environment.

The manifest's `environment` block stores `python` (`sys.version`), `python_executable`, `platform` (`platform.platform()`), `cwd`, `project_root`, and `runner`. It records these for provenance and does not branch on them. [VERIFIED] W2-19 (keys `cwd, platform, project_root, python, python_executable, runner`). The project root itself comes from `$PROJECT_ROOT` or the file location, never from git or the cwd. [SOURCE-CONFIRMED] `templates/run_test.py:749`.

## Fieldkit: active environment survey

This section points at the one component that inspects the environment on purpose.

`onboard.py survey()` walks the repo once and records the following:

- Python file counts per top-level directory
- venvs, found by `pyvenv.cfg` under any directory name
- `*.egg-info`
- git-ignored directories containing `.py` (via `git status --ignored`)
- src layout
- existing doctor configs
- test directories
- agent instruction files

`choose_runner()` then picks the interpreter. [VERIFIED] lane F [fieldkit.md](../_evidence/agent-findings/lane-f-ext/fieldkit.md) section 2 (E-O5 found a `tools-env` venv). Its `--python` path resolution follows symlinks out of the venv and rejects normal venv interpreters. [VERIFIED] lane F OB-1. See [D-20](../DISCOVERY-LEDGER.md#d-20).

## Sources

This section lists the code and evidence this page draws on.

- `src/somnus_debug/doctor/core.py:79`, `:525-539`, `:937-947`, `:995-1057`, `:1720`, `:2179-2181`
- `src/somnus_debug/pycache_cleaner/core.py:64`, `:337-355`
- `src/somnus_debug/test_harness/templates/run_test.py:590`, `:615-625`, `:749`
- [lane B configuration-findings.md](../_evidence/agent-findings/lane-b-config/configuration-findings.md); [lane D experiment-log.md](../_evidence/agent-findings/lane-d-cli-tests/experiment-log.md); [lane F fieldkit.md](../_evidence/agent-findings/lane-f-ext/fieldkit.md)
- W2 runs: [verification-results](../11-verification/verification-results.md#w2-runs)
