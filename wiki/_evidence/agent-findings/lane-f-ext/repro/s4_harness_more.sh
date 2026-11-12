#!/usr/bin/env bash
# Stage 4: harness scaffold (unedited + composed with doctor), pycache-before-doctor, src-layout cycles, self-check.
source "$(dirname "$0")/env.sh"; set -u; cd $W
R=$LANE/recipes; SDB=$W/venv/bin/somnus-debug
# ---------- H: scaffold + unedited template ----------
L=$LOGS/s4_harness.log; : > $L
rm -rf hproj && mkdir hproj && cp -r proj/src proj/tests hproj/
log "### H1 scaffold into repo root"; (cd hproj && $SDB init-test-harness) >>$L 2>&1; log "exit=$?"
log "### H2 scaffold again (refuse)"; (cd hproj && $SDB init-test-harness) >>$L 2>&1; log "exit=$?"
log "### H3 --no-contract into single_test/"; $SDB init-test-harness hproj/single_test --no-contract >>$L 2>&1; log "exit=$?"; ls hproj/single_test >>$L
log "### H4 --force over existing"; $SDB init-test-harness hproj --force >>$L 2>&1; log "exit=$?"
log "### H5 library API: scaffold() return value"; $W/venv/bin/python -c "
from pathlib import Path; from somnus_debug.test_harness.scaffold import scaffold
print(scaffold(Path('$W/hproj/lib_target'), with_contract=False))" >>$L 2>&1; log "exit=$?"
log "### H6 run UNEDITED template from repo root (PROJECT_ROOT defaults to parent of run_test.py's dir)"
(cd hproj && timeout 60 python3 run_test.py) > $W/h6.out 2>/dev/null; rc=$?; cat $W/h6.out >>$L; log "exit=$rc"
M=$(python3 -c "import json;print(json.load(open('$W/h6.out'))['artifacts']['manifest'])"); python3 -c "
import json;m=json.load(open('$M'));print('error:',m['error']['type'],m['error']['message']);print('acceptance:',m['acceptance']);print('environment.project_root:',m['environment']['project_root'])" >>$L
log "### H7 run unedited template from single_test/ (PROJECT_ROOT = repo)"; (cd hproj && timeout 60 python3 single_test/run_test.py) 2>/dev/null | python3 -c "import json,sys;d=json.loads(sys.stdin.read());print(d['verdict'],d['artifacts']['manifest'])" >>$L; log "exit=${PIPESTATUS[0]}"
log "### H8 run_test.py --help (no CLI: runs the test)"; (cd hproj && timeout 60 python3 single_test/run_test.py --help) 2>/dev/null | head -3 >>$L; log "exit=${PIPESTATUS[0]}"
log "### H9 PROJECT_ROOT + SINGLE_TEST_OUTPUT_DIR overrides"; (cd hproj && PROJECT_ROOT=$PWD SINGLE_TEST_OUTPUT_DIR=$W/hruns timeout 60 python3 run_test.py) >/dev/null 2>&1; log "exit=$?"; (cd $W/hruns && find . -type f | sort) >>$L
# ---------- C5: harness + doctor ----------
L=$LOGS/s4_C5.log; : > $L
export SD_PYTHON=$W/proj/.venv/bin/python FIELDKIT=$FK TEST_PYTHON=$W/venv/bin/python
$SDB init-test-harness proj/single_test --no-contract >>$L 2>&1; log "scaffold exit=$?"
python3 $R/harness_doctor_surface.py proj/single_test/run_test.py >>$L 2>&1
log "### C5a clean tree, no harness dispositions yet (scaffolded file is itself scanned)"; (cd proj && python3 single_test/run_test.py 2>/dev/null) > $W/c5a.json; log "harness exit=$?"
M=$(python3 -c "import json;print(json.load(open('$W/c5a.json'))['artifacts']['manifest'])"); python3 -c "
import json;m=json.load(open('$M'));print(m['verdict'],[(c['name'],c['passed']) for c in m['acceptance']['checks']]);d=m['result']['evidence']['delta'];print('regressions:',sorted((r['category'],r['symbol']) for r in d['regressions']));print('added_files:',d['added_files'])" >>$L
python3 - <<'P'
import json;p='/tmp/lane-f/proj/.somnus-debug/dispositions.json';d=json.load(open(p))
d+=[{"category":"security_risks","file":"single_test/run_test.py","reason":"harness scaffold: argv-list subprocess, no shell"},
    {"category":"broad_exceptions","file":"single_test/run_test.py","reason":"harness contract: any exception is a recorded FAIL with artifacts"},
    {"category":"silent_failures","file":"single_test/run_test.py","symbol":"<module>","reason":"template _setup_logger handler.close() cleanup; private fn findings are attributed to <module>"},
    {"category":"suspicious_short_classes","file":"single_test/run_test.py","reason":"@dataclass(frozen=True) value types are not recognised by the dataclass exemption"}]
