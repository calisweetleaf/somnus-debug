# Tested behaviors

This page lists every behavior that has an automated check (repo pytest or fieldkit selftest) and its current status. It then lists the behaviors this wiki verified by execution without any automated check. Untested behaviors are on [untested-behaviors](untested-behaviors.md).

## Repo smoke suite: 12 tests

This section gives the status of each shipped pytest test on 0.1.0.

Command (W2-03, cwd `/tmp/w2/repo-copy`, exit 1): `python -m pytest -p no:cacheprovider tests/ -v`

| # | Test | Asserts | Status |
|---:|---|---|---|
| 1 | `test_top_level_help` | rc 0; stdout mentions `somnus-debug` and `doctor` | PASS |
| 2 | `test_unknown_command_exits_nonzero` | rc 2 | PASS |
| 3 | `test_structure_help` | rc 0; "Index Python classes" | PASS |
| 4 | `test_doctor_help` | rc 0 | PASS |
| 5 | `test_doctor_scan_degrades_when_sqlite_state_is_unavailable` | state DB path is a directory -> stderr warning, rc 0, both root reports exist | PASS |
| 6 | `test_packaged_default_config_matches_init_config` | `default_config.yaml` equals `init-config` output after header strip | PASS |
| 7 | `test_structure_tolerates_type_like_comments` | a file with `# type:`-shaped header lines indexes with rc 0 | **FAIL**: `error: invalid syntax (header.py, line 3)`, rc 2 |
| 8 | `test_pycache_clean_help` | rc 0 | PASS |
| 9 | `test_init_test_harness_help` | rc 0 | PASS |
| 10 | `test_structure_self_index` | structure on its own `core.py`, rc 0 | **FAIL**: `error: invalid syntax (core.py, line 10)`, rc 2 |
| 11 | `test_init_test_harness_scaffolds_into_tmp` | `run_test.py` and `CONTRACT.md` written | PASS |
| 12 | `test_init_test_harness_refuses_overwrite_without_force` | rc 1; file unchanged | PASS (one assertion inside is a no-op `... or True`) |

