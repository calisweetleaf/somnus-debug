#!/usr/bin/env bash
# W3 configuration recipes, executed end to end in /tmp/w3r (never in the repo).
set -u
export PYTHONDONTWRITEBYTECODE=1 PYTHONWARNINGS=ignore
REPO=/workspace/projects/69c23182-5d69-4d5c-ae10-5cdad587b9d3/forge/somnus-debug
FK=$REPO/skills/somnus-debug-fieldkit/scripts
W=/tmp/w3r
rm -rf "$W"; mkdir -p "$W/bin"
cat > "$W/bin/somnus-debug" <<EOF
#!/bin/sh
PYTHONPATH=$REPO/src exec python3 -m somnus_debug.cli "\$@"
EOF
chmod +x "$W/bin/somnus-debug"; export PATH="$W/bin:$PATH"
say(){ printf '\n### %s\n' "$*"; }
run(){ printf '$ %s\n' "$*"; "$@"; printf '[exit=%s]\n' "$?"; }

# fixture project: one serious security finding, one stub, a TODO, and a real package dir named build/
mkdir -p "$W/app/myapp/build" "$W/app/tests" "$W/app/.venv/lib"
printf '"""Package docstring that is long enough."""\n' > "$W/app/myapp/__init__.py"
cat > "$W/app/myapp/core.py" <<'EOF'
"""Core module docstring that is long enough."""
import os


def risky(cmd: str) -> int:
    """Run a shell command (security finding)."""
    # TODO: replace with subprocess list form
    status = os.system(cmd)
    result = int(status)
    checked = result + 0
    return checked
EOF
printf '"""Build helpers docstring long enough."""\n\n\ndef helper() -> None:\n    """Helper that is only a stub."""\n    pass\n' > "$W/app/myapp/build/gen.py"
printf 'x = 1\n' > "$W/app/.venv/lib/junk.py"
mkdir -p "$W/scratch"; cd "$W/scratch"

say "R1 make doctor use your config (it never auto-loads python_doctor.yaml)"
run somnus-debug doctor init-config -o "$W/app/python_doctor.yaml"
sed -i 's/^severity_exit_level: .*/severity_exit_level: "critical"/' "$W/app/python_doctor.yaml"
run somnus-debug doctor scan "$W/app" --no-state -o r1.md
run somnus-debug doctor scan "$W/app" --no-state -o r1.md -c "$W/app/python_doctor.yaml"

say "R2 report-only mode: the gate value must be QUOTED"
printf 'severity_exit_level: none\n' > r2-bad.yaml
printf 'severity_exit_level: "none"\n' > r2.yaml
run somnus-debug doctor scan "$W/app" --no-state -o r2.md -c r2-bad.yaml 2>&1
run somnus-debug doctor scan "$W/app" --no-state -o r2.md -c r2.yaml

say "R3 CI gate that also fails a zero-file scan"
cat > gate.sh <<'EOF'
#!/usr/bin/env bash
out=$(somnus-debug doctor scan "$1" --no-state -c "$2" -o "$3" 2>&1); code=$?
echo "$out" | head -1
files=$(echo "$out" | sed -n 's/^Scan complete: files=\([0-9]*\),.*/\1/p')
if [ "${files:-0}" -eq 0 ]; then echo "gate: zero files scanned or doctor failed (exit $code)"; exit 3; fi
exit $code
EOF
chmod +x gate.sh
printf 'include_patterns: []\nseverity_exit_level: "none"\n' > r3-empty.yaml
run ./gate.sh "$W/app" r3-empty.yaml r3.md
run ./gate.sh "$W/app" r2.yaml r3.md

say "R4 keep every artifact out of the repository"
run somnus-debug doctor scan "$W/app" -c r2.yaml -o "$W/scratch/out/report.md" --json-output "$W/scratch/out/report.json" --no-state
printf 'severity_exit_level: "none"\nstate_dir: "%s/state"\n' "$W/scratch" > r4.yaml
run somnus-debug doctor scan "$W/app" -c r4.yaml -o "$W/scratch/out/r4.md"
run somnus-debug doctor history "$W/app" -c r4.yaml --limit 1
printf 'repo after R4: '; ls -A "$W/app" | tr '\n' ' '; echo

say "R5 narrow coverage with globs that match ('*' crosses '/'; '**' is not recursive)"
cat > lsfiles.py <<'EOF'
import sys, pathlib
from somnus_debug.doctor.core import ConfigManager, ProjectFileIndex
cm = ConfigManager(pathlib.Path(sys.argv[2]))
idx = ProjectFileIndex(pathlib.Path(sys.argv[1]), cm.config)
print(sorted(str(p.relative_to(idx.project_root)) for p in idx.python_files))
EOF
printf 'include_patterns:\n  - "myapp/**/*.py"\n' > r5-wrong.yaml
printf 'include_patterns:\n  - "myapp/*.py"\n' > r5.yaml
printf '$ lsfiles r5-wrong.yaml: '; PYTHONPATH=$REPO/src python3 lsfiles.py "$W/app" r5-wrong.yaml
printf '$ lsfiles r5.yaml:       '; PYTHONPATH=$REPO/src python3 lsfiles.py "$W/app" r5.yaml

say "R6 stop the default ignores from hiding a real package dir named build/"
cat > r6.yaml <<'EOF'
ignore_patterns:
  - "__pycache__/*"
  - "*.pyc"
  - ".git/*"
  - ".venv/*"
  - ".python_doctor/*"
  - "dist/*"
