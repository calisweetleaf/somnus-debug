# First project: a full doctor loop on a src-layout package

This page walks one realistic project through the full cycle:

1. generate and apply a config
2. handle a src layout
3. record a baseline
4. introduce a regression and catch it with history and `delta.py`
5. roll back the latest alias
6. fix the regression
7. add the single-test harness

Everything below was executed in this wave under `/tmp/w2/fp` with the installed 0.1.0 venv on PATH (Python 3.12.15). Doctor was always run from a separate scratch directory (`/tmp/w2/fp/work`), so the log never lands in the project.

## Step 1: lay out the project

This section creates a src-layout package with one test module.

Executed: yes.

```text
/tmp/w2/fp/calc/
  src/calc/__init__.py      """calc: a tiny arithmetic package."""
  src/calc/ops.py           add() and safe_div(), both validated and documented
  tests/test_ops.py         from calc.ops import add, safe_div; two tests
```

`src/calc/ops.py`:

```python
"""Arithmetic operations."""


def add(a: int, b: int) -> int:
    """Return a + b, validating inputs."""
    if not isinstance(a, int) or not isinstance(b, int):
        raise TypeError("add() takes integers")
    return a + b


def safe_div(a: float, b: float) -> float:
    """Divide a by b, raising a clear error on zero."""
    if b == 0:
        raise ZeroDivisionError("safe_div() divisor must be non-zero")
    return a / b
```

`tests/test_ops.py`:

```python
"""Tests for calc.ops."""

from calc.ops import add, safe_div


def test_add() -> None:
    """add() sums integers."""
    assert add(2, 3) == 5


def test_safe_div() -> None:
    """safe_div() divides."""
    assert safe_div(6, 3) == 2
```

## Step 2: generate a config and point the scan at it

This section writes the default config and makes one edit. Doctor will **not** read the file unless you pass `-c`.

Executed: yes (cwd `/tmp/w2/fp/work`, exit 0, W2-13).

```bash
cd /tmp/w2/fp/work
somnus-debug doctor init-config -o /tmp/w2/fp/calc/python_doctor.yaml
```

```text
Wrote default configuration: /tmp/w2/fp/calc/python_doctor.yaml
```

The generated file, verbatim:

```yaml
schema_version: "3.0"
min_function_lines: 5
min_class_lines: 6
min_docstring_length: 18
max_cyclomatic_complexity: 12
max_report_evidence_lines: 5
include_patterns:
  - "*.py"
ignore_patterns:
  - "__pycache__/*"
  - "*.pyc"
  - ".git/*"
  - ".hg/*"
  - ".mypy_cache/*"
  - ".pytest_cache/*"
  - ".ruff_cache/*"
  - ".tox/*"
  - ".venv/*"
  - "venv/*"
  - "env/*"
  - "node_modules/*"
  - ".python_doctor/*"
  - "build/*"
  - "dist/*"
ignore_functions:
  - "__repr__"
  - "__str__"
ignore_classes: []
check_private_functions: false
check_nested_functions: true
require_module_docstring: true
require_class_docstring: true
require_function_docstring: true
require_parameter_hints: true
require_return_hints: true
detect_unused_imports: true
detect_test_gaps: true
detect_security_risks: true
detect_silent_failures: true
detect_dependency_cycles: true
state_dir: ".python_doctor"
reports_dir: "reports"
report_basename: "production_doctor_report"
severity_exit_level: "serious"
max_workers: 4
markdown_include_css: true
severity_levels:
  analysis_read_errors: "critical"
  syntax_errors: "critical"
  tokenization_errors: "critical"
  missing_imports: "serious"
  dependency_cycles: "serious"
  stubs: "serious"
  placeholder_returns: "serious"
  incomplete_methods: "serious"
  suspicious_short_classes: "serious"
  silent_failures: "serious"
  broad_exceptions: "serious"
  security_risks: "serious"
  test_gaps: "serious"
  todos: "minor"
  missing_docstrings: "minor"
  suspicious_short_functions: "minor"
  type_hint_gaps: "minor"
  complexity: "minor"
  unused_imports: "minor"
  duplicate_definitions: "minor"
```

The one edit, which makes the Markdown report plain:

```bash
sed -i 's/^markdown_include_css: true/markdown_include_css: false/' /tmp/w2/fp/calc/python_doctor.yaml
```

Things to know about this file before editing it further (details in [06-configuration/configuration-pitfalls](../06-configuration/configuration-pitfalls.md)):