json.dump(d,open(p,'w'),indent=1)
P
log "### C5b clean tree after harness dispositions"; (cd proj && python3 single_test/run_test.py 2>/dev/null) > $W/c5b.json; log "harness exit=$?"
M=$(python3 -c "import json;print(json.load(open('$W/c5b.json'))['artifacts']['manifest'])"); python3 -c "
import json;m=json.load(open('$M'));print(m['verdict'],[(c['name'],c['passed']) for c in m['acceptance']['checks']],m['result']['metrics'])" >>$L
printf "$REGRESS_RISKY" >> proj/src/calc/ops.py
log "### C5c regression"; (cd proj && python3 single_test/run_test.py 2>/dev/null) > $W/c5c.json; log "harness exit=$?"
M=$(python3 -c "import json;print(json.load(open('$W/c5c.json'))['artifacts']['manifest'])"); python3 -c "
import json;m=json.load(open('$M'));print(m['verdict'],[(c['name'],c['passed']) for c in m['acceptance']['checks']]);print('regressions:',[(r['category'],r['symbol']) for r in m['result']['evidence']['delta']['regressions']])" >>$L
ls $(dirname $M) >>$L
cp $W/ops.fixed proj/src/calc/ops.py
log "### C5d missing env var -> exception -> FAIL with zero checks, traceback in test.log"; (cd proj && env -u SD_PYTHON python3 single_test/run_test.py 2>/dev/null) > $W/c5d.json; log "harness exit=$?"
M=$(python3 -c "import json;print(json.load(open('$W/c5d.json'))['artifacts']['manifest'])"); python3 -c "
import json;m=json.load(open('$M'));print(m['verdict'],m['acceptance']['total_checks'],m['error']['type'],m['error']['message'])" >>$L
# ---------- C4: pycache-clean before doctor ----------
L=$LOGS/s4_C4.log; : > $L
rm -rf c4 c4run && mkdir c4 c4run && cp -r proj/src proj/tests c4/ && python3 -m compileall -q c4 >/dev/null
log "pyc files: $(find c4 -name '*.pyc' | wc -l)"
cd c4run
$SDB doctor scan ../c4 --no-state -o with_pyc.md --json-output with_pyc.json >/dev/null 2>&1; log "scan with pyc exit=$?"
printf 'roots:\n  - "%s"\nexclude:\n  - ".git"\ntargets:\n  - "__pycache__"\n  - "*.pyc"\n  - "*.pyo"\ndry_run: true\nverbose: true\nmax_depth: null\nfollow_symlinks: false\nlog_file: null\n' "$W/c4" > pc.yaml
log "### pycache-clean --dry-run"; $SDB pycache-clean --config pc.yaml --dry-run --verbose >>$L 2>&1; log "exit=$? pyc remaining: $(find ../c4 -name '*.pyc' | wc -l)"
sed -i 's/dry_run: true/dry_run: false/' pc.yaml
log "### pycache-clean live (tmp copy only)"; $SDB pycache-clean --config pc.yaml >>$L 2>&1; log "exit=$? pyc remaining: $(find ../c4 -name '*.pyc' | wc -l)"
$SDB doctor scan ../c4 --no-state -o no_pyc.md --json-output no_pyc.json >/dev/null 2>&1; log "scan after clean exit=$?"
python3 -c "
import json
a=json.load(open('with_pyc.json'));b=json.load(open('no_pyc.json'))
k=lambda r:sorted((i['category'],i['file_path'],i['symbol'],i['message']) for i in r['issues'])
print('files_scanned', a['summary']['files_scanned'], b['summary']['files_scanned'], '| identical issue sets:', k(a)==k(b))" >>$L
cd $W
# ---------- C7: src layout runner vs local cycles ----------
L=$LOGS/s4_C7.log; : > $L
rm -rf c7 && mkdir -p c7/fromimp/src/pkg c7/imp/src/pkg c7/run
for v in fromimp imp; do echo '"""Package docstring long enough here."""' > c7/$v/src/pkg/__init__.py; done
printf '"""Module a docstring long enough."""\nfrom pkg import b\n\nVALUE = b\n' > c7/fromimp/src/pkg/a.py
printf '"""Module b docstring long enough."""\nfrom pkg import a\n\nVALUE = a\n' > c7/fromimp/src/pkg/b.py
printf '"""Module a docstring long enough."""\nimport pkg.b\n\nVALUE = pkg.b\n' > c7/imp/src/pkg/a.py
printf '"""Module b docstring long enough."""\nimport pkg.a\n\nVALUE = pkg.a\n' > c7/imp/src/pkg/b.py
cd c7/run; PY=$W/venv/bin/python
scan(){ label=$1; shift; "$@" > /dev/null 2>&1; python3 -c "
import json;d=json.load(open('o.json'));print('$label |', 'cycles=',d['summary']['dependency_cycles'],'missing=',d['summary']['missing_imports'],'edges=',sorted({(e['source_file'],e['target_file'],e['classification']) for e in d['dependency_graph']['edges']}))" >> $L; }
scan "import pkg.b  | root=repo, no PYTHONPATH" $PY -m somnus_debug.cli doctor scan ../imp --no-state -o o.md --json-output o.json
scan "import pkg.b  | root=repo, PYTHONPATH=src (onboard runner)" env PYTHONPATH=$W/c7/imp/src $PY -m somnus_debug.cli doctor scan ../imp --no-state -o o.md --json-output o.json
scan "import pkg.b  | root=src" $PY -m somnus_debug.cli doctor scan ../imp/src --no-state -o o.md --json-output o.json
scan "from pkg import b | root=src" $PY -m somnus_debug.cli doctor scan ../fromimp/src --no-state -o o.md --json-output o.json
cd $W
# ---------- C8: self-check side effect ----------
L=$LOGS/s4_C8_selfcheck.log; : > $L
P=$($W/venv/bin/python -c "import somnus_debug.doctor.core as c,os;print(os.path.dirname(c.__file__))"); ls $P > $W/sc_before.txt
mkdir -p sc && (cd sc && $SDB doctor self-check --no-state) >>$L 2>&1; log "exit=$?"; ls $P > $W/sc_after.txt
log "--- new files inside the installed package dir:"; diff $W/sc_before.txt $W/sc_after.txt >>$L
