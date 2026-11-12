"""Build the canonical configuration registry from lane-b's TSV plus W3 audit fixes."""
import csv
import sys
from pathlib import Path

WIKI = Path("/workspace/projects/69c23182-5d69-4d5c-ae10-5cdad587b9d3/forge/somnus-debug/wiki")
SRC = WIKI / "_evidence/agent-findings/lane-b-config/configuration-registry.tsv"
OUT = WIKI / "_evidence/configuration-registry.tsv"
COLS = ["name", "surface", "tool", "defined_at", "read_at", "default", "type", "valid_values", "precedence",
        "effect", "scope", "persistence", "dependencies", "failure_behavior", "doc_status", "verification", "example", "notes"]

D = "src/somnus_debug/doctor/core.py"
PC = "src/somnus_debug/pycache_cleaner/core.py"
SC = "src/somnus_debug/test_harness/scaffold.py"
RT = "src/somnus_debug/test_harness/templates/run_test.py"
OB = "skills/somnus-debug-fieldkit/scripts/onboard.py"
DL = "skills/somnus-debug-fieldkit/scripts/delta.py"
ST = "skills/somnus-debug-fieldkit/scripts/selftest.py"

rows = list(csv.DictReader(SRC.open(encoding="utf-8"), delimiter="\t"))
assert len(rows) == 94, len(rows)
for r in rows:
    r["notes"] = ""
    r["defined_at"] = r["defined_at"].replace("{D}", D)
    r["read_at"] = r["read_at"].replace("{D}", D)
    r["effect"] = r["effect"].replace("{D}", D)
    r["failure_behavior"] = r["failure_behavior"].replace("{D}", D)

TOOL_NORMALIZE = {
    "pycache-clean (and somnus-debug dispatcher)": "pycache-clean",
    "doctor (root)": "doctor",
    "run_test.py (template)": "run_test.py",
    "all": "packaging",
}

corrected = []


def fix(name, tool_prefix, note, **changes):
    hits = [r for r in rows if r["name"] == name and r["tool"].startswith(tool_prefix)]
    if len(hits) != 1:
        sys.exit(f"fix target not unique: {name} / {tool_prefix}: {len(hits)}")
    r = hits[0]
    for k, v in changes.items():
        r[k] = v
    r["notes"] = ("W3 corrected: " + note) if not r["notes"] else r["notes"] + "; " + note
    corrected.append(name + " [" + r["tool"] + "]")


# ---- corrections (each checked against source at baseline 034f46e) ----
fix("-o/--output (scan)", "doctor scan", "read_at line drift (1958 -> 1960; path resolved at 2081)",
    read_at=f"{D}:1960 (default), {D}:2081 (resolve against CWD)")
fix("--json-output", "doctor scan", "read_at line drift (1959 -> 1961)",
    read_at=f"{D}:1961, {D}:2081")
fix("report_basename", "doctor", "read_at narrowed to the lines that read it",
    read_at=f"{D}:1958-1960")
fix("ignore_functions", "doctor",
    "added default-value consequence: default list hides eval/exec inside any function named __repr__/__str__ (W3 F0); replacing the list re-exposes them (F2)",
    effect="matching function AND its entire body skipped (node.name in list, so any method or nested def with that bare name): security_risks/broad_exceptions/silent_failures inside are suppressed; with the DEFAULT list an eval() inside any __repr__/__str__ is never reported",
    example="default config: eval in module-level __repr__ not reported; ignore_functions: [outer] -> __repr__ eval reported, outer.inner eval gone (W3 F0/F2)")
fix("check_private_functions", "doctor", "added verified symbol attribution",
    effect="false: _private (non-dunder) funcs not recorded as functions (no docstring/hint/stub/short/complexity issues) but body still visited; issues inside are attributed to the enclosing symbol (e.g. <module>)",
    example="exec in _priv reported with symbol <module> by default; with true -> symbol _priv (W3 F0/F3)")
fix("--force", "init-test-harness", "read_at line drift (73 -> 75)", read_at=f"{SC}:75")
fix("--no-contract", "init-test-harness", "read_at line drift (71 -> 72)", read_at=f"{SC}:72")
fix("target", "init-test-harness", "read_at points to scaffold() where the path is used",
    read_at=f"{SC}:71,83,115")
