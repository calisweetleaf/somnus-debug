#!/usr/bin/env bash
# Stage 6 (integrations + failure probes): N1 harness with pytest, N2 harness + doctor + delta, N3 selftest,
# F failure probes for delta/onboard, E11 pycache targets. Needs stage 5 state in /tmp/w4/proj.
source "$(dirname "$0")/env.sh"; set -u
exec > "$LOGS/stage6_integrations.log" 2>&1
MAN='python3 -c "import json,sys,glob;m=json.load(open(sorted(glob.glob(\"test-runs/*/manifest.json\"))[-1]));print(m[\"verdict\"],[(c[\"name\"],c[\"passed\"]) for c in m[\"acceptance\"][\"checks\"]],m[\"result\"][\"metrics\"],m[\"environment\"][\"project_root\"],m[\"error\"] and m[\"error\"][\"type\"])"'
echo "## N1 harness: pytest only"
cd "$W" && rm -rf proj_h && cp -r proj proj_h && cd proj_h
run ".venv/bin/python -m somnus_debug.cli init-test-harness single_test 2>&1 | grep -v -e SyntaxWarning -e 'Windows long'"
run ".venv/bin/python -m somnus_debug.cli init-test-harness single_test 2>&1 | grep -v -e SyntaxWarning -e 'Windows long'"
run "grep -n '^TEST_NAME\|^def execute_test\|# Harness internals' single_test/run_test.py"
run "python3 $HERE/surface_pytest.py single_test/run_test.py"
run ".venv/bin/python single_test/run_test.py 2>/dev/null"
run "ls test-runs/*/"
run "$MAN"
sed -i 's/expected = 3/expected = 4/' tests/test_store.py; sleep 1
run ".venv/bin/python single_test/run_test.py 2>/dev/null | python3 -c 'import json,sys;print(json.load(sys.stdin)[\"verdict\"])'"
run "$MAN"
sed -i 's/expected = 4/expected = 3/' tests/test_store.py
echo; echo "## N2 harness + doctor + delta"
cd "$W" && rm -rf proj_h2 && cp -r proj proj_h2 && cd proj_h2
run ".venv/bin/python -m somnus_debug.cli init-test-harness single_test --no-contract 2>/dev/null"
run "python3 $REC/harness_doctor_surface.py single_test/run_test.py"
export SD_PYTHON=$W/proj_h2/.venv/bin/python FIELDKIT=$FK TEST_PYTHON=$W/proj_h2/.venv/bin/python
run "python3 single_test/run_test.py 2>/dev/null | python3 -c 'import json,sys;print(json.load(sys.stdin)[\"verdict\"])'"
run "python3 -c \"import json,glob;m=json.load(open(sorted(glob.glob('test-runs/*/manifest.json'))[-1]));print([(c['name'],c['passed']) for c in m['acceptance']['checks']]);print(sorted((r['category'],r['symbol']) for r in m['result']['evidence']['delta']['regressions']))\""
python3 - <<'P'
import json
from pathlib import Path
p = Path(".somnus-debug/dispositions.json")
d = json.loads(p.read_text())
H = "single_test/run_test.py"
d += [
 {"category": "security_risks", "file": H, "symbol": "execute_test", "reason": "Harness runs fixed argv lists (pytest, doctor, delta.py) with no shell."},
 {"category": "security_risks", "file": H, "symbol": "<module>", "reason": "Template _run_command (private, so attributed to <module>) runs argv lists with no shell."},
 {"category": "broad_exceptions", "file": H, "symbol": "*", "reason": "Template contract: any Exception in execute_test becomes a FAIL verdict with artifacts."},
 {"category": "silent_failures", "file": H, "symbol": "<module>", "reason": "Template _setup_logger handler cleanup; attributed to <module> because the function is private."},
 {"category": "suspicious_short_classes", "file": H, "symbol": "Check", "reason": "Frozen dataclass; doctor exempts only plain @dataclass."},
 {"category": "suspicious_short_classes", "file": H, "symbol": "TestContext", "reason": "Frozen dataclass; doctor exempts only plain @dataclass."},
]
p.write_text(json.dumps(d, indent=2) + "\n")
P
run "python3 -c \"import json;print(len(json.load(open('.somnus-debug/dispositions.json'))), 'dispositions')\""
sleep 1
run "python3 single_test/run_test.py 2>/dev/null | python3 -c 'import json,sys;print(json.load(sys.stdin)[\"verdict\"])'"
run "python3 -c \"import json,glob;m=json.load(open(sorted(glob.glob('test-runs/*/manifest.json'))[-1]));print([(c['name'],c['passed']) for c in m['acceptance']['checks']], m['result']['metrics']); import os; print(sorted(os.listdir(os.path.dirname(sorted(glob.glob('test-runs/*/manifest.json'))[-1]))))\""
cat >> src/inventory/store.py <<'P'


