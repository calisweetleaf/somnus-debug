# Lane A: architecture of `somnus_debug` (src/, baseline 034f46e)

Evidence classes follow BRIEF.md. All `file:line` refs are repo-relative under `src/somnus_debug/` unless stated otherwise. "VERIFIED" runs used an isolated venv at `/tmp/lane-a/venv` (`pip install <repo>`, non-editable, Python 3.12.15, PyYAML pulled in as a dependency), with the cwd always inside `/tmp/lane-a/...`. The fixture project is copied here as `fixture/proj/**.py.txt`. The `.txt` suffix keeps it from being scanned as real code if someone runs doctor on the repo; drop the suffix before reusing it.

---

## 1. Module map and boundaries

| Module | Lines | Responsibility | Imports from siblings | Import-time side effects |
|---|---:|---|---|---|
| `__init__.py` | 59 | `__version__ = "0.1.0"`, `__all__ = ["__version__"]` | none | none |
| `cli.py` | 128 | Thin router `somnus-debug <cmd> ...` → each tool's own `main()` | **imports all four tool modules eagerly** (cli.py:55-58) | imports PyYAML transitively through pycache_cleaner |
| `doctor/__init__.py` | 45 | re-exports `main` | `.core` | none |
| `doctor/core.py` | 2203 | The whole doctor: config, discovery, per-file AST analysis, import resolution, dependency graph, scoring, Markdown/JSON reports, SQLite state, CLI | stdlib only (no PyYAML; has its own YAML-subset parser) | none |
| `doctor/default_config.yaml` | 99 | Reference copy of `init-config` output. **Read by no code** (grep finds only `DEFAULT_CONFIG_NAME="python_doctor.yaml"` at core.py:81, used only as `init-config -o` default at core.py:2143) | n/a | n/a |
| `structure/__init__.py` | 43 | re-exports `build_index`, `main` | `.core` | none |
| `structure/core.py` | 351 | AST class/definition index → Markdown text | stdlib only | none |
| `pycache_cleaner/__init__.py` | 43 | re-exports `main` | `.core` | none |
| `pycache_cleaner/core.py` | 375 | Config-driven `__pycache__`/`*.pyc`/`*.pyo` deletion | **hard `import yaml`** (core.py:146-150, prints a message and re-raises ImportError) | SyntaxWarning `invalid escape sequence '\`'` at core.py:64 (docstring), emitted whenever the source is compiled (VERIFIED via `compile()`) |
| `test_harness/__init__.py` | 32 | metadata header only, no code, no `__all__` | none | none |
| `test_harness/scaffold.py` | 129 | Copies `templates/run_test.py` and `CONTRACT.md` into a target dir | `importlib.resources` → `somnus_debug.test_harness.templates` | none |
| `test_harness/templates/__init__.py` | 32 | metadata header only (makes templates a resource package) | none | none |
| `test_harness/templates/run_test.py` | 859 | Data file: the portable single-test harness. Not imported by the package at runtime; only read as text by `_template_text` (scaffold.py:58) | n/a | n/a |

Every `.py` file begins with a `# somnus:metadata:v2 ... # somnus:end` comment block. Some lines in that block look like PEP 484 type comments, for example `#     type: "source-code"`. That matters for `structure` (§4).

**Coupling (SOURCE-CONFIRMED and VERIFIED):** `cli.py` imports every tool at module load. A missing PyYAML therefore breaks *every* `somnus-debug` subcommand, doctor and structure included, even though neither uses YAML. VERIFIED in a `--no-deps` venv (`/tmp/lane-a/venv-noyaml`): `somnus-debug structure --help` and `somnus-debug doctor --help` both exit 1 with `ModuleNotFoundError: No module named 'yaml'`. The standalone `somnus-doctor --help` exits 0, and `import somnus_debug.structure` works. pyproject declares `dependencies = ["pyyaml"]`, so a normal install is unaffected.

Packaging (VERIFIED, `pip show -f`): the wheel ships every `.py` file plus `doctor/default_config.yaml`, `templates/CONTRACT.md` and `templates/run_test.py`. Console scripts: `somnus-debug`, `somnus-doctor`, `somnus-structure`, `somnus-pycache-clean`. There is **no** `somnus-init-test-harness` script; it is reachable only through `somnus-debug init-test-harness`.

---

## 2. `cli.py` dispatcher (somnus-debug)

