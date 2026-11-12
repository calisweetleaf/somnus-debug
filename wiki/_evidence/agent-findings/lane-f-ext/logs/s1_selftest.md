# somnus-debug fieldkit selftest (/tmp/lane-f/venv/bin/python -m somnus_debug.cli)

| Result | Check | Observed | Reference |
|---|---|---|---|
| PASS | --version answers | 0.1.0 | `references/install.md` |
| PASS | doctor scan --help flags | all documented flags present | `references/commands.md` |
| PASS | doctor init-config --help flags | all documented flags present | `references/commands.md` |
| PASS | doctor history --help flags | all documented flags present | `references/commands.md` |
| PASS | doctor rollback --help flags | all documented flags present | `references/commands.md` |
| PASS | doctor self-check --help flags | all documented flags present | `references/commands.md` |
| PASS | structure --help flags | all documented flags present | `references/commands.md` |
| PASS | pycache-clean --help flags | all documented flags present | `references/commands.md` |
| PASS | init-test-harness --help flags | all documented flags present | `references/commands.md` |
| PASS | init-config include is *.py | found | `references/commands.md` |
| PASS | init-config state_dir .python_doctor | found | `references/commands.md` |
| PASS | init-config gate serious | found | `references/commands.md` |
| PASS | zero-file scan exits 0 | exit=0 files=0 | `SKILL.md sharp edges` |
| PASS | serious finding exits 1 | exit=1 categories=['stubs', 'suspicious_short_functions'] | `references/commands.md` |
| PASS | critical (syntax) exits 2 | exit=2 | `references/commands.md` |
| PASS | invalid config exits 4 | exit=4 | `references/commands.md` |
| PASS | doctor writes production_doctor.log to cwd (even --help) | present | `SKILL.md sharp edges` |
| PASS | scan without -o writes report into project root | present | `SKILL.md sharp edges` |
| PASS | src layout: own imports flagged missing without PYTHONPATH, resolved with it | plain=True with_pythonpath=False | `references/findings.md#missing_imports` |
| PASS | uninstalled third-party import -> missing_imports | ['missing_imports', 'unused_imports'] | `references/findings.md#missing_imports` |
| PASS | silent_failures: log.warning flagged, logger.exception not | flagged=['warns'] | `references/findings.md#silent_failures` |
| PASS | abstractmethod with ... flagged as stub | [('stubs', 'Base.run')] | `references/findings.md#stubs` |
| PASS | property setter flagged as duplicate_definitions | [('duplicate_definitions', 'Box.value')] | `references/findings.md#duplicate_definitions` |
| PASS | test_gaps is not emitted by 0.1.0 (sentinel) | not emitted | `references/findings.md#test_gaps` |
| PASS | todos match case-insensitively ("temp" in prose) | ['todos'] | `references/findings.md#todos` |
| PASS | structure prints index to stdout and writes nothing | exit=0 | `references/commands.md` |
| PASS | pycache-clean --dry-run deletes nothing | exit=0 survived=True | `references/commands.md` |
| PASS | pycache exclude 'node_modules/*' does not exclude (names only) | path-style exclude ignored | `references/commands.md` |
| PASS | init-test-harness writes run_test.py + CONTRACT.md, refuses overwrite | first=0 second=1 | `references/commands.md` |

29/29 passed.
exit=0
