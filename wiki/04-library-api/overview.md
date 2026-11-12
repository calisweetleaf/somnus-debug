# Library API overview

This page explains what you can call from Python, how stable each part is, and which entry point to use for each job. The package was written as four CLI tools first. Its library surface is whatever those modules happen to define, and only a handful of names are exported.

## Three tiers of API

This section sorts every importable name into one of three tiers. The tier tells you how much to trust a name across versions.

| Tier | What it is | Names | Stability signal |
|---|---|---|---|
| Exported | listed in a package `__all__` | `somnus_debug.__version__`; `somnus_debug.doctor.main`; `somnus_debug.structure.build_index`, `somnus_debug.structure.main`; `somnus_debug.pycache_cleaner.main` | the only names the package re-exports [VERIFIED] [lane-a api-reference §0](../_evidence/agent-findings/lane-a-arch-api/api-reference.md) |
| Documented entry points | named in README / MANUAL §8 as library entry points, with no signatures | `ProjectScanner`, `ConfigManager`, `DoctorConfig`, `PycacheCleaner`, `CleanerConfig`, `scaffold` | [DOCUMENTED-ONLY] names only; this wiki supplies the signatures from source |
| Importable internals | every other module-level name in the `core` modules | about 240 symbols (see [api-index](api-index.md)) | no promise; names starting with `_` are private by convention |

Nothing is marked stable or versioned, and there is no deprecation policy. The package version is hard-coded as `0.1.0` in `src/somnus_debug/__init__.py:57` and in `pyproject.toml`. [SOURCE-CONFIRMED] See [D-23](../DISCOVERY-LEDGER.md#d-23).

## Which entry point for which job

This section maps common jobs to the call that does them with the fewest side effects.

| Job | Call | Side effects | Page |
|---|---|---|---|
| Scan a project in-process | `ProjectScanner(root, ConfigManager(None)).scan({})` | none (reads files only) | [public-api](public-api.md#doctor-scan-without-side-effects) |
| Scan with a config file | `ConfigManager(Path("cfg.yaml").resolve())` | reads the file | [classes](classes.md#configmanager) |
| Render reports | `MarkdownReportWriter(cfg).render(result)`, `dumps_json(result)` | none; returns strings | [functions](functions.md) |
| Keep history | `StateStore(root, cfg)` | creates `<root>/.python_doctor/` | [classes](classes.md#statestore) |
| CI gate decision | `exit_code_for_summary(result.summary, gate)` | none | [functions](functions.md) |
| Index one file | `build_index(source, source_name=...)` | none; may raise `SyntaxError` | [public-api](public-api.md#structurebuild_index) |
| Clean bytecode | `PycacheCleaner(CleanerConfig(roots=[...])).run()` | deletes files; mutates the config; may install a root logging handler | [public-api](public-api.md#pycache-cleaner) |
| Copy the test harness | `scaffold(Path(target))` | writes files | [public-api](public-api.md#scaffold) |
| Run a tool exactly as the CLI does | `doctor.main([...])`, `structure.main([...])`, `cli.main([...])` | doctor: log file in the cwd, root handlers replaced; may raise `SystemExit` | [public-api](public-api.md#cli-entry-points-as-functions) |

[VERIFIED] side-effect claims via the executed examples linked from each page. The scan-engine claim also has its own discovery entry, [D-12](../DISCOVERY-LEDGER.md#d-12).

## Import paths

This section gives the import lines that work, since `__init__` re-exports only a few names.

```python
import somnus_debug                                   # __version__ only
from somnus_debug.doctor import core as doctor        # everything in the doctor
from somnus_debug.doctor import main                  # re-exported
from somnus_debug.structure import build_index        # re-exported
from somnus_debug.pycache_cleaner.core import CleanerConfig, PycacheCleaner
from somnus_debug.test_harness.scaffold import scaffold   # NOT re-exported by test_harness
```

Executed: yes (`/tmp/w1/ex_api.py`, `/tmp/w1/ex_tools.py`, `/tmp/w1/ex_misc.py`; `PYTHONPATH=src`, Python 3.12.15; all exit 0).

`import somnus_debug.cli` pulls in PyYAML. Import the tool modules directly if you want to avoid that. [VERIFIED] [D-13](../DISCOVERY-LEDGER.md#d-13).

## Minimal working example

This section gives one end-to-end library call with its real output.

```python
from pathlib import Path
from somnus_debug.doctor import core as d

cm = d.ConfigManager(None)                         # built-in defaults
res = d.ProjectScanner(Path("proj"), cm).scan({})  # {} = no previous state
s = res.summary
print(s.files_scanned, s.total_issues, s.critical_issues, s.serious_issues, s.production_score)
print(d.exit_code_for_summary(s, cm.config.severity_exit_level))
```

Executed: yes (`/tmp/w1/ex_api.py`, on the lane-a fixture copied from [fixture/proj](../_evidence/agent-findings/lane-a-arch-api/fixture/proj), exit 0). Output, abridged from the script's longer print:

```
files 6 issues 37 crit 2 serious 13 minor 22 score 0
exit serious 2 ...
```

## Pages in this section

This section lists the remaining API pages and what each covers.

- [public-api](public-api.md): the exported and documented entry points, each with its signature, return value, side effects, and an executed example.
- [classes](classes.md): every class, with its constructor, attributes, and methods.
- [functions](functions.md): module-level functions, grouped by purpose.
- [types-and-schemas](types-and-schemas.md): dataclass fields, the JSON report schema, and the config schema.
- [exceptions](exceptions.md): the error hierarchy and what each tool raises.
- [async-and-concurrency](async-and-concurrency.md): threads and thread safety. There is no async.
- [internal-interfaces](internal-interfaces.md): the seams you can subclass or patch, and the risk of each.
- [api-index](api-index.md): an alphabetical index.

## Sources

This section lists the code, evidence files, and probes this page rests on.

- `src/somnus_debug/__init__.py`, `src/somnus_debug/*/__init__.py`, `pyproject.toml`
- [lane-a api-reference.md](../_evidence/agent-findings/lane-a-arch-api/api-reference.md)
- [lane-f extensions.md](../_evidence/agent-findings/lane-f-ext/extensions.md)
- Executed probes: `/tmp/w1/ex_api.py`, `/tmp/w1/ex_tools.py`, `/tmp/w1/ex_misc.py`