fix("PROJECT_ROOT", "run_test.py", "default stated precisely; expanduser noted; tool normalized",
    default="Path(__file__).resolve().parent.parent (the parent of the directory holding run_test.py)",
    valid_values="any path; ~ expanded; relative resolved against CWD",
    example="scaffold into th/repo, no env -> /tmp/w3/th/test-runs (outside repo); PROJECT_ROOT=/tmp/w3/th/repo -> repo/test-runs; copy into repo2/tools/ -> repo2/test-runs (W3 R1/R2/R6)")
fix("SINGLE_TEST_OUTPUT_DIR", "run_test.py", "added: relative values resolve against CWD, not PROJECT_ROOT (W3 R5)",
    valid_values="any path; ~ expanded; RELATIVE value resolved against CWD (not project_root)",
    example="PROJECT_ROOT=/tmp/w3/th/repo SINGLE_TEST_OUTPUT_DIR=rel_arts from cwd /tmp/w3/th -> /tmp/w3/th/rel_arts (W3 R5)")
fix("--dry-run", "pycache-clean", "read_at line drift", read_at=f"{PC}:357-358")
fix("--verbose", "pycache-clean", "read_at line drift", read_at=f"{PC}:359-360")
fix("--max-depth", "pycache-clean", "read_at line drift; added verified CLI-over-YAML example",
    read_at=f"{PC}:361-362", example="YAML max_depth: 0 + --max-depth 5 -> deeper caches deleted (W3 P6)")
fix("--follow-symlinks", "pycache-clean", "read_at line drift", read_at=f"{PC}:363-364")
fix("YAML mini-parser", "doctor", "pointer refined: scalar rules at 619-643 (null 627-628, inline list 634-638, int 639-640, float 641-642)",
    read_at=f"{D}:813 (via ConfigManager._load_raw)", valid_values="see wiki/06-configuration/file-based-configuration.md (Y01-Y58)")
fix("include_patterns", "doctor", "added basename-match example",
    example="include [c.py] matches src/c.py by basename; src/**/*.py -> only src/a/b.py; src/*.py -> src/c.py and src/a/b.py (W3 G2/G3/G6)")
fix("dry_run", "pycache-clean", "added MANUAL wording check", doc_status="partial (MANUAL 5.1 says omit/false deletes; YAML 1.1 no/off also delete; quoted 'false' does not)")
fix("severity_exit_level", "doctor", "added doc discrepancy on 'minor' gate wording",
    doc_status="partial: none/info undocumented; MANUAL 3.4 and QUICKSTART say minor fails 'on anything at all' but info-only findings pass the minor gate (D:2054-2055)")
fix("-v/--verbose", "doctor scan", "noted literal-string check spans all subcommands",
    failure_behavior="`--verbose` anywhere in argv (even after another subcommand) switches the log level before parsing; `history --verbose` / `init-config --verbose` then fail argparse exit 2")

for r in rows:
    r["tool"] = TOOL_NORMALIZE.get(r["tool"], r["tool"])


def add(**kw):
    r = {c: "" for c in COLS}
    r.update(kw)
    r["notes"] = "W3 added" + ("; " + kw["notes"] if kw.get("notes") else "")
    rows.append(r)


fix("ConfigManager.default_yaml()", "doctor", "read_at line drift (2100 -> 2101)", read_at=f"{D}:2101")
fix("JSON config", "doctor", "defined_at narrowed", defined_at=f"{D}:802-811")

# ---- additions: doctor ----
add(name="DEFAULT_CONFIG_NAME", surface="in-code constant", tool="doctor", defined_at=f"{D}:81", read_at=f"{D}:2143",
    default="python_doctor.yaml", type="str", precedence="used only as the init-config -o default",
    effect="names the file init-config writes; never used to LOAD a config (no auto-discovery)", scope="process",
    doc_status="missing", verification="SOURCE-CONFIRMED", example="grep: only core.py:81 and :2143 reference it")
add(name="config_hash", surface="derived value", tool="doctor", defined_at=f"{D}:790", read_at=f"{D}:1975",
    default="sha of merged raw config", type="str",
    effect="hash of the MERGED raw mapping (unknown keys included) stored in JSON reports and the runs table; never compared by doctor or delta.py",
    scope="run", persistence="SQLite runs.config_hash, report JSON", doc_status="missing", verification="VERIFIED",
    example="max_workers: 1 changes config_hash but not findings (W3 M3); replacing ConfigManager.config at runtime does NOT change it (W3 RT2)")
