# Exceptions

This page lists every exception a library caller can receive from each tool, and how each one maps to a CLI exit code. The doctor has a typed hierarchy. The other three tools raise plain built-in exceptions.

## Doctor error hierarchy

This section documents the `DoctorError` family, its fields, and its rendered form.

```
RuntimeError
└── DoctorError                     src/somnus_debug/doctor/core.py:95
    ├── ConfigurationError          :123   "Fix the configuration file or regenerate it with init-config."
    ├── FileReadError               :138   "Verify the file exists, permissions are correct, and the encoding is valid."
    ├── ReportGenerationError       :153   "Check output directory permissions and disk availability, then rerun."
    ├── StateStoreError             :168   "Inspect the state database and report directory permissions."
    └── AnalysisExecutionError      :183   "Inspect the project root and rerun with a valid path."
```

[SOURCE-CONFIRMED] each line. [VERIFIED] `/tmp/w1/ex_tools.py` printed the five subclasses and `RuntimeError` as the base.

`DoctorError(message: str, remediation: str | None = None, context: JsonObject | None = None)` has the attributes `.message`, `.remediation` (falls back to the class `default_remediation`), and `.context` (a dict). `.render()` returns:

```
Doctor failure: <message>
Remediation: <remediation>
Context:
<json.dumps(context, indent=2, sort_keys=True) or "{}">
```

The subclasses take only `(message, context=None)`, and always pass their class default as the remediation (`:128-135` and siblings). A caller cannot set a custom remediation on a subclass. `run_init_config` works around this by putting `"remediation"` inside `context`, so the rendered `Remediation:` line still shows the generic text. [VERIFIED] `/tmp/w1/ex_api.py`:

```
Doctor failure: Configuration file already exists.
Remediation: Fix the configuration file or regenerate it with init-config.
Context:
{
  "path": "x",
  "remediation": "Use --force to replace it."
}
```

Because `DoctorError` subclasses `RuntimeError`, `except RuntimeError` in a host program also catches every doctor error. [SOURCE-CONFIRMED] `:95`.

## What raises what (doctor)

This section maps each error to its sources, so a caller knows what to catch around each call.

| Exception | Raised by | Typical cause |
|---|---|---|
| `ConfigurationError` | `ConfigManager.__init__`, `MinimalYamlParser.parse`, `parse_yaml_scalar`, `require_*`, `parse_severities`, `run_init_config` | missing, bad-suffix, or malformed config; failed type check; `init-config` target exists |
| `AnalysisExecutionError` | `ProjectFileIndex._discover` (so `ProjectScanner.__init__`) | project root missing or not a directory |
| `FileReadError` | `SourceReader.read` (caught and converted to an issue), `stable_hash_file`, `FileAnalyzer._assemble` (stat) | unreadable or undecodable file; the stat/hash variants propagate |
| `ReportGenerationError` | `write_text_atomic` | output directory not writable |
| `StateStoreError` | every `StateStore` method except `report_paths`, `copy_file_atomic` | unusable DB, unknown `run_id`, missing stored artifacts |

[SOURCE-CONFIRMED] raise sites. [VERIFIED] examples in `/tmp/w1/ex_tools.py`:

```
AnalysisExecutionError: Project root does not exist. | Inspect the project root and rerun with a valid path.
ConfigurationError: Configuration file does not exist.
ConfigurationError: Configuration path must end with .yaml, .yml, or .json.
```

The first `ConfigurationError` above came from passing the relative `Path("x.toml")` before the file existed. The existence check runs before the suffix check (`:800-814`).

## Non-doctor exceptions the doctor can raise

This section lists the built-in exceptions that escape the scan engine. Callers who only catch `DoctorError` miss these.

| Exception | Where | Condition |
|---|---|---|
| Any exception from `FileAnalyzer.analyze`, including `RecursionError` | `ProjectScanner.scan` | only on the serial path (`max_workers == 1` or a one-file project); the threaded path converts these to issues |
| `KeyError`, `AttributeError`, and other unlisted types | anywhere | not converted by `main`; these escape as a traceback |
| `sqlite3.Error` | not expected from `StateStore`, which wraps it | `main` maps any that escape to exit 5 |

