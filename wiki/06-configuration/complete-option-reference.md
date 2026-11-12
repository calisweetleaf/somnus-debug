# Complete option reference

Every row of the canonical configuration registry, grouped by tool, with its default, valid values, effect, failure behavior, documentation status, and evidence class. The registry is the source of truth; this page is generated from it so the two cannot drift.

- Registry: [`_evidence/configuration-registry.tsv`](../_evidence/configuration-registry.tsv), 131 rows, 18 columns (17 lane columns plus `notes`).
- Baseline: commit `034f46e`, somnus-debug 0.1.0, Python 3.12.15, PyYAML 6.0.2. Paths are repo-relative.
- Evidence class per row is the registry `verification` value. `VERIFIED` rows were executed by lane B, lane F, or W3 (this wave) in `/tmp`; the `example` text names the probe. `SOURCE-CONFIRMED` rows were read from source only.
- Each entry is anchored as `tool-name` so other pages can link here. For how layers combine, read [precedence.md](precedence.md); for winning defaults, [defaults.md](defaults.md).

## Contents

This section lists the tool groups and their row counts.

- [somnus-debug dispatcher (cli)](#somnus-debug-dispatcher-cli) (5)
- [doctor: CLI arguments and subcommands](#doctor-cli-arguments-and-subcommands) (15)
- [doctor: configuration file keys](#doctor-configuration-file-keys) (30)
- [doctor: files, parser, merge, constants, and implicit inputs](#doctor-files-parser-merge-constants-and-implicit-inputs) (22)
- [pycache-clean](#pycache-clean) (20)
- [structure](#structure) (8)
- [init-test-harness](#init-test-harness) (3)
- [run_test.py (scaffolded template)](#runtestpy-scaffolded-template) (6)
- [fieldkit onboard.py](#fieldkit-onboardpy) (13)
- [fieldkit delta.py](#fieldkit-deltapy) (6)
- [fieldkit selftest.py](#fieldkit-selftestpy) (1)
- [packaging](#packaging) (2)

## somnus-debug dispatcher (cli)

This section documents the 5 registry rows for somnus-debug dispatcher (cli).

<a id="cli-command"></a>
### `<command>`

[VERIFIED] argv positional; tool `cli`. Defined at `src/somnus_debug/cli.py:60-65`; read at `src/somnus_debug/cli.py:118-124`.

| Field | Value |
|---|---|
| Default | (none: prints help, exit 0) |
| Type | str |
| Valid values | doctor\|structure\|pycache-clean\|init-test-harness |
| Precedence | n/a |
| Effect | routes remaining argv to tool main(); sys.argv rewritten to [prog,*rest] |
| Scope | process |
| Persistence | none |
| Dependencies | importing cli imports ALL tool modules incl. pycache (PyYAML) |
| Failure behavior | unknown command -> help on stderr, exit 2 (same code as argparse usage errors) |
| Doc status | partial |
| Verification | VERIFIED |
| Example / probe | somnus-debug bogus -> exit 2 |

<a id="cli--h--help-top"></a>
### `-h/--help (top)`

[VERIFIED] CLI flag; tool `cli`. Defined at `src/somnus_debug/cli.py:111`; read at `src/somnus_debug/cli.py:111-113`.

| Field | Value |
|---|---|
| Default | off |
| Type | flag |
| Precedence | only honored as argv[0] |
| Effect | prints static help |
| Scope | process |
| Persistence | none |
| Doc status | existing |
| Verification | VERIFIED |
| Example / probe | somnus-debug -> help, exit 0 |

<a id="cli--v--version-top"></a>
### `-V/--version (top)`

[VERIFIED] CLI flag; tool `cli`. Defined at `src/somnus_debug/cli.py:114`; read at `src/somnus_debug/cli.py:114-116`.

| Field | Value |
|---|---|
| Default | off |
| Type | flag |
| Precedence | only as argv[0]; tools have no --version |
| Effect | prints 0.1.0 |
| Scope | process |
| Persistence | none |
| Failure behavior | `somnus-debug doctor --version` -> argparse error exit 2 (normalized to scan . --version) |
| Doc status | missing |
| Verification | VERIFIED |
| Example / probe | somnus-debug -V -> 0.1.0 |

<a id="cli-systemexitreturn-mapping"></a>
### `SystemExit/return mapping`

[VERIFIED] implicit; tool `cli`. Defined at `src/somnus_debug/cli.py:99-104`; read at `src/somnus_debug/cli.py:99-104`.

| Field | Value |
|---|---|
| Effect | SystemExit(int) -> that int; non-int code -> 1; tool returning None (pycache-clean) -> 0 |
| Scope | process |
| Persistence | none |
| Failure behavior | pycache-clean main() returns None so success always 0; uncaught non-SystemExit exceptions (e.g. structure UnicodeDecodeError) propagate as traceback exit 1 |
| Doc status | missing |
| Verification | VERIFIED |
| Example / probe | somnus-debug structure latin1.py -> traceback exit 1 |

<a id="cli-pyyaml-presence-doctor-via-dispatcher"></a>
### `PyYAML presence (doctor via dispatcher)`

[VERIFIED] dependency; tool `cli`. Defined at `src/somnus_debug/cli.py:55-58`.

| Field | Value |
|---|---|
| Effect | somnus-debug imports every tool at import time, so missing PyYAML breaks all subcommands; somnus-doctor (doctor.core only) stays stdlib-only |
| Failure behavior | ImportError at import |
| Doc status | contradictory (README: doctor/structure stdlib-only) |
| Verification | VERIFIED |
| Example / probe | sys.modules['yaml']=None: doctor.core imports, somnus_debug.cli raises ImportError (W3 NOYAML1/2) |
| Notes | W3 added; see D-13 |

## doctor: CLI arguments and subcommands

This section documents the 15 registry rows for doctor: CLI arguments and subcommands.

<a id="doctor-normalize_argv-legacy-form"></a>
### `normalize_argv legacy form`

[VERIFIED] argv rewrite; tool `doctor`. Defined at `src/somnus_debug/doctor/core.py:2165-2176`; read at `src/somnus_debug/doctor/core.py:2188`.

| Field | Value |
|---|---|
| Default | [] -> ['scan','.'] |
| Precedence | before argparse |
| Effect | no args -> scan .; first arg starting '-' (other than -h) -> scan . <args>; any other non-command first arg -> scan <args> |
| Scope | process |
| Persistence | none |
| Dependencies | COMMANDS set {D}:83 |
| Failure behavior | a directory literally named history/rollback/etc. cannot be scanned in bare form |
| Doc status | partial (bare path documented; flag-only & no-arg forms missing) |
| Verification | VERIFIED |
| Example / probe | somnus-debug doctor --no-state == scan . --no-state |

<a id="doctor-scan-scan-project_root"></a>
### `scan project_root`

[VERIFIED] CLI positional; tool `doctor scan`. Defined at `src/somnus_debug/doctor/core.py:2135`; read at `src/somnus_debug/doctor/core.py:2064`.

| Field | Value |
|---|---|
| Default | . |
| Type | path |
| Valid values | existing directory |
| Precedence | CLI only |
| Effect | root of discovery, module naming, state dir and default report location |
| Scope | run |
| Persistence | none |
| Dependencies | cwd |
| Failure behavior | missing -> AnalysisExecutionError exit 4; file -> exit 4 |
| Doc status | existing |
| Verification | VERIFIED |
| Example / probe | doctor scan nope -> exit 4 |

<a id="doctor-scanhistoryrollbackself-check--c--config"></a>
### `-c/--config`

[VERIFIED] CLI flag; tool `doctor scan/history/rollback/self-check`. Defined at `src/somnus_debug/doctor/core.py:2136,2148,2154,2157`; read at `src/somnus_debug/doctor/core.py:2063,2108,2115`.

| Field | Value |
|---|---|
| Default | None (built-in DEFAULT_CONFIG_DATA) |
| Type | path |
| Valid values | *.yaml\|*.yml\|*.json (case-insensitive suffix) |
| Precedence | ONLY way to load a file; no auto-discovery; file values deep-merged over in-code defaults |
| Effect | loads config; relative path resolved against CWD (not project_root) |
| Scope | run |
| Persistence | none |
| Failure behavior | missing file / bad suffix / parse / validation error -> ConfigurationError exit 4 |
| Doc status | partial (docs imply python_doctor.yaml in project root is used; it is not unless -c) |
| Verification | VERIFIED |
| Example / probe | python_doctor.yaml in cwd without -c is ignored (E1 exit 1 vs E2 exit 0) |

<a id="doctor-scan--o--output-scan"></a>
### `-o/--output (scan)`

[VERIFIED] CLI flag; tool `doctor scan`. Defined at `src/somnus_debug/doctor/core.py:2137`; read at `src/somnus_debug/doctor/core.py:1960 (default), src/somnus_debug/doctor/core.py:2081 (resolve against CWD)`.

| Field | Value |
|---|---|
| Default | <project_root>/<report_basename>.md |
| Type | path |
| Valid values | any |
| Precedence | CLI > report_basename |
| Effect | markdown report path, resolved against CWD; JSON defaults to same path with .json suffix |
| Scope | run |
| Persistence | written |
| Failure behavior | -o X.json => md and json paths identical; JSON overwrites markdown silently |
| Doc status | partial |
| Verification | VERIFIED |
| Example / probe | scan -o report.json -> only JSON remains |
| Notes | W3 corrected: read_at line drift (1958 -> 1960; path resolved at 2081) |

<a id="doctor-scanself-check---json-output"></a>
### `--json-output`

[VERIFIED] CLI flag; tool `doctor scan/self-check`. Defined at `src/somnus_debug/doctor/core.py:2138,2159`; read at `src/somnus_debug/doctor/core.py:1961, src/somnus_debug/doctor/core.py:2081`.

| Field | Value |
|---|---|
| Default | <md path>.with_suffix('.json') |
| Type | path |
| Valid values | any |
| Precedence | CLI > derived |
| Effect | JSON report path (JSON is ALWAYS written) |
| Scope | run |
| Persistence | written |
| Doc status | contradictory (QUICKSTART 'JSON report (--json-output, if requested)') |
| Verification | VERIFIED |
| Notes | W3 corrected: read_at line drift (1959 -> 1961) |

<a id="doctor-scanself-check---no-state"></a>
### `--no-state`

[VERIFIED] CLI negative flag; tool `doctor scan/self-check`. Defined at `src/somnus_debug/doctor/core.py:2139,2160`; read at `src/somnus_debug/doctor/core.py:2066`.

| Field | Value |
|---|---|
| Default | False (state on) |
| Type | flag |
| Precedence | CLI only; no config key |
| Effect | skips SQLite + state report copies; only md/json written |
| Scope | run |
| Failure behavior | state init failure also falls back to stateless with stderr warning (src only; root duplicate has no fallback) |
| Doc status | existing |
| Verification | VERIFIED |

<a id="doctor-scan--v--verbose"></a>
### `-v/--verbose`

[VERIFIED] CLI flag; tool `doctor scan`. Defined at `src/somnus_debug/doctor/core.py:2140`; read at `src/somnus_debug/doctor/core.py:2186 (string match on '--verbose' only)`.

| Field | Value |
|---|---|
| Default | False |
| Type | flag |
| Effect | sets root log level DEBUG only if the literal '--verbose' is in argv; '-v' never does; doctor emits no DEBUG records anyway -> effectively a no-op |
| Scope | process |
| Persistence | production_doctor.log |
| Failure behavior | `--verbose` anywhere in argv (even after another subcommand) switches the log level before parsing; `history --verbose` / `init-config --verbose` then fail argparse exit 2 |
| Doc status | partial (documented as enabling debug logging) |
| Verification | VERIFIED |
| Example / probe | scan -v and --verbose both leave log empty (0 lines) |
| Notes | W3 corrected: noted literal-string check spans all subcommands |

<a id="doctor-init-config-init-config--o--output"></a>
### `init-config -o/--output`

[VERIFIED] CLI flag; tool `doctor init-config`. Defined at `src/somnus_debug/doctor/core.py:2143`; read at `src/somnus_debug/doctor/core.py:2098`.

| Field | Value |
|---|---|
| Default | python_doctor.yaml (in CWD) |
| Type | path |
| Valid values | any path; suffix not validated |
| Effect | writes ConfigManager.default_yaml() text |
| Scope | run |
| Persistence | written |
| Failure behavior | exists w/o --force -> exit 4; dir path -> exit 4; -o x.toml succeeds but is then unloadable by -c |
| Doc status | partial |
| Verification | VERIFIED |
| Example / probe | init-config -o x.toml exit 0; scan -c x.toml exit 4 |

<a id="doctor-init-config-init-config---force"></a>
### `init-config --force`

[VERIFIED] CLI flag; tool `doctor init-config`. Defined at `src/somnus_debug/doctor/core.py:2144`; read at `src/somnus_debug/doctor/core.py:2099`.

| Field | Value |
|---|---|
| Default | False |
| Type | flag |
| Effect | allow overwrite |
| Scope | run |
| Doc status | existing |
| Verification | VERIFIED |

<a id="doctor-history-history---limit"></a>
### `history --limit`

[VERIFIED] CLI flag; tool `doctor history`. Defined at `src/somnus_debug/doctor/core.py:2149`; read at `src/somnus_debug/doctor/core.py:1986`.

| Field | Value |
|---|---|
| Default | 10 |
| Type | int |
| Valid values | any int (no validation) |
| Effect | SQL LIMIT; 0 -> 'No recorded runs'; negative -> unlimited |
| Scope | run |
| Doc status | partial |
| Verification | VERIFIED |
| Example / probe | --limit -1 shows all |

<a id="doctor-rollback-rollback---run-id"></a>
### `rollback --run-id`

[VERIFIED] CLI flag (required); tool `doctor rollback`. Defined at `src/somnus_debug/doctor/core.py:2153`; read at `src/somnus_debug/doctor/core.py:1991-2009`.

| Field | Value |
|---|---|
| Default | (required) |
| Type | str |
| Valid values | existing run_id |
| Effect | copies stored report to <reports>/latest.* and repoints alias |
| Scope | run |
| Persistence | state |
| Dependencies | stored artifacts must still exist |
| Failure behavior | unknown id -> StateStoreError exit 4 |
| Doc status | existing |
| Verification | VERIFIED |

<a id="doctor-historyrollback-historyrollback-state-side-effect"></a>
### `history/rollback state side-effect`

[VERIFIED] implicit; tool `doctor history/rollback`. Defined at `src/somnus_debug/doctor/core.py:1981-1983,1991-1993`; read at `src/somnus_debug/doctor/core.py:1927-1940`.

| Field | Value |
|---|---|
| Effect | read-only-looking commands call initialize(): create <root>/<state_dir>/reports and state.sqlite3 |
| Scope | project |
| Persistence | creates dirs/db |
| Doc status | missing |
| Verification | VERIFIED |
| Example / probe | doctor history ../empty creates ../empty/.python_doctor/ |

<a id="doctor-historyrollback-historyrollback-config-coupling"></a>
### `history/rollback config coupling`

[VERIFIED] implicit; tool `doctor history/rollback`. Defined at `src/somnus_debug/doctor/core.py:2108,2115`.

| Field | Value |
|---|---|
| Effect | state_dir/reports_dir come from -c config; omitting -c after scanning with custom state_dir looks in .python_doctor and silently reports nothing |
| Scope | project |
| Failure behavior | silent empty history |
| Doc status | missing |
| Verification | VERIFIED |
| Example / probe | history -c alt.yaml -> 'No recorded runs' + creates alt_state/ |

<a id="doctor-self-check-self-check"></a>
### `self-check`

[VERIFIED] subcommand; tool `doctor self-check`. Defined at `src/somnus_debug/doctor/core.py:2156-2161`; read at `src/somnus_debug/doctor/core.py:2123-2127`.

| Field | Value |
|---|---|
| Default | project_root=<dir of doctor/core.py>; output=<that dir>/self_check_report.md |
| Precedence | -o overrides output; state dir still in package dir unless --no-state |
| Effect | scans the installed package directory and WRITES reports + .python_doctor/ INTO it (site-packages when installed) |
| Scope | install dir |
| Persistence | writes into package |
| Failure behavior | read-only package dir -> state fallback warning, then report write fails exit 4 unless -o given |
| Doc status | missing (implicit write location undocumented) |
| Verification | VERIFIED |
| Example / probe | /tmp copy: self_check_report.md + .python_doctor/ created in somnus_debug/doctor/ |

<a id="doctor-exit-codes"></a>
### `exit codes`

[VERIFIED] implicit; tool `doctor`. Defined at `src/somnus_debug/doctor/core.py:2046-2058,2194,2199`.

| Field | Value |
|---|---|
| Valid values | 0,1,2 (gate), 2 (argparse usage), 4 (DoctorError), 5 (unclassified) |
| Scope | process |
| Failure behavior | exit 2 is ambiguous: critical-gate breach vs CLI usage error |
| Doc status | partial (docs say only 0 / non-zero) |
| Verification | VERIFIED |

## doctor: configuration file keys

This section documents the 30 registry rows for doctor: configuration file keys.

<a id="doctor-schema_version"></a>
### `schema_version`

[VERIFIED] config key (YAML/JSON); tool `doctor`. Defined at `src/somnus_debug/doctor/core.py:451-479 (DEFAULT_CONFIG_DATA); dataclass src/somnus_debug/doctor/core.py:208-239`; read at `src/somnus_debug/doctor/core.py:822`.

| Field | Value |
|---|---|
| Default | 3.0 |
| Type | non-empty str |
| Valid values | any non-empty string; never compared to anything |
| Precedence | -c file value > DEFAULT_CONFIG_DATA (lists replaced, mappings deep-merged); no CLI override; no env |
| Effect | validated only (require_str); never checked for compatibility |
| Scope | run |
| Persistence | config_hash stored per run in SQLite |
| Failure behavior | int 3 -> exit 4; '99.9' accepted silently |
| Doc status | partial |
| Verification | VERIFIED |

<a id="doctor-min_function_lines"></a>
### `min_function_lines`

[SOURCE-CONFIRMED] config key (YAML/JSON); tool `doctor`. Defined at `src/somnus_debug/doctor/core.py:451-479 (DEFAULT_CONFIG_DATA); dataclass src/somnus_debug/doctor/core.py:208-239`; read at `src/somnus_debug/doctor/core.py:1292`.

| Field | Value |
|---|---|
| Default | 5 |
| Type | int>=1 |
| Valid values | int >=1 (bools rejected) |
| Precedence | -c file value > DEFAULT_CONFIG_DATA (lists replaced, mappings deep-merged); no CLI override; no env |
| Effect | functions with executable_line_count < N -> suspicious_short_functions |
| Scope | run |
| Persistence | config_hash stored per run in SQLite |
| Failure behavior | null/0/'4' -> exit 4 |
| Doc status | partial |
| Verification | SOURCE-CONFIRMED |

<a id="doctor-min_class_lines"></a>
### `min_class_lines`

[SOURCE-CONFIRMED] config key (YAML/JSON); tool `doctor`. Defined at `src/somnus_debug/doctor/core.py:451-479 (DEFAULT_CONFIG_DATA); dataclass src/somnus_debug/doctor/core.py:208-239`; read at `src/somnus_debug/doctor/core.py:1303`.

| Field | Value |
|---|---|
| Default | 6 |
| Type | int>=1 |
| Valid values | int >=1 |
| Precedence | -c file value > DEFAULT_CONFIG_DATA (lists replaced, mappings deep-merged); no CLI override; no env |
| Effect | class shortness threshold (dataclass/enum/exception exempt) |
| Scope | run |
| Persistence | config_hash stored per run in SQLite |
| Failure behavior | validation error -> ConfigurationError exit 4 |
| Doc status | partial |
| Verification | SOURCE-CONFIRMED |

<a id="doctor-min_docstring_length"></a>
### `min_docstring_length`

[SOURCE-CONFIRMED] config key (YAML/JSON); tool `doctor`. Defined at `src/somnus_debug/doctor/core.py:451-479 (DEFAULT_CONFIG_DATA); dataclass src/somnus_debug/doctor/core.py:208-239`; read at `src/somnus_debug/doctor/core.py:1169,1191,1258`.

| Field | Value |
|---|---|
| Default | 18 |
| Type | int>=1 |
| Valid values | int >=1 |
| Precedence | -c file value > DEFAULT_CONFIG_DATA (lists replaced, mappings deep-merged); no CLI override; no env |
| Effect | docstring shorter than N counts as missing (module/class/function) |
| Scope | run |
| Persistence | config_hash stored per run in SQLite |
| Failure behavior | validation error -> ConfigurationError exit 4 |
| Doc status | partial |
| Verification | SOURCE-CONFIRMED |

<a id="doctor-max_cyclomatic_complexity"></a>
### `max_cyclomatic_complexity`

[SOURCE-CONFIRMED] config key (YAML/JSON); tool `doctor`. Defined at `src/somnus_debug/doctor/core.py:451-479 (DEFAULT_CONFIG_DATA); dataclass src/somnus_debug/doctor/core.py:208-239`; read at `src/somnus_debug/doctor/core.py:1294`.

| Field | Value |
|---|---|
| Default | 12 |
| Type | int>=1 |
| Valid values | int >=1 |
| Precedence | -c file value > DEFAULT_CONFIG_DATA (lists replaced, mappings deep-merged); no CLI override; no env |
| Effect | complexity > N -> complexity issue |
| Scope | run |
| Persistence | config_hash stored per run in SQLite |
| Failure behavior | validation error -> ConfigurationError exit 4 |
| Doc status | partial |
| Verification | SOURCE-CONFIRMED |

<a id="doctor-max_report_evidence_lines"></a>
### `max_report_evidence_lines`

[SOURCE-CONFIRMED] config key (YAML/JSON); tool `doctor`. Defined at `src/somnus_debug/doctor/core.py:451-479 (DEFAULT_CONFIG_DATA); dataclass src/somnus_debug/doctor/core.py:208-239`; read at `src/somnus_debug/doctor/core.py:1087`.

| Field | Value |
|---|---|
| Default | 5 |
| Type | int>=1 |
| Valid values | int >=1 |
| Precedence | -c file value > DEFAULT_CONFIG_DATA (lists replaced, mappings deep-merged); no CLI override; no env |
| Effect | evidence radius = N//2 lines each side (1 -> only the line) |
| Scope | run |
| Persistence | config_hash stored per run in SQLite |
| Failure behavior | validation error -> ConfigurationError exit 4 |
| Doc status | missing |
| Verification | SOURCE-CONFIRMED |

<a id="doctor-include_patterns"></a>
### `include_patterns`

[VERIFIED] config key (YAML/JSON); tool `doctor`. Defined at `src/somnus_debug/doctor/core.py:451-479 (DEFAULT_CONFIG_DATA); dataclass src/somnus_debug/doctor/core.py:208-239`; read at `src/somnus_debug/doctor/core.py:949-952`.

| Field | Value |
|---|---|
| Default | ["*.py"] |
| Type | list[str] |
| Valid values | non-empty strings; empty list allowed |
| Precedence | -c file value > DEFAULT_CONFIG_DATA (lists replaced, mappings deep-merged); no CLI override; no env |
| Effect | fnmatch on rel path OR basename; '*' crosses '/', so 'src/**/*.py' needs >=1 subdir (drops src/c.py); case-sensitive on POSIX |
| Scope | run |
| Persistence | config_hash stored per run in SQLite |
| Failure behavior | [] -> 0 files, exit 0; string -> exit 4 |
| Doc status | partial |
| Verification | VERIFIED |
| Example / probe | include [c.py] matches src/c.py by basename; src/**/*.py -> only src/a/b.py; src/*.py -> src/c.py and src/a/b.py (W3 G2/G3/G6) |
| Notes | W3 corrected: added basename-match example |

<a id="doctor-ignore_patterns"></a>
### `ignore_patterns`

[VERIFIED] config key (YAML/JSON); tool `doctor`. Defined at `src/somnus_debug/doctor/core.py:451-479 (DEFAULT_CONFIG_DATA); dataclass src/somnus_debug/doctor/core.py:208-239`; read at `src/somnus_debug/doctor/core.py:937-947`.

| Field | Value |
|---|---|
| Default | 15 globs incl. env/*, build/*, venv/* |
| Type | list[str] |
| Valid values | non-empty strings |
| Precedence | -c file value > DEFAULT_CONFIG_DATA (lists replaced, mappings deep-merged); no CLI override; no env |
| Effect | match rel path or basename; 'X/*' also prunes ANY directory named X at any depth (pkg/env/ dropped); bare 'tests' prunes dirs named tests; replacing list drops ALL defaults (no merge) |
| Scope | run |
| Persistence | config_hash stored per run in SQLite |
| Failure behavior | validation error -> ConfigurationError exit 4 |
| Doc status | partial |
| Verification | VERIFIED |

<a id="doctor-ignore_functions"></a>
### `ignore_functions`

[VERIFIED] config key (YAML/JSON); tool `doctor`. Defined at `src/somnus_debug/doctor/core.py:451-479 (DEFAULT_CONFIG_DATA); dataclass src/somnus_debug/doctor/core.py:208-239`; read at `src/somnus_debug/doctor/core.py:1237-1238`.

| Field | Value |
|---|---|
| Default | ["__repr__","__str__"] |
| Type | list[str] |
| Valid values | bare names (not qualnames) |
| Precedence | -c file value > DEFAULT_CONFIG_DATA (lists replaced, mappings deep-merged); no CLI override; no env |
| Effect | matching function AND its entire body skipped (node.name in list, so any method or nested def with that bare name): security_risks/broad_exceptions/silent_failures inside are suppressed; with the DEFAULT list an eval() inside any __repr__/__str__ is never reported |
| Scope | run |
| Persistence | config_hash stored per run in SQLite |
| Failure behavior | validation error -> ConfigurationError exit 4 |
| Doc status | partial |
| Verification | VERIFIED |
| Example / probe | default config: eval in module-level __repr__ not reported; ignore_functions: [outer] -> __repr__ eval reported, outer.inner eval gone (W3 F0/F2) |
| Notes | W3 corrected: added default-value consequence: default list hides eval/exec inside any function named __repr__/__str__ (W3 F0); replacing the list re-exposes them (F2) |

<a id="doctor-ignore_classes"></a>
### `ignore_classes`

[SOURCE-CONFIRMED] config key (YAML/JSON); tool `doctor`. Defined at `src/somnus_debug/doctor/core.py:451-479 (DEFAULT_CONFIG_DATA); dataclass src/somnus_debug/doctor/core.py:208-239`; read at `src/somnus_debug/doctor/core.py:1271-1272`.

| Field | Value |
|---|---|
| Default | [] |
| Type | list[str] |
| Valid values | bare names |
| Precedence | -c file value > DEFAULT_CONFIG_DATA (lists replaced, mappings deep-merged); no CLI override; no env |
| Effect | only suppresses class-level docstring/stub/short-class issues; methods still analyzed |
| Scope | run |
| Persistence | config_hash stored per run in SQLite |
| Failure behavior | validation error -> ConfigurationError exit 4 |
| Doc status | partial |
| Verification | SOURCE-CONFIRMED |

<a id="doctor-check_private_functions"></a>
### `check_private_functions`

[VERIFIED] config key (YAML/JSON); tool `doctor`. Defined at `src/somnus_debug/doctor/core.py:451-479 (DEFAULT_CONFIG_DATA); dataclass src/somnus_debug/doctor/core.py:208-239`; read at `src/somnus_debug/doctor/core.py:1239-1241`.

| Field | Value |
|---|---|
| Default | false |
| Type | bool |
| Valid values | true\|false (YAML yes/no rejected) |
| Precedence | -c file value > DEFAULT_CONFIG_DATA (lists replaced, mappings deep-merged); no CLI override; no env |
| Effect | false: _private (non-dunder) funcs not recorded as functions (no docstring/hint/stub/short/complexity issues) but body still visited; issues inside are attributed to the enclosing symbol (e.g. <module>) |
| Scope | run |
| Persistence | config_hash stored per run in SQLite |
| Failure behavior | 'no' -> exit 4 |
| Doc status | missing |
| Verification | VERIFIED |
| Example / probe | exec in _priv reported with symbol <module> by default; with true -> symbol _priv (W3 F0/F3) |
| Notes | W3 corrected: added verified symbol attribution |

<a id="doctor-check_nested_functions"></a>
### `check_nested_functions`

[VERIFIED] config key (YAML/JSON); tool `doctor`. Defined at `src/somnus_debug/doctor/core.py:451-479 (DEFAULT_CONFIG_DATA); dataclass src/somnus_debug/doctor/core.py:208-239`; read at `src/somnus_debug/doctor/core.py:1235-1236`.

| Field | Value |
|---|---|
| Default | true |
| Type | bool |
| Valid values | true\|false |
| Precedence | -c file value > DEFAULT_CONFIG_DATA (lists replaced, mappings deep-merged); no CLI override; no env |
| Effect | false: nested defs AND their bodies skipped entirely (no security/except findings inside); nested check precedes private check |
| Scope | run |
| Persistence | config_hash stored per run in SQLite |
| Failure behavior | validation error -> ConfigurationError exit 4 |
| Doc status | missing |
| Verification | VERIFIED |

<a id="doctor-require_module_docstring"></a>
### `require_module_docstring`

[SOURCE-CONFIRMED] config key (YAML/JSON); tool `doctor`. Defined at `src/somnus_debug/doctor/core.py:451-479 (DEFAULT_CONFIG_DATA); dataclass src/somnus_debug/doctor/core.py:208-239`; read at `src/somnus_debug/doctor/core.py:1169`.

| Field | Value |
|---|---|
| Default | true |
| Type | bool |
| Valid values | true\|false |
| Precedence | -c file value > DEFAULT_CONFIG_DATA (lists replaced, mappings deep-merged); no CLI override; no env |
| Effect | module docstring check |
| Scope | run |
| Persistence | config_hash stored per run in SQLite |
| Failure behavior | validation error -> ConfigurationError exit 4 |
| Doc status | partial |
| Verification | SOURCE-CONFIRMED |

<a id="doctor-require_class_docstring"></a>
### `require_class_docstring`

[SOURCE-CONFIRMED] config key (YAML/JSON); tool `doctor`. Defined at `src/somnus_debug/doctor/core.py:451-479 (DEFAULT_CONFIG_DATA); dataclass src/somnus_debug/doctor/core.py:208-239`; read at `src/somnus_debug/doctor/core.py:1273`.

| Field | Value |
|---|---|
| Default | true |
| Type | bool |
| Valid values | true\|false |
| Precedence | -c file value > DEFAULT_CONFIG_DATA (lists replaced, mappings deep-merged); no CLI override; no env |
| Effect | class docstring check |
| Scope | run |
| Persistence | config_hash stored per run in SQLite |
| Failure behavior | validation error -> ConfigurationError exit 4 |
| Doc status | partial |
| Verification | SOURCE-CONFIRMED |

<a id="doctor-require_function_docstring"></a>
### `require_function_docstring`

[SOURCE-CONFIRMED] config key (YAML/JSON); tool `doctor`. Defined at `src/somnus_debug/doctor/core.py:451-479 (DEFAULT_CONFIG_DATA); dataclass src/somnus_debug/doctor/core.py:208-239`; read at `src/somnus_debug/doctor/core.py:1283`.

| Field | Value |
|---|---|
| Default | true |
| Type | bool |
| Valid values | true\|false |
| Precedence | -c file value > DEFAULT_CONFIG_DATA (lists replaced, mappings deep-merged); no CLI override; no env |
| Effect | function docstring check |
| Scope | run |
| Persistence | config_hash stored per run in SQLite |
| Failure behavior | validation error -> ConfigurationError exit 4 |
| Doc status | partial |
| Verification | SOURCE-CONFIRMED |

<a id="doctor-require_parameter_hints"></a>
### `require_parameter_hints`

[VERIFIED] config key (YAML/JSON); tool `doctor`. Defined at `src/somnus_debug/doctor/core.py:451-479 (DEFAULT_CONFIG_DATA); dataclass src/somnus_debug/doctor/core.py:208-239`; read at `src/somnus_debug/doctor/core.py:1412`.

| Field | Value |
|---|---|
| Default | true |
| Type | bool |
| Valid values | true\|false |
| Precedence | -c file value > DEFAULT_CONFIG_DATA (lists replaced, mappings deep-merged); no CLI override; no env |
| Effect | param/vararg/kwarg hint check (self/cls exempt) |
| Scope | run |
| Persistence | config_hash stored per run in SQLite |
| Failure behavior | validation error -> ConfigurationError exit 4 |
| Doc status | partial |
| Verification | VERIFIED |

<a id="doctor-require_return_hints"></a>
### `require_return_hints`

[VERIFIED] config key (YAML/JSON); tool `doctor`. Defined at `src/somnus_debug/doctor/core.py:451-479 (DEFAULT_CONFIG_DATA); dataclass src/somnus_debug/doctor/core.py:208-239`; read at `src/somnus_debug/doctor/core.py:1410`.

| Field | Value |
|---|---|
| Default | true |
| Type | bool |
| Valid values | true\|false |
| Precedence | -c file value > DEFAULT_CONFIG_DATA (lists replaced, mappings deep-merged); no CLI override; no env |
| Effect | return hint check |
| Scope | run |
| Persistence | config_hash stored per run in SQLite |
| Failure behavior | validation error -> ConfigurationError exit 4 |
| Doc status | partial |
| Verification | VERIFIED |

<a id="doctor-detect_unused_imports"></a>
### `detect_unused_imports`

[SOURCE-CONFIRMED] config key (YAML/JSON); tool `doctor`. Defined at `src/somnus_debug/doctor/core.py:451-479 (DEFAULT_CONFIG_DATA); dataclass src/somnus_debug/doctor/core.py:208-239`; read at `src/somnus_debug/doctor/core.py:1572`.

| Field | Value |
|---|---|
| Default | true |
| Type | bool |
| Valid values | true\|false |
| Precedence | -c file value > DEFAULT_CONFIG_DATA (lists replaced, mappings deep-merged); no CLI override; no env |
| Effect | unused_imports emission |
| Scope | run |
| Persistence | config_hash stored per run in SQLite |
| Failure behavior | validation error -> ConfigurationError exit 4 |
| Doc status | partial |
| Verification | SOURCE-CONFIRMED |

<a id="doctor-detect_test_gaps"></a>
### `detect_test_gaps`

[VERIFIED] config key (YAML/JSON); tool `doctor`. Defined at `src/somnus_debug/doctor/core.py:451-479 (DEFAULT_CONFIG_DATA); dataclass src/somnus_debug/doctor/core.py:208-239`; read at `(never read)`.

| Field | Value |
|---|---|
| Default | true |
| Type | bool |
| Valid values | true\|false |
| Precedence | -c file value > DEFAULT_CONFIG_DATA (lists replaced, mappings deep-merged); no CLI override; no env |
| Effect | NONE: validated at src/somnus_debug/doctor/core.py:840 but never read; no code emits test_gaps |
| Scope | run |
| Persistence | config_hash stored per run in SQLite |
| Failure behavior | false has no effect (same 9 issues) |
| Doc status | contradictory |
| Verification | VERIFIED |

<a id="doctor-detect_security_risks"></a>
### `detect_security_risks`

[VERIFIED] config key (YAML/JSON); tool `doctor`. Defined at `src/somnus_debug/doctor/core.py:451-479 (DEFAULT_CONFIG_DATA); dataclass src/somnus_debug/doctor/core.py:208-239`; read at `src/somnus_debug/doctor/core.py:1229`.

| Field | Value |
|---|---|
| Default | true |
| Type | bool |
| Valid values | true\|false |
| Precedence | -c file value > DEFAULT_CONFIG_DATA (lists replaced, mappings deep-merged); no CLI override; no env |
| Effect | SECURITY_CALLS detection |
| Scope | run |
| Persistence | config_hash stored per run in SQLite |
| Failure behavior | validation error -> ConfigurationError exit 4 |
| Doc status | partial |
| Verification | VERIFIED |

<a id="doctor-detect_silent_failures"></a>
### `detect_silent_failures`

[VERIFIED] config key (YAML/JSON); tool `doctor`. Defined at `src/somnus_debug/doctor/core.py:451-479 (DEFAULT_CONFIG_DATA); dataclass src/somnus_debug/doctor/core.py:208-239`; read at `src/somnus_debug/doctor/core.py:1222`.

| Field | Value |
|---|---|
| Default | true |
| Type | bool |
| Valid values | true\|false |
| Precedence | -c file value > DEFAULT_CONFIG_DATA (lists replaced, mappings deep-merged); no CLI override; no env |
| Effect | silent_failures only; broad_exceptions has NO toggle |
| Scope | run |
| Persistence | config_hash stored per run in SQLite |
| Failure behavior | validation error -> ConfigurationError exit 4 |
| Doc status | partial |
| Verification | VERIFIED |

<a id="doctor-detect_dependency_cycles"></a>
### `detect_dependency_cycles`

[SOURCE-CONFIRMED] config key (YAML/JSON); tool `doctor`. Defined at `src/somnus_debug/doctor/core.py:451-479 (DEFAULT_CONFIG_DATA); dataclass src/somnus_debug/doctor/core.py:208-239`; read at `src/somnus_debug/doctor/core.py:1631`.

| Field | Value |
|---|---|
| Default | true |
| Type | bool |
| Valid values | true\|false |
| Precedence | -c file value > DEFAULT_CONFIG_DATA (lists replaced, mappings deep-merged); no CLI override; no env |
| Effect | cycle detection (missing_imports has no toggle) |
| Scope | run |
| Persistence | config_hash stored per run in SQLite |
| Failure behavior | validation error -> ConfigurationError exit 4 |
| Doc status | partial |
| Verification | SOURCE-CONFIRMED |

<a id="doctor-state_dir"></a>
### `state_dir`

[VERIFIED] config key (YAML/JSON); tool `doctor`. Defined at `src/somnus_debug/doctor/core.py:451-479 (DEFAULT_CONFIG_DATA); dataclass src/somnus_debug/doctor/core.py:208-239`; read at `src/somnus_debug/doctor/core.py:1923`.

| Field | Value |
|---|---|
| Default | .python_doctor |
| Type | non-empty str |
| Valid values | any; absolute or '../' accepted (escapes project root) |
| Precedence | -c file value > DEFAULT_CONFIG_DATA (lists replaced, mappings deep-merged); no CLI override; no env |
| Effect | <project_root>/<state_dir>; ignore default '.python_doctor/*' not updated if renamed |
| Scope | run |
| Persistence | config_hash stored per run in SQLite |
| Failure behavior | '' -> exit 4 |
| Doc status | missing |
| Verification | VERIFIED |

<a id="doctor-reports_dir"></a>
### `reports_dir`

[VERIFIED] config key (YAML/JSON); tool `doctor`. Defined at `src/somnus_debug/doctor/core.py:451-479 (DEFAULT_CONFIG_DATA); dataclass src/somnus_debug/doctor/core.py:208-239`; read at `src/somnus_debug/doctor/core.py:1925`.

| Field | Value |
|---|---|
| Default | reports |
| Type | non-empty str |
| Valid values | any; '../..' accepted |
| Precedence | -c file value > DEFAULT_CONFIG_DATA (lists replaced, mappings deep-merged); no CLI override; no env |
| Effect | <state_root>/<reports_dir> |
| Scope | run |
| Persistence | config_hash stored per run in SQLite |
| Failure behavior | validation error -> ConfigurationError exit 4 |
| Doc status | missing |
| Verification | VERIFIED |

<a id="doctor-report_basename"></a>
### `report_basename`

[VERIFIED] config key (YAML/JSON); tool `doctor`. Defined at `src/somnus_debug/doctor/core.py:451-479 (DEFAULT_CONFIG_DATA); dataclass src/somnus_debug/doctor/core.py:208-239`; read at `src/somnus_debug/doctor/core.py:1958-1960`.

| Field | Value |
|---|---|
| Default | production_doctor_report |
| Type | non-empty str |
| Valid values | any; slashes create subdirs |
| Precedence | -c file value > DEFAULT_CONFIG_DATA (lists replaced, mappings deep-merged); no CLI override; no env |
| Effect | default md/json filename in project root and per-run copies |
| Scope | run |
| Persistence | config_hash stored per run in SQLite |
| Failure behavior | '  ' -> exit 4 |
| Doc status | missing |
| Verification | VERIFIED |
| Notes | W3 corrected: read_at narrowed to the lines that read it |

<a id="doctor-severity_exit_level"></a>
### `severity_exit_level`

[VERIFIED] config key (YAML/JSON); tool `doctor`. Defined at `src/somnus_debug/doctor/core.py:451-479 (DEFAULT_CONFIG_DATA); dataclass src/somnus_debug/doctor/core.py:208-239`; read at `src/somnus_debug/doctor/core.py:818-820,2046-2058`.

| Field | Value |
|---|---|
| Default | serious |
| Type | str |
| Valid values | critical\|serious\|minor\|info\|none (case-sensitive) |
| Precedence | -c file value > DEFAULT_CONFIG_DATA (lists replaced, mappings deep-merged); no CLI override; no env |
| Effect | exit gate: critical->2 on critical; serious->2 crit /1 serious; minor->1 on crit\|serious\|minor; info->1 on any; none->0 |
| Scope | run |
| Persistence | config_hash stored per run in SQLite |
| Failure behavior | UNQUOTED none parses as null -> exit 4; CRITICAL -> exit 4 |
| Doc status | partial: none/info undocumented; MANUAL 3.4 and QUICKSTART say minor fails 'on anything at all' but info-only findings pass the minor gate (D:2054-2055) |
| Verification | VERIFIED |
| Notes | W3 corrected: added doc discrepancy on 'minor' gate wording |

<a id="doctor-max_workers"></a>
### `max_workers`

[VERIFIED] config key (YAML/JSON); tool `doctor`. Defined at `src/somnus_debug/doctor/core.py:451-479 (DEFAULT_CONFIG_DATA); dataclass src/somnus_debug/doctor/core.py:208-239`; read at `src/somnus_debug/doctor/core.py:1720`.

| Field | Value |
|---|---|
| Default | 4 |
| Type | int>=1 |
| Valid values | int >=1 |
| Precedence | -c file value > DEFAULT_CONFIG_DATA (lists replaced, mappings deep-merged); no CLI override; no env |
| Effect | ThreadPoolExecutor size = min(N, files); 1 -> sequential path |
| Scope | run |
| Persistence | config_hash stored per run in SQLite |
| Failure behavior | 0/'4' -> exit 4; config-only (no -j) |
| Doc status | partial |
| Verification | VERIFIED |

<a id="doctor-markdown_include_css"></a>
### `markdown_include_css`

[VERIFIED] config key (YAML/JSON); tool `doctor`. Defined at `src/somnus_debug/doctor/core.py:451-479 (DEFAULT_CONFIG_DATA); dataclass src/somnus_debug/doctor/core.py:208-239`; read at `src/somnus_debug/doctor/core.py:1786`.

| Field | Value |
|---|---|
| Default | true |
| Type | bool |
| Valid values | true\|false |
| Precedence | -c file value > DEFAULT_CONFIG_DATA (lists replaced, mappings deep-merged); no CLI override; no env |
| Effect | prepends <style> block to markdown report |
| Scope | run |
| Persistence | config_hash stored per run in SQLite |
| Failure behavior | 'no' -> exit 4 |
| Doc status | missing |
| Verification | VERIFIED |

<a id="doctor-severity_levels"></a>
### `severity_levels`

[VERIFIED] config key (YAML/JSON); tool `doctor`. Defined at `src/somnus_debug/doctor/core.py:480-501 (DEFAULT_CONFIG_DATA); dataclass src/somnus_debug/doctor/core.py:208-239`; read at `src/somnus_debug/doctor/core.py:792-794`.

| Field | Value |
|---|---|
| Default | 20-category table (see findings) |
| Type | mapping str->str |
| Valid values | critical\|serious\|minor\|info (lowercase) |
| Precedence | -c file value > DEFAULT_CONFIG_DATA (lists replaced, mappings deep-merged); no CLI override; no env |
| Effect | per-category severity; DEEP-MERGED (partial override ok); unknown categories accepted silently; categories absent -> MINOR |
| Scope | run |
| Persistence | config_hash stored per run in SQLite |
| Failure behavior | '{}' (flow mapping) -> string -> exit 4; 'SERIOUS' -> exit 4 |
| Doc status | partial |
| Verification | VERIFIED |

<a id="doctor-unknown-config-keys"></a>
### `<unknown config keys>`

[VERIFIED] config key; tool `doctor`. Defined at `src/somnus_debug/doctor/core.py:816-851`; read at `never`.

| Field | Value |
|---|---|
| Type | any |
| Effect | silently ignored (no warning) - typos like detect_silent_failure: false have no effect |
| Scope | run |
| Persistence | included in config_hash |
| Failure behavior | silent |
| Doc status | missing |
| Verification | VERIFIED |
| Example / probe | detect_silent_failure: false -> same 9 issues, exit 1 |

## doctor: files, parser, merge, constants, and implicit inputs

This section documents the 22 registry rows for doctor: files, parser, merge, constants, and implicit inputs.

<a id="doctor-production_doctorlog"></a>
### `production_doctor.log`

[VERIFIED] implicit file; tool `doctor`. Defined at `src/somnus_debug/doctor/core.py:2179-2181`; read at `src/somnus_debug/doctor/core.py:2186`.

| Field | Value |
|---|---|
| Default | ./production_doctor.log (CWD), append |
| Precedence | not configurable |
| Effect | created on EVERY doctor invocation incl. --help; receives only error/critical records |
| Scope | process cwd |
| Persistence | persists |
| Doc status | existing (QUICKSTART 'Files generated') |
| Verification | VERIFIED |
| Example / probe | doctor --help creates empty production_doctor.log |

<a id="doctor-default_config_data"></a>
### `DEFAULT_CONFIG_DATA`

[VERIFIED] in-code default; tool `doctor`. Defined at `src/somnus_debug/doctor/core.py:451-502`; read at `src/somnus_debug/doctor/core.py:799,811,813`.

| Field | Value |
|---|---|
| Default | (authoritative runtime default) |
| Type | dict |
| Precedence | lowest layer, always applied |
| Doc status | partial |
| Verification | VERIFIED |
| Example / probe | equal to init-config output and default_config.yaml (parsed) |

<a id="doctor-configmanagerdefault_yaml"></a>
### `ConfigManager.default_yaml()`

[VERIFIED] init-config template; tool `doctor`. Defined at `src/somnus_debug/doctor/core.py:853-925`; read at `src/somnus_debug/doctor/core.py:2101`.

| Field | Value |
|---|---|
| Type | str |
| Precedence | only written by init-config |
| Effect | text identical to default_config.yaml body (no comments) |
| Doc status | contradictory (QUICKSTART says generated file has comments) |
| Verification | VERIFIED |
| Notes | W3 corrected: read_at line drift (2100 -> 2101) |

<a id="doctor-doctordefault_configyaml"></a>
### `doctor/default_config.yaml`

[VERIFIED] packaged file; tool `doctor`. Defined at `src/somnus_debug/doctor/default_config.yaml:33-99`; read at `tests/test_cli_smoke.py:90,117 only`.

| Field | Value |
|---|---|
| Precedence | NEVER read at runtime |
| Effect | reference copy only |
| Doc status | existing (README 'reference copy') |
| Verification | VERIFIED |

<a id="doctor-root-python_doctoryaml"></a>
### `root python_doctor.yaml`

[VERIFIED] repo file; tool `doctor`. Defined at `python_doctor.yaml`; read at `nothing`.

| Field | Value |
|---|---|
| Precedence | never auto-loaded |
| Effect | Somnus-specific include globs (tools/*.py, test/*.py...) -> 0 files on other repos if passed with -c |
| Doc status | existing (MANUAL 7.1) |
| Verification | VERIFIED |

<a id="doctor-yaml-mini-parser"></a>
### `YAML mini-parser`

[VERIFIED] parser; tool `doctor`. Defined at `src/somnus_debug/doctor/core.py:596-723`; read at `src/somnus_debug/doctor/core.py:813 (via ConfigManager._load_raw)`.

| Field | Value |
|---|---|
| Valid values | see wiki/06-configuration/file-based-configuration.md (Y01-Y58) |
| Effect | subset: block mappings, block sequences of scalars, inline [a,b] lists, quoted scalars via ast.literal_eval, # comments |
| Failure behavior | many silent mis-parses (see configuration-findings.md section 3) |
| Doc status | missing |
| Verification | VERIFIED |
| Notes | W3 corrected: pointer refined: scalar rules at 619-643 (null 627-628, inline list 634-638, int 639-640, float 641-642) |

<a id="doctor-json-config"></a>
### `JSON config`

[VERIFIED] config file; tool `doctor`. Defined at `src/somnus_debug/doctor/core.py:802-811`; read at `src/somnus_debug/doctor/core.py:2063`.

| Field | Value |
|---|---|
| Valid values | object root |
| Precedence | deep-merged over defaults like YAML |
| Effect | alternate format (legacy) |
| Scope | run |
| Failure behavior | non-object root/malformed -> exit 4; null value -> exit 4 |
| Doc status | partial |
| Verification | VERIFIED |
| Notes | W3 corrected: defined_at narrowed |

<a id="doctor-active-interpreter-syspath--pythonpath--cwd"></a>
### `active interpreter sys.path / PYTHONPATH / cwd`

[VERIFIED] implicit env; tool `doctor`. Defined at `src/somnus_debug/doctor/core.py:1001,1050-1055`; read at `src/somnus_debug/doctor/core.py:1012-1016`.

| Field | Value |
|---|---|
| Effect | missing_imports resolution uses importlib.util.find_spec in the RUNNING interpreter; `python -m` puts CWD on sys.path, console script does not |
| Scope | process |
| Dependencies | Python>=3.10 (sys.stdlib_module_names) |
| Failure behavior | results differ by venv/cwd |
| Doc status | missing |
| Verification | VERIFIED |
| Example / probe | import zzlocalonly: python -m -> 0 issues; python -P -> missing_imports |

<a id="doctor-security_calls--todo_patterns--placeholder_constants"></a>
### `SECURITY_CALLS / TODO_PATTERNS / PLACEHOLDER_CONSTANTS`

[SOURCE-CONFIRMED] internal constants; tool `doctor`. Defined at `src/somnus_debug/doctor/core.py:504-514`; read at `src/somnus_debug/doctor/core.py:1229,1558,1451-1469`.

| Field | Value |
|---|---|
| Default | see findings 6.3 |
| Precedence | not configurable |
| Effect | detection vocabularies (TODO/FIXME/HACK/XXX/TEMP/WIP case-insensitive; 13 security call names) |
| Doc status | partial |
| Verification | SOURCE-CONFIRMED |

<a id="doctor-cycle-search-limits"></a>
### `cycle search limits`

[SOURCE-CONFIRMED] internal constants; tool `doctor`. Defined at `src/somnus_debug/doctor/core.py:1642,1653`; read at `src/somnus_debug/doctor/core.py:1631`.

| Field | Value |
|---|---|
| Default | stop after 100 cycles; DFS path depth < 30 |
| Precedence | not configurable |
| Effect | cycle detection truncation |
| Failure behavior | silent truncation |
| Doc status | missing |
| Verification | SOURCE-CONFIRMED |

<a id="doctor-readiness-score-weights"></a>
### `readiness score weights`

[SOURCE-CONFIRMED] internal constants; tool `doctor`. Defined at `src/somnus_debug/doctor/core.py:1772`; read at `src/somnus_debug/doctor/core.py:1772`.

| Field | Value |
|---|---|
| Default | 100 - 20*critical - 8*serious - 2*minor - 1*info (floor 0) |
| Precedence | not configurable |
| Effect | score in summary |
| Doc status | missing |
| Verification | SOURCE-CONFIRMED |

<a id="doctor-run_id_format"></a>
### `RUN_ID_FORMAT`

[SOURCE-CONFIRMED] internal constant; tool `doctor`. Defined at `src/somnus_debug/doctor/core.py:82`; read at `src/somnus_debug/doctor/core.py:532`.

| Field | Value |
|---|---|
| Default | %Y%m%dT%H%M%SZ (UTC, 1-second resolution) |
| Precedence | not configurable |
| Effect | run_id and per-run report dir; two state-enabled scans within one second share run_id (INSERT OR REPLACE) |
| Doc status | partial |
| Verification | SOURCE-CONFIRMED |
| Example / probe | 20261112T001316Z |

<a id="doctor-unknown-severity-category-fallback"></a>
### `unknown severity category fallback`

[SOURCE-CONFIRMED] implicit default; tool `doctor`. Defined at `src/somnus_debug/doctor/core.py:794`; read at `src/somnus_debug/doctor/core.py:1081,1737,1747`.

| Field | Value |
|---|---|
| Default | MINOR |
| Precedence | severity_levels entry > MINOR |
| Effect | category missing from severity_levels gets minor |
| Doc status | missing |
| Verification | SOURCE-CONFIRMED |

<a id="doctor-default_config_name"></a>
### `DEFAULT_CONFIG_NAME`

[SOURCE-CONFIRMED] in-code constant; tool `doctor`. Defined at `src/somnus_debug/doctor/core.py:81`; read at `src/somnus_debug/doctor/core.py:2143`.

| Field | Value |
|---|---|
| Default | python_doctor.yaml |
| Type | str |
| Precedence | used only as the init-config -o default |
| Effect | names the file init-config writes; never used to LOAD a config (no auto-discovery) |
| Scope | process |
| Doc status | missing |
| Verification | SOURCE-CONFIRMED |
| Example / probe | grep: only core.py:81 and :2143 reference it |
| Notes | W3 added |

<a id="doctor-config_hash"></a>
### `config_hash`

[VERIFIED] derived value; tool `doctor`. Defined at `src/somnus_debug/doctor/core.py:790`; read at `src/somnus_debug/doctor/core.py:1975`.

| Field | Value |
|---|---|
| Default | sha of merged raw config |
| Type | str |
| Effect | hash of the MERGED raw mapping (unknown keys included) stored in JSON reports and the runs table; never compared by doctor or delta.py |
| Scope | run |
| Persistence | SQLite runs.config_hash, report JSON |
| Doc status | missing |
| Verification | VERIFIED |
| Example / probe | max_workers: 1 changes config_hash but not findings (W3 M3); replacing ConfigManager.config at runtime does NOT change it (W3 RT2) |
| Notes | W3 added |

<a id="doctor-deep_merge"></a>
### `deep_merge`

[VERIFIED] merge rule; tool `doctor`. Defined at `src/somnus_debug/doctor/core.py:726-734`; read at `src/somnus_debug/doctor/core.py:799,811,813`.

| Field | Value |
|---|---|
| Precedence | file > in-code default per key |
| Effect | file mapping merged over DEFAULT_CONFIG_DATA: nested dicts (only severity_levels) merge key-by-key; lists and scalars replace wholesale |
| Scope | run |
| Doc status | missing |
| Verification | VERIFIED |
| Example / probe | severity_levels {security_risks: info, stubs: info} keeps the other 18 defaults (W3 E4a); ignore_patterns [*.pyc] drops all 15 defaults so .venv is scanned (W3 E4b) |
| Notes | W3 added |

<a id="doctor-require_--detect_-bool-validation"></a>
### `require_* / detect_* bool validation`

[VERIFIED] validation rule; tool `doctor`. Defined at `src/somnus_debug/doctor/core.py:737-742`; read at `src/somnus_debug/doctor/core.py:832-849`.

| Field | Value |
|---|---|
| Type | bool |
| Valid values | true\|false (any case); yes/no/on/off are strings and rejected |
| Failure behavior | ConfigurationError exit 4 |
| Doc status | missing |
| Verification | VERIFIED |
| Example / probe | detect_security_risks: yes -> exit 4 (W3 E7d) |
| Notes | W3 added |

<a id="doctor-ignore_patterns-backslash-normalization"></a>
### `ignore_patterns backslash normalization`

[SOURCE-CONFIRMED] implicit; tool `doctor`. Defined at `src/somnus_debug/doctor/core.py:942`.

| Field | Value |
|---|---|
| Effect | each ignore pattern has \ replaced by / before matching (include_patterns get no such normalization) |
| Scope | run |
| Doc status | missing |
| Verification | SOURCE-CONFIRMED |
| Notes | W3 added |

<a id="doctor-severity-values"></a>
### `Severity values`

[SOURCE-CONFIRMED] enum; tool `doctor`. Defined at `src/somnus_debug/doctor/core.py:86-93`; read at `src/somnus_debug/doctor/core.py:774-778`.

| Field | Value |
|---|---|
| Valid values | critical\|serious\|minor\|info (lowercase, exact) |
| Effect | the only accepted severity_levels values |
| Failure behavior | other value -> exit 4 |
| Doc status | partial |
| Verification | SOURCE-CONFIRMED |
| Notes | W3 added |

<a id="doctor-projectscannerconfigmanager-runtime-override"></a>
### `ProjectScanner/ConfigManager runtime override`

[VERIFIED] library; tool `doctor`. Defined at `src/somnus_debug/doctor/core.py:782-790,1695-1703`; read at `src/somnus_debug/doctor/core.py:1702`.

| Field | Value |
|---|---|
| Type | DoctorConfig (frozen dataclass) |
| Precedence | whatever ConfigManager.config holds when ProjectScanner is constructed |
| Effect | programmatic configuration: ConfigManager(None or Path) then optionally cm.config = dataclasses.replace(cm.config, ...); DoctorConfig itself is frozen |
| Scope | process |
| Persistence | none (no disk/log writes from ProjectScanner.scan) |
| Failure behavior | direct attribute assignment on DoctorConfig -> FrozenInstanceError; replaced config bypasses validation and config_hash |
| Doc status | missing (MANUAL 8 shows CLI-level library use only) |
| Verification | VERIFIED |
| Example / probe | include_patterns=('pkg/*.py',) via replace -> files 3->2; config_hash unchanged (W3 RT2/RT3) |
| Notes | W3 added; see D-12 |

<a id="doctor-root-duplicate-python_production_doctorpy"></a>
### `root duplicate python_production_doctor.py`

[SOURCE-CONFIRMED] repo script; tool `doctor`. Defined at `python_production_doctor.py:81,2130-2162`.

| Field | Value |
|---|---|
| Default | same options as src doctor |
| Effect | same CLI and config keys as src doctor; lacks the SQLite-unavailable fallback (state errors exit 4 instead of warning) |
| Scope | process |
| Doc status | existing (MANUAL 7.5) |
| Verification | SOURCE-CONFIRMED |
| Notes | W3 added; per lane-b section 8 diff; see D-28 |

<a id="doctor-pythonpath--pythonsafepath--python--p--cwd-on-syspath"></a>
### `PYTHONPATH / PYTHONSAFEPATH / python -P / CWD on sys.path`

[VERIFIED] env var (interpreter); tool `doctor`. Defined at `-`; read at `src/somnus_debug/doctor/core.py:1050-1055`.

| Field | Value |
|---|---|
| Default | interpreter defaults |
| Precedence | interpreter-level; no doctor setting overrides it |
| Effect | missing_imports classification uses importlib.util.find_spec in the RUNNING interpreter: python -m adds CWD; -P/PYTHONSAFEPATH=1 removes it; PYTHONPATH adds roots |
| Scope | process |
| Failure behavior | same tree gives different missing_imports by invocation |
| Doc status | missing |
| Verification | VERIFIED |
| Example / probe | ENV1 python -m from a cwd holding zzlocalonly.py: only calc missing; ENV2 -P and ENV3 PYTHONSAFEPATH=1: calc + zzlocalonly; ENV4 -P + PYTHONPATH+=src: only zzlocalonly (W3) |
| Notes | W3 added; see D-22, D-26 |

## pycache-clean

This section documents the 20 registry rows for pycache-clean.

<a id="pycache-clean---config"></a>
### `--config`

[VERIFIED] CLI flag; tool `pycache-clean`. Defined at `src/somnus_debug/pycache_cleaner/core.py:340`; read at `src/somnus_debug/pycache_cleaner/core.py:351`.

| Field | Value |
|---|---|
| Default | config.yaml (relative to CWD) |
| Type | path |
| Valid values | existing YAML file |
| Precedence | no auto-discovery beyond CWD default |
| Effect | config path; expanduser applied |
| Scope | run |
| Dependencies | PyYAML |
| Failure behavior | missing -> stderr msg, exit 1 |
| Doc status | contradictory (module docstring: 'default config.yaml in the same directory') |
| Verification | VERIFIED |
| Example / probe | no config.yaml in cwd -> exit 1 |

<a id="pycache-clean---dry-run"></a>
### `--dry-run`

[VERIFIED] CLI flag; tool `pycache-clean`. Defined at `src/somnus_debug/pycache_cleaner/core.py:342`; read at `src/somnus_debug/pycache_cleaner/core.py:357-358`.

| Field | Value |
|---|---|
| Default | False (config value kept) |
| Type | flag |
| Precedence | CLI (only when set) > YAML > dataclass default |
| Effect | can only force True; no --no-dry-run, so config dry_run:true cannot be overridden live |
| Scope | run |
| Doc status | existing |
| Verification | VERIFIED |
| Notes | W3 corrected: read_at line drift |

<a id="pycache-clean---verbose"></a>
### `--verbose`

[VERIFIED] CLI flag; tool `pycache-clean`. Defined at `src/somnus_debug/pycache_cleaner/core.py:343`; read at `src/somnus_debug/pycache_cleaner/core.py:359-360`.

| Field | Value |
|---|---|
| Default | False (config value kept) |
| Type | flag |
| Precedence | CLI (only when set) > YAML > dataclass default |
| Effect | can only force True |
| Scope | run |
| Doc status | existing |
| Verification | VERIFIED |
| Notes | W3 corrected: read_at line drift |

<a id="pycache-clean---max-depth"></a>
### `--max-depth`

[VERIFIED] CLI flag; tool `pycache-clean`. Defined at `src/somnus_debug/pycache_cleaner/core.py:344`; read at `src/somnus_debug/pycache_cleaner/core.py:361-362`.

| Field | Value |
|---|---|
| Default | None (config value kept) |
| Type | int |
| Precedence | CLI (only when set) > YAML > dataclass default |
| Effect | int; overrides config incl. to 0; negative -> nothing processed |
| Scope | run |
| Doc status | existing |
| Verification | VERIFIED |
| Example / probe | YAML max_depth: 0 + --max-depth 5 -> deeper caches deleted (W3 P6) |
| Notes | W3 corrected: read_at line drift; added verified CLI-over-YAML example |

<a id="pycache-clean---follow-symlinks"></a>
### `--follow-symlinks`

[SOURCE-CONFIRMED] CLI flag; tool `pycache-clean`. Defined at `src/somnus_debug/pycache_cleaner/core.py:345`; read at `src/somnus_debug/pycache_cleaner/core.py:363-364`.

| Field | Value |
|---|---|
| Default | False (config value kept) |
| Type | flag |
| Precedence | CLI (only when set) > YAML > dataclass default |
| Effect | can only force True |
| Scope | run |
| Doc status | existing |
| Verification | SOURCE-CONFIRMED |
| Notes | W3 corrected: read_at line drift |

<a id="pycache-clean-roots"></a>
### `roots`

[VERIFIED] config key (PyYAML); tool `pycache-clean`. Defined at `src/somnus_debug/pycache_cleaner/core.py:160-167`; read at `src/somnus_debug/pycache_cleaner/core.py:171-179 (setattr, no type validation)`.

| Field | Value |
|---|---|
| Default | [] |
| Type | list[str] |
| Valid values | required non-empty; relative paths resolved against CWD (not config dir); ~ expanded; $VARS NOT expanded |
| Precedence | YAML > dataclass default; CLI flag only overrides when set |
| Effect | roots |
| Scope | run |
| Persistence | log_file only |
| Dependencies | PyYAML safe_load |
| Failure behavior | string value iterated per character (each char a 'root') |
| Doc status | contradictory (docstring claims env vars expanded) |
| Verification | VERIFIED |

<a id="pycache-clean-exclude"></a>
### `exclude`

[VERIFIED] config key (PyYAML); tool `pycache-clean`. Defined at `src/somnus_debug/pycache_cleaner/core.py:160-167`; read at `src/somnus_debug/pycache_cleaner/core.py:171-179 (setattr, no type validation)`.

| Field | Value |
|---|---|
| Default | [] |
| Type | list[str] |
| Valid values | fnmatchcase against directory BASENAME only, case-sensitive |
| Precedence | YAML > dataclass default; CLI flag only overrides when set |
| Effect | exclude |
| Scope | run |
| Persistence | log_file only |
| Dependencies | PyYAML safe_load |
| Failure behavior | 'node_modules/*' (MANUAL example) never matches; null -> TypeError exit 1; string -> per-char patterns |
| Doc status | contradictory (MANUAL 5.1 example uses node_modules/* globs) |
| Verification | VERIFIED |

<a id="pycache-clean-targets"></a>
### `targets`

[VERIFIED] config key (PyYAML); tool `pycache-clean`. Defined at `src/somnus_debug/pycache_cleaner/core.py:160-167`; read at `src/somnus_debug/pycache_cleaner/core.py:171-179 (setattr, no type validation)`.

| Field | Value |
|---|---|
| Default | [__pycache__, *.pyc, *.pyo] |
| Type | list[str] |
| Valid values | entries without * or ? = directory names; with wildcard = file patterns |
| Precedence | YAML > dataclass default; CLI flag only overrides when set |
| Effect | targets |
| Scope | run |
| Persistence | log_file only |
| Dependencies | PyYAML safe_load |
| Failure behavior | replaces defaults entirely; null -> TypeError traceback exit 1 |
| Doc status | partial |
| Verification | VERIFIED |

<a id="pycache-clean-dry_run"></a>
### `dry_run`

[VERIFIED] config key (PyYAML); tool `pycache-clean`. Defined at `src/somnus_debug/pycache_cleaner/core.py:160-167`; read at `src/somnus_debug/pycache_cleaner/core.py:171-179 (setattr, no type validation)`.

| Field | Value |
|---|---|
| Default | false |
| Type | bool (unvalidated) |
| Valid values | YAML bool |
| Precedence | YAML > dataclass default; CLI flag only overrides when set |
| Effect | dry_run |
| Scope | run |
| Persistence | log_file only |
| Dependencies | PyYAML safe_load |
| Failure behavior | quoted "false" is truthy -> dry run while log prints dry_run=false; YAML 1.1 'no'/'off' = False -> LIVE delete |
| Doc status | partial (MANUAL 5.1 says omit/false deletes; YAML 1.1 no/off also delete; quoted 'false' does not) |
| Verification | VERIFIED |
| Notes | W3 corrected: added MANUAL wording check |

<a id="pycache-clean-verbose"></a>
### `verbose`

[VERIFIED] config key (PyYAML); tool `pycache-clean`. Defined at `src/somnus_debug/pycache_cleaner/core.py:160-167`; read at `src/somnus_debug/pycache_cleaner/core.py:171-179 (setattr, no type validation)`.

| Field | Value |
|---|---|
| Default | false |
| Type | bool |
| Precedence | YAML > dataclass default; CLI flag only overrides when set |
| Effect | verbose |
| Scope | run |
| Persistence | log_file only |
| Dependencies | PyYAML safe_load |
| Failure behavior | DEBUG level + per-item 'Removed' lines; ignored if any unknown key present |
| Doc status | partial |
| Verification | VERIFIED |

<a id="pycache-clean-max_depth"></a>
### `max_depth`

[VERIFIED] config key (PyYAML); tool `pycache-clean`. Defined at `src/somnus_debug/pycache_cleaner/core.py:160-167`; read at `src/somnus_debug/pycache_cleaner/core.py:171-179 (setattr, no type validation)`.

| Field | Value |
|---|---|
| Default | null |
| Type | int\|null |
| Valid values | 0 = root only |
| Precedence | YAML > dataclass default; CLI flag only overrides when set |
| Effect | max_depth |
| Scope | run |
| Persistence | log_file only |
| Dependencies | PyYAML safe_load |
| Failure behavior | string -> TypeError, exit 1 |
| Doc status | existing |
| Verification | VERIFIED |

<a id="pycache-clean-follow_symlinks"></a>
### `follow_symlinks`

[SOURCE-CONFIRMED] config key (PyYAML); tool `pycache-clean`. Defined at `src/somnus_debug/pycache_cleaner/core.py:160-167`; read at `src/somnus_debug/pycache_cleaner/core.py:171-179 (setattr, no type validation)`.

| Field | Value |
|---|---|
| Default | false |
| Type | bool |
| Precedence | YAML > dataclass default; CLI flag only overrides when set |
| Effect | follow_symlinks |
| Scope | run |
| Persistence | log_file only |
| Dependencies | PyYAML safe_load |
| Failure behavior | false: symlinked dirs/files neither traversed nor deleted |
| Doc status | existing |
| Verification | SOURCE-CONFIRMED |

<a id="pycache-clean-log_file"></a>
### `log_file`

[VERIFIED] config key (PyYAML); tool `pycache-clean`. Defined at `src/somnus_debug/pycache_cleaner/core.py:160-167`; read at `src/somnus_debug/pycache_cleaner/core.py:171-179 (setattr, no type validation)`.

| Field | Value |
|---|---|
| Default | null |
| Type | str\|null |
| Valid values | path; ~ expanded; relative -> CWD |
| Precedence | YAML > dataclass default; CLI flag only overrides when set |
| Effect | log_file |
| Scope | run |
| Persistence | log_file only |
| Dependencies | PyYAML safe_load |
| Failure behavior | append mode; file created but stays EMPTY if any unknown key present; open failure -> stderr note, continues |
| Doc status | partial |
| Verification | VERIFIED |

<a id="pycache-clean-unknown-pycache-keys"></a>
### `<unknown pycache keys>`

[VERIFIED] config key; tool `pycache-clean`. Defined at `src/somnus_debug/pycache_cleaner/core.py:176-179`.

| Field | Value |
|---|---|
| Effect | logging.warning() BEFORE setup_logging -> implicit root handler; later basicConfig is a no-op: INFO output (incl. Summary), verbose and log_file all lost |
| Scope | process |
| Failure behavior | silent loss of output |
| Doc status | partial (MANUAL: 'logged as warnings and ignored, not fatal') |
| Verification | VERIFIED |
| Example / probe | bogus_key:1 -> only WARNING line printed, run.log 0 lines |

<a id="pycache-clean-emptynon-mapping-yaml"></a>
### `empty/non-mapping YAML`

[VERIFIED] config file; tool `pycache-clean`. Defined at `src/somnus_debug/pycache_cleaner/core.py:173`; read at `src/somnus_debug/pycache_cleaner/core.py:175`.

| Field | Value |
|---|---|
| Valid values | mapping |
| Effect | empty -> {} -> ValueError 'No roots' traceback exit 1; list root -> AttributeError traceback exit 1 |
| Failure behavior | traceback, exit 1 |
| Doc status | partial |
| Verification | VERIFIED |

<a id="pycache-clean-pyyaml-import"></a>
### `PyYAML import`

[VERIFIED] conditional import; tool `pycache-clean`. Defined at `src/somnus_debug/pycache_cleaner/core.py:150-154`; read at `module import`.

| Field | Value |
|---|---|
| Effect | ImportError re-raised after stderr hint; because cli.py imports pycache module, `somnus-debug doctor/structure` also require PyYAML |
| Dependencies | pyyaml |
| Failure behavior | ImportError at import |
| Doc status | contradictory (README: doctor/structure stdlib-only) |
| Verification | VERIFIED |
| Example / probe | sys.modules['yaml']=None: import somnus_debug.cli fails; doctor.core ok |

<a id="pycache-clean-module-docstring-escape"></a>
### `module docstring escape`

[VERIFIED] implicit; tool `pycache-clean`. Defined at `src/somnus_debug/pycache_cleaner/core.py:64`.

| Field | Value |
|---|---|
| Effect | SyntaxWarning invalid escape '\\`' on first compile (py3.12) |
| Failure behavior | noise on stderr |
| Doc status | missing |
| Verification | VERIFIED |

<a id="pycache-clean-pycache-relative-path-anchor"></a>
### `pycache relative path anchor`

[VERIFIED] implicit; tool `pycache-clean`. Defined at `src/somnus_debug/pycache_cleaner/core.py:184-186,351`.

| Field | Value |
|---|---|
| Effect | --config, roots and log_file are resolved against CWD; roots in a config are NOT relative to the config file |
| Scope | run |
| Doc status | contradictory (module docstring: config.yaml 'in the same directory') |
| Verification | VERIFIED |
| Example / probe | --config sub/c.yaml with roots [tree] from /tmp/w3/pc works; cd sub && --config c.yaml -> root /tmp/w3/pc/sub/tree missing, exit 0 (W3 P10/P11) |
| Notes | W3 added |

<a id="pycache-clean-no---no-dry-run--no---root"></a>
### `no --no-dry-run / no --root`

[VERIFIED] absent flag; tool `pycache-clean`. Defined at `src/somnus_debug/pycache_cleaner/core.py:337-346`.

| Field | Value |
|---|---|
| Effect | CLI can only force dry_run/verbose/follow_symlinks True; a YAML dry_run: true cannot be overridden live; roots cannot be given on the CLI |
| Failure behavior | --no-dry-run -> argparse exit 2 |
| Doc status | existing (MANUAL 5: no CLI root) |
| Verification | VERIFIED |
| Example / probe | pycache-clean --config config.yaml --no-dry-run -> exit 2 (W3 P15) |
| Notes | W3 added |

<a id="pycache-clean-dry-run-wording"></a>
### `dry-run wording`

[VERIFIED] implicit; tool `pycache-clean`. Defined at `src/somnus_debug/pycache_cleaner/core.py:287-290,305-308`.

| Field | Value |
|---|---|
| Effect | in dry-run, verbose lines still say 'Removed ...' and the summary says 'deleted N'; only the start line shows dry_run=True |
| Doc status | missing |
| Verification | VERIFIED |
| Example / probe | P3: 'Removed directory .../node_modules/__pycache__' printed in a dry run (W3) |
| Notes | W3 added |

## structure

This section documents the 8 registry rows for structure.

<a id="structure-source"></a>
### `source`

[VERIFIED] CLI; tool `structure`. Defined at `src/somnus_debug/structure/core.py:292`; read at `src/somnus_debug/structure/core.py:325-337`.

| Field | Value |
|---|---|
| Default | (required) |
| Precedence | CLI only |
| Effect | eff: single file to index (read as UTF-8) |
| Scope | run |
| Persistence | output file |
| Failure behavior | OSError/SyntaxError -> 'error:' exit 2; UnicodeDecodeError uncaught -> traceback exit 1 |
| Doc status | existing |
| Verification | VERIFIED |

<a id="structure--o--output"></a>
### `-o/--output`

[VERIFIED] CLI; tool `structure`. Defined at `src/somnus_debug/structure/core.py:294`; read at `src/somnus_debug/structure/core.py:325-337`.

| Field | Value |
|---|---|
| Default | stdout |
| Precedence | CLI only |
| Effect | eff: write index to path (parents created); prints nothing |
| Scope | run |
| Persistence | output file |
| Failure behavior | OSError/SyntaxError -> 'error:' exit 2; UnicodeDecodeError uncaught -> traceback exit 1 |
| Doc status | existing |
| Verification | VERIFIED |

<a id="structure---update-doc"></a>
### `--update-doc`

[VERIFIED] CLI; tool `structure`. Defined at `src/somnus_debug/structure/core.py:300`; read at `src/somnus_debug/structure/core.py:325-337`.

| Field | Value |
|---|---|
| Default | None |
| Precedence | CLI only |
| Effect | eff: IDENTICAL to -o; no existence check; mutually exclusive with -o |
| Scope | run |
| Persistence | output file |
| Failure behavior | OSError/SyntaxError -> 'error:' exit 2; UnicodeDecodeError uncaught -> traceback exit 1 |
| Doc status | partial |
| Verification | VERIFIED |

<a id="structure---no-line-numbers"></a>
### `--no-line-numbers`

[VERIFIED] CLI; tool `structure`. Defined at `src/somnus_debug/structure/core.py:306`; read at `src/somnus_debug/structure/core.py:325-337`.

| Field | Value |
|---|---|
| Default | False |
| Precedence | CLI only |
| Effect | eff: omit line spans |
| Scope | run |
| Persistence | output file |
| Failure behavior | OSError/SyntaxError -> 'error:' exit 2; UnicodeDecodeError uncaught -> traceback exit 1 |
| Doc status | existing |
| Verification | VERIFIED |

<a id="structure---source-label"></a>
### `--source-label`

[VERIFIED] CLI; tool `structure`. Defined at `src/somnus_debug/structure/core.py:311`; read at `src/somnus_debug/structure/core.py:325-337`.

| Field | Value |
|---|---|
| Default | str(source) |
| Precedence | CLI only |
| Effect | eff: name for heading (basename only shown) AND for SyntaxError filename |
| Scope | run |
| Persistence | output file |
| Failure behavior | OSError/SyntaxError -> 'error:' exit 2; UnicodeDecodeError uncaught -> traceback exit 1 |
| Doc status | existing |
| Verification | VERIFIED |

<a id="structure---no-module-functions"></a>
### `--no-module-functions`

[VERIFIED] CLI; tool `structure`. Defined at `src/somnus_debug/structure/core.py:315`; read at `src/somnus_debug/structure/core.py:325-337`.

| Field | Value |
|---|---|
| Default | False |
| Precedence | CLI only |
| Effect | eff: omit module-level functions section |
| Scope | run |
| Persistence | output file |
| Failure behavior | OSError/SyntaxError -> 'error:' exit 2; UnicodeDecodeError uncaught -> traceback exit 1 |
| Doc status | existing |
| Verification | VERIFIED |

<a id="structure-type_commentstrue"></a>
### `type_comments=True`

[VERIFIED] hard-coded parser option; tool `structure`. Defined at `src/somnus_debug/structure/core.py:210`.

| Field | Value |
|---|---|
| Default | True (src) / absent (root analyze_python_structure.py:210) |
| Precedence | not configurable |
| Effect | misplaced '# type:' comments make src version fail with SyntaxError exit 2 while root duplicate succeeds |
| Failure behavior | exit 2 |
| Doc status | contradictory (STATE.md says fixed) |
| Verification | VERIFIED |
| Example / probe | tc.py: src exit 2, root dup exit 0 |

<a id="structure-source-encoding"></a>
### `source encoding`

[VERIFIED] implicit; tool `structure`. Defined at `src/somnus_debug/structure/core.py:326`.

| Field | Value |
|---|---|
| Default | utf-8 |
| Effect | source read with encoding='utf-8' regardless of PEP 263 coding cookie |
| Failure behavior | UnicodeDecodeError uncaught -> traceback exit 1 |
| Doc status | missing |
| Verification | VERIFIED (lane-b) |
| Notes | W3 added |

## init-test-harness

This section documents the 3 registry rows for init-test-harness.

<a id="init-test-harness-target"></a>
### `target`

[VERIFIED] CLI positional; tool `init-test-harness`. Defined at `src/somnus_debug/test_harness/scaffold.py:96-101`; read at `src/somnus_debug/test_harness/scaffold.py:71,83,115`.

| Field | Value |
|---|---|
| Default | . |
| Type | path |
| Valid values | dir (created with parents) |
| Effect | destination for run_test.py (+CONTRACT.md) |
| Scope | run |
| Persistence | written |
| Failure behavior | target is a file -> misleading 'File exists' error exit 1 |
| Doc status | existing |
| Verification | VERIFIED |
| Notes | W3 corrected: read_at points to scaffold() where the path is used |

<a id="init-test-harness---force"></a>
### `--force`

[VERIFIED] CLI flag; tool `init-test-harness`. Defined at `src/somnus_debug/test_harness/scaffold.py:103`; read at `src/somnus_debug/test_harness/scaffold.py:75`.

| Field | Value |
|---|---|
| Default | False |
| Type | flag |
| Effect | overwrite |
| Scope | run |
| Failure behavior | existing files -> exit 1, nothing written |
| Doc status | existing |
| Verification | VERIFIED |
| Notes | W3 corrected: read_at line drift (73 -> 75) |

<a id="init-test-harness---no-contract"></a>
### `--no-contract`

[VERIFIED] CLI negative flag; tool `init-test-harness`. Defined at `src/somnus_debug/test_harness/scaffold.py:104-108`; read at `src/somnus_debug/test_harness/scaffold.py:72`.

| Field | Value |
|---|---|
| Default | False |
| Type | flag |
| Effect | write only run_test.py; existing CONTRACT.md then not checked |
| Scope | run |
| Doc status | existing |
| Verification | VERIFIED |
| Notes | W3 corrected: read_at line drift (71 -> 72) |

## run_test.py (scaffolded template)

This section documents the 6 registry rows for run_test.py (scaffolded template).

<a id="run_testpy-project_root"></a>
### `PROJECT_ROOT`

[VERIFIED] env var; tool `run_test.py`. Defined at `src/somnus_debug/test_harness/templates/run_test.py:188-190 (comment)`; read at `src/somnus_debug/test_harness/templates/run_test.py:748-750`.

| Field | Value |
|---|---|
| Default | Path(__file__).resolve().parent.parent (the parent of the directory holding run_test.py) |
| Type | path |
| Valid values | any path; ~ expanded; relative resolved against CWD |
| Precedence | env > default |
| Effect | ctx.project_root (cwd for subprocesses) and default artifact root |
| Scope | run |
| Failure behavior | empty string -> CWD; default points to the PARENT of the repo when scaffolded at repo root (scaffold default '.') |
| Doc status | contradictory (CONTRACT 'copy this directory into the repository' vs scaffold copying files into repo root) |
| Verification | VERIFIED |
| Example / probe | scaffold into th/repo, no env -> /tmp/w3/th/test-runs (outside repo); PROJECT_ROOT=/tmp/w3/th/repo -> repo/test-runs; copy into repo2/tools/ -> repo2/test-runs (W3 R1/R2/R6) |
| Notes | W3 corrected: default stated precisely; expanduser noted; tool normalized |

<a id="run_testpy-single_test_output_dir"></a>
### `SINGLE_TEST_OUTPUT_DIR`

[VERIFIED] env var; tool `run_test.py`. Defined at `src/somnus_debug/test_harness/templates/run_test.py:191-192 (comment)`; read at `src/somnus_debug/test_harness/templates/run_test.py:589-593`.

| Field | Value |
|---|---|
| Default | <project_root>/test-runs |
| Type | path |
| Valid values | any path; ~ expanded; RELATIVE value resolved against CWD (not project_root) |
| Precedence | env (non-empty) > default |
| Effect | artifact root; run dir created exist_ok=False |
| Scope | run |
| Persistence | artifacts |
| Failure behavior | empty string -> default |
| Doc status | partial (only in template comment) |
| Verification | VERIFIED |
| Example / probe | PROJECT_ROOT=/tmp/w3/th/repo SINGLE_TEST_OUTPUT_DIR=rel_arts from cwd /tmp/w3/th -> /tmp/w3/th/rel_arts (W3 R5) |
| Notes | W3 corrected: added: relative values resolve against CWD, not PROJECT_ROOT (W3 R5) |

<a id="run_testpy-test_name--execute_test"></a>
### `TEST_NAME / execute_test`

[VERIFIED] source edit; tool `run_test.py`. Defined at `src/somnus_debug/test_harness/templates/run_test.py:195-`; read at `src/somnus_debug/test_harness/templates/run_test.py:752-760`.

| Field | Value |
|---|---|
| Default | GOLDEN PATH LAYER 1 ... (gp-cli/cargo test) |
| Effect | template ships a project-specific cargo test -> FAIL out of the box |
| Dependencies | cargo |
| Failure behavior | verdict FAIL exit 1 |
| Doc status | existing |
| Verification | VERIFIED |

<a id="run_testpy-schema_version-manifest"></a>
### `SCHEMA_VERSION (manifest)`

[SOURCE-CONFIRMED] constant; tool `run_test.py`. Defined at `src/somnus_debug/test_harness/templates/run_test.py:489`; read at `src/somnus_debug/test_harness/templates/run_test.py:612`.

| Field | Value |
|---|---|
| Default | 1.0 |
| Precedence | not configurable |
| Effect | manifest schema_version |
| Doc status | partial |
| Verification | SOURCE-CONFIRMED |

<a id="run_testpy-run_testpy-argv"></a>
### `run_test.py argv`

[VERIFIED] absent CLI; tool `run_test.py`. Defined at `src/somnus_debug/test_harness/templates/run_test.py:747-855`.

| Field | Value |
|---|---|
| Effect | main() reads no argv: any flag (including --help) just runs the test |
| Doc status | missing |
| Verification | VERIFIED |
| Example / probe | python3 repo/run_test.py --help -> runs, verdict FAIL, exit 1 (W3 R7) |
| Notes | W3 added; see D-15 |

<a id="run_testpy-run_testpy-run_id--artifact-dir"></a>
### `run_test.py run_id / artifact dir`

[VERIFIED] derived value; tool `run_test.py`. Defined at `src/somnus_debug/test_harness/templates/run_test.py:753-760`.

| Field | Value |
|---|---|
| Default | <SLUG(TEST_NAME)>-<YYYYmmdd-HHMMSS>-<6 hex> |
| Effect | per-run directory created with exist_ok=False under the output root |
| Persistence | test.log, manifest.json, report.md |
| Doc status | partial (CONTRACT.md) |
| Verification | VERIFIED |
| Notes | W3 added |

## fieldkit onboard.py

This section documents the 13 registry rows for fieldkit onboard.py.

<a id="fieldkit-onboardpy-repo"></a>
### `repo`

[VERIFIED] CLI positional; tool `fieldkit onboard.py`. Defined at `skills/somnus-debug-fieldkit/scripts/onboard.py:454`; read at `skills/somnus-debug-fieldkit/scripts/onboard.py:461-464`.

| Field | Value |
|---|---|
| Default | . (cwd) |
| Type | path |
| Valid values | existing directory |
| Effect | repository to survey/onboard |
| Scope | run |
| Failure behavior | not a directory -> stderr error, exit 1 |
| Doc status | existing (references/onboarding.md) |
| Verification | VERIFIED |
| Example / probe | onboard.py ../fx/nonexist -> exit 1 (W3 OB7) |
| Notes | W3 added |

<a id="fieldkit-onboardpy---apply"></a>
### `--apply`

[VERIFIED] CLI flag; tool `fieldkit onboard.py`. Defined at `skills/somnus-debug-fieldkit/scripts/onboard.py:455`; read at `skills/somnus-debug-fieldkit/scripts/onboard.py:495-501,515-516`.

| Field | Value |
|---|---|
| Default | False (plan mode) |
| Type | flag |
| Effect | writes .somnus-debug/{python_doctor.yaml (unless adopting a root config), pycache.yaml, dispositions.json, .gitignore, PROFILE.md}; never overwrites |
| Scope | run |
| Persistence | repo files |
| Failure behavior | writes PROFILE.md even when verification failed (D-20) |
| Doc status | existing |
| Verification | VERIFIED |
| Example / probe | --apply --baseline on fx/ob wrote 5 files + runs/ + state/ (W3 OB3) |
| Notes | W3 added |

<a id="fieldkit-onboardpy---baseline"></a>
### `--baseline`

[VERIFIED] CLI flag; tool `fieldkit onboard.py`. Defined at `skills/somnus-debug-fieldkit/scripts/onboard.py:456`; read at `skills/somnus-debug-fieldkit/scripts/onboard.py:489-491,518-522`.

| Field | Value |
|---|---|
| Default | False |
| Type | flag |
| Effect | stateful scan with cwd .somnus-debug/ into runs/baseline.{md,json}; skipped silently unless verify status is 0 (verify exit 1 counts as status 0) |
| Scope | run |
| Persistence | .somnus-debug/runs, .somnus-debug/state |
| Failure behavior | without --apply and no config -> 'use --apply first', exit 1 |
| Doc status | existing |
| Verification | VERIFIED |
| Example / probe | onboard.py repo --baseline (no config) -> exit 1 (W3 OB2); verify exit=1 still recorded baseline (W3 OB3) |
| Notes | W3 added |

<a id="fieldkit-onboardpy---new-config"></a>
### `--new-config`

[VERIFIED] CLI flag; tool `fieldkit onboard.py`. Defined at `skills/somnus-debug-fieldkit/scripts/onboard.py:457`; read at `skills/somnus-debug-fieldkit/scripts/onboard.py:477-479`.

| Field | Value |
|---|---|
| Default | False |
| Type | flag |
| Precedence | default: adopt first ROOT python_doctor.yaml/.yml; flag forces .somnus-debug/python_doctor.yaml |
| Effect | ignore an existing root doctor config and generate a profile config instead |
| Scope | run |
| Doc status | existing |
| Verification | VERIFIED |
| Example / probe | root python_doctor.yaml present: plan adopts it (WARN 2 of 3 files); --new-config -> 'generate on --apply' (W3 OB4/OB5) |
| Notes | W3 added |

<a id="fieldkit-onboardpy---python"></a>
### `--python`

[VERIFIED] CLI flag; tool `fieldkit onboard.py`. Defined at `skills/somnus-debug-fieldkit/scripts/onboard.py:458`; read at `skills/somnus-debug-fieldkit/scripts/onboard.py:239-245`.

| Field | Value |
|---|---|
| Default | None (project venv, then PATH) |
| Type | path |
| Precedence | --python > project venvs (.venv, venv, env, any pyvenv.cfg dir) > somnus-debug on PATH |
| Effect | interpreter that runs python -m somnus_debug.cli |
| Scope | run |
| Failure behavior | path is resolve()d, so a symlinked venv python loses the venv -> BLOCKED exit 3; nonexistent path -> FileNotFoundError traceback exit 1 |
| Doc status | contradictory (references/onboarding.md:59) |
| Verification | VERIFIED |
| Example / probe | --python /nonexistent/python -> traceback exit 1 (W3 OB6) |
| Notes | W3 added; see D-20 |

<a id="fieldkit-onboardpy-path-lookup-of-somnus-debug"></a>
### `PATH lookup of somnus-debug`

[VERIFIED] env var; tool `fieldkit onboard.py`. Defined at `skills/somnus-debug-fieldkit/scripts/onboard.py:256-258`; read at `skills/somnus-debug-fieldkit/scripts/onboard.py:256`.

| Field | Value |
|---|---|
| Default | PATH |
| Effect | fallback runner when no --python and no project venv has somnus_debug |
| Scope | run |
| Failure behavior | none found -> BLOCKED, exit 3 |
| Doc status | existing |
| Verification | VERIFIED |
| Example / probe | no somnus-debug on PATH -> 'BLOCKED: no usable somnus-debug', exit 3 (W3 OB8) |
| Notes | W3 added |

<a id="fieldkit-onboardpy-pythonpath-extension-src-layout"></a>
### `PYTHONPATH extension (src layout)`

[VERIFIED] env var (child process); tool `fieldkit onboard.py`. Defined at `skills/somnus-debug-fieldkit/scripts/onboard.py:104-110,235-237`.

| Field | Value |
|---|---|
| Default | prepend <repo>/src when src/<pkg>/__init__.py exists |
| Precedence | prepended to any inherited PYTHONPATH |
| Effect | child doctor runs resolve the project's own src packages |
| Scope | run |
| Doc status | existing (references/onboarding.md) |
| Verification | VERIFIED (lane-f) |
| Notes | W3 added |

<a id="fieldkit-onboardpy-profile_dir"></a>
### `PROFILE_DIR`

[SOURCE-CONFIRMED] in-code constant; tool `fieldkit onboard.py`. Defined at `skills/somnus-debug-fieldkit/scripts/onboard.py:68`.

| Field | Value |
|---|---|
| Default | .somnus-debug |
| Type | str |
| Effect | profile directory; generated doctor config sets state_dir: .somnus-debug/state |
| Scope | run |
| Doc status | existing |
| Verification | SOURCE-CONFIRMED |
| Notes | W3 added |

<a id="fieldkit-onboardpy-generated-somnus-debugpython_doctoryaml"></a>
### `generated .somnus-debug/python_doctor.yaml`

[VERIFIED] generated file; tool `fieldkit onboard.py`. Defined at `skills/somnus-debug-fieldkit/scripts/onboard.py:276-297`; read at `doctor -c`.

| Field | Value |
|---|---|
| Default | init-config output with include [*.py], ignore BASE_IGNORES + venvs + egg-info + git-ignored py dirs, state_dir .somnus-debug/state |
| Effect | profile doctor config; header comment documents fnmatch semantics |
| Scope | run |
| Failure behavior | default layout changed -> RuntimeError |
| Doc status | existing |
| Verification | VERIFIED (lane-f logs/s1_profile_python_doctor.yaml.txt) |
| Notes | W3 added |

<a id="fieldkit-onboardpy-generated-somnus-debugpycacheyaml"></a>
### `generated .somnus-debug/pycache.yaml`

[VERIFIED] generated file; tool `fieldkit onboard.py`. Defined at `skills/somnus-debug-fieldkit/scripts/onboard.py:300-321`; read at `pycache-clean --config`.

| Field | Value |
|---|---|
| Default | roots [absolute repo], name-only excludes, dry_run: true |
| Effect | safe cleaner config; live run requires editing dry_run |
| Scope | run |
| Doc status | existing |
| Verification | VERIFIED (lane-f logs/s1_profile_pycache.yaml.txt) |
| Notes | W3 added |

<a id="fieldkit-onboardpy-always_prune--base_ignores--pycache_excludes--venv_names"></a>
### `ALWAYS_PRUNE / BASE_IGNORES / PYCACHE_EXCLUDES / VENV_NAMES`

[SOURCE-CONFIRMED] in-code constants; tool `fieldkit onboard.py`. Defined at `skills/somnus-debug-fieldkit/scripts/onboard.py:71-82`.

| Field | Value |
|---|---|
| Effect | survey pruning and the ignore/exclude lists written into generated configs |
| Scope | run |
| Doc status | partial |
| Verification | SOURCE-CONFIRMED |
| Notes | W3 added |

<a id="fieldkit-onboardpy-subprocess-timeouts"></a>
### `subprocess timeouts`

[SOURCE-CONFIRMED] in-code constants; tool `fieldkit onboard.py`. Defined at `skills/somnus-debug-fieldkit/scripts/onboard.py:149-151 (+ 60 s at call sites)`.

| Field | Value |
|---|---|
| Default | 600 s (scans); 60 s (version, init-config, git, import probe) |
| Effect | TimeoutExpired propagates as a traceback |
| Scope | run |
| Doc status | missing |
| Verification | SOURCE-CONFIRMED |
| Notes | W3 added |

<a id="fieldkit-onboardpy-onboard-exit-codes"></a>
### `onboard exit codes`

[VERIFIED] exit status; tool `fieldkit onboard.py`. Defined at `skills/somnus-debug-fieldkit/scripts/onboard.py:50,464,472,436-448`.

| Field | Value |
|---|---|
| Default | 0 ok |
| Valid values | 0 ok, 1 usage, 2 coverage failure, 3 somnus-debug unavailable |
| Scope | run |
| Failure behavior | doctor config error -> RuntimeError traceback exit 1, not 2 (D-20) |
| Doc status | partial |
| Verification | VERIFIED |
| Notes | W3 added |

## fieldkit delta.py

This section documents the 6 registry rows for fieldkit delta.py.

<a id="fieldkit-deltapy-baseline"></a>
### `baseline`

[VERIFIED] CLI positional; tool `fieldkit delta.py`. Defined at `skills/somnus-debug-fieldkit/scripts/delta.py:238`; read at `skills/somnus-debug-fieldkit/scripts/delta.py:245`.

| Field | Value |
|---|---|
| Type | path |
| Valid values | doctor JSON report |
| Scope | run |
| Failure behavior | unreadable / missing issues, summary, files -> exit 3 |
| Doc status | existing |
| Verification | VERIFIED |
| Example / probe | {} -> exit 3 (W3 DL7) |
| Notes | W3 added |

<a id="fieldkit-deltapy-latest"></a>
### `latest`

[VERIFIED] CLI positional; tool `fieldkit delta.py`. Defined at `skills/somnus-debug-fieldkit/scripts/delta.py:239`; read at `skills/somnus-debug-fieldkit/scripts/delta.py:245`.

| Field | Value |
|---|---|
| Type | path |
| Valid values | doctor JSON report |
| Scope | run |
| Failure behavior | missing argument -> argparse exit 2 (collides with coverage-regression code) |
| Doc status | partial |
| Verification | VERIFIED |
| Example / probe | delta.py base.json -> exit 2 (W3 DL5) |
| Notes | W3 added; see D-21 |

<a id="fieldkit-deltapy---dispositions"></a>
### `--dispositions`

[VERIFIED] CLI flag; tool `fieldkit delta.py`. Defined at `skills/somnus-debug-fieldkit/scripts/delta.py:240`; read at `skills/somnus-debug-fieldkit/scripts/delta.py:246-248`.

| Field | Value |
|---|---|
| Default | None |
| Type | path |
| Valid values | JSON list of {category, file (glob), symbol (glob, optional, default *), reason} |
| Effect | matching findings never count as regressions; unmatched entries reported stale |
| Scope | run |
| Failure behavior | missing file -> stderr note, continue without; malformed -> exit 3 |
| Doc status | existing |
| Verification | VERIFIED |
| Example / probe | disposition for new stub2 -> exit 1 becomes 0; missing.json -> note, exit 1 (W3 DL2/DL3) |
| Notes | W3 added; stale broad dispositions still mute (D-21) |

<a id="fieldkit-deltapy---root"></a>
### `--root`

[VERIFIED] CLI flag; tool `fieldkit delta.py`. Defined at `skills/somnus-debug-fieldkit/scripts/delta.py:241`; read at `skills/somnus-debug-fieldkit/scripts/delta.py:252`.

| Field | Value |
|---|---|
| Default | latest report's project_root |
| Type | path |
| Effect | where coverage checks look for files dropped from the latest scan |
| Scope | run |
| Doc status | existing |
| Verification | VERIFIED |
| Example / probe | --root at an empty dir: dropped files count as deleted, verdict unchanged (W3 DL6) |
| Notes | W3 added |

<a id="fieldkit-deltapy---json"></a>
### `--json`

[VERIFIED] CLI flag; tool `fieldkit delta.py`. Defined at `skills/somnus-debug-fieldkit/scripts/delta.py:242`; read at `skills/somnus-debug-fieldkit/scripts/delta.py:254`.

| Field | Value |
|---|---|
| Default | False (Markdown) |
| Type | flag |
| Effect | emit JSON result instead of Markdown |
| Scope | run |
| Doc status | existing |
| Verification | VERIFIED |
| Example / probe | W3 DL4 exit 1 with JSON body |
| Notes | W3 added |

<a id="fieldkit-deltapy-gating--severity_order"></a>
### `GATING / SEVERITY_ORDER`

[VERIFIED] in-code constants; tool `fieldkit delta.py`. Defined at `skills/somnus-debug-fieldkit/scripts/delta.py:67-68`.

| Field | Value |
|---|---|
| Default | {critical, serious} |
| Effect | only new undispositioned critical/serious findings are regressions; severities come from the reports, config_hash never compared |
| Scope | run |
| Doc status | partial |
| Verification | VERIFIED (lane-f D3) |
| Notes | W3 added; see D-21 |

## fieldkit selftest.py

This section documents the 1 registry rows for fieldkit selftest.py.

<a id="fieldkit-selftestpy---python"></a>
### `--python`

[VERIFIED] CLI flag; tool `fieldkit selftest.py`. Defined at `skills/somnus-debug-fieldkit/scripts/selftest.py:322`; read at `skills/somnus-debug-fieldkit/scripts/selftest.py:324-330`.

| Field | Value |
|---|---|
| Default | somnus-debug on PATH |
| Type | path |
| Effect | interpreter used as python -m somnus_debug.cli for the 29 checks (expanduser only, no resolve) |
| Scope | run |
| Failure behavior | neither --python nor PATH -> exit 3 |
| Doc status | existing |
| Verification | VERIFIED (lane-f 29/29) |
| Notes | W3 added |

## packaging

This section documents the 2 registry rows for packaging.

<a id="packaging-console-scripts"></a>
### `console scripts`

[SOURCE-CONFIRMED] packaging; tool `packaging`. Defined at `pyproject.toml:[project.scripts]`.

| Field | Value |
|---|---|
| Default | somnus-debug, somnus-doctor, somnus-structure, somnus-pycache-clean |
| Effect | no standalone script for init-test-harness; somnus-doctor imports only doctor.core (stdlib-only) while `somnus-debug doctor` also imports PyYAML |
| Scope | install |
| Doc status | partial |
| Verification | SOURCE-CONFIRMED |

<a id="packaging-toolhatchbuild-exclude"></a>
### `[tool.hatch.build] exclude`

[SOURCE-CONFIRMED] packaging config; tool `packaging`. Defined at `pyproject.toml:[tool.hatch.build]`.

| Field | Value |
|---|---|
| Default | .python_doctor/, *_report.md/json, production_doctor.log, __pycache__, *.pyc |
| Effect | keeps doctor state/report/log artifacts out of built wheels/sdists |
| Scope | build |
| Doc status | missing |
| Verification | SOURCE-CONFIRMED |
| Notes | W3 added |

## Sources

This section lists where the rows above come from.

- [`../_evidence/configuration-registry.tsv`](../_evidence/configuration-registry.tsv) (canonical; W3 audit of lane B's 94 rows plus 37 additions)
- [`../_evidence/agent-findings/lane-b-config/configuration-findings.md`](../_evidence/agent-findings/lane-b-config/configuration-findings.md) and [`configuration-registry.tsv`](../_evidence/agent-findings/lane-b-config/configuration-registry.tsv) (original 94 rows)
- [`../_evidence/agent-findings/lane-f-ext/fieldkit.md`](../_evidence/agent-findings/lane-f-ext/fieldkit.md) and [`harness.md`](../_evidence/agent-findings/lane-f-ext/harness.md) (fieldkit and harness behavior)
- Source files: `src/somnus_debug/cli.py`, `src/somnus_debug/doctor/core.py`, `src/somnus_debug/pycache_cleaner/core.py`, `src/somnus_debug/structure/core.py`, `src/somnus_debug/test_harness/scaffold.py`, `src/somnus_debug/test_harness/templates/run_test.py`, `skills/somnus-debug-fieldkit/scripts/{onboard,delta,selftest}.py`, `pyproject.toml`
