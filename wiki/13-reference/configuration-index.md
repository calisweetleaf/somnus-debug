# Configuration index

Alphabetical index of every configuration surface in the registry: flags, keys, environment variables, files, constants, and implicit inputs, each linked to its full entry.

Generated from [`../_evidence/configuration-registry.tsv`](../_evidence/configuration-registry.tsv) (131 rows). Concept pages: [configuration atlas](../06-configuration/configuration-atlas.md), [precedence](../06-configuration/precedence.md), [defaults](../06-configuration/defaults.md), [environment variables](../06-configuration/environment-variables.md).

## Index

This section is the A-Z table; the evidence column is the row's verification class.

| Name | Tool | Surface | Default | Evidence | Entry |
|---|---|---|---|---|---|
| `active interpreter sys.path / PYTHONPATH / cwd` | doctor | implicit env | - | VERIFIED | [entry](../06-configuration/complete-option-reference.md#doctor-active-interpreter-syspath--pythonpath--cwd) |
| `ALWAYS_PRUNE / BASE_IGNORES / PYCACHE_EXCLUDES / VENV_NAMES` | fieldkit onboard.py | in-code constants | - | SOURCE-CONFIRMED | [entry](../06-configuration/complete-option-reference.md#fieldkit-onboardpy-always_prune--base_ignores--pycache_excludes--venv_names) |
| `--apply` | fieldkit onboard.py | CLI flag | False (plan mode) | VERIFIED | [entry](../06-configuration/complete-option-reference.md#fieldkit-onboardpy---apply) |
| `baseline` | fieldkit delta.py | CLI positional | - | VERIFIED | [entry](../06-configuration/complete-option-reference.md#fieldkit-deltapy-baseline) |
| `--baseline` | fieldkit onboard.py | CLI flag | False | VERIFIED | [entry](../06-configuration/complete-option-reference.md#fieldkit-onboardpy---baseline) |
| `-c/--config` | doctor scan/history/rollback/self-check | CLI flag | None (built-in DEFAULT_CONFIG_DATA) | VERIFIED | [entry](../06-configuration/complete-option-reference.md#doctor-scanhistoryrollbackself-check--c--config) |
| `check_nested_functions` | doctor | config key (YAML/JSON) | true | VERIFIED | [entry](../06-configuration/complete-option-reference.md#doctor-check_nested_functions) |
| `check_private_functions` | doctor | config key (YAML/JSON) | false | VERIFIED | [entry](../06-configuration/complete-option-reference.md#doctor-check_private_functions) |
| `<command>` | cli | argv positional | (none: prints help, exit 0) | VERIFIED | [entry](../06-configuration/complete-option-reference.md#cli-command) |
| `--config` | pycache-clean | CLI flag | config.yaml (relative to CWD) | VERIFIED | [entry](../06-configuration/complete-option-reference.md#pycache-clean---config) |
| `config_hash` | doctor | derived value | sha of merged raw config | VERIFIED | [entry](../06-configuration/complete-option-reference.md#doctor-config_hash) |
| `ConfigManager.default_yaml()` | doctor | init-config template | - | VERIFIED | [entry](../06-configuration/complete-option-reference.md#doctor-configmanagerdefault_yaml) |
| `console scripts` | packaging | packaging | somnus-debug, somnus-doctor, somnus-structure, somnus-pyc... | SOURCE-CONFIRMED | [entry](../06-configuration/complete-option-reference.md#packaging-console-scripts) |
| `cycle search limits` | doctor | internal constants | stop after 100 cycles; DFS path depth < 30 | SOURCE-CONFIRMED | [entry](../06-configuration/complete-option-reference.md#doctor-cycle-search-limits) |
| `deep_merge` | doctor | merge rule | - | VERIFIED | [entry](../06-configuration/complete-option-reference.md#doctor-deep_merge) |
| `DEFAULT_CONFIG_DATA` | doctor | in-code default | (authoritative runtime default) | VERIFIED | [entry](../06-configuration/complete-option-reference.md#doctor-default_config_data) |
| `DEFAULT_CONFIG_NAME` | doctor | in-code constant | python_doctor.yaml | SOURCE-CONFIRMED | [entry](../06-configuration/complete-option-reference.md#doctor-default_config_name) |
| `detect_dependency_cycles` | doctor | config key (YAML/JSON) | true | SOURCE-CONFIRMED | [entry](../06-configuration/complete-option-reference.md#doctor-detect_dependency_cycles) |
| `detect_security_risks` | doctor | config key (YAML/JSON) | true | VERIFIED | [entry](../06-configuration/complete-option-reference.md#doctor-detect_security_risks) |
| `detect_silent_failures` | doctor | config key (YAML/JSON) | true | VERIFIED | [entry](../06-configuration/complete-option-reference.md#doctor-detect_silent_failures) |
| `detect_test_gaps` | doctor | config key (YAML/JSON) | true | VERIFIED | [entry](../06-configuration/complete-option-reference.md#doctor-detect_test_gaps) |
| `detect_unused_imports` | doctor | config key (YAML/JSON) | true | SOURCE-CONFIRMED | [entry](../06-configuration/complete-option-reference.md#doctor-detect_unused_imports) |
| `--dispositions` | fieldkit delta.py | CLI flag | None | VERIFIED | [entry](../06-configuration/complete-option-reference.md#fieldkit-deltapy---dispositions) |
| `doctor/default_config.yaml` | doctor | packaged file | - | VERIFIED | [entry](../06-configuration/complete-option-reference.md#doctor-doctordefault_configyaml) |
| `--dry-run` | pycache-clean | CLI flag | False (config value kept) | VERIFIED | [entry](../06-configuration/complete-option-reference.md#pycache-clean---dry-run) |
| `dry-run wording` | pycache-clean | implicit | - | VERIFIED | [entry](../06-configuration/complete-option-reference.md#pycache-clean-dry-run-wording) |
| `dry_run` | pycache-clean | config key (PyYAML) | false | VERIFIED | [entry](../06-configuration/complete-option-reference.md#pycache-clean-dry_run) |
| `empty/non-mapping YAML` | pycache-clean | config file | - | VERIFIED | [entry](../06-configuration/complete-option-reference.md#pycache-clean-emptynon-mapping-yaml) |
| `exclude` | pycache-clean | config key (PyYAML) | [] | VERIFIED | [entry](../06-configuration/complete-option-reference.md#pycache-clean-exclude) |
| `exit codes` | doctor | implicit | - | VERIFIED | [entry](../06-configuration/complete-option-reference.md#doctor-exit-codes) |
| `--follow-symlinks` | pycache-clean | CLI flag | False (config value kept) | SOURCE-CONFIRMED | [entry](../06-configuration/complete-option-reference.md#pycache-clean---follow-symlinks) |
| `follow_symlinks` | pycache-clean | config key (PyYAML) | false | SOURCE-CONFIRMED | [entry](../06-configuration/complete-option-reference.md#pycache-clean-follow_symlinks) |
| `--force` | init-test-harness | CLI flag | False | VERIFIED | [entry](../06-configuration/complete-option-reference.md#init-test-harness---force) |
| `GATING / SEVERITY_ORDER` | fieldkit delta.py | in-code constants | {critical, serious} | VERIFIED | [entry](../06-configuration/complete-option-reference.md#fieldkit-deltapy-gating--severity_order) |
| `generated .somnus-debug/pycache.yaml` | fieldkit onboard.py | generated file | roots [absolute repo], name-only excludes, dry_run: true | VERIFIED | [entry](../06-configuration/complete-option-reference.md#fieldkit-onboardpy-generated-somnus-debugpycacheyaml) |
| `generated .somnus-debug/python_doctor.yaml` | fieldkit onboard.py | generated file | init-config output with include [*.py], ignore BASE_IGNOR... | VERIFIED | [entry](../06-configuration/complete-option-reference.md#fieldkit-onboardpy-generated-somnus-debugpython_doctoryaml) |
| `-h/--help (top)` | cli | CLI flag | off | VERIFIED | [entry](../06-configuration/complete-option-reference.md#cli--h--help-top) |
| `history --limit` | doctor history | CLI flag | 10 | VERIFIED | [entry](../06-configuration/complete-option-reference.md#doctor-history-history---limit) |
| `history/rollback config coupling` | doctor history/rollback | implicit | - | VERIFIED | [entry](../06-configuration/complete-option-reference.md#doctor-historyrollback-historyrollback-config-coupling) |
| `history/rollback state side-effect` | doctor history/rollback | implicit | - | VERIFIED | [entry](../06-configuration/complete-option-reference.md#doctor-historyrollback-historyrollback-state-side-effect) |
| `ignore_classes` | doctor | config key (YAML/JSON) | [] | SOURCE-CONFIRMED | [entry](../06-configuration/complete-option-reference.md#doctor-ignore_classes) |
| `ignore_functions` | doctor | config key (YAML/JSON) | ["__repr__","__str__"] | VERIFIED | [entry](../06-configuration/complete-option-reference.md#doctor-ignore_functions) |
| `ignore_patterns` | doctor | config key (YAML/JSON) | 15 globs incl. env/*, build/*, venv/* | VERIFIED | [entry](../06-configuration/complete-option-reference.md#doctor-ignore_patterns) |
| `ignore_patterns backslash normalization` | doctor | implicit | - | SOURCE-CONFIRMED | [entry](../06-configuration/complete-option-reference.md#doctor-ignore_patterns-backslash-normalization) |
| `include_patterns` | doctor | config key (YAML/JSON) | ["*.py"] | VERIFIED | [entry](../06-configuration/complete-option-reference.md#doctor-include_patterns) |
| `init-config --force` | doctor init-config | CLI flag | False | VERIFIED | [entry](../06-configuration/complete-option-reference.md#doctor-init-config-init-config---force) |
| `init-config -o/--output` | doctor init-config | CLI flag | python_doctor.yaml (in CWD) | VERIFIED | [entry](../06-configuration/complete-option-reference.md#doctor-init-config-init-config--o--output) |
| `--json` | fieldkit delta.py | CLI flag | False (Markdown) | VERIFIED | [entry](../06-configuration/complete-option-reference.md#fieldkit-deltapy---json) |
| `JSON config` | doctor | config file | - | VERIFIED | [entry](../06-configuration/complete-option-reference.md#doctor-json-config) |
| `--json-output` | doctor scan/self-check | CLI flag | <md path>.with_suffix('.json') | VERIFIED | [entry](../06-configuration/complete-option-reference.md#doctor-scanself-check---json-output) |
| `latest` | fieldkit delta.py | CLI positional | - | VERIFIED | [entry](../06-configuration/complete-option-reference.md#fieldkit-deltapy-latest) |
| `log_file` | pycache-clean | config key (PyYAML) | null | VERIFIED | [entry](../06-configuration/complete-option-reference.md#pycache-clean-log_file) |
| `markdown_include_css` | doctor | config key (YAML/JSON) | true | VERIFIED | [entry](../06-configuration/complete-option-reference.md#doctor-markdown_include_css) |
| `--max-depth` | pycache-clean | CLI flag | None (config value kept) | VERIFIED | [entry](../06-configuration/complete-option-reference.md#pycache-clean---max-depth) |
| `max_cyclomatic_complexity` | doctor | config key (YAML/JSON) | 12 | SOURCE-CONFIRMED | [entry](../06-configuration/complete-option-reference.md#doctor-max_cyclomatic_complexity) |
| `max_depth` | pycache-clean | config key (PyYAML) | null | VERIFIED | [entry](../06-configuration/complete-option-reference.md#pycache-clean-max_depth) |
| `max_report_evidence_lines` | doctor | config key (YAML/JSON) | 5 | SOURCE-CONFIRMED | [entry](../06-configuration/complete-option-reference.md#doctor-max_report_evidence_lines) |
| `max_workers` | doctor | config key (YAML/JSON) | 4 | VERIFIED | [entry](../06-configuration/complete-option-reference.md#doctor-max_workers) |
| `min_class_lines` | doctor | config key (YAML/JSON) | 6 | SOURCE-CONFIRMED | [entry](../06-configuration/complete-option-reference.md#doctor-min_class_lines) |
| `min_docstring_length` | doctor | config key (YAML/JSON) | 18 | SOURCE-CONFIRMED | [entry](../06-configuration/complete-option-reference.md#doctor-min_docstring_length) |
| `min_function_lines` | doctor | config key (YAML/JSON) | 5 | SOURCE-CONFIRMED | [entry](../06-configuration/complete-option-reference.md#doctor-min_function_lines) |
| `module docstring escape` | pycache-clean | implicit | - | VERIFIED | [entry](../06-configuration/complete-option-reference.md#pycache-clean-module-docstring-escape) |
| `--new-config` | fieldkit onboard.py | CLI flag | False | VERIFIED | [entry](../06-configuration/complete-option-reference.md#fieldkit-onboardpy---new-config) |
| `no --no-dry-run / no --root` | pycache-clean | absent flag | - | VERIFIED | [entry](../06-configuration/complete-option-reference.md#pycache-clean-no---no-dry-run--no---root) |
| `--no-contract` | init-test-harness | CLI negative flag | False | VERIFIED | [entry](../06-configuration/complete-option-reference.md#init-test-harness---no-contract) |
| `--no-line-numbers` | structure | CLI | False | VERIFIED | [entry](../06-configuration/complete-option-reference.md#structure---no-line-numbers) |
| `--no-module-functions` | structure | CLI | False | VERIFIED | [entry](../06-configuration/complete-option-reference.md#structure---no-module-functions) |
| `--no-state` | doctor scan/self-check | CLI negative flag | False (state on) | VERIFIED | [entry](../06-configuration/complete-option-reference.md#doctor-scanself-check---no-state) |
| `normalize_argv legacy form` | doctor | argv rewrite | [] -> ['scan','.'] | VERIFIED | [entry](../06-configuration/complete-option-reference.md#doctor-normalize_argv-legacy-form) |
| `-o/--output` | structure | CLI | stdout | VERIFIED | [entry](../06-configuration/complete-option-reference.md#structure--o--output) |
| `-o/--output (scan)` | doctor scan | CLI flag | <project_root>/<report_basename>.md | VERIFIED | [entry](../06-configuration/complete-option-reference.md#doctor-scan--o--output-scan) |
| `onboard exit codes` | fieldkit onboard.py | exit status | 0 ok | VERIFIED | [entry](../06-configuration/complete-option-reference.md#fieldkit-onboardpy-onboard-exit-codes) |
| `PATH lookup of somnus-debug` | fieldkit onboard.py | env var | PATH | VERIFIED | [entry](../06-configuration/complete-option-reference.md#fieldkit-onboardpy-path-lookup-of-somnus-debug) |
| `production_doctor.log` | doctor | implicit file | ./production_doctor.log (CWD), append | VERIFIED | [entry](../06-configuration/complete-option-reference.md#doctor-production_doctorlog) |
| `PROFILE_DIR` | fieldkit onboard.py | in-code constant | .somnus-debug | SOURCE-CONFIRMED | [entry](../06-configuration/complete-option-reference.md#fieldkit-onboardpy-profile_dir) |
| `PROJECT_ROOT` | run_test.py | env var | Path(__file__).resolve().parent.parent (the parent of the... | VERIFIED | [entry](../06-configuration/complete-option-reference.md#run_testpy-project_root) |
| `ProjectScanner/ConfigManager runtime override` | doctor | library | - | VERIFIED | [entry](../06-configuration/complete-option-reference.md#doctor-projectscannerconfigmanager-runtime-override) |
| `pycache relative path anchor` | pycache-clean | implicit | - | VERIFIED | [entry](../06-configuration/complete-option-reference.md#pycache-clean-pycache-relative-path-anchor) |
| `--python` | fieldkit onboard.py | CLI flag | None (project venv, then PATH) | VERIFIED | [entry](../06-configuration/complete-option-reference.md#fieldkit-onboardpy---python) |
| `--python` | fieldkit selftest.py | CLI flag | somnus-debug on PATH | VERIFIED | [entry](../06-configuration/complete-option-reference.md#fieldkit-selftestpy---python) |
| `PYTHONPATH / PYTHONSAFEPATH / python -P / CWD on sys.path` | doctor | env var (interpreter) | interpreter defaults | VERIFIED | [entry](../06-configuration/complete-option-reference.md#doctor-pythonpath--pythonsafepath--python--p--cwd-on-syspath) |
| `PYTHONPATH extension (src layout)` | fieldkit onboard.py | env var (child process) | prepend <repo>/src when src/<pkg>/__init__.py exists | VERIFIED | [entry](../06-configuration/complete-option-reference.md#fieldkit-onboardpy-pythonpath-extension-src-layout) |
| `PyYAML import` | pycache-clean | conditional import | - | VERIFIED | [entry](../06-configuration/complete-option-reference.md#pycache-clean-pyyaml-import) |
| `PyYAML presence (doctor via dispatcher)` | cli | dependency | - | VERIFIED | [entry](../06-configuration/complete-option-reference.md#cli-pyyaml-presence-doctor-via-dispatcher) |
| `readiness score weights` | doctor | internal constants | 100 - 20*critical - 8*serious - 2*minor - 1*info (floor 0) | SOURCE-CONFIRMED | [entry](../06-configuration/complete-option-reference.md#doctor-readiness-score-weights) |
| `repo` | fieldkit onboard.py | CLI positional | . (cwd) | VERIFIED | [entry](../06-configuration/complete-option-reference.md#fieldkit-onboardpy-repo) |
| `report_basename` | doctor | config key (YAML/JSON) | production_doctor_report | VERIFIED | [entry](../06-configuration/complete-option-reference.md#doctor-report_basename) |
| `reports_dir` | doctor | config key (YAML/JSON) | reports | VERIFIED | [entry](../06-configuration/complete-option-reference.md#doctor-reports_dir) |
| `require_* / detect_* bool validation` | doctor | validation rule | - | VERIFIED | [entry](../06-configuration/complete-option-reference.md#doctor-require_--detect_-bool-validation) |
| `require_class_docstring` | doctor | config key (YAML/JSON) | true | SOURCE-CONFIRMED | [entry](../06-configuration/complete-option-reference.md#doctor-require_class_docstring) |
| `require_function_docstring` | doctor | config key (YAML/JSON) | true | SOURCE-CONFIRMED | [entry](../06-configuration/complete-option-reference.md#doctor-require_function_docstring) |
| `require_module_docstring` | doctor | config key (YAML/JSON) | true | SOURCE-CONFIRMED | [entry](../06-configuration/complete-option-reference.md#doctor-require_module_docstring) |
| `require_parameter_hints` | doctor | config key (YAML/JSON) | true | VERIFIED | [entry](../06-configuration/complete-option-reference.md#doctor-require_parameter_hints) |
| `require_return_hints` | doctor | config key (YAML/JSON) | true | VERIFIED | [entry](../06-configuration/complete-option-reference.md#doctor-require_return_hints) |
| `rollback --run-id` | doctor rollback | CLI flag (required) | (required) | VERIFIED | [entry](../06-configuration/complete-option-reference.md#doctor-rollback-rollback---run-id) |
| `--root` | fieldkit delta.py | CLI flag | latest report's project_root | VERIFIED | [entry](../06-configuration/complete-option-reference.md#fieldkit-deltapy---root) |
| `root duplicate python_production_doctor.py` | doctor | repo script | same options as src doctor | SOURCE-CONFIRMED | [entry](../06-configuration/complete-option-reference.md#doctor-root-duplicate-python_production_doctorpy) |
| `root python_doctor.yaml` | doctor | repo file | - | VERIFIED | [entry](../06-configuration/complete-option-reference.md#doctor-root-python_doctoryaml) |
| `roots` | pycache-clean | config key (PyYAML) | [] | VERIFIED | [entry](../06-configuration/complete-option-reference.md#pycache-clean-roots) |
| `RUN_ID_FORMAT` | doctor | internal constant | %Y%m%dT%H%M%SZ (UTC, 1-second resolution) | SOURCE-CONFIRMED | [entry](../06-configuration/complete-option-reference.md#doctor-run_id_format) |
| `run_test.py argv` | run_test.py | absent CLI | - | VERIFIED | [entry](../06-configuration/complete-option-reference.md#run_testpy-run_testpy-argv) |
| `run_test.py run_id / artifact dir` | run_test.py | derived value | <SLUG(TEST_NAME)>-<YYYYmmdd-HHMMSS>-<6 hex> | VERIFIED | [entry](../06-configuration/complete-option-reference.md#run_testpy-run_testpy-run_id--artifact-dir) |
| `scan project_root` | doctor scan | CLI positional | . | VERIFIED | [entry](../06-configuration/complete-option-reference.md#doctor-scan-scan-project_root) |
| `schema_version` | doctor | config key (YAML/JSON) | 3.0 | VERIFIED | [entry](../06-configuration/complete-option-reference.md#doctor-schema_version) |
| `SCHEMA_VERSION (manifest)` | run_test.py | constant | 1.0 | SOURCE-CONFIRMED | [entry](../06-configuration/complete-option-reference.md#run_testpy-schema_version-manifest) |
| `SECURITY_CALLS / TODO_PATTERNS / PLACEHOLDER_CONSTANTS` | doctor | internal constants | see findings 6.3 | SOURCE-CONFIRMED | [entry](../06-configuration/complete-option-reference.md#doctor-security_calls--todo_patterns--placeholder_constants) |
| `self-check` | doctor self-check | subcommand | project_root=<dir of doctor/core.py>; output=<that dir>/s... | VERIFIED | [entry](../06-configuration/complete-option-reference.md#doctor-self-check-self-check) |
| `Severity values` | doctor | enum | - | SOURCE-CONFIRMED | [entry](../06-configuration/complete-option-reference.md#doctor-severity-values) |
| `severity_exit_level` | doctor | config key (YAML/JSON) | serious | VERIFIED | [entry](../06-configuration/complete-option-reference.md#doctor-severity_exit_level) |
| `severity_levels` | doctor | config key (YAML/JSON) | 20-category table (see findings) | VERIFIED | [entry](../06-configuration/complete-option-reference.md#doctor-severity_levels) |
| `SINGLE_TEST_OUTPUT_DIR` | run_test.py | env var | <project_root>/test-runs | VERIFIED | [entry](../06-configuration/complete-option-reference.md#run_testpy-single_test_output_dir) |
| `source` | structure | CLI | (required) | VERIFIED | [entry](../06-configuration/complete-option-reference.md#structure-source) |
| `source encoding` | structure | implicit | utf-8 | VERIFIED | [entry](../06-configuration/complete-option-reference.md#structure-source-encoding) |
| `--source-label` | structure | CLI | str(source) | VERIFIED | [entry](../06-configuration/complete-option-reference.md#structure---source-label) |
| `state_dir` | doctor | config key (YAML/JSON) | .python_doctor | VERIFIED | [entry](../06-configuration/complete-option-reference.md#doctor-state_dir) |
| `subprocess timeouts` | fieldkit onboard.py | in-code constants | 600 s (scans); 60 s (version, init-config, git, import pr... | SOURCE-CONFIRMED | [entry](../06-configuration/complete-option-reference.md#fieldkit-onboardpy-subprocess-timeouts) |
| `SystemExit/return mapping` | cli | implicit | - | VERIFIED | [entry](../06-configuration/complete-option-reference.md#cli-systemexitreturn-mapping) |
| `target` | init-test-harness | CLI positional | . | VERIFIED | [entry](../06-configuration/complete-option-reference.md#init-test-harness-target) |
| `targets` | pycache-clean | config key (PyYAML) | [__pycache__, *.pyc, *.pyo] | VERIFIED | [entry](../06-configuration/complete-option-reference.md#pycache-clean-targets) |
| `TEST_NAME / execute_test` | run_test.py | source edit | GOLDEN PATH LAYER 1 ... (gp-cli/cargo test) | VERIFIED | [entry](../06-configuration/complete-option-reference.md#run_testpy-test_name--execute_test) |
| `[tool.hatch.build] exclude` | packaging | packaging config | .python_doctor/, *_report.md/json, production_doctor.log,... | SOURCE-CONFIRMED | [entry](../06-configuration/complete-option-reference.md#packaging-toolhatchbuild-exclude) |
| `type_comments=True` | structure | hard-coded parser option | True (src) / absent (root analyze_python_structure.py:210) | VERIFIED | [entry](../06-configuration/complete-option-reference.md#structure-type_commentstrue) |
| `<unknown config keys>` | doctor | config key | - | VERIFIED | [entry](../06-configuration/complete-option-reference.md#doctor-unknown-config-keys) |
| `<unknown pycache keys>` | pycache-clean | config key | - | VERIFIED | [entry](../06-configuration/complete-option-reference.md#pycache-clean-unknown-pycache-keys) |
| `unknown severity category fallback` | doctor | implicit default | MINOR | SOURCE-CONFIRMED | [entry](../06-configuration/complete-option-reference.md#doctor-unknown-severity-category-fallback) |
| `--update-doc` | structure | CLI | None | VERIFIED | [entry](../06-configuration/complete-option-reference.md#structure---update-doc) |
| `-v/--verbose` | doctor scan | CLI flag | False | VERIFIED | [entry](../06-configuration/complete-option-reference.md#doctor-scan--v--verbose) |
| `-V/--version (top)` | cli | CLI flag | off | VERIFIED | [entry](../06-configuration/complete-option-reference.md#cli--v--version-top) |
| `--verbose` | pycache-clean | CLI flag | False (config value kept) | VERIFIED | [entry](../06-configuration/complete-option-reference.md#pycache-clean---verbose) |
| `verbose` | pycache-clean | config key (PyYAML) | false | VERIFIED | [entry](../06-configuration/complete-option-reference.md#pycache-clean-verbose) |
| `YAML mini-parser` | doctor | parser | - | VERIFIED | [entry](../06-configuration/complete-option-reference.md#doctor-yaml-mini-parser) |

## By surface

This section counts registry rows per surface kind.

| Surface | Rows |
|---|---|
| config key (YAML/JSON) | 29 |
| CLI flag | 23 |
| implicit | 9 |
| config key (PyYAML) | 8 |
| CLI | 6 |
| CLI positional | 5 |
| env var | 3 |
| in-code constants | 3 |
| internal constants | 3 |
| CLI negative flag | 2 |
| config file | 2 |
| config key | 2 |
| derived value | 2 |
| generated file | 2 |
| in-code constant | 2 |
| CLI flag (required) | 1 |
| absent CLI | 1 |
| absent flag | 1 |
| argv positional | 1 |
| argv rewrite | 1 |
| conditional import | 1 |
| constant | 1 |
| dependency | 1 |
| enum | 1 |
| env var (child process) | 1 |
| env var (interpreter) | 1 |
| exit status | 1 |
| hard-coded parser option | 1 |
| implicit default | 1 |
| implicit env | 1 |
| implicit file | 1 |
| in-code default | 1 |
| init-config template | 1 |
| internal constant | 1 |
| library | 1 |
| merge rule | 1 |
| packaged file | 1 |
| packaging | 1 |
| packaging config | 1 |
| parser | 1 |
| repo file | 1 |
| repo script | 1 |
| source edit | 1 |
| subcommand | 1 |
| validation rule | 1 |

## Sources

This section lists the inputs for this index.

- [`../_evidence/configuration-registry.tsv`](../_evidence/configuration-registry.tsv)
- [`../06-configuration/complete-option-reference.md`](../06-configuration/complete-option-reference.md)