def purge(path: str) -> int:
    """Delete a path through the shell; this is the regression."""
    import os
    status = os.system("rm -rf " + path)
    code = int(status)
    return code
P
sleep 1
run "python3 single_test/run_test.py 2>/dev/null | python3 -c 'import json,sys;print(json.load(sys.stdin)[\"verdict\"])'"
run "python3 -c \"import json,glob;m=json.load(open(sorted(glob.glob('test-runs/*/manifest.json'))[-1]));print([(r['category'],r['symbol']) for r in m['result']['evidence']['delta']['regressions']])\""
unset SD_PYTHON; sleep 1
run "python3 single_test/run_test.py 2>/dev/null | python3 -c 'import json,sys;print(json.load(sys.stdin)[\"verdict\"])'"
run "grep -m1 KeyError \$(ls -d test-runs/*/ | tail -1)test.log"
echo; echo "## N3 selftest"
rm -rf "$W/n3" && mkdir -p "$W/n3" && cd "$W/n3"
run "python3 $FK/scripts/selftest.py --python $W/venv/bin/python > selftest.md; tail -2 selftest.md; grep -c '^| PASS' selftest.md"
run "env PATH=/usr/bin:/bin python3 $FK/scripts/selftest.py"
run "ls"
echo; echo "## F failure probes"
rm -rf "$W/f" && mkdir -p "$W/f" && cd "$W/f"
D="python3 $FK/scripts/delta.py"; B=$W/proj/.somnus-debug/runs/baseline.json
run "$D $B 2>&1 | tail -1"
echo '{}' > empty.json
run "$D $B empty.json"
python3 -c "import json;r=json.load(open('$B'));r['issues']=[{'file_path':'x.py'}];json.dump(r,open('noncat.json','w'))"
run "$D $B noncat.json 2>&1 | tail -1"
run "$D $B $B --dispositions missing.json > /dev/null"
echo '[{"category":"stubs","file":"x.py"}]' > noreason.json
run "$D $B $B --dispositions noreason.json"
cd "$W/proj_h2/.somnus-debug"
run "env PYTHONPATH=../src ../.venv/bin/python -m somnus_debug.cli doctor scan .. -c python_doctor.yaml --no-state -o $W/f/l.md --json-output $W/f/l.json > /dev/null 2>&1"
run "$D runs/baseline.json $W/f/l.json --dispositions dispositions.json --json | python3 -c 'import json,sys;d=json.load(sys.stdin);print(\"narrow only: exit\",d[\"exit\"],[(r[\"category\"],r[\"symbol\"]) for r in d[\"regressions\"]])'"
python3 -c "import json;d=json.load(open('dispositions.json'));d.append({'category':'security_risks','file':'src/*','reason':'old broad entry'});json.dump(d,open('$W/f/plusbroad.json','w'))"
run "$D runs/baseline.json $W/f/l.json --dispositions $W/f/plusbroad.json --json | python3 -c 'import json,sys;d=json.load(sys.stdin);print(\"plus broad: exit\",d[\"exit\"],[(r[\"category\"],r[\"symbol\"]) for r in d[\"regressions\"]],\"stale\",len(d[\"stale_dispositions\"]))'"
cd "$W"
run "python3 $FK/scripts/onboard.py $W/proj --python $W/venv/bin/python 2>&1 | tail -3"
run "ls -l $W/venv/bin/python | sed 's/.*venv/venv/'"
echo; echo "## E11 pycache targets"
rm -rf "$W/c1" && mkdir -p "$W/c1/tree/a/build_cache" && cd "$W/c1" && touch tree/a/x.bak tree/a/keep.py tree/a/build_cache/blob
printf 'roots: ["%s"]\ntargets: ["*.bak", "build_cache"]\n' "$W/c1/tree" > c.yaml
run "cat c.yaml"
run "$SD pycache-clean --config c.yaml 2>&1 | grep -v -e SyntaxWarning -e 'Windows long'"
run "find tree | sort"
