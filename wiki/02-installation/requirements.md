# Requirements

This page states what somnus-debug 0.1.0 needs to install and run: the declared requirements, the real runtime requirements per tool, and the requirements of the repo-only tooling (tests, fieldkit, harness). Where the docs and the code disagree, the code wins and the disagreement is marked.

## Declared requirements

This section records what the package metadata promises.

| Item | Declared value | Source |
|---|---|---|
| Python | `>=3.10` (classifiers list 3.10, 3.11, 3.12) | `pyproject.toml` `[project]`; installed `METADATA` shows `Requires-Python: >=3.10` [VERIFIED] W2-02 |
| Runtime dependency | `pyyaml` (unpinned) | `pyproject.toml` `dependencies`; `METADATA` `Requires-Dist: pyyaml` [VERIFIED] W2-02 |
| Optional `dev` extra | `pytest>=7` | `pyproject.toml` `[project.optional-dependencies]` |
| Build backend | `hatchling` | `pyproject.toml` `[build-system]` |
| OS | "OS Independent" classifier | `pyproject.toml` |

## Real runtime requirements per tool

This section says what each tool imports in practice, which differs from the README's "doctor and structure are stdlib-only".

| Tool / entry | Needs PyYAML? | Evidence |
|---|---|---|
| `somnus-debug <any subcommand>` (dispatcher) | **yes**. `cli.py` imports all four tools at load, including the PyYAML-importing pycache cleaner | [SOURCE-CONFIRMED] `src/somnus_debug/cli.py:55-58`, `src/somnus_debug/pycache_cleaner/core.py:150-154`. [VERIFIED] W2-05: under Python 3.13.5 without PyYAML, `python -m somnus_debug.cli doctor --help` exits 1 with `ModuleNotFoundError: No module named 'yaml'` |
| `somnus-doctor`, `python -m somnus_debug.doctor.core` | no; stdlib only, with its own YAML-subset parser | [VERIFIED] W2-05: under the same PyYAML-less 3.13, `-m somnus_debug.doctor.core --help` exits 0, and a scan of the quickstart fixture gives `files=3, issues=7, critical=0, serious=2`, exit 1, matching 3.12 |
| `somnus-structure`, `python -m somnus_debug.structure.core` | no | [VERIFIED] W2-05 (exit 0 under PyYAML-less 3.13) |
| `somnus-pycache-clean` | yes | [SOURCE-CONFIRMED] `pycache_cleaner/core.py:150-154` |
| `init-test-harness` | via the dispatcher, yes; the library `scaffold()` alone, no | [SOURCE-CONFIRMED] `src/somnus_debug/test_harness/scaffold.py:47-53` imports only the stdlib |

Doctor additionally needs a working `sqlite3` module for state. Without it, `scan` still works (with a warning), but `history` and `rollback` do not. [VERIFIED] lane D D39-D41. See [D-28](../DISCOVERY-LEDGER.md#d-28).

The README claim "Zero runtime dependencies beyond `pyyaml`, and that's only for `pycache-clean`" (`README.md:176-177`) holds only for the per-tool scripts. [DISCREPANCY] See [D-13](../DISCOVERY-LEDGER.md#d-13).

## Minimum Python version in practice

This section checks the `>=3.10` claim against the code and real interpreters.

- Doctor uses `sys.stdlib_module_names` (added in 3.10) for stdlib detection and `typing.TypeAlias` (3.10). It defines its own `UTC = dt.timezone.utc` rather than importing `datetime.UTC` (3.11+). [SOURCE-CONFIRMED] `src/somnus_debug/doctor/core.py:72`, `:79`, `:1001`.
- Python 3.10.22, 3.11.17, 3.12.15, and 3.13.5 all ran the tools in this wave. [VERIFIED] W2-06, W2-05; details in [compatibility](compatibility.md).
- Below 3.10 has not been tried. `sys.stdlib_module_names` would be missing. Because of the `getattr(..., frozenset())` fallback, stdlib imports would then be misclassified rather than crashing. [HYPOTHESIS] from `:1001`.

## Requirements of the repo-only tooling

This section covers what you need beyond the wheel to run tests, the fieldkit, or the harness.

| Tool | Requires | Evidence |
|---|---|---|
| `tests/test_cli_smoke.py` | pytest; PyYAML in the interpreter running pytest (tests call `sys.executable -m somnus_debug.cli`); a repo checkout (they set `PYTHONPATH=<repo>/src`) | [SOURCE-CONFIRMED] `tests/test_cli_smoke.py:49-61`. [VERIFIED] W2-03 |
| fieldkit `selftest.py`, `onboard.py`, `delta.py` | Python 3 stdlib; a `somnus-debug` CLI on PATH or `--python` pointing at an interpreter **with somnus-debug installed** | [VERIFIED] W2-04; lane D F01-F03; lane F [fieldkit.md](../_evidence/agent-findings/lane-f-ext/fieldkit.md) |
| scaffolded `run_test.py` | stdlib only for the harness machinery. The shipped default test needs `cargo` and a `gp-cli` crate, and fails without them | [VERIFIED] W2-19 |

## Disk and write requirements

This section lists where the tools must be able to write, because write failures turn into exit 4 or tracebacks.

| Tool | Must be able to write |
|---|---|
| doctor (any) | cwd (`production_doctor.log`) |
| doctor scan | the report paths (default: project root); with state on, `<root>/.python_doctor/` |
| doctor self-check | the installed `doctor/` package directory, unless `-o`, `--json-output`, and `--no-state` are given |
| pycache-clean | the configured roots (it deletes there); `log_file` if set |
| init-test-harness | the target directory |
| run_test.py | `<project_root>/test-runs/` or `$SINGLE_TEST_OUTPUT_DIR` |

[VERIFIED] lane D D14, D43; W2-10, W2-11, W2-19. See [D-10](../DISCOVERY-LEDGER.md#d-10).

## Sources

This section lists the code and evidence this page draws on.

- `pyproject.toml`; installed `somnus_debug-0.1.0.dist-info/METADATA`
- `src/somnus_debug/cli.py:55-58`; `src/somnus_debug/pycache_cleaner/core.py:150-154`; `src/somnus_debug/doctor/core.py:72`, `:79`, `:1001`; `src/somnus_debug/test_harness/scaffold.py:47-53`
- `README.md:176-177`; `tests/test_cli_smoke.py:49-61`
- [lane A architecture.md](../_evidence/agent-findings/lane-a-arch-api/architecture.md) section 1; [lane D install-vs-source.md](../_evidence/agent-findings/lane-d-cli-tests/install-vs-source.md) section 6
- W2 runs: [verification-results](../11-verification/verification-results.md#w2-runs)
