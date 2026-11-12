# Lane C: programmatic API reference for `somnus_debug` 0.1.0

The full symbol inventory is in `symbols.tsv` (256 symbols, produced by `ast_enum.py.txt`). This file covers the callables that are public or practically usable. Runs used `/tmp/lane-a/venv` (pip-installed from the repo) with cwd under `/tmp/lane-a/lib`. The example scripts are in `examples/*.py.txt`.

## 0. Export surface (VERIFIED: `examples/ex1_exports.py.txt`, exit 0)

| Import path | `__all__` | All names resolve |
|---|---|---|
| `somnus_debug` | `["__version__"]` → `"0.1.0"` | yes |
| `somnus_debug.cli` | none | n/a |
| `somnus_debug.doctor` | `["main"]` | yes |
| `somnus_debug.structure` | `["build_index", "main"]` | yes |
| `somnus_debug.pycache_cleaner` | `["main"]` | yes |
| `somnus_debug.test_harness` | none (empty module, header only) | n/a; `scaffold` is **not** re-exported |
| `somnus_debug.test_harness.templates` | none (resource package) | n/a |
| `*.core`, `test_harness.scaffold` | none | everything module-level is importable |

`import somnus_debug.cli` imports PyYAML (`"yaml" in sys.modules` → True). Without PyYAML, every `somnus-debug` subcommand fails (see architecture.md §1).

The README and MANUAL §8 name `build_index`, `ProjectScanner`, `ConfigManager`, `DoctorConfig`, `PycacheCleaner`, `CleanerConfig` and `scaffold` as library entry points, with **no signatures, return types or side-effect notes**.

---

## 1. Doctor: `somnus_debug.doctor.core`

### Entry point
`main(argv: Sequence[str] | None = None) -> int` (core.py:2184; re-exported; console script `somnus-doctor`)
* Returns 0/1/2 (gate), 4 (DoctorError) or 5 (classified runtime error). argparse errors and `--help` **raise SystemExit** (2/0); they do not return.
* Side effects: creates `./production_doctor.log` in the cwd; `logging.basicConfig(force=True)` **replaces the caller's root handlers** (VERIFIED, ex3); prints to stdout/stderr; writes reports and state (architecture.md §3.7). Does not mutate `sys.argv`.

### Configuration
* `ConfigManager(config_path: Path | None)` (core.py:782). Attributes: `.config: DoctorConfig`, `.raw_config: dict`, `.config_hash: str` (sha256 hex), `.config_path`. Method `.severity(category) -> Severity` (unknown → `Severity.MINOR`). Static `ConfigManager.default_yaml() -> str`. Raises `ConfigurationError` for a missing path, a bad suffix, malformed JSON/YAML-subset, or a failed type check. `None` means built-in defaults; there is no file discovery.
  VERIFIED (ex2): `ConfigManager(None)` → `config_hash ff1bdc11340bc602…`, `severity_exit_level 'serious'`, `max_workers 4`.
* `DoctorConfig` (frozen dataclass, core.py:208): 29 fields (see `symbols.tsv`, or `DEFAULT_CONFIG_DATA` core.py:451). `severity_levels: Mapping[str, Severity]`.
* `MinimalYamlParser(path).parse() -> dict` (core.py:646). Stdlib-only YAML subset: block mappings and sequences, inline `[a, b]`, quoted scalars via `ast.literal_eval`, int/float/bool/null (`null|none|~`, case-insensitive). No flow mappings, anchors, multi-docs or block scalars. Raises `ConfigurationError` with line numbers.
  VERIFIED (ex3): identical to `yaml.safe_load` on the repo's `python_doctor.yaml` and `default_config.yaml`. `severity_exit_level: none` → `{'severity_exit_level': None}`; `{stubs: minor}` → kept as a string.
* `deep_merge(base, override) -> dict` (core.py:726), non-mutating. `parse_severities(raw) -> Mapping[str, Severity]`. `require_bool/int/str/str_tuple`.

