# File index

This page lists every file in the repository snapshot (baseline `034f46e`, `somnus-debug.zip` uploaded 2026-11-11), excluding `wiki/` and `.git/`. For each file it gives the size, line count, a short hash, what the file is, and where it is documented. Use it to locate a file or to check that a snapshot matches this one.

## Provenance of this table

This section states where the numbers come from and which files are outside version control.

The 46 git-tracked files come from [_evidence/source-files.tsv](../_evidence/source-files.tsv). The three untracked operator files (`.gitignore`, `PLAN.md`, `STATE.md`) were measured for this page with `wc -c`, `wc -l`, and `sha256sum`. [VERIFIED] The local `.gitignore` ignores itself and both operator files, so `git ls-files` does not list them. They are present in the uploaded zip. Generated `__pycache__/` directories under `src/` are excluded: they are gitignored and were not part of the upload (origin discussed in [lane-a architecture §8](../_evidence/agent-findings/lane-a-arch-api/architecture.md)). `docs/OPSEC.md`, referenced elsewhere, does not exist (lead reconciliation).

Kinds: `package-source` and `package-data` ship in the wheel. `root-duplicate-script` files are pre-packaging copies. `fieldkit-*` files are the agent skill. `doc` and `meta` are repository documentation and metadata. `test` is the test suite. `operator (untracked)` files are local operator notes.

## Files

This section is the table, sorted by path.