Totals: **10 passed, 2 failed.** Identical on Python 3.10.22, 3.11.17, and 3.12.15 (W2-06). Lane D got the same result independently ([test-coverage.md](../_evidence/agent-findings/lane-d-cli-tests/test-coverage.md)). Both failures have one cause, `type_comments=True` at `src/somnus_debug/structure/core.py:210` ([D-01](../DISCOVERY-LEDGER.md#d-01)). `STATE.md` claims "smoke 12/12" for 2026-11-05. [DISCREPANCY]

## Fieldkit selftest: 29 checks

This section lists the 29 contract checks, all passing against the installed CLI.

Command (W2-04, cwd outside the repo): `env PATH=<venv>/bin:/usr/bin:/bin python3 skills/somnus-debug-fieldkit/scripts/selftest.py`. Exit 0, `29/29 passed.` Re-run while writing this page (W2-27): 29/29, exit 0.

| # | Check | Status |
|---:|---|---|
| 1 | `--version` answers | PASS |
| 2-9 | `--help` flags of doctor scan, init-config, history, rollback, self-check, structure, pycache-clean, init-test-harness | PASS (8 checks) |
| 10 | init-config include is `*.py` | PASS |
| 11 | init-config `state_dir` `.python_doctor` | PASS |
| 12 | init-config gate `serious` | PASS |
| 13 | zero-file scan exits 0 | PASS |
| 14 | serious finding exits 1 | PASS |
| 15 | critical (syntax) exits 2 | PASS |
| 16 | invalid config exits 4 | PASS |
| 17 | doctor writes `production_doctor.log` to cwd (even `--help`) | PASS |
| 18 | scan without `-o` writes the report into the project root | PASS |
| 19 | src layout: own imports flagged missing without `PYTHONPATH`, resolved with it | PASS (FAILs under `--python` + `PYTHONPATH=src`, a harness artifact) |
| 20 | uninstalled third-party import -> `missing_imports` | PASS |
| 21 | `silent_failures`: `log.warning` flagged, `logger.exception` not | PASS |
| 22 | `abstractmethod` with `...` flagged as stub | PASS |
| 23 | property setter flagged as `duplicate_definitions` | PASS |
| 24 | `test_gaps` not emitted by 0.1.0 (sentinel) | PASS |
| 25 | todos match case-insensitively | PASS |
| 26 | structure prints the index to stdout and writes nothing | PASS |
| 27 | pycache-clean `--dry-run` deletes nothing | PASS |
| 28 | pycache exclude `node_modules/*` does not exclude (names only) | PASS |
| 29 | init-test-harness writes both files and refuses to overwrite | PASS |

Checks 21-24 and 28 pin **defects** as current behavior (name sensitivity, false positives, the dead `test_gaps`, path-style excludes). A fix to any of them will turn its check red. That is by design: the selftest guards the docs, not correctness. See [D-05](../DISCOVERY-LEDGER.md#d-05), [D-07](../DISCOVERY-LEDGER.md#d-07), [D-14](../DISCOVERY-LEDGER.md#d-14).

## Behaviors verified by execution but not by any automated check

This section lists what the wiki lanes and W2 verified by hand. These rest on recorded runs rather than on a test that someone will re-run.

| Area | Behavior | Evidence |
|---|---|---|
| doctor gates | `none`/`critical`/`serious`/`minor`/`info` exits, including `minor`/`info` returning 1 with criticals | W2-08; lane D D26_* |
| doctor config | no auto-discovery; partial merge; unknown keys accepted; malformed YAML accepted; JSON accepted; unquoted `none` -> 4 | lane D D27-D34; W2-08; [minimal-examples](../03-getting-started/minimal-examples.md) |
| doctor exit 4 causes | 9+ distinct `DoctorError` causes | lane D; W2-08, W2-16, W2-21 |
| doctor exit 5 | `RecursionError` on the serial path | lane D D44; [execution-model](../01-system/execution-model.md) |
| state | persist, history, `--limit`, rollback, unknown run ID, same-second collision, corrupt DB, `history` creating the DB | W2-11, W2-14, W2-16, W2-17; lane D D06-D13, D39-D41 |
| outputs | `-o`/`--json-output` independence, `-o x.json` collision, parents created, the JSON schema | W2-12, W2-23; lane D D18, D43 |
| logging | log in cwd, 0 bytes on success, `-v`/`--verbose` no-op, host handler replacement | W2-07, W2-20 |
| self-check | writes into the package dir; 17 serious on itself | lane D D14, D15 |
| detectors | per-category triggers and false positives on fixtures (20 categories) | lane D detector table ([command-reference.md](../_evidence/agent-findings/lane-d-cli-tests/command-reference.md) section 2); lane A |
| import resolution | interpreter, `PYTHONPATH`, and invocation-form dependence | lane D D05; W2-14, W2-25 |
| structure | all flags; error paths; stamped crash; non-UTF-8 traceback; `-o` silent | lane D S01-S17; W2-09, W2-15, W2-22, W2-26 |
| pycache-clean | real deletion; excludes; missing root exits 0; config errors; unknown-key log loss; type coercions; max-depth | W2-18; lane D P01-P10; lane B |
| harness | placement trap; default FAIL; PASS after edit; template's own doctor findings | W2-19; lane D H01-H10; lane F C5 |
| fieldkit | onboard and delta exit codes and edge cases | lane D O01-O08, T01-T08; lane F |
| compositions | doctor JSON -> delta gate, ratchet, rollback as baseline, structure slices | lane F C1-C7; W2-14/W2-17 |
| install | PyPI == src code; root duplicate differences; four console scripts | lane D install-vs-source; W2-02 |
| versions | 3.10, 3.11, 3.12, 3.13 (no PyYAML) | W2-05, W2-06 |

## Sources

This section lists the code and evidence this page draws on.

- `tests/test_cli_smoke.py`; `skills/somnus-debug-fieldkit/scripts/selftest.py`; `STATE.md`
- `src/somnus_debug/structure/core.py:210`
- [lane D test-coverage.md](../_evidence/agent-findings/lane-d-cli-tests/test-coverage.md), [experiment-log.md](../_evidence/agent-findings/lane-d-cli-tests/experiment-log.md); [lane F fieldkit.md](../_evidence/agent-findings/lane-f-ext/fieldkit.md), [compositions.md](../_evidence/agent-findings/lane-f-ext/compositions.md); [lane B configuration-findings.md](../_evidence/agent-findings/lane-b-config/configuration-findings.md)
- W2 runs: [verification-results](verification-results.md#w2-runs)