```
main(argv=None) cli.py:107
  argv = sys.argv[1:] if None
  []/-h/--help        -> print _TOP_LEVEL_HELP, return 0        cli.py:111-113
  -V/--version        -> print __version__, return 0           cli.py:114-116
  unknown             -> stderr help, return 2                 cli.py:119-122
  _run_subcommand(name, rest) cli.py:85
     sys.argv = [prog, *rest]       (mutated; restored in finally, cli.py:97-104)
     doctor/structure/init-test-harness: entry_point(list(argv))
     pycache-clean: entry_point()   <-- SPECIAL CASE cli.py:100
     SystemExit caught -> int(code) if int else 1
     non-int return (pycache main returns None) -> 0
```

* **pycache-clean special case.** `pycache_cleaner.core.main()` takes no argv. Its `parse_args()` (pycache core.py:337) calls `argparse.parse_args()` with no arguments, so it reads `sys.argv`. The dispatcher sets `sys.argv` for it. VERIFIED in-process: `cli.main(["pycache-clean","--config","config.yaml"])` returns 0, and `sys.argv` is restored afterwards (`examples/ex6`, output in api-reference.md §6).
* Exit codes are passed through unchanged from the tools. `SystemExit(None)` maps to 1, not 0 (cli.py:102). `argparse --help` raises `SystemExit(0)` and maps to 0.
* The `--version` short form is `-V` only.

---

## 3. Doctor (`doctor/core.py`): end-to-end call graph

### 3.0 Entry: `main(argv)` core.py:2184

1. `setup_logging("--verbose" in (argv or sys.argv[1:]))` core.py:2186 → core.py:2179-2181: `logging.basicConfig(..., handlers=[FileHandler("production_doctor.log")], force=True)`.
   * **Every call** to `main()` creates or opens `./production_doctor.log` in the **cwd**, including `--help` and argparse errors. (VERIFIED: a 0-byte log appears after a successful scan, because nothing logs on the happy path.)
   * `force=True` **removes the host process's root handlers**. VERIFIED in-process: a host `StreamHandler` was replaced by `FileHandler(production_doctor.log)`, and the root level was set to INFO (examples/ex3).
   * Only the literal `--verbose` is checked. **`-v` is accepted by argparse but has no effect.** VERIFIED: the root level stays 20 after `-v` and becomes 10 after `--verbose`. Doctor contains no `logger.debug` calls anyway (grep). Only `main()` logs (core.py:2192, 2196).
   * If `argv == []`, the `or` falls back to `sys.argv[1:]`.
2. `build_parser()` core.py:2130 defines the subcommands `scan`, `init-config`, `history`, `rollback`, `self-check`. Subparsers are `required=True`.
3. `normalize_argv()` core.py:2165 maps legacy forms: `[]` → `["scan","."]`; first arg starting with `-` (except `-h/--help`) → `["scan",".",*argv]`; first arg not a command → `["scan",*argv]`. VERIFIED: `normalize_argv(["-v"]) == ["scan",".","-v"]`.
4. `args.func(args)` is dispatched under two exception tiers (core.py:2189-2201):
   * `DoctorError` subclasses → `error.render()` to stderr and to the log at ERROR → **exit 4**
   * `OSError, RuntimeError, TypeError, ValueError, sqlite3.Error` → CRITICAL with traceback to the log, rendered to stderr → **exit 5**
   * Anything else (for example `KeyError`, `AttributeError`) is uncaught and produces a raw traceback (exit 1 from the interpreter). SOURCE-CONFIRMED, not triggered.
   * argparse errors → `SystemExit(2)`, **the same code as the "critical gate tripped" result** (VERIFIED: `scan proj --bogus` exits 2).

### 3.1 `scan`: `run_scan(args)` core.py:2061-2093

