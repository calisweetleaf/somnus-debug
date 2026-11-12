# Recipe execution log

This page lists every recipe in the chapter with the command that proves it, the observed exit codes, and the log that holds the full output. All rows are from one complete run of the [repro driver](_repro/README.md) on 2026-11-11 (CST).

## Results

This section is the per-recipe record. "Executed: yes" for every row; each exit code is copied from the `[exit=N]` line in the named log.

| Recipe | Key command(s) | Observed exit codes | Matches expectation | Log |
|---|---|---|---|---|
| [beginner/first-scan](beginner/first-scan.md) | `doctor init-config`; `doctor scan ../proj -c cfg.yaml --no-state -o … --json-output …` | 0; 2 (2 criticals) | yes | [stage 1](_repro/logs/stage1_beginner.log) B1 |
| [beginner/index-one-file](beginner/index-one-file.md) | `structure b.py`; `structure --no-line-numbers --no-module-functions`; `structure stamped.py` | 0; 0; 2 (`invalid syntax … line 9`) | yes (crash is [D-01](../DISCOVERY-LEDGER.md#d-01)) | [stage 1](_repro/logs/stage1_beginner.log) B2 |
| [beginner/pycache-dry-run](beginner/pycache-dry-run.md) | `pycache-clean --config clean.yaml --dry-run --verbose`; same without `--dry-run` | 0; 0; all 3 files still present | yes | [stage 1](_repro/logs/stage1_beginner.log) B3 |
| [intermediate/onboard-a-repo](intermediate/onboard-a-repo.md) | `onboard.py proj`; `--apply --baseline`; `--apply` again | 0; 0; 0 ("Kept existing") | yes | [stage 2](_repro/logs/stage2_intermediate.log) I1 |
| [intermediate/baseline-delta-loop](intermediate/baseline-delta-loop.md) | scan; `delta.py`; disposition + fix; scan; `delta.py`; `delta.py --json` | 1; 1; 1; 0; 0 | yes (doctor 1 vs delta 0 by design) | [stage 2](_repro/logs/stage2_intermediate.log) I2 |
| [intermediate/severity-and-gate-tuning](intermediate/severity-and-gate-tuning.md) | 6 scans with default, tuned, unquoted `none`, quoted `"none"`, typo key | 1; 0; 2; 4; 0; 1 | yes | [stage 2](_repro/logs/stage2_intermediate.log) I3 |
| [advanced/quality-ratchet](advanced/quality-ratchet.md) | `ratchet_promote.sh` clean; after regression | 0 (advanced); 1 (held) | yes | [stage 3](_repro/logs/stage3_advanced.log) A1 |
| [advanced/findings-to-source-slices](advanced/findings-to-source-slices.md) | `findings_to_slices.py`; `--all`; after editing the file; `structure_slice.py parse_qty nope` | 0; 0; 2 (stale guard); 1 (missing name) | yes | [stage 3](_repro/logs/stage3_advanced.log) A2 |
| [advanced/custom-detector-probe](advanced/custom-detector-probe.md) | stock scan; `ext_custom_detector.py`; `delta.py stock patched` | 0; 2; 1 | yes | [stage 3](_repro/logs/stage3_advanced.log) A3 |
| [advanced/src-layout-cycle-check](advanced/src-layout-cycle-check.md) | scan root `repo/`; with `PYTHONPATH=src`; root `repo/src` | 1 (cycles 0); 0 (cycles 0); 1 (cycles 1) | yes | [stage 3](_repro/logs/stage3_advanced.log) A4 |
| [programmatic/embedded-scan](programmatic/embedded-scan.md) | `python embed_scan.py proj`; parity check | 0 (no new paths, handlers `[]`); 0 (all keys equal except run_id and times) | yes | [stage 4](_repro/logs/stage4_programmatic.log) P1, [stage 4b](_repro/logs/stage4b_json_parity.log) |
| [programmatic/index-stamped-file](programmatic/index-stamped-file.md) | `python index_any.py stamped_scaffold.py` | 0 (`scaffold` at lines 62-88 = file line 62) | yes | [stage 4](_repro/logs/stage4_programmatic.log) P2 |
| [programmatic/inprocess-main-isolated](programmatic/inprocess-main-isolated.md) | `python inprocess_main.py proj work/out` | 0 (`main()` returned 1; handlers restored; no cwd log) | yes | [stage 4](_repro/logs/stage4_programmatic.log) P3 |
| [automation/ci-delta-gate](automation/ci-delta-gate.md) | `ci_delta_gate.sh` on regression; broken config; clean | 1; 3; 0 | yes | [stage 3](_repro/logs/stage3_advanced.log) A1, [stage 5](_repro/logs/stage5_automation.log) T1 |
| [automation/pre-commit-gate](automation/pre-commit-gate.md) | `git commit` with `shell=True` call; clean commit | 1 (blocked); 0 | yes | [stage 5](_repro/logs/stage5_automation.log) T2 |
| [automation/history-and-rollback](automation/history-and-rollback.md) | `doctor history`; `rollback --run-id <first>`; `rollback --run-id NOPE`; `delta.py` on state reports | 0; 0; 4; 1 | yes | [stage 5](_repro/logs/stage5_automation.log) T3, [stage 5b](_repro/logs/stage5b_state_reports.log) |
| [integrations/harness-pytest](integrations/harness-pytest.md) | `init-test-harness single_test` ×2; `run_test.py` passing; failing | 0; 1; 0 (PASS); 1 (FAIL) | yes | [stage 6](_repro/logs/stage6_integrations.log) N1 |
| [integrations/harness-doctor-delta](integrations/harness-doctor-delta.md) | `run_test.py` fresh; after dispositions; with regression; without `SD_PYTHON` | 1; 0; 1; 1 | yes | [stage 6](_repro/logs/stage6_integrations.log) N2 |
| [integrations/fieldkit-selftest](integrations/fieldkit-selftest.md) | `selftest.py --python venv/bin/python`; with no CLI on PATH | 0 (29/29); 3 | yes | [stage 6](_repro/logs/stage6_integrations.log) N3 |

## Probes used by the extension and agent pages

This section lists the non-recipe runs cited elsewhere.

| Probe | Observed | Cited in | Log |
|---|---|---|---|
| `delta.py` with one positional argument | exit 2 (argparse), same code as coverage regression | [failure-recovery](../10-agent-usage/failure-recovery.md) | [stage 6](_repro/logs/stage6_integrations.log) F |
| `delta.py` with `{}` as latest | exit 3, "is not a somnus-debug doctor JSON report" | same | same |
| `delta.py` with an issue lacking `category` | `KeyError: 'category'`, exit 1 | same | same |
| `delta.py --dispositions missing.json` | note on stderr, exit 0 (continues without dispositions) | same | same |
| disposition without `reason` | exit 3 | [customization](../08-extensions/customization.md) | same |
| narrow vs narrow + broad `{security_risks, src/*}` disposition on a new `os.system` | exit 1 vs exit 0, broad entry not stale | [customization](../08-extensions/customization.md) | same |
| `onboard.py --python /tmp/w4/venv/bin/python` (symlinked venv interpreter) | `BLOCKED`, exit 3 | [onboard-a-repo](intermediate/onboard-a-repo.md) | same |
| `pycache-clean` with `targets: ["*.bak", "build_cache"]` | deleted `x.bak` and `build_cache/`, kept `keep.py`, exit 0 | [existing-extension-points](../08-extensions/existing-extension-points.md) | [stage 6](_repro/logs/stage6_integrations.log) E11 |
| Two loop scans in the same second | both printed `Run ID: 20261112T004522Z` | [baseline-delta-loop](intermediate/baseline-delta-loop.md) | [stage 2](_repro/logs/stage2_intermediate.log) |
| Agent subprocess wrapper `doctor_scan_subprocess.py` (good config; bad gate) | `ran: True, exit 1, files 4`; `ran: False, exit 4`; two failed drafts kept | [programmatic-invocation](../10-agent-usage/programmatic-invocation.md) | [stage 6c](_repro/logs/stage6c_subprocess_pattern.log) |
| Two stateful scans launched together, fresh state dir | one recorded; the other warned `local SQLite state is unavailable` and ran stateless; both exit 1 | [subagent-patterns](../10-agent-usage/subagent-patterns.md) | [stage 6d](_repro/logs/stage6d_parallel.log) |
| Two stateful scans launched together, existing state DB | both printed the same run ID; history kept one row | same | same |
| Two `--no-state` scans together, private cwds and outputs | identical issues, each its own log | same | same |
| Key sets of doctor JSON, delta JSON, manifest, dispositions | recorded | [automation-contracts](../10-agent-usage/automation-contracts.md) | [stage 6b](_repro/logs/stage6b_contract_keys.log) |

## Not executed

This section lists what the chapter mentions but did not run.

- Patching `SECURITY_CALLS` at import time ([experimental-extensions](../08-extensions/experimental-extensions.md)) [HYPOTHESIS].
- A `targets: ["*.py"]` cleaner run (would delete source) [HYPOTHESIS, deliberately not run].
- Feeding a `src/`-rooted scan into `delta.py` against a repo-rooted baseline [HYPOTHESIS].
- Any GitHub Actions or other hosted CI run; the CI recipe was run as a shell script only.

## Sources

This section lists the files, logs and evidence this page rests on.

- [repro driver](_repro/README.md) and its logs.
