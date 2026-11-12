#!/usr/bin/env bash
# Opt-in local gate for a repo onboarded with the somnus-debug fieldkit.
# Rescans with the profile config and blocks the commit on new serious/critical findings.
# somnus-debug ships no hook installer; copy this to .git/hooks/pre-commit by hand.
# Set FIELDKIT to the somnus-debug-fieldkit directory. Scans the WORKING TREE, not the staged index.
git diff --cached --name-only --diff-filter=ACMR | grep -q '\.py$' || exit 0
cd "$(git rev-parse --show-toplevel)/.somnus-debug" || exit 1
PYTHONPATH=../src ../.venv/bin/python -m somnus_debug.cli doctor scan .. -c python_doctor.yaml --no-state \
  -o runs/precommit.md --json-output runs/precommit.json > /dev/null
rc=$?
[ "$rc" -ge 4 ] && { echo "pre-commit: doctor failed to run (exit $rc)"; exit 1; }
python3 "$FIELDKIT/scripts/delta.py" runs/baseline.json runs/precommit.json --dispositions dispositions.json --json \
  | python3 -c 'import json,sys; d=json.load(sys.stdin); [print("pre-commit regression:", r["category"], r["file"], r["line"], r["symbol"]) for r in d["regressions"]]; sys.exit(d["exit"])'
