# Configuration recipes

This page gives twelve configuration recipes, each executed end to end, with the commands, the config text, and the observed output. They are written to avoid the pitfalls on [configuration-pitfalls.md](configuration-pitfalls.md).

## How these were run

This section states the environment every recipe ran in, so the outputs can be reproduced.

- All twelve ran in one script under `/tmp/w3r` (never in the repo), Python 3.12.15, PyYAML 6.0.2, baseline `034f46e`, with `PYTHONDONTWRITEBYTECODE=1 PYTHONWARNINGS=ignore`. Executed: yes, script exit 0.
- `somnus-debug` on `PATH` was a two-line wrapper: `PYTHONPATH=<repo>/src exec python3 -m somnus_debug.cli "$@"`. Because it uses `python -m`, the CWD is on `sys.path` (see [environment-variables.md](environment-variables.md)); every doctor command ran from `/tmp/w3r/scratch`.
- Fixture `/tmp/w3r/app`: `myapp/__init__.py`; `myapp/core.py` with an `os.system` call (serious `security_risks`), a `TODO` (minor), and a short function; `myapp/build/gen.py` (a real package directory named `build`, holding a stub); `.venv/lib/junk.py`; an empty `tests/`.
- Timestamps and run IDs in outputs are from the run; `<repo>` stands for the repository path. Outputs are trimmed to the lines that matter (mostly the `Markdown report:`/`JSON report:` lines and log timestamps); nothing is reworded.

## R1: make doctor use your config file

