# Source Inventory

This page records exactly what was investigated: the uploaded tree, its identity, and every file with its size and hash prefix.

## Identity

This section fixes the version and provenance of the investigated code.

- Upload: `somnus-debug.zip`, 193,777 bytes, received 2026-11-11 18:08 CST; unpacked and committed as baseline `034f46e` in a private workshop git repo (the upload had no `.git`).
- Package: `somnus-debug` 0.1.0 (`pyproject.toml`, `src/somnus_debug/__init__.py:57`), hatchling build, `requires-python >=3.10`, runtime dependency `pyyaml`, optional `dev = [pytest>=7]`.
- Console scripts: `somnus-debug`, `somnus-doctor`, `somnus-structure`, `somnus-pycache-clean` (`pyproject.toml [project.scripts]`). No `somnus-init-test-harness`.
- Sandbox runtime: Python 3.12.15, PyYAML 6.0.2 system-wide, no pytest system-wide (lanes used /tmp venvs).
- Installed vs source vs PyPI: no somnus-debug was installed in the sandbox; lanes installed the repo non-editable into /tmp venvs. PyPI 0.1.0 was downloaded (not installed) and diffed: code identical to `src/` after header stripping, `default_config.yaml` differs ([install-vs-source](agent-findings/lane-d-cli-tests/install-vs-source.md)). Daeron's own `~/.local/bin/somnus-debug` (per STATE.md) was not reachable.
- Every tracked file carries a `somnus:metadata:v2` header with its own artifact URN; root duplicates and `src/` copies carry different URNs.

## Source-of-truth locations

This section says which copy of each tool is authoritative.

| Tool | Authoritative (packaged) | Root duplicate | Difference |
|---|---|---|---|
| doctor | `src/somnus_debug/doctor/core.py` (2203 lines) | `python_production_doctor.py` (2192) | root lacks SQLite fallback in `run_scan` |
| structure | `src/somnus_debug/structure/core.py` | `analyze_python_structure.py` | root drops `type_comments=True` (works on stamped files) |
| pycache-clean | `src/somnus_debug/pycache_cleaner/core.py` | `pycache_cleaner.py` | headers only |
| harness template | `src/somnus_debug/test_harness/templates/run_test.py` | `run_test.py` | headers only |
| doctor config | `src/somnus_debug/doctor/default_config.yaml` (reference only) | `python_doctor.yaml` (read by nothing) | headers only |

## Files

This section lists all 46 tracked files from the upload; `wiki/` is excluded.