add(name="deep_merge", surface="merge rule", tool="doctor", defined_at=f"{D}:726-734", read_at=f"{D}:799,811,813",
    effect="file mapping merged over DEFAULT_CONFIG_DATA: nested dicts (only severity_levels) merge key-by-key; lists and scalars replace wholesale",
    precedence="file > in-code default per key", scope="run", doc_status="missing", verification="VERIFIED",
    example="severity_levels {security_risks: info, stubs: info} keeps the other 18 defaults (W3 E4a); ignore_patterns [*.pyc] drops all 15 defaults so .venv is scanned (W3 E4b)")
add(name="require_* / detect_* bool validation", surface="validation rule", tool="doctor", defined_at=f"{D}:737-742", read_at=f"{D}:832-849",
    type="bool", valid_values="true|false (any case); yes/no/on/off are strings and rejected",
    failure_behavior="ConfigurationError exit 4", doc_status="missing", verification="VERIFIED",
    example="detect_security_risks: yes -> exit 4 (W3 E7d)")
add(name="ignore_patterns backslash normalization", surface="implicit", tool="doctor", defined_at=f"{D}:942",
    effect="each ignore pattern has \\ replaced by / before matching (include_patterns get no such normalization)", scope="run",
    doc_status="missing", verification="SOURCE-CONFIRMED")
add(name="Severity values", surface="enum", tool="doctor", defined_at=f"{D}:86-93", read_at=f"{D}:774-778",
    valid_values="critical|serious|minor|info (lowercase, exact)", effect="the only accepted severity_levels values",
    failure_behavior="other value -> exit 4", doc_status="partial", verification="SOURCE-CONFIRMED")
add(name="ProjectScanner/ConfigManager runtime override", surface="library", tool="doctor", defined_at=f"{D}:782-790,1695-1703",
    read_at=f"{D}:1702", type="DoctorConfig (frozen dataclass)",
    precedence="whatever ConfigManager.config holds when ProjectScanner is constructed",
    effect="programmatic configuration: ConfigManager(None or Path) then optionally cm.config = dataclasses.replace(cm.config, ...); DoctorConfig itself is frozen",
    scope="process", persistence="none (no disk/log writes from ProjectScanner.scan)",
    failure_behavior="direct attribute assignment on DoctorConfig -> FrozenInstanceError; replaced config bypasses validation and config_hash",
    doc_status="missing (MANUAL 8 shows CLI-level library use only)", verification="VERIFIED",
    example="include_patterns=('pkg/*.py',) via replace -> files 3->2; config_hash unchanged (W3 RT2/RT3)", notes="see D-12")
add(name="root duplicate python_production_doctor.py", surface="repo script", tool="doctor",
    defined_at="python_production_doctor.py:81,2130-2162", default="same options as src doctor",
    effect="same CLI and config keys as src doctor; lacks the SQLite-unavailable fallback (state errors exit 4 instead of warning)",
    scope="process", doc_status="existing (MANUAL 7.5)", verification="SOURCE-CONFIRMED",
    notes="per lane-b section 8 diff; see D-28")
add(name="PYTHONPATH / PYTHONSAFEPATH / python -P / CWD on sys.path", surface="env var (interpreter)", tool="doctor",
    read_at=f"{D}:1050-1055", default="interpreter defaults",
    precedence="interpreter-level; no doctor setting overrides it",
    effect="missing_imports classification uses importlib.util.find_spec in the RUNNING interpreter: python -m adds CWD; -P/PYTHONSAFEPATH=1 removes it; PYTHONPATH adds roots",
    scope="process", failure_behavior="same tree gives different missing_imports by invocation", doc_status="missing",
    verification="VERIFIED",
    example="ENV1 python -m from a cwd holding zzlocalonly.py: only calc missing; ENV2 -P and ENV3 PYTHONSAFEPATH=1: calc + zzlocalonly; ENV4 -P + PYTHONPATH+=src: only zzlocalonly (W3)",
    notes="see D-22, D-26")
add(name="PyYAML presence (doctor via dispatcher)", surface="dependency", tool="cli", defined_at="src/somnus_debug/cli.py:55-58",
    effect="somnus-debug imports every tool at import time, so missing PyYAML breaks all subcommands; somnus-doctor (doctor.core only) stays stdlib-only",
    failure_behavior="ImportError at import", doc_status="contradictory (README: doctor/structure stdlib-only)", verification="VERIFIED",
    example="sys.modules['yaml']=None: doctor.core imports, somnus_debug.cli raises ImportError (W3 NOYAML1/2)", notes="see D-13")