- Keep string values quoted. Unquoted `none` becomes null and makes the scan exit 4 ([D-03](../DISCOVERY-LEDGER.md#d-03)).
- Doctor's YAML parser is a minimal subset. Malformed lines and unknown keys are accepted silently ([D-04](../DISCOVERY-LEDGER.md#d-04)).
- `detect_test_gaps` and `test_gaps` have no effect ([D-05](../DISCOVERY-LEDGER.md#d-05)).
- An `ignore_patterns` entry like `env/*` also skips any directory named `env` at any depth ([D-17](../DISCOVERY-LEDGER.md#d-17)).
- `include_patterns` uses fnmatch, where `*` crosses `/` and there is no real `**`.

## Step 3: scan, with and without the src path

This section shows why a src layout needs `PYTHONPATH`.

Executed: yes (cwd `/tmp/w2/fp/work`, W2-14).

Without `PYTHONPATH` (exit 1):

```bash
somnus-debug doctor scan /tmp/w2/fp/calc -c /tmp/w2/fp/calc/python_doctor.yaml --no-state -o /tmp/w2/fp/work/nopp.md
```

```text
Scan complete: files=3, issues=5, critical=0, serious=1
Markdown report: /tmp/w2/fp/work/nopp.md
JSON report: /tmp/w2/fp/work/nopp.json
```

The serious finding is `missing_imports tests/test_ops.py 3 Import could not be resolved: calc.ops.` The other four are `suspicious_short_functions` (minor).

With `PYTHONPATH=src` the import resolves. Doctor checks imports against the interpreter it runs in ([D-26](../DISCOVERY-LEDGER.md#d-26)). The import is then classified `third_party` rather than `local`, so cycles through such imports cannot be seen ([D-22](../DISCOVERY-LEDGER.md#d-22)).

## Step 4: record a baseline

This section makes the first stateful scan and keeps a copy of its JSON.

Executed: yes (exit 0, W2-14).

```bash
PYTHONPATH=/tmp/w2/fp/calc/src somnus-debug doctor scan /tmp/w2/fp/calc -c /tmp/w2/fp/calc/python_doctor.yaml
cp /tmp/w2/fp/calc/production_doctor_report.json baseline.json
```

```text
Scan complete: files=3, issues=4, critical=0, serious=0
Markdown report: /tmp/w2/fp/calc/production_doctor_report.md
JSON report: /tmp/w2/fp/calc/production_doctor_report.json
State latest markdown: /tmp/w2/fp/calc/.python_doctor/reports/latest.md
Run ID: 20261112T003752Z
```

The summary was `production_score: 92`, with four minor `suspicious_short_functions` findings. The scratch directory now holds `production_doctor.log`. The project gained `.python_doctor/` and the two root reports.

## Step 5: introduce a regression, see it, roll back, fix it

This section exercises history, the fieldkit `delta.py` gate, and rollback.

Executed: yes (W2-14, W2-16, W2-17).

Append a risky function to `src/calc/ops.py`:

```python
def evaluate(expression: str) -> float:
    """Evaluate a user-supplied arithmetic expression."""
    try:
        return float(eval(expression))
    except Exception:
        return 0.0
```

Rescan after at least one second. The pause avoids a same-second run-ID collision ([D-08](../DISCOVERY-LEDGER.md#d-08)).

```bash
sleep 1
PYTHONPATH=/tmp/w2/fp/calc/src somnus-debug doctor scan /tmp/w2/fp/calc -c /tmp/w2/fp/calc/python_doctor.yaml   # exit 1
somnus-debug doctor history /tmp/w2/fp/calc                                                                     # exit 0
```

```text
Scan complete: files=3, issues=8, critical=0, serious=3
...
Run ID: 20261112T003759Z
Run history:
- 20261112T003759Z | <completed_at> | files=3 | issues=8 | critical=0 | serious=3
  markdown=/tmp/w2/fp/calc/.python_doctor/reports/20261112T003759Z/production_doctor_report.md
  json=/tmp/w2/fp/calc/.python_doctor/reports/20261112T003759Z/production_doctor_report.json
- 20261112T003752Z | <completed_at> | files=3 | issues=4 | critical=0 | serious=0
  markdown=/tmp/w2/fp/calc/.python_doctor/reports/20261112T003752Z/production_doctor_report.md
  json=/tmp/w2/fp/calc/.python_doctor/reports/20261112T003752Z/production_doctor_report.json
```

The latest JSON's `state_delta` was `modified_files: ["src/calc/ops.py"]`, with the other two files unchanged.

Gate on what is new with the fieldkit script (from a checkout of `skills/somnus-debug-fieldkit/`):

```bash
python3 <fieldkit>/scripts/delta.py baseline.json /tmp/w2/fp/calc/production_doctor_report.json   # exit 1
```

It reported `REGRESSION: new serious/critical findings.` with four new findings: `security_risks` (eval), `broad_exceptions`, and `silent_failures` at `src/calc/ops.py:21-22`, plus one minor. The full output is in [automation-examples](../05-cli-and-tools/automation-examples.md#example-2-regression-gate-baseline-vs-latest-with-deltapy).

Roll the `latest` alias back to the baseline run:

```bash
somnus-debug doctor rollback /tmp/w2/fp/calc --run-id 20261112T003752Z    # exit 0
```

```text
Rolled latest report state back to run 20261112T003752Z.
Markdown report: /tmp/w2/fp/calc/.python_doctor/reports/20261112T003752Z/production_doctor_report.md
JSON report: /tmp/w2/fp/calc/.python_doctor/reports/20261112T003752Z/production_doctor_report.json
```

After the rollback, `.python_doctor/reports/latest.json` carried run ID `20261112T003752Z`. **The root `production_doctor_report.json` still carried `20261112T003759Z`.** Rollback never touches the root reports, and it never touches source ([D-09](../DISCOVERY-LEDGER.md#d-09)). An unknown ID (`--run-id NOPE`) printed `Doctor failure: Run ID does not exist in state history.` and exited 4.

Fix the code by deleting `evaluate`, then rescan and re-gate:

```text
Scan complete: files=3, issues=4, critical=0, serious=0        # doctor exit 0
{'exit': 0, 'persisting': 4, 'coverage_failure': False} new 0 resolved 0   # delta.py --json, exit 0
```

## Step 6: add the single-test harness (optional)

This section gives the project one artifact-producing test entrypoint without the placement trap.

Executed: yes (`/tmp/w2/hs/myproj`, the quickstart fixture; W2-19).

```bash
somnus-debug init-test-harness tools --no-contract     # NOT ".": see the placement trap
```

```text
wrote /tmp/w2/hs/myproj/tools/run_test.py

Next: edit TEST_NAME and execute_test() in run_test.py for this project. See CONTRACT.md for what the harness does and does not own.
```

Replace the shipped project-specific test, from `TEST_NAME = "` up to the `# Harness internals` banner, with your own. Splice script, executed as-is:

```python
"""Replace the template's project-specific test with a pytest-running test."""
import sys
from pathlib import Path

path = Path(sys.argv[1])
text = path.read_text(encoding="utf-8")
start = text.index('TEST_NAME = "')
end = text.index("# ============================================================================\n# Harness internals")
new_block = '''TEST_NAME = "myproj unit tests"


def execute_test(ctx: TestContext) -> TestOutcome:
    """Run the project's pytest suite once and record the result."""
    result = subprocess.run(
        [sys.executable, "-m", "pytest", "-q", "-p", "no:cacheprovider", "tests"],
        cwd=ctx.project_root, capture_output=True, text=True,
    )
    (ctx.artifact_dir / "pytest.txt").write_text(result.stdout + result.stderr, encoding="utf-8")
    return TestOutcome(
        summary="pytest over tests/",
        checks=[Check("pytest-exit-zero", result.returncode == 0, expected=0, observed=result.returncode)],
        metrics={"pytest_exit": result.returncode},
    )


'''
path.write_text(text[:start] + new_block + text[end:], encoding="utf-8")
```

```bash
python3 splice.py tools/run_test.py
PYTHONPATH=. python tools/run_test.py      # exit 0
```

```text
{
  "run_id": "MYPROJ-UNIT-TESTS-20261112-003727-0f3430",
  "test_name": "myproj unit tests",
  "verdict": "PASS",
  "elapsed_s": 0.369095,
  "artifacts": {
    "manifest": "/tmp/w2/hs/myproj/test-runs/MYPROJ-UNIT-TESTS-20261112-003727-0f3430/manifest.json",
    "report": "/tmp/w2/hs/myproj/test-runs/MYPROJ-UNIT-TESTS-20261112-003727-0f3430/report.md",
    "log": "/tmp/w2/hs/myproj/test-runs/MYPROJ-UNIT-TESTS-20261112-003727-0f3430/test.log"
  }
}
```

The artifacts are now inside the project, in `test-runs/<RUN_ID>/`, alongside `pytest.txt`. Two follow-ups:

- The template imports `subprocess` and `sys` already. Its other "common" imports (`hashlib`, `shutil`, `sqlite3`, `tempfile`) will now show up as `unused_imports`.
- The next doctor scan counts `tools/run_test.py` as a new file with 9 serious findings inherited from the template (W2-19). Disposition them narrowly or add `tools/run_test.py` to `ignore_patterns`.

## Step 7: what to commit

This section separates durable project files from run output.

| Commit | Do not commit |
|---|---|
| `python_doctor.yaml` (and remember every caller must pass `-c`) | `production_doctor_report.{md,json}`, `.python_doctor/`, `production_doctor.log`, `test-runs/` |
| `tools/run_test.py` (edited) | `baseline.json` copies, unless you deliberately version a baseline the way the fieldkit's `.somnus-debug/runs/` convention does (that directory is git-ignored by onboard) |

The ignore patterns matching the left-hand column's run output are in this repo's own `.gitignore`: `*_report.md`, `*_report.json`, `.python_doctor/`, `*.log`.

## Sources

This section lists the code and evidence this page draws on.

- `src/somnus_debug/doctor/core.py:451-502` (defaults), `:854-924` (`default_yaml`), `:995-1057`, `:1916-2010`, `:2061-2120`
- `src/somnus_debug/test_harness/templates/run_test.py:117-136`, `:195-487`, `:749`
- [lane B configuration-findings.md](../_evidence/agent-findings/lane-b-config/configuration-findings.md)
- [lane F fieldkit.md](../_evidence/agent-findings/lane-f-ext/fieldkit.md), [harness.md](../_evidence/agent-findings/lane-f-ext/harness.md), [compositions.md](../_evidence/agent-findings/lane-f-ext/compositions.md)
- W2 runs: [verification-results](../11-verification/verification-results.md#w2-runs)
