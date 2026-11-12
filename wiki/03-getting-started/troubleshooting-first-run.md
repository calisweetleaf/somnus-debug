# Troubleshooting the first run

This page maps the symptoms people hit in their first hour to a cause and a fix. Each entry was reproduced by execution in this wave or by an evidence lane; the run is cited.

## Symptom index

This section is the lookup table; details follow.

| Symptom | Cause | Fix | Evidence |
|---|---|---|---|
| `production_doctor.log` appears in my repo | doctor opens it in **cwd** on every call | run doctor from another directory | [VERIFIED] W2-01, W2-21. See [D-10](../DISCOVERY-LEDGER.md#d-10) |
| my `python_doctor.yaml` is ignored | no auto-discovery | pass `-c python_doctor.yaml` | [VERIFIED] lane D D27/D27b; lane B E1/E2. See [D-02](../DISCOVERY-LEDGER.md#d-02) |
| `Doctor failure: Configuration value must be a non-empty string.` with `"key": "severity_exit_level", "value": "None"`, exit 4 | unquoted `none` parsed as null | write `severity_exit_level: "none"` | [VERIFIED] W2-08. See [D-03](../DISCOVERY-LEDGER.md#d-03) |
| config edits have no effect, and no error | malformed YAML or a misspelled key is accepted silently | validate the file (for example, load it with PyYAML) and compare key names against `init-config` output | [VERIFIED] lane D D29, D30. See [D-04](../DISCOVERY-LEDGER.md#d-04) |
| `Scan complete: files=0`, exit 0 | globs do not match (for example this repo's root `python_doctor.yaml`, which has Somnus-MCP globs), or `include_patterns: []` | regenerate with `init-config`; always assert `files_scanned > 0` | [VERIFIED] lane D D17; lane F OB-5. See [D-17](../DISCOVERY-LEDGER.md#d-17) |
| a real package directory named `env/`, `build/`, or `venv/` is never scanned | default `X/*` ignores prune same-named directories at any depth | remove or narrow those ignore entries | [VERIFIED] lane B finding 5 |
| `missing_imports` on my own package | src layout without `PYTHONPATH=src` | `PYTHONPATH=<repo>/src somnus-debug doctor scan ...` | [VERIFIED] W2-14 |
| `missing_imports` on an installed library | doctor's interpreter does not have it | install somnus-debug into the project's venv | [VERIFIED] lane D D05a/b. See [D-26](../DISCOVERY-LEDGER.md#d-26) |
| exit 1 under `severity_exit_level: "minor"` although there are criticals | the `minor`/`info` gates return 1, never 2 | read `summary.critical_issues` | [VERIFIED] W2-08. See [D-18](../DISCOVERY-LEDGER.md#d-18) |
| `-v` gives no extra output | `-v` is ignored; `--verbose` has nothing to log | none needed; doctor has no debug output | [VERIFIED] W2-07 |
| my "report.json" contains JSON but no Markdown | `-o report.json` makes Markdown and JSON share one path | pass both `-o x.md` and `--json-output x.json` | [VERIFIED] W2-23. See [D-25](../DISCOVERY-LEDGER.md#d-25) |
| history shows one run where I ran two | same-second run IDs overwrite | space scans at least 1 s apart | [VERIFIED] W2-17. See [D-08](../DISCOVERY-LEDGER.md#d-08) |
| `self-check` failed with exit 4 or wrote files into site-packages | self-check writes next to `doctor/core.py` | `somnus-debug doctor self-check --no-state -o /tmp/sc.md --json-output /tmp/sc.json` | [VERIFIED] lane D D14/D15; lane B finding 11 |
| a doctor run ends with `Unclassified runtime failure: RecursionError ...`, exit 5 | a pathological expression on the serial analysis path (one file, or `max_workers: 1`) | exclude the file; with two or more files it becomes a per-file critical issue | [VERIFIED] lane D D44; [execution-model](../01-system/execution-model.md) |
| `structure`: `error: invalid syntax (<file>, line N)` on a file that runs fine | `type_comments=True` rejects comment lines shaped like `#   type: "..."` (every `# somnus:metadata:v2` header) | use `python3 <repo>/analyze_python_structure.py FILE`, or strip the header first | [VERIFIED] W2-15. See [D-01](../DISCOVERY-LEDGER.md#d-01) |
| `structure`: `UnicodeDecodeError` traceback, exit 1 | non-UTF-8 source; only `OSError`/`SyntaxError` are handled | re-encode the file as UTF-8 | [VERIFIED] W2-09 |
| `structure -o` printed nothing | it writes silently (the README shows a message it never prints) | check the file | [VERIFIED] W2-22 |
| `somnus-debug doctor --help` fails with `No module named 'yaml'` | the dispatcher imports the pycache tool, which needs PyYAML | `pip install pyyaml`, or use `somnus-doctor` or `python -m somnus_debug.doctor.core` | [VERIFIED] W2-05. See [D-13](../DISCOVERY-LEDGER.md#d-13) |
| `SyntaxWarning: invalid escape sequence '\`'` on stderr | docstring at `pycache_cleaner/core.py:64`, compiled without a cached `.pyc` | harmless; set `PYTHONWARNINGS=ignore` to hide it | [VERIFIED] W2-01 |
| `pycache-clean`: `Configuration file not found: .../config.yaml` | the default config path is `./config.yaml` | `--config /abs/path.yaml` | [VERIFIED] lane D P04 |
| `pycache-clean` says "Removed ..." in dry-run | same wording in both modes | trust the `dry_run=True` header line | [VERIFIED] W2-18 |
| `pycache-clean` printed only `WARNING:root:Ignoring unknown config key ...` | that warning pre-empts logging setup, so all later output is lost (deletion still happens) | remove the unknown key | [VERIFIED] lane D P09. See [D-14](../DISCOVERY-LEDGER.md#d-14) |
| `pycache-clean` ran live with `dry_run: no`, or stayed dry with `dry_run: "false"` | values are not type-checked; YAML `no` is false, and the string `"false"` is truthy | use `true`/`false` unquoted, or `--dry-run` | [VERIFIED] lane B finding 9 |
| a `test-runs/` directory appeared next to my repo | `run_test.py` at the repo root treats the parent directory as the project | scaffold into `<repo>/tools/` or set `PROJECT_ROOT` | [VERIFIED] W2-19. See [D-15](../DISCOVERY-LEDGER.md#d-15) |
| `run_test.py --help` ran a cargo test and FAILed | the template has no argument parser and ships a project-specific test | replace `execute_test` | [VERIFIED] lane D H09; W2-19 |
| doctor findings jumped after adding the harness | the template itself triggers 9 serious findings | disposition them narrowly or ignore the file | [VERIFIED] W2-19 |
| `pytest tests/` in the repo fails 2 tests | the `structure` crash above | expected for this tree; see [verification-results](../11-verification/verification-results.md) | [VERIFIED] W2-03 |
| `python -m somnus_debug` fails | no `__main__` module | use `python -m somnus_debug.cli` | [VERIFIED] lane D C04 |

## When the cause is not in the table

This section gives the diagnostic order to follow.

1. Re-run with the exit code printed (`; echo "exit=$?"`) and map it with [exit-codes](../05-cli-and-tools/exit-codes.md).
2. For doctor exit 4 or 5, read the stderr render and `production_doctor.log` in the cwd of that run. Those two codes are the only ones that log anything.
3. Run the fieldkit `selftest.py` against the same interpreter. 29/29 means the CLI behaves as the fieldkit documents. Note that its structure check misses the stamped-file crash. [VERIFIED] W2-04.
4. Compare against a fresh `/tmp` fixture, as in [quickstart](quickstart.md). If the fixture behaves, the cause is in your config or tree, not the install.

## Sources

This section lists the code and evidence this page draws on.

- `src/somnus_debug/doctor/core.py:625-626`, `:796-814`, `:937-947`, `:1953-1960`, `:2046-2058`, `:2179-2201`
- `src/somnus_debug/structure/core.py:210`, `:323-347`
- `src/somnus_debug/pycache_cleaner/core.py:64`, `:150-154`, `:170-180`, `:323-372`
- `src/somnus_debug/test_harness/templates/run_test.py:749`
- [lane D experiment-log.md](../_evidence/agent-findings/lane-d-cli-tests/experiment-log.md), [lane B configuration-findings.md](../_evidence/agent-findings/lane-b-config/configuration-findings.md), [lane F fieldkit.md](../_evidence/agent-findings/lane-f-ext/fieldkit.md)
- W2 runs: [verification-results](../11-verification/verification-results.md#w2-runs)