| Path | Kind | Lines | Bytes | sha256 (12) |
|---|---|---|---|---|
| `LICENSE` | meta | 21 | 1097 | `e788900647a9` |
| `LICENSE.somnus.yaml` | meta | 34 | 847 | `ef2a662f0fa4` |
| `README.md` | meta | 409 | 17501 | `7b1a1f85e36f` |
| `analyze_python_structure.py` | root-duplicate-script | 351 | 11925 | `d4fd24d14b14` |
| `assets/somnus-debug-banner.svg` | meta | 52 | 2362 | `7f301d804b7c` |
| `assets/somnus-sovereign-systems-footer.svg` | meta | 38 | 1323 | `5b5fe3b45dfa` |
| `docs/AGENTS_APPENDIX.md` | doc | 97 | 4238 | `55f7f8209048` |
| `docs/CONTRACT.md` | doc | 149 | 4474 | `adacc84b839c` |
| `docs/MANUAL.md` | doc | 418 | 15172 | `14720529b08d` |
| `docs/PUBLISHING.md` | doc | 153 | 6773 | `7662ad209133` |
| `docs/Python_Doctor_QUICKSTART.md` | doc | 252 | 7331 | `eac196218437` |
| `pycache_cleaner.py` | root-duplicate-script | 375 | 14632 | `084dc7228a51` |
| `pyproject.toml` | meta | 101 | 3587 | `ed2aebb77bc3` |
| `python_doctor.yaml` | meta | 96 | 2605 | `f7ee3fbf2885` |
| `python_production_doctor.py` | root-duplicate-script | 2192 | 110283 | `40e1abdf24cc` |
| `run_test.py` | root-duplicate-script | 859 | 30621 | `b18849dc39e2` |
| `skills/somnus-debug-fieldkit/README.md` | fieldkit-doc | 72 | 3342 | `ef613cd13f59` |
| `skills/somnus-debug-fieldkit/SKILL.md` | fieldkit-doc | 129 | 9093 | `40c19a23664f` |
| `skills/somnus-debug-fieldkit/references/accelerate-integration.md` | fieldkit-doc | 64 | 3761 | `4b4c9c7c94ef` |
| `skills/somnus-debug-fieldkit/references/automation.md` | fieldkit-doc | 75 | 4068 | `aca4bb8ffe13` |
| `skills/somnus-debug-fieldkit/references/commands.md` | fieldkit-doc | 139 | 8037 | `b23dfe0c3b96` |
| `skills/somnus-debug-fieldkit/references/doctor-loop.md` | fieldkit-doc | 100 | 5027 | `17b51bde6292` |
| `skills/somnus-debug-fieldkit/references/findings.md` | fieldkit-doc | 146 | 11911 | `a798cb1287d6` |
| `skills/somnus-debug-fieldkit/references/install.md` | fieldkit-doc | 84 | 3750 | `adc3fefaf9ba` |
| `skills/somnus-debug-fieldkit/references/onboarding.md` | fieldkit-doc | 84 | 5394 | `29fff440a1a6` |
| `skills/somnus-debug-fieldkit/references/provenance.md` | fieldkit-doc | 88 | 8784 | `b4b828469177` |
| `skills/somnus-debug-fieldkit/references/topology.md` | fieldkit-doc | 131 | 8034 | `c8b576098a61` |
| `skills/somnus-debug-fieldkit/scripts/delta.py` | fieldkit-script | 259 | 11587 | `468f18e00149` |
| `skills/somnus-debug-fieldkit/scripts/onboard.py` | fieldkit-script | 534 | 25460 | `f74a00dd4897` |
| `skills/somnus-debug-fieldkit/scripts/selftest.py` | fieldkit-script | 350 | 18257 | `6b4e88685888` |
| `skills/somnus-debug-fieldkit/templates/AGENTS_APPENDIX.md` | fieldkit-doc | 55 | 2706 | `faa06e2a3a88` |
| `src/somnus_debug/__init__.py` | package-source | 59 | 2305 | `3d6baeeaf0d8` |
| `src/somnus_debug/cli.py` | package-source | 128 | 4579 | `a650d21eb9ec` |
| `src/somnus_debug/doctor/__init__.py` | package-source | 45 | 1435 | `8397200e9e9e` |
| `src/somnus_debug/doctor/core.py` | package-source | 2203 | 110654 | `379fb2c393e8` |
| `src/somnus_debug/doctor/default_config.yaml` | package-data | 99 | 2606 | `b857bc8bd60b` |
| `src/somnus_debug/pycache_cleaner/__init__.py` | package-source | 43 | 1245 | `f2345c3d9049` |
| `src/somnus_debug/pycache_cleaner/core.py` | package-source | 375 | 14632 | `364b030f60eb` |
| `src/somnus_debug/structure/__init__.py` | package-source | 43 | 1273 | `921d95d473fe` |
| `src/somnus_debug/structure/core.py` | package-source | 351 | 11945 | `a732df7f6348` |
| `src/somnus_debug/test_harness/__init__.py` | package-source | 32 | 863 | `70bbbb905878` |
| `src/somnus_debug/test_harness/scaffold.py` | package-source | 129 | 4603 | `fbea87209ce1` |
| `src/somnus_debug/test_harness/templates/CONTRACT.md` | package-data | 149 | 4474 | `910fd0a49997` |
| `src/somnus_debug/test_harness/templates/__init__.py` | package-source | 32 | 863 | `1843218b0f0d` |
| `src/somnus_debug/test_harness/templates/run_test.py` | package-source | 859 | 30621 | `46cb31569edc` |
| `tests/test_cli_smoke.py` | test | 181 | 6517 | `04079847a9c6` |

## Sources

- [source-files.tsv](source-files.tsv), [source-coverage.tsv](source-coverage.tsv)
