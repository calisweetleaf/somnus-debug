#!/usr/bin/env bash
# Recipe C1: doctor JSON -> delta.py regression gate (CI / pre-handoff).
# Usage: ci_delta_gate.sh <repo-with-.somnus-debug-profile> <fieldkit-dir> <runner...>
# Gates on delta.py's exit code, NOT doctor's raw exit (doctor exits 1 on any
# pre-existing serious finding; delta exits 1 only on NEW undispositioned ones).
# Doctor exit >=4 (config/runtime failure) is treated as a hard failure (exit 3).
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
