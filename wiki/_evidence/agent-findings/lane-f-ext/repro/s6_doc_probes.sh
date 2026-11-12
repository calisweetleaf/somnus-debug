#!/usr/bin/env bash
# Stage 6: targeted probes for doc claims (MANUAL / QUICKSTART / README).
source "$(dirname "$0")/env.sh"; set -u; cd $W
PY=$W/venv/bin/python; L=$LOGS/s6_doc_probes.log; : > $L
rm -rf dp && mkdir -p dp/proj/src/pkg dp/run && cd dp/run
printf '"""Top-level module directly under src."""\nVALUE = 1\n' > ../proj/src/top.py
printf '"""Package module docstring here."""\nVALUE = 2\n' > ../proj/src/pkg/mod.py
$PY -m somnus_debug.cli doctor init-config -o base.yaml >/dev/null
log "### P1 init-config output contains comments? lines starting with '#': $(grep -c '^#' base.yaml)"
cp base.yaml glob.yaml; python3 - <<'P'
s=open('glob.yaml').read().replace('include_patterns:\n  - "*.py"\n','include_patterns:\n  - "src/**/*.py"\n'); open('glob.yaml','w').write(s)
P
$PY -m somnus_debug.cli doctor scan ../proj -c glob.yaml --no-state -o g.md --json-output g.json >/dev/null 2>&1
log "### P2 MANUAL example include 'src/**/*.py' (fnmatch, no ** semantics): scanned=$(python3 -c "import json;print([f['relative_path'] for f in json.load(open('g.json'))['files']])") (src/top.py and src/pkg/mod.py exist)"
$PY -m somnus_debug.cli doctor scan ../proj --no-state -o only_md.md >/dev/null 2>&1
log "### P3 scan with -o only (no --json-output): json written? $(ls only_md.json 2>/dev/null || echo no)"
printf '"""Module docstring long enough here."""\n# TODO tidy\nVALUE = 1\n' > ../proj/src/pkg/todo.py
rm -f ../proj/src/top.py ../proj/src/pkg/mod.py
cp base.yaml minor.yaml && sed -i 's/severity_exit_level: "serious"/severity_exit_level: "minor"/' minor.yaml && sed -i 's/  todos: "minor"/  todos: "info"/' minor.yaml
$PY -m somnus_debug.cli doctor scan ../proj -c minor.yaml --no-state -o m.md --json-output m.json >/dev/null 2>&1; rc=$?
log "### P4 gate=minor with only an info-level finding: exit=$rc summary=$(python3 -c "import json;s=json.load(open('m.json'))['summary'];print({k:s[k] for k in ('critical_issues','serious_issues','minor_issues','info_issues')})")"
printf '"""Module docstring long enough here."""\n\n\ndef outer(x: int) -> int:\n    """Outer function docstring."""\n    def inner():\n        pass\n    return inner() or x\n' > ../proj/src/pkg/todo.py
cp base.yaml ig.yaml && sed -i 's/  - "__str__"/  - "__str__"\n  - "outer"/' ig.yaml
$PY -m somnus_debug.cli doctor scan ../proj -c ig.yaml --no-state -o i.md --json-output i.json >/dev/null 2>&1
log "### P5 ignore_functions: [outer] also hides nested inner()? issues for outer/inner: $(python3 -c "import json;print([(i['category'],i['symbol']) for i in json.load(open('i.json'))['issues'] if 'outer' in i['symbol'] or 'inner' in i['symbol']])")"
printf '"""Module docstring long enough here."""\n\n\nclass Thing:\n    """Thing class docstring here."""\n\n    def run(self):\n        pass\n' > ../proj/src/pkg/todo.py
cp base.yaml igc.yaml && sed -i 's/^ignore_classes: \[\]/ignore_classes:\n  - "Thing"/' igc.yaml
$PY -m somnus_debug.cli doctor scan ../proj -c igc.yaml --no-state -o c.md --json-output c.json >/dev/null 2>&1
log "### P6 ignore_classes: [Thing] -> remaining issues on Thing/Thing.run: $(python3 -c "import json;print([(i['category'],i['symbol']) for i in json.load(open('c.json'))['issues'] if 'Thing' in i['symbol']])")"
$PY -m somnus_debug.cli structure ../proj/src/pkg/todo.py -o idx/out.md > s.out 2>&1; rc=$?
log "### P7 structure -o: exit=$rc stdout/stderr bytes=$(wc -c < s.out) file written=$(test -f idx/out.md && echo yes)"
$PY -m somnus_debug.cli structure ../proj/src/pkg/todo.py --update-doc idx/never_existed.md > s2.out 2>&1; rc=$?
log "### P8 structure --update-doc on a path that does not exist: exit=$rc created=$(test -f idx/never_existed.md && echo yes)"
log "### P9 version sources: pyproject=$(grep -m1 '^version' $REPO/pyproject.toml) __init__=$(grep -m1 '__version__ =' $REPO/src/somnus_debug/__init__.py)"
log "### P10 smoke test functions in tests/test_cli_smoke.py: $(grep -c '^def test_' $REPO/tests/test_cli_smoke.py)"
log "### P11 pycache CleanerConfig.dry_run default: $(grep -n 'dry_run: bool' $REPO/src/somnus_debug/pycache_cleaner/core.py)"
