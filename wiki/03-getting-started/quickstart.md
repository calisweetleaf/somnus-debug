# Quickstart

This page takes you from install to a first doctor report, a structure index, a safe pycache dry run, and a scaffolded harness in about ten commands. Every command and output below was executed in this wave on a throwaway fixture under `/tmp/w2`, with somnus-debug 0.1.0 installed from this repo into a fresh Python 3.12.15 venv. Read the three warnings first. They are the ways a first run surprises people.

## Three warnings before you start

This section states the first-run hazards up front.

1. **Every doctor call writes `production_doctor.log` into your current directory**, even `--help`. Run doctor from a scratch directory if you do not want that file in your repo. [VERIFIED] W2-01, W2-10. See [D-10](../DISCOVERY-LEDGER.md#d-10).
2. **`structure` crashes on files with a `# somnus:metadata:v2` header** (or any comment line shaped like a type comment, such as `#     type: "..."`). It prints `error: invalid syntax (<file>, line N)` and exits 2. This includes every source file in this repository. [VERIFIED] W2-15. See [D-01](../DISCOVERY-LEDGER.md#d-01).
3. **`init-test-harness .` at a repo root puts test artifacts outside the repo**, in `<repo>/../test-runs/`. Scaffold into a subdirectory such as `tools/`. [VERIFIED] W2-19. See [D-15](../DISCOVERY-LEDGER.md#d-15).

## 1. Install

This section installs the package into an isolated environment.

Executed: yes (`/tmp/w2`, exit 0, W2-02).

```bash
python3 -m venv venv
./venv/bin/pip install /path/to/somnus-debug      # or: pip install somnus-debug   (PyPI 0.1.0)
export PATH="$PWD/venv/bin:$PATH"
somnus-debug --version
```

```text
0.1.0
```

PyPI 0.1.0 has the same code as this tree's `src/`. The only difference is the reference-only `default_config.yaml`, so either source works. [VERIFIED] lane D [install-vs-source.md](../_evidence/agent-findings/lane-d-cli-tests/install-vs-source.md) section 3. Full options: [installation](../02-installation/installation.md).

## 2. Make a tiny project

This section creates the fixture every later step uses.

Executed: yes (`/tmp/w2/qs/myproj`).

```bash
mkdir -p myproj/app myproj/tests && cd myproj
cat > app/__init__.py <<'EOF'
"""Demo application package."""
EOF
cat > app/core.py <<'EOF'
"""Core arithmetic helpers for the demo project."""

import json


def add(a: int, b: int) -> int:
    """Return the sum of a and b."""
    return a + b


def parse_count(text: str) -> int:
    """Parse a count from text, falling back to zero."""
    try:
        return int(text)
    except ValueError:
        pass
    return 0


def export_report(values: list[int]) -> str:
    """Serialize values for a report."""
    # TODO: include a schema version
    raise NotImplementedError
EOF
cat > tests/test_core.py <<'EOF'
"""Tests for app.core."""

from app.core import add


def test_add() -> None:
    """add() sums two integers."""
    assert add(2, 3) == 5
EOF
```

## 3. First scan (no state)

This section runs doctor once without its history database.

Executed: yes (cwd `/tmp/w2/qs/myproj`, exit 1, W2-10).

```bash
somnus-debug doctor scan . --no-state
echo "exit=$?"
```

```text
Scan complete: files=3, issues=7, critical=0, serious=2
Markdown report: /tmp/w2/qs/myproj/production_doctor_report.md
JSON report: /tmp/w2/qs/myproj/production_doctor_report.json
exit=1
```

Exit 1 means "serious findings, no critical" under the default `serious` gate ([exit-codes](../05-cli-and-tools/exit-codes.md)). The project root now holds `production_doctor.log` (0 bytes), `production_doctor_report.md`, and `production_doctor_report.json`.

What it found, read from the JSON:

```text
minor   unused_imports              app/core.py 3  json
minor   suspicious_short_functions  app/core.py 6  add
serious silent_failures             app/core.py 15 parse_count
serious stubs                       app/core.py 20 export_report
minor   suspicious_short_functions  app/core.py 20 export_report
minor   todos                       app/core.py 22 <comment>
minor   suspicious_short_functions  tests/test_core.py 6 test_add
```

The JSON `summary` is `production_score: 74` (100 - 2x8 - 5x2). The full report shape is in [input-output-contracts](../05-cli-and-tools/input-output-contracts.md#doctor-json-report-schema-as-observed).

Two of these findings are judgment calls rather than bugs:

- `except ValueError: pass` followed by `return 0` is flagged as a silent failure by design.
- A 1-line function counts as "suspiciously short" under the default `min_function_lines: 5`.

Tune both with a config file ([first-project](first-project.md)).

## 4. Stateful scan and history

This section turns on run history.

Executed: yes (cwd `/tmp/w2/qs/myproj`, scan exit 1, history exit 0, W2-11/W2-14).

```bash
somnus-debug doctor scan .
somnus-debug doctor history .
```

```text
Scan complete: files=3, issues=7, critical=0, serious=2
Markdown report: /tmp/w2/qs/myproj/production_doctor_report.md
JSON report: /tmp/w2/qs/myproj/production_doctor_report.json
State latest markdown: /tmp/w2/qs/myproj/.python_doctor/reports/latest.md
Run ID: 20261112T003638Z
Run history:
- 20261112T003638Z | <completed_at> | files=3 | issues=7 | critical=0 | serious=2
  markdown=/tmp/w2/qs/myproj/.python_doctor/reports/20261112T003638Z/production_doctor_report.md
  json=/tmp/w2/qs/myproj/.python_doctor/reports/20261112T003638Z/production_doctor_report.json
```

`<completed_at>` is an ISO-8601 UTC timestamp. The sandbox display rewrote it, so it is elided here. State now lives in `.python_doctor/`:

- `state.sqlite3`
- `reports/<RUN_ID>/production_doctor_report.{md,json}`
- `reports/latest.{md,json}`

If you scan twice within the same second, the second run replaces the first in history ([D-08](../DISCOVERY-LEDGER.md#d-08)).

## 5. Index a file with structure

This section shows the indexer on a normal file and on a stamped one.

Executed: yes (cwd `/tmp/w2/qs/myproj`, W2-15).

```bash
somnus-debug structure app/core.py          # exit 0
```

```text
# Class Index for `core.py`

Generated by `analyze_python_structure.py` using Python's AST; the source is never imported or executed.

- Class declarations: 0 (0 top-level, 0 nested)
- Definitions emitted (module-level functions and class methods): 3

_No classes found._

## Module-level functions

- `def add(a: int, b: int) -> int:` (lines 6-8)
  - Return the sum of a and b.
- `def parse_count(text: str) -> int:` (lines 11-17)
  - Parse a count from text, falling back to zero.
- `def export_report(values: list[int]) -> str:` (lines 20-23)
  - Serialize values for a report.
```

On a copy of the same file with this repo's 32-line metadata header prepended (`stamped.py`), it fails:

```text
$ somnus-debug structure stamped.py
error: invalid syntax (stamped.py, line 9)            # exit 2; line 9 is `#     type: "source-code"`
```

Workaround: run the repo-root duplicate, which parses without `type_comments` and exits 0:

```bash
python3 <repo>/analyze_python_structure.py stamped.py
```

Doctor scans the same stamped file without crashing (exit 1, 6 ordinary findings). [VERIFIED] W2-15.

Add `-o INDEX.md` to write the index to a file. It prints nothing when writing to a file. [VERIFIED] W2-22.

## 6. Dry-run the pycache cleaner

This section shows the cleaner safely. It has no path argument; roots come from a YAML file.

Executed: yes (cwd `/tmp/w2/pc`, all exit 0, W2-18).

```bash
mkdir -p tree/pkg/__pycache__ tree/node_modules/x/__pycache__
touch tree/pkg/__pycache__/m.cpython-312.pyc tree/pkg/loose.pyc tree/node_modules/x/__pycache__/n.pyc tree/pkg/keep.py
cat > config.yaml <<EOF
roots:
  - /tmp/w2/pc/tree
exclude:
  - node_modules
EOF
somnus-debug pycache-clean --dry-run
```

```text
2026-11-12 00:37:07,852 [INFO] Starting pycache cleaner (dry_run=True)
2026-11-12 00:37:07,853 [INFO] Scanning root: /tmp/w2/pc/tree
2026-11-12 00:37:07,853 [INFO] Summary: deleted 1 directories, 1 files; freed 0.00 MiB
```

Nothing was deleted: all four files were still present. The "deleted" wording is the same in dry-run and real runs. A real run (`somnus-debug pycache-clean`) then removed `pkg/__pycache__/` and `pkg/loose.pyc`, and kept `node_modules/x/__pycache__/` (excluded by basename) and `keep.py`.

## 7. Scaffold the single-test harness (correctly)

This section shows the placement trap and the fix.

Executed: yes (`/tmp/w2/hs/myproj`, W2-19).

The trap. Scaffolding at the repo root and running the unedited template:

```text
$ somnus-debug init-test-harness .
wrote /tmp/w2/hs/myproj/run_test.py
wrote /tmp/w2/hs/myproj/CONTRACT.md
...
$ python3 run_test.py          # exit 1
{ ... "verdict": "FAIL",
  "artifacts": { "manifest": "/tmp/w2/hs/test-runs/GOLDEN-PATH-LAYER-1-DATA-HIGHWAY-RESTORATION-20261112-003719-434431/manifest.json", ... } }
```

The artifacts went to `/tmp/w2/hs/test-runs/`, **outside** the project. The test FAILs because the shipped `execute_test` is a project-specific cargo test.

The fix: scaffold one level down and replace `execute_test`. See [first-project step 6](first-project.md#step-6-add-the-single-test-harness-optional) for the exact splice. The result was `"verdict": "PASS"`, exit 0, with artifacts in `/tmp/w2/hs/myproj/test-runs/`.

## Where next

This section points at the next pages.

- A full loop with a config file, a src layout, regression detection, history, and rollback: [first-project](first-project.md).
- Copy-paste snippets per tool: [minimal-examples](minimal-examples.md).
- Things that went wrong: [troubleshooting-first-run](troubleshooting-first-run.md).

## Sources

This section lists the code and evidence this page draws on.

- `src/somnus_debug/doctor/core.py:1953-1960`, `:2061-2093`, `:2179-2181`
- `src/somnus_debug/structure/core.py:210`, `:323-347`
- `src/somnus_debug/pycache_cleaner/core.py:323-372`
- `src/somnus_debug/test_harness/templates/run_test.py:749`
- [lane D install-vs-source.md](../_evidence/agent-findings/lane-d-cli-tests/install-vs-source.md), [command-reference.md](../_evidence/agent-findings/lane-d-cli-tests/command-reference.md)
- [lane F harness.md](../_evidence/agent-findings/lane-f-ext/harness.md)
- W2 runs: [verification-results](../11-verification/verification-results.md#w2-runs)
