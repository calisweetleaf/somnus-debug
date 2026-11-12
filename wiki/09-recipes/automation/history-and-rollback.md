# Recipe: audit runs with `doctor history`, and what `rollback` really does

**Tier:** supported now. **Tools:** `doctor history`, `doctor rollback`, fieldkit `delta.py`.

Use doctor's stateful history as an audit trail of past scans, reuse any archived run as a delta baseline, and understand that `rollback` moves a report alias, not your code.

## When to use

This section separates what history is for from what it is not.

Use history to see the trend across a work session and to retrieve the full report of an earlier run. Use rollback only to re-point the `latest` report alias, for example to reproduce what a reviewer saw. Neither touches source files. For baseline management, the [quality ratchet](../advanced/quality-ratchet.md) is the stronger tool.

## Steps

This section gives the commands. Run from `.somnus-debug/`; `pr` is the profile runner.

```console
pr doctor history .. -c python_doctor.yaml --limit 3
pr doctor rollback .. -c python_doctor.yaml --run-id <run_id>
python3 <fieldkit>/scripts/delta.py state/reports/latest.json state/reports/<run_id>/production_doctor_report.json --dispositions dispositions.json
```

Pass the same `-c` as the scans. `history` and `rollback` read `state_dir` from the config; without `-c` they look in the default `.python_doctor/` and find nothing [VERIFIED by lane B, O10].

## Executed result

This section shows history, a rollback, a bad run ID, and a state report used as a delta baseline.

Executed: yes (`/tmp/w4/proj/.somnus-debug`; [stage 5 log](../_repro/logs/stage5_automation.log) section T3, [stage 5b log](../_repro/logs/stage5b_state_reports.log))

```text
$ pr doctor history .. -c python_doctor.yaml --limit 3
Run history:
- 20261112T004537Z | Wed 2026-11-11 6:45 PM CST (UTC-06:00) | files=3 | issues=2 | critical=0 | serious=1
  markdown=/tmp/w4/proj/.somnus-debug/state/reports/20261112T004537Z/production_doctor_report.md
  json=/tmp/w4/proj/.somnus-debug/state/reports/20261112T004537Z/production_doctor_report.json
- 20261112T004527Z | ... | files=3 | issues=4 | critical=0 | serious=2
- 20261112T004522Z | ... | files=3 | issues=2 | critical=0 | serious=1     [exit=0]
latest alias before: 20261112T004537Z
$ pr doctor rollback .. -c python_doctor.yaml --run-id 20261112T004521Z
Rolled latest report state back to run 20261112T004521Z.                       [exit=0]
latest alias after: 20261112T004521Z
$ pr doctor rollback .. -c python_doctor.yaml --run-id NOPE
Doctor failure: Run ID does not exist in state history.                        [exit=4]
$ git -C .. status --short
                                                                               # no source change
$ python3 delta.py state/reports/latest.json state/reports/20261112T004527Z/production_doctor_report.json --dispositions dispositions.json
| serious | `security_risks` | `src/inventory/store.py:47` | `export_report` | High-risk call detected: os.system. |   [exit=1]
```

The rolled-back `latest.json` (the onboarding baseline, 0 issues) and the archived report of the regression scan worked as delta inputs directly; doctor's state reports have the same shape as `--json-output` [VERIFIED].

The history timestamps print as `Wed 2026-11-11 6:45 PM CST`: in this sandbox `datetime.isoformat()` is localized. On a normal host the column is ISO-8601. History orders by that text column, so ordering here is [CONDITIONAL] ([lane-f fieldkit, sandbox caveat](../../_evidence/agent-findings/lane-f-ext/fieldkit.md)).

## What rollback changes and what it does not

This section lists rollback's real effects.

- It copies the chosen run's reports over `state/reports/latest.{md,json}` and moves the alias [VERIFIED].
- It does **not** restore code, and does not touch reports written with `-o` (the fieldkit's `runs/*`) or reports in the project root ([D-09](../../DISCOVERY-LEDGER.md#d-09)).
- It does change the hash index the **next** stateful scan computes `state_delta` against, so the next scan reports changes relative to the rolled-back run [VERIFIED by lane F, C3g].

## Pitfalls

This section lists the history hazards.

- **Missing runs.** Same-second scans share a run ID and `INSERT OR REPLACE` keeps only the last ([D-08](../../DISCOVERY-LEDGER.md#d-08)). In this wave the history above has no separate row for the first loop scan: both loop scans got `20261112T004522Z` [VERIFIED, [stage 2 log](../_repro/logs/stage2_intermediate.log)].
- **No SQLite, no history.** When the state database cannot be opened, scans fall back to stateless with a warning, but `history` and `rollback` exit 4 ([D-28](../../DISCOVERY-LEDGER.md#d-28)).
- **`--no-state` scans are invisible here.** The pre-commit hook and onboard's verify scan never appear in history.

## Sources

This section lists the files, logs and evidence this page rests on.

- [stage 5 log](../_repro/logs/stage5_automation.log), [stage 5b log](../_repro/logs/stage5b_state_reports.log), [stage 2 log](../_repro/logs/stage2_intermediate.log)
- [lane-f compositions C3, C3'](../../_evidence/agent-findings/lane-f-ext/compositions.md), [lane-b configuration findings §7](../../_evidence/agent-findings/lane-b-config/configuration-findings.md), [lane-a API reference, State](../../_evidence/agent-findings/lane-a-arch-api/api-reference.md)
- `src/somnus_debug/doctor/core.py:1916` (`StateStore`)