### Scanning
* `ProjectScanner(project_root: Path, config_manager: ConfigManager)` (core.py:1695). The constructor **walks the tree immediately** (`ProjectFileIndex`) and raises `AnalysisExecutionError` if the root is missing or not a directory.
  `.scan(previous_index: Mapping[str, str]) -> ProjectAnalysisResult`. Pass `{}` for a stateless delta. **Writes nothing to disk and installs no logging** (VERIFIED, ex2: no new files; root handlers `[]`; no log file).
* `ProjectAnalysisResult` (frozen): `run_id, project_root, started_at, finished_at, config_hash, summary: SummaryCounts, files: tuple[FileAnalysisResult], issues: tuple[DiagnosticIssue], dependency_graph: DependencyGraphResult, state_delta: StateDelta`. JSON top-level keys VERIFIED: `config_hash, dependency_graph, files, finished_at, issues, project_root, run_id, started_at, state_delta, summary`.
* `SummaryCounts`: `files_scanned, total_issues, critical_issues, serious_issues, minor_issues, info_issues, syntax_error_files, missing_imports, dependency_cycles, suspicious_short_classes, suspicious_short_functions, production_score`.
* `DiagnosticIssue`: `category, severity: Severity, file_path (relative POSIX), line_number, column_offset, symbol, message, evidence (numbered source excerpt; "" for read/cycle/worker issues), remediation, details: dict`; `.identity() -> str`.
* `FileAnalyzer(path, index: ProjectFileIndex, config_manager).analyze() -> FileAnalysisResult` (core.py:1507). Analyzes one file; needs a `ProjectFileIndex` for import resolution. `FileAnalysisResult` adds `file_hash, size_bytes, modified_time, syntax_valid, metrics: FileMetrics, imports, import_edges, functions: tuple[FunctionDiagnostic], classes: tuple[ClassDiagnostic], code_map: dict`.
* `ProjectFileIndex(project_root, config)` (core.py:926): `.python_files`, `.module_to_file`, `.file_to_module`, `.should_ignore(path)`, `.should_include(path)`, `.module_for_file(path)`, `.resolve_local_module(name)`.
* `ImportResolver(index).resolve(source_path, ImportRecord) -> ImportEdge` (classification ∈ `local|standard_library|third_party|missing|unresolved_relative`, with a confidence of 1.0/0.95/0.85/0.9/0.2). Third-party detection uses `importlib.util.find_spec` **in the doctor's own interpreter**, so results depend on which venv runs the doctor.
* `DependencyGraphBuilder(config).build(files) -> DependencyGraphResult(nodes, edges, missing_imports, cycles, mermaid)`.
* Rendering: `MarkdownReportWriter(config).render(result) -> str`. `dumps_json(obj, *, indent=2) -> str` (sorted keys, Enum → value, Path → str, datetime → `...Z`). `to_json_value(obj)`.
* Gate: `exit_code_for_summary(summary, gate: str) -> int`. Unknown gate → 1.

**Example A: programmatic scan, no CLI, no disk writes (VERIFIED, `examples/ex2_doctor_lib.py.txt`, exit 0)**
```python
from pathlib import Path
from somnus_debug.doctor.core import ConfigManager, ProjectScanner, MarkdownReportWriter, dumps_json, exit_code_for_summary, FileAnalyzer, ProjectFileIndex
cm = ConfigManager(None)
res = ProjectScanner(Path("ex2/proj"), cm).scan({})
```
Captured output:
```
config_hash ff1bdc11340bc602 gate serious workers 4
ProjectAnalysisResult run_id 20261112T001410Z files 6 issues 37 crit 2 serious 13 score 0
first issue: unused_imports pkg/a.py 3 Severity.MINOR
exit code (gate=serious): 2 (gate=critical): 2
md chars 27421 json chars 89657 md starts with <style>: True
index modules: ['pkg', 'pkg.a', 'pkg.b', 'pkg.broken', 'pkg.todo_mod', 'tests.test_nothing']
single-file: pkg/a.py syntax_valid True issues ['unused_imports', 'unused_imports', 'missing_imports', 'unused_imports']
edges: [('os', 'standard_library', ''), ('json', 'standard_library', ''), ('nonexistent_mod_xyz', 'missing', ''), ('pkg', 'local', 'pkg/__init__.py'), ('pkg', 'local', 'pkg/__init__.py')]
files written under ex2: []
cwd log exists: False root handlers: []
```
(The last edge pair shows the masking defect: `from pkg import b` and `from . import missing_sibling` both resolve to `pkg/__init__.py`.)

