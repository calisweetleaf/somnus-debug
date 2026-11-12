# Precedence

This page states, for each tool, the order in which configuration layers are applied, which layer wins for each setting, and what each relative path is resolved against.

## doctor

This section gives doctor's layer order and shows the winning value in each combination.

### Layer order

| Order (low to high) | Layer | Applies to | Source |
|---|---|---|---|
| 0 | in-code `DEFAULT_CONFIG_DATA` | every config key | `src/somnus_debug/doctor/core.py:451-502,799` |
| 1 | file passed with `-c` (`.yaml`/`.yml` via `MinimalYamlParser`, `.json` via `json.loads`; suffix checked case-insensitively) | keys present in the file; merged by `deep_merge` | `core.py:796-814,726-734` |
| 2 | CLI flags | only `project_root`, `-o`, `--json-output`, `--no-state`, `-v`, `--limit`, `--run-id`, `--force` | `core.py:2130-2162` |
| none | environment variables, `pyproject.toml`, user config, auto-discovered `python_doctor.yaml` | nothing | [VERIFIED W3 E1; grep finds no env reads in `core.py`] |

The only overlap between layer 1 and layer 2 is the report path: `-o` beats `report_basename` for the top-level report, while the per-run state copies keep `report_basename` [SOURCE-CONFIRMED `core.py:1958-1961`]. No CLI flag can change any other config key [SOURCE-CONFIRMED `core.py:2134-2161`].

### Winning value per layer

Five places hold a value for a doctor setting; only argparse, the in-code dict, and a `-c` file take part at runtime. The reference YAML and the init-config output are inert until passed with `-c`.

| Setting | argparse default | in-code `DEFAULT_CONFIG_DATA` | `default_config.yaml` (src / PyPI 0.1.0) | init-config output | YAML via `-c` | Winner |
|---|---|---|---|---|---|---|
| config file to load | `-c None` | n/a | never loaded | written to `./python_doctor.yaml`, never loaded unless passed | the file | `-c` file, else none [VERIFIED W3 E1] |
| `severity_exit_level` | no flag | `"serious"` | `"serious"` / `"serious"` | `"serious"` | file value | file if key present, else in-code [VERIFIED W3 E1b/E3] |
| `include_patterns` | no flag | `["*.py"]` | `["*.py"]` / `tools/*.py` and 3 more | `["*.py"]` | replaces whole list | file list, else in-code [VERIFIED W3 G2-G5] |
| `severity_levels.stubs` | no flag | `"serious"` | `"serious"` / `"serious"` | `"serious"` | merged per category | file category, else in-code [VERIFIED W3 E4a] |
| `max_workers` | no flag (no `-j`) | `4` | `4` / `4` | `4` | file value | file, else in-code [VERIFIED W3 M3] |
| top-level markdown report path | `-o None` | `report_basename: "production_doctor_report"` under project root | same | same | `report_basename` | `-o` > file `report_basename` > in-code [VERIFIED W3 E9a, O2] |
| JSON report path | `--json-output None` | derived from markdown path | n/a | n/a | n/a | `--json-output` > markdown path with `.json` [VERIFIED W3 O1/O2] |
| state location | `--no-state False` | `state_dir: ".python_doctor"` | same | same | `state_dir` | `--no-state` disables; else file `state_dir` > in-code [VERIFIED W3 E9a] |
| log file | none | `./production_doctor.log` (code constant) | n/a | n/a | n/a | fixed [VERIFIED W3 E10d] |
| log level | `-v/--verbose False` | INFO | n/a | n/a | n/a | DEBUG only if the literal `--verbose` is in argv; no DEBUG records exist [VERIFIED W3 E10a/E10b] |

Per tool, the same question has these answers:

| Tool | argparse | in-code | reference file | generated file | user file | Winner |
|---|---|---|---|---|---|---|
| doctor | path/report flags only | `DEFAULT_CONFIG_DATA` | `default_config.yaml` (inert) | `init-config` output (inert until `-c`) | `-c` | table above |
| pycache-clean | `--config config.yaml`, 4 override flags | `CleanerConfig` | MANUAL 5.1 example (doc only) | onboard `pycache.yaml` (used only via `--config`) | `--config` file | CLI-when-set > YAML > dataclass |
| structure | all settings | argparse defaults | none | none | none | argparse |
| init-test-harness | all settings | argparse defaults | none | none | none | argparse |
| run_test.py | none (argv ignored) | `parent.parent`, `test-runs` | CONTRACT.md comment only | none | env vars | env > in-code |
| onboard.py | 5 flags | constants | none | writes `.somnus-debug/*` | root `python_doctor.yaml` | `--new-config` > root config > generated |
| delta.py | 5 args | `GATING` | none | none | `--dispositions` file | CLI |

