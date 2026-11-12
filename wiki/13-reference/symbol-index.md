# Symbol index

This page lists every symbol defined in `src/somnus_debug/`, grouped by module and ordered by line number. It is the complete inventory; [04-library-api/api-index](../04-library-api/api-index.md) is the shorter, linked alphabetical view, and [04-library-api/public-api](../04-library-api/public-api.md) says which names are meant for callers.

## How this index was produced

This section states the source and limits of the table so readers know how far to trust it.

The rows are generated from [lane-a symbols.tsv](../_evidence/agent-findings/lane-a-arch-api/symbols.tsv) (256 symbols). That file was itself produced by an AST walk over `src/` ([ast_enum.py.txt](../_evidence/agent-findings/lane-a-arch-api/ast_enum.py.txt)). [VERIFIED] Spot checks against source at baseline `034f46e`:

- `ConfigManager` at `src/somnus_debug/doctor/core.py:782`
- `exit_code_for_summary` at `:2046`
- `build_index` at `src/somnus_debug/structure/core.py:202`
- `scaffold` at `src/somnus_debug/test_harness/scaffold.py:62`

Signatures are as rendered by `ast.unparse`, so defaults print as `=None` without spaces, and long values are truncated at 150 characters with `…`. The Exported column is `yes` only for names reachable through a package `__all__`. Instance attributes are not symbols and are not listed; see [04-library-api/classes](../04-library-api/classes.md).

Kinds: class 21, constant 15, dataclass 19, dunder 5, enum 1, function 77, method 105, module_var 4, nested_function 1, property 1, reexport 4, staticmethod 3. The template module `test_harness/templates/run_test.py` is data copied by `scaffold`, not imported code.

## Modules

This section links to each module's table.