**Example B: `main()` in-process side effects (VERIFIED, `examples/ex3_side_effects.py.txt`)**
```
host handlers before: [<StreamHandler <stderr> (NOTSET)>]
main() returned 2
host handlers after: [<FileHandler /tmp/lane-a/lib/ex3/production_doctor.log (NOTSET)>] level 20
cwd files: [..., 'out', 'production_doctor.log', ...]   out: ['r.json', 'r.md']
normalize_argv: ['scan', '.'] ['scan', 'proj'] ['scan', '.', '-v'] ['history']
```
For embedding, call `ProjectScanner` directly (Example A), not `main()`.

### State
`StateStore(project_root, config)` (core.py:1916): `.initialize()` (mkdir + schema), `.previous_file_index() -> {relpath: sha256}`, `.report_paths(run_id, output, json_output) -> ReportPaths`, `.persist(result, md, json_text, paths)`, `.history(limit) -> tuple[RunRecord]`, `.rollback(run_id) -> RunRecord`. All raise `StateStoreError`. Every method except `report_paths` creates `.python_doctor/` under the project root. `render_history(records) -> str`. `write_text_atomic(path, text)` raises `ReportGenerationError`; `copy_file_atomic(src, dst)` raises `StateStoreError`.

### Errors (core.py:95-193)
`DoctorError(RuntimeError)` with `.message`, `.remediation`, `.context`, `.render() -> str`. Subclasses `ConfigurationError`, `FileReadError`, `ReportGenerationError`, `StateStoreError`, `AnalysisExecutionError`, each with its own default remediation text. Note that `run_init_config` passes `{"remediation": ...}` inside `context`, so the rendered Remediation line shows the class default ("Fix the configuration file…") and not "Use --force" (VERIFIED in stderr).

### AST helper primitives (pure functions)
`cyclomatic_complexity(node) -> int`, `body_is_stub(body) -> bool`, `placeholder_return_kind(body) -> str`, `handler_is_silent(ExceptHandler) -> bool`, `dotted_name(node) -> str`, `missing_type_hints(fn, config) -> tuple[str]`, `executable_line_count(body)`, `body_without_docstring(body)`, `function_argument_count(fn)`, `meaningful_doc(node, min_len)`, `is_private_function(name)`, `canonical_cycle(seq)`, `mermaid_escape(s)`, `dedupe_issues(iter)`, `stable_hash_text/file`, `safe_relpath`, `table_escape`, `strip_yaml_comment`, `parse_yaml_scalar`, `utc_now/utc_now_text/isoformat_utc`. Visitors: `ImportCollector`, `LoadedNameCollector`, `CodeQualityVisitor(cm, DiagnosticIssueFactory)`.

---

## 2. Structure: `somnus_debug.structure` (exported)

`build_index(source: str, *, source_name: str, include_lines: bool = True, include_module_functions: bool = True) -> str` (core.py:202). Pure: no I/O and nothing is imported or executed. Raises `SyntaxError`, **including on any file with PEP-484-looking comments, because of `type_comments=True` (core.py:210)**. That covers every file in this repo.
`main(argv: Sequence[str] | None = None) -> int` (core.py:323): 0 ok, 2 on OSError/SyntaxError; argparse errors raise SystemExit(2). Writes to stdout or `-o`/`--update-doc` (creates parent dirs).

