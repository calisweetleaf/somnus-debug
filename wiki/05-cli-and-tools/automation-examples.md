# Automation examples

This page collects scripts that drive somnus-debug unattended. Each one was executed, and its real output and exit code are shown. Each example states where it ran. None of them writes into the scanned project except where noted.

## Example 1: CI gate on the raw doctor result

This section gives a shell gate that handles doctor's overloaded exit codes and keeps the checkout clean.

Executed: yes (`/tmp/w2/auto`, installed 0.1.0 venv on PATH; run W2-21).

```bash
#!/usr/bin/env bash
# CI gate: scan with an explicit config, never write state, fail on doctor errors.
set -u
ROOT="$1"; OUT="$2"; CFG="$3"
mkdir -p "$OUT"
cd "$OUT" || exit 3                      # production_doctor.log lands here, not in ROOT
somnus-debug doctor scan "$ROOT" -c "$CFG" --no-state -o "$OUT/doctor.md" --json-output "$OUT/doctor.json"
RC=$?
case $RC in
  0) echo "gate: pass" ;;
  1) echo "gate: serious findings" ;;
  2) if [ -f "$OUT/doctor.json" ]; then echo "gate: critical findings"; else echo "gate: usage error"; exit 3; fi ;;
  4) echo "gate: doctor configuration/input error"; exit 3 ;;
  5) echo "gate: doctor runtime failure (see $OUT/production_doctor.log)"; exit 3 ;;
  *) echo "gate: unexpected exit $RC (uncaught exception?)"; exit 3 ;;
esac
python3 -c 'import json,sys; s=json.load(open(sys.argv[1]))["summary"]; print("files=%(files_scanned)d critical=%(critical_issues)d serious=%(serious_issues)d score=%(production_score)d" % s)' "$OUT/doctor.json"
exit $RC
```

The config `cfg.yaml` was produced by `somnus-debug doctor init-config -o /tmp/w2/auto/cfg.yaml` (defaults). Results:

| Run | Project | Output (stdout) | Exit |
|---|---|---|---:|
| clean | `/tmp/w2/fp/calc` (2 files, no serious findings) | `Scan complete: files=2, issues=1, critical=0, serious=0` / `gate: pass` / `files=2 critical=0 serious=0 score=98` | 0 |
| findings | `/tmp/w2/qs/myproj` (silent `except ValueError: pass`) | `Scan complete: files=2, issues=2, critical=0, serious=1` / `gate: serious findings` / `files=2 critical=0 serious=1 score=90` | 1 |
| broken config | `-c /tmp/w2/auto/missing.yaml` | `gate: doctor configuration/input error` (doctor exited 4) | 3 |

After all three runs, `/tmp/w2/fp/calc` contained only `src/` and `tests/`. The `o3/` directory held only `production_doctor.log`, and no reports were written for the failed run.

Notes:

- Doctor's exit 2 does not say whether it came from findings or bad arguments, so the script checks for the JSON file. [SOURCE-CONFIRMED] [exit-codes](exit-codes.md#telling-codes-apart-as-a-caller).
- Add `[ "$(python3 -c ...files_scanned...)" -gt 0 ]` to fail zero-file scans. The example does not do this. See [D-17](../DISCOVERY-LEDGER.md#d-17).

## Example 2: regression gate (baseline vs latest) with delta.py

This section shows the recommended gate for code that already has findings.

Executed: yes (`/tmp/w2/fp`, W2-14 and W2-17). Commands:

```bash
cd /tmp/w2/fp/work
PYTHONPATH=/tmp/w2/fp/calc/src somnus-debug doctor scan /tmp/w2/fp/calc -c /tmp/w2/fp/calc/python_doctor.yaml
cp /tmp/w2/fp/calc/production_doctor_report.json baseline.json
# ...add a function using eval() inside `try/except Exception: return 0.0`...
sleep 1     # avoid a same-second run-ID collision (D-08)
PYTHONPATH=/tmp/w2/fp/calc/src somnus-debug doctor scan /tmp/w2/fp/calc -c /tmp/w2/fp/calc/python_doctor.yaml
python3 <fieldkit>/scripts/delta.py baseline.json /tmp/w2/fp/calc/production_doctor_report.json
```

Real `delta.py` output (exit 1):

```text
# doctor delta: 20261112T003752Z -> 20261112T003759Z

| Metric | Baseline | Latest | Change |
|---|---|---|---|
| files scanned | 3 | 3 | +0 |
| total | 4 | 8 | +4 |
| critical | 0 | 0 | +0 |
| serious | 0 | 3 | +3 |
| minor | 4 | 5 | +1 |
| production score | 92 | 66 | -26 |

**REGRESSION: new serious/critical findings.**

New (open): 4 · Resolved: 0 · Persisting: 4 · Dispositioned: 0

## New findings

| Severity | Category | Location | Symbol | Message |
|---|---|---|---|---|
| serious | `security_risks` | `src/calc/ops.py:21` | `evaluate` | High-risk call detected: eval. |
| serious | `broad_exceptions` | `src/calc/ops.py:22` | `evaluate` | Broad exception handler catches Exception. |
| serious | `silent_failures` | `src/calc/ops.py:22` | `evaluate` | Exception handler can suppress failure without actionable diagnostics. |
| minor | `suspicious_short_functions` | `src/calc/ops.py:18` | `evaluate` | Function evaluate is suspiciously short. |
```

After removing the function and rescanning, `delta.py ... --json` reported `{'exit': 0, 'persisting': 4, 'coverage_failure': False}` with 0 new and 0 resolved, and exited 0.

The packaged form of this loop, which works from a fieldkit profile, is lane F's `ci_delta_gate.sh`. Its gate treats doctor exit >= 4 as a hard failure, exit 3. [VERIFIED] lane F C1a-C1d ([compositions.md](../_evidence/agent-findings/lane-f-ext/compositions.md); [recipes/ci_delta_gate.sh](../_evidence/agent-findings/lane-f-ext/recipes/ci_delta_gate.sh)).

Known holes in this gate:

- A stale but broad disposition silently absorbs new findings (lane F L7).
- A latest scan run with a looser config can launder a regression, because `config_hash` is never compared (lane F D3).
- Argparse errors exit 2, the same code as "coverage regression".

See [D-21](../DISCOVERY-LEDGER.md#d-21).

## Example 3: quality ratchet

This section describes promoting the baseline only on a clean, fully reviewed delta.

Executed: yes, by lane F (C3a held at exit 1 on a regression; C3b advanced on a clean delta and archived the old baseline). Not re-run in this wave. Script: [recipes/ratchet_promote.sh](../_evidence/agent-findings/lane-f-ext/recipes/ratchet_promote.sh). It promotes only when `delta.py` exits 0 **and** `stale_dispositions` is empty. That rule also closes the stale-disposition hole from Example 2.

## Example 4: in-process call from Python

This section shows the subprocess-free form and its side effects.

Executed: yes (`/tmp/w2/inproc`, venv Python 3.12; W2-20).

```python
import io, json, logging, contextlib
from pathlib import Path
from somnus_debug import cli
from somnus_debug.doctor.core import ProjectScanner, ConfigManager

logging.basicConfig(level=logging.WARNING)           # host program's own logging
before = [type(h).__name__ for h in logging.getLogger().handlers]
buf = io.StringIO()
with contextlib.redirect_stdout(buf):
    rc = cli.main(["doctor", "scan", "/tmp/w2/qs/myproj", "--no-state", "-o", "/tmp/w2/inproc/r.md"])
after = [type(h).__name__ for h in logging.getLogger().handlers]
print("cli.main rc =", rc, "| stdout first line:", buf.getvalue().splitlines()[0])
print("root handlers before:", before, "after:", after)
print("log file exists in cwd:", Path("production_doctor.log").exists())

res = ProjectScanner(Path("/tmp/w2/qs/myproj"), ConfigManager(None)).scan({})
print("library scan:", res.summary.files_scanned, res.summary.serious_issues, res.run_id[:9])
```

Output:

```text
cli.main rc = 1 | stdout first line: Scan complete: files=2, issues=2, critical=0, serious=1
root handlers before: ['StreamHandler'] after: ['FileHandler']
log file exists in cwd: True
library scan: 2 1 20261112T
```

Use the `ProjectScanner` route inside long-lived processes. It writes nothing and leaves logging alone ([D-12](../DISCOVERY-LEDGER.md#d-12)). The `cli.main` route hijacks logging ([D-11](../DISCOVERY-LEDGER.md#d-11)).

## Example 5: wrap the project's tests in the single-test harness

This section shows the harness producing a PASS/FAIL artifact set that automation can archive.

Executed: yes (`/tmp/w2/hs/myproj`, W2-19). The splice script and steps are in [first-project](../03-getting-started/first-project.md#step-6-add-the-single-test-harness-optional). After scaffolding into `tools/` and replacing `execute_test`, `python tools/run_test.py` printed the summary JSON with `"verdict": "PASS"`, exited 0, and wrote `test-runs/<RUN_ID>/{manifest.json, report.md, test.log, pytest.txt}` under the project. A CI job can archive `test-runs/` and gate on the exit code.

## Example 6: safe bytecode cleanup in a job

This section shows the only safe way to run the cleaner unattended.

Executed: yes (`/tmp/w2/pc`, W2-18).

```bash
cat > config.yaml <<EOF
roots:
  - /tmp/w2/pc/tree
exclude:
  - node_modules
EOF
somnus-debug pycache-clean --dry-run    # exit 0; nothing removed
somnus-debug pycache-clean              # exit 0; pkg/__pycache__ and pkg/loose.pyc removed
```

Rules:

- Use absolute `roots` written as a YAML **list**.
- Write `exclude` entries as bare directory names, not `node_modules/*`.
- Never use `dry_run: no` in the file. It parses as false and runs live.
- Grep the output for `[ERROR] Root path does not exist`, because the exit code stays 0.
- Never point the cleaner at a tree you have not dry-run first.

See [D-14](../DISCOVERY-LEDGER.md#d-14).

## Sources

This section lists the code and evidence this page draws on.

- `src/somnus_debug/cli.py:107-125`; `src/somnus_debug/doctor/core.py:2046-2093`, `:2179-2201`
- `src/somnus_debug/pycache_cleaner/core.py:349-372`
- [lane F compositions.md](../_evidence/agent-findings/lane-f-ext/compositions.md), [fieldkit.md](../_evidence/agent-findings/lane-f-ext/fieldkit.md), [recipes/ci_delta_gate.sh](../_evidence/agent-findings/lane-f-ext/recipes/ci_delta_gate.sh), [recipes/ratchet_promote.sh](../_evidence/agent-findings/lane-f-ext/recipes/ratchet_promote.sh)
- W2 runs: [verification-results](../11-verification/verification-results.md#w2-runs)
