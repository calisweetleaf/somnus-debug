# Recipe: CI regression gate (doctor JSON → `delta.py`)

**Tier:** supported now. **Script:** lane F's [ci_delta_gate.sh](../../_evidence/agent-findings/lane-f-ext/recipes/ci_delta_gate.sh). **Needs:** an onboarded repo with `runs/baseline.json`.

Fail a CI job, or a pre-handoff check, only when a change introduces new serious or critical findings or breaks scan coverage, and fail distinctly when doctor could not run at all.

## When to use

This section explains why the gate is on delta and not on doctor.

Doctor exits 1 on any serious finding, old or new, so on a real codebase it is red from day one. `delta.py` exits 1 only on new, undispositioned serious or critical findings, and 2 on coverage loss. The fieldkit's own automation reference says to gate on delta's exit code (`skills/somnus-debug-fieldkit/references/automation.md:65`). Somnus-debug ships no CI configuration; this script is the step you would call from one.

## The script

This section is the whole gate.

```bash
# ci_delta_gate.sh <repo-with-.somnus-debug-profile> <fieldkit-dir> <runner...>
set -u
REPO="$1"; FK="$2"; shift 2; RUNNER=("$@")
cd "$REPO/.somnus-debug" || exit 3
"${RUNNER[@]}" doctor scan .. -c python_doctor.yaml -o runs/latest.md --json-output runs/latest.json
DOC=$?
echo "doctor exit=$DOC"
if [ "$DOC" -ge 4 ]; then echo "doctor failed to run"; exit 3; fi
[ -f runs/baseline.json ] || { echo "no baseline; run onboard.py --baseline first"; exit 3; }
python3 "$FK/scripts/delta.py" runs/baseline.json runs/latest.json --dispositions dispositions.json
GATE=$?
echo "delta exit=$GATE"
exit $GATE
```

No `set -e`: doctor's exit 1 on pre-existing findings is expected. The runner is passed as trailing arguments, for example `env PYTHONPATH=<repo>/src <repo>/.venv/bin/python -m somnus_debug.cli`.

## Executed result

This section shows all three outcomes.

Executed: yes (`/tmp/w4/proj` and a copy with a broken config; [stage 3 log](../_repro/logs/stage3_advanced.log) section A1, [stage 5 log](../_repro/logs/stage5_automation.log) section T1)

```text
# regression: export_report() calling os.system was added
doctor exit=1
**REGRESSION: new serious/critical findings.**
| serious | `security_risks` | `src/inventory/store.py:47` | `export_report` | High-risk call detected: os.system. |
delta exit=1                                                                   [exit=1]

# broken config: severity_exit_level: "bogus" (in /tmp/w4/proj_ci)
Doctor failure: Invalid severity_exit_level.
doctor exit=4
doctor failed to run                                                           [exit=3]

# clean: regression removed
**CLEAN: no new serious/critical findings, coverage intact.**
New (open): 0 · Resolved: 0 · Persisting: 2 · Dispositioned: 1
delta exit=0                                                                   [exit=0]
```

## Exit contract for the CI job

This section is what a CI system should key on.

| Gate exit | Meaning |
|---|---|
| 0 | No new serious or critical findings; coverage intact |
| 1 | New serious or critical finding (or delta crashed on a malformed report, see pitfalls) |
| 2 | Coverage regression (or a delta usage error) |
| 3 | Doctor could not run (exit ≥ 4), no baseline, or bad delta input |

## Pitfalls

This section lists the holes CI should know about. Most are [D-21](../../DISCOVERY-LEDGER.md#d-21).

- **Exit 2 is overloaded:** argparse usage errors in `delta.py` also exit 2 [VERIFIED, [stage 6 log](../_repro/logs/stage6_integrations.log)].
- **Exit 1 is overloaded:** an issue object without `category` crashes delta with `KeyError` and exit 1 [VERIFIED, stage 6].
- **Pin the config.** The script always uses `-c python_doctor.yaml`; review edits to that file like code, since a severity downgrade in it hides regressions.
- **Broad dispositions** absorb new findings ([customization](../../08-extensions/customization.md#dispositions-the-fieldkits-customization-layer)).
- **The scan is stateful** (no `--no-state`), so it writes to `.somnus-debug/state/`; two CI scans in the same second overwrite each other's history row ([D-08](../../DISCOVERY-LEDGER.md#d-08)). On CI runners that do not keep state between jobs this is harmless.
- **Doctor is static analysis.** Run the project's tests in the same job; doctor never emits `test_gaps` ([D-05](../../DISCOVERY-LEDGER.md#d-05)). The [harness-doctor-delta](../integrations/harness-doctor-delta.md) recipe puts both in one verdict.

## Sources

This section lists the files, logs and evidence this page rests on.

- [stage 3 log](../_repro/logs/stage3_advanced.log), [stage 5 log](../_repro/logs/stage5_automation.log), [stage 6 log](../_repro/logs/stage6_integrations.log)
- [lane-f compositions C1](../../_evidence/agent-findings/lane-f-ext/compositions.md)
- `skills/somnus-debug-fieldkit/references/automation.md:48-71`, `skills/somnus-debug-fieldkit/scripts/delta.py:235-255`