**Example C (VERIFIED, `examples/ex4_structure.py.txt`, exit 0)**: indexing a 20-line string with nested and function-scoped classes produced this (excerpt):
```
- Class declarations: 4 (1 top-level, 3 nested)
- Definitions emitted (module-level functions and class methods): 7
## class `Outer` (lines 2-10)
**Doc**: Outer doc paragraph.
- `def m(a: dict[str, int]) -> None:` (lines 7-8)
  - Decorator: `staticmethod`
...
## Classes nested in functions or other scopes
### class `Local` (lines 12-15)
### class `LocalInner` (lines 13-14)     <- rendered once (correct)
### class `LocalInner` (lines 13-14)     <- rendered again (defect; count 7 should be 6)
## Module-level functions
- `def factory():` (lines 11-17)
- `async def go(*a, **k) -> int:` (lines 18-19)
build_index failures over repo .py files: [16 of 16 files: 'invalid syntax' at line 9/10]
'x = [  # type: List[int]\n 1]\n' build_index: SyntaxError | plain ast.parse: ok
```

---

## 3. Pycache cleaner: `somnus_debug.pycache_cleaner.core`

* `CleanerConfig` (mutable dataclass, core.py:158): `roots: list[str]=[]`, `exclude: list[str]=[]`, `targets=["__pycache__","*.pyc","*.pyo"]`, `dry_run=False`, `verbose=False`, `max_depth: int|None=None`, `follow_symlinks=False`, `log_file: str|None=None`. `CleanerConfig.from_yaml(path)` (static; PyYAML; no type checks; unknown keys go through `logging.warning`). `.normalize()` mutates in place, resolving against the **cwd**.
* `PycacheCleaner(config)` (core.py:189): the constructor calls `config.normalize()` (it **mutates the caller's config**) and raises `ValueError("No roots specified in configuration.")` when there are no roots. `.run() -> None` logs through the **root logger** (`logging.info/debug`). Results are only available as attributes: `.deleted_dirs`, `.deleted_files`, `.deleted_bytes`. Missing roots are logged as errors and skipped, never raised.
* `setup_logging(cfg)` (basicConfig without force), `parse_args()` (reads `sys.argv`), `main() -> None` (exits through `sys.exit(1)` on errors).

**Example D (VERIFIED, `examples/ex5_pycache.py.txt`, exit 0; temp tree only)**
```
dry run returned None dirs 2 files 1 bytes 0 unchanged: True
cfg.roots after normalize (mutated in place): ['/tmp/lane-a/lib/ex5/tree']
live max_depth=1: dirs 1 files 1 remaining: [..., 'b/STRAY.PYC', ..., 'b/c/d/__pycache__/z.pyc', ..., 'node_modules/__pycache__/y.pyc']
roots='/tmp/...' (str) normalizes to: ['/', '/tmp/lane-a/lib/t', '/tmp/lane-a/lib/m', '/tmp/lane-a/lib/p', '/', '/tmp/lane-a/lib/l'] ... count 24
no roots -> ValueError No roots specified in configuration.
```
The string-roots result is a safety hazard: `/` becomes a root. Only the constructor was called; `run()` was never invoked on it.

---

## 4. Test-harness scaffold: `somnus_debug.test_harness.scaffold`

* `scaffold(target_dir: Path, *, force: bool = False, with_contract: bool = True) -> list[Path]` (scaffold.py:62). Returns the absolute written paths. Raises `FileExistsError` (and writes nothing) if any destination exists and force is not set. Creates `target_dir` with `mkdir -p`.
* `_template_text(name) -> str`: reads `run_test.py` or `CONTRACT.md` from package resources.
* `main(argv=None) -> int`: 0 ok, 1 on refusal.

**Example E (VERIFIED, `examples/ex7_scaffold.py.txt`, exit 0)**
```
scaffold returned: ['/tmp/lane-a/lib/ex7/repo/run_test.py', '/tmp/lane-a/lib/ex7/repo/CONTRACT.md']
no-contract returned: ['/tmp/lane-a/lib/ex7/repo/single_test/run_test.py']
FileExistsError: refusing to overwrite existing file(s) without --force: /tmp/lane-a/lib/ex7/repo
forced: 2
template TEST_NAME line: ['TEST_NAME = "GOLDEN PATH LAYER 1 DATA HIGHWAY RESTORATION"']
template invokes cargo: True
```
Running the scaffolded file unedited: `repo/run_test.py` → exit 1, FAIL (`FileNotFoundError: 'cargo'`), artifacts in **`ex7/test-runs/`, outside the repo**. `repo/single_test/run_test.py` → FAIL, artifacts in `ex7/repo/test-runs/`.

Template API (copied, not imported): `Check(name, passed, detail="", expected=None, observed=None)` (frozen), `TestOutcome(summary, checks, metrics={}, evidence={}, notes=[])` with `.passed` = non-empty and all checks pass, `TestContext(run_id, project_root, artifact_dir, logger)`, `_run_command(cmd, *, cwd, logger, expected=0) -> CompletedProcess` (raises RuntimeError on an unexpected exit), `SCHEMA_VERSION = "1.0"`, `main() -> int` (0 PASS / 1 FAIL).

---

## 5. Dispatcher: `somnus_debug.cli`

`main(argv: Sequence[str] | None = None) -> int`. `_run_subcommand(name, argv) -> int` temporarily sets `sys.argv = [prog, *argv]`, converts SystemExit to an int, and maps a non-int return to 0. `_SUBCOMMANDS` is a dict mapping each command to `(prog, callable)`.

**Example F (VERIFIED, `examples/ex6_cli.py.txt` (run from /tmp/lane-a/lib/ex6), exit 0)**
```
pycache-clean (dry) -> 0        sys.argv restored: True
pycache-clean missing cfg -> 1
structure -> 0                  (non-metadata file)
init-test-harness -> 0 ; again -> 1
unknown -> 2
```

---

## 6. CLI runs (VERIFIED; cwd /tmp/lane-a/run*, exit codes as observed)

| Command | Exit | Note |
|---|---:|---|
| `somnus-debug doctor scan proj` (fixture) | 2 | 6 files, 37 issues, 2 critical, 13 serious |
| `doctor init-config -o cfg.yaml` / again | 0 / 4 | |
| `doctor scan proj -c nope.yaml` / `-c c.toml` / bad gate | 4 / 4 / 4 | |
| `-c` with unquoted `severity_exit_level: none` | 4 | parsed as null |
| `-c` with quoted `"none"` / `critical` | 0 / 2 | |
| `doctor scan proj --bogus` | 2 | argparse; same code as the critical gate |
| `doctor scan /nonexistent` | 4 | AnalysisExecutionError |
| `doctor` (no args, empty dir) | 0 | scans `.`, writes reports + state into cwd |
| `doctor history proj` after 2 same-second scans | 0 | **1 run listed** (collision) |
| `doctor rollback proj --run-id <first>` / `NOPE` | 0 / 4 | the project-root report is not rolled back |
| `doctor self-check` (venv) | 1 | writes into site-packages |
| `doctor scan proj` with `.python_doctor` as a regular file | 2 | warning, stateless fallback; `history` → 4 |
| `somnus-debug structure <metadata-stamped file>` | 2 | `invalid syntax (…, line 9)` |
| root `analyze_python_structure.py` on the same file | 0 | |
| `somnus-structure plain.py --update-doc newdir/idx.md` | 0 | creates a new file and dir |
| `somnus-debug --version` / `bogus` | 0 / 2 | |
| `somnus-debug {structure,doctor} --help` without PyYAML | 1 / 1 | |
