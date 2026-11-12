# Lane F: extension points in `src/somnus_debug/`

Baseline: commit 034f46e, package 0.1.0. Experiments ran in `/tmp/lane-f/` against a non-editable install of the repo (`repro/s0_setup.sh`). Logs are in `logs/`. Every probe can be rerun with `repro/s5_extension_probes.sh`.

## Verdict

**There is no supported extension mechanism.** The package has no detector registry, no plugin or entry-point discovery, no hooks or callbacks, and no config-driven rule list. A new doctor detector needs either an edit to `doctor/core.py` or a monkeypatch of private internals. A monkeypatch does work, and the probe below proves it, but it is not an API.

What you *can* change without code: thresholds, on/off toggles for some detectors, include and ignore globs, per-category severity, and the exit gate. You cannot change the score weights.

## Evidence

| Question | Answer | Class | Evidence |
|---|---|---|---|
| Plugin or entry-point discovery? | None. The only entry points are the 4 `console_scripts`. No other entry-point group references `somnus_debug`. | VERIFIED | `logs/s5_library_and_links.log` (importlib.metadata scan); `pyproject.toml` `[project.scripts]` |
| Registry, hook, or callback code? | None. Grep for `entry_points\|pkg_resources\|importlib.metadata\|register\|plugin\|hook\|callback\|__subclasses__\|import_module(` over `src/somnus_debug/**/*.py` finds nothing. | VERIFIED | `logs/s5_library_and_links.log` |
| How are detectors wired? | They are hard-coded methods on `CodeQualityVisitor` (`visit_ExceptHandler`, `visit_Call`, `_analyze_function`, `_analyze_class`, `_check_duplicates`, `_check_abstracts`), plus `FileAnalyzer._token_diagnostics` (todos), `_import_diagnostics` (missing and unused imports), and `ProjectScanner._attach_cycles`. `FileAnalyzer.analyze` instantiates `CodeQualityVisitor` by its module-global name. | SOURCE-CONFIRMED | `doctor/core.py:1143-1358`, `:1548-1581`, `:1740-1755`, `:1542` |
| Rule data you could patch | `TODO_PATTERNS`, `PLACEHOLDER_CONSTANTS`, `SECURITY_CALLS` are module-level tuples or frozensets. Nothing reads them from config. | SOURCE-CONFIRMED | `doctor/core.py:500-514` |
| Add a detector without editing core | **Works only by monkeypatch.** Subclass `CodeQualityVisitor`, then rebind `somnus_debug.doctor.core.CodeQualityVisitor`. The new `print_calls` category flowed into the JSON, the Markdown, the summary, the score and the exit gate. `delta.py` handled it generically. | VERIFIED (HYPOTHESIS for stability across versions) | `recipes/ext_custom_detector.py`; `logs/s5_ext.log` X2/X3/X5 |
| Custom category severity | Works through normal config. `parse_severities` accepts **any** category name. A category with no mapping defaults to `minor`. | VERIFIED | `doctor/core.py:769-779`, `:792-794`; `logs/s5_ext.log` X2 (minor, exit 0), X3 (critical, exit 2, score 78) |
| A severity entry for a category no detector emits | Silently accepted and has no effect. | VERIFIED | `logs/s5_ext.log` X4 |
| Remap built-in severities | Works. `stubs: info` turns a stub into an info finding, exit 0, score −1 instead of −8. | VERIFIED | `logs/s5_ext.log` X7 |
| Exit gate | `severity_exit_level` ∈ {critical, serious, minor, info, none}. Exits observed on one serious stub plus minors: critical 0, serious 1, minor 1, info 1, none 0. Gate `minor` with **only an info** finding exits 0. | VERIFIED | `doctor/core.py:2046-2058`; `logs/s5_ext.log` X8; `logs/s6_doc_probes.log` P4 |
| Score customization | Not possible. Weights are hard-coded: `max(0, 100 - 20c - 8s - 2m - i)`. | SOURCE-CONFIRMED | `doctor/core.py:1772` |
| Per-detector toggles | Only `detect_unused_imports`, `detect_security_risks`, `detect_silent_failures`, `detect_dependency_cycles`, and `require_*` (docstrings and hints). `detect_test_gaps` is parsed but nothing reads it. There is **no toggle** for stubs, placeholder_returns, incomplete_methods, short classes or functions, broad_exceptions, complexity, duplicate_definitions or todos. The only lever for those is severity remap plus the gate. | SOURCE-CONFIRMED | `doctor/core.py:829-849` (parsed), usage at `:1222`, `:1229`, `:1574`, `:1631`, `:1299-1303`, `:1408-1419`; no use of `detect_test_gaps` |
| Suppression comments (`# noqa`-style) | None. The only exclusions are `ignore_patterns` (paths), `ignore_functions` and `ignore_classes` (bare names). | SOURCE-CONFIRMED | grep `noqa\|pragma` in `doctor/core.py`: no matches |
| `ignore_functions` semantics | It returns before `generic_visit`, so nested definitions inside an ignored function are hidden too. | VERIFIED | `doctor/core.py:1237-1238`; `logs/s6_doc_probes.log` P5 |
| `ignore_classes` semantics | It suppresses only class-level diagnostics. The class's methods are still fully analyzed. | VERIFIED | `doctor/core.py:1271-1272`; `logs/s6_doc_probes.log` P6 |
| Config typos | Unknown keys (`severity_exit_levle`, `max_complexity`) and a misspelled category (`stubz`) are silently accepted, with no warning. | VERIFIED | `doctor/core.py:726-735` (deep_merge keeps all keys; `_validate` reads known keys only); `logs/s5_ext.log` X6 |
| Library reuse | `ProjectScanner`, `ConfigManager`, `FileAnalyzer`, `CodeQualityVisitor`, `build_index`, `PycacheCleaner`, `CleanerConfig`, `scaffold` are all importable. `scaffold()` returns the written paths. There is no `__all__` beyond `main` and `build_index`, and nothing is marked public or stable. | VERIFIED | `logs/s5_library_and_links.log`; `logs/s4_harness.log` H5; `doctor/__init__.py`, `structure/__init__.py` |

