# Module map

This page lists every module in `src/somnus_debug/`, what it owns, what it imports, and what happens when you import it. Use it to decide which module to read or import. The per-file inventory of the whole repository is in [file-index](../13-reference/file-index.md); per-symbol detail is in [symbol-index](../13-reference/symbol-index.md).

## Module table

This section gives one row per module with its responsibility and import-time behavior.

| Module | Lines | Owns | Imports from siblings | `__all__` | Import-time side effects |
|---|---:|---|---|---|---|
| `somnus_debug` | 59 | version string | none | `["__version__"]` | none |
| `somnus_debug.cli` | 128 | `somnus-debug` router, `_SUBCOMMANDS`, `_TOP_LEVEL_HELP` | all four tools, eagerly (`src/somnus_debug/cli.py:55-58`) | none | imports PyYAML through `pycache_cleaner.core` |
| `somnus_debug.doctor` | 45 | re-export | `.core` | `["main"]` | none |
| `somnus_debug.doctor.core` | 2203 | the doctor | stdlib only | none (every module-level name importable) | none |
| `somnus_debug.structure` | 43 | re-export | `.core` | `["build_index", "main"]` | none |
| `somnus_debug.structure.core` | 351 | structure indexer | stdlib only | none | none |
| `somnus_debug.pycache_cleaner` | 43 | re-export | `.core` | `["main"]` | imports PyYAML |
| `somnus_debug.pycache_cleaner.core` | 375 | cleaner | PyYAML, stdlib | none | `import yaml` or print to stderr and re-raise `ImportError` (`:150-154`); a `SyntaxWarning: invalid escape sequence '\`'` from the docstring at `:64` when the source is compiled |
| `somnus_debug.test_harness` | 32 | nothing (metadata header only) | none | none | none |
| `somnus_debug.test_harness.scaffold` | 129 | `scaffold()`, `init-test-harness` CLI | `importlib.resources` on `somnus_debug.test_harness.templates` | none | none |
| `somnus_debug.test_harness.templates` | 32 | resource package marker | none | none | none |
| `templates/run_test.py` | 859 | harness template (data) | n/a, never imported by the package | n/a | n/a |

Line counts: [VERIFIED] `wc -l`. Exports: [VERIFIED] [lane-a api-reference §0](../_evidence/agent-findings/lane-a-arch-api/api-reference.md) (`examples/ex1_exports.py.txt`, exit 0). Import-time effects: [SOURCE-CONFIRMED] cited lines; the SyntaxWarning [VERIFIED] in `/tmp/w1` (stderr of `python3 -m somnus_debug.cli` with `PYTHONDONTWRITEBYTECODE=1`) and in [lane-a architecture §1](../_evidence/agent-findings/lane-a-arch-api/architecture.md).

`test_harness` does not re-export `scaffold`; import it from `somnus_debug.test_harness.scaffold`. [VERIFIED] [lane-a api-reference §0](../_evidence/agent-findings/lane-a-arch-api/api-reference.md).

## Import graph

This section shows which module pulls in which, including the PyYAML edge that makes the dispatcher fragile.

```mermaid
graph TD
  pkg[somnus_debug] 
  cli[somnus_debug.cli] --> pkg
  cli --> dcore[doctor.core]
  cli --> score[structure.core]
  cli --> pcore[pycache_cleaner.core]
  cli --> scf[test_harness.scaffold]
  d[doctor] --> dcore
  s[structure] --> score
  p[pycache_cleaner] --> pcore
  pcore --> yaml[(yaml / PyYAML)]
  scf -. importlib.resources .-> tpl[test_harness.templates]
```