### Merge rules inside layer 1

| Value kind | Rule | Evidence |
|---|---|---|
| scalar (`severity_exit_level`, `max_workers`, ...) | file value replaces default | [VERIFIED W3 E3] |
| list (`include_patterns`, `ignore_patterns`, `ignore_functions`, `ignore_classes`) | file list replaces the whole default list; nothing is appended | [VERIFIED W3 E4b: `ignore_patterns: ["*.pyc"]` scanned `.venv/lib/junk.py`, files 3 -> 4; F2: `ignore_functions: [outer]` re-exposed `__repr__`] |
| mapping (`severity_levels`, the only one) | merged per category; categories you omit keep their defaults | [VERIFIED W3 E4a: two categories set to `info`, the other 18 kept, serious 2 -> 0] |
| key absent | default | [SOURCE-CONFIRMED `core.py:728`] |
| key present with null (`~`, `null`, `none`, `None`) | null replaces default, then validation fails, exit 4 | [VERIFIED W3 E2] |
| unknown key | kept in `raw_config` (so it changes `config_hash`) and otherwise ignored | [VERIFIED W3 E7a] |
| duplicate key in one YAML file | last occurrence wins, no warning | [VERIFIED lane B Y25] |

### Winning value per combination

| Scenario | `severity_exit_level` that applies | Exit on the W3 fixture (2 serious) | Evidence |
|---|---|---|---|
| no file anywhere | `serious` (in-code) | 1 | [VERIFIED W3 E1a] |
| `python_doctor.yaml` with `"none"` in CWD and in project root, no `-c` | `serious` (file ignored) | 1 | [VERIFIED W3 E1a] |
| same file passed with `-c python_doctor.yaml` | `none` | 0 | [VERIFIED W3 E1b] |
| `-c` file with unquoted `none` | null -> validation error | 4 | [VERIFIED W3 E2] |
| `-c` file with `critical` / `serious` / `minor` / `info` | that gate | 0 / 1 / 1 / 1 | [VERIFIED W3 E3] |
| `-c` JSON `{"severity_exit_level": "none"}` | `none` | 0 | [VERIFIED W3 E6a] |
| `-c G.YML` (upper-case suffix) | file value | as file | [VERIFIED W3 E6d] |
| `-c x.toml` | none: rejected before parsing | 4 | [VERIFIED W3 E6c] |

### Path anchors

Relative paths are not all resolved against the same directory.

| Path | Resolved against | Evidence |
|---|---|---|
| `-c` | CWD | [VERIFIED W3 E5a/E5b: `-c c.yaml` works from `sub/`, exit 4 "does not exist" from its parent] |
| `-o`, `--json-output` | CWD | [VERIFIED W3 O2: `outdir/rep`, `j/x.json` created under CWD] |
| default report (no `-o`) | project root | [VERIFIED W3 L1] |
| `state_dir` | project root (`project_root / state_dir`; an absolute value escapes it) | [VERIFIED W3 E9a; recipe R4 with an absolute `state_dir`] |
| `reports_dir` | `state_dir` | [VERIFIED W3 E9a] |
| `include_patterns`, `ignore_patterns` | matched against the path relative to project root and against the basename | [VERIFIED W3 G6; `core.py:939-952`] |
| `production_doctor.log` | CWD, fixed | [VERIFIED W3 E10d] |
| `init-config -o` | CWD | [SOURCE-CONFIRMED `core.py:2098`] |

### Subcommand coupling

`history` and `rollback` take their own `-c` and do not remember the config used at scan time. After a scan with a custom `state_dir`, `history` without `-c` looks in `.python_doctor/`, prints "No recorded runs found.", exits 0, and creates an empty `.python_doctor/` [VERIFIED W3 E9b vs E9c]. `self-check` resolves its project root from the package location, not from CWD [SOURCE-CONFIRMED `core.py:2125-2126`].

## pycache-clean

This section gives the cleaner's layer order; the CLI can only push values one way.

| Order (low to high) | Layer | Source |
|---|---|---|
| 0 | `CleanerConfig` dataclass defaults | `src/somnus_debug/pycache_cleaner/core.py:160-167` |
| 1 | YAML from `--config` (default `./config.yaml`), loaded with `yaml.safe_load`, applied by `setattr` with no type checks; unknown keys warned and skipped | `pycache_cleaner/core.py:170-180` |
| 2 | CLI flags, applied only when given: `--dry-run`, `--verbose`, `--follow-symlinks` can only set `True`; `--max-depth N` sets any int, including below the YAML value | `pycache_cleaner/core.py:357-364` |

