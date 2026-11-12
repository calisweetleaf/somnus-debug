# Recipe: quality ratchet (promote the baseline only when clean)

**Tier:** supported now. **Tools:** fieldkit `delta.py --json`, shell. **Script:** lane F's [ratchet_promote.sh](../../_evidence/agent-findings/lane-f-ext/recipes/ratchet_promote.sh).

Move the baseline forward only when the latest scan has no new serious findings and no stale dispositions, archiving the old baseline, so quality can only ratchet up between work slices.

## When to use

This section says where the ratchet sits in the loop.

At the end of a work slice, after [baseline-delta-loop](../intermediate/baseline-delta-loop.md) reaches delta exit 0. Never mid-slice: the baseline is what separates findings you introduced from ones that were there.

## The script

This section shows the whole recipe; it is short enough to read.

```bash
# ratchet_promote.sh <repo> <fieldkit-dir>
set -u
cd "$1/.somnus-debug" || exit 3
OUT=$(python3 "$2/scripts/delta.py" runs/baseline.json runs/latest.json --dispositions dispositions.json --json)
RC=$?
STALE=$(printf '%s' "$OUT" | python3 -c 'import json,sys;print(len(json.load(sys.stdin)["stale_dispositions"]))')
echo "delta exit=$RC stale_dispositions=$STALE"
if [ "$RC" -ne 0 ] || [ "$STALE" -ne 0 ]; then echo "ratchet held: baseline unchanged"; exit 1; fi
TS=$(python3 -c 'import json;print(json.load(open("runs/baseline.json"))["run_id"])')
mkdir -p runs/archive && cp runs/baseline.json "runs/archive/baseline-$TS.json" && cp runs/baseline.md "runs/archive/baseline-$TS.md"
cp runs/latest.json runs/baseline.json && cp runs/latest.md runs/baseline.md
```

## Executed result

This section shows the ratchet advancing on a clean delta and holding on a regression.

Executed: yes (`/tmp/w4/proj` after the [loop recipe](../intermediate/baseline-delta-loop.md); [stage 3 log](../_repro/logs/stage3_advanced.log), section A1)

```text
$ bash ratchet_promote.sh /tmp/w4/proj <fieldkit>
delta exit=0 stale_dispositions=0
ratchet advanced: baseline <- 20261112T004522Z (old archived as 20261112T004521Z)   [exit=0]
$ ls proj/.somnus-debug/runs proj/.somnus-debug/runs/archive
archive  baseline.json  baseline.md  latest.json  latest.md
baseline-20261112T004521Z.json  baseline-20261112T004521Z.md
# add export_report() calling os.system, rescan through the CI gate (exit 1), then:
$ bash ratchet_promote.sh /tmp/w4/proj <fieldkit>
delta exit=1 stale_dispositions=0
ratchet held: baseline unchanged                                                    [exit=1]
```

## Why also require zero stale dispositions

This section explains the second condition.

A disposition that matches nothing is dead weight today, and if it is broad it is a mute switch for tomorrow's findings: `delta.py` applies every disposition to every latest finding, first match wins (`skills/somnus-debug-fieldkit/scripts/delta.py:166-175`). Lane F showed a stale `{security_risks, src/*}` entry absorbing a new `os.system` call (case L7) [VERIFIED by lane F]. Requiring an empty stale list before promotion forces the list to be cleaned at every slice boundary. It does not catch a broad entry that still matches something; review those by hand ([customization](../../08-extensions/customization.md#dispositions-the-fieldkits-customization-layer)).

## Pitfalls

This section lists what the ratchet does not do.

- It uses the baseline's `run_id` for the archive name. Two baselines from the same second would collide ([D-08](../../DISCOVERY-LEDGER.md#d-08)) [HYPOTHESIS for the archive; the run-ID collision itself is VERIFIED].
- It trusts that `runs/latest.json` is fresh. Rescan immediately before ratcheting.
- It does not check that both reports were produced under the same config ([D-21](../../DISCOVERY-LEDGER.md#d-21)).
- Doctor's own history is an audit trail beside the ratchet, not a replacement: [automation/history-and-rollback](../automation/history-and-rollback.md).

## Sources

This section lists the files, logs and evidence this page rests on.

- [stage 3 log](../_repro/logs/stage3_advanced.log)
- [lane-f compositions C3](../../_evidence/agent-findings/lane-f-ext/compositions.md), [lane-f fieldkit §3](../../_evidence/agent-findings/lane-f-ext/fieldkit.md)
- `skills/somnus-debug-fieldkit/scripts/delta.py:159-191`, `skills/somnus-debug-fieldkit/SKILL.md:123-125`
