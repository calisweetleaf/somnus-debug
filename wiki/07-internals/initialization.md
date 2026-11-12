# Initialization

This page records what happens between "the interpreter starts" and "the first file is analyzed", for each entry point. It covers import-time work, the order of setup steps, and setup that happens lazily inside other calls.

## Import time

This section lists what importing each module does, which matters for embedding and for environments without PyYAML.

| Import | Work done at import | Evidence |
|---|---|---|
| `somnus_debug` | defines `__version__` | [SOURCE-CONFIRMED] `src/somnus_debug/__init__.py:57-59` |
| `somnus_debug.doctor.core` | stdlib imports (including `sqlite3`, `concurrent.futures`), builds `DEFAULT_CONFIG_DATA`, compiles nothing else; no I/O, no logging config | [SOURCE-CONFIRMED] `src/somnus_debug/doctor/core.py:49-523` |
| `somnus_debug.structure.core` | stdlib imports only | [SOURCE-CONFIRMED] |
| `somnus_debug.pycache_cleaner.core` | `import yaml`; on `ImportError` prints "PyYAML is required…" to stderr and re-raises. When compiled from source, it also emits `SyntaxWarning: invalid escape sequence '\``' for the docstring at `:64` | [SOURCE-CONFIRMED] `:150-154`; [VERIFIED] warning seen when running from `src/` with `PYTHONDONTWRITEBYTECODE=1` in `/tmp/w1` |
| `somnus_debug.test_harness.scaffold` | stdlib only; templates are read later | [SOURCE-CONFIRMED] |
| `somnus_debug.cli` | imports all four tool modules (`:55-58`), so it inherits the PyYAML requirement; builds `_TOP_LEVEL_HELP` from `__version__` | [VERIFIED] [D-13](../DISCOVERY-LEDGER.md#d-13) |

No module configures logging, opens files, or touches the cwd at import time. [SOURCE-CONFIRMED] module-level statements across `src/somnus_debug/**/*.py`.

## Doctor startup sequence

This section lists the doctor's setup steps in order, with the side effects each one causes.

```
main(argv)                                         src/somnus_debug/doctor/core.py:2184
 1 setup_logging("--verbose" in (argv or sys.argv[1:]))       :2186 -> :2179-2181
     logging.basicConfig(level=DEBUG|INFO, format=..., handlers=[FileHandler("production_doctor.log")], force=True)
 2 build_parser()                                   :2130-2162
 3 parse_args(normalize_argv(argv or sys.argv[1:])) :2188, :2165-2176
 4 args.func(args)  -> run_scan                     :2061
 5   ConfigManager(path|None)                       :782-790
       _load_raw -> deep_merge(DEFAULT_CONFIG_DATA, parsed)
       _validate -> DoctorConfig (frozen)
       config_hash = sha256(dumps_json(raw_config))
 6   StateStore(project_root, config)               :1919-1925   (paths only, no I/O)
 7   if state: previous_file_index() -> initialize()   :1927-1940  (mkdir, PRAGMA WAL, CREATE TABLE x3)
 8   ProjectScanner(project_root, cm)               :1698-1703
       ProjectFileIndex(...)                        :929-935
         _discover(): exists/is_dir checks, os.walk with pruning, sort
         _modules(): module name map
 9   scan(previous) -> first FileAnalyzer.analyze()
```

[SOURCE-CONFIRMED] each line cited. Points that follow from this order:

- Logging is configured before argparse runs. `--help` and usage errors therefore still create `production_doctor.log`. [VERIFIED] `/tmp/w1/help`: `main(['--help'])` left a 0-byte log ([D-10](../DISCOVERY-LEDGER.md#d-10)).
- Configuration is loaded before the project root is checked. A bad config therefore reports exit 4 even when the root is also wrong.
- **State is opened before discovery, so a mistyped root can pass silently.** Step 7 calls `mkdir(parents=True)` on `<root>/.python_doctor/reports` (`:1930`). For a root path that does not exist but is writable, that call creates the root. Discovery then finds an empty directory, and the scan succeeds with 0 files and exit 0. [VERIFIED] `/tmp/w1`:

  | Command | Exit | Result |
  |---|---:|---|
  | `scan ghost/root` | 0 | "Scan complete: files=0"; `ghost/root/` now holds reports and `.python_doctor/` |
  | `scan ghost2/root --no-state` | 4 | "Project root does not exist." |
  | `history ghost3/root` | 0 | "No recorded runs found."; creates `ghost3/root/.python_doctor/` |

  A root that cannot be created (lane-a's `/nonexistent`, under an unwritable `/`) makes the state step fail and fall back to stateless mode, and the scan then exits 4. This is a variant of [D-10](../DISCOVERY-LEDGER.md#d-10) and [D-17](../DISCOVERY-LEDGER.md#d-17) (zero-file scans pass the gate). It has no discovery ID of its own.
- Discovery is eager. All paths are collected and sorted before any analysis starts. Memory use is O(files) for paths, and every result object is held in memory until the reports are rendered.

## Verbose flag initialization

This section reconciles how `-v` and `--verbose` reach the log level. Earlier lanes described this differently.

`setup_logging` receives `"--verbose" in (argv or sys.argv[1:])`. That is a literal string membership test, run before argparse. `-v` is declared by argparse (`:2140`) but never read afterwards. `--verbose` sets the root level to DEBUG, but `doctor/core.py` contains no `logger.debug` call, so the setting has no visible effect. [VERIFIED] [lane-a architecture §3.0](../_evidence/agent-findings/lane-a-arch-api/architecture.md): root level 20 after `-v`, 10 after `--verbose`. Lead reconciliation in WRITING-BRIEF: this account is the canonical one.

Two quirks of the literal test:

- `--verbose` anywhere in argv counts, even as the value of another option.
- `main([])` checks the host's `sys.argv`.

[SOURCE-CONFIRMED] `:2186`.

## Lazy initialization inside other calls

This section lists setup that is deferred until a method first needs it.

| Deferred setup | Triggered by | Evidence |
|---|---|---|
| `.python_doctor/` + schema | every `StateStore` method except `report_paths` | [SOURCE-CONFIRMED] `:1943`, `:1966`, `:1983`, `:1993` |
| stdlib name set | each `ImportResolver.__init__`, which runs once per `FileAnalyzer` | [SOURCE-CONFIRMED] `:998-1001` |
| report output directory | `write_text_atomic` creates parents | [SOURCE-CONFIRMED] `:2015` |
| root logger handler (pycache) | first module-level `logging.*` call when the host has no handler | [VERIFIED] `/tmp/w1`: `[]` → `[StreamHandler <stderr>]` |
| templates | `scaffold` reads them via `importlib.resources` per call | [SOURCE-CONFIRMED] `src/somnus_debug/test_harness/scaffold.py:58-59` |

## Other tools

This section gives the startup order for the three smaller tools.

- **structure**: `_parse_args`, then `read_text`, then `build_index`. No other setup. [SOURCE-CONFIRMED] `src/somnus_debug/structure/core.py:323-332`.
- **pycache-clean**: `parse_args`, config existence check, `from_yaml`, CLI overrides, `setup_logging`, the first `logging.info`, then `PycacheCleaner.__init__` (which normalizes and splits targets into directory names and file patterns), then `run`. Calling `from_yaml` before `setup_logging` is the cause of the silenced-logging defect. [SOURCE-CONFIRMED] `src/somnus_debug/pycache_cleaner/core.py:349-369`; [VERIFIED] [D-14](../DISCOVERY-LEDGER.md#d-14).
- **init-test-harness**: `_parse_args`, then `scaffold`. [SOURCE-CONFIRMED].
- **dispatcher**: `cli.main` handles help and version first. Otherwise it validates the command name and then swaps `sys.argv`. [SOURCE-CONFIRMED] `src/somnus_debug/cli.py:107-125`.

## Sources

This section lists the code, evidence files, and probes this page rests on.

- `src/somnus_debug/doctor/core.py:49-523`, `:782-790`, `:926-992`, `:995-1001`, `:1919-1940`, `:2012-2020`, `:2130-2199`
- `src/somnus_debug/cli.py:55-125`, `src/somnus_debug/pycache_cleaner/core.py:150-154`, `:349-369`, `src/somnus_debug/structure/core.py:323-332`, `src/somnus_debug/test_harness/scaffold.py:58-59`
- [lane-a architecture.md](../_evidence/agent-findings/lane-a-arch-api/architecture.md), [lane-b configuration-findings.md](../_evidence/agent-findings/lane-b-config/configuration-findings.md)
- `../_evidence/agent-findings/WRITING-BRIEF.md` (lead reconciliation of `-v`)