- [`src/somnus_debug/__init__.py`](#srcsomnus_debug__init__py) (2 symbols)
- [`src/somnus_debug/cli.py`](#srcsomnus_debugclipy) (4 symbols)
- [`src/somnus_debug/doctor/__init__.py`](#srcsomnus_debugdoctor__init__py) (2 symbols)
- [`src/somnus_debug/doctor/core.py`](#srcsomnus_debugdoctorcorepy) (192 symbols)
- [`src/somnus_debug/pycache_cleaner/__init__.py`](#srcsomnus_debugpycache_cleaner__init__py) (2 symbols)
- [`src/somnus_debug/pycache_cleaner/core.py`](#srcsomnus_debugpycache_cleanercorepy) (15 symbols)
- [`src/somnus_debug/structure/__init__.py`](#srcsomnus_debugstructure__init__py) (3 symbols)
- [`src/somnus_debug/structure/core.py`](#srcsomnus_debugstructurecorepy) (14 symbols)
- [`src/somnus_debug/test_harness/scaffold.py`](#srcsomnus_debugtest_harnessscaffoldpy) (5 symbols)
- [`src/somnus_debug/test_harness/templates/run_test.py`](#srcsomnus_debugtest_harnesstemplatesrun_testpy) (17 symbols)

## src/somnus_debug/__init__.py

This section lists the 2 symbols defined in `src/somnus_debug/__init__.py`.

| Line | Kind | Name | Signature | Exported | Notes |
|---:|---|---|---|---|---|
| 57 | dunder | `__version__` | `__version__ = '0.1.0'` | yes | end=57 |
| 59 | dunder | `__all__` | `__all__ = ['__version__']` | no | end=59 |

## src/somnus_debug/cli.py

This section lists the 4 symbols defined in `src/somnus_debug/cli.py`.

| Line | Kind | Name | Signature | Exported | Notes |
|---:|---|---|---|---|---|
| 60 | constant | `_SUBCOMMANDS` | `_SUBCOMMANDS = {'doctor': ('somnus-debug doctor', _doctor_main), 'structure': ('somnus-debug st` | no | end=65 |
| 67 | constant | `_TOP_LEVEL_HELP` | `_TOP_LEVEL_HELP = f'somnus-debug {__version__} -- Somnus Sovereign Systems Python developer toolki` | no | end=82 |
| 85 | function | `_run_subcommand` | `def _run_subcommand(name: str, argv: Sequence[str]) -> int` | no | end=104; Rewrite sys.argv for the target tool's own argparse and invoke it. |
| 107 | function | `main` | `def main(argv: Sequence[str] \| None=None) -> int` | no | console script somnus-debug; end=124; Entry point for the ``somnus-debug`` console script. |

## src/somnus_debug/doctor/__init__.py

This section lists the 2 symbols defined in `src/somnus_debug/doctor/__init__.py`.

| Line | Kind | Name | Signature | Exported | Notes |
|---:|---|---|---|---|---|
| 43 | reexport | `main` | `from .core import main` | yes | re-exported via __all__ |
| 45 | dunder | `__all__` | `__all__ = ['main']` | no | end=45 |

## src/somnus_debug/doctor/core.py

This section lists the 192 symbols defined in `src/somnus_debug/doctor/core.py`.

| Line | Kind | Name | Signature | Exported | Notes |
|---:|---|---|---|---|---|
| 74 | module_var | `JsonScalar` | `JsonScalar = str \| int \| float \| bool \| None` | no | end=74 |
| 75 | module_var | `JsonValue` | `JsonValue = JsonScalar \| list['JsonValue'] \| dict[str, 'JsonValue']` | no | end=75 |
| 76 | module_var | `JsonObject` | `JsonObject = dict[str, JsonValue]` | no | end=76 |
| 77 | module_var | `ImportKind` | `ImportKind = Literal['local', 'standard_library', 'third_party', 'missing', 'unresolved_relat` | no | end=77 |
| 79 | constant | `UTC` | `UTC = dt.timezone.utc` | no | end=79 |
| 80 | constant | `LOGGER_NAME` | `LOGGER_NAME = 'python_production_doctor'` | no | end=80 |
| 81 | constant | `DEFAULT_CONFIG_NAME` | `DEFAULT_CONFIG_NAME = 'python_doctor.yaml'` | no | end=81 |
| 82 | constant | `RUN_ID_FORMAT` | `RUN_ID_FORMAT = '%Y%m%dT%H%M%SZ'` | no | end=82 |
| 83 | constant | `COMMANDS` | `COMMANDS = {'scan', 'init-config', 'history', 'rollback', 'self-check'}` | no | end=83 |
| 86 | enum | `Severity` | `class Severity(str, Enum)` | no | end=92; fields[CRITICAL='critical'; SERIOUS='serious'; MINOR='minor'; INFO='info']; Severity values used by issue gates and report sorting. |
| 95 | class | `DoctorError` | `class DoctorError(RuntimeError)` | no | end=120; Base domain error with user-facing remediation and JSON-safe context. |
| 100 | method | `DoctorError.__init__` | `def __init__(self, message: str, remediation: str \| None=None, context: JsonObject \| None=None) -> None` | no | end=111; Initialize a domain error. |
| 113 | method | `DoctorError.render` | `def render(self) -> str` | no | end=120; Render a deterministic error block. |
| 123 | class | `ConfigurationError` | `class ConfigurationError(DoctorError)` | no | end=135; Raised when YAML, JSON, or typed configuration validation fails. |
| 128 | method | `ConfigurationError.__init__` | `def __init__(self, message: str, context: JsonObject \| None=None) -> None` | no | end=135; Initialize a configuration error. |
| 138 | class | `FileReadError` | `class FileReadError(DoctorError)` | no | end=150; Raised when a source file cannot be read, decoded, or hashed. |
| 143 | method | `FileReadError.__init__` | `def __init__(self, message: str, context: JsonObject \| None=None) -> None` | no | end=150; Initialize a file read error. |
| 153 | class | `ReportGenerationError` | `class ReportGenerationError(DoctorError)` | no | end=165; Raised when markdown, JSON, or state report artifacts cannot be written. |
| 158 | method | `ReportGenerationError.__init__` | `def __init__(self, message: str, context: JsonObject \| None=None) -> None` | no | end=165; Initialize a report generation error. |
| 168 | class | `StateStoreError` | `class StateStoreError(DoctorError)` | no | end=180; Raised when local report-state persistence cannot complete. |
| 173 | method | `StateStoreError.__init__` | `def __init__(self, message: str, context: JsonObject \| None=None) -> None` | no | end=180; Initialize a state store error. |
| 183 | class | `AnalysisExecutionError` | `class AnalysisExecutionError(DoctorError)` | no | end=195; Raised when project-level analysis cannot proceed. |
| 188 | method | `AnalysisExecutionError.__init__` | `def __init__(self, message: str, context: JsonObject \| None=None) -> None` | no | end=195; Initialize an analysis execution error. |
| 199 | dataclass | `YamlLine` | `class YamlLine()` | no | decorators=dataclass(frozen=True); end=204; fields[number:int; indent:int; content:str]; One prepared YAML line with indentation metadata. |
| 208 | dataclass | `DoctorConfig` | `class DoctorConfig()` | no | named in README/MANUAL library section; decorators=dataclass(frozen=True); end=239; fields[schema_version:str; min_function_lines:int; min_c… |
| 243 | dataclass | `DiagnosticIssue` | `class DiagnosticIssue()` | no | decorators=dataclass(frozen=True); end=263; fields[category:str; severity:Severity; file_path:str; line_number:int; column_offset:int; symbo… |
| 257 | method | `DiagnosticIssue.identity` | `def identity(self) -> str` | no | end=263; Return a stable identity string for de-duplication. |
| 267 | dataclass | `FunctionDiagnostic` | `class FunctionDiagnostic()` | no | decorators=dataclass(frozen=True); end=281; fields[qualname:str; kind:str; line_number:int; end_line_number:int; executable_line_count:int; … |
| 285 | dataclass | `ClassDiagnostic` | `class ClassDiagnostic()` | no | decorators=dataclass(frozen=True); end=299; fields[qualname:str; line_number:int; end_line_number:int; executable_line_count:int; method_cou… |
| 303 | dataclass | `ImportRecord` | `class ImportRecord()` | no | decorators=dataclass(frozen=True); end=313; fields[module:str; imported_names:tuple[str, ...]; bound_names:tuple[str, ...]; line_number:int;… |
| 317 | dataclass | `ImportEdge` | `class ImportEdge()` | no | decorators=dataclass(frozen=True); end=327; fields[source_file:str; imported_module:str; line_number:int; classification:ImportKind; status:… |
| 331 | dataclass | `FileMetrics` | `class FileMetrics()` | no | decorators=dataclass(frozen=True); end=346; fields[total_lines:int; code_lines:int; comment_lines:int; blank_lines:int; total_classes:int; t… |
| 350 | dataclass | `FileAnalysisResult` | `class FileAnalysisResult()` | no | decorators=dataclass(frozen=True); end=365; fields[file_path:str; relative_path:str; file_hash:str; size_bytes:int; modified_time:str; synta… |
| 369 | dataclass | `DependencyGraphResult` | `class DependencyGraphResult()` | no | decorators=dataclass(frozen=True); end=376; fields[nodes:tuple[str, ...]; edges:tuple[ImportEdge, ...]; missing_imports:tuple[ImportEdge, ..… |
| 380 | dataclass | `StateDelta` | `class StateDelta()` | no | decorators=dataclass(frozen=True); end=386; fields[new_files:tuple[str, ...]; modified_files:tuple[str, ...]; deleted_files:tuple[str, ...];… |
| 390 | dataclass | `SummaryCounts` | `class SummaryCounts()` | no | decorators=dataclass(frozen=True); end=404; fields[files_scanned:int; total_issues:int; critical_issues:int; serious_issues:int; minor_issue… |
| 408 | dataclass | `ProjectAnalysisResult` | `class ProjectAnalysisResult()` | no | decorators=dataclass(frozen=True); end=420; fields[run_id:str; project_root:str; started_at:str; finished_at:str; config_hash:str; summary:S… |
| 424 | dataclass | `ReportPaths` | `class ReportPaths()` | no | decorators=dataclass(frozen=True); end=432; fields[markdown_path:Path; json_path:Path; state_markdown_path:Path; state_json_path:Path; lates… |
| 436 | dataclass | `RunRecord` | `class RunRecord()` | no | decorators=dataclass(frozen=True); end=448; fields[run_id:str; project_root:str; completed_at:str; status:str; files_scanned:int; total_issu… |
| 451 | constant | `DEFAULT_CONFIG_DATA` | `DEFAULT_CONFIG_DATA = {'schema_version': '3.0', 'min_function_lines': 5, 'min_class_lines': 6, 'min_do` | no | end=502 |
| 504 | constant | `TODO_PATTERNS` | `TODO_PATTERNS = (('\\bTODO\\b', 'Action Required'), ('\\bFIXME\\b', 'Critical Fix Needed'), ('\\` | no | end=511 |
| 513 | constant | `PLACEHOLDER_CONSTANTS` | `PLACEHOLDER_CONSTANTS = (None, False, True, 0, -1, '')` | no | end=513 |
| 514 | constant | `SECURITY_CALLS` | `SECURITY_CALLS = frozenset({'eval', 'exec', 'compile', 'pickle.load', 'pickle.loads', 'subprocess` | no | end=514 |
| 516 | constant | `SOMNUS_MARKDOWN_STYLE` | `SOMNUS_MARKDOWN_STYLE = '<style>\n.t{background:#141414;border-radius:10px;box-shadow:0 12px 40px rgba(0` | no | end=522 |
| 525 | function | `utc_now` | `def utc_now() -> dt.datetime` | no | end=527; Return a timezone-aware UTC timestamp. |
| 530 | function | `utc_now_text` | `def utc_now_text() -> str` | no | end=532; Return a compact UTC timestamp for run identifiers. |
| 535 | function | `isoformat_utc` | `def isoformat_utc(value: dt.datetime) -> str` | no | end=539; Render a datetime with stable UTC suffix. |
| 542 | function | `stable_hash_text` | `def stable_hash_text(text: str) -> str` | no | end=544; Return SHA-256 hex digest for text. |
| 547 | function | `stable_hash_file` | `def stable_hash_file(path: Path) -> str` | no | end=556; Return SHA-256 hex digest for a file. |
| 559 | function | `to_json_value` | `def to_json_value(value: object) -> JsonValue` | no | end=575; Convert dataclasses, paths, enums, mappings, sequences, and scalars to JSON-safe values. |
| 578 | function | `dumps_json` | `def dumps_json(value: object, *, indent: int=2) -> str` | no | end=580; Serialize a supported object to deterministic JSON. |
| 583 | function | `safe_relpath` | `def safe_relpath(path: Path, root: Path) -> str` | no | end=588; Return a POSIX relative path when possible. |
| 591 | function | `table_escape` | `def table_escape(value: object) -> str` | no | end=593; Escape a value for markdown tables. |
| 596 | function | `strip_yaml_comment` | `def strip_yaml_comment(line: str) -> str` | no | end=616; Remove YAML comments outside quoted strings. |
| 619 | function | `parse_yaml_scalar` | `def parse_yaml_scalar(value: str, line_number: int) -> JsonValue` | no | end=643; Parse one scalar or inline sequence from the native YAML subset. |
| 646 | class | `MinimalYamlParser` | `class MinimalYamlParser()` | no | end=723; Strict native parser for the YAML subset used by doctor configs. |
| 649 | method | `MinimalYamlParser.__init__` | `def __init__(self, path: Path) -> None` | no | end=651; Initialize parser for a config path. |
| 653 | method | `MinimalYamlParser.parse` | `def parse(self) -> JsonObject` | no | end=668; Parse YAML file and return a JSON-safe mapping. |
| 670 | method | `MinimalYamlParser._prepare_lines` | `def _prepare_lines(self, raw_lines: Sequence[str]) -> list[YamlLine]` | no | end=679; Prepare non-empty YAML lines. |
| 681 | method | `MinimalYamlParser._parse_block` | `def _parse_block(self, lines: Sequence[YamlLine], index: int, indent: int) -> tuple[JsonValue, int]` | no | end=716; Parse a mapping or sequence block. |
| 718 | method | `MinimalYamlParser._parse_child` | `def _parse_child(self, lines: Sequence[YamlLine], index: int, indent: int, line_number: int) -> tuple[JsonValue, int]` | no | end=723; Parse an indented child block. |
| 726 | function | `deep_merge` | `def deep_merge(base: JsonObject, override: JsonObject) -> JsonObject` | no | end=734; Merge config mappings recursively without mutating inputs. |
| 737 | function | `require_bool` | `def require_bool(data: Mapping[str, JsonValue], key: str) -> bool` | no | end=742; Read a required boolean config value. |
| 745 | function | `require_int` | `def require_int(data: Mapping[str, JsonValue], key: str, minimum: int) -> int` | no | end=750; Read a required integer config value with lower bound. |
| 753 | function | `require_str` | `def require_str(data: Mapping[str, JsonValue], key: str) -> str` | no | end=758; Read a required non-empty string config value. |
| 761 | function | `require_str_tuple` | `def require_str_tuple(data: Mapping[str, JsonValue], key: str) -> tuple[str, ...]` | no | end=766; Read a required list of strings config value. |
| 769 | function | `parse_severities` | `def parse_severities(raw: JsonValue) -> Mapping[str, Severity]` | no | end=779; Parse severity mapping from raw config. |
| 782 | class | `ConfigManager` | `class ConfigManager()` | no | named in README/MANUAL library section; end=923; Loads, validates, and exposes YAML-first configuration. |
| 785 | method | `ConfigManager.__init__` | `def __init__(self, config_path: Path \| None) -> None` | no | end=790; Load configuration from YAML, JSON, or defaults. |
| 792 | method | `ConfigManager.severity` | `def severity(self, category: str) -> Severity` | no | end=794; Return configured severity for a category. |
| 796 | method | `ConfigManager._load_raw` | `def _load_raw(self, config_path: Path \| None) -> JsonObject` | no | end=814; Load raw merged configuration. |
| 816 | method | `ConfigManager._validate` | `def _validate(self, data: JsonObject) -> DoctorConfig` | no | end=851; Validate raw mapping into DoctorConfig. |
| 854 | staticmethod | `ConfigManager.default_yaml` | `def default_yaml() -> str` | no | decorators=staticmethod; end=923; Return the default YAML configuration text. |
| 926 | class | `ProjectFileIndex` | `class ProjectFileIndex()` | no | end=992; Indexes Python files and importable module names for a project. |
| 929 | method | `ProjectFileIndex.__init__` | `def __init__(self, project_root: Path, config: DoctorConfig) -> None` | no | end=935; Initialize project index from a root and config. |
| 937 | method | `ProjectFileIndex.should_ignore` | `def should_ignore(self, path: Path) -> bool` | no | end=947; Return true when path matches ignore configuration. |
| 949 | method | `ProjectFileIndex.should_include` | `def should_include(self, path: Path) -> bool` | no | end=952; Return true when path matches include configuration. |
| 954 | method | `ProjectFileIndex.module_for_file` | `def module_for_file(self, path: Path) -> str` | no | end=961; Return best importable module name for a file. |
| 963 | method | `ProjectFileIndex.resolve_local_module` | `def resolve_local_module(self, module_name: str) -> Path \| None` | no | end=965; Resolve an importable module name to a local file. |
| 967 | method | `ProjectFileIndex._discover` | `def _discover(self) -> tuple[Path, ...]` | no | end=982; Discover Python files under project root. |
| 984 | method | `ProjectFileIndex._modules` | `def _modules(self, python_files: Sequence[Path]) -> dict[str, Path]` | no | end=992; Build module-name to file-path mapping. |
| 995 | class | `ImportResolver` | `class ImportResolver()` | no | end=1055; Resolves import records as local, standard library, third-party, or missing. |
| 998 | method | `ImportResolver.__init__` | `def __init__(self, index: ProjectFileIndex) -> None` | no | end=1001; Initialize resolver with project index. |
| 1003 | method | `ImportResolver.resolve` | `def resolve(self, source_path: Path, record: ImportRecord) -> ImportEdge` | no | end=1016; Resolve one import record into an ImportEdge. |
| 1018 | method | `ImportResolver._absolute_module` | `def _absolute_module(self, source_path: Path, record: ImportRecord) -> str` | no | end=1030; Convert relative import records to absolute module names. |
| 1032 | method | `ImportResolver._resolve_local` | `def _resolve_local(self, module_name: str, record: ImportRecord) -> Path \| None` | no | end=1048; Resolve exact module or from-import child module locally. |
| 1050 | method | `ImportResolver._third_party_exists` | `def _third_party_exists(self, top_level: str) -> bool` | no | end=1055; Return true when an import exists in active environment. |
| 1058 | class | `SourceReader` | `class SourceReader()` | no | end=1067; Reads Python source with declared encoding support. |
| 1061 | method | `SourceReader.read` | `def read(self, path: Path) -> str` | no | end=1067; Read Python source text. |
| 1070 | class | `DiagnosticIssueFactory` | `class DiagnosticIssueFactory()` | no | end=1090; Creates normalized issues with bounded source evidence. |
| 1073 | method | `DiagnosticIssueFactory.__init__` | `def __init__(self, config_manager: ConfigManager, relative_path: str, lines: Sequence[str]) -> None` | no | end=1077; Initialize factory for a file. |
| 1079 | method | `DiagnosticIssueFactory.create` | `def create(self, category: str, line: int, column: int, symbol: str, message: str, remediation: str, details: JsonObject \| None=None) -> DiagnosticIs…` | no | end=1081; Create a normalized diagnostic issue. |
| 1083 | method | `DiagnosticIssueFactory._evidence` | `def _evidence(self, line: int) -> str` | no | end=1090; Extract bounded evidence around line. |
| 1093 | class | `ImportCollector` | `class ImportCollector(ast.NodeVisitor)` | no | end=1119; Collects static and literal dynamic import records. |
| 1096 | method | `ImportCollector.__init__` | `def __init__(self) -> None` | no | end=1098; Initialize import collection. |
| 1100 | method | `ImportCollector.visit_Import` | `def visit_Import(self, node: ast.Import) -> None` | no | end=1104; Collect import statement records. |
| 1106 | method | `ImportCollector.visit_ImportFrom` | `def visit_ImportFrom(self, node: ast.ImportFrom) -> None` | no | end=1110; Collect from-import statement records. |
| 1112 | method | `ImportCollector.visit_Call` | `def visit_Call(self, node: ast.Call) -> None` | no | end=1119; Collect literal dynamic import calls. |
| 1122 | class | `LoadedNameCollector` | `class LoadedNameCollector(ast.NodeVisitor)` | no | end=1140; Collects loaded names while skipping import binding sites. |
| 1125 | method | `LoadedNameCollector.__init__` | `def __init__(self) -> None` | no | end=1127; Initialize loaded-name collection. |
| 1129 | method | `LoadedNameCollector.visit_Import` | `def visit_Import(self, node: ast.Import) -> None` | no | end=1131; Skip import binding site. |
| 1133 | method | `LoadedNameCollector.visit_ImportFrom` | `def visit_ImportFrom(self, node: ast.ImportFrom) -> None` | no | end=1135; Skip from-import binding site. |
| 1137 | method | `LoadedNameCollector.visit_Name` | `def visit_Name(self, node: ast.Name) -> None` | no | end=1140; Collect loaded name. |
| 1143 | class | `CodeQualityVisitor` | `class CodeQualityVisitor(ast.NodeVisitor)` | no | end=1358; Performs AST quality, completeness, typing, and safety analysis. |
| 1146 | method | `CodeQualityVisitor.__init__` | `def __init__(self, config_manager: ConfigManager, issue_factory: DiagnosticIssueFactory) -> None` | no | end=1158; Initialize AST visitor for one file. |
| 1160 | method | `CodeQualityVisitor.analyze` | `def analyze(self, tree: ast.AST) -> tuple[tuple[DiagnosticIssue, ...], tuple[FunctionDiagnostic, ...], tuple[ClassDiagnostic, ...]]` | no | end=1165; Analyze tree and return issues, functions, and classes. |
| 1167 | method | `CodeQualityVisitor.visit_Module` | `def visit_Module(self, node: ast.Module) -> None` | no | end=1172; Analyze module-level docs and definitions. |
| 1174 | method | `CodeQualityVisitor.visit_ClassDef` | `def visit_ClassDef(self, node: ast.ClassDef) -> None` | no | end=1205; Analyze class definitions. |
| 1207 | method | `CodeQualityVisitor.visit_FunctionDef` | `def visit_FunctionDef(self, node: ast.FunctionDef) -> None` | no | end=1209; Analyze synchronous functions. |
| 1211 | method | `CodeQualityVisitor.visit_AsyncFunctionDef` | `def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None` | no | end=1213; Analyze asynchronous functions. |
| 1215 | method | `CodeQualityVisitor.visit_ExceptHandler` | `def visit_ExceptHandler(self, node: ast.ExceptHandler) -> None` | no | end=1224; Analyze exception handlers. |
| 1226 | method | `CodeQualityVisitor.visit_Call` | `def visit_Call(self, node: ast.Call) -> None` | no | end=1231; Analyze high-risk calls. |
| 1233 | method | `CodeQualityVisitor._visit_function` | `def _visit_function(self, node: ast.FunctionDef \| ast.AsyncFunctionDef, kind: str) -> None` | no | end=1267; Analyze one function-like node. |
| 1269 | method | `CodeQualityVisitor._analyze_class` | `def _analyze_class(self, node: ast.ClassDef, info: ClassDiagnostic) -> None` | no | end=1279; Emit class diagnostics. |
| 1281 | method | `CodeQualityVisitor._analyze_function` | `def _analyze_function(self, node: ast.FunctionDef \| ast.AsyncFunctionDef, info: FunctionDiagnostic, body: Sequence[ast.stmt]) -> None` | no | end=1295; Emit function diagnostics. |
| 1297 | method | `CodeQualityVisitor._short_class` | `def _short_class(self, info: ClassDiagnostic, body: Sequence[ast.stmt]) -> bool` | no | end=1307; Return true when a class deserves suspicious-short review. |
| 1309 | method | `CodeQualityVisitor._record_definitions` | `def _record_definitions(self, statements: Sequence[ast.stmt]) -> None` | no | end=1313; Record function and class definitions in current scope. |
| 1315 | method | `CodeQualityVisitor._check_duplicates` | `def _check_duplicates(self) -> None` | no | end=1322; Emit duplicate definition issues for current scope. |
| 1324 | method | `CodeQualityVisitor._check_abstracts` | `def _check_abstracts(self) -> None` | no | end=1336; Check same-file subclasses against same-file abstract contracts. |
| 1338 | method | `CodeQualityVisitor._abstract_methods` | `def _abstract_methods(self, node: ast.ClassDef) -> set[str]` | no | end=1346; Return abstract method names in a class. |
| 1348 | method | `CodeQualityVisitor._qualname` | `def _qualname(self, name: str) -> str` | no | end=1350; Build qualified name from current scope. |
| 1352 | method | `CodeQualityVisitor._current_symbol` | `def _current_symbol(self) -> str` | no | end=1354; Return current scope symbol. |
| 1356 | method | `CodeQualityVisitor._inside_function` | `def _inside_function(self) -> bool` | no | end=1358; Return whether current scope is inside a function. |
| 1361 | function | `dedupe_issues` | `def dedupe_issues(issues: Iterable[DiagnosticIssue]) -> list[DiagnosticIssue]` | no | end=1371; Remove duplicate issues while preserving diagnostic order. |
| 1374 | function | `meaningful_doc` | `def meaningful_doc(node: ast.AST, min_length: int) -> bool` | no | end=1376; Return true when node has a docstring at configured minimum length. |
| 1379 | function | `body_without_docstring` | `def body_without_docstring(body: Sequence[ast.stmt]) -> tuple[ast.stmt, ...]` | no | end=1383; Return body with leading docstring removed. |
| 1386 | function | `executable_line_count` | `def executable_line_count(body: Sequence[ast.stmt]) -> int` | no | end=1394; Count unique executable lines in a body. |
| 1397 | function | `function_argument_count` | `def function_argument_count(node: ast.FunctionDef \| ast.AsyncFunctionDef) -> int` | no | end=1399; Count all explicit function arguments. |
| 1402 | function | `is_private_function` | `def is_private_function(name: str) -> bool` | no | end=1404; Return true for private but non-dunder function names. |
| 1407 | function | `missing_type_hints` | `def missing_type_hints(node: ast.FunctionDef \| ast.AsyncFunctionDef, config: DoctorConfig) -> tuple[str, ...]` | no | end=1420; Return missing type-hint labels for a function. |
| 1423 | function | `cyclomatic_complexity` | `def cyclomatic_complexity(node: ast.AST) -> int` | no | end=1433; Calculate conservative cyclomatic complexity. |
| 1436 | function | `body_is_stub` | `def body_is_stub(body: Sequence[ast.stmt]) -> bool` | no | end=1448; Return true when body is a direct stub. |
| 1451 | function | `placeholder_return_kind` | `def placeholder_return_kind(body: Sequence[ast.stmt]) -> str` | no | end=1468; Return placeholder kind when a body only returns a trivial value. |
| 1471 | function | `handler_is_silent` | `def handler_is_silent(node: ast.ExceptHandler) -> bool` | no | end=1487; Return true when an exception handler suppresses diagnostics. |
| 1490 | function | `dotted_name` | `def dotted_name(node: ast.AST \| None) -> str` | no | end=1504; Return dotted name for Name and Attribute nodes. |
| 1507 | class | `FileAnalyzer` | `class FileAnalyzer()` | no | end=1615; Analyzes one Python file for syntax, AST, imports, and diagnostics. |
| 1510 | method | `FileAnalyzer.__init__` | `def __init__(self, path: Path, index: ProjectFileIndex, config_manager: ConfigManager) -> None` | no | end=1518; Initialize analyzer for one file. |
| 1520 | method | `FileAnalyzer.analyze` | `def analyze(self) -> FileAnalysisResult` | no | end=1546; Run file analysis and return a complete result. |
| 1548 | method | `FileAnalyzer._token_diagnostics` | `def _token_diagnostics(self, source: str, factory: DiagnosticIssueFactory) -> list[DiagnosticIssue]` | no | end=1564; Run token-level diagnostics including technical debt comments. |
| 1566 | method | `FileAnalyzer._import_diagnostics` | `def _import_diagnostics(self, edges: Sequence[ImportEdge], tree: ast.AST, imports: Sequence[ImportRecord], factory: DiagnosticIssueFactory) -> list[Di…` | no | end=1581; Run import resolution and unused import diagnostics. |
| 1583 | method | `FileAnalyzer._read_error` | `def _read_error(self, error: FileReadError) -> FileAnalysisResult` | no | end=1586; Build result for unreadable file. |
| 1588 | method | `FileAnalyzer._assemble` | `def _assemble(self, source: str, lines: Sequence[str], syntax_valid: bool, issues: Sequence[DiagnosticIssue], imports: Sequence[ImportRecord], edges: …` | no | end=1595; Assemble result from analyzed parts. |
| 1597 | method | `FileAnalyzer._metrics` | `def _metrics(self, lines: Sequence[str], imports: Sequence[ImportRecord], edges: Sequence[ImportEdge], functions: Sequence[FunctionDiagnostic], classe…` | no | end=1615; Calculate file metrics. |
| 1618 | class | `DependencyGraphBuilder` | `class DependencyGraphBuilder()` | no | end=1679; Builds local import graph, cycles, and Mermaid diagram. |
| 1621 | method | `DependencyGraphBuilder.__init__` | `def __init__(self, config: DoctorConfig) -> None` | no | end=1623; Initialize graph builder. |
| 1625 | method | `DependencyGraphBuilder.build` | `def build(self, files: Sequence[FileAnalysisResult]) -> DependencyGraphResult` | no | end=1632; Build dependency graph result. |
| 1634 | method | `DependencyGraphBuilder._cycles` | `def _cycles(self, nodes: Sequence[str], edges: Sequence[ImportEdge]) -> tuple[tuple[str, ...], ...]` | no | end=1644; Detect directed cycles. |
| 1646 | method | `DependencyGraphBuilder._visit` | `def _visit(self, start: str, current: str, graph: Mapping[str, set[str]], path: list[str], visiting: set[str], cycles: set[tuple[str, ...]]) -> None` | no | end=1656; Traverse graph for cycles. |
| 1658 | method | `DependencyGraphBuilder._mermaid` | `def _mermaid(self, nodes: Sequence[str], edges: Sequence[ImportEdge], missing: Sequence[ImportEdge], cycles: Sequence[tuple[str, ...]]) -> str` | no | end=1679; Render Mermaid dependency graph. |
| 1682 | function | `canonical_cycle` | `def canonical_cycle(cycle: Sequence[str]) -> tuple[str, ...]` | no | end=1687; Return canonical representation of a cycle. |
| 1690 | function | `mermaid_escape` | `def mermaid_escape(value: str) -> str` | no | end=1692; Escape Mermaid label text. |
| 1695 | class | `ProjectScanner` | `class ProjectScanner()` | no | named in README/MANUAL library section; end=1773; Coordinates project scan, graph generation, state delta, and summary. |
| 1698 | method | `ProjectScanner.__init__` | `def __init__(self, project_root: Path, config_manager: ConfigManager) -> None` | no | end=1703; Initialize project scanner. |
| 1705 | method | `ProjectScanner.scan` | `def scan(self, previous_index: Mapping[str, str]) -> ProjectAnalysisResult` | no | end=1714; Run a complete project scan. |
| 1716 | method | `ProjectScanner._analyze_files` | `def _analyze_files(self) -> tuple[FileAnalysisResult, ...]` | no | end=1732; Analyze all discovered Python files. |
| 1734 | method | `ProjectScanner._execution_error` | `def _execution_error(self, path: Path, error: BaseException) -> FileAnalysisResult` | no | end=1738; Build explicit result for worker failure. |
| 1740 | method | `ProjectScanner._attach_cycles` | `def _attach_cycles(self, files: Sequence[FileAnalysisResult], graph: DependencyGraphResult) -> tuple[FileAnalysisResult, ...]` | no | end=1755; Attach dependency cycle issues to first file in each cycle. |
| 1757 | method | `ProjectScanner._state_delta` | `def _state_delta(self, files: Sequence[FileAnalysisResult], previous: Mapping[str, str]) -> StateDelta` | no | end=1762; Compare current hashes with previous run. |
| 1764 | method | `ProjectScanner._summary` | `def _summary(self, files: Sequence[FileAnalysisResult], issues: Sequence[DiagnosticIssue], graph: DependencyGraphResult) -> SummaryCounts` | no | end=1773; Build aggregate summary counts. |
| 1776 | class | `MarkdownReportWriter` | `class MarkdownReportWriter()` | no | end=1913; Renders project diagnostics into Somnus-styled markdown. |
| 1779 | method | `MarkdownReportWriter.__init__` | `def __init__(self, config: DoctorConfig) -> None` | no | end=1781; Initialize markdown writer. |
| 1783 | method | `MarkdownReportWriter.render` | `def render(self, result: ProjectAnalysisResult) -> str` | no | end=1798; Render full markdown report. |
| 1800 | method | `MarkdownReportWriter._header` | `def _header(self, result: ProjectAnalysisResult) -> list[str]` | no | end=1802; Render report header. |
| 1804 | method | `MarkdownReportWriter._terminal` | `def _terminal(self, result: ProjectAnalysisResult) -> list[str]` | no | end=1820; Render terminal-style executive block. |
| 1822 | method | `MarkdownReportWriter._summary` | `def _summary(self, result: ProjectAnalysisResult) -> list[str]` | no | end=1846; Render summary and categories. |
| 1848 | method | `MarkdownReportWriter._state` | `def _state(self, delta: StateDelta) -> list[str]` | no | end=1850; Render local state delta. |
| 1852 | method | `MarkdownReportWriter._dependency` | `def _dependency(self, result: ProjectAnalysisResult) -> list[str]` | no | end=1867; Render dependency graph section. |
| 1869 | method | `MarkdownReportWriter._short_sections` | `def _short_sections(self, result: ProjectAnalysisResult) -> list[str]` | no | end=1878; Render mandatory short class and function sections. |
| 1880 | method | `MarkdownReportWriter._issue_index` | `def _issue_index(self, result: ProjectAnalysisResult) -> list[str]` | no | end=1888; Render every issue in a sortable table. |
| 1890 | method | `MarkdownReportWriter._file_sections` | `def _file_sections(self, result: ProjectAnalysisResult) -> list[str]` | no | end=1900; Render per-file evidence and details. |
| 1902 | method | `MarkdownReportWriter._action_plan` | `def _action_plan(self, result: ProjectAnalysisResult) -> list[str]` | no | end=1913; Render action plan from severity gates. |
| 1916 | class | `StateStore` | `class StateStore()` | no | end=2009; Persists scan history, report aliases, and file hashes for report rollback. |
| 1919 | method | `StateStore.__init__` | `def __init__(self, project_root: Path, config: DoctorConfig) -> None` | no | end=1925; Initialize state store under project root. |
| 1927 | method | `StateStore.initialize` | `def initialize(self) -> None` | no | end=1940; Create state directories and SQLite schema. |
| 1942 | method | `StateStore.previous_file_index` | `def previous_file_index(self) -> Mapping[str, str]` | no | end=1953; Load previous latest file hash index. |
| 1955 | method | `StateStore.report_paths` | `def report_paths(self, run_id: str, output: Path \| None, json_output: Path \| None) -> ReportPaths` | no | end=1962; Resolve all report paths for a run. |
| 1964 | method | `StateStore.persist` | `def persist(self, result: ProjectAnalysisResult, markdown: str, json_text: str, paths: ReportPaths) -> None` | no | end=1979; Write artifacts and record the run. |
| 1981 | method | `StateStore.history` | `def history(self, limit: int) -> tuple[RunRecord, ...]` | no | end=1989; Return recent run records. |
| 1991 | method | `StateStore.rollback` | `def rollback(self, run_id: str) -> RunRecord` | no | end=2009; Make a previous run the latest report alias. |
| 2012 | function | `write_text_atomic` | `def write_text_atomic(path: Path, text: str) -> None` | no | end=2020; Write text atomically to path. |
| 2023 | function | `copy_file_atomic` | `def copy_file_atomic(source: Path, destination: Path) -> None` | no | end=2031; Copy file atomically. |
| 2034 | function | `render_history` | `def render_history(records: Sequence[RunRecord]) -> str` | no | end=2043; Render run history for CLI output. |
| 2046 | function | `exit_code_for_summary` | `def exit_code_for_summary(summary: SummaryCounts, gate: str) -> int` | no | end=2058; Calculate process exit code from severity gate. |
| 2061 | function | `run_scan` | `def run_scan(args: argparse.Namespace) -> int` | no | end=2093; Execute scan command and write reports. |
| 2096 | function | `run_init_config` | `def run_init_config(args: argparse.Namespace) -> int` | no | end=2103; Write default YAML configuration. |
| 2106 | function | `run_history` | `def run_history(args: argparse.Namespace) -> int` | no | end=2110; Print local scan history. |
| 2113 | function | `run_rollback` | `def run_rollback(args: argparse.Namespace) -> int` | no | end=2120; Roll latest report alias back to a previous run. |
| 2123 | function | `run_self_check` | `def run_self_check(args: argparse.Namespace) -> int` | no | end=2127; Run doctor against directory containing this file. |
| 2130 | function | `build_parser` | `def build_parser() -> argparse.ArgumentParser` | no | end=2162; Build CLI parser. |
| 2165 | function | `normalize_argv` | `def normalize_argv(argv: Sequence[str]) -> list[str]` | no | end=2176; Normalize legacy positional invocation into scan subcommand. |
| 2179 | function | `setup_logging` | `def setup_logging(verbose: bool=False) -> None` | no | end=2181; Configure diagnostic logging. |
| 2184 | function | `main` | `def main(argv: Sequence[str] \| None=None) -> int` | yes | re-exported by somnus_debug.doctor.__all__; console script somnus-doctor; end=2199; Run command-line interface. |

## src/somnus_debug/pycache_cleaner/__init__.py

This section lists the 2 symbols defined in `src/somnus_debug/pycache_cleaner/__init__.py`.

| Line | Kind | Name | Signature | Exported | Notes |
|---:|---|---|---|---|---|
| 41 | reexport | `main` | `from .core import main` | yes | re-exported via __all__ |
| 43 | dunder | `__all__` | `__all__ = ['main']` | no | end=43 |

## src/somnus_debug/pycache_cleaner/core.py

This section lists the 15 symbols defined in `src/somnus_debug/pycache_cleaner/core.py`.

| Line | Kind | Name | Signature | Exported | Notes |
|---:|---|---|---|---|---|
| 158 | dataclass | `CleanerConfig` | `class CleanerConfig()` | no | named in README/MANUAL library section; decorators=dataclass; end=186; fields[roots:List[str]=field(default_factory=list); exclude:List[str]… |
| 170 | staticmethod | `CleanerConfig.from_yaml` | `def from_yaml(path: Path) -> 'CleanerConfig'` | no | decorators=staticmethod; end=180; Load configuration from a YAML file. |
| 182 | method | `CleanerConfig.normalize` | `def normalize(self) -> None` | no | end=186; Normalize and expand paths in the configuration. |
| 189 | class | `PycacheCleaner` | `class PycacheCleaner()` | no | named in README/MANUAL library section; end=321; Implements the logic for finding and deleting Python cache artefacts. |
| 192 | method | `PycacheCleaner.__init__` | `def __init__(self, config: CleanerConfig) -> None` | no | end=205;  |
| 207 | method | `PycacheCleaner.run` | `def run(self) -> None` | no | end=218; Run the cleaner across all configured root directories. |
| 220 | method | `PycacheCleaner._scan_root` | `def _scan_root(self, root: Path) -> None` | no | end=258; Recursively scan a root directory and delete matching targets. |
| 260 | method | `PycacheCleaner._is_excluded` | `def _is_excluded(self, name: str) -> bool` | no | end=265; Check whether a directory name matches any exclude pattern. |
| 267 | method | `PycacheCleaner._match_file` | `def _match_file(self, name: str) -> bool` | no | end=272; Check whether a file name matches any target file pattern. |
| 274 | method | `PycacheCleaner._delete_directory` | `def _delete_directory(self, path: Path) -> None` | no | end=290; Delete a directory tree and update statistics. |
| 292 | method | `PycacheCleaner._delete_file` | `def _delete_file(self, path: Path) -> None` | no | end=308; Delete a single file and update statistics. |
| 311 | staticmethod | `PycacheCleaner._get_dir_size` | `def _get_dir_size(path: Path) -> int` | no | decorators=staticmethod; end=321; Compute total size of files under a directory tree. |
| 324 | function | `setup_logging` | `def setup_logging(cfg: CleanerConfig) -> None` | no | end=334; Configure logging based on the configuration and CLI options. |
| 337 | function | `parse_args` | `def parse_args() -> argparse.Namespace` | no | end=346; Parse command‑line arguments. |
| 349 | function | `main` | `def main() -> None` | yes | re-exported by somnus_debug.pycache_cleaner.__all__; console script somnus-pycache-clean; end=372 |

## src/somnus_debug/structure/__init__.py

This section lists the 3 symbols defined in `src/somnus_debug/structure/__init__.py`.

| Line | Kind | Name | Signature | Exported | Notes |
|---:|---|---|---|---|---|
| 41 | reexport | `build_index` | `from .core import build_index` | yes | re-exported via __all__ |
| 41 | reexport | `main` | `from .core import main` | yes | re-exported via __all__ |
| 43 | dunder | `__all__` | `__all__ = ['build_index', 'main']` | no | end=43 |

## src/somnus_debug/structure/core.py

This section lists the 14 symbols defined in `src/somnus_debug/structure/core.py`.

| Line | Kind | Name | Signature | Exported | Notes |
|---:|---|---|---|---|---|
| 58 | function | `_one_line` | `def _one_line(value: str) -> str` | no | end=60; Collapse source/docstring whitespace for compact index entries. |
| 63 | function | `_doc_summary` | `def _doc_summary(node: ast.AST) -> Optional[str]` | no | end=72; Return the first paragraph of a node's docstring, if present. |
| 75 | function | `_unparse` | `def _unparse(node: ast.AST) -> str` | no | end=80; Unparse an AST node with a readable fallback for older Python versions. |
| 83 | function | `_signature` | `def _signature(node: ast.FunctionDef \| ast.AsyncFunctionDef) -> str` | no | end=91; Render a function signature without its body. |
| 94 | function | `_decorators` | `def _decorators(node: ast.AST) -> list[str]` | no | end=95;  |
| 98 | function | `_line_span` | `def _line_span(node: ast.AST) -> str` | no | end=101;  |
| 104 | function | `_class_header` | `def _class_header(node: ast.ClassDef) -> str` | no | end=106;  |
| 109 | function | `_definition_lines` | `def _definition_lines(node: ast.FunctionDef \| ast.AsyncFunctionDef, *, indent: str, include_lines: bool) -> list[str]` | no | end=124;  |
| 127 | function | `_iter_classes` | `def _iter_classes(body: Iterable[ast.stmt]) -> Iterable[ast.ClassDef]` | no | end=132; Yield classes in source order, including nested classes. |
| 135 | function | `_count_indexed_definitions` | `def _count_indexed_definitions(classes: Iterable[ast.ClassDef], module_functions: Iterable[ast.AST]) -> int` | no | end=147; Count the definitions that the renderer actually emits. |
| 150 | function | `_render_class` | `def _render_class(node: ast.ClassDef, *, include_lines: bool, nested: bool=False, occurrence_label: str='', occurrence_map: Optional[dict[int, str]]=N…` | no | end=199;  |
| 202 | function | `build_index` | `def build_index(source: str, *, source_name: str, include_lines: bool=True, include_module_functions: bool=True) -> str` | yes | re-exported by somnus_debug.structure.__all__; named in README/MANUAL library section; end=285; Build a deterministic Markdown/plain-text in… |
| 288 | function | `_parse_args` | `def _parse_args(argv: Optional[Sequence[str]]=None) -> argparse.Namespace` | no | end=320;  |
| 323 | function | `main` | `def main(argv: Optional[Sequence[str]]=None) -> int` | yes | re-exported by somnus_debug.structure.__all__; console script somnus-structure; end=347 |

## src/somnus_debug/test_harness/scaffold.py

This section lists the 5 symbols defined in `src/somnus_debug/test_harness/scaffold.py`.

| Line | Kind | Name | Signature | Exported | Notes |
|---:|---|---|---|---|---|
| 55 | constant | `_TEMPLATE_FILES` | `_TEMPLATE_FILES = ('run_test.py', 'CONTRACT.md')` | no | end=55 |
| 58 | function | `_template_text` | `def _template_text(name: str) -> str` | no | end=59;  |
| 62 | function | `scaffold` | `def scaffold(target_dir: Path, *, force: bool=False, with_contract: bool=True) -> list[Path]` | no | named in README/MANUAL library section; end=88; Copy the test-harness template into ``target_dir``. |
| 91 | function | `_parse_args` | `def _parse_args(argv: Sequence[str] \| None) -> argparse.Namespace` | no | end=109;  |
| 112 | function | `main` | `def main(argv: Sequence[str] \| None=None) -> int` | no | end=125;  |

## src/somnus_debug/test_harness/templates/run_test.py

This section lists the 17 symbols defined in `src/somnus_debug/test_harness/templates/run_test.py`.

| Line | Kind | Name | Signature | Exported | Notes |
|---:|---|---|---|---|---|
| 144 | dataclass | `Check` | `class Check()` | no | decorators=dataclass(frozen=True); end=151; fields[name:str; passed:bool; detail:str=''; expected:Any=None; observed:Any=None]; One package-… |
| 155 | dataclass | `TestOutcome` | `class TestOutcome()` | no | decorators=dataclass; end=171; fields[summary:str; checks:list[Check]; metrics:dict[str, Any]=field(default_factory=dict); evidence:dict[str… |
| 170 | property | `TestOutcome.passed` | `def passed(self) -> bool` | no | decorators=property; end=171;  |
| 175 | dataclass | `TestContext` | `class TestContext()` | no | decorators=dataclass(frozen=True); end=181; fields[run_id:str; project_root:Path; artifact_dir:Path; logger:logging.Logger]; Runtime context… |
| 195 | constant | `TEST_NAME` | `TEST_NAME = 'GOLDEN PATH LAYER 1 DATA HIGHWAY RESTORATION'` | no | end=195 |
| 198 | function | `execute_test` | `def execute_test(ctx: TestContext) -> TestOutcome` | no | end=482; Execute ONE meaningful project/package validation. |
| 249 | nested_function | `execute_test.digest` | `def digest(path: Path) -> str` | no | end=250;  |
| 489 | constant | `SCHEMA_VERSION` | `SCHEMA_VERSION = '1.0'` | no | end=489 |
| 492 | function | `_run_command` | `def _run_command(command: list[str], *, cwd: Path, logger: logging.Logger, expected: int=0) -> subprocess.CompletedProcess[str]` | no | end=527; Run a subprocess, log the invocation and output, and raise on unexpected exit. |
| 530 | function | `_utc_now` | `def _utc_now() -> datetime` | no | end=531;  |
| 534 | function | `_slug` | `def _slug(value: str) -> str` | no | end=538;  |
| 541 | function | `_json_safe` | `def _json_safe(value: Any) -> Any` | no | end=551; Recursively convert common values to JSON-safe representations. |
| 554 | function | `_setup_logger` | `def _setup_logger(log_file: Path) -> logging.Logger` | no | end=586;  |
| 589 | function | `_default_output_root` | `def _default_output_root(project_root: Path) -> Path` | no | end=593;  |
| 596 | function | `_build_manifest` | `def _build_manifest(*, ctx: TestContext, started_at: datetime, finished_at: datetime, elapsed_s: float, outcome: TestOutcome \| None, error: dict[str,…` | no | end=645;  |
| 648 | function | `_render_report` | `def _render_report(manifest: Mapping[str, Any]) -> str` | no | end=744; Produce a factual Markdown run summary. |
| 747 | function | `main` | `def main() -> int` | no | end=855;  |

## Sources

This section lists where the data came from.

- [lane-a symbols.tsv](../_evidence/agent-findings/lane-a-arch-api/symbols.tsv) and [ast_enum.py.txt](../_evidence/agent-findings/lane-a-arch-api/ast_enum.py.txt)
- `src/somnus_debug/**/*.py` at baseline `034f46e` (spot checks above)
