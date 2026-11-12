# Classes

This page documents every class in the package that has behavior: what it does, how it is constructed, and its public methods. Pure data classes (frozen dataclasses) are listed here by name only. Their fields are in [types-and-schemas](types-and-schemas.md); the error classes are in [exceptions](exceptions.md). Signatures are from source at baseline `034f46e`.

## Configuration classes

This section covers the classes that load and validate doctor configuration.

### ConfigManager

`ConfigManager(config_path: Path | None)` lives at `src/somnus_debug/doctor/core.py:782-924`.

| Member | Kind | Behavior |
|---|---|---|
| `config_path` | attribute | the path given |
| `raw_config` | attribute | `deep_merge(DEFAULT_CONFIG_DATA, loaded)`, JSON-safe, unknown keys kept |
| `config` | attribute | validated `DoctorConfig` |
| `config_hash` | attribute | `sha256(dumps_json(raw_config))`; `ff1bdc11340bc602…` for the defaults [VERIFIED] |
| `severity(category)` | method | `config.severity_levels.get(category, Severity.MINOR)` |
| `_load_raw(path)` | private | `None` gives defaults, `.json` uses `json.loads`, `.yaml`/`.yml` uses `MinimalYamlParser`, anything else raises `ConfigurationError` |
| `_validate(data)` | private | the `require_*` helpers, plus a gate check against `{critical, serious, minor, info, none}` |
| `default_yaml()` | staticmethod | the YAML text `init-config` writes; parses to the same values as `DEFAULT_CONFIG_DATA` [VERIFIED] [lane-b §2.2](../_evidence/agent-findings/lane-b-config/configuration-findings.md) |

