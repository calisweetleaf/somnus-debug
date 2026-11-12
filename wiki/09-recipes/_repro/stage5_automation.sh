#!/usr/bin/env bash
# Stage 5 (automation): T1 CI delta gate (regression, broken config, clean), T2 opt-in pre-commit hook, T3 history + rollback.
# Needs stage 3 state in /tmp/w4/proj (export_report regression present).
source "$(dirname "$0")/env.sh"; set -u
exec > "$LOGS/stage5_automation.log" 2>&1
cd "$W"
PR="env PYTHONPATH=$W/proj/src $W/proj/.venv/bin/python -m somnus_debug.cli"
echo "## T1 CI gate"
rm -rf proj_ci && cp -r proj proj_ci
sed -i 's/^severity_exit_level: .*/severity_exit_level: "bogus"/' proj_ci/.somnus-debug/python_doctor.yaml
run "bash $REC/ci_delta_gate.sh $W/proj_ci $FK env PYTHONPATH=$W/proj_ci/src $W/proj/.venv/bin/python -m somnus_debug.cli"
python3 - <<'P'
from pathlib import Path
p = Path("/tmp/w4/proj/src/inventory/store.py"); t = p.read_text(); i = t.index("\n\ndef export_report"); p.write_text(t[:i] + "\n")
P
sleep 1
run "bash $REC/ci_delta_gate.sh $W/proj $FK $PR | tail -4"
echo; echo "## T2 opt-in pre-commit hook"
cd "$W/proj"
git add -A >/dev/null; git -c user.email=a@b -c user.name=x commit -qm "profile + fixes"
cp "$HERE/pre-commit.sh" .git/hooks/pre-commit && chmod +x .git/hooks/pre-commit
export FIELDKIT=$FK
cat >> src/inventory/store.py <<'P'


def run_tool(cmd: str) -> int:
    """Run an external tool by string; this is the regression."""
    import subprocess
    done = subprocess.run(cmd, shell=True, check=False)
    code = int(done.returncode)
    return code
P
git add -A
run "git -c user.email=a@b -c user.name=x commit -qm 'add run_tool'"
run "git log --oneline"
python3 - <<'P'
from pathlib import Path
p = Path("/tmp/w4/proj/src/inventory/store.py"); t = p.read_text(); i = t.index("\n\ndef run_tool"); p.write_text(t[:i] + "\n")
P
echo '"""Notes module."""' > src/inventory/notes.py
git add -A
run "git -c user.email=a@b -c user.name=x commit -qm 'add notes'"
run "git log --oneline; git status --short"
rm .git/hooks/pre-commit
echo; echo "## T3 history and rollback"
cd "$W/proj/.somnus-debug"
run "$PR doctor history .. -c python_doctor.yaml --limit 3"
FIRST=$(ls runs/archive/*.json | head -1 | sed 's/.*baseline-\(.*\)\.json/\1/')
run "python3 -c \"import json;print('latest alias before:', json.load(open('state/reports/latest.json'))['run_id'])\""
run "$PR doctor rollback .. -c python_doctor.yaml --run-id $FIRST"
run "python3 -c \"import json;print('latest alias after:', json.load(open('state/reports/latest.json'))['run_id'])\""
run "$PR doctor rollback .. -c python_doctor.yaml --run-id NOPE"
run "git -C .. status --short"
