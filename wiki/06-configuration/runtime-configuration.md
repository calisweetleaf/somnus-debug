# Runtime configuration

This page covers configuring the tools from Python instead of from the command line: which objects carry configuration, how to change it in-process, what happens to the stored config hash, and which calls have side effects.

There is no public configuration API: the package exports only `__version__` and each tool's `main` [SOURCE-CONFIRMED `src/somnus_debug/__init__.py:57-59`, `src/somnus_debug/doctor/__init__.py:41-45`]. Everything below uses module-level names in the `core.py` files, which are importable but undocumented. Treat them as internal: see [../04-library-api/internal-interfaces.md](../04-library-api/internal-interfaces.md).

## doctor: ConfigManager and DoctorConfig

This section shows the three ways to give doctor a configuration in-process.

| Way | How | Validation | `config_hash` | Evidence |
|---|---|---|---|---|
| defaults | `ConfigManager(None)` | yes | hash of `DEFAULT_CONFIG_DATA` | [VERIFIED W3 RT1] |
| from a file | `ConfigManager(Path("cfg.yaml" or "cfg.json"))` | yes, same rules as the CLI | hash of merged file | [VERIFIED W3 RT4] |
| replace in-process | `cm.config = dataclasses.replace(cm.config, ...)` | **none**; you can set values the validator would reject | unchanged: still the hash of what `ConfigManager` loaded | [VERIFIED W3 RT2] |

`DoctorConfig` is a frozen dataclass, so assigning to one of its fields raises `FrozenInstanceError`; `ConfigManager.config` is an ordinary attribute and can be replaced [VERIFIED W3 RT3; `src/somnus_debug/doctor/core.py:207-239,785-790`]. There is no constructor that takes a dict: to pass a dict through validation, write it to a temporary `.json` file and load that (RT4).

`ProjectScanner(root, config_manager)` reads `config_manager.config` once in its constructor and builds the file index immediately, so changes after construction do not affect discovery [SOURCE-CONFIRMED `core.py:1698-1703`]. `config_manager.severity()` reads `config.severity_levels` on every call, so a replaced map is honored [SOURCE-CONFIRMED `core.py:792-794`].

Example (W3 RT1-RT5; fixture `/tmp/w3/fx/proj` with 3 files and 6 issues under defaults):

```python
import dataclasses, json, os, pathlib, tempfile
from somnus_debug.doctor.core import ConfigManager, ProjectScanner, Severity

root = pathlib.Path("/tmp/w3/fx/proj")
cm = ConfigManager(None)
r0 = ProjectScanner(root, cm).scan({})
print("RT1 defaults:", r0.summary.files_scanned, r0.summary.total_issues, "hash", cm.config_hash[:12])

cm2 = ConfigManager(None)
cm2.config = dataclasses.replace(cm2.config, include_patterns=("pkg/*.py",),
    severity_levels={**cm2.config.severity_levels, "stubs": Severity.INFO})
r1 = ProjectScanner(root, cm2).scan({})
print("RT2 replaced config:", r1.summary.files_scanned, r1.summary.total_issues,
      "serious", r1.summary.serious_issues, "| config_hash unchanged:", cm2.config_hash == cm.config_hash)

try:
    cm2.config.max_workers = 2
except dataclasses.FrozenInstanceError as e:
    print("RT3 DoctorConfig frozen:", type(e).__name__)

with tempfile.TemporaryDirectory() as t:
    p = pathlib.Path(t, "c.json"); p.write_text(json.dumps({"include_patterns": ["pkg/*.py"]}))
    cm3 = ConfigManager(p)
    print("RT4 JSON temp file:", ProjectScanner(root, cm3).scan({}).summary.files_scanned,
          "hash differs:", cm3.config_hash != cm.config_hash)
print("RT5 cwd files after:", sorted(os.listdir(".")))
```

Executed: yes (`/tmp/w3/prog`, `PYTHONPATH=<repo>/src`, exit 0; this exact block was extracted from the page and run). Output:

```text
RT1 defaults: 3 6 hash ff1bdc11340b
RT2 replaced config: 2 5 serious 1 | config_hash unchanged: True
RT3 DoctorConfig frozen: FrozenInstanceError
RT4 JSON temp file: 2 hash differs: True
RT5 cwd files after: ['b0.py', 'b1.py', 'b2.py']
```

