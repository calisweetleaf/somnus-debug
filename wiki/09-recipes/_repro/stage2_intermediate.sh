#!/usr/bin/env bash
# Stage 2 (intermediate): I1 onboard, I2 baseline/change/delta/disposition loop, I3 severity + gate tuning.
source "$(dirname "$0")/env.sh"; set -u
exec > "$LOGS/stage2_intermediate.log" 2>&1
cd "$W"
echo "## I1 onboard (plan, then apply + baseline)"
run "python3 $FK/scripts/onboard.py proj"
run "git -C proj status --short"
run "python3 $FK/scripts/onboard.py proj --apply --baseline"
run "git -C proj status --short; (cd proj && find .somnus-debug -type f | sort)"
run "python3 $FK/scripts/onboard.py proj --apply"
echo; echo "## I2 loop"
cat >> proj/src/inventory/store.py <<'P'


def reserve(levels: dict[str, int], sku: str) -> None:
    """Reserve one unit of a SKU (not written yet)."""
    pass


def safe_level(levels: dict[str, int], sku: str) -> int:
    """Return a level, swallowing any lookup problem."""
    try:
        level = levels[sku]
    except KeyError:
        level = 0
    return level
P
cd proj/.somnus-debug
PR="env PYTHONPATH=../src $W/proj/.venv/bin/python -m somnus_debug.cli"
run "$PR doctor scan .. -c python_doctor.yaml -o runs/latest.md --json-output runs/latest.json"
run "python3 $FK/scripts/delta.py runs/baseline.json runs/latest.json --dispositions dispositions.json"
cat > dispositions.json <<'J'
[
  {"category": "silent_failures", "file": "src/inventory/store.py", "symbol": "safe_level",
   "reason": "Missing SKU means zero stock by design; KeyError is the expected path, not a failure."}
]
J
python3 - <<'P'
from pathlib import Path
p = Path("../src/inventory/store.py"); t = p.read_text()
t = t.replace('''    """Reserve one unit of a SKU (not written yet)."""
    pass
''', '''    """Reserve one unit of a SKU, never going below zero."""
    current = levels.get(sku, 0)
    if current <= 0:
        raise ValueError(f"no stock for {sku}")
    levels[sku] = current - 1
''')
p.write_text(t)
P
run "cat dispositions.json"
run "$PR doctor scan .. -c python_doctor.yaml -o runs/latest.md --json-output runs/latest.json"
run "python3 $FK/scripts/delta.py runs/baseline.json runs/latest.json --dispositions dispositions.json"
run "python3 $FK/scripts/delta.py runs/baseline.json runs/latest.json --dispositions dispositions.json --json"
echo; echo "## I3 severity remap and gate (cwd $W/b1/out)"
cd "$W/b1/out"
sed -e 's/^  stubs: "serious"/  stubs: "minor"/' -e 's/^severity_exit_level: "serious"/severity_exit_level: "critical"/' cfg.yaml > tuned.yaml
run "diff cfg.yaml tuned.yaml"
run "$SD doctor scan ../proj_nobroken -c cfg.yaml --no-state -o d.md --json-output d.json"
run "$SD doctor scan ../proj_nobroken -c tuned.yaml --no-state -o t.md --json-output t.json"
run "$SD doctor scan ../proj -c tuned.yaml --no-state -o t2.md --json-output t2.json"
sed -e 's/^severity_exit_level: "serious"/severity_exit_level: none/' cfg.yaml > none_unquoted.yaml
sed -e 's/^severity_exit_level: "serious"/severity_exit_level: "none"/' cfg.yaml > none_quoted.yaml
sed -e 's/^severity_exit_level: "serious"/severity_exit_levle: "critical"/' cfg.yaml > typo.yaml
run "$SD doctor scan ../proj_nobroken -c none_unquoted.yaml --no-state -o n.md --json-output n.json"
run "$SD doctor scan ../proj_nobroken -c none_quoted.yaml --no-state -o n.md --json-output n.json"
run "$SD doctor scan ../proj_nobroken -c typo.yaml --no-state -o n.md --json-output n.json"