EOF
printf '$ lsfiles defaults (r2.yaml): '; PYTHONPATH=$REPO/src python3 lsfiles.py "$W/app" r2.yaml
printf '$ lsfiles r6.yaml:            '; PYTHONPATH=$REPO/src python3 lsfiles.py "$W/app" r6.yaml

say "R7 re-severity one category and switch one detector off (severity_levels merges, lists replace)"
printf 'severity_levels:\n  security_risks: "info"\ndetect_dependency_cycles: false\n' > r7.yaml
run somnus-debug doctor scan "$W/app" --no-state -o r7.md -c r7.yaml

say "R8 src layout: put src on PYTHONPATH so own imports resolve"
mkdir -p "$W/srcapp/src/calc" "$W/srcapp/tests"
printf '"""Calc package docstring long enough."""\n' > "$W/srcapp/src/calc/__init__.py"
printf '"""Tests docstring that is long enough."""\nimport calc\n\nVALUE = calc\n' > "$W/srcapp/tests/test_c.py"
run somnus-debug doctor scan "$W/srcapp" --no-state -o r8.md -c r2.yaml
python3 -c "import json;print('missing_imports:',[i['message'] for i in json.load(open('r8.json'))['issues'] if i['category']=='missing_imports'])"
printf '$ PYTHONPATH=%s/src:<repo>/src python3 -m somnus_debug.cli doctor scan ...\n' "$W/srcapp"
PYTHONPATH=$W/srcapp/src:$REPO/src python3 -m somnus_debug.cli doctor scan "$W/srcapp" --no-state -o r8b.md -c r2.yaml | head -1
python3 -c "import json;print('missing_imports:',[i['message'] for i in json.load(open('r8b.json'))['issues'] if i['category']=='missing_imports'])"

say "R9 safe pycache-clean: absolute roots, name-only excludes, dry-run config plus a separate live config"
mkdir -p "$W/tree/a/__pycache__" "$W/tree/node_modules/__pycache__"; touch "$W/tree/a/__pycache__/m.pyc" "$W/tree/node_modules/__pycache__/n.pyc" "$W/tree/a/x.pyc"
cat > pycache.dry.yaml <<EOF
roots:
  - "$W/tree"
exclude:
  - "node_modules"
  - ".git"
dry_run: true
EOF
sed 's/^dry_run: true/dry_run: false/' pycache.dry.yaml > pycache.live.yaml
run somnus-debug pycache-clean --config pycache.dry.yaml --verbose
printf 'left after dry run: %s\n' "$(find "$W/tree" -name '*.pyc' | wc -l)"
run somnus-debug pycache-clean --config pycache.live.yaml
printf 'left after live run: %s (node_modules kept)\n' "$(find "$W/tree" -name '*.pyc' | wc -l)"

say "R10 run_test.py artifacts inside the repo"
mkdir -p "$W/hrepo"
run somnus-debug init-test-harness "$W/hrepo/tools" --no-contract
( cd "$W/scratch" && python3 "$W/hrepo/tools/run_test.py" >/dev/null 2>&1; echo "[run_test exit=$?]" )
printf 'artifact root: '; ls -d "$W"/hrepo/test-runs/* | head -1
( cd "$W/scratch" && SINGLE_TEST_OUTPUT_DIR="$W/scratch/arts" python3 "$W/hrepo/tools/run_test.py" >/dev/null 2>&1; echo "[run_test exit=$?]" )
printf 'artifact root: '; ls -d "$W"/scratch/arts/* | head -1

say "R11 programmatic configuration without a file"
cat > r11.py <<EOF
import dataclasses, pathlib
from somnus_debug.doctor.core import ConfigManager, ProjectScanner, Severity
cm = ConfigManager(None)
cm.config = dataclasses.replace(cm.config, include_patterns=("myapp/*.py",),
    severity_levels={**cm.config.severity_levels, "security_risks": Severity.INFO})
result = ProjectScanner(pathlib.Path("$W/app"), cm).scan({})
print(result.summary.files_scanned, result.summary.serious_issues, result.summary.info_issues)
EOF
printf '$ python3 r11.py -> files serious info: '; PYTHONPATH=$REPO/src python3 r11.py

say "R12 fieldkit: onboard a repo, then gate on delta with a disposition"
rm -f "$W/app/python_doctor.yaml"
printf '$ python3 onboard.py %s --apply --baseline\n' "$W/app"; python3 "$FK/onboard.py" "$W/app" --apply --baseline > ob.log 2>&1; echo "[exit=$?]"; grep -E "^Doctor config|^Verify|^Baseline|^- .*somnus-debug/" ob.log
cd "$W/app/.somnus-debug"
printf '\n\ndef later() -> None:\n    """Added after the baseline."""\n    pass\n' >> "$W/app/myapp/core.py"
somnus-debug doctor scan .. -c python_doctor.yaml -o runs/latest.md --json-output runs/latest.json >/dev/null
echo '$ delta.py runs/baseline.json runs/latest.json --json'; python3 "$FK/delta.py" runs/baseline.json runs/latest.json --json > d1.json; echo "[exit=$?]"; python3 -c "import json;d=json.load(open('d1.json'));print('exit field',d['exit'],'regressions',[(x['category'],x['symbol']) for x in d['regressions']])"
echo '[{"category":"stubs","file":"myapp/core.py","symbol":"later","reason":"placeholder accepted until ticket closes"}]' > dispositions.json
echo '$ delta.py runs/baseline.json runs/latest.json --dispositions dispositions.json'; python3 "$FK/delta.py" runs/baseline.json runs/latest.json --dispositions dispositions.json > d2.md; echo "[exit=$?]"; grep -E "CLEAN|REGRESSION" d2.md
echo; echo "ALL RECIPES DONE"