| Setting | YAML says | CLI says | Winner | Evidence |
|---|---|---|---|---|
| `dry_run` | `true` | (no way to say false) | dry run | [VERIFIED W3 P15: `--no-dry-run` -> exit 2] |
| `dry_run` | `false` or absent | `--dry-run` | dry run | [VERIFIED W3 P3] |
| `max_depth` | `0` | `--max-depth 5` | 5 | [VERIFIED W3 P6] |
| `max_depth` | absent | `--max-depth 0` | 0 (the root only: its matching files and its direct target dirs such as `__pycache__`) | [VERIFIED W3 P5: 1 file deleted] |
| `verbose` | `false` | `--verbose` | verbose, unless an unknown key was present (logging then silenced) | [VERIFIED W3 P9] |

Path anchors: `--config`, `roots`, and `log_file` resolve against CWD, never against the config file's directory; only `~` is expanded, `$VAR` is not [VERIFIED W3 P10/P11/P12/P19; `pycache_cleaner/core.py:184-186,351`].

## structure, init-test-harness

This section covers the two CLI-only tools.

- structure: CLI only. `-o` and `--update-doc` are mutually exclusive (argparse exit 2) and otherwise identical [VERIFIED W3 S2/S3/S4]. Relative paths resolve against CWD [SOURCE-CONFIRMED `structure/core.py:326,340`].
- init-test-harness: CLI only. `target` resolves against CWD and is created with parents [VERIFIED W3 T1; `scaffold.py:71,83`].

## run_test.py

This section gives the scaffolded harness's two-layer order.

| Variable | Order | Empty string | Relative value | Evidence |
|---|---|---|---|---|
| `PROJECT_ROOT` | env (if set, even empty) > `Path(__file__).resolve().parent.parent` | `Path("")` -> CWD | resolved against CWD | [VERIFIED W3 R4b: empty -> `<cwd>/test-runs`; `run_test.py:748-750`] |
| `SINGLE_TEST_OUTPUT_DIR` | env (if non-empty) > `<project_root>/test-runs` | default used | resolved against **CWD**, not project root | [VERIFIED W3 R5; `run_test.py:589-593`] |

## Fieldkit scripts

This section gives the precedence rules inside onboard.py and delta.py.

- onboard.py runner: `--python` > `.venv`, `venv`, `env`, then any `pyvenv.cfg` directory that can `import somnus_debug` > `somnus-debug` on PATH > blocked (exit 3) [VERIFIED W3 OB3/OB8; `onboard.py:233-259`].
- onboard.py config: first root `python_doctor.yaml`/`.yml` unless `--new-config`; else `.somnus-debug/python_doctor.yaml` [VERIFIED W3 OB4/OB5; `onboard.py:477-479`]. The generated config is init-config output with `include_patterns`, `ignore_patterns`, and `state_dir` rewritten [SOURCE-CONFIRMED `onboard.py:276-297`].
- onboard.py child environment: `<repo>/src` is prepended to any inherited `PYTHONPATH` for src layouts [SOURCE-CONFIRMED `onboard.py:104-110,235-237`].
- delta.py: `--root` > the latest report's `project_root` > `.` [SOURCE-CONFIRMED `delta.py:252`]. Severities come from the reports themselves; `config_hash` is never compared, so a latest scan with a re-severitied config can hide a regression [VERIFIED lane F D3]. [D-21](../DISCOVERY-LEDGER.md#d-21)

## Sources

This section lists the evidence behind this page.

- [`../_evidence/configuration-registry.tsv`](../_evidence/configuration-registry.tsv)
- [`../_evidence/agent-findings/lane-b-config/configuration-findings.md`](../_evidence/agent-findings/lane-b-config/configuration-findings.md) section 2
- [`../_evidence/agent-findings/lane-f-ext/fieldkit.md`](../_evidence/agent-findings/lane-f-ext/fieldkit.md), [`harness.md`](../_evidence/agent-findings/lane-f-ext/harness.md)
- `src/somnus_debug/doctor/core.py:726-814,1955-1962,2061-2162`, `src/somnus_debug/pycache_cleaner/core.py:157-186,337-365`, `src/somnus_debug/test_harness/templates/run_test.py:589-593,747-760`, `skills/somnus-debug-fieldkit/scripts/onboard.py:104-110,233-297,477-479`, `skills/somnus-debug-fieldkit/scripts/delta.py:235-255`
- W3 probes E1-E10, O2, L1, G6, P3-P19, S2-S4, T1, R4b/R5, OB3-OB8 (run in `/tmp/w3`)
