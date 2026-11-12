# Recipe: baseline, change, rescan, delta, triage

**Tier:** supported now. **Tools:** `doctor scan`, fieldkit `delta.py`, `dispositions.json`. **Needs:** an onboarded repo ([onboard-a-repo](onboard-a-repo.md)).

Find out whether your change introduced new serious findings, separate them from the ones that were already there, and record the ones you accept.

## When to use

This section says when the loop applies.

For every Python change in an onboarded repo. It is the loop the fieldkit's `SKILL.md` makes mandatory ("Python change ⇒ the loop", `skills/somnus-debug-fieldkit/SKILL.md:105`).

## Steps

This section gives the commands. Run them from `.somnus-debug/`; `pr` is the runner printed in `PROFILE.md`, here `env PYTHONPATH=../src /tmp/w4/proj/.venv/bin/python -m somnus_debug.cli`.

```console
cd .somnus-debug
# 1. baseline (onboard --baseline already wrote runs/baseline.*)
# 2. make the change and run the project's own tests
# 3. rescan
pr doctor scan .. -c python_doctor.yaml -o runs/latest.md --json-output runs/latest.json
# 4. delta
python3 <fieldkit>/scripts/delta.py runs/baseline.json runs/latest.json --dispositions dispositions.json
# 5. triage each new finding: fix, disposition with a reason, out of scope, or unverified; repeat 3-5
```

## Executed result

This section walks one full loop on the fixture.

Executed: yes (`/tmp/w4/proj`; [stage 2 log](../_repro/logs/stage2_intermediate.log), section I2)

The change adds `reserve()`, a `pass` stub, and `safe_level()`, which catches `KeyError` and returns 0.

```text
$ pr doctor scan .. -c python_doctor.yaml -o runs/latest.md --json-output runs/latest.json
Scan complete: files=3, issues=3, critical=0, serious=2
Run ID: 20261112T004522Z                                                       [exit=1]
$ python3 delta.py runs/baseline.json runs/latest.json --dispositions dispositions.json
**REGRESSION: new serious/critical findings.**
New (open): 3 · Resolved: 0 · Persisting: 0 · Dispositioned: 0
| serious | `stubs`                      | `src/inventory/store.py:27` | `reserve`    | Function reserve has a stub implementation. |
| serious | `silent_failures`            | `src/inventory/store.py:36` | `safe_level` | Exception handler can suppress failure without actionable diagnostics. |
| minor   | `suspicious_short_functions` | `src/inventory/store.py:27` | `reserve`    | Function reserve is suspiciously short. |   [exit=1]
```

Triage: the stub is real, so implement `reserve()`. The silent failure is a design choice (a missing SKU means zero stock), so disposition it narrowly with a reason:

```json
[
  {"category": "silent_failures", "file": "src/inventory/store.py", "symbol": "safe_level",
   "reason": "Missing SKU means zero stock by design; KeyError is the expected path, not a failure."}
]
```

```text
$ pr doctor scan .. -c python_doctor.yaml -o runs/latest.md --json-output runs/latest.json
Scan complete: files=3, issues=2, critical=0, serious=1
Run ID: 20261112T004522Z                                                       [exit=1]
$ python3 delta.py runs/baseline.json runs/latest.json --dispositions dispositions.json
**CLEAN: no new serious/critical findings, coverage intact.**
New (open): 1 · Resolved: 0 · Persisting: 0 · Dispositioned: 1
| minor | `suspicious_short_functions` | `src/inventory/store.py:27` | `reserve` | Function reserve is suspiciously short. |   [exit=0]
```

Doctor still exits 1 (the dispositioned serious finding is still a serious finding to doctor); delta exits 0 (nothing new and unaccepted). Gate on delta, not on doctor [VERIFIED]. `--json` returns the same verdict as an object with `exit`, `new`, `regressions`, `stale_dispositions` and coverage fields; its full shape is in [automation-contracts](../../10-agent-usage/automation-contracts.md).

## Delta exit codes

This section is the decision table for step 5.

| delta exit | Meaning | Next move |
|---|---|---|
| 0 | No new serious or critical finding; coverage intact | Review new minors in touched code; close when the native gate passes and no dispositions are stale |
| 1 | New serious or critical finding not covered by a disposition | Triage each one, repeat |
| 2 | Coverage regression: latest scanned 0 files, or a baseline file is missing from latest while still on disk. **Also** an argparse usage error | Fix coverage before reading anything else; if the command line was wrong, read stderr |
| 3 | Bad input: unreadable report, missing keys, invalid dispositions | Rerun the scan; check paths and the dispositions file |

Sources: `skills/somnus-debug-fieldkit/scripts/delta.py:53-54`, `:181-190`; usage error exit 2 VERIFIED in [stage 6 log](../_repro/logs/stage6_integrations.log) ([D-21](../../DISCOVERY-LEDGER.md#d-21)).

## Pitfalls

This section lists what the loop does not protect against.

- **Same-second scans share a run ID.** Both scans above printed `Run ID: 20261112T004522Z`; doctor's history now holds only the second ([D-08](../../DISCOVERY-LEDGER.md#d-08)) [VERIFIED]. The `runs/*.json` files the loop uses are separate files and unaffected, but if you rely on `doctor history`, wait a second between scans.
- **Identity is `(category, file, symbol, message)`.** Moving code does not create findings; renaming a function does, and its disposition goes stale (lane F, D9) [VERIFIED by lane F].
- **Broad dispositions mute future findings** ([customization](../../08-extensions/customization.md#dispositions-the-fieldkits-customization-layer)).
- **A config change between baseline and latest can hide a regression;** use the same `-c` for both ([D-21](../../DISCOVERY-LEDGER.md#d-21)).
- **A malformed issue object crashes delta with a `KeyError` and exit 1,** which looks like "regression" ([D-21](../../DISCOVERY-LEDGER.md#d-21)) [VERIFIED in this wave].
- **Keep one baseline per work slice.** Promote it only through [advanced/quality-ratchet](../advanced/quality-ratchet.md).

## Sources

This section lists the files, logs and evidence this page rests on.

- [stage 2 log](../_repro/logs/stage2_intermediate.log), [stage 6 log](../_repro/logs/stage6_integrations.log)
- [lane-f fieldkit §3](../../_evidence/agent-findings/lane-f-ext/fieldkit.md)
- `skills/somnus-debug-fieldkit/scripts/delta.py`, `skills/somnus-debug-fieldkit/references/doctor-loop.md`, `skills/somnus-debug-fieldkit/SKILL.md:66-77`, `:105`