Doctor never auto-loads `python_doctor.yaml`; always pass `-c` [D-02](../DISCOVERY-LEDGER.md#d-02).

```console
$ somnus-debug doctor init-config -o /tmp/w3r/app/python_doctor.yaml
Wrote default configuration: /tmp/w3r/app/python_doctor.yaml
[exit=0]
$ sed -i 's/^severity_exit_level: .*/severity_exit_level: "critical"/' /tmp/w3r/app/python_doctor.yaml
$ somnus-debug doctor scan /tmp/w3r/app --no-state -o r1.md
Scan complete: files=2, issues=3, critical=0, serious=1
[exit=1]
$ somnus-debug doctor scan /tmp/w3r/app --no-state -o r1.md -c /tmp/w3r/app/python_doctor.yaml
Scan complete: files=2, issues=3, critical=0, serious=1
[exit=0]
```

Executed: yes (`/tmp/w3r/scratch`). The edited gate took effect only with `-c` [VERIFIED].

## R2: report-only mode

Quote the gate value; unquoted `none` is parsed as null [D-03](../DISCOVERY-LEDGER.md#d-03).

```yaml
# r2.yaml
severity_exit_level: "none"
```

```console
$ somnus-debug doctor scan /tmp/w3r/app --no-state -o r2.md -c r2-bad.yaml      # contains: severity_exit_level: none
Doctor failure: Configuration value must be a non-empty string.
Remediation: Fix the configuration file or regenerate it with init-config.
Context:
{
  "key": "severity_exit_level",
  "value": "None"
}
[exit=4]
$ somnus-debug doctor scan /tmp/w3r/app --no-state -o r2.md -c r2.yaml
Scan complete: files=2, issues=3, critical=0, serious=1
[exit=0]
```

Executed: yes [VERIFIED].

## R3: a CI gate that also fails a zero-file scan

A config that matches no files exits 0, so check the file count yourself [D-17](../DISCOVERY-LEDGER.md#d-17), [D-18](../DISCOVERY-LEDGER.md#d-18).

```bash
#!/usr/bin/env bash
# gate.sh PROJECT CONFIG REPORT
out=$(somnus-debug doctor scan "$1" --no-state -c "$2" -o "$3" 2>&1); code=$?
echo "$out" | head -1
files=$(echo "$out" | sed -n 's/^Scan complete: files=\([0-9]*\),.*/\1/p')
if [ "${files:-0}" -eq 0 ]; then echo "gate: zero files scanned or doctor failed (exit $code)"; exit 3; fi
exit $code
```

```console
$ ./gate.sh /tmp/w3r/app r3-empty.yaml r3.md       # include_patterns: [] and gate "none"
Scan complete: files=0, issues=0, critical=0, serious=0
gate: zero files scanned or doctor failed (exit 0)
[exit=3]
$ ./gate.sh /tmp/w3r/app r2.yaml r3.md
Scan complete: files=2, issues=3, critical=0, serious=1
[exit=0]
```

Executed: yes [VERIFIED]. By the same logic (not separately executed), a doctor error, which prints no "Scan complete" line, also ends in exit 3, keeping it apart from argparse's exit 2. The fieldkit's `onboard.py` applies the same zero-file rule in `report_scan` [SOURCE-CONFIRMED `skills/somnus-debug-fieldkit/scripts/onboard.py:435-448`].

## R4: keep every artifact out of the repository

Run from a scratch CWD (the log lands there), send reports to absolute paths, and either skip state or point `state_dir` outside the project [D-10](../DISCOVERY-LEDGER.md#d-10).

```yaml
# r4.yaml
severity_exit_level: "none"
state_dir: "/tmp/w3r/scratch/state"
```

```console
$ somnus-debug doctor scan /tmp/w3r/app -c r2.yaml -o /tmp/w3r/scratch/out/report.md --json-output /tmp/w3r/scratch/out/report.json --no-state
Scan complete: files=2, issues=3, critical=0, serious=1
[exit=0]
$ somnus-debug doctor scan /tmp/w3r/app -c r4.yaml -o /tmp/w3r/scratch/out/r4.md
Scan complete: files=2, issues=3, critical=0, serious=1
Markdown report: /tmp/w3r/scratch/out/r4.md
JSON report: /tmp/w3r/scratch/out/r4.json
State latest markdown: /tmp/w3r/scratch/state/reports/latest.md
Run ID: 20261112T004804Z
[exit=0]
$ somnus-debug doctor history /tmp/w3r/app -c r4.yaml --limit 1
Run history:
- 20261112T004804Z | Wed 2026-11-11 6:48 PM CST (UTC-06:00) | files=2 | issues=3 | critical=0 | serious=1
  markdown=/tmp/w3r/scratch/state/reports/20261112T004804Z/production_doctor_report.md
  json=/tmp/w3r/scratch/state/reports/20261112T004804Z/production_doctor_report.json
[exit=0]
repo after R4: .venv myapp python_doctor.yaml tests
```

Executed: yes [VERIFIED]. The project gained nothing (`python_doctor.yaml` is R1's deliberate file). `history` needs the same `-c` to find the state [VERIFIED W3 E9b/E9c]. The `completed_at` column shows a localized string in this sandbox (lane F caveat).

## R5: narrow coverage with globs that match

fnmatch `*` crosses `/`; `**` is not recursive, so `pkg/**/*.py` needs at least one subdirectory.

```yaml
# r5-wrong.yaml                 # r5.yaml
include_patterns:               include_patterns:
  - "myapp/**/*.py"               - "myapp/*.py"
```

```console
$ lsfiles r5-wrong.yaml: []
$ lsfiles r5.yaml:       ['myapp/__init__.py', 'myapp/core.py']
```

`lsfiles` is `ProjectFileIndex(root, ConfigManager(Path(cfg)).config).python_files`, the list doctor would scan. Executed: yes [VERIFIED]. `myapp/build/gen.py` is still excluded by the default `build/*` ignore (R6). MANUAL 3.1's suggested `src/**/*.py` has the same flaw.

## R6: stop the default ignores from hiding a real package directory

Default `build/*`, `env/*`, `dist/*`, ... prune directories with those names at any depth. Replace the list (lists are not merged) with only what you need [D-17](../DISCOVERY-LEDGER.md#d-17).

```yaml
# r6.yaml
ignore_patterns:
  - "__pycache__/*"
  - "*.pyc"
  - ".git/*"
  - ".venv/*"
  - ".python_doctor/*"
  - "dist/*"
```

```console
$ lsfiles defaults (r2.yaml): ['myapp/__init__.py', 'myapp/core.py']
$ lsfiles r6.yaml:            ['myapp/__init__.py', 'myapp/build/gen.py', 'myapp/core.py']
```

Executed: yes [VERIFIED]. Keep `.venv/*` and similar in your replacement list, or virtualenv code gets scanned (W3 E4b).

## R7: re-severity a category and switch a detector off

`severity_levels` merges per category; everything you do not name keeps its default.

```yaml
# r7.yaml
severity_levels:
  security_risks: "info"
detect_dependency_cycles: false
```

```console
$ somnus-debug doctor scan /tmp/w3r/app --no-state -o r7.md -c r7.yaml
Scan complete: files=2, issues=3, critical=0, serious=0
[exit=0]
```

Executed: yes [VERIFIED]. The `os.system` finding is still reported (as info) and no longer fails the default `serious` gate. A category cannot be turned off unless it has a `detect_*` key ([hidden-and-conditional-options.md](hidden-and-conditional-options.md)).

## R8: src layout without false missing_imports

Doctor names `src/calc` as module `src.calc`, so `import calc` only resolves through the interpreter. Put `src` on `PYTHONPATH` [D-22](../DISCOVERY-LEDGER.md#d-22).

```console
$ somnus-debug doctor scan /tmp/w3r/srcapp --no-state -o r8.md -c r2.yaml
Scan complete: files=2, issues=1, critical=0, serious=1
missing_imports: ['Import could not be resolved: calc.']
$ PYTHONPATH=/tmp/w3r/srcapp/src:<repo>/src python3 -m somnus_debug.cli doctor scan /tmp/w3r/srcapp --no-state -o r8b.md -c r2.yaml
Scan complete: files=2, issues=0, critical=0, serious=0
missing_imports: []
```

Executed: yes [VERIFIED]. The `missing_imports:` lines come from reading the JSON report. With an installed CLI, put the project's `src` on `PYTHONPATH` the same way, or install the project into the interpreter that runs doctor.

## R9: safe pycache-clean

Absolute roots, name-only excludes, and two configs, because no flag can turn a YAML `dry_run: true` off [D-14](../DISCOVERY-LEDGER.md#d-14).

```yaml
# pycache.dry.yaml (pycache.live.yaml is identical with dry_run: false)
roots:
  - "/tmp/w3r/tree"
exclude:
  - "node_modules"
  - ".git"
dry_run: true
```

```console
$ somnus-debug pycache-clean --config pycache.dry.yaml --verbose
[INFO] Starting pycache cleaner (dry_run=True)
[INFO] Scanning root: /tmp/w3r/tree
[DEBUG] Skipping excluded directory: /tmp/w3r/tree/node_modules
[DEBUG] Deleting directory: /tmp/w3r/tree/a/__pycache__ (0.00 MiB)
[INFO] Removed directory /tmp/w3r/tree/a/__pycache__
[DEBUG] Deleting file: /tmp/w3r/tree/a/x.pyc (0.00 KiB)
[INFO] Removed file /tmp/w3r/tree/a/x.pyc
[INFO] Summary: deleted 1 directories, 1 files; freed 0.00 MiB
[exit=0]
left after dry run: 3
$ somnus-debug pycache-clean --config pycache.live.yaml
[INFO] Starting pycache cleaner (dry_run=False)
[INFO] Scanning root: /tmp/w3r/tree
[INFO] Summary: deleted 1 directories, 1 files; freed 0.00 MiB
[exit=0]
left after live run: 1 (node_modules kept)
```

Executed: yes (timestamps trimmed) [VERIFIED]. The dry run says "Removed" and "deleted" although nothing was removed; only the `dry_run=True` line tells the modes apart. Write `true`/`false` unquoted; `"false"` keeps the run dry and `no` makes it live (W3 P7/P8).

## R10: keep run_test.py artifacts inside the repository

Scaffold into a subdirectory, or set an absolute `SINGLE_TEST_OUTPUT_DIR` / `PROJECT_ROOT` [D-15](../DISCOVERY-LEDGER.md#d-15).

```console
$ somnus-debug init-test-harness /tmp/w3r/hrepo/tools --no-contract
wrote /tmp/w3r/hrepo/tools/run_test.py
[exit=0]
$ (cd /tmp/w3r/scratch && python3 /tmp/w3r/hrepo/tools/run_test.py)
[run_test exit=1]
artifact root: /tmp/w3r/hrepo/test-runs/GOLDEN-PATH-LAYER-1-DATA-HIGHWAY-RESTORATION-20261112-004805-06357e
$ (cd /tmp/w3r/scratch && SINGLE_TEST_OUTPUT_DIR=/tmp/w3r/scratch/arts python3 /tmp/w3r/hrepo/tools/run_test.py)
[run_test exit=1]
artifact root: /tmp/w3r/scratch/arts/GOLDEN-PATH-LAYER-1-DATA-HIGHWAY-RESTORATION-20261112-004806-7c100e
```

Executed: yes [VERIFIED]. Exit 1 is expected: the template's `execute_test()` is a gp-cli cargo test until you replace it. Use absolute values for `SINGLE_TEST_OUTPUT_DIR`; a relative one resolves against CWD (W3 R5).

## R11: configure doctor in-process without a file

Replace the frozen config on the manager with `dataclasses.replace`; no file is needed.

```python
import dataclasses, pathlib
from somnus_debug.doctor.core import ConfigManager, ProjectScanner, Severity
cm = ConfigManager(None)
cm.config = dataclasses.replace(cm.config, include_patterns=("myapp/*.py",),
    severity_levels={**cm.config.severity_levels, "security_risks": Severity.INFO})
result = ProjectScanner(pathlib.Path("/tmp/w3r/app"), cm).scan({})
print(result.summary.files_scanned, result.summary.serious_issues, result.summary.info_issues)
```

Executed: yes; output `2 0 1` [VERIFIED]. No validation and no `config_hash` update happen on this path; see [runtime-configuration.md](runtime-configuration.md). [D-12](../DISCOVERY-LEDGER.md#d-12)

## R12: fieldkit onboarding plus a delta gate with a disposition

Onboard a repo with the fieldkit, introduce a regression, then accept it with a narrow disposition.

```console
$ python3 <repo>/skills/somnus-debug-fieldkit/scripts/onboard.py /tmp/w3r/app --apply --baseline
[exit=0]
Doctor config: .somnus-debug/python_doctor.yaml (generate on --apply)
Verify scan: files=2 issues=3 critical=0 serious=1 exit=1 (serious findings exceed gate)
Baseline: files=2 issues=3 serious=1 critical=0 exit=1 run_id=20261112T004806Z
- /tmp/w3r/app/.somnus-debug/python_doctor.yaml
- /tmp/w3r/app/.somnus-debug/pycache.yaml
- /tmp/w3r/app/.somnus-debug/dispositions.json
- /tmp/w3r/app/.somnus-debug/.gitignore
- /tmp/w3r/app/.somnus-debug/PROFILE.md
# (a stub function `later` is appended to myapp/core.py, then from .somnus-debug/:)
$ somnus-debug doctor scan .. -c python_doctor.yaml -o runs/latest.md --json-output runs/latest.json
$ python3 <repo>/skills/somnus-debug-fieldkit/scripts/delta.py runs/baseline.json runs/latest.json --json
[exit=1]
exit field 1 regressions [('stubs', 'later')]
# dispositions.json was then written with this content:
[{"category":"stubs","file":"myapp/core.py","symbol":"later","reason":"placeholder accepted until ticket closes"}]
$ python3 <repo>/skills/somnus-debug-fieldkit/scripts/delta.py runs/baseline.json runs/latest.json --dispositions dispositions.json
[exit=0]
**CLEAN: no new serious/critical findings, coverage intact.**
```

Executed: yes [VERIFIED]. R1's root `python_doctor.yaml` was removed first so onboard generated its own config. The verify scan's doctor exit 1 still allowed the baseline (only zero files or exit >= 4 block it). Keep dispositions narrow (exact `file` and `symbol`); a broad stale entry keeps muting new findings ([D-21](../DISCOVERY-LEDGER.md#d-21)).

## Sources

This section lists the evidence behind this page.

- Recipe script and log: W3 working files `work/w3/recipes.sh` and `work/w3/recipes.log` in the project workspace (outside the wiki; outputs quoted above in full where they matter)
- [`../_evidence/configuration-registry.tsv`](../_evidence/configuration-registry.tsv)
- [`../_evidence/agent-findings/lane-b-config/configuration-findings.md`](../_evidence/agent-findings/lane-b-config/configuration-findings.md), [`../_evidence/agent-findings/lane-f-ext/fieldkit.md`](../_evidence/agent-findings/lane-f-ext/fieldkit.md)
- `src/somnus_debug/doctor/core.py:726-851,937-992,1955-1962,2061-2093`, `src/somnus_debug/pycache_cleaner/core.py:157-365`, `src/somnus_debug/test_harness/templates/run_test.py:589-593,747-760`, `skills/somnus-debug-fieldkit/scripts/onboard.py`, `skills/somnus-debug-fieldkit/scripts/delta.py`