```
ConfigManager(Path(args.config).resolve() | None)          core.py:782
  _load_raw  core.py:796
     None           -> deep_merge(DEFAULT_CONFIG_DATA, {})   (NO auto-discovery of python_doctor.yaml)
     missing path   -> ConfigurationError (exit 4)
     .json          -> json.loads, root must be object, deep_merge onto defaults
     .yaml/.yml     -> MinimalYamlParser(path).parse()  core.py:646 (native subset parser; PyYAML NOT used)
     other suffix   -> ConfigurationError
  _validate  core.py:816 -> frozen DoctorConfig (core.py:208), require_* helpers core.py:737-779
  config_hash = sha256(dumps_json(raw_config))
StateStore(project_root, config)                            core.py:1916
  state_root = <project_root>/<state_dir=.python_doctor>; db = state.sqlite3; reports_root = state_root/<reports_dir=reports>
if not --no-state:
  store.previous_file_index()  core.py:1942 -> initialize() (mkdir + CREATE TABLEs) -> hashes for the run that alias 'latest' points to
  StateStoreError -> stderr warning, state disabled, scan continues   core.py:2067-2075 (src only; the root python_production_doctor.py lacks this fallback)
ProjectScanner(project_root, cm)                              core.py:1695
  ProjectFileIndex(root, config)                              core.py:926
     _discover core.py:967: os.walk, prune dirs via should_ignore (core.py:937), keep files that pass should_include (core.py:949), sorted by relpath
     _modules  core.py:984: relpath -> dotted module name (pkg/__init__.py -> "pkg")
  .scan(previous) core.py:1705
     run_id = UTC "%Y%m%dT%H%M%SZ" (second resolution) core.py:82/530
     _analyze_files core.py:1716 -> ThreadPoolExecutor(min(max_workers, n_files)); serial path when that is 1
         FileAnalyzer(path).analyze()  core.py:1520   (per file, see 3.2)
         worker exceptions (DoctorError/OSError/RuntimeError/TypeError/ValueError/LookupError) -> _execution_error core.py:1734 = synthetic analysis_read_errors result
         (serial path max_workers==1 has NO such wrapping: an exception escapes to main -> exit 4/5)
     DependencyGraphBuilder(config).build(files) core.py:1625
         local edges only -> _cycles (DFS from each node, path<30, stop at >=100 cycles) core.py:1634-1656
         _mermaid core.py:1658
     _attach_cycles core.py:1740 -> one dependency_cycles issue on the first file of each canonical cycle
     _summary core.py:1764 -> SummaryCounts incl. production_score = max(0, 100 - 20*crit - 8*serious - 2*minor - 1*info)
     _state_delta core.py:1757 -> new/modified/deleted/unchanged vs previous hash index
MarkdownReportWriter(config).render(result) core.py:1783   (CSS <style> + HTML terminal block + tables + mermaid + per-issue evidence)
dumps_json(result)  core.py:578  (to_json_value recursion over dataclasses, sort_keys=True)
store.report_paths(run_id, -o, --json-output) core.py:1955
   markdown_path = -o or <project_root>/production_doctor_report.md
   json_path     = --json-output or markdown_path.with_suffix(".json")
   state copies  = <state>/reports/<run_id>/production_doctor_report.{md,json}; latest.{md,json}
stateless: write_text_atomic(md), write_text_atomic(json)
stateful : store.persist() core.py:1964 -> 6 atomic writes + INSERT OR REPLACE into runs, file_snapshots, report_aliases('latest')
print summary lines; return exit_code_for_summary(summary, gate) core.py:2046
```

**Exit-code decision** `exit_code_for_summary` (core.py:2046-2058), VERIFIED for none, critical and serious:

| gate (`severity_exit_level`) | result |
|---|---|
| `none` | 0 |
| `critical` | 2 if any critical, else 0 |
| `serious` (default) | 2 if any critical, else 1 if any serious, else 0 |
| `minor` | 1 if any critical/serious/minor, else 0 |
| `info` | 1 if any issue, else 0 |

The full process exit-code set is **0, 1, 2 (gate *or* argparse usage error), 4 (DoctorError), 5 (classified runtime error)**, plus an uncaught traceback for unlisted exception types. MANUAL §3.4 only says "non-zero".

**YAML gotcha (VERIFIED):** `severity_exit_level: none` unquoted is parsed as null by `parse_yaml_scalar` (core.py:626-627 maps `none/null/~` to None). `_validate` then rejects it: "Configuration value must be a non-empty string", exit 4. Only `"none"` with quotes works. Flow mappings (`{a: b}`) are kept as a string, which fails `severity_levels must be a mapping`. VERIFIED: `MinimalYamlParser` output for both the repo-root `python_doctor.yaml` and `doctor/default_config.yaml` equals `yaml.safe_load` on every key (diff = {}), and both validate.

### 3.2 Per-file analysis: `FileAnalyzer.analyze()` core.py:1520-1546

