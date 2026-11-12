"""Generate complete-option-reference.md and 13-reference/configuration-index.md from the registry."""
import csv
import re
from collections import OrderedDict
from pathlib import Path

WIKI = Path("/workspace/projects/69c23182-5d69-4d5c-ae10-5cdad587b9d3/forge/somnus-debug/wiki")
REG = WIKI / "_evidence/configuration-registry.tsv"
rows = list(csv.DictReader(REG.open(encoding="utf-8"), delimiter="\t"))

GROUPS = OrderedDict([
    ("cli", ("somnus-debug dispatcher (cli)", lambda t: t == "cli")),
    ("doctor-cli", ("doctor: CLI arguments and subcommands", lambda t: t.startswith("doctor ") or t == "doctor" and False)),
    ("doctor-keys", ("doctor: configuration file keys", None)),
    ("doctor-impl", ("doctor: files, parser, merge, constants, and implicit inputs", None)),
    ("pycache-clean", ("pycache-clean", lambda t: t == "pycache-clean")),
    ("structure", ("structure", lambda t: t == "structure")),
    ("init-test-harness", ("init-test-harness", lambda t: t == "init-test-harness")),
    ("run_test.py", ("run_test.py (scaffolded template)", lambda t: t == "run_test.py")),
    ("fieldkit onboard.py", ("fieldkit onboard.py", lambda t: t == "fieldkit onboard.py")),
    ("fieldkit delta.py", ("fieldkit delta.py", lambda t: t == "fieldkit delta.py")),
    ("fieldkit selftest.py", ("fieldkit selftest.py", lambda t: t == "fieldkit selftest.py")),
    ("packaging", ("packaging", lambda t: t == "packaging")),
])


def group_of(r):
    t = r["tool"]
    if t.startswith("doctor "):
        return "doctor-cli"
    if t == "doctor":
        if r["surface"].startswith("config key"):
            return "doctor-keys"
        if r["surface"] in ("CLI flag", "argv rewrite", "subcommand") or r["name"] in ("exit codes",):
            return "doctor-cli"
        return "doctor-impl"
    for key, (_, pred) in GROUPS.items():
        if pred and pred(t):
            return key
    raise SystemExit("ungrouped: " + t)


def esc(s):
    return (s or "").replace("|", "\\|").strip() or "-"


def evclass(v):
    m = re.match(r"(VERIFIED|SOURCE-CONFIRMED|DOCUMENTED-ONLY|CONDITIONAL|DISCREPANCY|UNVERIFIED|HYPOTHESIS)", v or "")
    return m.group(1) if m else (v or "UNVERIFIED")


def anchor(name, tool):
    base = f"{tool} {name}".lower()
    base = re.sub(r"[^a-z0-9 _-]", "", base).strip().replace(" ", "-")
    return base


by_group = OrderedDict((k, []) for k in GROUPS)
for r in rows:
    by_group[group_of(r)].append(r)
assert sum(len(v) for v in by_group.values()) == len(rows)

out = []
out.append("# Complete option reference")
out.append("")
out.append("Every row of the canonical configuration registry, grouped by tool, with its default, valid values, effect, failure behavior, documentation status, and evidence class. The registry is the source of truth; this page is generated from it so the two cannot drift.")
out.append("")
out.append(f"- Registry: [`_evidence/configuration-registry.tsv`](../_evidence/configuration-registry.tsv), {len(rows)} rows, 18 columns (17 lane columns plus `notes`).")
out.append("- Baseline: commit `034f46e`, somnus-debug 0.1.0, Python 3.12.15, PyYAML 6.0.2. Paths are repo-relative.")
out.append("- Evidence class per row is the registry `verification` value. `VERIFIED` rows were executed by lane B, lane F, or W3 (this wave) in `/tmp`; the `example` text names the probe. `SOURCE-CONFIRMED` rows were read from source only.")
out.append("- Each entry is anchored as `tool-name` so other pages can link here. For how layers combine, read [precedence.md](precedence.md); for winning defaults, [defaults.md](defaults.md).")
out.append("")
out.append("## Contents")
out.append("")
out.append("This section lists the tool groups and their row counts.")
out.append("")
for key, (title, _) in GROUPS.items():
    if by_group[key]:
        a = re.sub(r"[^a-z0-9 -]", "", title.lower()).strip().replace(" ", "-")
        out.append(f"- [{title}](#{a}) ({len(by_group[key])})")
