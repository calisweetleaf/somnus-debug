# Types and schemas

This page is the field-level reference for every data type the library returns or accepts, and for the JSON report the doctor writes. Fields are listed in declaration order, which is also the positional constructor order. Configuration semantics per key are in [06-configuration/complete-option-reference](../06-configuration/complete-option-reference.md); this page gives types and defaults only.

## Aliases, enum and constants

This section lists the type aliases and the one enum the other types use.

| Name | Definition | Location |
|---|---|---|
| `JsonScalar` | `str \| int \| float \| bool \| None` | `src/somnus_debug/doctor/core.py:74` |
| `JsonValue` | `JsonScalar \| list[JsonValue] \| dict[str, JsonValue]` | `:75` |
| `JsonObject` | `dict[str, JsonValue]` | `:76` |
| `ImportKind` | `Literal["local","standard_library","third_party","missing","unresolved_relative"]` | `:77` |
| `Severity(str, Enum)` | `CRITICAL="critical"`, `SERIOUS="serious"`, `MINOR="minor"`, `INFO="info"` | `:86-92` |
| `RUN_ID_FORMAT` | `"%Y%m%dT%H%M%SZ"` | `:82` |
| `COMMANDS` | `{"scan","init-config","history","rollback","self-check"}` | `:83` |
| `LOGGER_NAME` | `"python_production_doctor"` | `:80` |
| `TODO_PATTERNS` | `(regex, label)` pairs for TODO, FIXME, HACK, XXX, TEMP, WIP | `:504-511` |
| `PLACEHOLDER_CONSTANTS` | `(None, False, True, 0, -1, "")` | `:513` |
| `SECURITY_CALLS` | `eval`, `exec`, `compile`, `pickle.load(s)`, `subprocess.call/run/Popen`, `os.system`, `os.popen`, `yaml.load`, `marshal.load(s)` | `:514` |

Because `Severity` subclasses `str`, `Severity.MINOR == "minor"` is true. It serializes as its value. [SOURCE-CONFIRMED]

## DoctorConfig

This section lists the 29 validated configuration fields with their default values.

`@dataclass(frozen=True) class DoctorConfig` lives at `src/somnus_debug/doctor/core.py:207-240`. Defaults come from `DEFAULT_CONFIG_DATA` (`:451-502`). Each field is validated by the `require_*` helper named here (`:816-851`).

