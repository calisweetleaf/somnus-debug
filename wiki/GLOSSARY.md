# Glossary

This glossary defines the terms the wiki uses, with the source location that gives each one its meaning in this codebase.

## Tool and package terms

This section defines the names of the parts of somnus-debug.

| Term | Meaning | Source |
|---|---|---|
| doctor | AST-based production-readiness scanner (`somnus-debug doctor`, `somnus-doctor`) | `src/somnus_debug/doctor/core.py` |
| structure | Single-file class/definition indexer with line spans | `src/somnus_debug/structure/core.py` |
| pycache-clean | Config-driven remover of `__pycache__`, `*.pyc`, `*.pyo` | `src/somnus_debug/pycache_cleaner/core.py` |
| init-test-harness | Scaffolder that copies `run_test.py` and `CONTRACT.md` into a target directory | `src/somnus_debug/test_harness/scaffold.py` |
| dispatcher | `somnus-debug` console script that routes argv to each tool's own `main()` | `src/somnus_debug/cli.py` |
| root duplicate | Pre-packaging copy of a tool at the repo root, excluded from the build | `python_production_doctor.py` etc. |
| fieldkit | Agent skill in `skills/somnus-debug-fieldkit/` with `onboard.py`, `delta.py`, `selftest.py` and references; ships in the repo, not the wheel | `skills/somnus-debug-fieldkit/SKILL.md` |

## Doctor terms

This section defines doctor's own vocabulary.

| Term | Meaning | Source |
|---|---|---|
| category | Named finding type (e.g. `silent_failures`); 20 configured, 19 emitted | `doctor/core.py:480-500` |
| severity | One of critical, serious, minor, info; per-category, unmapped categories default minor | `doctor/core.py:792-794` |
| severity gate | `severity_exit_level`; the lowest severity that makes the scan exit non-zero | `doctor/core.py:477` |
| score | `max(0, 100 - 20*critical - 8*serious - 2*minor - info)` | `doctor/core.py:1772` |
| run id | Per-second UTC timestamp identifying a scan | `doctor/core.py:532` |
| state store | SQLite database `<root>/.python_doctor/state.sqlite3` with `runs`, `file_snapshots`, `report_aliases` | `doctor/core.py:1916-2010` |
| latest alias | `report_aliases` row named `latest`; what rollback moves | `doctor/core.py:1977, 2006` |
| previous index | `{relative_path: file_hash}` from the last run, used to mark changed files | `doctor/core.py:2066-2077` |
| mini-YAML parser | `MinimalYamlParser`, the zero-dependency YAML subset reader | `doctor/core.py:596-725` |

## Fieldkit terms

This section defines the fieldkit's vocabulary.

| Term | Meaning | Source |
|---|---|---|
| profile | `.somnus-debug/PROFILE.md` written by `onboard.py --apply` | `skills/somnus-debug-fieldkit/scripts/onboard.py` |
| baseline | A doctor JSON report recorded as the reference for later deltas | `onboard.py --baseline`, `delta.py` |
| delta | Comparison of baseline and latest report: new, persisting, fixed findings, coverage drop | `skills/somnus-debug-fieldkit/scripts/delta.py` |
| disposition | Reviewed finding (category, file, symbol?, reason) that `delta.py` excuses | `delta.py:240` |
| stale disposition | A disposition that matches nothing in the latest report | `delta.py` |

## Evidence terms

This section defines the evidence classes used throughout the wiki.

| Term | Meaning |
|---|---|
| VERIFIED | Executed in a controlled /tmp environment; command and result recorded |
| SOURCE-CONFIRMED | Read in source at a cited line; not exercised |
| DOCUMENTED-ONLY | Claimed by existing docs; no implementation found |
| CONDITIONAL | Depends on settings, dependencies, platform, or runtime |
| DISCREPANCY | Source, docs, tests, or installed runtime disagree |
| UNVERIFIED | Evidence insufficient |
| HYPOTHESIS | Exploratory possibility, not a capability claim |

See also [terminology](13-reference/terminology.md).
