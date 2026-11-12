# API index

This page is an alphabetical index of every module-level name, class, function, and static method in `src/somnus_debug/`, linked to the page that documents it. Instance methods are omitted here; they are listed under their class in [classes](classes.md) and in full in [symbol-index](../13-reference/symbol-index.md).

## How to read the tiers

This section defines the tier column, which says how much to rely on a name.

- **exported**: listed in a package `__all__`, or the `__version__` constant.
- **documented**: named as a library entry point in README / MANUAL §8 ([DOCUMENTED-ONLY] there; signatures are in [public-api](public-api.md)).
- **internal**: importable, with no leading underscore and no promise of stability.
- **private**: leading underscore.
- **template**: defined in `test_harness/templates/run_test.py`. That file is copied into projects by `scaffold` and is not imported by the package.

[SOURCE-CONFIRMED] Rows were generated from [lane-a symbols.tsv](../_evidence/agent-findings/lane-a-arch-api/symbols.tsv) (256 symbols, produced by an AST walk over `src/`). Method rows and re-export rows are dropped, except static methods. Spot-checked against source: `ConfigManager` at `src/somnus_debug/doctor/core.py:782`, `scaffold` at `src/somnus_debug/test_harness/scaffold.py:62`, `build_index` at `src/somnus_debug/structure/core.py:202`. [VERIFIED]

## Index

This section is the table itself, sorted case-insensitively by name.

