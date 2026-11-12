# Terminology

This page maps terms used in the existing docs and operator notes to the names the code uses, so readers can move between them.

## Doc term to code name

This section resolves naming drift between docs and source.

| Term in docs or notes | Code name | Note |
|---|---|---|
| Python Doctor, production doctor | `somnus_debug.doctor.core` | Same tool; root duplicate is `python_production_doctor.py` |
| structure analyzer, class/def index | `somnus_debug.structure.core` | Root duplicate `analyze_python_structure.py` |
| pycache cleaner | `somnus_debug.pycache_cleaner.core` | CLI name `pycache-clean` |
| test harness, CONTRACT harness | `somnus_debug.test_harness` | CLI name `init-test-harness`; no standalone script |
| test gaps | category `test_gaps`, flag `detect_test_gaps` | Never emitted ([D-05](../DISCOVERY-LEDGER.md#d-05)) |
| state, history | `StateStore`, `.python_doctor/state.sqlite3` | |
| fieldkit loop | `onboard.py` then `delta.py` with dispositions | |
| somnus metadata header | `# somnus:metadata:v2` ... `# somnus:end` comment block | Triggers [D-01](../DISCOVERY-LEDGER.md#d-01) in structure |

See the [glossary](../GLOSSARY.md) for definitions.