# ---- additions: pycache-clean ----
add(name="pycache relative path anchor", surface="implicit", tool="pycache-clean", defined_at=f"{PC}:184-186,351",
    effect="--config, roots and log_file are resolved against CWD; roots in a config are NOT relative to the config file",
    scope="run", doc_status="contradictory (module docstring: config.yaml 'in the same directory')", verification="VERIFIED",
    example="--config sub/c.yaml with roots [tree] from /tmp/w3/pc works; cd sub && --config c.yaml -> root /tmp/w3/pc/sub/tree missing, exit 0 (W3 P10/P11)")
add(name="no --no-dry-run / no --root", surface="absent flag", tool="pycache-clean", defined_at=f"{PC}:337-346",
    effect="CLI can only force dry_run/verbose/follow_symlinks True; a YAML dry_run: true cannot be overridden live; roots cannot be given on the CLI",
    failure_behavior="--no-dry-run -> argparse exit 2", doc_status="existing (MANUAL 5: no CLI root)", verification="VERIFIED",
    example="pycache-clean --config config.yaml --no-dry-run -> exit 2 (W3 P15)")
add(name="dry-run wording", surface="implicit", tool="pycache-clean", defined_at=f"{PC}:287-290,305-308",
    effect="in dry-run, verbose lines still say 'Removed ...' and the summary says 'deleted N'; only the start line shows dry_run=True",
    doc_status="missing", verification="VERIFIED", example="P3: 'Removed directory .../node_modules/__pycache__' printed in a dry run (W3)")

# ---- additions: structure / harness ----
add(name="source encoding", surface="implicit", tool="structure", defined_at="src/somnus_debug/structure/core.py:326",
    default="utf-8", effect="source read with encoding='utf-8' regardless of PEP 263 coding cookie", failure_behavior="UnicodeDecodeError uncaught -> traceback exit 1",
    doc_status="missing", verification="VERIFIED (lane-b)")
add(name="run_test.py argv", surface="absent CLI", tool="run_test.py", defined_at=f"{RT}:747-855",
    effect="main() reads no argv: any flag (including --help) just runs the test", doc_status="missing", verification="VERIFIED",
    example="python3 repo/run_test.py --help -> runs, verdict FAIL, exit 1 (W3 R7)", notes="see D-15")
add(name="run_test.py run_id / artifact dir", surface="derived value", tool="run_test.py", defined_at=f"{RT}:753-760",
    default="<SLUG(TEST_NAME)>-<YYYYmmdd-HHMMSS>-<6 hex>", effect="per-run directory created with exist_ok=False under the output root",
    persistence="test.log, manifest.json, report.md", doc_status="partial (CONTRACT.md)", verification="VERIFIED")

# ---- additions: fieldkit onboard.py ----
OBC = dict(tool="fieldkit onboard.py", scope="run")
add(name="repo", surface="CLI positional", defined_at=f"{OB}:454", read_at=f"{OB}:461-464", default=". (cwd)", type="path",
    valid_values="existing directory", effect="repository to survey/onboard", failure_behavior="not a directory -> stderr error, exit 1",
    doc_status="existing (references/onboarding.md)", verification="VERIFIED", example="onboard.py ../fx/nonexist -> exit 1 (W3 OB7)", **OBC)
add(name="--apply", surface="CLI flag", defined_at=f"{OB}:455", read_at=f"{OB}:495-501,515-516", default="False (plan mode)", type="flag",
    effect="writes .somnus-debug/{python_doctor.yaml (unless adopting a root config), pycache.yaml, dispositions.json, .gitignore, PROFILE.md}; never overwrites",
    persistence="repo files", failure_behavior="writes PROFILE.md even when verification failed (D-20)", doc_status="existing", verification="VERIFIED",
    example="--apply --baseline on fx/ob wrote 5 files + runs/ + state/ (W3 OB3)", **OBC)
