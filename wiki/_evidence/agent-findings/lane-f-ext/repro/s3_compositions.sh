#!/usr/bin/env bash
# Stage 3: compositions C1 (CI delta gate), C3 (ratchet + history/rollback), C2 (targeted reading).
source "$(dirname "$0")/env.sh"; set -u; cd $W
R=$LANE/recipes
python3 - <<'P'
import json;p='/tmp/lane-f/proj/.somnus-debug/dispositions.json';d=json.load(open(p));json.dump([x for x in d if x['category']!='security_risks'],open(p,'w'),indent=1)
P
L=$LOGS/s3_C1_C3.log; : > $L
log "(setup: removed the broad security_risks disposition left by stage 2)"
log "### C1a clean tree"; bash $R/ci_delta_gate.sh $W/proj $FK $PRUN > $W/c1a.txt 2>&1; rc=$?; grep -E 'exit=|\*\*' $W/c1a.txt >>$L; log "recipe exit=$rc"
printf "$REGRESS_RISKY" >> proj/src/calc/ops.py
log "### C1b regression (os.system)"; bash $R/ci_delta_gate.sh $W/proj $FK $PRUN > $W/c1b.txt 2>&1; rc=$?; grep -E 'exit=|\*\*|security' $W/c1b.txt >>$L; log "recipe exit=$rc"
log "### C3a ratchet on regression"; bash $R/ratchet_promote.sh $W/proj $FK >>$L 2>&1; log "recipe exit=$?"
cp proj/.somnus-debug/runs/latest.json $W/regression_latest.json
cp $W/ops.fixed proj/src/calc/ops.py
cp proj/.somnus-debug/python_doctor.yaml $W/cfg.bak; sed -i 's/severity_exit_level: "serious"/severity_exit_level: "bogus"/' proj/.somnus-debug/python_doctor.yaml
log "### C1c broken config -> doctor exit 4 -> recipe exit 3"; bash $R/ci_delta_gate.sh $W/proj $FK $PRUN > $W/c1c.txt 2>&1; rc=$?; grep -E 'exit=|failed' $W/c1c.txt >>$L; log "recipe exit=$rc"
cp $W/cfg.bak proj/.somnus-debug/python_doctor.yaml
log "### C1d clean again"; bash $R/ci_delta_gate.sh $W/proj $FK $PRUN > $W/c1d.txt 2>&1; rc=$?; grep -E 'exit=' $W/c1d.txt >>$L; log "recipe exit=$rc"
log "### C3b ratchet on clean delta"; bash $R/ratchet_promote.sh $W/proj $FK >>$L 2>&1; log "recipe exit=$?"
log "### C3c doctor history"; (cd proj/.somnus-debug && $PRUN doctor history .. -c python_doctor.yaml --limit 10) >>$L 2>&1; log "exit=$?"
FIRST=$(python3 -c "import json,glob;print(json.load(open(sorted(glob.glob('$W/proj/.somnus-debug/runs/archive/*.json'))[0]))['run_id'])")
cd proj/.somnus-debug
log "### C3d rollback latest alias to the first (onboarding) run $FIRST"; $PRUN doctor rollback .. -c python_doctor.yaml --run-id $FIRST >>$L 2>&1; log "exit=$?"
python3 -c "import json;print('state/reports/latest.json run_id after rollback:',json.load(open('state/reports/latest.json'))['run_id'])" >>$L
log "### C3e delta: rolled-back state/reports/latest.json as baseline vs the earlier regression scan"; python3 $FK/scripts/delta.py state/reports/latest.json $W/regression_latest.json --dispositions dispositions.json 2>&1 | grep -E '\*\*|New \(open|security' >>$L; log "delta exit=${PIPESTATUS[0]}"
log "### C3f rollback to a non-existent run id"; $PRUN doctor rollback .. -c python_doctor.yaml --run-id nope >>$L 2>&1; log "exit=$?"
log "### C3g next stateful scan diffs file hashes against the rolled-back run"; $PRUN doctor scan .. -c python_doctor.yaml -o $W/after_rb.md --json-output $W/after_rb.json >/dev/null 2>&1; python3 -c "import json;print(json.load(open('$W/after_rb.json'))['state_delta'])" >>$L
log "### C3h sandbox timestamp note: started_at as stored"; python3 -c "import json;d=json.load(open('$W/after_rb.json'));print(repr(d['started_at']), repr(d['run_id']))" >>$L
cd $W
# ---------- C2 ----------
L=$LOGS/s3_C2.log; : > $L
log "### C2a structure_slice add parse nonexistent"; python3 $R/structure_slice.py $W/venv/bin/python proj/src/calc/ops.py add parse nonexistent >>$L 2>&1; log "exit=$?"
cd proj/.somnus-debug
python3 $FK/scripts/delta.py runs/archive/$(ls runs/archive | grep json | head -1) $W/regression_latest.json --json > $W/delta_reg.json; log "delta(onboarding baseline vs regression scan) exit=$?"
log "### C2b findings_to_slices on a report whose file has changed since (guard)"; python3 $R/findings_to_slices.py $W/regression_latest.json $W/delta_reg.json --all >>$L 2>&1; log "exit=$?"
printf "$REGRESS_RISKY" >> ../src/calc/ops.py
$PRUN doctor scan .. -c python_doctor.yaml -o runs/latest.md --json-output runs/latest.json --no-state >/dev/null 2>&1
python3 $FK/scripts/delta.py runs/baseline.json runs/latest.json --dispositions dispositions.json --json > $W/delta_new.json; log "fresh scan + delta exit=$?"
log "### C2c findings_to_slices on fresh report"; python3 $R/findings_to_slices.py runs/latest.json $W/delta_new.json >>$L 2>&1; log "exit=$?"
cp $W/ops.fixed ../src/calc/ops.py