## Side observations surfaced while probing (detector behavior; another lane may own these)

- **`@dataclass(frozen=True)` is not exempt from `suspicious_short_classes`.** The exemption test is `name.endswith("dataclass")` on the unparsed decorator, so `dataclass(frozen=True)` fails it. Plain `@dataclass` is exempt. VERIFIED: `doctor/core.py:1192`; `logs/s5_ext.log` X9. The harness template's own frozen dataclasses trip it (`logs/s4_C5.log` C5a).
- **Findings inside a skipped private function are attributed to the enclosing scope.** At module level that is `<module>`. Private functions are not pushed onto the scope stack but are still visited. This matters for symbol-scoped dispositions. VERIFIED: `doctor/core.py:1239-1241`, `:1352-1354`; `logs/s4_C5.log` C5a (`security_risks`/`silent_failures`/`broad_exceptions` on `<module>` come from `_run_command`/`_setup_logger`).
- **`doctor self-check` writes its reports into the installed package directory** (site-packages). It scans only `doctor/` (2 files). With state enabled it would also create `.python_doctor/` there (SOURCE-CONFIRMED, not run statefully). VERIFIED: `doctor/core.py:2123-2127`; `logs/s4_C8_selfcheck.log`.

## What a real extension point would need (HYPOTHESIS, not present)

The smallest seam would be to read the visitor class (or a list of extra visitors) from `ConfigManager`, or to discover `somnus_debug.detectors` entry points, and pass them into `FileAnalyzer`. Severity already generalizes to arbitrary categories, and `delta.py` is category-agnostic, so downstream would need no change.