add(name="--baseline", surface="CLI flag", defined_at=f"{OB}:456", read_at=f"{OB}:489-491,518-522", default="False", type="flag",
    effect="stateful scan with cwd .somnus-debug/ into runs/baseline.{md,json}; skipped silently unless verify status is 0 (verify exit 1 counts as status 0)",
    persistence=".somnus-debug/runs, .somnus-debug/state", failure_behavior="without --apply and no config -> 'use --apply first', exit 1",
    doc_status="existing", verification="VERIFIED", example="onboard.py repo --baseline (no config) -> exit 1 (W3 OB2); verify exit=1 still recorded baseline (W3 OB3)", **OBC)
add(name="--new-config", surface="CLI flag", defined_at=f"{OB}:457", read_at=f"{OB}:477-479", default="False", type="flag",
    precedence="default: adopt first ROOT python_doctor.yaml/.yml; flag forces .somnus-debug/python_doctor.yaml",
    effect="ignore an existing root doctor config and generate a profile config instead", doc_status="existing", verification="VERIFIED",
    example="root python_doctor.yaml present: plan adopts it (WARN 2 of 3 files); --new-config -> 'generate on --apply' (W3 OB4/OB5)", **OBC)
add(name="--python", surface="CLI flag", defined_at=f"{OB}:458", read_at=f"{OB}:239-245", default="None (project venv, then PATH)", type="path",
    precedence="--python > project venvs (.venv, venv, env, any pyvenv.cfg dir) > somnus-debug on PATH",
    effect="interpreter that runs python -m somnus_debug.cli", failure_behavior="path is resolve()d, so a symlinked venv python loses the venv -> BLOCKED exit 3; nonexistent path -> FileNotFoundError traceback exit 1",
    doc_status="contradictory (references/onboarding.md:59)", verification="VERIFIED", example="--python /nonexistent/python -> traceback exit 1 (W3 OB6)", notes="see D-20", **OBC)
add(name="PATH lookup of somnus-debug", surface="env var", defined_at=f"{OB}:256-258", read_at=f"{OB}:256", default="PATH",
    effect="fallback runner when no --python and no project venv has somnus_debug", failure_behavior="none found -> BLOCKED, exit 3",
    doc_status="existing", verification="VERIFIED", example="no somnus-debug on PATH -> 'BLOCKED: no usable somnus-debug', exit 3 (W3 OB8)", **OBC)
add(name="PYTHONPATH extension (src layout)", surface="env var (child process)", defined_at=f"{OB}:104-110,235-237",
    default="prepend <repo>/src when src/<pkg>/__init__.py exists", precedence="prepended to any inherited PYTHONPATH",
    effect="child doctor runs resolve the project's own src packages", doc_status="existing (references/onboarding.md)", verification="VERIFIED (lane-f)", **OBC)
add(name="PROFILE_DIR", surface="in-code constant", defined_at=f"{OB}:68", default=".somnus-debug", type="str",
    effect="profile directory; generated doctor config sets state_dir: .somnus-debug/state", doc_status="existing", verification="SOURCE-CONFIRMED", **OBC)
add(name="generated .somnus-debug/python_doctor.yaml", surface="generated file", defined_at=f"{OB}:276-297", read_at="doctor -c",
    default="init-config output with include [*.py], ignore BASE_IGNORES + venvs + egg-info + git-ignored py dirs, state_dir .somnus-debug/state",
    effect="profile doctor config; header comment documents fnmatch semantics", failure_behavior="default layout changed -> RuntimeError",
    doc_status="existing", verification="VERIFIED (lane-f logs/s1_profile_python_doctor.yaml.txt)", **OBC)
add(name="generated .somnus-debug/pycache.yaml", surface="generated file", defined_at=f"{OB}:300-321", read_at="pycache-clean --config",
    default="roots [absolute repo], name-only excludes, dry_run: true", effect="safe cleaner config; live run requires editing dry_run",
    doc_status="existing", verification="VERIFIED (lane-f logs/s1_profile_pycache.yaml.txt)", **OBC)
add(name="ALWAYS_PRUNE / BASE_IGNORES / PYCACHE_EXCLUDES / VENV_NAMES", surface="in-code constants", defined_at=f"{OB}:71-82",
    effect="survey pruning and the ignore/exclude lists written into generated configs", doc_status="partial", verification="SOURCE-CONFIRMED", **OBC)
add(name="subprocess timeouts", surface="in-code constants", defined_at=f"{OB}:149-151 (+ 60 s at call sites)", default="600 s (scans); 60 s (version, init-config, git, import probe)",
    effect="TimeoutExpired propagates as a traceback", doc_status="missing", verification="SOURCE-CONFIRMED", **OBC)
