# Failure recovery

This page maps the failures an agent will actually see from somnus-debug and its fieldkit to their cause and the next action. Each row is a failure observed in this wave or by an earlier lane; the symptom column is what appears on screen.

## Doctor

This section covers `doctor scan` and its siblings.

| Symptom | Cause | Action | Evidence |
|---|---|---|---|
| `Scan complete: files=0 …`, exit 0 | Include/ignore globs match nothing; an adopted config from another layout; `X/*` pruning a same-named directory | Treat as failure. Fix `include_patterns`/`ignore_patterns`, rerun `onboard.py` plan mode | [D-17](../DISCOVERY-LEDGER.md#d-17) [VERIFIED] |
| Exit 4, `Doctor failure: Configuration value must be a non-empty string.` with `"key": "severity_exit_level", "value": "None"` | Unquoted `none` in YAML | Write `"none"` | [stage 2 log](../09-recipes/_repro/logs/stage2_intermediate.log) [VERIFIED]; [D-03](../DISCOVERY-LEDGER.md#d-03) |
| Exit 4, `Invalid severity_exit_level.` | Gate not in `critical, serious, minor, info, none` | Fix the value | [stage 5 log](../09-recipes/_repro/logs/stage5_automation.log) [VERIFIED] |
| Exit 4, `Configuration file does not exist.` | Relative `-c` path resolved against a different cwd | Pass an absolute path | [first-attempt log](../09-recipes/_repro/logs/stage6c_first_attempt_relative_paths.log) [VERIFIED] |
| Exit 1 or 2 where the config should have made it 0 | Config not passed (`-c` missing, no auto-discovery), or a misspelled key ignored | Pass `-c`; diff the config against `init-config` output for typos | [D-02](../DISCOVERY-LEDGER.md#d-02), [D-04](../DISCOVERY-LEDGER.md#d-04) [VERIFIED] |
| Exit 2 and `usage:` on stderr | argparse error, not a critical finding | Fix the command line | [D-18](../DISCOVERY-LEDGER.md#d-18) [VERIFIED by lane D] |
| Exit 1 with `ModuleNotFoundError: somnus_debug`, no report | Interpreter without the package, e.g. a venv path passed through `Path.resolve()` | Use the venv path as-is (`absolute()`), or the profile runner | [second-attempt log](../09-recipes/_repro/logs/stage6c_second_attempt_resolved_interpreter.log) [VERIFIED: no report written] |
| Exit 5 | Unclassified runtime error, e.g. `RecursionError` on one pathological file aborts the whole scan | Find the file (log, traceback), exclude it deliberately with a recorded reason, scan it separately | [D-18](../DISCOVERY-LEDGER.md#d-18) [VERIFIED by lane D] |
| Many `missing_imports` for real dependencies | Doctor running outside the project's environment | Use the project venv runner; src layout needs `PYTHONPATH=src` | [D-26](../DISCOVERY-LEDGER.md#d-26) [VERIFIED by lane F selftest] |
| `dependency_cycles: 0` in a src layout you know has a cycle | `PYTHONPATH=src` classifies own imports as third-party | Second scan rooted at `src/` | [src-layout-cycle-check](../09-recipes/advanced/src-layout-cycle-check.md) [VERIFIED] |
| `Warning: local SQLite state is unavailable; continuing without history or rollback` | State DB could not be initialized (permissions, or a concurrent scan) | Results are valid; history for this run is missing. Serialize stateful scans | [stage 6d log](../09-recipes/_repro/logs/stage6d_parallel.log) [VERIFIED] |
| A scan is missing from `doctor history` | Two scans in the same second share a run ID | Space stateful scans by ≥ 1 s; rely on `runs/*.json`, not history | [D-08](../DISCOVERY-LEDGER.md#d-08) [VERIFIED] |
| `history` empty, or a stray `.python_doctor/` appears | `history`/`rollback` run without the same `-c` as the scans (custom `state_dir`) | Pass the profile config | [lane-b §7](../_evidence/agent-findings/lane-b-config/configuration-findings.md) [VERIFIED by lane B] |
| `rollback` exit 4, `Run ID does not exist in state history.` | Unknown run ID | Read `history` first | [stage 5 log](../09-recipes/_repro/logs/stage5_automation.log) [VERIFIED] |
| Markdown report contains JSON | `-o report.json` | `-o` takes the `.md` path; `--json-output` the JSON | [D-25](../DISCOVERY-LEDGER.md#d-25) [VERIFIED by lane D] |
| Host program's logs stop appearing after calling `main()` | `basicConfig(force=True)` replaced the root handlers | Use `ProjectScanner`, or restore handlers | [inprocess-main-isolated](../09-recipes/programmatic/inprocess-main-isolated.md) [VERIFIED] |
| `ImportError: yaml` from `somnus-debug doctor …` | Dispatcher imports every tool; PyYAML missing | Install PyYAML in that environment, or call `somnus-doctor` / `python -m somnus_debug.doctor.core` | [D-13](../DISCOVERY-LEDGER.md#d-13) [VERIFIED by lane B] |

## Fieldkit

This section covers `onboard.py`, `delta.py` and `selftest.py`.

| Symptom | Cause | Action | Evidence |
|---|---|---|---|
| `onboard.py … --python <venv>/bin/python` → `BLOCKED: no usable somnus-debug`, exit 3 | `--python` resolves the venv symlink to the base interpreter | Omit `--python` and let the project `.venv` be found, or use a `venv --copies` interpreter | [stage 6 log](../09-recipes/_repro/logs/stage6_integrations.log) [VERIFIED]; [D-20](../DISCOVERY-LEDGER.md#d-20) |
| `onboard.py` traceback `RuntimeError: doctor scan produced no summary`, exit 1 | Doctor failed with the adopted config (exit 4) | Run the scan by hand to read doctor's error; fix or `--new-config` | [lane-f fieldkit OB-2](../_evidence/agent-findings/lane-f-ext/fieldkit.md) [VERIFIED by lane F] |
| `PROFILE.md` exists but no `runs/baseline.json` | Verify scan failed; `--apply` still wrote the profile | Read the PROFILE's verification line; fix coverage; delete `PROFILE.md`; rerun `--apply --baseline` | [lane-f fieldkit OB-3](../_evidence/agent-findings/lane-f-ext/fieldkit.md) [VERIFIED by lane F] |
| `delta.py` exit 2 with `usage: delta.py …` | Missing argument (argparse) | Fix the command; do not read it as coverage loss | [stage 6 log](../09-recipes/_repro/logs/stage6_integrations.log) [VERIFIED] |
| `delta.py` exit 2 with `COVERAGE REGRESSION` | Latest scanned 0 files, or a baseline file is no longer scanned but still on disk | Fix coverage; the finding counts are meaningless until then | [lane-f fieldkit D1, D2](../_evidence/agent-findings/lane-f-ext/fieldkit.md) [VERIFIED by lane F] |
| `delta.py` exit 3, `… is not a somnus-debug doctor JSON report` | Wrong file, empty or partial report | Rescan; check paths | [stage 6 log](../09-recipes/_repro/logs/stage6_integrations.log) [VERIFIED] |
| `delta.py` exit 3, `[0] needs non-empty string category, file, and reason` | Disposition missing a required field | Add the reason | same [VERIFIED] |
| `delta.py` traceback `KeyError: 'category'`, exit 1 | An issue object without `category` (hand-edited or foreign report) | Regenerate the report; never treat this exit 1 as "regression" without reading stderr | same [VERIFIED] |
| `note: dispositions.json not found; continuing without dispositions` | Wrong cwd or path | Run from `.somnus-debug/`; the run is stricter, not looser | same [VERIFIED] |
| `delta.py` exit 0 but you added a risky call | A broad disposition (`file: "src/*"`) absorbed it, or the latest scan ran with a downgraded severity | Inspect `dispositioned` count and the dispositions file; compare `config_hash` of both reports | [customization](../08-extensions/customization.md) [VERIFIED]; [D-21](../DISCOVERY-LEDGER.md#d-21) |
| A finding you fixed reappears as new under another name | Rename changed `symbol`; identity includes symbol and message | Expected; its old disposition is now stale and must be removed | [lane-f fieldkit D9](../_evidence/agent-findings/lane-f-ext/fieldkit.md) [VERIFIED by lane F] |
| `selftest.py` exit 3 | No `somnus-debug` on PATH and no `--python` | Pass `--python <venv>/bin/python` | [stage 6 log](../09-recipes/_repro/logs/stage6_integrations.log) [VERIFIED] |
| `selftest.py` exit 1 | Installed CLI and the fieldkit references disagree | Trust the CLI; update the referenced file (`SKILL.md:129`) | [fieldkit-selftest](../09-recipes/integrations/fieldkit-selftest.md) |

## Other tools

This section covers `structure`, `pycache-clean` and the harness.

| Symptom | Cause | Action | Evidence |
|---|---|---|---|
| `structure` exit 2, `invalid syntax (…, line 9)` on a file that runs fine | `type_comments=True` reading the metadata header | [index-stamped-file](../09-recipes/programmatic/index-stamped-file.md) | [D-01](../DISCOVERY-LEDGER.md#d-01) [VERIFIED] |
| `pycache-clean` says "Removed …" but nothing changed | Dry run; the wording is misleading | None needed | [pycache-dry-run](../09-recipes/beginner/pycache-dry-run.md) [VERIFIED] |
| `pycache-clean` deleted files it should not have | Untyped config (`dry_run: no`), scalar `roots`, broad `targets`, path-style `exclude` | Stop; restore from version control; rewrite the config from the fieldkit's template | [D-14](../DISCOVERY-LEDGER.md#d-14) [VERIFIED by lanes A, B and this wave] |
| `pycache-clean` prints nothing at INFO | An unknown config key triggered an early warning that pre-empted logging setup | Remove the unknown key | [lane-b §1 item 8](../_evidence/agent-findings/lane-b-config/configuration-findings.md) [VERIFIED by lane B] |
| `init-test-harness` exit 1, `refusing to overwrite` | Files exist | Choose another directory; `--force` only with authority | [harness-pytest](../09-recipes/integrations/harness-pytest.md) [VERIFIED] |
| Harness `test-runs/` appears next to the repo, not in it | Scaffolded at the repo root | Scaffold into a subdirectory, or set `PROJECT_ROOT` | [D-15](../DISCOVERY-LEDGER.md#d-15) [VERIFIED by lanes B, D, F] |
| Harness FAIL with 0 checks, `FileNotFoundError: 'cargo'` | Unedited template | Replace `execute_test()` | [lane-f harness H-1](../_evidence/agent-findings/lane-f-ext/harness.md) [VERIFIED by lane F] |
| Harness FAIL with 0 checks, `KeyError: 'SD_PYTHON'` in `test.log` | Env var for the doctor surface not set | Export `SD_PYTHON`, `FIELDKIT`, `TEST_PYTHON` | [stage 6 log](../09-recipes/_repro/logs/stage6_integrations.log) [VERIFIED] |

## When to stop and ask

This section lists failures an agent should not work around on its own.

- Any fix that needs lowering a severity, a gate, or excluding source to get green (`skills/somnus-debug-fieldkit/SKILL.md:109`).
- Installing somnus-debug or PyYAML into the project's environment (`SKILL.md:53`).
- A live `pycache-clean`, `--force`, or a hook/CI install (`SKILL.md:110`).
- The same failure surviving three repair attempts: record it as a blocker with its evidence.

## Sources

This section lists the files, logs and evidence this page rests on.

- [stage logs](../09-recipes/_repro/README.md), [recipes execution log](../09-recipes/execution-log.md)
- [lane-d exit codes](../_evidence/agent-findings/lane-d-cli-tests/exit-codes.md), [lane-f fieldkit](../_evidence/agent-findings/lane-f-ext/fieldkit.md), [lane-f harness](../_evidence/agent-findings/lane-f-ext/harness.md), [lane-b configuration findings](../_evidence/agent-findings/lane-b-config/configuration-findings.md)
- `skills/somnus-debug-fieldkit/SKILL.md:50-129`
