# Minimal examples

This page gives the smallest working invocation for each common task, one block per task, with the observed result. Every block was executed in this wave against the installed 0.1.0 venv (Python 3.12.15) under `/tmp/w2`, with cwd outside any project, unless it says otherwise.

## doctor

This section covers scans, configs, and history.

Scan a directory, no state, reports out of the tree. Executed: yes (W2-21, exit 1 on a project with one serious finding).

```bash
somnus-debug doctor scan /path/to/project --no-state -o out/doctor.md --json-output out/doctor.json
```

Scan with a JSON config that disables the gate and narrows the scan. Executed: yes (`/tmp/w2/min`, exit 0; `files=2, issues=2, critical=0, serious=1` (from the reduced post-reset fixture holding only `parse_count`; on the full quickstart fixture the same code prints `files=2, issues=6, critical=0, serious=2` [VERIFIED review-h])).

```bash
echo '{"severity_exit_level": "none", "include_patterns": ["app/*.py"]}' > gate-none.json
somnus-debug doctor scan /tmp/w2/qs/myproj -c gate-none.json --no-state -o /tmp/w2/min/r.md
```

Gate only on critical findings (YAML; **keep the value quoted**). Executed: not in this wave. The `critical` gate was run by lane D (D26_critical, exit 2 with a critical finding present). The quoting rule was tested in W2-08 with `none`: quoted `"none"` exited 0, unquoted `none` exited 4.

```yaml
severity_exit_level: "critical"
```

Write the default config somewhere specific. Executed: yes (W2-13, exit 0).

```bash
somnus-debug doctor init-config -o /path/to/project/python_doctor.yaml
```

History and rollback. Executed: yes (W2-14 history exit 0; W2-16 rollback exit 0, unknown ID exit 4).

```bash
somnus-debug doctor history /path/to/project --limit 5
somnus-debug doctor rollback /path/to/project --run-id 20261112T003752Z
```

src-layout project. Executed: yes (W2-14: `missing_imports` serious without `PYTHONPATH`, 0 serious with it).

```bash
PYTHONPATH=/path/to/project/src somnus-debug doctor scan /path/to/project -c /path/to/project/python_doctor.yaml
```

## structure

This section covers the indexer.

```bash
somnus-debug structure app/core.py                         # stdout; exit 0 (W2-15)
somnus-debug structure app/core.py -o docs/CORE_INDEX.md   # file only, prints nothing; exit 0 (W2-22)
somnus-debug structure app/core.py --no-line-numbers --no-module-functions --source-label core.py   # flags (lane D S10)
python3 <repo>/analyze_python_structure.py stamped.py      # root duplicate: works on metadata-stamped files; exit 0 (W2-15)
```

## pycache-clean

This section covers the cleaner. Roots come only from the config.

Executed: yes (`/tmp/w2/pc`, W2-18, exit 0 both runs).

```bash
printf 'roots:\n  - /abs/path/tree\nexclude:\n  - node_modules\n' > config.yaml
somnus-debug pycache-clean --dry-run --verbose     # reports what it would remove ("Removed ...")
somnus-debug pycache-clean                         # actually removes
```

## init-test-harness

This section covers the scaffolder.

Executed: yes (W2-19, exit 0).

```bash
somnus-debug init-test-harness tools --no-contract    # writes tools/run_test.py
python3 tools/run_test.py                              # FAILs until execute_test is replaced (exit 1)
```

## Python library calls

This section shows the importable entry points that need no subprocess.

Executed: yes (`/tmp/w2/min`, exit 0).

```python
from pathlib import Path
from somnus_debug.structure import build_index
src = Path("/tmp/w2/qs/myproj/app/core.py").read_text(encoding="utf-8")
print(build_index(src, source_name="core.py", include_lines=False).splitlines()[-2:])

from somnus_debug.test_harness.scaffold import scaffold
print(scaffold(Path("/tmp/w2/min/harness"), with_contract=False))

from somnus_debug.doctor.core import ConfigManager
cm = ConfigManager(Path("/tmp/w2/min/gate-none.json"))
print(cm.config.severity_exit_level, cm.config.include_patterns, cm.config.max_workers)
```

```text
['- `def parse_count(text: str) -> int:`', '  - Parse a count from text, falling back to zero.']
[PosixPath('/tmp/w2/min/harness/run_test.py')]
none ('app/*.py',) 4
```

A full doctor scan without the CLI's logging side effects, executed in W2-20:

```python
ProjectScanner(Path(root), ConfigManager(None)).scan({})
```

See [automation-examples](../05-cli-and-tools/automation-examples.md#example-4-in-process-call-from-python). More API detail: [04-library-api/public-api](../04-library-api/public-api.md).

## Module and dispatcher forms

This section lists the `python -m` forms that work.

| Form | Result |
|---|---|
| `python -m somnus_debug.cli --version` | `0.1.0`, exit 0 [VERIFIED] `/tmp/w2/min` |
| `python -m somnus_debug.doctor.core scan ...` | works, with a runpy `RuntimeWarning`; also works without PyYAML [VERIFIED] W2-05 |
| `python -m somnus_debug.structure.core FILE` | works, with a runpy `RuntimeWarning` [VERIFIED] W2-05 |
| `python -m somnus_debug.test_harness.scaffold --help` | works; `prog` shows `somnus-debug init-test-harness` [VERIFIED] W2-02 |
| `python -m somnus_debug` / `python -m somnus_debug.doctor` | no `__main__`, exit 1 [VERIFIED] lane D C04, C05 |

## Sources

This section lists the code and evidence this page draws on.

- `src/somnus_debug/structure/__init__.py`; `src/somnus_debug/structure/core.py:202-208`
- `src/somnus_debug/test_harness/scaffold.py:62-88`
- `src/somnus_debug/doctor/core.py:782-814`, `:1695-1705`
- [lane D experiment-log.md](../_evidence/agent-findings/lane-d-cli-tests/experiment-log.md)
- W2 runs: [verification-results](../11-verification/verification-results.md#w2-runs)
