# Test architecture

This page describes every layer of automated checking that exists for somnus-debug 0.1.0: what each layer runs, how it isolates itself, what it can and cannot detect, and how this wiki's own verification sits on top. Results are on [verification-results](verification-results.md).

## Layers

This section lists the layers from most to least official.

| Layer | Location | Size | Runner | Ships in wheel/sdist? |
|---|---|---|---|---|
| Repo smoke suite | `tests/test_cli_smoke.py` | 12 test functions | pytest | no |
| Fieldkit contract test | `skills/somnus-debug-fieldkit/scripts/selftest.py` | 29 checks in 4 groups | plain Python | no |
| Single-test harness | `src/somnus_debug/test_harness/templates/run_test.py` (template) | 1 project-defined test | plain Python | yes (as package data) |
| Wiki evidence probes | `wiki/_evidence/agent-findings/lane-*/` plus W2 runs on this page set | about 150 recorded runs | shell / Python in `/tmp` | no |
| CI | none (no `.github/`, no tox/nox config) | 0 | n/a | n/a |

[SOURCE-CONFIRMED] repo file list; `tests/test_cli_smoke.py`; lane F [fieldkit.md](../_evidence/agent-findings/lane-f-ext/fieldkit.md) section 1.

## Repo smoke suite

This section explains how `tests/test_cli_smoke.py` works and what that implies.

- **Mechanism.** Every test calls `_run(*args)`, which runs `[sys.executable, "-m", "somnus_debug.cli", *args]` in a subprocess. It uses `cwd=REPO_ROOT` (unless overridden), prepends `REPO_ROOT/src` to `PYTHONPATH`, and has a 30 s timeout (`tests/test_cli_smoke.py:51-62`).
- **What is under test.** The `src/` tree next to the tests, **not** the installed package. Installing the wheel does not change the results. [VERIFIED] W2-03: an installed venv ran the suite and the failures pointed at `/tmp/w2/repo-copy/src/...`.
- **Interpreter.** Whatever runs pytest. That interpreter must have PyYAML, because `-m somnus_debug.cli` imports the pycache tool.
- **Side effects.** Tests run doctor with `cwd=REPO_ROOT`, so `production_doctor.log` is written to the repo root. Without `PYTHONDONTWRITEBYTECODE=1`, `__pycache__/` directories appear under `src/` and `tests/`. [VERIFIED] W2-03 (the log appeared at `/tmp/w2/repo-copy/`); lane D [test-coverage.md](../_evidence/agent-findings/lane-d-cli-tests/test-coverage.md) section 1. Run the suite on a copy.
- **Isolation.** Five tests use pytest's `tmp_path`, and the degraded-state and init-config tests also pass `cwd=tmp_path`:
  - degraded-state scan
  - init-config drift guard
  - type-comment regression
  - scaffold
  - refuse-overwrite

  The remaining tests run with `cwd=REPO_ROOT`. Of those, `test_doctor_help` is the one that drops `production_doctor.log` at the repo root. [SOURCE-CONFIRMED] `tests/test_cli_smoke.py:83-181`.
- **Depth.** The module docstring says it plainly: "These are intentionally shallow ... not a replacement for exercising each tool's actual diagnostic logic." No test asserts any doctor detector output. [SOURCE-CONFIRMED] `tests/test_cli_smoke.py:33-39`.

The 12 tests, grouped:

| Group | Tests |
|---|---|
| plumbing (help, rc) | `test_top_level_help`, `test_unknown_command_exits_nonzero`, `test_structure_help`, `test_doctor_help`, `test_pycache_clean_help`, `test_init_test_harness_help` |
| behavior | `test_doctor_scan_degrades_when_sqlite_state_is_unavailable`, `test_init_test_harness_scaffolds_into_tmp`, `test_init_test_harness_refuses_overwrite_without_force` |
| drift guard | `test_packaged_default_config_matches_init_config` |
| regression / e2e | `test_structure_tolerates_type_like_comments`, `test_structure_self_index` (both **fail** on 0.1.0) |