| Name | Kind | Module | Defined at | Tier | Documented in |
|---|---|---|---|---|---|
| `__version__` | dunder | `somnus_debug.__init__` | `src/somnus_debug/__init__.py:57` | exported | [public-api](public-api.md) |
| `_build_manifest` | function | `somnus_debug.test_harness.templates.run_test` | `src/somnus_debug/test_harness/templates/run_test.py:596` | template | [types-and-schemas](types-and-schemas.md#pycache-and-harness-types) |
| `_class_header` | function | `somnus_debug.structure.core` | `src/somnus_debug/structure/core.py:104` | private | [functions](functions.md) |
| `_count_indexed_definitions` | function | `somnus_debug.structure.core` | `src/somnus_debug/structure/core.py:135` | private | [functions](functions.md) |
| `_decorators` | function | `somnus_debug.structure.core` | `src/somnus_debug/structure/core.py:94` | private | [functions](functions.md) |
| `_default_output_root` | function | `somnus_debug.test_harness.templates.run_test` | `src/somnus_debug/test_harness/templates/run_test.py:589` | template | [types-and-schemas](types-and-schemas.md#pycache-and-harness-types) |
| `_definition_lines` | function | `somnus_debug.structure.core` | `src/somnus_debug/structure/core.py:109` | private | [functions](functions.md) |
| `_doc_summary` | function | `somnus_debug.structure.core` | `src/somnus_debug/structure/core.py:63` | private | [functions](functions.md) |
| `_iter_classes` | function | `somnus_debug.structure.core` | `src/somnus_debug/structure/core.py:127` | private | [functions](functions.md) |
| `_json_safe` | function | `somnus_debug.test_harness.templates.run_test` | `src/somnus_debug/test_harness/templates/run_test.py:541` | template | [types-and-schemas](types-and-schemas.md#pycache-and-harness-types) |
| `_line_span` | function | `somnus_debug.structure.core` | `src/somnus_debug/structure/core.py:98` | private | [functions](functions.md) |
| `_one_line` | function | `somnus_debug.structure.core` | `src/somnus_debug/structure/core.py:58` | private | [functions](functions.md) |
| `_parse_args` | function | `somnus_debug.structure.core` | `src/somnus_debug/structure/core.py:288` | private | [functions](functions.md) |
| `_parse_args` | function | `somnus_debug.test_harness.scaffold` | `src/somnus_debug/test_harness/scaffold.py:91` | private | [functions](functions.md) |
| `_render_class` | function | `somnus_debug.structure.core` | `src/somnus_debug/structure/core.py:150` | private | [functions](functions.md) |
| `_render_report` | function | `somnus_debug.test_harness.templates.run_test` | `src/somnus_debug/test_harness/templates/run_test.py:648` | template | [types-and-schemas](types-and-schemas.md#pycache-and-harness-types) |
| `_run_command` | function | `somnus_debug.test_harness.templates.run_test` | `src/somnus_debug/test_harness/templates/run_test.py:492` | template | [types-and-schemas](types-and-schemas.md#pycache-and-harness-types) |
| `_run_subcommand` | function | `somnus_debug.cli` | `src/somnus_debug/cli.py:85` | private | [functions](functions.md) |
| `_setup_logger` | function | `somnus_debug.test_harness.templates.run_test` | `src/somnus_debug/test_harness/templates/run_test.py:554` | template | [types-and-schemas](types-and-schemas.md#pycache-and-harness-types) |
| `_signature` | function | `somnus_debug.structure.core` | `src/somnus_debug/structure/core.py:83` | private | [functions](functions.md) |
| `_slug` | function | `somnus_debug.test_harness.templates.run_test` | `src/somnus_debug/test_harness/templates/run_test.py:534` | template | [types-and-schemas](types-and-schemas.md#pycache-and-harness-types) |
| `_SUBCOMMANDS` | constant | `somnus_debug.cli` | `src/somnus_debug/cli.py:60` | private | [symbol-index](../13-reference/symbol-index.md) |
| `_TEMPLATE_FILES` | constant | `somnus_debug.test_harness.scaffold` | `src/somnus_debug/test_harness/scaffold.py:55` | private | [symbol-index](../13-reference/symbol-index.md) |
| `_template_text` | function | `somnus_debug.test_harness.scaffold` | `src/somnus_debug/test_harness/scaffold.py:58` | private | [functions](functions.md) |
| `_TOP_LEVEL_HELP` | constant | `somnus_debug.cli` | `src/somnus_debug/cli.py:67` | private | [symbol-index](../13-reference/symbol-index.md) |
| `_unparse` | function | `somnus_debug.structure.core` | `src/somnus_debug/structure/core.py:75` | private | [functions](functions.md) |
| `_utc_now` | function | `somnus_debug.test_harness.templates.run_test` | `src/somnus_debug/test_harness/templates/run_test.py:530` | template | [types-and-schemas](types-and-schemas.md#pycache-and-harness-types) |
| `AnalysisExecutionError` | class | `somnus_debug.doctor.core` | `src/somnus_debug/doctor/core.py:183` | internal | [exceptions](exceptions.md) |
| `body_is_stub` | function | `somnus_debug.doctor.core` | `src/somnus_debug/doctor/core.py:1436` | internal | [functions](functions.md) |
| `body_without_docstring` | function | `somnus_debug.doctor.core` | `src/somnus_debug/doctor/core.py:1379` | internal | [functions](functions.md) |
| `build_index` | function | `somnus_debug.structure.core` | `src/somnus_debug/structure/core.py:202` | exported | [public-api](public-api.md) |
| `build_parser` | function | `somnus_debug.doctor.core` | `src/somnus_debug/doctor/core.py:2130` | internal | [functions](functions.md) |
| `canonical_cycle` | function | `somnus_debug.doctor.core` | `src/somnus_debug/doctor/core.py:1682` | internal | [functions](functions.md) |
| `Check` | dataclass | `somnus_debug.test_harness.templates.run_test` | `src/somnus_debug/test_harness/templates/run_test.py:144` | template | [types-and-schemas](types-and-schemas.md#pycache-and-harness-types) |
| `ClassDiagnostic` | dataclass | `somnus_debug.doctor.core` | `src/somnus_debug/doctor/core.py:285` | internal | [types-and-schemas](types-and-schemas.md) |
| `CleanerConfig` | dataclass | `somnus_debug.pycache_cleaner.core` | `src/somnus_debug/pycache_cleaner/core.py:158` | documented | [public-api](public-api.md) |
| `CleanerConfig.from_yaml` | staticmethod | `somnus_debug.pycache_cleaner.core` | `src/somnus_debug/pycache_cleaner/core.py:170` | internal | [functions](functions.md) |
| `CodeQualityVisitor` | class | `somnus_debug.doctor.core` | `src/somnus_debug/doctor/core.py:1143` | internal | [classes](classes.md) |
| `COMMANDS` | constant | `somnus_debug.doctor.core` | `src/somnus_debug/doctor/core.py:83` | internal | [types-and-schemas](types-and-schemas.md) |
| `ConfigManager` | class | `somnus_debug.doctor.core` | `src/somnus_debug/doctor/core.py:782` | documented | [public-api](public-api.md) |
| `ConfigManager.default_yaml` | staticmethod | `somnus_debug.doctor.core` | `src/somnus_debug/doctor/core.py:854` | internal | [functions](functions.md) |
| `ConfigurationError` | class | `somnus_debug.doctor.core` | `src/somnus_debug/doctor/core.py:123` | internal | [exceptions](exceptions.md) |
| `copy_file_atomic` | function | `somnus_debug.doctor.core` | `src/somnus_debug/doctor/core.py:2023` | internal | [functions](functions.md) |
| `cyclomatic_complexity` | function | `somnus_debug.doctor.core` | `src/somnus_debug/doctor/core.py:1423` | internal | [functions](functions.md) |
| `dedupe_issues` | function | `somnus_debug.doctor.core` | `src/somnus_debug/doctor/core.py:1361` | internal | [functions](functions.md) |
| `deep_merge` | function | `somnus_debug.doctor.core` | `src/somnus_debug/doctor/core.py:726` | internal | [functions](functions.md) |
| `DEFAULT_CONFIG_DATA` | constant | `somnus_debug.doctor.core` | `src/somnus_debug/doctor/core.py:451` | internal | [types-and-schemas](types-and-schemas.md) |
| `DEFAULT_CONFIG_NAME` | constant | `somnus_debug.doctor.core` | `src/somnus_debug/doctor/core.py:81` | internal | [symbol-index](../13-reference/symbol-index.md) |
| `DependencyGraphBuilder` | class | `somnus_debug.doctor.core` | `src/somnus_debug/doctor/core.py:1618` | internal | [classes](classes.md) |
| `DependencyGraphResult` | dataclass | `somnus_debug.doctor.core` | `src/somnus_debug/doctor/core.py:369` | internal | [types-and-schemas](types-and-schemas.md) |
| `DiagnosticIssue` | dataclass | `somnus_debug.doctor.core` | `src/somnus_debug/doctor/core.py:243` | internal | [types-and-schemas](types-and-schemas.md) |
| `DiagnosticIssueFactory` | class | `somnus_debug.doctor.core` | `src/somnus_debug/doctor/core.py:1070` | internal | [classes](classes.md) |
| `DoctorConfig` | dataclass | `somnus_debug.doctor.core` | `src/somnus_debug/doctor/core.py:208` | documented | [public-api](public-api.md) |
| `DoctorError` | class | `somnus_debug.doctor.core` | `src/somnus_debug/doctor/core.py:95` | internal | [exceptions](exceptions.md) |
| `dotted_name` | function | `somnus_debug.doctor.core` | `src/somnus_debug/doctor/core.py:1490` | internal | [functions](functions.md) |
| `dumps_json` | function | `somnus_debug.doctor.core` | `src/somnus_debug/doctor/core.py:578` | internal | [functions](functions.md) |
| `executable_line_count` | function | `somnus_debug.doctor.core` | `src/somnus_debug/doctor/core.py:1386` | internal | [functions](functions.md) |
| `execute_test` | function | `somnus_debug.test_harness.templates.run_test` | `src/somnus_debug/test_harness/templates/run_test.py:198` | template | [types-and-schemas](types-and-schemas.md#pycache-and-harness-types) |
| `execute_test.digest` | nested_function | `somnus_debug.test_harness.templates.run_test` | `src/somnus_debug/test_harness/templates/run_test.py:249` | template | [types-and-schemas](types-and-schemas.md#pycache-and-harness-types) |
| `exit_code_for_summary` | function | `somnus_debug.doctor.core` | `src/somnus_debug/doctor/core.py:2046` | internal | [functions](functions.md) |
| `FileAnalysisResult` | dataclass | `somnus_debug.doctor.core` | `src/somnus_debug/doctor/core.py:350` | internal | [types-and-schemas](types-and-schemas.md) |
| `FileAnalyzer` | class | `somnus_debug.doctor.core` | `src/somnus_debug/doctor/core.py:1507` | internal | [classes](classes.md) |
| `FileMetrics` | dataclass | `somnus_debug.doctor.core` | `src/somnus_debug/doctor/core.py:331` | internal | [types-and-schemas](types-and-schemas.md) |
| `FileReadError` | class | `somnus_debug.doctor.core` | `src/somnus_debug/doctor/core.py:138` | internal | [exceptions](exceptions.md) |
| `function_argument_count` | function | `somnus_debug.doctor.core` | `src/somnus_debug/doctor/core.py:1397` | internal | [functions](functions.md) |
| `FunctionDiagnostic` | dataclass | `somnus_debug.doctor.core` | `src/somnus_debug/doctor/core.py:267` | internal | [types-and-schemas](types-and-schemas.md) |
| `handler_is_silent` | function | `somnus_debug.doctor.core` | `src/somnus_debug/doctor/core.py:1471` | internal | [functions](functions.md) |
| `ImportCollector` | class | `somnus_debug.doctor.core` | `src/somnus_debug/doctor/core.py:1093` | internal | [classes](classes.md) |
| `ImportEdge` | dataclass | `somnus_debug.doctor.core` | `src/somnus_debug/doctor/core.py:317` | internal | [types-and-schemas](types-and-schemas.md) |
| `ImportKind` | module_var | `somnus_debug.doctor.core` | `src/somnus_debug/doctor/core.py:77` | internal | [types-and-schemas](types-and-schemas.md) |
| `ImportRecord` | dataclass | `somnus_debug.doctor.core` | `src/somnus_debug/doctor/core.py:303` | internal | [types-and-schemas](types-and-schemas.md) |
| `ImportResolver` | class | `somnus_debug.doctor.core` | `src/somnus_debug/doctor/core.py:995` | internal | [classes](classes.md) |
| `is_private_function` | function | `somnus_debug.doctor.core` | `src/somnus_debug/doctor/core.py:1402` | internal | [functions](functions.md) |
| `isoformat_utc` | function | `somnus_debug.doctor.core` | `src/somnus_debug/doctor/core.py:535` | internal | [functions](functions.md) |
| `JsonObject` | module_var | `somnus_debug.doctor.core` | `src/somnus_debug/doctor/core.py:76` | internal | [types-and-schemas](types-and-schemas.md) |
| `JsonScalar` | module_var | `somnus_debug.doctor.core` | `src/somnus_debug/doctor/core.py:74` | internal | [types-and-schemas](types-and-schemas.md) |
| `JsonValue` | module_var | `somnus_debug.doctor.core` | `src/somnus_debug/doctor/core.py:75` | internal | [types-and-schemas](types-and-schemas.md) |
| `LoadedNameCollector` | class | `somnus_debug.doctor.core` | `src/somnus_debug/doctor/core.py:1122` | internal | [classes](classes.md) |
| `LOGGER_NAME` | constant | `somnus_debug.doctor.core` | `src/somnus_debug/doctor/core.py:80` | internal | [types-and-schemas](types-and-schemas.md) |
| `main` | function | `somnus_debug.cli` | `src/somnus_debug/cli.py:107` | internal | [public-api](public-api.md) |
| `main` | function | `somnus_debug.doctor.core` | `src/somnus_debug/doctor/core.py:2184` | exported | [public-api](public-api.md) |
| `main` | function | `somnus_debug.pycache_cleaner.core` | `src/somnus_debug/pycache_cleaner/core.py:349` | exported | [public-api](public-api.md) |
| `main` | function | `somnus_debug.structure.core` | `src/somnus_debug/structure/core.py:323` | exported | [public-api](public-api.md) |
| `main` | function | `somnus_debug.test_harness.scaffold` | `src/somnus_debug/test_harness/scaffold.py:112` | internal | [public-api](public-api.md) |
| `main` | function | `somnus_debug.test_harness.templates.run_test` | `src/somnus_debug/test_harness/templates/run_test.py:747` | template | [types-and-schemas](types-and-schemas.md#pycache-and-harness-types) |
| `MarkdownReportWriter` | class | `somnus_debug.doctor.core` | `src/somnus_debug/doctor/core.py:1776` | internal | [classes](classes.md) |
| `meaningful_doc` | function | `somnus_debug.doctor.core` | `src/somnus_debug/doctor/core.py:1374` | internal | [functions](functions.md) |
| `mermaid_escape` | function | `somnus_debug.doctor.core` | `src/somnus_debug/doctor/core.py:1690` | internal | [functions](functions.md) |
| `MinimalYamlParser` | class | `somnus_debug.doctor.core` | `src/somnus_debug/doctor/core.py:646` | internal | [classes](classes.md) |
| `missing_type_hints` | function | `somnus_debug.doctor.core` | `src/somnus_debug/doctor/core.py:1407` | internal | [functions](functions.md) |
| `normalize_argv` | function | `somnus_debug.doctor.core` | `src/somnus_debug/doctor/core.py:2165` | internal | [functions](functions.md) |
| `parse_args` | function | `somnus_debug.pycache_cleaner.core` | `src/somnus_debug/pycache_cleaner/core.py:337` | internal | [functions](functions.md) |
| `parse_severities` | function | `somnus_debug.doctor.core` | `src/somnus_debug/doctor/core.py:769` | internal | [functions](functions.md) |
| `parse_yaml_scalar` | function | `somnus_debug.doctor.core` | `src/somnus_debug/doctor/core.py:619` | internal | [functions](functions.md) |
| `PLACEHOLDER_CONSTANTS` | constant | `somnus_debug.doctor.core` | `src/somnus_debug/doctor/core.py:513` | internal | [types-and-schemas](types-and-schemas.md) |
| `placeholder_return_kind` | function | `somnus_debug.doctor.core` | `src/somnus_debug/doctor/core.py:1451` | internal | [functions](functions.md) |
| `ProjectAnalysisResult` | dataclass | `somnus_debug.doctor.core` | `src/somnus_debug/doctor/core.py:408` | internal | [types-and-schemas](types-and-schemas.md) |
| `ProjectFileIndex` | class | `somnus_debug.doctor.core` | `src/somnus_debug/doctor/core.py:926` | internal | [classes](classes.md) |
| `ProjectScanner` | class | `somnus_debug.doctor.core` | `src/somnus_debug/doctor/core.py:1695` | documented | [public-api](public-api.md) |
| `PycacheCleaner` | class | `somnus_debug.pycache_cleaner.core` | `src/somnus_debug/pycache_cleaner/core.py:189` | documented | [public-api](public-api.md) |
| `PycacheCleaner._get_dir_size` | staticmethod | `somnus_debug.pycache_cleaner.core` | `src/somnus_debug/pycache_cleaner/core.py:311` | private | [functions](functions.md) |
| `render_history` | function | `somnus_debug.doctor.core` | `src/somnus_debug/doctor/core.py:2034` | internal | [functions](functions.md) |
| `ReportGenerationError` | class | `somnus_debug.doctor.core` | `src/somnus_debug/doctor/core.py:153` | internal | [exceptions](exceptions.md) |
| `ReportPaths` | dataclass | `somnus_debug.doctor.core` | `src/somnus_debug/doctor/core.py:424` | internal | [types-and-schemas](types-and-schemas.md) |
| `require_bool` | function | `somnus_debug.doctor.core` | `src/somnus_debug/doctor/core.py:737` | internal | [functions](functions.md) |
| `require_int` | function | `somnus_debug.doctor.core` | `src/somnus_debug/doctor/core.py:745` | internal | [functions](functions.md) |
| `require_str` | function | `somnus_debug.doctor.core` | `src/somnus_debug/doctor/core.py:753` | internal | [functions](functions.md) |
| `require_str_tuple` | function | `somnus_debug.doctor.core` | `src/somnus_debug/doctor/core.py:761` | internal | [functions](functions.md) |
| `run_history` | function | `somnus_debug.doctor.core` | `src/somnus_debug/doctor/core.py:2106` | internal | [functions](functions.md) |
| `RUN_ID_FORMAT` | constant | `somnus_debug.doctor.core` | `src/somnus_debug/doctor/core.py:82` | internal | [types-and-schemas](types-and-schemas.md) |
| `run_init_config` | function | `somnus_debug.doctor.core` | `src/somnus_debug/doctor/core.py:2096` | internal | [functions](functions.md) |
| `run_rollback` | function | `somnus_debug.doctor.core` | `src/somnus_debug/doctor/core.py:2113` | internal | [functions](functions.md) |
| `run_scan` | function | `somnus_debug.doctor.core` | `src/somnus_debug/doctor/core.py:2061` | internal | [functions](functions.md) |
| `run_self_check` | function | `somnus_debug.doctor.core` | `src/somnus_debug/doctor/core.py:2123` | internal | [functions](functions.md) |
| `RunRecord` | dataclass | `somnus_debug.doctor.core` | `src/somnus_debug/doctor/core.py:436` | internal | [types-and-schemas](types-and-schemas.md) |
| `safe_relpath` | function | `somnus_debug.doctor.core` | `src/somnus_debug/doctor/core.py:583` | internal | [functions](functions.md) |
| `scaffold` | function | `somnus_debug.test_harness.scaffold` | `src/somnus_debug/test_harness/scaffold.py:62` | documented | [public-api](public-api.md) |
| `SCHEMA_VERSION` | constant | `somnus_debug.test_harness.templates.run_test` | `src/somnus_debug/test_harness/templates/run_test.py:489` | template | [types-and-schemas](types-and-schemas.md#pycache-and-harness-types) |
| `SECURITY_CALLS` | constant | `somnus_debug.doctor.core` | `src/somnus_debug/doctor/core.py:514` | internal | [types-and-schemas](types-and-schemas.md) |
| `setup_logging` | function | `somnus_debug.doctor.core` | `src/somnus_debug/doctor/core.py:2179` | internal | [functions](functions.md) |
| `setup_logging` | function | `somnus_debug.pycache_cleaner.core` | `src/somnus_debug/pycache_cleaner/core.py:324` | internal | [functions](functions.md) |
| `Severity` | enum | `somnus_debug.doctor.core` | `src/somnus_debug/doctor/core.py:86` | internal | [types-and-schemas](types-and-schemas.md) |
| `SOMNUS_MARKDOWN_STYLE` | constant | `somnus_debug.doctor.core` | `src/somnus_debug/doctor/core.py:516` | internal | [symbol-index](../13-reference/symbol-index.md) |
| `SourceReader` | class | `somnus_debug.doctor.core` | `src/somnus_debug/doctor/core.py:1058` | internal | [classes](classes.md) |
| `stable_hash_file` | function | `somnus_debug.doctor.core` | `src/somnus_debug/doctor/core.py:547` | internal | [functions](functions.md) |
| `stable_hash_text` | function | `somnus_debug.doctor.core` | `src/somnus_debug/doctor/core.py:542` | internal | [functions](functions.md) |
| `StateDelta` | dataclass | `somnus_debug.doctor.core` | `src/somnus_debug/doctor/core.py:380` | internal | [types-and-schemas](types-and-schemas.md) |
| `StateStore` | class | `somnus_debug.doctor.core` | `src/somnus_debug/doctor/core.py:1916` | internal | [classes](classes.md) |
| `StateStoreError` | class | `somnus_debug.doctor.core` | `src/somnus_debug/doctor/core.py:168` | internal | [exceptions](exceptions.md) |
| `strip_yaml_comment` | function | `somnus_debug.doctor.core` | `src/somnus_debug/doctor/core.py:596` | internal | [functions](functions.md) |
| `SummaryCounts` | dataclass | `somnus_debug.doctor.core` | `src/somnus_debug/doctor/core.py:390` | internal | [types-and-schemas](types-and-schemas.md) |
| `table_escape` | function | `somnus_debug.doctor.core` | `src/somnus_debug/doctor/core.py:591` | internal | [functions](functions.md) |
| `TEST_NAME` | constant | `somnus_debug.test_harness.templates.run_test` | `src/somnus_debug/test_harness/templates/run_test.py:195` | template | [types-and-schemas](types-and-schemas.md#pycache-and-harness-types) |
| `TestContext` | dataclass | `somnus_debug.test_harness.templates.run_test` | `src/somnus_debug/test_harness/templates/run_test.py:175` | template | [types-and-schemas](types-and-schemas.md#pycache-and-harness-types) |
| `TestOutcome` | dataclass | `somnus_debug.test_harness.templates.run_test` | `src/somnus_debug/test_harness/templates/run_test.py:155` | template | [types-and-schemas](types-and-schemas.md#pycache-and-harness-types) |
| `TestOutcome.passed` | property | `somnus_debug.test_harness.templates.run_test` | `src/somnus_debug/test_harness/templates/run_test.py:170` | template | [types-and-schemas](types-and-schemas.md#pycache-and-harness-types) |
| `to_json_value` | function | `somnus_debug.doctor.core` | `src/somnus_debug/doctor/core.py:559` | internal | [functions](functions.md) |
| `TODO_PATTERNS` | constant | `somnus_debug.doctor.core` | `src/somnus_debug/doctor/core.py:504` | internal | [types-and-schemas](types-and-schemas.md) |
| `UTC` | constant | `somnus_debug.doctor.core` | `src/somnus_debug/doctor/core.py:79` | internal | [symbol-index](../13-reference/symbol-index.md) |
| `utc_now` | function | `somnus_debug.doctor.core` | `src/somnus_debug/doctor/core.py:525` | internal | [functions](functions.md) |
| `utc_now_text` | function | `somnus_debug.doctor.core` | `src/somnus_debug/doctor/core.py:530` | internal | [functions](functions.md) |
| `write_text_atomic` | function | `somnus_debug.doctor.core` | `src/somnus_debug/doctor/core.py:2012` | internal | [functions](functions.md) |
| `YamlLine` | dataclass | `somnus_debug.doctor.core` | `src/somnus_debug/doctor/core.py:199` | internal | [types-and-schemas](types-and-schemas.md) |

## Sources

This section lists the code, evidence files, and probes this page rests on.

- [lane-a symbols.tsv](../_evidence/agent-findings/lane-a-arch-api/symbols.tsv), [lane-a ast_enum.py.txt](../_evidence/agent-findings/lane-a-arch-api/ast_enum.py.txt)
- `src/somnus_debug/**/__init__.py` (`__all__`), README.md / docs/MANUAL.md §8 (documented names)
