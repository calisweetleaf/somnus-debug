#!/usr/bin/env bash
# Stage 3 (advanced): A1 ratchet, A2 findings -> source slices, A3 custom detector probe, A4 src-layout cycle check.
# Needs stage 2 state in /tmp/w4/proj.
source "$(dirname "$0")/env.sh"; set -u
exec > "$LOGS/stage3_advanced.log" 2>&1
cd "$W"
PR="env PYTHONPATH=$W/proj/src $W/proj/.venv/bin/python -m somnus_debug.cli"
echo "## A1 ratchet: clean delta -> promote"
run "bash $REC/ratchet_promote.sh $W/proj $FK"
run "ls proj/.somnus-debug/runs proj/.somnus-debug/runs/archive"
cat >> proj/src/inventory/store.py <<'P'


def export_report(path: str) -> int:
    """Export the stock report by shelling out to a helper."""
    import os
    status = os.system("report-tool " + path)
    code = int(status)
    return code
P
sleep 1
run "bash $REC/ci_delta_gate.sh $W/proj $FK $PR"
run "bash $REC/ratchet_promote.sh $W/proj $FK"
echo; echo "## A2 findings -> slices"
cd "$W/proj/.somnus-debug"
run "python3 $FK/scripts/delta.py runs/baseline.json runs/latest.json --dispositions dispositions.json --json > runs/delta.json"
run "python3 $REC/findings_to_slices.py runs/latest.json runs/delta.json"
run "python3 $REC/findings_to_slices.py runs/latest.json runs/delta.json --all"
echo '# touched after scan' >> ../src/inventory/store.py
run "python3 $REC/findings_to_slices.py runs/latest.json runs/delta.json"
python3 - <<'P'
from pathlib import Path
p = Path("../src/inventory/store.py"); t = p.read_text(); p.write_text(t.replace("# touched after scan\n", ""))
P
run "python3 $REC/structure_slice.py $W/proj/.venv/bin/python ../src/inventory/store.py parse_qty nope"
echo; echo "## A3 custom detector probe (private API monkeypatch)"
rm -rf "$W/a3"; mkdir -p "$W/a3/m" "$W/a3/out"; cd "$W/a3"
cat > m/m.py <<'P'
"""Module that prints instead of logging."""


def shout(message: str) -> None:
    """Print a message loudly to stdout for the operator."""
    text = message.upper()
    print(text)
    return None
P
cd out
run "$SD doctor init-config -o base.yaml"
sed 's/^  duplicate_definitions: "minor"/  duplicate_definitions: "minor"\n  print_calls: "critical"/' base.yaml > crit.yaml
run "grep -n print_calls crit.yaml"
run "$SD doctor scan ../m -c crit.yaml --no-state -o stock.md --json-output stock.json"
sleep 1
run "$W/venv/bin/python $REC/ext_custom_detector.py ../m crit.yaml patched"
run "python3 -c \"import json;r=json.load(open('patched.json'));print([(i['category'],i['severity'],i['symbol'],i['line_number']) for i in r['issues']], r['summary']['production_score'])\""
run "python3 $FK/scripts/delta.py stock.json patched.json"
echo; echo "## A4 src layout x dependency cycles"
rm -rf "$W/a4"; mkdir -p "$W/a4/repo/src/pkg" "$W/a4/out"; cd "$W/a4"
echo '"""Cycle fixture package."""' > repo/src/pkg/__init__.py
cat > repo/src/pkg/a.py <<'P'
"""Module a imports module b."""
import pkg.b


def use_b(value: int) -> int:
    """Delegate to b and add one to the result for the caller."""
    result = pkg.b.helper(value)
    result += 1
    result = int(result)
    return result
P
cat > repo/src/pkg/b.py <<'P'
"""Module b imports module a back."""
import pkg.a


def helper(value: int) -> int:
    """Double a value and keep a reference to module a for the cycle."""
    doubled = value * 2
    name = pkg.a.__name__
    doubled += len(name) * 0
    return doubled
P
cd out
SUM="python3 -c \"import json,sys;r=json.load(open(sys.argv[1]));s=r['summary'];g=r['dependency_graph'];print('cycles',s['dependency_cycles'],'missing',s['missing_imports'],[(e['imported_module'],e['classification'],e['target_file']) for e in g['edges'] if e['imported_module'].startswith('pkg')],g['cycles'])\""
run "env -u PYTHONPATH $SD doctor scan ../repo --no-state -o r1.md --json-output r1.json > /dev/null"
run "$SUM r1.json"
run "env PYTHONPATH=$W/a4/repo/src $SD doctor scan ../repo --no-state -o r2.md --json-output r2.json > /dev/null"
run "$SUM r2.json"
run "$SD doctor scan ../repo/src --no-state -o r3.md --json-output r3.json > /dev/null"
run "$SUM r3.json"
