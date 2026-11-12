# Recipe: scan in-process with `ProjectScanner` (no files, no logging changes)

**Tier:** small integration step. Uses classes that are importable but not exported or marked stable. **Script:** [embed_scan.py](../_repro/embed_scan.py).

Run doctor's full analysis from Python and get structured results, without the CLI's side effects: no log file in the cwd, no reports, no state directory, no change to the host's logging.

## When to use

This section says when to embed instead of shelling out.

When a Python host (a test, a notebook, an agent tool, a custom gate) needs findings as objects, or must not have its logging replaced. `doctor.core.main()` writes `production_doctor.log` to the cwd and calls `logging.basicConfig(force=True)` ([D-10](../../DISCOVERY-LEDGER.md#d-10), [D-11](../../DISCOVERY-LEDGER.md#d-11)); `ProjectScanner` does neither ([D-12](../../DISCOVERY-LEDGER.md#d-12)). If you need `main()` itself, see [inprocess-main-isolated](inprocess-main-isolated.md).

## The code

This section is the full script.

```python
"""Scan a tree in-process with doctor's library classes: no files written, no logging changes."""
import json
import logging
import sys
from collections import Counter
from pathlib import Path

from somnus_debug.doctor.core import ConfigManager, ProjectScanner, dumps_json, exit_code_for_summary

root = Path(sys.argv[1]).resolve()
config = ConfigManager(Path(sys.argv[2]) if len(sys.argv) > 2 else None)   # None = built-in defaults
before = set(root.rglob("*"))
result = ProjectScanner(root, config).scan({})                               # {} = no previous index, all files "new"
summary = result.summary
print("files", summary.files_scanned, "issues", summary.total_issues,
      "critical", summary.critical_issues, "serious", summary.serious_issues, "score", summary.production_score)
print("by category", Counter(i.category for i in result.issues).most_common(4))
print("gate", config.config.severity_exit_level, "->", exit_code_for_summary(summary, config.config.severity_exit_level))
payload = json.loads(dumps_json(result))                                     # same shape as --json-output
print("json keys", sorted(payload))
print("new paths under root:", sorted(str(p) for p in set(root.rglob("*")) - before))
print("root handlers:", logging.getLogger().handlers, "cwd log:", Path("production_doctor.log").exists())
```

## Executed result

This section shows the run and the side-effect checks.

Executed: yes (`/tmp/w4/p`, 4-file lane-A fixture without its syntax-error file, run with `/tmp/w4/venv/bin/python`; [stage 4 log](../_repro/logs/stage4_programmatic.log), section P1)

```text
$ python embed_scan.py proj
files 4 issues 32 critical 0 serious 13 score 0
by category [('suspicious_short_functions', 11), ('stubs', 6), ('unused_imports', 3), ('duplicate_definitions', 2)]
gate serious -> 1
json keys ['config_hash', 'dependency_graph', 'files', 'finished_at', 'issues', 'project_root', 'run_id', 'started_at', 'state_delta', 'summary']
new paths under root: []
root handlers: [] cwd log: False                                             [exit=0]
$ ls
proj                                                                         # nothing else in the cwd
```

The counts match the CLI scan of the same tree in [severity-and-gate-tuning](../intermediate/severity-and-gate-tuning.md) (`issues=32, critical=0, serious=13`, exit 1) [VERIFIED].

## API notes

This section lists what the objects give you. Details: [lane-a API reference](../../_evidence/agent-findings/lane-a-arch-api/api-reference.md).

- `ConfigManager(path | None)`: raises `ConfigurationError` on a missing path, bad suffix, malformed file or failed type check; `.config` is a frozen `DoctorConfig`; `.config_hash` is sha256 hex [VERIFIED by lane A].
- `ProjectScanner(root, cm)`: walks the tree in the constructor and raises `AnalysisExecutionError` for a missing root [VERIFIED by lane A].
- `.scan(previous_index)`: returns a frozen `ProjectAnalysisResult` with `summary`, `issues` (each with `category, severity, file_path, line_number, column_offset, symbol, message, evidence, remediation, details`), `files`, `dependency_graph`, `state_delta`.
- `exit_code_for_summary(summary, gate)`: the CLI's gate logic; an unknown gate returns 1 [SOURCE-CONFIRMED, `src/somnus_debug/doctor/core.py:2046-2058`].
- `dumps_json(result)` produces the same JSON as `--json-output`: for the same tree, every top-level key except `run_id`, `started_at` and `finished_at` was equal to the CLI's report, `config_hash` included (the CLI run used `init-config`'s file, the library run used `ConfigManager(None)`). A file you write from it is a valid `delta.py` input [VERIFIED, [stage 4b log](../_repro/logs/stage4b_json_parity.log)].

## Pitfalls

This section lists what still depends on the environment.

- Third-party import resolution uses `find_spec` in **your** interpreter and `sys.path`, so `missing_imports` differs between hosts ([D-26](../../DISCOVERY-LEDGER.md#d-26)).
- `run_id` is per-second; irrelevant here since nothing is persisted.
- `somnus_debug.doctor` exports only `main`; these imports reach into `doctor.core` and can change without notice.

## Sources

This section lists the files, logs and evidence this page rests on.

- [stage 4 log](../_repro/logs/stage4_programmatic.log), [stage 4b log](../_repro/logs/stage4b_json_parity.log), [embed_scan.py](../_repro/embed_scan.py)
- [lane-a API reference §1](../../_evidence/agent-findings/lane-a-arch-api/api-reference.md), [lane-a ex2](../../_evidence/agent-findings/lane-a-arch-api/examples/ex2_doctor_lib.py.txt)
- `src/somnus_debug/doctor/core.py:782-799`, `:1695`, `:2046-2058`