`test_init_test_harness_refuses_overwrite_without_force` contains a no-op assertion (`assert ... or True`). The real check is on the next line. [SOURCE-CONFIRMED] lane D test-coverage section 2.

## Fieldkit contract test

This section explains `selftest.py`.

- **Purpose.** It proves the CLI on PATH (or `--python`) still behaves the way the fieldkit's reference docs say. Every row cites the reference file it guards.
- **Groups.** CLI surface (version, 8 help surfaces, 3 init-config defaults); exit codes and side effects; finding triggers; other tools. There are 29 checks in total.
- **Isolation.** It builds every fixture in `TemporaryDirectory(prefix="sd-selftest-")` and passes `cwd` into it for each call, so it writes nothing outside the temp directory. [VERIFIED] lane F.
- **Exit codes.** 0 all pass, 1 any fail, 3 no CLI.
- **Known blind spots:**
  - Its structure fixture has no metadata header, so it cannot see [D-01](../DISCOVERY-LEDGER.md#d-01).
  - It overwrites `PYTHONPATH` in the src-layout check, so `--python` only works with an installed package (28/29 otherwise, W2-04).
  - It tests the *absence* of `test_gaps` as a sentinel, which means it will flag a future fix as a FAIL. That is intended.

## Single-test harness

This section places `run_test.py` in the picture. It is a contract for **downstream** projects, not a test of somnus-debug.

The contract:

- one `execute_test(ctx) -> TestOutcome`
- PASS only if `checks` is non-empty and every check passes
- artifacts (`manifest.json`, `report.md`, `test.log`) on every run, including exceptions
- exit 0 or 1

The repo never runs it against itself. The shipped body is a Golden Path cargo test, so running it unedited is a FAIL. [VERIFIED] W2-19; lane F [harness.md](../_evidence/agent-findings/lane-f-ext/harness.md).

## Wiki evidence probes

This section explains the verification layer this wiki added, which is what most behavior claims rest on.

- Lanes A, B, D, and F ran fixtures in `/tmp/<lane>/`. They used installed venvs or `PYTHONPATH=src`, `PYTHONDONTWRITEBYTECODE=1`, and cwd always outside the repo.
- Each lane recorded commands, exit codes, and outputs in its findings directory, for example lane D's [experiments.jsonl](../_evidence/agent-findings/lane-d-cli-tests/experiments.jsonl): stdout, stderr, and file deltas per run.
- This page set's own runs are numbered W2-01 to W2-26 on [verification-results](verification-results.md#w2-runs).
- `/tmp` was wiped twice during the waves: once in lane D's run, and once around 00:40 UTC during W2. Fixtures are therefore described inline, so they can be rebuilt. Probes that rebuild them are on [reproducible-probes](reproducible-probes.md).

## What the layers cannot see together

This section names the structural gap.

No layer runs the doctor's detectors against a fixture with known expected findings and asserts the exact result. Twelve detector categories have no automated check in either pytest or selftest:

- `tokenization_errors`
- `analysis_read_errors`
- `unused_imports`
- `dependency_cycles`
- `placeholder_returns`
- `incomplete_methods`
- `suspicious_short_classes`
- `broad_exceptions`
- `security_risks`
- `missing_docstrings`
- `type_hint_gaps`
- `complexity`

State, history, and rollback have no automated check either. [VERIFIED by inventory] lane D test-coverage section 5. See [untested-behaviors](untested-behaviors.md).

## Sources

This section lists the code and evidence this page draws on.

- `tests/test_cli_smoke.py:33-62`, `:138-181`
- `skills/somnus-debug-fieldkit/scripts/selftest.py:145-346`
- `src/somnus_debug/test_harness/templates/run_test.py:747-855`
- [lane D test-coverage.md](../_evidence/agent-findings/lane-d-cli-tests/test-coverage.md); [lane F fieldkit.md](../_evidence/agent-findings/lane-f-ext/fieldkit.md), [harness.md](../_evidence/agent-findings/lane-f-ext/harness.md)
- W2 runs: [verification-results](verification-results.md#w2-runs)