1. `SourceReader.read` core.py:1061 (`tokenize.open`, honours the encoding cookie). Read or decode failure → `_read_error` core.py:1583 → `analysis_read_errors`.
2. `_token_diagnostics` core.py:1548: comment tokens matched against `TODO_PATTERNS` (TODO/FIXME/HACK/XXX/TEMP/WIP, case-insensitive, core.py:504) → `todos`. `tokenize.TokenError` → `tokenization_errors`.
3. `ast.parse` → on `SyntaxError` → `syntax_errors` and **early return**: no AST, import or quality checks for that file (core.py:1529-1535). VERIFIED: `broken.py` yields both `syntax_errors` and `tokenization_errors` (2 criticals).
4. `ImportCollector` core.py:1093 collects `import`, `from-import` and literal `__import__`/`importlib.import_module` calls.
5. `ImportResolver.resolve` core.py:1003: relative→absolute (core.py:1018), then local (exact module, then from-import child, then parent prefixes, core.py:1032), then stdlib (`sys.stdlib_module_names`), then third party (`importlib.util.find_spec` in the **doctor's own interpreter**, core.py:1050), else `missing`.
6. `_import_diagnostics` core.py:1566 emits `missing_imports` and `unused_imports` (via `LoadedNameCollector` core.py:1122, which only sees `ast.Name` loads).
7. `CodeQualityVisitor(cm, factory).analyze(tree)` core.py:1160 runs every AST detector (table below), then `_check_duplicates` and `_check_abstracts`, then `dedupe_issues`.
8. `_assemble` core.py:1588: stat, sha256, `FileMetrics` (core.py:1597), plus a `code_map` dict (module name, docstring flag, imports, classes, functions).

### 3.3 Detector table (category → emitting line → predicate)

Severity comes from `config.severity_levels[category]` (default MINOR when absent, core.py:792-794). Evidence is ±(`max_report_evidence_lines`//2) source lines (core.py:1083).

| Category (default severity) | Emitted at | Predicate (source) | Observed behaviour (VERIFIED on fixture unless noted) |
|---|---|---|---|
| analysis_read_errors (critical) | 1585, 1737 | unreadable file / worker exception | not triggered |
| syntax_errors (critical) | 1532, 1535 | `ast.parse` SyntaxError/ValueError | fires |
| tokenization_errors (critical) | 1563 | `tokenize.TokenError` | fires *together with* syntax_errors on an unterminated `def oops(:` |
| missing_imports (serious) | 1571 | edge classification missing/unresolved_relative | fires for `import nonexistent_mod_xyz`. **Does not fire for `from . import ghost` or `from pkg import ghost` when `pkg/__init__.py` exists**: the exact-module match on the package `__init__` wins (core.py:1034-1036) |
| dependency_cycles (serious) | 1747 | DFS over **local** edges | fires for `import pkg.a` ↔ `import pkg.b`. **Misses `from pkg import a` ↔ `from pkg import b`** (both edges resolve to `pkg/__init__.py`). VERIFIED in `/tmp/lane-a/run2`: proj → cycle found, exit 1; proj2 → 0 issues, exit 0 |
| stubs (serious) | 1277, 1288 | `body_is_stub` core.py:1436: single `pass` / `...` / `raise NotImplementedError` | **ignores decorators and base classes**: flags `@abstractmethod ...`, `Protocol` members and every `@overload` stub. VERIFIED (Base.run, Proto.ping, over@59, over@63) |
| placeholder_returns (serious) | 1291 | single `return` of None/False/True/0/-1/""/empty container | fires. Also hits doctor's own `LoadedNameCollector.visit_Import` (`return` used as an intentional no-op) |
| incomplete_methods (serious) | 1336 | same-file subclass of same-file class with `@abstractmethod`/`abstractproperty` | fires (Child) |
| suspicious_short_classes (serious) | 1279 | `_short_class` core.py:1297 | **`@dataclass(frozen=True)` is NOT recognised as a dataclass**: `is_dataclass` tests `name.endswith("dataclass")` on the unparsed decorator text `dataclass(frozen=True)` (core.py:1186). VERIFIED: self-check flags doctor's own frozen dataclasses YamlLine, DependencyGraphResult, StateDelta |
| silent_failures (serious) | 1223 | `handler_is_silent` core.py:1471 | **name-sensitive**: only `logging.error/exception` and `logger.error/exception` count as logging. VERIFIED: `self.log.error(...)` is flagged and `logger.error(...)` is not. Doctor's own `main()` handlers (`logging.getLogger(NAME).error`, then `return 4`) are flagged in self-check, 11 silent_failures in total |
| broad_exceptions (serious) | 1218, 1221 | bare `except`, `except Exception/BaseException` | fires even when the body is a bare `raise` |
| security_risks (serious) | 1230 | dotted call name in `SECURITY_CALLS` (core.py:514) | fires (`eval`). `from subprocess import run; run()` is **not** caught (name-based, SOURCE-CONFIRMED) |
| test_gaps (serious) | — | **none**: configured (core.py:229, 470, 493, 840), never emitted | VERIFIED: no issue on a project with `tests/` |
| todos (minor) | 1559 | comment tokens | fires |
| missing_docstrings (minor) | 1170, 1274, 1284 | docstring length < `min_docstring_length` (18) | fires |
| suspicious_short_functions (minor) | 1293 | executable lines < `min_function_lines` (5) | very noisy: 51 of 78 issues in self-check |
| type_hint_gaps (minor) | 1286 | missing param/return annotations (self/cls exempt) | fires |
| complexity (minor) | 1295 | `cyclomatic_complexity` > 12 (core.py:1423) | boundary is strict `>`; a function scoring exactly 12 is not flagged (fixture `complex_fn`) |
| unused_imports (minor) | 1580 | bound name never loaded as `ast.Name` | **false positives** on `from __future__ import annotations` (every file) and on `__all__` re-exports (e.g. `doctor/__init__.py` `main`). VERIFIED in self-check |
| duplicate_definitions (minor) | 1321 | same name defined at two linenos in one scope | flags **property setters** (`Prop.v`) and `@overload` groups. VERIFIED |

Scope attribution quirk (VERIFIED in self-check): when `check_private_functions=false`, private functions are *not pushed* onto `scope_stack` (core.py:1239-1241). Issues inside them are therefore attributed to the enclosing class or module: a handler inside `ImportResolver._third_party_exists` is reported with symbol `ImportResolver`.

Ordering quirk: `dedupe_issues` sorts by `severity.value` as a string, so alphabetical order is critical < info < minor < serious, not severity rank (core.py:1371). The project-level `issues` are re-sorted by (file, line, category) (core.py:1714).

### 3.4 State store: SQLite (`StateStore`, core.py:1916-2009)

* **Location:** `<scanned project_root>/.python_doctor/state.sqlite3`, `PRAGMA journal_mode=WAL` (VERIFIED: `wal`).
* **Tables** (core.py:1935-1937): `runs(run_id PK, project_root, config_hash, started_at, completed_at, status, files_scanned, total_issues, critical_issues, serious_issues, minor_issues, info_issues, report_md, report_json, report_hash)`, `file_snapshots(run_id, relative_path, file_hash, size_bytes, modified_time, PK(run_id,relative_path))`, `report_aliases(alias PK, run_id, report_md, report_json, updated_at)`. Only alias `latest` is ever written.
* **Run-ID collision (VERIFIED):** `run_id` has one-second resolution and every insert is `INSERT OR REPLACE`. Two scans of the same project within one second leave **one** `runs` row and **one** report directory; the earlier run is silently overwritten. Run3: two back-to-back scans gave `history` = 1 run.
* **history** (`run_history` core.py:2106 → `StateStore.history` core.py:1981): `ORDER BY completed_at DESC LIMIT n`. It calls `initialize()`, so a read-only `history` on a fresh tree **creates `.python_doctor/` and the DB** (VERIFIED, run8). With a broken state dir, `history` exits 4 (no fallback, VERIFIED run7).
* **rollback** (`run_rollback` core.py:2113 → `StateStore.rollback` core.py:1991): copies `<run>/…md/json` over `reports/latest.{md,json}` and repoints alias `latest`. It does **not** touch the project-root `production_doctor_report.md` (VERIFIED: cmp differs). Because `previous_file_index` reads alias `latest`, the **next scan's State Delta is computed against the rolled-back run** (SOURCE-CONFIRMED, core.py:1946-1950). An unknown run-id gives `StateStoreError` and exit 4 (VERIFIED).
* **Fallback:** if `initialize()` fails during scan, there is a warning and the scan stays stateless (VERIFIED run7: `.python_doctor` made a regular file, scan exit 2 with reports written).

### 3.5 `init-config`: `run_init_config` core.py:2096

Writes `ConfigManager.default_yaml()` (core.py:854) atomically to `-o` (default `./python_doctor.yaml` in the cwd). If the file exists and `--force` is not given → `ConfigurationError` → exit 4 (VERIFIED). `doctor/default_config.yaml` = `default_yaml()` **plus comment lines** (byte-equal False, equal after stripping `#` lines: VERIFIED).

### 3.6 `self-check`: `run_self_check` core.py:2123

Scans `Path(__file__).parent`, i.e. the installed `somnus_debug/doctor/` directory, **and writes there**: `self_check_report.{md,json}` (even with `--no-state`) plus `.python_doctor/` state unless `--no-state`. VERIFIED: in the venv this wrote into `site-packages/somnus_debug/doctor/`. Run against the source tree via PYTHONPATH it would write into `src/somnus_debug/doctor/` in the repo, so it was not run that way. Result on 0.1.0: 2 files, 78 issues, 17 serious → exit 1. Relative import `.core` in `doctor/__init__.py` resolves as `missing_imports`, because the package dir is the scan root and `__init__.py` maps to module `""` (core.py:987-989).

### 3.7 On-disk lifecycle (doctor)

| When | What | Where |
|---|---|---|
| every `main()` call | `production_doctor.log` (append) | **cwd** |
| scan (any mode) | `production_doctor_report.md` + `.json` | `-o` path, else **scanned project root** |
| scan (stateful) | `.python_doctor/state.sqlite3`, `reports/<run_id>/production_doctor_report.{md,json}`, `reports/latest.{md,json}` | scanned project root |
| history/rollback | creates `.python_doctor/` + DB if absent | project root |
| init-config | `python_doctor.yaml` | cwd or `-o` |
| self-check | `self_check_report.{md,json}` (+ state) | **the installed doctor package dir** |

Writes go through `write_text_atomic` (core.py:2012: `.<name>.tmp` then `replace`). The `.python_doctor/*` ignore pattern keeps state out of later scans.

**State ownership:** the scanned project owns all state (DB keyed by run_id; `project_root` stored as a column but never filtered on). The cwd owns only the log. Nothing is global or per-user.

---

## 4. `structure` (`structure/core.py`)

`main(argv)` core.py:323 → `_parse_args` core.py:288 → `read_text(utf-8)` → `build_index(source, source_name=--source-label or path, include_lines, include_module_functions)` core.py:202 → stdout, or `-o`/`--update-doc` (mutually exclusive; both just `mkdir -p` the parent and overwrite; `--update-doc` does **not** require an existing file despite its help text, VERIFIED). Exit codes: 0 ok, 2 on OSError/SyntaxError or an argparse error.

`build_index` walks top-level classes (`_render_class` recursion for nested classes), then "Classes nested in functions or other scopes", then module-level functions. Nested functions are never listed. No disk access: a pure function of the string.

**Defect: the structure tool cannot index its own package (VERIFIED).** `ast.parse(..., type_comments=True)` (core.py:210) turns metadata-header comments such as `#     type: "source-code"` into SyntaxErrors. `build_index` fails on **all 16** `.py` files in this repo (12 under src/ plus 4 root scripts). `somnus-debug structure cli.py` → `error: invalid syntax (target.py, line 9)`, exit 2. The root `analyze_python_structure.py` differs from `src/` **only** on that line (diff = 1 changed line pair) and indexes the same file successfully. This contradicts STATE.md's "fixed 2026-11-05" claim **for src/**. The smoke tests `test_structure_tolerates_type_like_comments` and `test_structure_self_index` (tests/test_cli_smoke.py:138, 160) should therefore fail against src (inferred, not executed by this lane). Minimal triggers: `x = [  # type: List[int]\n 1]` and a misplaced `# type:` comment after a statement.

**Defect: double render (VERIFIED).** A class nested inside a class that is itself inside a function (`factory → Local → LocalInner`) is rendered twice: once under `Local` and once in the scoped section. "Definitions emitted" counts it twice (7 reported vs 6 real).

## 5. `pycache-clean` (`pycache_cleaner/core.py`)

`main()` core.py:349 (no argv) → `parse_args()` from `sys.argv` → `--config` default `config.yaml` **in cwd**; missing → `sys.exit(1)` → `CleanerConfig.from_yaml` (core.py:170, PyYAML `safe_load`; unknown keys are warned and ignored; **no type validation**) → CLI overrides → `setup_logging` (core.py:324: `basicConfig` stdout + optional append `log_file`; **no `force`**, so it is a no-op if the host already configured logging) → `PycacheCleaner(cfg)` (core.py:192: `normalize()` mutates cfg in place, resolving roots **relative to the cwd, not the config file**) → `run()` → `_scan_root` (iterative stack; target dirs deleted wholesale, wildcard targets matched against file names with case-sensitive `fnmatchcase`; excludes matched against the **directory basename** only) → summary log. Any exception → `logging.exception` + `sys.exit(1)`. Returns None, which the dispatcher maps to 0.

* **Hazard (VERIFIED at the normalize level only; never run):** `roots` given as a YAML scalar string (`roots: /some/path`) is iterated character by character. `CleanerConfig(roots="/tmp/lane-a/lib/ex5/tree")` normalizes to `['/', '<cwd>/t', '<cwd>/m', ...]` (24 roots, including filesystem `/`). A live run with such a config would sweep `__pycache__` across the whole filesystem.
* Dry run still increments counters and logs "Summary: **deleted** N directories". Byte counts are real sizes (VERIFIED).
* `max_depth=1` leaves `b/c/d/__pycache__` (depth 3) in place (VERIFIED).
* The module docstring promises "Windows long path support: Paths are normalized to the `\\?\` namespace". **No such code exists** (grep finds only the docstring). DISCREPANCY.
* The upper-case `STRAY.PYC` is not removed (case-sensitive match, VERIFIED).

## 6. `init-test-harness` (`test_harness/scaffold.py`)

`main(argv)` scaffold.py:112 → `_parse_args` (target default `.`, `--force`, `--no-contract`) → `scaffold(target, force, with_contract)` scaffold.py:62. The function resolves the target, refuses (raising `FileExistsError` **before writing anything**) if any destination exists and force is not set, creates the dir with `mkdir -p`, writes `run_test.py` (+ `CONTRACT.md`) from package resources, and returns the written paths. `main` maps FileExistsError to exit 1 and success to 0. VERIFIED for all paths.

Scaffolded `run_test.py` (template, 859 lines):
* **Not agnostic as shipped (VERIFIED):** `TEST_NAME = "GOLDEN PATH LAYER 1 DATA HIGHWAY RESTORATION"`, and `execute_test()` runs `cargo metadata` / `cargo build -p gp-cli` (a leftover from another project). Run unedited, it FAILs with `FileNotFoundError: 'cargo'`.
* **Default placement puts artifacts outside the repo (VERIFIED):** `project_root = Path(__file__).resolve().parent.parent` (template main). `init-test-harness` defaults to writing into `.` (the repo root), so `project_root` becomes the repo's *parent*, and artifacts land in `<parent>/test-runs/<RUN_ID>/`. Scaffolding into a subdir (e.g. `repo/single_test/`) gives `repo/test-runs/`. CONTRACT.md says "Copy this directory into the repository", so the scaffold default and the template's assumption disagree.
* Artifacts: `test-runs/<SLUG>-<YYYYmmdd-HHMMSS>-<6hex>/{test.log, manifest.json, report.md}`. `SINGLE_TEST_OUTPUT_DIR` and `PROJECT_ROOT` env overrides are honoured. A JSON summary goes to stdout and logs to stderr. Exit 0 = PASS, 1 = FAIL. `mkdir(exist_ok=False)` per run.

---

## 7. Root duplicates vs src (diff with metadata headers stripped)

| root file | src twin | changed lines |
|---|---|---:|
| python_production_doctor.py | doctor/core.py | 17 (src adds the SQLite-unavailable fallback in run_scan; root raises instead) |
| analyze_python_structure.py | structure/core.py | 2 (root: `ast.parse(source, filename=...)`; src adds `type_comments=True`) |
| pycache_cleaner.py | pycache_cleaner/core.py | 0 |
| run_test.py | templates/run_test.py | 0 |

## 8. Repo hygiene note

`src/somnus_debug/**/__pycache__/` directories exist in the repo tree, with mtime 2026-11-12 00:12:03Z. They are gitignored (git status shows only `wiki/`). The timestamp coincides with this lane's `pip install <repo>` and also possibly with another lane's PYTHONPATH runs. Origin UNVERIFIED. Not deleted, per the BRIEF.
