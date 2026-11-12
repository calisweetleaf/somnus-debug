# Defaults

This page gives the value each setting takes when nobody sets it, layer by layer and tool by tool, and names which layer actually wins at runtime.

Baseline: commit `034f46e`. Layer names used below:

- **argparse**: the `default=` in the tool's parser.
- **in-code**: a Python literal the tool always applies (`DEFAULT_CONFIG_DATA`, the `CleanerConfig` dataclass, module constants).
- **init-config output**: the text `doctor init-config` writes (`ConfigManager.default_yaml()`).
- **default_config.yaml**: the packaged reference file `src/somnus_debug/doctor/default_config.yaml` (and its PyPI 0.1.0 counterpart).
- **YAML via `-c`**: a file the user passes. It only matters when passed.

## The three doctor default layers agree, and only one is live

This section shows that the in-code dict, the init-config text, and the src reference YAML are the same data, and that only the in-code dict is read at runtime.

| Layer | Location | Read at runtime? | Equal to `DEFAULT_CONFIG_DATA`? |
|---|---|---|---|
| in-code `DEFAULT_CONFIG_DATA` | `src/somnus_debug/doctor/core.py:451-502` | Yes, always the merge base (`core.py:799,811,813`) | itself |
| init-config output | `src/somnus_debug/doctor/core.py:853-923` | No; written to disk by `init-config` (`core.py:2101`) | Yes [VERIFIED W3 E8d: parsed with doctor's parser and with PyYAML, both equal] |
| src `doctor/default_config.yaml` | `src/somnus_debug/doctor/default_config.yaml:33-99` | No; read only by `tests/test_cli_smoke.py:90,117` | Yes [VERIFIED W3 E8d]; its body is byte-identical to `default_yaml()` after the metadata header [VERIFIED W3 E8e] |
| PyPI 0.1.0 `doctor/default_config.yaml` | wheel/sdist | No | **No**: old Somnus MCP globs [SOURCE-CONFIRMED by lane D diff, [install-vs-source.md](../_evidence/agent-findings/lane-d-cli-tests/install-vs-source.md)]. Reference-only, so no runtime effect. [D-23](../DISCOVERY-LEDGER.md#d-23) |
| repo-root `python_doctor.yaml` | `python_doctor.yaml` | No; nothing references it (grep finds only docstrings and the fieldkit adopting it) | **No**: differs in `include_patterns` and `ignore_patterns` only [VERIFIED W3 E8f]; lane D found it equal to the PyPI reference file |

Winner without `-c`: `DEFAULT_CONFIG_DATA`, always [SOURCE-CONFIRMED `core.py:798-799`]. Winner with `-c FILE`: the file's value for each key it sets, `DEFAULT_CONFIG_DATA` for each key it omits, with `severity_levels` merged per category [VERIFIED W3 E4a]. The `init-config` output carries no comments, although QUICKSTART says "see the generated file for the full set with comments" [VERIFIED W3 E8e: no `#` lines; DISCREPANCY with `docs/Python_Doctor_QUICKSTART.md:66`].

## doctor config keys: value per layer

This section lists every doctor key with its value in each default layer and the value that wins.

`src` = in-code, init-config output, and src `default_config.yaml` (identical). `root/PyPI` = repo-root `python_doctor.yaml` and the PyPI 0.1.0 reference file. A `-c` file, when passed, overrides per key.

| Key | src default (wins without `-c`) | root/PyPI reference | Type / validation | Evidence |
|---|---|---|---|---|
| `schema_version` | `"3.0"` | same | non-empty str; never compared | [VERIFIED lane B C20/C21] |
| `min_function_lines` | `5` | same | int >= 1 | [SOURCE-CONFIRMED `core.py:453,823`] |
| `min_class_lines` | `6` | same | int >= 1 | [SOURCE-CONFIRMED `core.py:454,824`] |
| `min_docstring_length` | `18` | same | int >= 1 | [SOURCE-CONFIRMED `core.py:455,825`] |
| `max_cyclomatic_complexity` | `12` | same | int >= 1 | [SOURCE-CONFIRMED `core.py:456,826`] |
| `max_report_evidence_lines` | `5` | same | int >= 1; evidence = N//2 lines each side | [VERIFIED W3 M2: 5 lines default, 1 line with `1`] |
| `include_patterns` | `["*.py"]` | `tools/*.py`, `tools/native/speech/*.py`, `test/*.py`, `test/speech/*.py` | list of non-empty str; `[]` allowed (0 files) | [VERIFIED W3 E8f, G5] |
| `ignore_patterns` | 15 globs: `__pycache__/*`, `*.pyc`, `.git/*`, `.hg/*`, `.mypy_cache/*`, `.pytest_cache/*`, `.ruff_cache/*`, `.tox/*`, `.venv/*`, `venv/*`, `env/*`, `node_modules/*`, `.python_doctor/*`, `build/*`, `dist/*` | drops `.hg`, `.mypy_cache`, `.pytest_cache`, `.ruff_cache`, `.tox`, `env`, `node_modules`, `build`, `dist`; adds `potential-project-developments/*`, `reports/*`, `test/*/runs/*` | list of non-empty str | [VERIFIED W3 E8f] |
| `ignore_functions` | `["__repr__", "__str__"]` | same | list of bare names | [VERIFIED W3 F0: an `eval` inside a function named `__repr__` is not reported under defaults] |
| `ignore_classes` | `[]` | same | list of bare names | [SOURCE-CONFIRMED `core.py:461`] |
| `check_private_functions` | `false` | same | bool | [VERIFIED W3 F0/F3] |
| `check_nested_functions` | `true` | same | bool | [VERIFIED W3 F1] |
| `require_module_docstring` | `true` | same | bool | [SOURCE-CONFIRMED `core.py:464`] |
| `require_class_docstring` | `true` | same | bool | [SOURCE-CONFIRMED `core.py:465`] |
| `require_function_docstring` | `true` | same | bool | [SOURCE-CONFIRMED `core.py:466`] |
| `require_parameter_hints` | `true` | same | bool | [SOURCE-CONFIRMED `core.py:467`] |
| `require_return_hints` | `true` | same | bool | [SOURCE-CONFIRMED `core.py:468`] |
| `detect_unused_imports` | `true` | same | bool | [SOURCE-CONFIRMED `core.py:469`] |
| `detect_test_gaps` | `true` | same | bool; **never read** | [VERIFIED W3 E7c: `false` changes nothing] [D-05](../DISCOVERY-LEDGER.md#d-05) |
| `detect_security_risks` | `true` | same | bool | [VERIFIED W3 E7b: `false` drops the `os.system` finding] |
| `detect_silent_failures` | `true` | same | bool | [SOURCE-CONFIRMED `core.py:472`] |
| `detect_dependency_cycles` | `true` | same | bool | [SOURCE-CONFIRMED `core.py:473`] |
| `state_dir` | `".python_doctor"` | same | non-empty str; relative to project root; absolute accepted | [VERIFIED W3 E9a, recipe R4] |
| `reports_dir` | `"reports"` | same | non-empty str; relative to `state_dir` | [VERIFIED W3 E9a] |
| `report_basename` | `"production_doctor_report"` | same | non-empty str | [VERIFIED W3 E9a] |
| `severity_exit_level` | `"serious"` | same | `critical`/`serious`/`minor`/`info`/`none` | [VERIFIED W3 E3] |
| `max_workers` | `4` | same | int >= 1; capped at file count | [VERIFIED W3 M3/M5/M6] |
| `markdown_include_css` | `true` | same | bool | [VERIFIED W3 M1] |
| `severity_levels` | 20-category map (below) | same | mapping; values lowercase severities | [SOURCE-CONFIRMED `core.py:480-501`] |

### Default severity per category

This subsection lists the default severity map and the fallback.

| Severity | Categories (`core.py:480-501`) |
|---|---|
| critical | `analysis_read_errors`, `syntax_errors`, `tokenization_errors` |
| serious | `missing_imports`, `dependency_cycles`, `stubs`, `placeholder_returns`, `incomplete_methods`, `suspicious_short_classes`, `silent_failures`, `broad_exceptions`, `security_risks`, `test_gaps` (never emitted) |
| minor | `todos`, `missing_docstrings`, `suspicious_short_functions`, `type_hint_gaps`, `complexity`, `unused_imports`, `duplicate_definitions` |
| fallback | any category missing from the map gets `minor` (`core.py:794`) [SOURCE-CONFIRMED] |

## doctor CLI defaults

This section lists argparse defaults for doctor's subcommands and where unset paths land.

| Subcommand / flag | argparse default | Effective value | Evidence |
|---|---|---|---|
| (no arguments) | n/a | rewritten to `scan .` | [VERIFIED lane B; `core.py:2167-2168`] |
| `scan project_root` | `.` | CWD | [SOURCE-CONFIRMED `core.py:2135`] |
| `scan -c` | `None` | `DEFAULT_CONFIG_DATA` | [VERIFIED W3 E1] |
| `scan -o` | `None` | `<project_root>/<report_basename>.md` | [VERIFIED W3 L1: report landed in the scanned project] |
| `scan --json-output` | `None` | `-o` path with suffix `.json`; always written | [VERIFIED W3 O1/O2] |
| `scan --no-state` | `False` | state on: `<project_root>/.python_doctor/` | [VERIFIED W3 E9a] |
| `scan -v/--verbose` | `False` | no observable effect | [VERIFIED W3 E10a/E10b: 0-byte log either way] |
| `init-config -o` | `python_doctor.yaml` | in CWD | [SOURCE-CONFIRMED `core.py:2143`] |
| `init-config --force` | `False` | refuse to overwrite, exit 4 | [VERIFIED W3 E8b] |
| `history --limit` | `10` | SQL `LIMIT`; `0` shows nothing, negative shows all | [VERIFIED W3 H1/H2] |
| `rollback --run-id` | required | n/a | [VERIFIED W3 H3: unknown id exit 4] |
| `self-check` project root | n/a | the directory holding `doctor/core.py` (site-packages when installed) | [SOURCE-CONFIRMED `core.py:2125-2126`; VERIFIED lane B on a copy] |
| `self-check -o` | `None` | `<package dir>/self_check_report.md` | [SOURCE-CONFIRMED `core.py:2126`] |
| log file | not configurable | `./production_doctor.log`, append, created on every call | [VERIFIED W3 E10d: created by `--help`] |

## pycache-clean defaults

This section lists the cleaner's defaults per layer.

| Setting | argparse | dataclass (in-code) | MANUAL 5.1 example | onboard-generated `pycache.yaml` | Winner when unset everywhere |
|---|---|---|---|---|---|
| `--config` | `config.yaml` (CWD) | n/a | n/a | n/a | `./config.yaml`; missing exits 1 [VERIFIED W3 P1] |
| `roots` | n/a | `[]` | two absolute paths | `[<absolute repo>]` | `[]` -> `ValueError` "No roots", exit 1 [VERIFIED W3 P16] |
| `exclude` | n/a | `[]` | `node_modules/*`, `.git/*` (never match, see pitfalls) | `.git`, `.hg`, `node_modules`, `.venv`, `venv`, `env`, `.tox`, `.nox`, `site-packages` + venv names | `[]` |
| `targets` | n/a | `["__pycache__", "*.pyc", "*.pyo"]` | same | same | dataclass |
| `dry_run` | `--dry-run` False | `False` | `true` | `true` | `False`: a config that omits it deletes [SOURCE-CONFIRMED `pycache_cleaner/core.py:163`] |
| `verbose` | `--verbose` False | `False` | `false` | `false` | `False` |
| `max_depth` | `--max-depth` None | `None` | `null` | `null` | unlimited |
| `follow_symlinks` | `--follow-symlinks` False | `False` | `false` | `false` | `False` |
| `log_file` | n/a | `None` | `null` | `null` | stdout only |

Sources: [SOURCE-CONFIRMED] `src/somnus_debug/pycache_cleaner/core.py:160-167,340-345`; `docs/MANUAL.md:250-266`; `skills/somnus-debug-fieldkit/scripts/onboard.py:300-321`.

## structure, init-test-harness, run_test.py

This section lists the remaining tools' defaults.

| Tool | Setting | Default | Evidence |
|---|---|---|---|
| structure | `-o` / `--update-doc` | stdout | [VERIFIED W3 S1] |
| structure | `--source-label` | `str(source)`; heading shows basename only | [VERIFIED W3 S1: `lbl/x.py` -> heading `x.py`] |
| structure | `--no-line-numbers`, `--no-module-functions` | `False` | [SOURCE-CONFIRMED `structure/core.py:306-319`] |
| structure | parser option | `type_comments=True` (src); absent in root duplicate | [VERIFIED W3 S5/S5b] [D-01](../DISCOVERY-LEDGER.md#d-01) |
| init-test-harness | `target` | `.` | [SOURCE-CONFIRMED `scaffold.py:96-101`] |
| init-test-harness | `--force`, `--no-contract` | `False` | [VERIFIED W3 T2/T3] |
| run_test.py | `PROJECT_ROOT` | parent of the directory that holds `run_test.py` | [VERIFIED W3 R1/R6] |
| run_test.py | `SINGLE_TEST_OUTPUT_DIR` | `<project_root>/test-runs` | [VERIFIED W3 R2] |
| run_test.py | `TEST_NAME` / `execute_test()` | gp-cli cargo test (fails out of the box) | [VERIFIED W3 R1: verdict FAIL, exit 1] [D-15](../DISCOVERY-LEDGER.md#d-15) |

## Fieldkit defaults

This section lists defaults of the fieldkit scripts.

| Script | Setting | Default | Evidence |
|---|---|---|---|
| onboard.py | `repo` | `.` | [SOURCE-CONFIRMED `onboard.py:454`] |
| onboard.py | mode | plan (writes nothing in the repo) | [VERIFIED W3 OB1] |
| onboard.py | config choice | first root `python_doctor.yaml`/`.yml`; else `.somnus-debug/python_doctor.yaml` | [VERIFIED W3 OB4/OB5] |
| onboard.py | runner | `--python` > project venv > `somnus-debug` on PATH | [VERIFIED W3 OB3/OB8] |
| onboard.py | generated `state_dir` | `.somnus-debug/state` | [SOURCE-CONFIRMED `onboard.py:288`] |
| onboard.py | subprocess timeouts | 600 s scans, 60 s probes | [SOURCE-CONFIRMED `onboard.py:149`] |
| delta.py | `--root` | latest report's `project_root` | [SOURCE-CONFIRMED `delta.py:252`] |
| delta.py | output | Markdown | [VERIFIED W3 DL1/DL4] |
| delta.py | disposition `symbol` | `*` | [SOURCE-CONFIRMED `delta.py:143`] |
| selftest.py | runner | `somnus-debug` on PATH | [SOURCE-CONFIRMED `selftest.py:324-330`] |

## Sources

This section lists the evidence behind this page.

- [`../_evidence/configuration-registry.tsv`](../_evidence/configuration-registry.tsv)
- [`../_evidence/agent-findings/lane-b-config/configuration-findings.md`](../_evidence/agent-findings/lane-b-config/configuration-findings.md) sections 2.2, 4
- [`../_evidence/agent-findings/lane-d-cli-tests/install-vs-source.md`](../_evidence/agent-findings/lane-d-cli-tests/install-vs-source.md) (PyPI reference YAML)
- `src/somnus_debug/doctor/core.py:81,451-502,853-923,2130-2162`, `src/somnus_debug/doctor/default_config.yaml`, `python_doctor.yaml`, `src/somnus_debug/pycache_cleaner/core.py:157-167,337-346`, `docs/MANUAL.md` section 5.1, `docs/Python_Doctor_QUICKSTART.md` "Configuration"
- W3 probes E1-E10, M1-M6, H1-H3, P1/P16, S1/S5, T2/T3, R1/R2/R6, OB1-OB8, DL1/DL4 (in `/tmp/w3`)
