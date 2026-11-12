#!/usr/bin/env bash
# Stage 5b: doctor state reports as delta inputs (after stage 5's rollback). Needs stage 5 state in /tmp/w4/proj.
source "$(dirname "$0")/env.sh"; set -u
exec > "$LOGS/stage5b_state_reports.log" 2>&1
cd "$W/proj/.somnus-debug"
run "ls state/reports"
run "python3 -c \"import json;r=json.load(open('state/reports/latest.json'));print('latest alias:', r['run_id'], r['summary']['total_issues'], 'issues')\""
REG=$(python3 -c "import json,glob;print([p for p in sorted(glob.glob('state/reports/*/production_doctor_report.json')) if any(i['symbol']=='export_report' for i in json.load(open(p))['issues'])][0])")
run "echo $REG"
run "python3 $FK/scripts/delta.py state/reports/latest.json $REG --dispositions dispositions.json | tail -8"