[SOURCE-CONFIRMED] import statements in each file. Consequence: `import somnus_debug.cli` fails without PyYAML, while `import somnus_debug.doctor.core` and `import somnus_debug.structure` succeed. [VERIFIED] [lane-a architecture §1](../_evidence/agent-findings/lane-a-arch-api/architecture.md), [lane-b configuration-findings §1 item 12](../_evidence/agent-findings/lane-b-config/configuration-findings.md); [D-13](../DISCOVERY-LEDGER.md#d-13).

## Console scripts to modules

This section maps each installed command to the function it runs.

| Script | Target | Notes |
|---|---|---|
| `somnus-debug` | `somnus_debug.cli:main` | needs PyYAML for every subcommand |
| `somnus-doctor` | `somnus_debug.doctor.core:main` | stdlib only |
| `somnus-structure` | `somnus_debug.structure.core:main` | stdlib only |
| `somnus-pycache-clean` | `somnus_debug.pycache_cleaner.core:main` | `main()` returns `None`, so success exits 0 |
| (none) | `somnus_debug.test_harness.scaffold:main` | only via `somnus-debug init-test-harness` |

[SOURCE-CONFIRMED] `pyproject.toml` `[project.scripts]`. Full command behavior: [05-cli-and-tools/command-reference](../05-cli-and-tools/command-reference.md).

## Doctor internal map

This section maps the named regions of `doctor/core.py`, the one module large enough to need it.

| Region | Lines | Main symbols |
|---|---|---|
| Aliases, constants | `src/somnus_debug/doctor/core.py:74-83` | `JsonValue`, `ImportKind`, `LOGGER_NAME`, `DEFAULT_CONFIG_NAME`, `RUN_ID_FORMAT`, `COMMANDS` |
| Severity and errors | `:86-196` | `Severity`, `DoctorError`, `ConfigurationError`, `FileReadError`, `ReportGenerationError`, `StateStoreError`, `AnalysisExecutionError` |
| Data model | `:198-448` | `YamlLine`, `DoctorConfig`, `DiagnosticIssue`, `FunctionDiagnostic`, `ClassDiagnostic`, `ImportRecord`, `ImportEdge`, `FileMetrics`, `FileAnalysisResult`, `DependencyGraphResult`, `StateDelta`, `SummaryCounts`, `ProjectAnalysisResult`, `ReportPaths`, `RunRecord` |
| Rule data | `:451-523` | `DEFAULT_CONFIG_DATA`, `TODO_PATTERNS`, `PLACEHOLDER_CONSTANTS`, `SECURITY_CALLS`, `SOMNUS_MARKDOWN_STYLE` |
| Utilities | `:525-595` | `utc_now`, `stable_hash_*`, `to_json_value`, `dumps_json`, `safe_relpath`, `table_escape` |
| YAML subset | `:596-724` | `strip_yaml_comment`, `parse_yaml_scalar`, `MinimalYamlParser` |
| Validation | `:726-924` | `deep_merge`, `require_*`, `parse_severities`, `ConfigManager` |
| Discovery and imports | `:926-1057` | `ProjectFileIndex`, `ImportResolver` |
| Per-file machinery | `:1058-1360` | `SourceReader`, `DiagnosticIssueFactory`, `ImportCollector`, `LoadedNameCollector`, `CodeQualityVisitor` |
| AST predicates | `:1361-1505` | `dedupe_issues`, `body_is_stub`, `placeholder_return_kind`, `handler_is_silent`, `cyclomatic_complexity`, `missing_type_hints`, `dotted_name` |
| Analyzer and graph | `:1507-1693` | `FileAnalyzer`, `DependencyGraphBuilder`, `canonical_cycle`, `mermaid_escape` |
| Orchestration | `:1695-1774` | `ProjectScanner` |
| Reports and state | `:1776-2044` | `MarkdownReportWriter`, `StateStore`, `write_text_atomic`, `copy_file_atomic`, `render_history` |
| CLI | `:2046-2203` | `exit_code_for_summary`, `run_*`, `build_parser`, `normalize_argv`, `setup_logging`, `main` |

[SOURCE-CONFIRMED] `grep -n "^class \|^def "` over the file.

## Sources

This section lists the code, evidence files, and probes this page rests on.

- `src/somnus_debug/**/*.py`, `pyproject.toml`
- [lane-a architecture.md §1](../_evidence/agent-findings/lane-a-arch-api/architecture.md), [lane-a api-reference.md §0](../_evidence/agent-findings/lane-a-arch-api/api-reference.md)
- [lane-b configuration-findings.md](../_evidence/agent-findings/lane-b-config/configuration-findings.md)
