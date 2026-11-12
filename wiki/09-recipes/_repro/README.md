# Recipe repro driver

Every recipe in this chapter was executed by these scripts. This page says what they build, how to rerun them, and where the raw logs are.

## What the stages do

This section maps each stage to the recipes it proves.

| Stage | Script | Builds or runs | Log |
|---|---|---|---|
| 0 | [stage0_setup.sh](stage0_setup.sh) | `/tmp/w4/venv` (non-editable `pip install` of this repo + pytest); fixture `b1/proj` (lane-A fixture files), `b1/proj_nobroken`; fixture `proj` (src-layout `inventory` package, git repo, own `.venv` with the repo + pytest) | [stage0_setup.log](logs/stage0_setup.log) |
| 1 | [stage1_beginner.sh](stage1_beginner.sh) | B1 first scan, B2 structure, B3 pycache dry run | [stage1_beginner.log](logs/stage1_beginner.log) |
| 2 | [stage2_intermediate.sh](stage2_intermediate.sh) | I1 onboard, I2 loop, I3 severity and gate | [stage2_intermediate.log](logs/stage2_intermediate.log) |
| 3 | [stage3_advanced.sh](stage3_advanced.sh) | A1 ratchet + CI gate on a regression, A2 slices, A3 custom-detector probe, A4 src-layout cycles | [stage3_advanced.log](logs/stage3_advanced.log) |
| 4 | [stage4_programmatic.sh](stage4_programmatic.sh) | P1 [embed_scan.py](embed_scan.py), P2 [index_any.py](index_any.py), P3 [inprocess_main.py](inprocess_main.py) | [stage4_programmatic.log](logs/stage4_programmatic.log) |
| 4b | [stage4b_json_parity.sh](stage4b_json_parity.sh) | library `dumps_json` vs CLI `--json-output` | [stage4b_json_parity.log](logs/stage4b_json_parity.log) |
| 5 | [stage5_automation.sh](stage5_automation.sh) | T1 CI gate (broken config, clean), T2 [pre-commit.sh](pre-commit.sh), T3 history and rollback | [stage5_automation.log](logs/stage5_automation.log) |
| 5b | [stage5b_state_reports.sh](stage5b_state_reports.sh) | state reports as delta inputs after rollback | [stage5b_state_reports.log](logs/stage5b_state_reports.log) |
| 6 | [stage6_integrations.sh](stage6_integrations.sh) | N1 harness + [surface_pytest.py](surface_pytest.py), N2 harness + doctor + delta, N3 selftest, F failure probes, E11 pycache `targets` | [stage6_integrations.log](logs/stage6_integrations.log) |
| 6b | [stage6b_contract_keys.sh](stage6b_contract_keys.sh) | key sets of doctor JSON, `delta.py --json`, harness `manifest.json`, `dispositions.json` | [stage6b_contract_keys.log](logs/stage6b_contract_keys.log) |
| 6c | [stage6c_subprocess_pattern.sh](stage6c_subprocess_pattern.sh) | the agent subprocess wrapper [doctor_scan_subprocess.py](doctor_scan_subprocess.py); two failed drafts kept as [first attempt](logs/stage6c_first_attempt_relative_paths.log) and [second attempt](logs/stage6c_second_attempt_resolved_interpreter.log) | [stage6c_subprocess_pattern.log](logs/stage6c_subprocess_pattern.log) |
| 6d | [stage6d_parallel.sh](stage6d_parallel.sh) | two scans launched together, stateful (fresh and existing state DB) and `--no-state` with private dirs | [stage6d_parallel.log](logs/stage6d_parallel.log) |

Lane F's scripts are reused, not copied: [ci_delta_gate.sh, ratchet_promote.sh, findings_to_slices.py, structure_slice.py, ext_custom_detector.py, harness_doctor_surface.py](../../_evidence/agent-findings/lane-f-ext/recipes/).

## How to rerun

This section gives the order and the rules the scripts follow.

```console
cd wiki/09-recipes/_repro
for s in stage0_setup stage1_beginner stage2_intermediate stage3_advanced stage4_programmatic \
         stage4b_json_parity stage5_automation stage5b_state_reports stage6_integrations stage6b_contract_keys stage6c_subprocess_pattern stage6d_parallel; do bash $s.sh; done
```

- Stages are sequential: 3 needs 2's state, 5 needs 3's, 6 needs 5's. Stage 0 deletes and rebuilds `/tmp/w4`.
- Each stage rewrites its own log in `logs/`. Every command is echoed as `$ ...` and followed by `[exit=N]`; `set -o pipefail` (in [env.sh](env.sh)) makes `N` the tool's own code when output is piped.
- `PYTHONDONTWRITEBYTECODE=1` is set, and every tool runs with its cwd under `/tmp/w4`, so nothing is written into the repo outside this directory. A side effect of no bytecode caching: each cold import of `pycache_cleaner` prints a `SyntaxWarning` (`pycache_cleaner/core.py:64`); the logs keep it.
- Stage 0 needs network access for `pip install pytest`.
- The repo's `.gitignore` ignores `*.log`, so `logs/` shows as ignored in `git status`; the files are present in the workspace.

## Environment of the recorded run

This section records where the logs came from.

Python 3.12.15 in the Hark sandbox, somnus-debug 0.1.0 installed from this checkout (baseline commit 034f46e), 2026-11-11 CST (run IDs are UTC, `20261112T00…`). `/tmp` was reset once during this wave; every stage was rerun from stage 0 after the reset, and the logs here are from that complete rerun.

## Sources

This section lists the files, logs and evidence this page rests on.

- The scripts and logs in this directory.
- [lane-f repro](../../_evidence/agent-findings/lane-f-ext/repro/env.sh) (the pattern these stages follow)
