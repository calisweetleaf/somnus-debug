#!/usr/bin/env bash
# Stage 6d: parallel scans, as subagents would run them (needs stage 2 fixture in /tmp/w4/proj).
source "$(dirname "$0")/env.sh"; set -u
exec > "$LOGS/stage6d_parallel.log" 2>&1
rm -rf "$W/par" && cp -r "$W/proj" "$W/par" && cd "$W/par/.somnus-debug"
PR="env PYTHONPATH=../src $W/par/.venv/bin/python -m somnus_debug.cli"
echo "## P-A: two subagents, stateful, same state_dir, launched together"
run "rm -rf state && for i in 1 2; do ($PR doctor scan .. -c python_doctor.yaml -o runs/w\$i.md --json-output runs/w\$i.json > runs/w\$i.out 2>&1; echo \"worker \$i exit=\$?\") & done; wait"
run "grep -h -e 'Run ID' -e '^Warning' runs/w1.out runs/w2.out"
run "$PR doctor history .. -c python_doctor.yaml --limit 5 | grep -c '^- '"
echo; echo "## P-A2: same, but the state DB already exists"
sleep 1
run "for i in 3 4; do ($PR doctor scan .. -c python_doctor.yaml -o runs/w\$i.md --json-output runs/w\$i.json > runs/w\$i.out 2>&1; echo \"worker \$i exit=\$?\") & done; wait"
run "grep -h -e 'Run ID' -e '^Warning' runs/w3.out runs/w4.out"
run "$PR doctor history .. -c python_doctor.yaml --limit 5 | grep '^- ' | cut -d'|' -f1"
echo; echo "## P-B: two subagents, --no-state, private output dirs and cwds, launched together"
run "for i in 1 2; do (mkdir -p /tmp/w4/par_w\$i && cd /tmp/w4/par_w\$i && $W/par/.venv/bin/python -m somnus_debug.cli doctor scan $W/par -c $W/par/.somnus-debug/python_doctor.yaml --no-state -o out.md --json-output out.json > out.txt 2>&1; echo \"worker \$i exit=\$?\") & done; wait"
run "python3 -c \"import json; a=json.load(open('/tmp/w4/par_w1/out.json')); b=json.load(open('/tmp/w4/par_w2/out.json')); print('same issues', a['issues']==b['issues'], 'files', a['summary']['files_scanned'], b['summary']['files_scanned'])\""
run "ls /tmp/w4/par_w1 /tmp/w4/par_w2"