Unknown keys survive into `raw_config` and `config_hash` but are otherwise ignored. A typo therefore changes the hash and nothing else. [SOURCE-CONFIRMED] `:726-735`, `:816-851`; [VERIFIED] [D-04](../DISCOVERY-LEDGER.md#d-04).

### MinimalYamlParser

`MinimalYamlParser(path: Path)` lives at `src/somnus_debug/doctor/core.py:646-723`. Its `.parse() -> dict` reads UTF-8 and supports block mappings, block sequences of scalars, inline `[a, b]` lists, and scalars. It raises `ConfigurationError` with a line number on indentation errors, mixed containers, a missing child block, extra content, or a non-mapping root. Its full grammar and silent mis-parses are in [lane-b configuration-findings §3](../_evidence/agent-findings/lane-b-config/configuration-findings.md) and [D-04](../DISCOVERY-LEDGER.md#d-04).

[VERIFIED] `/tmp/w1/ex_misc.py`: `severity_exit_level: none` parses to `{'severity_exit_level': None}` ([D-03](../DISCOVERY-LEDGER.md#d-03)), and `schema_version: [` parses to the string `'['`, which validation accepts.

## Scan engine classes

This section covers the classes that discover files and produce findings. `ProjectScanner` is the one to call; the rest are its parts.

### ProjectScanner

`ProjectScanner(project_root: Path, config_manager: ConfigManager)` lives at `src/somnus_debug/doctor/core.py:1695-1774`.

| Member | Behavior |
|---|---|
| `project_root` | the resolved root |
| `index` | the `ProjectFileIndex`, built in `__init__` (tree walk happens here) |
| `scan(previous_index) -> ProjectAnalysisResult` | runs `_analyze_files`, then `DependencyGraphBuilder.build`, `_attach_cycles`, `_summary`, and `_state_delta` |
| `_analyze_files()` | uses a thread pool when `min(max_workers, n_files) > 1`, otherwise runs serially; see [async-and-concurrency](async-and-concurrency.md) |
| `_execution_error(path, error)` | builds the synthetic `analysis_read_errors` result for a worker failure |
| `_attach_cycles(files, graph)` | adds one `dependency_cycles` issue to the first file of each cycle |
| `_summary(...)` | builds `SummaryCounts`, with `production_score = max(0, 100 - 20c - 8s - 2m - i)` |
| `_state_delta(files, previous)` | compares current file hashes with the previous ones and returns new, modified, deleted, and unchanged files |

### ProjectFileIndex

`ProjectFileIndex(project_root: Path, config: DoctorConfig)` lives at `src/somnus_debug/doctor/core.py:926-992`.

| Member | Behavior |
|---|---|
| `python_files: tuple[Path, ...]` | resolved paths, sorted by relative path |
| `module_to_file`, `file_to_module` | maps between dotted module names and paths. `pkg/__init__.py` maps to `pkg`. A root-level `__init__.py` gets no entry |
| `should_ignore(path) -> bool` | `fnmatch` on the relative path or the basename; any `X/*` pattern also matches a directory named `X` at any depth ([D-17](../DISCOVERY-LEDGER.md#d-17)) |
| `should_include(path) -> bool` | `fnmatch` on the relative path or the basename |
| `module_for_file(path) -> str` | looks the file up, falling back to computing the dotted name |
| `resolve_local_module(name) -> Path \| None` | dictionary lookup |

Raises `AnalysisExecutionError` for a missing or non-directory root. [VERIFIED] `/tmp/w1/ex_tools.py`: "Project root does not exist."

### ImportResolver

`ImportResolver(index: ProjectFileIndex)` lives at `src/somnus_debug/doctor/core.py:995-1055`. Its `.resolve(source_path, record: ImportRecord) -> ImportEdge` returns a classification with a confidence:

| Classification | Confidence | Condition |
|---|---:|---|
| `unresolved_relative` | 0.2 | a relative import ascends above the root |
| `local` | 1.0 | exact module match, then from-import child, then parent prefix |
| `standard_library` | 0.95 | top-level name is in `sys.stdlib_module_names` or `sys.builtin_module_names` |
| `third_party` | 0.85 | `importlib.util.find_spec(top)` is not None in the running interpreter |
| `missing` | 0.9 | none of the above |

The exact-match-first rule makes `from pkg import ghost` resolve to `pkg/__init__.py`. [VERIFIED] `/tmp/w1/ex_api.py` edges: `('pkg', 'local', 'pkg/__init__.py')` twice for `from pkg import b` and `from . import missing_sibling`. [D-06](../DISCOVERY-LEDGER.md#d-06).

### FileAnalyzer

`FileAnalyzer(path: Path, index: ProjectFileIndex, config_manager: ConfigManager)` lives at `src/somnus_debug/doctor/core.py:1507-1615`. Its `.analyze() -> FileAnalysisResult` analyzes one file; the pipeline is in [call-chains](../07-internals/call-chains.md#per-file-analysis). It returns an `analysis_read_errors` result on a read failure, and a `syntax_valid=False` result with no AST checks on a syntax error. It can raise `FileReadError` if `stat` or hashing fails after the read (`:1590-1595`). [SOURCE-CONFIRMED]

### CodeQualityVisitor

`CodeQualityVisitor(config_manager: ConfigManager, issue_factory: DiagnosticIssueFactory)` subclasses `ast.NodeVisitor` and lives at `src/somnus_debug/doctor/core.py:1143-1358`. Its `.analyze(tree) -> (issues, functions, classes)` holds every AST detector. It is the only subclassing seam in the package, and that seam is unsupported; see [internal-interfaces](internal-interfaces.md#codequalityvisitor-subclass-and-rebind).

### Supporting classes

| Class | Location | Role |
|---|---|---|
| `SourceReader` | `src/somnus_debug/doctor/core.py:1058-1067` | `.read(path)` uses `tokenize.open`, which honors the encoding cookie; raises `FileReadError` |
| `DiagnosticIssueFactory` | `:1070-1090` | `.create(category, line, column, symbol, message, remediation, details=None) -> DiagnosticIssue`; looks up severity from config; evidence is ±`max_report_evidence_lines // 2` lines |
| `ImportCollector` | `:1093-1119` | `ast.NodeVisitor`; collects `import`, `from … import`, and literal `__import__("x")` / `importlib.import_module("x")` calls |
| `LoadedNameCollector` | `:1122-1140` | collects `ast.Name` loads. Attribute bases count, because `os.path` loads `os`. Strings in `__all__` do not count, which causes [D-07](../DISCOVERY-LEDGER.md#d-07) false positives |
| `DependencyGraphBuilder` | `:1618-1679` | `.build(files) -> DependencyGraphResult`; DFS over local edges with path length < 30, stopping after the start node that brings the total to ≥ 100 cycles |

## Output and state classes

This section covers rendering and persistence.

### MarkdownReportWriter

`MarkdownReportWriter(config: DoctorConfig)` lives at `src/somnus_debug/doctor/core.py:1776-1913`. Its `.render(result) -> str` emits, in order:

1. CSS, when `markdown_include_css` is set
2. a header
3. an HTML terminal block
4. Summary and Issue Categories
5. Local State Delta
6. Dependency Map (mermaid)
7. Suspiciously Short Classes and Functions
8. Full Issue Index
9. File Diagnostics
10. Recommended Action Plan

[VERIFIED] H2 list from `/tmp/w1/ex_api.py`. User-controlled text is escaped only for table pipes and newlines (`table_escape`) and Mermaid brackets (`mermaid_escape`). The project root in the HTML block goes through `html.escape`. [SOURCE-CONFIRMED]

### StateStore

`StateStore(project_root: Path, config: DoctorConfig)` lives at `src/somnus_debug/doctor/core.py:1916-2009`.

| Method | Returns | Creates state? | Raises |
|---|---|---|---|
| `initialize()` | None | yes (mkdir + DDL) | `StateStoreError` |
| `previous_file_index()` | `Mapping[str, str]` | yes | `StateStoreError` |
| `report_paths(run_id, output, json_output)` | `ReportPaths` | no | none |
| `persist(result, markdown, json_text, paths)` | None | yes | `ReportGenerationError` (files), `StateStoreError` (DB) |
| `history(limit)` | `tuple[RunRecord, ...]` newest first | yes | `StateStoreError` |
| `rollback(run_id)` | `RunRecord` | yes | `StateStoreError` (unknown run, missing artifacts, copy or DB failure) |

Schema and semantics: [state-and-persistence](../01-system/state-and-persistence.md). [VERIFIED] `/tmp/w1/ex_state.py` exercised every method.

## Pycache and harness classes

This section points to the classes outside the doctor.

- `CleanerConfig` and `PycacheCleaner`: [public-api](public-api.md#pycache-cleaner). Private helpers: `_scan_root`, `_is_excluded`, `_match_file`, `_delete_directory`, `_delete_file`, and `_get_dir_size` (staticmethod) at `src/somnus_debug/pycache_cleaner/core.py:220-321`.
- Template classes `Check`, `TestOutcome` (with property `passed`), and `TestContext` live in `src/somnus_debug/test_harness/templates/run_test.py:144-183`. They are copied into a project, never imported. [SOURCE-CONFIRMED]

## Sources

This section lists the code, evidence files, and probes this page rests on.

- `src/somnus_debug/doctor/core.py:646-2009`; `src/somnus_debug/pycache_cleaner/core.py:157-321`; `src/somnus_debug/test_harness/templates/run_test.py:144-183`
- [lane-a api-reference.md](../_evidence/agent-findings/lane-a-arch-api/api-reference.md), [lane-a symbols.tsv](../_evidence/agent-findings/lane-a-arch-api/symbols.tsv), [lane-b configuration-findings.md](../_evidence/agent-findings/lane-b-config/configuration-findings.md)
- Executed probes: `/tmp/w1/ex_api.py`, `/tmp/w1/ex_misc.py`, `/tmp/w1/ex_state.py`, `/tmp/w1/ex_tools.py`