| Path | Kind | Bytes | Lines | sha256 (12) | What it is | Documented in |
|---|---|---:|---:|---|---|---|
| `.gitignore` | operator (untracked) | 576 | 42 | `b8b9cf2c5e7d` | local ignore file; ignores itself, STATE.md, PLAN.md, state and report artifacts |  |
| `analyze_python_structure.py` | root-duplicate-script | 11925 | 351 | `d4fd24d14b14` | pre-packaging structure script; differs from src only by not using `type_comments=True` | [module-index](module-index.md#root-level-scripts-not-packaged) |
| `assets/somnus-debug-banner.svg` | meta | 2362 | 52 | `7f301d804b7c` | README banner |  |
| `assets/somnus-sovereign-systems-footer.svg` | meta | 1323 | 38 | `5b5fe3b45dfa` | README footer |  |
| `docs/AGENTS_APPENDIX.md` | doc | 4238 | 97 | `55f7f8209048` | agent-facing usage appendix |  |
| `docs/CONTRACT.md` | doc | 4474 | 149 | `adacc84b839c` | single-test harness contract (also shipped as a template) |  |
| `docs/MANUAL.md` | doc | 15172 | 418 | `14720529b08d` | user manual (CLI, config, library §8) |  |
| `docs/PUBLISHING.md` | doc | 6773 | 153 | `7662ad209133` | release checklist |  |
| `docs/Python_Doctor_QUICKSTART.md` | doc | 7331 | 252 | `eac196218437` | doctor quickstart |  |
| `LICENSE` | meta | 1097 | 21 | `e788900647a9` | MIT license text |  |
| `LICENSE.somnus.yaml` | meta | 847 | 34 | `ef2a662f0fa4` | Somnus license metadata companion |  |
| `PLAN.md` | operator (untracked) | 5178 | 46 | `8f01766ff2ad` | operator plan (local, gitignored upstream; not public documentation) |  |
| `pycache_cleaner.py` | root-duplicate-script | 14632 | 375 | `084dc7228a51` | pre-packaging cleaner script; identical to src after header strip | [module-index](module-index.md#root-level-scripts-not-packaged) |
| `pyproject.toml` | meta | 3587 | 101 | `ed2aebb77bc3` | package metadata, dependencies, console scripts, hatch build config |  |
| `python_doctor.yaml` | meta | 2605 | 96 | `f7ee3fbf2885` | repo-root doctor config for another project layout; read by nothing unless passed with `-c` |  |
| `python_production_doctor.py` | root-duplicate-script | 110283 | 2192 | `40e1abdf24cc` | pre-packaging doctor script; lacks the stateless SQLite fallback | [module-index](module-index.md#root-level-scripts-not-packaged) |
| `README.md` | meta | 17501 | 409 | `7b1a1f85e36f` | project README (landing page, quickstart, library section) |  |
| `run_test.py` | root-duplicate-script | 30621 | 859 | `b18849dc39e2` | pre-packaging harness script; identical to the template | [module-index](module-index.md#root-level-scripts-not-packaged) |
| `skills/somnus-debug-fieldkit/README.md` | fieldkit-doc | 3342 | 72 | `ef613cd13f59` | fieldkit skill documentation |  |
| `skills/somnus-debug-fieldkit/references/accelerate-integration.md` | fieldkit-doc | 3761 | 64 | `4b4c9c7c94ef` | fieldkit skill documentation |  |
| `skills/somnus-debug-fieldkit/references/automation.md` | fieldkit-doc | 4068 | 75 | `aca4bb8ffe13` | fieldkit skill documentation |  |
| `skills/somnus-debug-fieldkit/references/commands.md` | fieldkit-doc | 8037 | 139 | `b23dfe0c3b96` | fieldkit skill documentation |  |
| `skills/somnus-debug-fieldkit/references/doctor-loop.md` | fieldkit-doc | 5027 | 100 | `17b51bde6292` | fieldkit skill documentation |  |
| `skills/somnus-debug-fieldkit/references/findings.md` | fieldkit-doc | 11911 | 146 | `a798cb1287d6` | fieldkit skill documentation |  |
| `skills/somnus-debug-fieldkit/references/install.md` | fieldkit-doc | 3750 | 84 | `adc3fefaf9ba` | fieldkit skill documentation |  |
| `skills/somnus-debug-fieldkit/references/onboarding.md` | fieldkit-doc | 5394 | 84 | `29fff440a1a6` | fieldkit skill documentation |  |
| `skills/somnus-debug-fieldkit/references/provenance.md` | fieldkit-doc | 8784 | 88 | `b4b828469177` | fieldkit skill documentation |  |
| `skills/somnus-debug-fieldkit/references/topology.md` | fieldkit-doc | 8034 | 131 | `c8b576098a61` | fieldkit skill documentation |  |
| `skills/somnus-debug-fieldkit/scripts/delta.py` | fieldkit-script | 11587 | 259 | `468f18e00149` | fieldkit script | [module-index](module-index.md#fieldkit-scripts-skillssomnus-debug-fieldkitscripts) |
| `skills/somnus-debug-fieldkit/scripts/onboard.py` | fieldkit-script | 25460 | 534 | `f74a00dd4897` | fieldkit script | [module-index](module-index.md#fieldkit-scripts-skillssomnus-debug-fieldkitscripts) |
| `skills/somnus-debug-fieldkit/scripts/selftest.py` | fieldkit-script | 18257 | 350 | `6b4e88685888` | fieldkit script | [module-index](module-index.md#fieldkit-scripts-skillssomnus-debug-fieldkitscripts) |
| `skills/somnus-debug-fieldkit/SKILL.md` | fieldkit-doc | 9093 | 129 | `40c19a23664f` | fieldkit skill documentation |  |
| `skills/somnus-debug-fieldkit/templates/AGENTS_APPENDIX.md` | fieldkit-doc | 2706 | 55 | `faa06e2a3a88` | fieldkit skill documentation |  |
| `src/somnus_debug/__init__.py` | package-source | 2305 | 59 | `3d6baeeaf0d8` | package root, `__version__` |  |
| `src/somnus_debug/cli.py` | package-source | 4579 | 128 | `a650d21eb9ec` | `somnus-debug` dispatcher | [architecture](../01-system/architecture.md#dispatcher-layer) |
| `src/somnus_debug/doctor/__init__.py` | package-source | 1435 | 45 | `8397200e9e9e` | re-exports `main` |  |
| `src/somnus_debug/doctor/core.py` | package-source | 110654 | 2203 | `379fb2c393e8` | the doctor (config, scan, graph, reports, SQLite state, CLI) | [architecture](../01-system/architecture.md#doctor-layers) |
| `src/somnus_debug/doctor/default_config.yaml` | package-data | 2606 | 99 | `b857bc8bd60b` | reference copy of `init-config` output plus comments; not read at runtime |  |
| `src/somnus_debug/pycache_cleaner/__init__.py` | package-source | 1245 | 43 | `f2345c3d9049` | re-exports `main` |  |
| `src/somnus_debug/pycache_cleaner/core.py` | package-source | 14632 | 375 | `364b030f60eb` | bytecode cleaner (PyYAML) | [public-api](../04-library-api/public-api.md#pycache-cleaner) |
| `src/somnus_debug/structure/__init__.py` | package-source | 1273 | 43 | `921d95d473fe` | re-exports `build_index`, `main` |  |
| `src/somnus_debug/structure/core.py` | package-source | 11945 | 351 | `a732df7f6348` | class/definition indexer | [public-api](../04-library-api/public-api.md#structurebuild_index) |
| `src/somnus_debug/test_harness/__init__.py` | package-source | 863 | 32 | `70bbbb905878` | header only |  |
| `src/somnus_debug/test_harness/scaffold.py` | package-source | 4603 | 129 | `fbea87209ce1` | `init-test-harness` and `scaffold()` | [public-api](../04-library-api/public-api.md#scaffold) |
| `src/somnus_debug/test_harness/templates/__init__.py` | package-source | 863 | 32 | `1843218b0f0d` | resource package marker |  |
| `src/somnus_debug/test_harness/templates/CONTRACT.md` | package-data | 4474 | 149 | `910fd0a49997` | harness contract template |  |
| `src/somnus_debug/test_harness/templates/run_test.py` | package-source | 30621 | 859 | `46cb31569edc` | harness template (project-specific as shipped: cargo gp-cli) |  |
| `STATE.md` | operator (untracked) | 3937 | 41 | `75a3a95a2b21` | operator state notes (local, gitignored upstream); claims the structure crash was fixed, which src/ contradicts |  |
| `tests/test_cli_smoke.py` | test | 6517 | 181 | `04079847a9c6` | 12 CLI smoke tests (10 pass, 2 fail at baseline) | [module-index](module-index.md#tests) |

## Totals

This section summarizes the table by kind.

| Kind | Files | Lines |
|---|---:|---:|
| doc | 5 | 1069 |
| fieldkit-doc | 12 | 1167 |
| fieldkit-script | 3 | 1143 |
| meta | 7 | 751 |
| operator (untracked) | 3 | 129 |
| package-data | 2 | 248 |
| package-source | 12 | 4299 |
| root-duplicate-script | 4 | 3777 |
| test | 1 | 181 |
| **total** | **49** | **12764** |

## Sources

This section lists the data this page was built from.

- [_evidence/source-files.tsv](../_evidence/source-files.tsv)
- `wc -c`, `wc -l`, `sha256sum` over `.gitignore`, `PLAN.md`, `STATE.md` (run for this page)
- [lane-a architecture.md](../_evidence/agent-findings/lane-a-arch-api/architecture.md), [lane-d install-vs-source.md](../_evidence/agent-findings/lane-d-cli-tests/install-vs-source.md)
