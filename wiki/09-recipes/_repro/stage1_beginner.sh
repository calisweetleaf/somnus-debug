#!/usr/bin/env bash
# Stage 1 (beginner): B1 first scan, B2 one-file index, B3 pycache dry run.
source "$(dirname "$0")/env.sh"; set -u
exec > "$LOGS/stage1_beginner.log" 2>&1
echo "## B1 first scan (cwd $W/b1/out)"; cd "$W/b1/out"
run "$SD doctor init-config -o cfg.yaml"
run "$SD doctor scan ../proj -c cfg.yaml --no-state -o report.md --json-output report.json"
run "ls; ls ../proj"
run "python3 -c \"import json; from collections import Counter; r=json.load(open('report.json')); print(r['summary']); print(Counter((i['severity'],i['category']) for i in r['issues']).most_common())\""
run "python3 -c \"import json; r=json.load(open('report.json')); i=[x for x in r['issues'] if x['category']=='stubs'][0]; print({k:i[k] for k in ('category','severity','file_path','line_number','symbol','message','remediation')})\""
echo; echo "## B2 structure on one file"
run "$SD structure ../proj/pkg/b.py > b_index.md; head -20 b_index.md"
run "$SD structure ../proj/pkg/b.py --no-line-numbers --no-module-functions | sed -n 1,12p"
run "cp $REPO/src/somnus_debug/__init__.py stamped.py && $SD structure stamped.py"
run "sed -n 9p stamped.py"
echo; echo "## B3 pycache-clean dry run (cwd $W/b3)"
rm -rf "$W/b3"; mkdir -p "$W/b3/tree/pkg/__pycache__" "$W/b3/tree/node_modules/__pycache__"; cd "$W/b3"
touch tree/pkg/__pycache__/m.cpython-312.pyc tree/pkg/stray.pyc tree/node_modules/__pycache__/x.pyc
printf 'roots:\n  - "%s"\nexclude:\n  - node_modules\ndry_run: true\n' "$W/b3/tree" > clean.yaml
run "cat clean.yaml"
run "$SD pycache-clean --config clean.yaml --dry-run --verbose 2>&1 | grep -v -e SyntaxWarning -e 'Windows long'"
run "find tree -type f | sort"
run "$SD pycache-clean --config clean.yaml 2>&1 | grep -v -e SyntaxWarning -e 'Windows long'"
run "find tree -type f | sort"
run "ls"
