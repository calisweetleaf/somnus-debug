# Registries and discovery

This page lists every lookup table the code uses as a registry, and every mechanism by which it finds things at runtime: source files, module names, imports, configuration, and templates. It also lists the discovery mechanisms a reader might expect that do not exist.

## Static registries

This section lists the hard-coded tables that act as registries. None can be extended through configuration, except where noted.

| Registry | Location | Keys → values | Extensible? |
|---|---|---|---|
| `_SUBCOMMANDS` | `src/somnus_debug/cli.py:60-65` | `doctor`, `structure`, `pycache-clean`, `init-test-harness` → `(prog, main)` | no (in-process patch only) |
| `COMMANDS` | `src/somnus_debug/doctor/core.py:83` | doctor subcommand names used by `normalize_argv` | no; must match `build_parser` |
| `build_parser` subparsers | `:2130-2162` | `scan`, `init-config`, `history`, `rollback`, `self-check` → `run_*` via `set_defaults(func=...)` | no |
| `severity_levels` | `:480-501` defaults, config key | category → `Severity` | **yes, via config**, for any category string; unmapped categories default to `minor` (`:792-794`) |
| `SECURITY_CALLS` | `:514` | 13 dotted call names | no (module-global patch, see [internal-interfaces](../04-library-api/internal-interfaces.md#patching-rule-data)) |
| `TODO_PATTERNS` | `:504-511` | regex → marker label | no |
| `PLACEHOLDER_CONSTANTS` | `:513` | trivial return constants | no |
| logging names in `handler_is_silent` | `:1482`, `:1486` | `print`, `logging.debug/info` (silent); `logging.error/exception`, `logger.error/exception` (not silent) | no; name-sensitive ([D-07](../DISCOVERY-LEDGER.md#d-07)) |
| abstract decorator names | `:1344` | `abstractmethod`, `abc.abstractmethod`, `abstractproperty`, `abc.abstractproperty` | no |
| gate values | `:819` | `critical`, `serious`, `minor`, `info`, `none` | no |
| `_TEMPLATE_FILES` | `src/somnus_debug/test_harness/scaffold.py:55` | `run_test.py`, `CONTRACT.md` | no |
| console scripts | `pyproject.toml` `[project.scripts]` | 4 scripts | packaging only |

[SOURCE-CONFIRMED] every row. `COMMANDS` and the subparsers are two separate lists of the same names. They agree in 0.1.0. [SOURCE-CONFIRMED]

## Source file discovery (doctor)

This section explains how the doctor decides which files to scan. Most "why was this file skipped" questions are answered here.

`ProjectFileIndex._discover` (`src/somnus_debug/doctor/core.py:967-982`):

1. The root must exist and be a directory. Otherwise it raises `AnalysisExecutionError`. With state enabled, a writable missing root is created first; see [initialization](initialization.md#doctor-startup-sequence).
2. `os.walk(root)` runs top-down without following symlinked directories (the `os.walk` default). Directories are pruned in place when `should_ignore(dir)` is true.
3. A file is kept when `not should_ignore(file) and should_include(file)`.
4. Results are resolved and sorted by relative path.

Matching rules (`:937-952`):

- **`should_ignore`.** A pattern matches if `fnmatch(rel_path, pat)` or `fnmatch(basename, pat)` is true. In addition, a pattern ending in `/*` matches when its prefix equals **any path component**, so `env/*` skips `pkg/env/` at any depth ([D-17](../DISCOVERY-LEDGER.md#d-17)). Backslashes in patterns are converted to `/`.
- **`should_include`.** A pattern matches if `fnmatch(rel_path, pat)` or `fnmatch(basename, pat)` is true. `fnmatch`'s `*` crosses `/`, but `src/**/*.py` still needs at least one directory under `src/`. [VERIFIED] [lane-b configuration-findings §1 item 6](../_evidence/agent-findings/lane-b-config/configuration-findings.md).
- `fnmatch.fnmatch` is case-insensitive only on case-insensitive platforms, through `os.path.normcase`. [SOURCE-CONFIRMED] stdlib behavior.
- An empty `include_patterns` scans 0 files and exits 0. [VERIFIED] [D-17](../DISCOVERY-LEDGER.md#d-17).

Symlinked **files** are included, because `os.walk` lists them, and they are resolved to their targets (`path.resolve()`, `:981`). A symlink that points outside the root then gets an absolute `relative_path` from `safe_relpath`. [SOURCE-CONFIRMED] `:583-588`; not run. [HYPOTHESIS] for the report effect.

## Module name discovery

This section explains how file paths become module names, which decides local import resolution.

`ProjectFileIndex._modules` (`:984-992`) maps every discovered file to a dotted name relative to the **scan root**:

- `a/b.py` maps to `a.b`.
- `a/__init__.py` maps to `a`.
- A root-level `__init__.py` maps to nothing (empty parts are skipped). Its relative imports therefore cannot resolve, which is why self-check flags `from .core import main` in `doctor/__init__.py` as missing. [VERIFIED] [lane-a architecture §3.6](../_evidence/agent-findings/lane-a-arch-api/architecture.md).

The root is never treated as a package. There is no src-layout detection, so scanning a repo root with `src/pkg/` names modules `src.pkg.*`, and `import pkg` does not resolve as local. [SOURCE-CONFIRMED] With `PYTHONPATH=src` it resolves as third-party instead ([D-22](../DISCOVERY-LEDGER.md#d-22)). Scanning `src/` directly gives the intended names. [HYPOTHESIS] Follows from the mapping; see [lane-f compositions C7](../_evidence/agent-findings/lane-f-ext/compositions.md) for the measured src-layout behavior.

## Import discovery and resolution

This section summarizes how imports are found and classified. The class-level contract is in [classes](../04-library-api/classes.md#importresolver).

- **Found.** `ImportCollector` (`:1093-1119`) collects `import x.y` (bound name `x`), `from m import a as b` (star imports are dropped from the names), and literal `__import__("m")` / `importlib.import_module("m")` calls. A non-literal dynamic import is invisible.
- **Resolved.** Relative imports become absolute through the source module's package. Then the resolver tries an exact local module, then a from-import child, then a local parent prefix, then stdlib, then `find_spec` in the doctor's interpreter, and finally falls back to `missing`. [SOURCE-CONFIRMED] `:1003-1055`.
- **Masking.** The exact-module step runs first, so `from pkg import ghost` resolves to `pkg/__init__.py` and is never reported missing. Its parent-prefix step does the same for `import pkg.ghost`. [VERIFIED] [D-06](../DISCOVERY-LEDGER.md#d-06).

## Configuration discovery

This section records that the doctor does not discover configuration.

| Tool | Discovery | Evidence |
|---|---|---|
| doctor | **none**. Only `-c PATH`. `python_doctor.yaml` in the cwd or project root is ignored; `DEFAULT_CONFIG_NAME` is used only as the `init-config -o` default | [VERIFIED] [D-02](../DISCOVERY-LEDGER.md#d-02); `src/somnus_debug/doctor/core.py:81`, `:2143` |
| pycache-clean | `--config`, default `config.yaml` in the **cwd** | [SOURCE-CONFIRMED] `src/somnus_debug/pycache_cleaner/core.py:340`, `:351` |
| structure, init-test-harness | no config | [SOURCE-CONFIRMED] |
| `doctor/default_config.yaml` | packaged, never read at runtime | [SOURCE-CONFIRMED] grep; [lane-b §2.2](../_evidence/agent-findings/lane-b-config/configuration-findings.md) |

## Template discovery

This section covers how the scaffold finds its files.

`_template_text(name)` reads `resources.files("somnus_debug.test_harness.templates").joinpath(name)`. This works from a wheel, an sdist install, or a source checkout on `sys.path`, because `templates/` has an `__init__.py`. [SOURCE-CONFIRMED] `src/somnus_debug/test_harness/scaffold.py:58-59`. [VERIFIED] with `PYTHONPATH=src` in `/tmp/w1/ex_tools.py`, and with a wheel install in [lane-a api-reference §4](../_evidence/agent-findings/lane-a-arch-api/api-reference.md).

## Discovery that does not exist

This section lists absent mechanisms, so readers stop looking for them.

- No plugin, entry-point group, or `importlib.metadata` lookup. [VERIFIED] [lane-f extensions](../_evidence/agent-findings/lane-f-ext/extensions.md); [D-19](../DISCOVERY-LEDGER.md#d-19).
- No `pyproject.toml` `[tool.*]` section is read. [SOURCE-CONFIRMED] grep for `tomllib|pyproject` in `src/`: none.
- No environment variables are read by the package. [SOURCE-CONFIRMED] grep for `os.environ|getenv` in `src/somnus_debug/` outside the template: none.
- No test discovery. `detect_test_gaps` is never implemented ([D-05](../DISCOVERY-LEDGER.md#d-05)).

## Sources

This section lists the code, evidence files, and probes this page rests on.

- `src/somnus_debug/cli.py:60-65`; `src/somnus_debug/doctor/core.py:81-83`, `:480-514`, `:583-588`, `:792-794`, `:818`, `:926-1055`, `:1093-1119`, `:1344`, `:1471-1488`, `:2130-2162`; `src/somnus_debug/pycache_cleaner/core.py:340-351`; `src/somnus_debug/test_harness/scaffold.py:55-59`; `pyproject.toml`
- [lane-a architecture.md](../_evidence/agent-findings/lane-a-arch-api/architecture.md), [lane-b configuration-findings.md](../_evidence/agent-findings/lane-b-config/configuration-findings.md), [lane-f extensions.md](../_evidence/agent-findings/lane-f-ext/extensions.md), [lane-f compositions.md](../_evidence/agent-findings/lane-f-ext/compositions.md)
- Executed probe: `/tmp/w1/ex_tools.py`
