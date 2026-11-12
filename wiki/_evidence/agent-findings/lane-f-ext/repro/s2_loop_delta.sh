#!/usr/bin/env bash
# Stage 2: baseline -> regression -> delta -> disposition -> fix loop, plus delta.py edge cases.
source "$(dirname "$0")/env.sh"; set -u; cd $W
L=$LOGS/s2_loop.log; : > $L
DELTA="python3 $FK/scripts/delta.py"
cp proj/src/calc/ops.py $W/ops.orig
cat >> proj/src/calc/ops.py <<'P'


def divide(a: int, b: int) -> int:
    """Divide two integers, someday for real."""
    pass


def safe_int(value: str) -> int:
    """Parse an integer, swallowing errors quietly."""
    try:
        return int(value)
    except ValueError:
        log_it = value
        return 0
P
python3 - <<'P'
p='/tmp/lane-f/proj/tests/test_ops.py';s=open(p).read();s=s.replace('from calc.ops import add\n','from calc.ops import add\n\n\nVALUE_A = 1\nVALUE_B = 2\n');open(p,'w').write(s)
P
cd proj/.somnus-debug
log "### L1 rescan after regression (stub + silent failure; test_add moved down 4 lines)"; $PRUN doctor scan .. -c python_doctor.yaml -o runs/latest.md --json-output runs/latest.json >>$L 2>&1; log "doctor exit=$?"
log "### L2 delta (empty dispositions)"; $DELTA runs/baseline.json runs/latest.json --dispositions dispositions.json >>$L 2>&1; log "delta exit=$?"
cat > dispositions.json <<'P'
[
  {"category": "silent_failures", "file": "src/calc/*.py", "symbol": "safe_int", "reason": "lenient parser by contract; callers treat 0 as absent"},
  {"category": "security_risks", "file": "src/*", "reason": "deliberately broad: matches nothing today"}
]
P
log "### L3 delta with dispositions (stub still open; one stale broad entry)"; $DELTA runs/baseline.json runs/latest.json --dispositions dispositions.json >>$L 2>&1; log "delta exit=$?"
log "### L4 delta --json"; $DELTA runs/baseline.json runs/latest.json --dispositions dispositions.json --json >>$L 2>&1; log "delta exit=$?"
python3 - <<'P'
p='/tmp/lane-f/proj/src/calc/ops.py';s=open(p).read()
s=s.replace('    """Divide two integers, someday for real."""\n    pass\n','    """Divide two integers, raising on a zero divisor."""\n    if b == 0:\n        raise ZeroDivisionError("divisor is zero")\n    quotient = a // b\n    checked = int(quotient)\n    return checked\n')
open(p,'w').write(s)
P
log "### L5 rescan after fixing the stub"; $PRUN doctor scan .. -c python_doctor.yaml -o runs/latest.md --json-output runs/latest.json >>$L 2>&1; log "doctor exit=$?"
log "### L6 delta after fix"; $DELTA runs/baseline.json runs/latest.json --dispositions dispositions.json >>$L 2>&1; log "delta exit=$?"
cp ../src/calc/ops.py $W/ops.fixed
printf "$REGRESS_RISKY" >> ../src/calc/ops.py
log "### L7 NEW os.system regression while the broad 'stale' security_risks disposition is still present"; $PRUN doctor scan .. -c python_doctor.yaml -o $W/l7.md --json-output $W/l7.json --no-state >>$L 2>&1; log "doctor exit=$?"
$DELTA runs/baseline.json $W/l7.json --dispositions dispositions.json >>$L 2>&1; log "delta exit=$?"
cp $W/ops.fixed ../src/calc/ops.py
# ---------- delta edge cases ----------
L=$LOGS/s2_delta_edges.log; : > $L
sed 's#  - "dist/\*"#  - "dist/*"\n  - "tests/*"#' python_doctor.yaml > $W/cfg_notests.yaml
log "### D1 coverage drop: latest config ignores tests/"; $PRUN doctor scan .. -c $W/cfg_notests.yaml -o $W/d1.md --json-output $W/d1.json --no-state >>$L 2>&1; log "doctor exit=$?"
$DELTA runs/baseline.json $W/d1.json --dispositions dispositions.json >>$L 2>&1; log "delta exit=$?"
sed 's#  - "\*.py"#  - "tools/*.py"#' python_doctor.yaml > $W/cfg_zero.yaml
log "### D2 zero-file latest"; $PRUN doctor scan .. -c $W/cfg_zero.yaml -o $W/d2.md --json-output $W/d2.json --no-state >>$L 2>&1; log "doctor exit=$?"
$DELTA runs/baseline.json $W/d2.json 2>&1 | grep '\*\*' >>$L; log "delta exit=${PIPESTATUS[0]}"
sed 's#  stubs: "serious"#  stubs: "info"#' python_doctor.yaml > $W/cfg_stubinfo.yaml
printf '\n\ndef later(x: int) -> int:\n    """Placeholder that will be done later."""\n    pass\n' >> ../src/calc/ops.py
log "### D3 new stub; LATEST config remaps stubs -> info (baseline used profile config)"; $PRUN doctor scan .. -c $W/cfg_stubinfo.yaml -o $W/d3.md --json-output $W/d3.json --no-state >>$L 2>&1; log "doctor exit=$?"
$DELTA runs/baseline.json $W/d3.json --dispositions dispositions.json 2>&1 | grep -E '\*\*|stubs' >>$L; log "delta exit=${PIPESTATUS[0]}"
python3 -c "import json;a=json.load(open('runs/baseline.json'));b=json.load(open('$W/d3.json'));print('config_hash differs between baseline and latest:',a['config_hash']!=b['config_hash'],'(delta.py never reads config_hash)')" >>$L
log "### D3b same stub, profile config"; $PRUN doctor scan .. -c python_doctor.yaml -o $W/d3b.md --json-output $W/d3b.json --no-state >>$L 2>&1; log "doctor exit=$?"
$DELTA runs/baseline.json $W/d3b.json --dispositions dispositions.json 2>&1 | grep -E '\*\*|stubs' >>$L; log "delta exit=${PIPESTATUS[0]}"
cp $W/ops.fixed ../src/calc/ops.py
echo '{}' > $W/bad.json
log "### D4 latest is not a doctor report"; $DELTA runs/baseline.json $W/bad.json >>$L 2>&1; log "delta exit=$?"
log "### D5 argparse usage error (missing LATEST)"; $DELTA runs/baseline.json >>$L 2>&1; log "delta exit=$?"
echo '[{"category":"stubs","file":"*"}]' > $W/baddisp.json
log "### D6 disposition without reason"; $DELTA runs/baseline.json runs/latest.json --dispositions $W/baddisp.json >>$L 2>&1; log "delta exit=$?"
log "### D7 dispositions path does not exist"; $DELTA runs/baseline.json runs/latest.json --dispositions $W/nope.json 2>&1 | grep -E 'note|\*\*' >>$L; log "delta exit=${PIPESTATUS[0]}"
python3 -c "
import json;d=json.load(open('runs/latest.json'));d['issues'][0].pop('category');json.dump(d,open('$W/nocat.json','w'))"
log "### D8 issue object missing 'category'"; $DELTA runs/baseline.json $W/nocat.json 2>&1 | tail -1 >>$L; log "delta exit=${PIPESTATUS[0]}"
log "### D9 rename a function (identity includes symbol+message)"
sed 's/def safe_int(/def lenient_int(/' ../src/calc/ops.py > $W/ops.renamed; cp $W/ops.renamed ../src/calc/ops.py
$PRUN doctor scan .. -c python_doctor.yaml -o $W/d9.md --json-output $W/d9.json --no-state >/dev/null 2>&1
$DELTA runs/baseline.json $W/d9.json --dispositions dispositions.json 2>&1 | grep -E '\*\*|New \(open|silent|Stale|safe_int' >>$L; log "delta exit=${PIPESTATUS[0]}"
cp $W/ops.fixed ../src/calc/ops.py
# ---------- venv detection by pyvenv.cfg under a nonstandard name ----------
cd $W; rm -rf o5 && mkdir -p o5 && cp -r proj/src o5/ && cp -a proj/.venv o5/tools-env
L=$LOGS/s1_onboard_edges.log
log "### E-O5 venv under nonstandard dir name (tools-env) is found via pyvenv.cfg"; python3 $FK/scripts/onboard.py o5 2>&1 | grep -E "Noise|runner:|note: Project" >>$L; log "exit=${PIPESTATUS[0]}"