out.append("")
for key, (title, _) in GROUPS.items():
    items = by_group[key]
    if not items:
        continue
    out.append(f"## {title}")
    out.append("")
    out.append(f"This section documents the {len(items)} registry rows for {title}.")
    out.append("")
    for r in items:
        a = anchor(r["name"], r["tool"])
        out.append(f'<a id="{a}"></a>')
        out.append(f"### `{r['name']}`")
        out.append("")
        out.append(f"[{evclass(r['verification'])}] {esc(r['surface'])}; tool `{r['tool']}`. Defined at `{esc(r['defined_at'])}`" + (f"; read at `{esc(r['read_at'])}`." if r['read_at'] else "."))
        out.append("")
        out.append("| Field | Value |")
        out.append("|---|---|")
        for label, col in (("Default", "default"), ("Type", "type"), ("Valid values", "valid_values"), ("Precedence", "precedence"),
                           ("Effect", "effect"), ("Scope", "scope"), ("Persistence", "persistence"), ("Dependencies", "dependencies"),
                           ("Failure behavior", "failure_behavior"), ("Doc status", "doc_status"), ("Verification", "verification"),
                           ("Example / probe", "example"), ("Notes", "notes")):
            if r[col].strip():
                out.append(f"| {label} | {esc(r[col])} |")
        out.append("")
out.append("## Sources")
out.append("")
out.append("This section lists where the rows above come from.")
out.append("")
out.append("- [`../_evidence/configuration-registry.tsv`](../_evidence/configuration-registry.tsv) (canonical; W3 audit of lane B's 94 rows plus 37 additions)")
out.append("- [`../_evidence/agent-findings/lane-b-config/configuration-findings.md`](../_evidence/agent-findings/lane-b-config/configuration-findings.md) and [`configuration-registry.tsv`](../_evidence/agent-findings/lane-b-config/configuration-registry.tsv) (original 94 rows)")
out.append("- [`../_evidence/agent-findings/lane-f-ext/fieldkit.md`](../_evidence/agent-findings/lane-f-ext/fieldkit.md) and [`harness.md`](../_evidence/agent-findings/lane-f-ext/harness.md) (fieldkit and harness behavior)")
out.append("- Source files: `src/somnus_debug/cli.py`, `src/somnus_debug/doctor/core.py`, `src/somnus_debug/pycache_cleaner/core.py`, `src/somnus_debug/structure/core.py`, `src/somnus_debug/test_harness/scaffold.py`, `src/somnus_debug/test_harness/templates/run_test.py`, `skills/somnus-debug-fieldkit/scripts/{onboard,delta,selftest}.py`, `pyproject.toml`")
(WIKI / "06-configuration").mkdir(parents=True, exist_ok=True)
(WIKI / "06-configuration/complete-option-reference.md").write_text("\n".join(out) + "\n", encoding="utf-8")

# ---- configuration index ----
idx = ["# Configuration index", "",
       "Alphabetical index of every configuration surface in the registry: flags, keys, environment variables, files, constants, and implicit inputs, each linked to its full entry.", "",
       f"Generated from [`../_evidence/configuration-registry.tsv`](../_evidence/configuration-registry.tsv) ({len(rows)} rows). Concept pages: [configuration atlas](../06-configuration/configuration-atlas.md), [precedence](../06-configuration/precedence.md), [defaults](../06-configuration/defaults.md), [environment variables](../06-configuration/environment-variables.md).", "",
       "## Index", "", "This section is the A-Z table; the evidence column is the row's verification class.", "",
       "| Name | Tool | Surface | Default | Evidence | Entry |", "|---|---|---|---|---|---|"]
for r in sorted(rows, key=lambda r: (re.sub(r"^[^a-zA-Z0-9]+", "", r["name"]).lower(), r["tool"])):
    a = anchor(r["name"], r["tool"])
    d = esc(r["default"])
    if len(d) > 60:
        d = d[:57] + "..."
    idx.append(f"| `{esc(r['name'])}` | {r['tool']} | {esc(r['surface'])} | {d} | {evclass(r['verification'])} | [entry](../06-configuration/complete-option-reference.md#{a}) |")
idx += ["", "## By surface", "", "This section counts registry rows per surface kind.", "", "| Surface | Rows |", "|---|---|"]
from collections import Counter
for s, n in sorted(Counter(r["surface"] for r in rows).items(), key=lambda x: (-x[1], x[0])):
    idx.append(f"| {esc(s)} | {n} |")
idx += ["", "## Sources", "", "This section lists the inputs for this index.", "",
        "- [`../_evidence/configuration-registry.tsv`](../_evidence/configuration-registry.tsv)",
        "- [`../06-configuration/complete-option-reference.md`](../06-configuration/complete-option-reference.md)"]
(WIKI / "13-reference").mkdir(parents=True, exist_ok=True)
(WIKI / "13-reference/configuration-index.md").write_text("\n".join(idx) + "\n", encoding="utf-8")
print({k: len(v) for k, v in by_group.items()})
