#!/usr/bin/env bash
# Stage 5: extension-point probes (custom detector via monkeypatch, severity/gate config), library imports, doc link check.
source "$(dirname "$0")/env.sh"; set -u; cd $W
R=$LANE/recipes; PY=$W/venv/bin/python
L=$LOGS/s5_ext.log; : > $L
rm -rf e1 && mkdir -p e1/proj e1/run
cat > e1/proj/m.py <<'P'
"""Module with a print call for the extension probe."""


def shout(value: str) -> str:
    """Print and return the value in upper case."""
    loud = value.upper()
    print(loud)
    checked = str(loud)
    return checked
P
cd e1/run
$PY -m somnus_debug.cli doctor init-config -o base.yaml >/dev/null
cp base.yaml crit.yaml && sed -i 's/^severity_levels:/severity_levels:\n  print_calls: "critical"/' crit.yaml
log "### X1 stock doctor"; $PY -m somnus_debug.cli doctor scan ../proj --no-state -o stock.md --json-output stock.json >>$L 2>&1; log "exit=$?"
log "### X2 monkeypatched visitor, default config (print_calls unmapped -> minor)"; $PY $R/ext_custom_detector.py ../proj base.yaml p_minor >>$L 2>&1; log "exit=$?"
log "### X3 monkeypatched visitor, config maps print_calls: critical"; $PY $R/ext_custom_detector.py ../proj crit.yaml p_crit >>$L 2>&1; log "exit=$?"
for f in stock p_minor p_crit; do python3 -c "import json;d=json.load(open('$f.json'));print('$f',[(i['category'],i['severity']) for i in d['issues']],'score',d['summary']['production_score'])" >>$L; done
log "custom category appears in markdown report: $(grep -c print_calls p_crit.md) lines"
log "### X4 stock doctor + crit.yaml (category mapped, no detector -> nothing)"; $PY -m somnus_debug.cli doctor scan ../proj -c crit.yaml --no-state -o s2.md --json-output s2.json >>$L 2>&1; log "exit=$?"
log "### X5 delta.py handles the custom category generically"; python3 $FK/scripts/delta.py stock.json p_crit.json 2>&1 | grep -E '\*\*|print_calls' >>$L; log "delta exit=${PIPESTATUS[0]}"
printf '"""Mod docstring long enough here."""\n\n\ndef f(x: int) -> int:\n    """Stub function for probe."""\n    pass\n' > ../proj/s.py
cp base.yaml typo.yaml && printf 'severity_exit_levle: "none"\nmax_complexity: 3\n' >> typo.yaml && sed -i 's/  stubs: "serious"/  stubz: "info"/' typo.yaml
log "### X6 config with unknown keys (severity_exit_levle, max_complexity) and misspelled category (stubz)"; $PY -m somnus_debug.cli doctor scan ../proj -c typo.yaml --no-state -o t.md --json-output t.json >>$L 2>&1; log "exit=$? stubs severity: $(python3 -c "import json;print([(i['category'],i['severity']) for i in json.load(open('t.json'))['issues'] if i['category']=='stubs'])")"
cp base.yaml remap.yaml && sed -i 's/  stubs: "serious"/  stubs: "info"/' remap.yaml
log "### X7 remap stubs -> info"; $PY -m somnus_debug.cli doctor scan ../proj -c remap.yaml --no-state -o r.md --json-output r.json >/dev/null 2>&1; log "exit=$? $(python3 -c "import json;d=json.load(open('r.json'));print([(i['category'],i['severity']) for i in d['issues'] if i['category']=='stubs'],'info_issues=',d['summary']['info_issues'],'score=',d['summary']['production_score'])")"
for g in critical serious minor info none; do cp base.yaml g_$g.yaml && sed -i "s/severity_exit_level: \"serious\"/severity_exit_level: \"$g\"/" g_$g.yaml; $PY -m somnus_debug.cli doctor scan ../proj -c g_$g.yaml --no-state -o g.md --json-output g.json >/dev/null 2>&1; log "X8 gate=$g exit=$? (issues: serious stub + minors)"; done
cd $W; rm -rf dc && mkdir dc && cat > dc/m.py <<'P'
"""Module docstring long enough here."""
from dataclasses import dataclass


@dataclass
class Plain:
    """Plain dataclass value type."""

    a: int


@dataclass(frozen=True)
class Frozen:
    """Frozen dataclass value type."""

    a: int
P
(cd dc && $PY -m somnus_debug.cli doctor scan . --no-state -o r.md --json-output r.json >/dev/null 2>&1); log "### X9 dataclass exemption probe: $(python3 -c "import json;print([(i['category'],i['symbol']) for i in json.load(open('dc/r.json'))['issues']])")"
# ---------- library surface ----------
L=$LOGS/s5_library_and_links.log; : > $L
$PY - >>$L 2>&1 <<'P'
import importlib
for mod, names in [("somnus_debug.structure.core", ["build_index"]), ("somnus_debug.doctor.core", ["ProjectScanner", "ConfigManager", "CodeQualityVisitor", "FileAnalyzer"]), ("somnus_debug.pycache_cleaner.core", ["PycacheCleaner", "CleanerConfig"]), ("somnus_debug.test_harness.scaffold", ["scaffold"])]:
    m = importlib.import_module(mod)
    for n in names:
        print(f"{mod}.{n}: {'present' if hasattr(m, n) else 'ABSENT'}")
import somnus_debug.pycache_cleaner.core as p
print("pycache_cleaner.core public classes:", [n for n in dir(p) if n[:1].isupper() and isinstance(getattr(p, n), type)])
from importlib.metadata import entry_points
eps = entry_points()
print("console_scripts from this dist:", sorted(e.name for e in eps.select(group="console_scripts") if e.value.startswith("somnus_debug")))
print("any non-console entry-point group referencing somnus_debug:", sorted({e.group for e in eps if e.value.startswith("somnus_debug") and e.group != "console_scripts"}))
P
log "--- grep for plugin/registry/hook mechanisms in src/somnus_debug:"
grep -rnE "entry_points|iter_entry_points|pkg_resources|importlib\.metadata|register|plugin|hook|callback|__subclasses__|import_module\(" $REPO/src/somnus_debug --include=*.py >>$L || log "(no matches in .py)"
log "--- relative link check (README, docs, fieldkit):"
cd $REPO
for f in README.md docs/*.md skills/somnus-debug-fieldkit/*.md skills/somnus-debug-fieldkit/references/*.md; do
  grep -noE '\]\([^)#]+' "$f" | while IFS=: read -r line rest; do t=${rest#](}; case "$t" in http*|mailto*) continue;; esac; [ -e "$(dirname "$f")/$t" ] && echo "ok   $f:$line -> $t" || echo "DEAD $f:$line -> $t"; done
done >>$L
