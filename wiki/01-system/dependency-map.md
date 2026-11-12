# Dependency map

This page lists what `somnus-debug` depends on: the Python version, third-party packages, the standard-library modules each tool imports, and the environment facts that change results. Install-level detail is in [02-installation/requirements](../02-installation/requirements.md).

## Declared dependencies

This section restates what `pyproject.toml` declares.

| Item | Value |
|---|---|
| `requires-python` | `>=3.10` |
| runtime `dependencies` | `["pyyaml"]` (no version pin) |
| optional `dev` | `["pytest>=7"]` |
| build backend | `hatchling` |

[SOURCE-CONFIRMED] `pyproject.toml`. This wiki was verified on Python 3.12.15 with PyYAML 6.0.2 [VERIFIED] (`python3 --version`, `yaml.__version__`). The classifiers also claim Python 3.10 and 3.11; neither was tested. [UNVERIFIED]

## Third-party dependency per tool

This section shows that only one tool needs PyYAML, but the dispatcher makes all of them need it.

| Tool | Needs PyYAML directly | Needs PyYAML when run through `somnus-debug` | Evidence |
|---|---|---|---|
| doctor | no (it has its own YAML-subset parser) | yes | [VERIFIED] [D-13](../DISCOVERY-LEDGER.md#d-13) |
| structure | no | yes | [VERIFIED] |
| pycache-clean | yes: `import yaml` at module load, `yaml.safe_load` | yes | [SOURCE-CONFIRMED] `src/somnus_debug/pycache_cleaner/core.py:150-154`, `:173` |
| init-test-harness | no | yes | [SOURCE-CONFIRMED] |

Without PyYAML installed:

- `somnus-debug structure --help` and `somnus-debug doctor --help` exit 1 with `ModuleNotFoundError`.
- `somnus-doctor --help` exits 0.

[VERIFIED] [lane-a architecture §1](../_evidence/agent-findings/lane-a-arch-api/architecture.md), in a `--no-deps` venv.

## Standard-library usage

This section lists the stdlib modules each tool imports, for anyone vendoring or auditing them.

| Module | stdlib imports | Import block |
|---|---|---|
| `doctor/core.py` | `argparse`, `ast`, `concurrent.futures`, `datetime`, `fnmatch`, `hashlib`, `html`, `importlib.util`, `io`, `json`, `logging`, `os`, `re`, `shutil`, `sqlite3`, `sys`, `tokenize`, `collections`, `dataclasses`, `enum`, `pathlib`, `typing` | `src/somnus_debug/doctor/core.py:49-72` |
| `structure/core.py` | `argparse`, `ast`, `re`, `sys`, `pathlib`, `typing` | `src/somnus_debug/structure/core.py:48-55` |
| `pycache_cleaner/core.py` | `argparse`, `fnmatch`, `logging`, `os`, `shutil`, `sys`, `dataclasses`, `pathlib`, `typing` | `src/somnus_debug/pycache_cleaner/core.py:140-154` |
| `test_harness/scaffold.py` | `argparse`, `sys`, `importlib.resources`, `pathlib`, `typing` | `src/somnus_debug/test_harness/scaffold.py:47-53` |
| `cli.py` | `sys`, `typing` | `src/somnus_debug/cli.py:49-58` |

[SOURCE-CONFIRMED] each import block.

`doctor/core.py` imports `sqlite3` at the top level (`src/somnus_debug/doctor/core.py:65`). [SOURCE-CONFIRMED] Two consequences follow:

- A Python build without `_sqlite3` cannot import the doctor at all. [HYPOTHESIS]
- The stateless fallback cannot help in that case. It covers an unusable database file, not a missing module.

## Version-sensitive stdlib features

This section names the stdlib features whose presence depends on the Python version.

- **`sys.stdlib_module_names` (3.10+).** It decides the `standard_library` classification. The code reads it with `getattr(..., frozenset())`, unioned with `sys.builtin_module_names`. [SOURCE-CONFIRMED] `src/somnus_debug/doctor/core.py:1001`
- **`ast.Match` (3.10+).** It is referenced in `cyclomatic_complexity`, so the doctor cannot run on 3.9. [SOURCE-CONFIRMED] `src/somnus_debug/doctor/core.py:1427`
- **`ast.unparse` (3.9+).** Both the doctor and the structure indexer use it throughout. [SOURCE-CONFIRMED]
- **`X | Y` annotations.** These are safe at definition time because every module uses `from __future__ import annotations`. The `TypeAlias` assignments in the doctor (`src/somnus_debug/doctor/core.py:74-77`) are evaluated eagerly and need 3.10+. [SOURCE-CONFIRMED]

## Environment dependencies that change results

This section lists external facts that change doctor output with no configuration change.

| Factor | Effect | Evidence |
|---|---|---|
| Which interpreter runs the doctor | `third_party` vs `missing` comes from `importlib.util.find_spec` in that interpreter (`src/somnus_debug/doctor/core.py:1050-1055`) | [VERIFIED] [D-26](../DISCOVERY-LEDGER.md#d-26) |
| cwd on `sys.path` | modules importable from the cwd count as third-party | [VERIFIED] [D-26](../DISCOVERY-LEDGER.md#d-26) |
| `PYTHONPATH=src` in a src-layout repo | the project's own imports resolve as `third_party`, and `dependency_cycles` drops to 0 | [VERIFIED] [D-22](../DISCOVERY-LEDGER.md#d-22) |
| cwd | location of the log, of relative `-c`/`-o` paths, and of pycache roots | [VERIFIED] [D-10](../DISCOVERY-LEDGER.md#d-10), [D-14](../DISCOVERY-LEDGER.md#d-14) |

Environment variables: the package reads none. The scaffolded `run_test.py` reads `PROJECT_ROOT` and `SINGLE_TEST_OUTPUT_DIR`. [SOURCE-CONFIRMED] [lane-b configuration-findings §2.5](../_evidence/agent-findings/lane-b-config/configuration-findings.md).

## Sources

This section lists the code, evidence files, and probes this page rests on.

- `pyproject.toml`, plus the import blocks listed above
- `src/somnus_debug/doctor/core.py:65`, `:74-77`, `:1001`, `:1050-1055`, `:1427`
- [lane-a architecture.md §1](../_evidence/agent-findings/lane-a-arch-api/architecture.md)
- [lane-b configuration-findings.md](../_evidence/agent-findings/lane-b-config/configuration-findings.md)
- [lane-f compositions.md](../_evidence/agent-findings/lane-f-ext/compositions.md) (C7)
