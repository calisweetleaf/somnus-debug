#!/usr/bin/env bash
# Recipe C3: quality ratchet. Promote runs/latest.json to the baseline only when
# delta is clean (exit 0) AND there are no stale dispositions; archive the old one.
# Usage: ratchet_promote.sh <repo> <fieldkit-dir>
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
echo "ratchet advanced: baseline <- $(python3 -c 'import json;print(json.load(open("runs/baseline.json"))["run_id"])') (old archived as $TS)"