[VERIFIED] serial-path `ValueError` and `RecursionError` in `/tmp/w1/ex_serial.py` and in `/tmp/w1/rec1` versus `rec2` ([execution-model](../01-system/execution-model.md#doctor-the-serial-path-drops-the-error-wrapper)). Other rows [SOURCE-CONFIRMED] `src/somnus_debug/doctor/core.py:1716-1731`, `:2189-2199`.

## Exit-code mapping in `doctor.main`

This section shows how exceptions become process exit codes. It matters when you call `main` from Python.

| Outcome | Return / raise |
|---|---|
| success | `exit_code_for_summary`: 0, 1, or 2 |
| `DoctorError` subclass | return 4, after logging ERROR and printing `render()` to stderr |
| `OSError`, `RuntimeError` (non-Doctor), `TypeError`, `ValueError`, `sqlite3.Error` | return 5, after logging CRITICAL with traceback to `production_doctor.log` and printing a rendered generic `DoctorError` |
| argparse error / `--help` | raises `SystemExit(2)` / `SystemExit(0)` |
| anything else | propagates |

[SOURCE-CONFIRMED] `src/somnus_debug/doctor/core.py:2187-2199`. [VERIFIED] 0, 1, 2, 4, and 5 all observed in [lane-d exit-codes](../_evidence/agent-findings/lane-d-cli-tests/exit-codes.md). Code 3 is unused. Exit 2 is shared between the critical gate and usage errors ([D-18](../DISCOVERY-LEDGER.md#d-18)).

## structure, pycache-clean, init-test-harness

This section lists what the other tools raise, since they have no error classes of their own.

| Call | Raises | Notes |
|---|---|---|
| `build_index` | `SyntaxError` (including the type-comment false positive, [D-01](../DISCOVERY-LEDGER.md#d-01)), possibly `ValueError` | `main` maps `OSError`/`SyntaxError` to 2; `UnicodeDecodeError` propagates ([lane-b §2.4](../_evidence/agent-findings/lane-b-config/configuration-findings.md)) |
| `PycacheCleaner(cfg)` | `ValueError("No roots specified in configuration.")`; `TypeError` on wrong value types (for example `targets: None`) | `main` catches all `Exception` → `sys.exit(1)` |
| `CleanerConfig.from_yaml` | `yaml.YAMLError`, `AttributeError` (non-mapping root), `OSError` | not caught by `main`: traceback, exit 1 [VERIFIED] [lane-d exit-codes](../_evidence/agent-findings/lane-d-cli-tests/exit-codes.md) P06/P07 |
| `PycacheCleaner.run` | essentially none: permission and OS errors are logged and skipped | missing roots logged at ERROR |
| `scaffold` | `FileExistsError` (refusal), `OSError` | `main` maps `FileExistsError` to 1 |
| `cli.main` | anything but `SystemExit` from the tool | `SystemExit(int)` → int; non-int → 1 |

[VERIFIED] `ValueError` and `FileExistsError` in `/tmp/w1/ex_tools.py`.

## Recommended catch pattern

This section gives a defensive wrapper for embedding the doctor scan.

```python
from pathlib import Path
from somnus_debug.doctor import core as d

def scan(root: str, config: str | None = None):
    try:
        cm = d.ConfigManager(Path(config).resolve() if config else None)
        return d.ProjectScanner(Path(root), cm).scan({})
    except d.DoctorError as err:          # config, root, read/stat failures
        raise SystemExit(err.render())
    except RecursionError as err:         # serial path only; see execution-model
        raise SystemExit(f"pathological source: {err}")
```

Executed: yes (`/tmp/w1/ex_wrap.py`, exit 0):

```
('proj',) -> 37
('nope',) -> SystemExit: Doctor failure: Project root does not exist.
('rec1',) -> SystemExit: pathological source: maximum recursion depth exceeded during ast construction
```

## Sources

This section lists the code, evidence files, and probes this page rests on.

- `src/somnus_debug/doctor/core.py:95-196`, `:796-851`, `:1058-1067`, `:1590-1595`, `:1716-1731`, `:1916-2031`, `:2096-2104`, `:2184-2199`
- `src/somnus_debug/structure/core.py:323-347`, `src/somnus_debug/pycache_cleaner/core.py:170-195`, `:349-372`, `src/somnus_debug/test_harness/scaffold.py:62-125`, `src/somnus_debug/cli.py:85-104`
- [lane-a api-reference.md](../_evidence/agent-findings/lane-a-arch-api/api-reference.md), [lane-d exit-codes.md](../_evidence/agent-findings/lane-d-cli-tests/exit-codes.md), [lane-b configuration-findings.md](../_evidence/agent-findings/lane-b-config/configuration-findings.md)
- Executed probes: `/tmp/w1/ex_api.py`, `/tmp/w1/ex_tools.py`, `/tmp/w1/ex_serial.py`, `/tmp/w1/rec1`, `/tmp/w1/rec2`