add(name="onboard exit codes", surface="exit status", defined_at=f"{OB}:50,464,472,436-448", default="0 ok",
    valid_values="0 ok, 1 usage, 2 coverage failure, 3 somnus-debug unavailable", failure_behavior="doctor config error -> RuntimeError traceback exit 1, not 2 (D-20)",
    doc_status="partial", verification="VERIFIED", **OBC)

# ---- additions: fieldkit delta.py ----
DLC = dict(tool="fieldkit delta.py", scope="run")
add(name="baseline", surface="CLI positional", defined_at=f"{DL}:238", read_at=f"{DL}:245", type="path", valid_values="doctor JSON report",
    failure_behavior="unreadable / missing issues, summary, files -> exit 3", doc_status="existing", verification="VERIFIED", example="{} -> exit 3 (W3 DL7)", **DLC)
add(name="latest", surface="CLI positional", defined_at=f"{DL}:239", read_at=f"{DL}:245", type="path", valid_values="doctor JSON report",
    failure_behavior="missing argument -> argparse exit 2 (collides with coverage-regression code)", doc_status="partial", verification="VERIFIED",
    example="delta.py base.json -> exit 2 (W3 DL5)", notes="see D-21", **DLC)
add(name="--dispositions", surface="CLI flag", defined_at=f"{DL}:240", read_at=f"{DL}:246-248", default="None", type="path",
    valid_values="JSON list of {category, file (glob), symbol (glob, optional, default *), reason}",
    effect="matching findings never count as regressions; unmatched entries reported stale", failure_behavior="missing file -> stderr note, continue without; malformed -> exit 3",
    doc_status="existing", verification="VERIFIED", example="disposition for new stub2 -> exit 1 becomes 0; missing.json -> note, exit 1 (W3 DL2/DL3)", notes="stale broad dispositions still mute (D-21)", **DLC)
add(name="--root", surface="CLI flag", defined_at=f"{DL}:241", read_at=f"{DL}:252", default="latest report's project_root", type="path",
    effect="where coverage checks look for files dropped from the latest scan", doc_status="existing", verification="VERIFIED",
    example="--root at an empty dir: dropped files count as deleted, verdict unchanged (W3 DL6)", **DLC)
add(name="--json", surface="CLI flag", defined_at=f"{DL}:242", read_at=f"{DL}:254", default="False (Markdown)", type="flag",
    effect="emit JSON result instead of Markdown", doc_status="existing", verification="VERIFIED", example="W3 DL4 exit 1 with JSON body", **DLC)
add(name="GATING / SEVERITY_ORDER", surface="in-code constants", defined_at=f"{DL}:67-68", default="{critical, serious}",
    effect="only new undispositioned critical/serious findings are regressions; severities come from the reports, config_hash never compared",
    doc_status="partial", verification="VERIFIED (lane-f D3)", notes="see D-21", **DLC)

# ---- additions: fieldkit selftest.py ----
add(name="--python", surface="CLI flag", tool="fieldkit selftest.py", defined_at=f"{ST}:322", read_at=f"{ST}:324-330", default="somnus-debug on PATH",
    type="path", effect="interpreter used as python -m somnus_debug.cli for the 29 checks (expanduser only, no resolve)",
    failure_behavior="neither --python nor PATH -> exit 3", scope="run", doc_status="existing", verification="VERIFIED (lane-f 29/29)")

# ---- packaging ----
add(name="[tool.hatch.build] exclude", surface="packaging config", tool="packaging", defined_at="pyproject.toml:[tool.hatch.build]",
    default=".python_doctor/, *_report.md/json, production_doctor.log, __pycache__, *.pyc",
    effect="keeps doctor state/report/log artifacts out of built wheels/sdists", scope="build", doc_status="missing", verification="SOURCE-CONFIRMED")

with OUT.open("w", encoding="utf-8", newline="") as fh:
    w = csv.DictWriter(fh, fieldnames=COLS, delimiter="\t", lineterminator="\n")
    w.writeheader()
    for r in rows:
        w.writerow({c: (r.get(c) or "").replace("\t", " ").replace("\n", " ") for c in COLS})
print("rows", len(rows), "corrected", len(corrected), "added", len(rows) - 94)
print("\n".join(corrected))
