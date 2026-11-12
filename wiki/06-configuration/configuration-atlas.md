# Configuration atlas

This is the map of every place somnus-debug 0.1.0 takes configuration from: command-line flags, the doctor YAML or JSON file, the pycache YAML file, environment variables, in-code defaults, and inputs nobody sets on purpose (the working directory, the interpreter, the clock). Start here, then follow the links.

Baseline: commit `034f46e`, Python 3.12.15, PyYAML 6.0.2. Every row mentioned here is in the canonical registry [`../_evidence/configuration-registry.tsv`](../_evidence/configuration-registry.tsv) (131 rows) and rendered in [complete-option-reference.md](complete-option-reference.md).

## The model in one screen

This section states, per tool, where its settings come from and which one wins.

| Tool | CLI flags | Config file | Env vars read | In-code defaults | Auto-discovery |
|---|---|---|---|---|---|
| `somnus-debug` dispatcher | `<command>`, `-h`, `-V` (first position only) | none | none | `_SUBCOMMANDS` | n/a |
| `doctor` (`scan`, `init-config`, `history`, `rollback`, `self-check`) | per subcommand; no flag overrides any config key | `-c PATH` with suffix `.yaml`/`.yml`/`.json` | none | `DEFAULT_CONFIG_DATA` | **none** |
| `pycache-clean` | `--config`, `--dry-run`, `--verbose`, `--max-depth`, `--follow-symlinks` | `--config` (default `config.yaml` in CWD), loaded with PyYAML | none (only `~` expansion) | `CleanerConfig` dataclass | only `./config.yaml` |
| `structure` | `source`, `-o`/`--update-doc`, `--no-line-numbers`, `--source-label`, `--no-module-functions` | none | none | argparse defaults | n/a |
| `init-test-harness` | `target`, `--force`, `--no-contract` | none | none | argparse defaults | n/a |
| scaffolded `run_test.py` | **none** (argv ignored) | none (edit `TEST_NAME`/`execute_test()`) | `PROJECT_ROOT`, `SINGLE_TEST_OUTPUT_DIR` | `Path(__file__).resolve().parent.parent` | n/a |
| fieldkit `onboard.py` | `repo`, `--apply`, `--baseline`, `--new-config`, `--python` | adopts a root `python_doctor.yaml`/`.yml`, else generates `.somnus-debug/python_doctor.yaml` | `PATH`; extends child `PYTHONPATH` | constants at `onboard.py:68-92` | root doctor config only |
| fieldkit `delta.py` | `baseline`, `latest`, `--dispositions`, `--root`, `--json` | `dispositions.json` (via flag) | none | `GATING = {critical, serious}` | none |
| fieldkit `selftest.py` | `--python` | none | `PATH` | `HELP_FLAGS` table | n/a |

Evidence: [SOURCE-CONFIRMED] `src/somnus_debug/cli.py:60-124`, `src/somnus_debug/doctor/core.py:796-814,2130-2176`, `src/somnus_debug/pycache_cleaner/core.py:157-180,337-365`, `src/somnus_debug/structure/core.py:288-320`, `src/somnus_debug/test_harness/scaffold.py:91-109`, `src/somnus_debug/test_harness/templates/run_test.py:589-593,747-750`, `skills/somnus-debug-fieldkit/scripts/onboard.py:451-459`, `skills/somnus-debug-fieldkit/scripts/delta.py:235-243`, `skills/somnus-debug-fieldkit/scripts/selftest.py:319-330`. A repo-wide search for `os.environ` and `getenv` in `src/` finds only the two `run_test.py` reads (`run_test.py:590,749`) [VERIFIED by grep at baseline].

## How a doctor setting reaches the scanner

This section traces one doctor value from its sources to the code that uses it.

```text
argv --normalize_argv()--> argparse (scan/history/rollback/self-check/init-config)
                               |
                               | args.config (relative to CWD)        args.output / --json-output (relative to CWD)
                               v                                        |
DEFAULT_CONFIG_DATA --deep_merge()--> raw_config --_validate()--> DoctorConfig (frozen) --> ProjectScanner / StateStore
        ^                    ^                                         |
        |                    | MinimalYamlParser (.yaml/.yml)          +--> config_hash (raw_config, unknown keys included)
        |                    | json.loads (.json)                      +--> exit_code_for_summary(severity_exit_level)
   always the base      only when -c is given
```

