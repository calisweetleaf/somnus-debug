# Hidden and conditional options

This page collects settings that exist but are not documented, settings that are documented but do nothing, and settings whose effect depends on another condition. Doc status is measured against `README.md`, `docs/MANUAL.md`, and `docs/Python_Doctor_QUICKSTART.md`.

## Undocumented doctor keys

This section lists config keys that work but appear in no user document.

| Key | Default | What it does | Evidence |
|---|---|---|---|
| `max_report_evidence_lines` | `5` | evidence snippet size: `N // 2` lines either side of the finding | [VERIFIED W3 M2: 5-line evidence by default, 1 line with `1`; `src/somnus_debug/doctor/core.py:1087`] |
| `markdown_include_css` | `true` | prepends a `<style>` block (terminal-style CSS) to the Markdown report | [VERIFIED W3 M1; `core.py:516-522,1786`] |
| `state_dir` | `".python_doctor"` | state location under project root; absolute or `../` values escape the project | [VERIFIED W3 E9a, recipe R4] |
| `reports_dir` | `"reports"` | report archive under `state_dir` | [VERIFIED W3 E9a] |
| `report_basename` | `"production_doctor_report"` | file stem of default and archived reports; slashes create subdirectories | [VERIFIED W3 E9a; lane B S3] |
| `check_private_functions` | `false` | when false, `_private` functions are not analyzed as functions, but their bodies are, and findings there carry the enclosing symbol | [VERIFIED W3 F0/F3] |
| `check_nested_functions` | `true` | when false, nested defs and everything inside them are skipped, security findings included | [VERIFIED W3 F1: `eval` in `outer.inner` dropped] [D-16](../DISCOVERY-LEDGER.md#d-16) |

Lane B found none of these seven in any doc [DOCUMENTED-ONLY absence check by lane B, section 6.1]. The QUICKSTART's "key fields" list also omits `ignore_classes` and `severity_levels` from its sample, though it mentions `ignore_classes` in prose (`docs/Python_Doctor_QUICKSTART.md:217`).

## Undocumented gate values

This section covers the two `severity_exit_level` values no document mentions.

| Value | Exit rule (`core.py:2046-2058`) | Evidence |
|---|---|---|
| `"info"` | 1 if there is any finding at all, else 0 | [VERIFIED W3 E3-info: exit 1] |
| `"none"` | always 0; must be quoted in YAML | [VERIFIED W3 E1b exit 0, E2 unquoted exit 4] [D-03](../DISCOVERY-LEDGER.md#d-03) |

The documented values behave with two quirks: `"minor"` returns 1 (not 2) even when criticals exist, and does not fail on info-only findings, although MANUAL 3.4 says `"minor"` fails "on anything at all" [SOURCE-CONFIRMED `core.py:2054-2055`; DISCREPANCY with `docs/MANUAL.md:178-179`]. [D-18](../DISCOVERY-LEDGER.md#d-18)

## Documented settings that do nothing

This section lists settings that are accepted and validated but never consulted.

| Setting | Why it is dead | Evidence |
|---|---|---|
| `detect_test_gaps` | validated (`core.py:840`) and stored, never read; no code emits `test_gaps` | [VERIFIED W3 E7c: `false` gives the same 6 issues as defaults; grep finds only `core.py:229,470,840,892`] [D-05](../DISCOVERY-LEDGER.md#d-05) |
| `severity_levels.test_gaps` | the category is never produced | [SOURCE-CONFIRMED `core.py:493`] |
| `scan -v` / `--verbose` | `-v` never changes the log level; `--verbose` sets DEBUG but doctor has no `logger.debug` calls | [VERIFIED W3 E10a/E10b: 0-byte log both ways] |
| `schema_version` | validated as a non-empty string, never compared | [VERIFIED lane B C20: `"99.9"` accepted] |
| `doctor/default_config.yaml` and repo-root `python_doctor.yaml` | look like live config files, are never loaded | [VERIFIED W3 E1, E8] [D-02](../DISCOVERY-LEDGER.md#d-02) |
| unknown top-level keys and unknown categories | accepted silently; typos have no effect | [VERIFIED W3 E7a] [D-04](../DISCOVERY-LEDGER.md#d-04) |

## Categories with no toggle

This section lists finding categories that cannot be turned off, only re-severitied.

`broad_exceptions`, `missing_imports`, `todos`, `stubs`, `placeholder_returns`, `duplicate_definitions`, `complexity` (raise `max_cyclomatic_complexity` instead), `suspicious_short_functions` and `suspicious_short_classes` (lower `min_function_lines` / `min_class_lines` to 1 instead), `incomplete_methods`, `syntax_errors`, `tokenization_errors`, `analysis_read_errors` [SOURCE-CONFIRMED: no `detect_*` key guards them; lane B section 6.2]. Re-severitying to `info` removes a category from every gate except `"info"` [VERIFIED W3 E4a, recipe R7]. `detect_silent_failures` controls `silent_failures` only, not `broad_exceptions` [SOURCE-CONFIRMED `core.py:1222`].

## Options whose effect depends on something else

This section lists conditional behavior: the same setting acts differently depending on another input.

| Setting | Condition | Behavior | Evidence |
|---|---|---|---|
| `ignore_functions` | a function with a listed name contains risky calls | its whole body is skipped; with the default list, `eval` inside any `__repr__`/`__str__` is never reported | [VERIFIED W3 F0 vs F2] [D-16](../DISCOVERY-LEDGER.md#d-16) |
| `ignore_classes` | always | suppresses only class-level docstring, stub, and short-class findings; methods are still analyzed | [SOURCE-CONFIRMED `core.py:1200-1202,1269-1272`] |
| `ignore_patterns` entry `X/*` | a directory named `X` exists at any depth | pruned there too (`myapp/build/`, `pkg/env/`) | [VERIFIED W3 G1, recipe R6] [D-17](../DISCOVERY-LEDGER.md#d-17) |
| `include_patterns` | pattern has no `/` | also matches by basename anywhere in the tree | [VERIFIED W3 G6] |
| `max_workers` | fewer files than workers, or `1` | pool size is `min(N, files)`; `1` runs sequentially | [SOURCE-CONFIRMED `core.py:1720-1722`; VERIFIED W3 M3 same findings] |
| `--no-state` | state store unavailable in src/PyPI | without the flag, src falls back to stateless with a stderr warning; the root duplicate errors (exit 4) | [SOURCE-CONFIRMED `core.py:2068-2077`; lane D diff] [D-28](../DISCOVERY-LEDGER.md#d-28) |
| `-o` | path ends in `.json` and no `--json-output` | the JSON report overwrites the Markdown report at the same path | [VERIFIED W3 O1] [D-25](../DISCOVERY-LEDGER.md#d-25) |
| `history`/`rollback` `-c` | scan used a custom `state_dir` | without the same `-c`, they read and create the default `.python_doctor/` and report nothing | [VERIFIED W3 E9b/E9c] |
| `self-check -o` | package directory is read-only | required, or the run fails with exit 4 | [VERIFIED lane B] |
| pycache `verbose`, `log_file` | any unknown key in the same YAML | silently disabled | [VERIFIED W3 P9] [D-14](../DISCOVERY-LEDGER.md#d-14) |
| pycache `--max-depth` | directory listing happens before the depth check | entries one level past the limit are still listed; root files are processed at depth 0 | [VERIFIED W3 P5; lane B P4] |
| pycache `follow_symlinks` | false | symlinked directories are neither traversed nor deleted; symlinked files are not deleted | [SOURCE-CONFIRMED `pycache_cleaner/core.py:237-255`] |
| onboard `--baseline` | verification status is not 0 (zero files or doctor exit >= 4) | silently skipped; a doctor gate failure (exit 1 or 2) still counts as status 0 | [VERIFIED W3 OB3; lane F OB-4] |
| onboard `--apply` | verification failed | still writes PROFILE.md describing a failed scan as passed | [VERIFIED lane F OB-3] [D-20](../DISCOVERY-LEDGER.md#d-20) |
| onboard config choice | a root `python_doctor.yaml`/`.yml` exists | adopted unless `--new-config`; coverage then depends on that file's globs | [VERIFIED W3 OB4/OB5] |
| delta `--dispositions` | a stale but broad disposition remains | it still mutes new findings it matches | [VERIFIED lane F L7] [D-21](../DISCOVERY-LEDGER.md#d-21) |
| run_test `PROJECT_ROOT` | harness placed at repo root (the scaffold default) | default root is the repo's parent; artifacts land outside the repo | [VERIFIED W3 R1 vs R6] [D-15](../DISCOVERY-LEDGER.md#d-15) |

## Hard-coded behavior that looks like it should be an option

This section lists constants that control results and have no setting.

| Constant | Value | Evidence |
|---|---|---|
| `TODO_PATTERNS` | `TODO`, `FIXME`, `HACK`, `XXX`, `TEMP`, `WIP`, word match, case-insensitive, comments only | [SOURCE-CONFIRMED `core.py:504-511`] |
| `PLACEHOLDER_CONSTANTS` | `None`, `False`, `True`, `0`, `-1`, `""` | [SOURCE-CONFIRMED `core.py:513`] |
| `SECURITY_CALLS` | 13 dotted names (`eval`, `exec`, `compile`, `pickle.load(s)`, `subprocess.call/run/Popen`, `os.system`, `os.popen`, `yaml.load`, `marshal.load(s)`); matched by dotted name, so `from subprocess import run; run()` is not matched | [SOURCE-CONFIRMED `core.py:514,1228-1229`] |
| cycle search | stops at 100 cycles, path depth below 30, silently | [SOURCE-CONFIRMED `core.py:1642,1653`] |
| production score | `max(0, 100 - 20*critical - 8*serious - 2*minor - info)` | [SOURCE-CONFIRMED `core.py:1772`] |
| run ID | `%Y%m%dT%H%M%SZ`, one-second resolution | [SOURCE-CONFIRMED `core.py:82`] [D-08](../DISCOVERY-LEDGER.md#d-08) |
| structure parse flags | `type_comments=True` | [VERIFIED W3 S5] [D-01](../DISCOVERY-LEDGER.md#d-01) |
| delta gating set | `{critical, serious}` | [SOURCE-CONFIRMED `delta.py:68`] |
| onboard timeouts | 600 s scans, 60 s probes | [SOURCE-CONFIRMED `onboard.py:149`] |

## Sources

This section lists the evidence behind this page.

- [`../_evidence/configuration-registry.tsv`](../_evidence/configuration-registry.tsv)
- [`../_evidence/agent-findings/lane-b-config/configuration-findings.md`](../_evidence/agent-findings/lane-b-config/configuration-findings.md) sections 1, 6, 7, 9
- [`../_evidence/agent-findings/lane-f-ext/fieldkit.md`](../_evidence/agent-findings/lane-f-ext/fieldkit.md)
- [`../_evidence/agent-findings/lane-d-cli-tests/install-vs-source.md`](../_evidence/agent-findings/lane-d-cli-tests/install-vs-source.md)
- `src/somnus_debug/doctor/core.py:82,504-522,816-851,1087,1220-1310,1642-1653,1720-1786,2046-2077`, `src/somnus_debug/pycache_cleaner/core.py:226-255`, `skills/somnus-debug-fieldkit/scripts/onboard.py`, `skills/somnus-debug-fieldkit/scripts/delta.py:67-68`, `docs/MANUAL.md` section 3.4, `docs/Python_Doctor_QUICKSTART.md`
- W3 probes E1-E10, F0-F3, G1/G6, M1-M3, O1, P5/P9, R1/R6, S5, OB3-OB5
