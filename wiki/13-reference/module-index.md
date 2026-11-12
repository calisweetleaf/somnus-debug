# Module index

This page lists every Python module in the repository: the installable package, the template it ships, the root-level duplicate scripts, the fieldkit scripts, and the tests. For each one it gives the import name and size, says what it is for, and links to its main documentation. Line counts are [VERIFIED] (`wc -l`, baseline `034f46e`), and agree with `_evidence/source-files.tsv`.

## Package modules (`src/somnus_debug/`)

This section covers the modules that `pip install somnus-debug` installs.

| Import name | File | Lines | Role | Entry point | Documented in |
|---|---|---:|---|---|---|
| `somnus_debug` | `src/somnus_debug/__init__.py` | 59 | `__version__` | none | [public-api](../04-library-api/public-api.md#__version__) |
| `somnus_debug.cli` | `src/somnus_debug/cli.py` | 128 | dispatcher | `somnus-debug` | [architecture](../01-system/architecture.md#dispatcher-layer) |
| `somnus_debug.doctor` | `src/somnus_debug/doctor/__init__.py` | 45 | re-exports `main` | none | [module-map](../01-system/module-map.md) |
| `somnus_debug.doctor.core` | `src/somnus_debug/doctor/core.py` | 2203 | production-readiness doctor | `somnus-doctor` | [architecture](../01-system/architecture.md#doctor-layers), [call-chains](../07-internals/call-chains.md) |
| `somnus_debug.structure` | `src/somnus_debug/structure/__init__.py` | 43 | re-exports `build_index`, `main` | none | [module-map](../01-system/module-map.md) |
| `somnus_debug.structure.core` | `src/somnus_debug/structure/core.py` | 351 | class/definition indexer | `somnus-structure` | [public-api](../04-library-api/public-api.md#structurebuild_index) |
| `somnus_debug.pycache_cleaner` | `src/somnus_debug/pycache_cleaner/__init__.py` | 43 | re-exports `main` | none | [module-map](../01-system/module-map.md) |
| `somnus_debug.pycache_cleaner.core` | `src/somnus_debug/pycache_cleaner/core.py` | 375 | bytecode cleaner (PyYAML) | `somnus-pycache-clean` | [public-api](../04-library-api/public-api.md#pycache-cleaner) |
| `somnus_debug.test_harness` | `src/somnus_debug/test_harness/__init__.py` | 32 | header only | none | [module-map](../01-system/module-map.md) |
| `somnus_debug.test_harness.scaffold` | `src/somnus_debug/test_harness/scaffold.py` | 129 | copies the harness template | via `somnus-debug init-test-harness` | [public-api](../04-library-api/public-api.md#scaffold) |
| `somnus_debug.test_harness.templates` | `src/somnus_debug/test_harness/templates/__init__.py` | 32 | resource package marker | none | [registries-and-discovery](../07-internals/registries-and-discovery.md#template-discovery) |
| (data) `templates/run_test.py` | `src/somnus_debug/test_harness/templates/run_test.py` | 859 | harness template, copied, never imported | `python run_test.py` after scaffolding | [types-and-schemas](../04-library-api/types-and-schemas.md#pycache-and-harness-types) |

Import-time behavior of each module is listed in [module-map](../01-system/module-map.md#module-table). Every symbol: [symbol-index](symbol-index.md).

## Root-level scripts (not packaged)

This section covers the standalone scripts at the repository root. They predate the package and are not part of the wheel.

| File | Lines | Packaged twin | Difference after stripping metadata headers | Evidence |
|---|---:|---|---|---|
| `python_production_doctor.py` | 2192 | `src/somnus_debug/doctor/core.py` | lacks the SQLite-unavailable fallback in `run_scan` | [VERIFIED] [lane-a §7](../_evidence/agent-findings/lane-a-arch-api/architecture.md); [D-28](../DISCOVERY-LEDGER.md#d-28) |
| `analyze_python_structure.py` | 351 | `src/somnus_debug/structure/core.py` | `ast.parse` **without** `type_comments=True`, so it works on stamped files | [VERIFIED]; [D-01](../DISCOVERY-LEDGER.md#d-01) |
| `pycache_cleaner.py` | 375 | `src/somnus_debug/pycache_cleaner/core.py` | identical | [VERIFIED] |
| `run_test.py` | 859 | `src/somnus_debug/test_harness/templates/run_test.py` | identical | [VERIFIED] |

Nothing imports these scripts. [SOURCE-CONFIRMED] grep. README calls them "pending cleanup". [DOCUMENTED-ONLY] `README.md:330`.

## Fieldkit scripts (`skills/somnus-debug-fieldkit/scripts/`)

This section covers the agent-skill scripts shipped in the repository but not in the wheel.

| File | Lines | Role | Exit codes | Evidence |
|---|---:|---|---|---|
| `skills/somnus-debug-fieldkit/scripts/selftest.py` | 350 | contract self-test of the installed CLI | 0 pass, 1 fail, 3 CLI unavailable | [VERIFIED] 29/29 pass ([lane-f fieldkit](../_evidence/agent-findings/lane-f-ext/fieldkit.md)) |
| `skills/somnus-debug-fieldkit/scripts/onboard.py` | 534 | survey a repo, choose a runner, write a profile | 0, 1, 2 coverage failure, 3 CLI unavailable | [VERIFIED] [lane-f fieldkit](../_evidence/agent-findings/lane-f-ext/fieldkit.md); [D-20](../DISCOVERY-LEDGER.md#d-20) |
| `skills/somnus-debug-fieldkit/scripts/delta.py` | 259 | regression gate between two doctor JSON reports | 0 clean, 1 regression, 2 coverage regression, 3 input error | [VERIFIED] [lane-f fieldkit](../_evidence/agent-findings/lane-f-ext/fieldkit.md); [D-21](../DISCOVERY-LEDGER.md#d-21) |

These scripts call the CLI or read its JSON. None of them imports `somnus_debug`. `onboard.py` only checks importability by running `python -c "import somnus_debug"` in a subprocess (`skills/somnus-debug-fieldkit/scripts/onboard.py:228-230`). [SOURCE-CONFIRMED] grep. Exit codes: [VERIFIED] [lane-d exit-codes](../_evidence/agent-findings/lane-d-cli-tests/exit-codes.md) (fieldkit table).

## Tests

This section covers the repository's test module.

| File | Lines | Tests | Result at baseline | Evidence |
|---|---:|---:|---|---|
| `tests/test_cli_smoke.py` | 181 | 12 | 10 passed, 2 failed (`test_structure_tolerates_type_like_comments`, `test_structure_self_index`, both [D-01](../DISCOVERY-LEDGER.md#d-01)) | [VERIFIED] [lane-d test-coverage](../_evidence/agent-findings/lane-d-cli-tests/test-coverage.md); lead reconciliation |

The tests run the CLI in subprocesses (`_run` helper). The only library-level check is the packaged-default-config parity test (`tests/test_cli_smoke.py:112`). [SOURCE-CONFIRMED]

## Sources

This section lists the code and evidence this page rests on.

- `src/somnus_debug/**/*.py`, root `*.py`, `skills/somnus-debug-fieldkit/scripts/*.py`, `tests/test_cli_smoke.py`, `pyproject.toml`, `README.md`
- [_evidence/source-files.tsv](../_evidence/source-files.tsv)
- [lane-a architecture.md](../_evidence/agent-findings/lane-a-arch-api/architecture.md), [lane-d install-vs-source.md](../_evidence/agent-findings/lane-d-cli-tests/install-vs-source.md), [lane-d test-coverage.md](../_evidence/agent-findings/lane-d-cli-tests/test-coverage.md), [lane-d exit-codes.md](../_evidence/agent-findings/lane-d-cli-tests/exit-codes.md), [lane-f fieldkit.md](../_evidence/agent-findings/lane-f-ext/fieldkit.md)