- With no `-c`, `ConfigManager(None)` merges `DEFAULT_CONFIG_DATA` with `{}` and never looks for a file [VERIFIED W3 E1: `python_doctor.yaml` holding `severity_exit_level: "none"` in both CWD and project root, scan exit 1 without `-c`, exit 0 with `-c`; `src/somnus_debug/doctor/core.py:796-799,2063`]. See [D-02](../DISCOVERY-LEDGER.md#d-02).
- `deep_merge` merges nested mappings key by key (only `severity_levels` is a mapping) and replaces lists and scalars wholesale [VERIFIED W3 E4a/E4b; `src/somnus_debug/doctor/core.py:726-734`].
- `DEFAULT_CONFIG_NAME = "python_doctor.yaml"` is used only as the default output name of `init-config` [SOURCE-CONFIRMED `src/somnus_debug/doctor/core.py:81,2143`].

## Where each kind of setting lives

This section points to the page that owns each configuration surface.

| Surface | Page | Key facts |
|---|---|---|
| Every flag, key, constant | [complete-option-reference.md](complete-option-reference.md) | 131 rows grouped by tool |
| Winning default per layer | [defaults.md](defaults.md) | the three doctor default layers agree in src; PyPI's reference YAML does not |
| Layer order and path anchors | [precedence.md](precedence.md) | CLI never overrides a doctor config key; pycache CLI only forces `True`/an int |
| Environment variables | [environment-variables.md](environment-variables.md) | two real env vars, both in `run_test.py`; interpreter variables change doctor results |
| Doctor and pycache files | [file-based-configuration.md](file-based-configuration.md) | doctor's mini-YAML parser contract, 58 inputs vs PyYAML |
| Library-level configuration | [runtime-configuration.md](runtime-configuration.md) | `ConfigManager` plus `dataclasses.replace`; no side effects |
| Inputs nobody sets on purpose | [implicit-configuration.md](implicit-configuration.md) | CWD, interpreter, clock, logging state, package directory |
| Undocumented and conditional options | [hidden-and-conditional-options.md](hidden-and-conditional-options.md) | 7 undocumented keys, 2 undocumented gates, 2 dead settings |
| Executed recipes | [configuration-recipes.md](configuration-recipes.md) | 12 recipes run in `/tmp/w3r` |
| Mistakes that pass silently | [configuration-pitfalls.md](configuration-pitfalls.md) | ranked by blast radius |
| A-Z lookup | [../13-reference/configuration-index.md](../13-reference/configuration-index.md) | links every row |

## Five facts that change how you configure it

This section lists the behaviors most likely to surprise an operator, each with its evidence.

1. **Doctor reads a config file only with `-c`.** Editing a `python_doctor.yaml` and running `scan .` changes nothing [VERIFIED W3 E1, recipe R1]. [D-02](../DISCOVERY-LEDGER.md#d-02)
2. **The mini-YAML parser reads unquoted `none` as null**, so `severity_exit_level: none` fails validation with exit 4; write `"none"` [VERIFIED W3 E2, recipe R2; `src/somnus_debug/doctor/core.py:627-628,818`]. [D-03](../DISCOVERY-LEDGER.md#d-03)
3. **Unknown doctor keys are accepted silently.** A typo such as `detect_security_risk: false` has no effect and no warning [VERIFIED W3 E7a]. [D-04](../DISCOVERY-LEDGER.md#d-04)
4. **An empty or wrong `include_patterns` scans 0 files and exits 0** [VERIFIED W3 G5, recipe R3]. `src/**/*.py` does not match `src/x.py` because fnmatch `*` crosses `/` and `**` is not recursive [VERIFIED W3 G2, recipe R5]. [D-17](../DISCOVERY-LEDGER.md#d-17)
5. **pycache-clean values are not type-checked.** `dry_run: no` is a live run; `dry_run: "false"` is a dry run that logs `dry_run=false` [VERIFIED W3 P7/P8]. [D-14](../DISCOVERY-LEDGER.md#d-14)

## What is not configurable

This section lists behavior a user might expect to tune but cannot.

- Doctor has no CLI override for any config key, no `-j`/`--workers`, no environment variable, no `pyproject.toml` section, and no user-level config [SOURCE-CONFIRMED `src/somnus_debug/doctor/core.py:2130-2162`; QUICKSTART says `max_workers` is config-only].
- The log file name and location (`./production_doctor.log`) are fixed [SOURCE-CONFIRMED `src/somnus_debug/doctor/core.py:2181`]. [D-10](../DISCOVERY-LEDGER.md#d-10)
- Detection vocabularies (`TODO_PATTERNS`, `PLACEHOLDER_CONSTANTS`, `SECURITY_CALLS`), the cycle search limits (100 cycles, depth below 30), the score weights, and the run-ID format are constants [SOURCE-CONFIRMED `src/somnus_debug/doctor/core.py:82,504-514,1642,1653,1772`].
- Eleven finding categories have no on/off toggle and can only be re-severitied (for example `broad_exceptions`, `todos`, `stubs`, `missing_imports`) [SOURCE-CONFIRMED; lane B section 6.2]. See [hidden-and-conditional-options.md](hidden-and-conditional-options.md).
- pycache-clean cannot take roots on the command line and has no `--no-dry-run` [VERIFIED W3 P15: `--no-dry-run` exit 2].
- `run_test.py` takes no flags at all; `--help` runs the test [VERIFIED W3 R7]. [D-15](../DISCOVERY-LEDGER.md#d-15)

## Sources

This section lists the evidence behind this page.

- [`../_evidence/configuration-registry.tsv`](../_evidence/configuration-registry.tsv)
- [`../_evidence/agent-findings/lane-b-config/configuration-findings.md`](../_evidence/agent-findings/lane-b-config/configuration-findings.md)
- [`../_evidence/agent-findings/lane-f-ext/fieldkit.md`](../_evidence/agent-findings/lane-f-ext/fieldkit.md), [`harness.md`](../_evidence/agent-findings/lane-f-ext/harness.md)
- W3 probes E1-E10, G1-G6, F0-F3, M1-M6, O1-O2, L1-L3, H1-H3, P1-P19, S1-S5, T1-T4, R1-R7, OB1-OB8, DL1-DL7, RT1-RT5, ENV1-ENV4 (run in `/tmp/w3`, outputs quoted on the pages that use them); recipes R1-R12 in [configuration-recipes.md](configuration-recipes.md)
- `src/somnus_debug/cli.py`, `src/somnus_debug/doctor/core.py`, `src/somnus_debug/pycache_cleaner/core.py`, `src/somnus_debug/structure/core.py`, `src/somnus_debug/test_harness/scaffold.py`, `src/somnus_debug/test_harness/templates/run_test.py`, `skills/somnus-debug-fieldkit/scripts/*.py`
