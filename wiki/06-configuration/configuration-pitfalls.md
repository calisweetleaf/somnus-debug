# Configuration pitfalls

This page ranks the configuration mistakes that pass silently or do the opposite of what was intended, with the symptom, the cause in source, and the fix. Ranking is by blast radius: a false green in CI or a deletion outranks noise.

## Ranked list

This section is the table of pitfalls; details follow below it.

| # | Pitfall | Symptom | Fix | Evidence |
|---|---|---|---|---|
| 1 | Config file not passed with `-c` | edits to `python_doctor.yaml` have no effect | always pass `-c` | [VERIFIED W3 E1, R1] [D-02](../DISCOVERY-LEDGER.md#d-02) |
| 2 | Coverage matches nothing | `files=0`, exit 0, green CI | check `files=` > 0 (recipe R3) | [VERIFIED W3 G5, R3] [D-17](../DISCOVERY-LEDGER.md#d-17) |
| 3 | `pycache-clean` `dry_run: no` / omitted | live deletion when a preview was meant | write `dry_run: true` unquoted; keep separate dry and live configs | [VERIFIED W3 P7] [D-14](../DISCOVERY-LEDGER.md#d-14) |
| 4 | Default `ignore_functions` | `eval`/`exec` inside any `__repr__`/`__str__` never reported | set `ignore_functions: []` for security review runs | [VERIFIED W3 F0/F2] [D-16](../DISCOVERY-LEDGER.md#d-16) |
| 5 | `check_nested_functions: false` | everything inside nested defs vanishes, security findings included | leave it `true` | [VERIFIED W3 F1] [D-16](../DISCOVERY-LEDGER.md#d-16) |
| 6 | Default ignores prune same-named dirs at any depth | `myapp/build/`, `pkg/env/` silently unscanned | replace `ignore_patterns` (recipe R6) | [VERIFIED W3 G1, R6] [D-17](../DISCOVERY-LEDGER.md#d-17) |
| 7 | Unquoted `severity_exit_level: none` | exit 4 "must be a non-empty string" | `"none"` | [VERIFIED W3 E2, R2] [D-03](../DISCOVERY-LEDGER.md#d-03) |
| 8 | Typo in a key | no error, no effect | diff your keys against `init-config` output | [VERIFIED W3 E7a] [D-04](../DISCOVERY-LEDGER.md#d-04) |
| 9 | `detect_test_gaps` trusted as a control | nothing ever emitted either way | do not rely on it | [VERIFIED W3 E7c] [D-05](../DISCOVERY-LEDGER.md#d-05) |
| 10 | `src/**/*.py` style globs | top-level files of `src/` skipped | `src/*.py` (`*` crosses `/`) | [VERIFIED W3 G2/G3, R5] |
| 11 | Replacing a list expecting a merge | `ignore_patterns: [x]` drops all 15 defaults; `.venv` gets scanned | restate every default you still want | [VERIFIED W3 E4b] |
| 12 | `-o report.json` | Markdown report overwritten by JSON | pass `-o x.md --json-output x.json` | [VERIFIED W3 O1] [D-25](../DISCOVERY-LEDGER.md#d-25) |
| 13 | `history` without the scan's `-c` | "No recorded runs found." plus a stray `.python_doctor/` | pass the same `-c` | [VERIFIED W3 E9b/E9c] |
| 14 | `python -m` vs console script vs venv | different `missing_imports` on the same tree | run doctor in the project's interpreter, set `PYTHONPATH` for src layouts | [VERIFIED W3 ENV1-ENV4, R8] [D-26](../DISCOVERY-LEDGER.md#d-26) |
| 15 | pycache `exclude: ["node_modules/*"]` (MANUAL 5.1 example) | `node_modules/__pycache__` deleted anyway | bare names: `node_modules` | [VERIFIED W3 P3/P4] [D-14](../DISCOVERY-LEDGER.md#d-14) |
| 16 | pycache unknown key | no INFO output, `--verbose` and `log_file` dead | remove unknown keys | [VERIFIED W3 P9] [D-14](../DISCOVERY-LEDGER.md#d-14) |
| 17 | pycache `dry_run: "false"` | dry run while the log prints `dry_run=false` | unquoted bool | [VERIFIED W3 P8] |
| 18 | pycache relative roots / `$VARS` | root not found, exit 0 | absolute roots; no env expansion exists | [VERIFIED W3 P11/P12] |
| 19 | `run_test.py` at repo root | artifacts written to the repo's parent | scaffold into a subdirectory or set `PROJECT_ROOT` (recipe R10) | [VERIFIED W3 R1/R6] [D-15](../DISCOVERY-LEDGER.md#d-15) |
| 20 | relative `SINGLE_TEST_OUTPUT_DIR` | resolved against CWD, not the project | absolute value | [VERIFIED W3 R5] |
| 21 | Re-severitying in the latest scan only | delta.py reports clean while a regression hides | keep baseline and latest configs identical; compare `config_hash` yourself | [VERIFIED lane F D3] [D-21](../DISCOVERY-LEDGER.md#d-21) |
| 22 | Expecting `-v` to log more | empty `production_doctor.log` | nothing to enable; doctor logs only errors | [VERIFIED W3 E10a/E10b] |
| 23 | Copying the repo-root `python_doctor.yaml` | 0 files on any other project | start from `init-config` | [VERIFIED lane F OB-5; W3 E8f] |

## Silent false greens

This section explains pitfalls 1, 2, 4-6, 8-10, and 21, which make a scan look cleaner than the code is.

- **Unloaded config (1).** `ConfigManager(None)` is used whenever `-c` is absent (`src/somnus_debug/doctor/core.py:2063`). The QUICKSTART tells users to "Generate a starting config in your project root", and the README quickstart runs `init-config -o python_doctor.yaml` followed by `scan . -o report.md` with no `-c`, which reads as if the file is picked up [DISCREPANCY: `docs/Python_Doctor_QUICKSTART.md:60`, `README.md:213-216`; MANUAL 3.3's everyday commands also omit `-c`, `docs/MANUAL.md:151-158`]. It goes unnoticed at first because the generated file equals the defaults [VERIFIED W3 E8d].
- **Zero-file scans (2).** `exit_code_for_summary` sees no findings and returns 0 under every gate (`core.py:2046-2058`). Causes seen: `include_patterns: []` (W3 G5), wrong globs (W3 R5 `myapp/**/*.py` -> `[]`), the repo-root Somnus config on another repo (lane F OB-5).
- **Skipped bodies (4, 5).** `_visit_function` returns before `generic_visit` for ignored names and for nested functions when `check_nested_functions` is false (`core.py:1235-1238`), so no visitor sees the calls inside.
- **Pruned directories (6).** `should_ignore` treats `X/*` as "any path component equals X" (`core.py:945-946`).
- **Accepted typos (8, 9).** `_validate` reads only known keys and never lists leftovers (`core.py:816-851`); `detect_test_gaps` has no reader.
- **Severity laundering (21).** delta.py trusts the severities stored in each report and never checks `config_hash` (`skills/somnus-debug-fieldkit/scripts/delta.py:159-191`).

## Destructive or misleading pycache settings

This section explains pitfalls 3 and 15-18, all in `src/somnus_debug/pycache_cleaner/core.py`.

- Values go through `setattr` with no type check (`:175-177`), so YAML 1.1 `no`/`off` are real `False` (live run) while the string `"false"` is truthy (dry run).
- The dataclass default is `dry_run=False` (`:163`): a config that omits `dry_run` deletes. The CLI can force a dry run but never force a live one (`:357-358`).
- `exclude` is matched with `fnmatchcase(entry.name, pattern)` (`:263`): only a single directory name can match, never a path.
- An unknown key calls `logging.warning` before `setup_logging` (`:179` vs `:365`); the implicit root handler makes the later `basicConfig` a no-op (`:334`).
- `normalize()` resolves `roots` against CWD and expands only `~` (`:184`).
- Dry-run output still says "Removed" and "deleted" (`:287-308`) [VERIFIED W3 P3, R9].

## Errors that look like something else

This section lists failures whose exit code or message points the wrong way.

- Exit 2 means both "critical findings under the `critical`/`serious` gate" and "argparse usage error" for doctor, and both "coverage regression" and "usage error" for delta.py [VERIFIED W3 L3, DL5] [D-18](../DISCOVERY-LEDGER.md#d-18), [D-21](../DISCOVERY-LEDGER.md#d-21).
- `init-test-harness FILE` where FILE exists as a regular file prints `error: [Errno 17] File exists` (exit 1), which reads like an overwrite refusal [VERIFIED W3 T4].
- `onboard.py --python /path/to/venv/bin/python` on a symlinked venv reports that `/usr/local/bin/python3.x cannot import somnus_debug` because the path is `resolve()`d [VERIFIED lane F OB-1]; a nonexistent path is a traceback, exit 1 [VERIFIED W3 OB6] [D-20](../DISCOVERY-LEDGER.md#d-20).
- pycache `max_depth: "2"` surfaces as `'>' not supported between instances of 'int' and 'str'` (exit 1) [VERIFIED W3 P14].

## A pre-flight checklist

This section condenses the fixes into checks to run before trusting a configuration.

1. The command line contains `-c <file>` for `scan`, `history`, and `rollback` alike.
2. Every string value is double-quoted; booleans are bare `true`/`false`.
3. The scan summary shows `files=` equal to what you expect (compare with `find . -name '*.py' | wc -l` minus your ignores).
4. `ignore_patterns` lists every default you still want, and no directory name in it collides with a real package directory.
5. For security review, `ignore_functions: []` and `check_nested_functions: true`.
6. doctor runs in the project's interpreter (or with `PYTHONPATH` covering `src/`), from a scratch CWD.
7. pycache configs: absolute roots, bare-name excludes, explicit `dry_run: true`, no unknown keys.
8. For delta gating: identical config for baseline and latest, narrow dispositions.

## Sources

This section lists the evidence behind this page.

- [`../_evidence/configuration-registry.tsv`](../_evidence/configuration-registry.tsv)
- [`../_evidence/agent-findings/lane-b-config/configuration-findings.md`](../_evidence/agent-findings/lane-b-config/configuration-findings.md) sections 1, 7
- [`../_evidence/agent-findings/lane-f-ext/fieldkit.md`](../_evidence/agent-findings/lane-f-ext/fieldkit.md)
- `src/somnus_debug/doctor/core.py:816-851,937-952,1235-1238,2046-2063`, `src/somnus_debug/pycache_cleaner/core.py:157-365`, `src/somnus_debug/test_harness/templates/run_test.py:589-593,747-750`, `skills/somnus-debug-fieldkit/scripts/delta.py:159-191`, `docs/MANUAL.md` sections 3.1, 3.4, 5.1, `docs/Python_Doctor_QUICKSTART.md`
- W3 probes and recipes cited per row
