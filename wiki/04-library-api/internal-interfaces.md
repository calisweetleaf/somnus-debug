# Internal interfaces

This page documents the seams inside the package where you can subclass, substitute, or patch behavior. None of them is a supported extension API: the package has no registry, plugin discovery, or hooks ([D-19](../DISCOVERY-LEDGER.md#d-19)). Each seam below is labeled with how it works and what breaks it. For the extension story as a whole, see [08-extensions/extension-overview](../08-extensions/extension-overview.md).

## How the doctor finds its collaborators

This section explains the one mechanism that makes most seams possible: module-global name lookup at call time.

`FileAnalyzer.analyze` creates `CodeQualityVisitor(...)`, `ImportCollector()`, and `DiagnosticIssueFactory(...)` by their module-global names on every call (`src/somnus_debug/doctor/core.py:1527`, `:1537`, `:1542`). `FileAnalyzer.__init__` does the same for `SourceReader()` and `ImportResolver(index)` (`:1517-1518`). `ProjectScanner` looks up `FileAnalyzer` and `DependencyGraphBuilder` the same way (`:1721-1725`, `:1710`). Rebinding a name in `somnus_debug.doctor.core` therefore changes the behavior of every scan that starts afterwards, in the whole process. [SOURCE-CONFIRMED]

Rule data works the same way. `SECURITY_CALLS`, `TODO_PATTERNS`, and `PLACEHOLDER_CONSTANTS` are module globals read at call time (`:1229`, `:1557`, `:1458`). [SOURCE-CONFIRMED]

## CodeQualityVisitor: subclass and rebind

This section shows the only seam that adds a new detector without editing the source.

Contract, read from the source (`src/somnus_debug/doctor/core.py:1143-1358`):

- **Constructor.** `(config_manager, issue_factory)`. Call `super().__init__`.
- **Emit.** Append to `self.issues` using `self.issue_factory.create(category, line, column, symbol, message, remediation, details)`. Severity comes from `config.severity_levels[category]`, and falls back to `minor`.
- **Visiting.** Override `visit_*` methods. Call `super().visit_X(node)`, or `self.generic_visit(node)`, so that the stock detectors and child traversal still run.
- **Context.** `self.scope_stack`, `self._current_symbol()`, `self._qualname(name)`, and `self.config` are available.
- **Return.** `analyze(tree)` returns `(issues, functions, classes)` after `_check_duplicates`, `_check_abstracts`, and `dedupe_issues`.

```python
import ast
from pathlib import Path
from somnus_debug.doctor import core

class PrintCallVisitor(core.CodeQualityVisitor):
    def visit_Call(self, node: ast.Call) -> None:
        if core.dotted_name(node.func) == "print":
            self.issues.append(self.issue_factory.create(
                "print_calls", node.lineno, node.col_offset, self._current_symbol(),
                "print() call in library code.", "Use the module logger.", {"call": "print"}))
        super().visit_Call(node)

core.CodeQualityVisitor = PrintCallVisitor   # rebind the module global
res = core.ProjectScanner(Path("ext"), core.ConfigManager(None)).scan({})
```

Executed: yes (`/tmp/w1/ex_ext.py`, one-file project `ext/m.py` containing one `print`, exit 0):

```
before ['suspicious_short_functions']
after  [('suspicious_short_functions', 'minor', 'shout'), ('print_calls', 'minor', 'shout')] score 96
```

The new category flowed into the summary and the score. It defaulted to `minor` because the default `severity_levels` does not map it. Add `print_calls: "serious"` to a config's `severity_levels` to gate on it. Lane F verified the same pattern end to end through `main`, JSON, Markdown, and `delta.py`. [VERIFIED] [lane-f extensions](../_evidence/agent-findings/lane-f-ext/extensions.md), recipe `recipes/ext_custom_detector.py`.

Risks:

- The rebinding is process-wide and not thread-scoped.
- Private members such as `_current_symbol`, `scope_stack`, and `issue_factory` can change without notice.
- Detectors that need cross-file context do not fit here. The visitor sees one file; cross-file checks belong after the scan, the way `ProjectScanner._attach_cycles` works.

[HYPOTHESIS] for stability across versions.

## Patching rule data

This section covers changing what existing detectors match without writing a detector.

```python
core.SECURITY_CALLS = core.SECURITY_CALLS | {"print"}
```

Executed: yes (same script). The next scan reported `security_risks` for the `print` call: categories `['print_calls', 'security_risks', 'suspicious_short_functions']`.

Patchable globals: `SECURITY_CALLS` (frozenset of dotted call names), `TODO_PATTERNS` (tuple of `(regex, label)`), `PLACEHOLDER_CONSTANTS`, `DEFAULT_CONFIG_DATA` (affects `ConfigManager(None)`), and `SOMNUS_MARKDOWN_STYLE`. [SOURCE-CONFIRMED] Matching stays name-based. `from subprocess import run; run()` is still not caught as `subprocess.run`. [SOURCE-CONFIRMED] [lane-a architecture §3.3](../_evidence/agent-findings/lane-a-arch-api/architecture.md).

## Other substitution points

This section lists the remaining seams, what each controls, and the contract to keep.

| Seam | Location | Use | Contract to keep |
|---|---|---|---|
| `DiagnosticIssueFactory` | `src/somnus_debug/doctor/core.py:1070-1090` | change evidence windows or tag issues | `create(...) -> DiagnosticIssue` with the same positional arguments |
| `ImportResolver` / `ImportResolver._third_party_exists` | `:995-1055` | resolve imports against another environment instead of the doctor's interpreter (the root of [D-26](../DISCOVERY-LEDGER.md#d-26)) | `resolve(path, record) -> ImportEdge`; classification must be one of the five `ImportKind` values, because `_import_diagnostics` and `DependencyGraphBuilder` key on them |
| `SourceReader` | `:1058-1067` | in-memory sources, or a different decoding policy | `read(path) -> str`, raising `FileReadError` on failure |
| `ProjectFileIndex` | `:926-992` | custom discovery, for example from `git ls-files` | `python_files`, `module_to_file`, `file_to_module`, `module_for_file`, `resolve_local_module`, `project_root`. `ProjectScanner.__init__` constructs it by name |
| `DependencyGraphBuilder` | `:1618-1679` | other cycle semantics | `build(files) -> DependencyGraphResult` |
| `MarkdownReportWriter` | `:1776-1913` | a different report format | `render(result) -> str`; subclass and override `_header`, `_summary`, and the other section methods |
| `StateStore` | `:1916-2009` | another storage backend | methods used by `run_scan`: `previous_file_index`, `report_paths`, `persist`; by history and rollback: `history`, `rollback` |
| `exit_code_for_summary` | `:2046-2058` | custom gates | `(SummaryCounts, str) -> int` |
| `cli._SUBCOMMANDS` | `src/somnus_debug/cli.py:60-65` | add a subcommand to `somnus-debug` in-process | `name -> (prog, callable(argv) -> int)`; `pycache-clean` is special-cased by name at `:100` |
| `scaffold._template_text` / `_TEMPLATE_FILES` | `src/somnus_debug/test_harness/scaffold.py:55-59` | ship a different template | `name -> str` |

[SOURCE-CONFIRMED] every row. Only the `CodeQualityVisitor` and `SECURITY_CALLS` seams were executed for this page. The others follow from the same name-lookup mechanism. [HYPOTHESIS] for each untested seam.

## Seams that do not exist

This section lists the extension points a reader might expect, which the code does not have.

- No detector registry, entry-point group, or plugin loader. [VERIFIED] grep and `importlib.metadata` scan in [lane-f extensions](../_evidence/agent-findings/lane-f-ext/extensions.md).
- No suppression comments (`# noqa`, `# pragma`). [SOURCE-CONFIRMED]
- No configurable score weights. They are hard-coded at `:1772`. [SOURCE-CONFIRMED]
- No per-detector toggle for stubs, placeholder returns, incomplete methods, short classes and functions, broad exceptions, complexity, duplicates, or TODOs. The only lever is a severity remap plus the gate. [SOURCE-CONFIRMED] [lane-f extensions](../_evidence/agent-findings/lane-f-ext/extensions.md).
- No callback or progress reporting during a scan. [SOURCE-CONFIRMED]

## Sources

This section lists the code, evidence files, and probes this page rests on.

- `src/somnus_debug/doctor/core.py:926-1358`, `:1507-1546`, `:1618-1774`, `:1776-2058`
- `src/somnus_debug/cli.py:60-104`, `src/somnus_debug/test_harness/scaffold.py:55-59`
- [lane-f extensions.md](../_evidence/agent-findings/lane-f-ext/extensions.md), [lane-f recipes/ext_custom_detector.py](../_evidence/agent-findings/lane-f-ext/recipes/ext_custom_detector.py)
- [lane-a architecture.md](../_evidence/agent-findings/lane-a-arch-api/architecture.md)
- Executed probe: `/tmp/w1/ex_ext.py`