(The three files are the page's own code blocks, extracted and run from that directory; nothing else was created.)

RT5 shows that `ConfigManager` plus `ProjectScanner.scan()` wrote nothing to CWD: no `production_doctor.log`, no reports, no `.python_doctor/` [VERIFIED W3 RT5]. That is the clean embedding path; `main()` and `run_scan()` do write (log file, reports, state) and `main()` replaces the host's root logging handlers [SOURCE-CONFIRMED `core.py:2179-2186`]. [D-12](../DISCOVERY-LEDGER.md#d-12), [D-11](../DISCOVERY-LEDGER.md#d-11)

The same in-process override is shown in recipe R11 in [configuration-recipes.md](configuration-recipes.md) (output `2 0 1`: 2 files, 0 serious, 1 info after remapping `security_risks` to `info`).

### Consequences of replacing the config

- The JSON report and the SQLite `runs` row record `config_hash` from load time, so two runs with different replaced configs look identical by hash [VERIFIED W3 RT2]. delta.py never compares the hash anyway [SOURCE-CONFIRMED `delta.py:159-191`].
- Validation is skipped: `max_workers=0`, a severity string instead of a `Severity`, or an empty `state_dir` go straight to the scanner. Their behavior is [UNVERIFIED]; prefer the temp-file route when values come from users.
- `max_workers` controls a `ThreadPoolExecutor`; `1` takes a sequential path. Results were identical with 1 and 4 workers on the W3 fixture [VERIFIED W3 M3; `core.py:1720-1722`].

## doctor through `main(argv)`

This section covers driving the CLI entry point from Python.

`somnus_debug.doctor.core.main(argv)` and `somnus_debug.cli.main(argv)` accept an argv list and return the exit code instead of exiting (except argparse errors, which raise `SystemExit(2)`; the dispatcher converts that to a return value) [SOURCE-CONFIRMED `src/somnus_debug/cli.py:99-104`, `core.py:2184-2199`]. Configuration is then exactly the CLI's: a config file only through `-c`. Side effects are the CLI's too: `production_doctor.log` in CWD and `logging.basicConfig(force=True)` on every call [SOURCE-CONFIRMED `core.py:2181`].

## pycache-clean: CleanerConfig

This section shows configuring the cleaner without a YAML file.

`CleanerConfig` is a mutable dataclass; `PycacheCleaner(cfg)` calls `cfg.normalize()` (resolving roots against CWD, mutating your object) and rejects empty roots [SOURCE-CONFIRMED `pycache_cleaner/core.py:157-195`].

```python
import logging, pathlib, os
from somnus_debug.pycache_cleaner.core import CleanerConfig, PycacheCleaner
os.makedirs("t/__pycache__", exist_ok=True); open("t/__pycache__/a.pyc","w").close()
cfg = CleanerConfig(roots=["t"], dry_run=True)
c = PycacheCleaner(cfg); c.run()
print("PC1 dry:", c.deleted_dirs, c.deleted_files, "exists:", os.path.exists("t/__pycache__"), "roots normalized:", cfg.roots)
```

Executed: yes (`/tmp/w3/prog`, exit 0). Output: `PC1 dry: 1 0 exists: True roots normalized: ['/tmp/w3/prog/t']`. The counters say "deleted" even in dry-run mode [VERIFIED]. Logging goes through the root logger and is silent unless the host configures it; `setup_logging()` is only called by `main()` [SOURCE-CONFIRMED `pycache_cleaner/core.py:324-334,365`]. Values are not type-checked here either (see [file-based-configuration.md](file-based-configuration.md)).

## structure and init-test-harness

This section covers the keyword arguments that configure the two remaining library functions.

```python
from somnus_debug.structure.core import build_index
print(build_index('class A:\n    def m(self): pass\n', source_name='x/y.py', include_lines=False, include_module_functions=False).splitlines()[0])
from somnus_debug.test_harness.scaffold import scaffold
import pathlib; print([p.name for p in scaffold(pathlib.Path('h'), with_contract=False)])
```

Executed: yes (`/tmp/w3/prog`, exit 0). Output:

```text
# Class Index for `y.py`
['run_test.py']
```

- `build_index(source, *, source_name, include_lines=True, include_module_functions=True)` maps one-to-one to `--source-label`, `--no-line-numbers`, `--no-module-functions`; it always parses with `type_comments=True` [SOURCE-CONFIRMED `structure/core.py:202-210`]. [D-01](../DISCOVERY-LEDGER.md#d-01)
- `scaffold(target_dir, *, force=False, with_contract=True)` maps to `target`, `--force`, `--no-contract` and raises `FileExistsError` instead of returning 1 [SOURCE-CONFIRMED `scaffold.py:62-88`].

## No live reload, no global state to tune

This section lists runtime knobs that do not exist.

- No tool watches its config file or re-reads it during a run [SOURCE-CONFIRMED: each loads once, `core.py:785-790`, `pycache_cleaner/core.py:355`].
- No module-level setting (for example a verbosity flag) is consulted at call time; constants such as `SECURITY_CALLS` or `TODO_PATTERNS` are read directly by the visitor, so monkeypatching them affects every later scan in the process [HYPOTHESIS, not tested].

## Sources

This section lists the evidence behind this page.

- [`../_evidence/configuration-registry.tsv`](../_evidence/configuration-registry.tsv) row `ProjectScanner/ConfigManager runtime override`
- [`../_evidence/agent-findings/lane-a-arch-api/api-reference.md`](../_evidence/agent-findings/lane-a-arch-api/api-reference.md), [`../_evidence/agent-findings/lane-a-arch-api/examples/ex3_side_effects.py.txt`](../_evidence/agent-findings/lane-a-arch-api/examples/ex3_side_effects.py.txt)
- `src/somnus_debug/doctor/core.py:207-239,782-851,1695-1722,2179-2199`, `src/somnus_debug/pycache_cleaner/core.py:157-195,324-365`, `src/somnus_debug/structure/core.py:202-210`, `src/somnus_debug/test_harness/scaffold.py:62-88`
- W3 probes RT1-RT5, PC1, M3 (`/tmp/w3/prog`); recipe R11