| Field | Type | Default | Validation |
|---|---|---|---|
| `schema_version` | str | `"3.0"` | non-empty str; never compared |
| `min_function_lines` | int | 5 | int ≥ 1 |
| `min_class_lines` | int | 6 | int ≥ 1 |
| `min_docstring_length` | int | 18 | int ≥ 1 |
| `max_cyclomatic_complexity` | int | 12 | int ≥ 1 |
| `max_report_evidence_lines` | int | 5 | int ≥ 1 |
| `include_patterns` | tuple[str, ...] | `("*.py",)` | list of non-empty str |
| `ignore_patterns` | tuple[str, ...] | `__pycache__/*`, `*.pyc`, `.git/*`, `.hg/*`, `.mypy_cache/*`, `.pytest_cache/*`, `.ruff_cache/*`, `.tox/*`, `.venv/*`, `venv/*`, `env/*`, `node_modules/*`, `.python_doctor/*`, `build/*`, `dist/*` | list of non-empty str |
| `ignore_functions` | tuple[str, ...] | `("__repr__","__str__")` | list |
| `ignore_classes` | tuple[str, ...] | `()` | list |
| `check_private_functions` | bool | False | bool |
| `check_nested_functions` | bool | True | bool |
| `require_module_docstring` | bool | True | bool |
| `require_class_docstring` | bool | True | bool |
| `require_function_docstring` | bool | True | bool |
| `require_parameter_hints` | bool | True | bool |
| `require_return_hints` | bool | True | bool |
| `detect_unused_imports` | bool | True | bool |
| `detect_test_gaps` | bool | True | bool; **never read** ([D-05](../DISCOVERY-LEDGER.md#d-05)) |
| `detect_security_risks` | bool | True | bool |
| `detect_silent_failures` | bool | True | bool |
| `detect_dependency_cycles` | bool | True | bool |
| `state_dir` | str | `".python_doctor"` | non-empty str |
| `reports_dir` | str | `"reports"` | non-empty str |
| `report_basename` | str | `"production_doctor_report"` | non-empty str |
| `severity_exit_level` | str | `"serious"` | one of critical, serious, minor, info, none |
| `max_workers` | int | 4 | int ≥ 1 |
| `markdown_include_css` | bool | True | bool |
| `severity_levels` | Mapping[str, Severity] | 20 categories (below) | dict whose values are lowercase severities; any key accepted |

Default `severity_levels` (`:480-501`):

- **critical:** `analysis_read_errors`, `syntax_errors`, `tokenization_errors`
- **serious:** `missing_imports`, `dependency_cycles`, `stubs`, `placeholder_returns`, `incomplete_methods`, `suspicious_short_classes`, `silent_failures`, `broad_exceptions`, `security_risks`, `test_gaps`
- **minor:** `todos`, `missing_docstrings`, `suspicious_short_functions`, `type_hint_gaps`, `complexity`, `unused_imports`, `duplicate_definitions`
- **info:** none by default. A category with no mapping falls back to `minor`.

[SOURCE-CONFIRMED] all rows. [VERIFIED] defaults load as `gate serious workers 4` in `/tmp/w1/ex_api.py`.

## Result types

This section lists the frozen dataclasses a scan returns, from the top-level result down to the per-issue record.

**`ProjectAnalysisResult`** (`:408-421`): `run_id: str`, `project_root: str` (absolute), `started_at: str`, `finished_at: str` (ISO with `Z`), `config_hash: str`, `summary: SummaryCounts`, `files: tuple[FileAnalysisResult, ...]`, `issues: tuple[DiagnosticIssue, ...]` (all files, sorted by file, line, category), `dependency_graph: DependencyGraphResult`, `state_delta: StateDelta`.

**`SummaryCounts`** (`:390-405`): `files_scanned`, `total_issues`, `critical_issues`, `serious_issues`, `minor_issues`, `info_issues`, `syntax_error_files` (files with `syntax_valid=False`, which includes unreadable files), `missing_imports` (edges), `dependency_cycles`, `suspicious_short_classes`, `suspicious_short_functions`, `production_score` (`max(0, 100 - 20c - 8s - 2m - i)`). All are `int`.

**`FileAnalysisResult`** (`:350-366`): `file_path` (absolute), `relative_path` (POSIX), `file_hash` (sha256, `""` if unreadable), `size_bytes`, `modified_time` (ISO, or `"unavailable"`), `syntax_valid: bool`, `metrics: FileMetrics`, `issues`, `imports: tuple[ImportRecord, ...]`, `import_edges: tuple[ImportEdge, ...]`, `functions: tuple[FunctionDiagnostic, ...]`, `classes: tuple[ClassDiagnostic, ...]`, `code_map: JsonObject` (keys `module`, `docstring_present`, `imports`, `classes`, `functions`; `{}` when the file did not parse).

**`DiagnosticIssue`** (`:243-264`): `category: str`, `severity: Severity`, `file_path: str` (relative), `line_number: int`, `column_offset: int`, `symbol: str`, `message: str`, `evidence: str` (numbered excerpt; `""` for read, cycle, and worker issues), `remediation: str`, `details: JsonObject`. Method `identity() -> str` joins category, severity, file, line, symbol, and message with `|`.

**`FileMetrics`** (`:331-347`): `total_lines`, `code_lines`, `comment_lines`, `blank_lines`, `total_classes`, `total_functions`, `total_methods`, `documented_symbols`, `fully_type_hinted_functions`, `import_count`, `local_dependency_count`, `missing_import_count`, `max_cyclomatic_complexity`.

**`FunctionDiagnostic`** (`:267-282`): `qualname`, `kind` (`function` or `async_function`), `line_number`, `end_line_number`, `executable_line_count`, `statement_count`, `cyclomatic_complexity`, `return_count`, `argument_count`, `missing_type_hints: tuple[str, ...]`, `has_docstring`, `decorators: tuple[str, ...]`.

**`ClassDiagnostic`** (`:285-300`): `qualname`, `line_number`, `end_line_number`, `executable_line_count`, `method_count`, `public_method_count`, `bases`, `decorators`, `has_docstring`, `is_dataclass` (decorator text ends with `dataclass`, so `dataclass(frozen=True)` is False, [D-07](../DISCOVERY-LEDGER.md#d-07)), `is_exception`, `is_enum`.

**`ImportRecord`** (`:303-314`): `module`, `imported_names`, `bound_names`, `line_number`, `column_offset`, `level`, `kind` (`import`, `from_import`, or `dynamic_import`), `raw`.

**`ImportEdge`** (`:317-328`): `source_file`, `imported_module`, `line_number`, `classification: ImportKind`, `status`, `target_file` (relative, or `""`), `confidence: float`, `raw`.

**`DependencyGraphResult`** (`:369-377`): `nodes: tuple[str, ...]`, `edges: tuple[ImportEdge, ...]` (all edges, not only local ones), `missing_imports`, `cycles: tuple[tuple[str, ...], ...]`, `mermaid: str`.

**`StateDelta`** (`:380-387`): `new_files`, `modified_files`, `deleted_files`, `unchanged_files`, each a sorted tuple of relative paths.

## State and path types

This section lists the types used by the state store.

**`ReportPaths`** (`:424-433`): `markdown_path`, `json_path`, `state_markdown_path`, `state_json_path`, `latest_markdown_path`, `latest_json_path`, all of type `Path`.

**`RunRecord`** (`:436-448`): `run_id`, `project_root`, `completed_at`, `status`, `files_scanned`, `total_issues`, `critical_issues`, `serious_issues`, `report_md`, `report_json`. It omits `minor_issues`, `info_issues`, and `config_hash`, even though the table stores them. The SQLite DDL is in [state-and-persistence](../01-system/state-and-persistence.md#sqlite-schema).

**`YamlLine`** (`:199-205`): `number`, `indent`, `content`. Internal to the parser.

## JSON report schema

This section gives the shape of `production_doctor_report.json`, which is `dumps_json(ProjectAnalysisResult)` with sorted keys.

```
{
  "config_hash": str,
  "dependency_graph": { "cycles": [[str]], "edges": [ImportEdge], "mermaid": str,
                        "missing_imports": [ImportEdge], "nodes": [str] },
  "files": [ { "classes": [ClassDiagnostic], "code_map": {...}, "file_hash": str, "file_path": str,
               "functions": [FunctionDiagnostic], "import_edges": [ImportEdge], "imports": [ImportRecord],
               "issues": [DiagnosticIssue], "metrics": FileMetrics, "modified_time": str,
               "relative_path": str, "size_bytes": int, "syntax_valid": bool } ],
  "finished_at": str,
  "issues": [ { "category", "column_offset", "details", "evidence", "file_path", "line_number",
                "message", "remediation", "severity", "symbol" } ],
  "project_root": str, "run_id": str, "started_at": str,
  "state_delta": { "deleted_files", "modified_files", "new_files", "unchanged_files" },
  "summary": SummaryCounts
}
```

[VERIFIED] key lists printed by `/tmp/w1/ex_api.py`: top-level, `issues[0]`, and `files[0]` keys match the shape above exactly. The JSON carries no schema version field, and `DoctorConfig.schema_version` is not included. Consumers detect the shape by its keys. Lane F's `delta.py` depends on this shape. [VERIFIED] [lane-f fieldkit](../_evidence/agent-findings/lane-f-ext/fieldkit.md).

Issues appear twice in the JSON: once in the top-level `issues` and once under each file's `issues`. [SOURCE-CONFIRMED] `src/somnus_debug/doctor/core.py:1712-1714`.

## Pycache and harness types

This section covers the non-doctor data types.

- `CleanerConfig`: see [public-api](public-api.md#pycache-cleaner). It is a mutable dataclass with no type validation.
- The template `run_test.py` defines these types:
  - `Check(name: str, passed: bool, detail: str = "", expected: Any = None, observed: Any = None)` (frozen)
  - `TestOutcome(summary: str, checks: list[Check], metrics: dict = {}, evidence: dict = {}, notes: list = [])`, whose `.passed` is true only when `checks` is non-empty and every check passed
  - `TestContext(run_id, project_root, artifact_dir, logger)` (frozen)
  - the manifest `SCHEMA_VERSION = "1.0"`

[SOURCE-CONFIRMED] `src/somnus_debug/test_harness/templates/run_test.py:144-183`, `:489`. Manifest fields: [lane-f harness](../_evidence/agent-findings/lane-f-ext/harness.md).

## Sources

This section lists the code, evidence files, and probes this page rests on.

- `src/somnus_debug/doctor/core.py:74-514`, `:1712-1714`
- `src/somnus_debug/pycache_cleaner/core.py:157-167`, `src/somnus_debug/test_harness/templates/run_test.py:144-195`, `:489`
- [lane-a api-reference.md](../_evidence/agent-findings/lane-a-arch-api/api-reference.md), [lane-f fieldkit.md](../_evidence/agent-findings/lane-f-ext/fieldkit.md), [lane-f harness.md](../_evidence/agent-findings/lane-f-ext/harness.md)
- Executed probe: `/tmp/w1/ex_api.py`
