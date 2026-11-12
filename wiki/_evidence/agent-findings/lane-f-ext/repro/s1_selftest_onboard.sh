#!/usr/bin/env bash
# Stage 1: fieldkit selftest + onboard.py happy path and edges.
source "$(dirname "$0")/env.sh"; set -u; cd $W
python3 $FK/scripts/selftest.py --python $W/venv/bin/python > $LOGS/s1_selftest.md 2>&1; echo "exit=$?" >> $LOGS/s1_selftest.md
L=$LOGS/s1_onboard.log; : > $L
mv proj/.venv $W/proj-venv-hidden   # hide project env (outside the repo) to observe the no-runner path
log "### O0 no runner anywhere (no project venv, none on PATH)"; python3 $FK/scripts/onboard.py proj >>$L 2>&1; log "exit=$?"
log "### O0b --python <symlinked venv python> (absolute)"; python3 $FK/scripts/onboard.py proj --python $W/venv/bin/python >>$L 2>&1; log "exit=$?"
log "### O0c --python <venv --copies python>"; python3 $FK/scripts/onboard.py proj --python $W/venvc/bin/python >>$L 2>&1; log "exit=$?"
mv $W/proj-venv-hidden proj/.venv
log "### O1 plan with project .venv"; python3 $FK/scripts/onboard.py proj >>$L 2>&1; log "exit=$?"
log "--- git status after plan:"; (cd proj && git status --porcelain --ignored) >>$L
log "### O2 --apply --baseline"; python3 $FK/scripts/onboard.py proj --apply --baseline >>$L 2>&1; log "exit=$?"
log "--- files:"; (cd proj && find .somnus-debug -type f | sort; git status --porcelain --ignored) >>$L
log "### O3 re-apply (never overwrites)"; python3 $FK/scripts/onboard.py proj --apply >>$L 2>&1; log "exit=$?"
cp proj/.somnus-debug/PROFILE.md $LOGS/s1_PROFILE.md.txt
cp proj/.somnus-debug/python_doctor.yaml $LOGS/s1_profile_python_doctor.yaml.txt
cp proj/.somnus-debug/pycache.yaml $LOGS/s1_profile_pycache.yaml.txt
python3 -c "
import json;d=json.load(open('proj/.somnus-debug/runs/baseline.json'))
print('top-level keys:',sorted(d)); print('summary:',d['summary']); print('issue keys:',sorted(d['issues'][0])); print('file keys:',sorted(d['files'][0])); print('function keys:',sorted(d['files'][1]['functions'][0])); print('state_delta:',d['state_delta']); print('dependency_graph keys:',sorted(d['dependency_graph'])); print('edge keys:',sorted(d['dependency_graph']['edges'][0]))" > $LOGS/s1_doctor_json_shape.txt 2>&1
L=$LOGS/s1_onboard_edges.log; : > $L
for v in o_root o_bad o3; do rm -rf $v; mkdir -p $v; cp -r proj/src $v/; ln -s $W/proj/.venv $v/.venv; done
cp $REPO/python_doctor.yaml o_root/python_doctor.yaml
printf 'severity_exit_level: "bogus"\n' > o_bad/python_doctor.yaml
log "### E-O1 adopt repo-root python_doctor.yaml (Somnus globs) with --apply --baseline"; python3 $FK/scripts/onboard.py o_root --apply --baseline >>$L 2>&1; log "exit=$?"; ls -a o_root/.somnus-debug >>$L 2>&1
log "--- PROFILE.md verification line written despite coverage failure:"; grep "Verification scan" o_root/.somnus-debug/PROFILE.md >>$L
log "### E-O1b re-run plan: profile now reported present"; python3 $FK/scripts/onboard.py o_root > $W/eo1b.txt 2>&1; rc=$?; grep -oE "profile: (True|False)|FAIL.*" $W/eo1b.txt >>$L; log "exit=$rc"
log "### E-O2 adopt invalid root config (doctor exit 4)"; python3 $FK/scripts/onboard.py o_bad >>$L 2>&1; log "exit=$?"
log "### E-O3 --baseline without --apply, no config"; python3 $FK/scripts/onboard.py o3 --baseline 2>&1 | tail -2 >>$L; log "exit=${PIPESTATUS[0]}"
log "### E-O4 repo not a directory"; python3 $FK/scripts/onboard.py $W/nonexistent 2>&1 | tail -1 >>$L; log "exit=${PIPESTATUS[0]}"
