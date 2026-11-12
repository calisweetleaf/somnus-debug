# Lane F: test harness (`init-test-harness`, `templates/run_test.py`, `CONTRACT.md`)

Files: `src/somnus_debug/test_harness/scaffold.py`, `src/somnus_debug/test_harness/templates/{run_test.py, CONTRACT.md, __init__.py}`. Real file line numbers are used throughout (each file has a ~32-line metadata header). Runs: `repro/s4_harness_more.sh` → `logs/s4_harness.log`, `logs/s4_C5.log`.

## 1. The scaffold command

- **CLI** (`scaffold.py:91-109`): `somnus-debug init-test-harness [target=.] [--force] [--no-contract]`. There is no standalone console script; `pyproject.toml` defines only 3 per-tool scripts.
- **Behavior** (`scaffold.py:62-88`):
  1. Resolves the target. Without `--force`, if **any** destination exists it raises `FileExistsError` before writing anything.
  2. Otherwise it runs `mkdir -p` on the target and writes `run_test.py` (plus `CONTRACT.md` unless `--no-contract`). The text comes from package data via `importlib.resources`.
- **Exit codes:** 0 written; 1 refused (`scaffold.py:116-118`); argparse errors 2.
- **Library:** `scaffold(target_dir, *, force=False, with_contract=True) -> list[Path]`.

VERIFIED (`logs/s4_harness.log`): H1 writes both (exit 0); H2 refuses with the existing paths listed (exit 1); H3 `--no-contract` writes only run_test.py into a new `single_test/` dir; H4 `--force` overwrites (exit 0); H5 `scaffold()` returns `[PosixPath('.../run_test.py')]`.

The template `run_test.py` and `CONTRACT.md` are byte-identical to the repo-root `run_test.py` and `docs/CONTRACT.md` apart from the metadata `id` URNs (`diff`, SOURCE-CONFIRMED).

## 2. What the scaffolded `run_test.py` does

The contract surface, which the project edits:
- `TEST_NAME` (`run_test.py:195`).
- `execute_test(ctx: TestContext) -> TestOutcome` (`:198`).
- `TestContext{run_id, project_root, artifact_dir, logger}`.
- `TestOutcome{summary, checks: list[Check], metrics, evidence, notes}`. `passed` is true only if `checks` is non-empty and all of them pass.
- `Check{name, passed, detail, expected, observed}` (`:143-180`).
- Helper `_run_command(argv, cwd, logger, expected=0)`. It logs the command and its output and raises `RuntimeError` on an unexpected exit code (`:492-527`).

The machinery (`main`, `:747-855`):
1. **Project root** = `$PROJECT_ROOT`, else **the parent of the directory containing run_test.py** (`:749`).
2. Run ID = `<SLUG(TEST_NAME).upper()>-<YYYYmmdd-HHMMSS>-<6 hex>`.
3. Artifact dir = `$SINGLE_TEST_OUTPUT_DIR/<run_id>`, else `<project_root>/test-runs/<run_id>`, created with `exist_ok=False`.
4. Logger writes `test.log` at DEBUG and stderr at INFO.
5. Calls `execute_test`. Any `Exception` (not `BaseException`) is captured as `error{type,message,traceback}` and logged (`:802-808`). A non-`TestOutcome` return or an empty `checks` list is turned into an error (`:786-794`).
6. Writes `manifest.json` (schema below) and `report.md` (factual rendering: checks table, metrics, evidence, notes, failure block, artifact roles).
7. Prints a final JSON summary `{run_id, test_name, verdict, elapsed_s, artifacts{manifest,report,log}}` to **stdout**. Progress goes to stderr.

- **Exit:** 0 if verdict PASS, else 1 (`:855`).
- **Flags:** **none.** `main()` reads no argv. `run_test.py --help` simply runs the test (VERIFIED H8, exit 1). Configuration is the two env vars only.

`manifest.json` (schema_version "1.0", `:489`, `:596-645`):
```text
{schema_version, run_id, test_name, verdict: "PASS"|"FAIL", started_at_utc, finished_at_utc, elapsed_s,
 environment:{python, python_executable, platform, cwd, project_root, runner},
 acceptance:{total_checks, passed_checks, failed_checks, checks:[{name,passed,detail,expected,observed}]},
 result:{summary, metrics, evidence, notes}, error: null|{type,message,traceback},
 artifacts:{manifest:"manifest.json", report:"report.md", log:"test.log"}}
```

## 3. Findings

| # | Finding | Class | Evidence |
|---|---|---|---|
| H-1 | **The shipped template is not neutral.** `execute_test()` contains a full project-specific "GOLDEN PATH LAYER 1 DATA HIGHWAY RESTORATION" test that shells out to `cargo metadata`/`cargo build -p gp-cli` and exercises a `gp` binary and SQLite ledgers. Its docstring admits this ("Everything after this docstring is specific to gp-cli / Golden Path"). Run unedited in any other repo, it FAILs with `FileNotFoundError: 'cargo'` and 0 checks. The contract handles this correctly (FAIL, artifacts, exit 1), but there is no runnable placeholder. | VERIFIED | `run_test.py:195-482`; `logs/s4_harness.log` H6/H7 |
| H-2 | **The default scaffold location puts artifacts outside the repo.** `init-test-harness` defaults to `.` (repo root), but `run_test.py` defaults `project_root` to the **parent of its own directory**. A root-scaffolded harness therefore treats the repo's parent as the project and writes `../test-runs/`. VERIFIED: `environment.project_root: /tmp/lane-f`, artifacts in `/tmp/lane-f/test-runs/`. CONTRACT.md's "Copy this directory into the repository" implies a subdirectory layout, which works (H7 → `<repo>/test-runs/`). Fix-free workarounds: scaffold into `<repo>/<subdir>` or set `PROJECT_ROOT`. | VERIFIED / DISCREPANCY (scaffold default vs template default) | `scaffold.py:100`; `run_test.py:749`; H6 vs H7, H9 |
| H-3 | **The scaffolded file is itself a doctor regression source.** Once it lives in the repo, the next doctor scan picks it up as a new file. It produced 9 new serious findings that made delta exit 1: `security_risks` ×4 (subprocess in `execute_test`/`_run_command`), `broad_exceptions` ×2, `silent_failures` (handler cleanup in `_setup_logger`), and `suspicious_short_classes` ×2 (frozen dataclasses `Check`, `TestContext`). Several are attributed to `<module>` because they sit in private functions. Narrow dispositions (4 entries) cleared them. | VERIFIED | `logs/s4_C5.log` C5a→C5b |
| H-4 | `run_test.py` takes no CLI flags. Only `PROJECT_ROOT` and `SINGLE_TEST_OUTPUT_DIR` are configurable. | VERIFIED | `run_test.py:747-760`; H8, H9 |
| H-5 | Exceptions in `execute_test` produce a FAIL with full artifacts. `KeyboardInterrupt`/`SystemExit` are not caught (they derive from `BaseException`), so no manifest is written in that case. | VERIFIED (Exception path, C5d) / SOURCE-CONFIRMED (BaseException) | `run_test.py:802`; `logs/s4_C5.log` C5d |
| H-6 | The template imports `hashlib, shutil, sqlite3, subprocess, tempfile` "Common in execute_test() — remove if unused". After an edit, doctor's `unused_imports` will flag whichever ones remain unused. | SOURCE-CONFIRMED | `run_test.py:131-136` |
| H-7 | The template's module docstring carries operator-specific narrative (hours logged, standards). It ships into every scaffolded repo. Informational. | SOURCE-CONFIRMED | `run_test.py:34-112` |

## 4. CONTRACT.md: claims vs template

| CONTRACT claim (docs/CONTRACT.md == templates/CONTRACT.md) | Template behavior | Verdict |
|---|---|---|
| L61: one primary Python test entrypoint | one `execute_test` | matches |
| L64: unique run ID and own artifact dir | uuid-suffixed ID; `mkdir(exist_ok=False)` | matches (VERIFIED H6/H7/H9) |
| L65-68: three artifacts every run | always written, including on exception (C5d) | matches (VERIFIED) |
| L69: one unambiguous PASS/FAIL | verdict plus exit 0/1 | matches |
| L70: exception = failed run, still produces artifacts "when possible" | `Exception` yes; `BaseException` no | matches ("when possible") |
| L98-99: metrics are not acceptance unless the test makes them so | `passed` depends only on `checks` | matches |
| L118-121: report may be extended but not override the verdict | report is generated from the manifest; nothing enforces later edits | documented-only (policy) |
| L123-132: "edit only `TEST_NAME` and `execute_test`" | true, but the shipped `execute_test` is gp-cli specific (H-1), so the edit is mandatory | matches with caveat |
| L123 "Copy this directory into the repository" | scaffold defaults to repo root, which breaks the root default (H-2) | DISCREPANCY (with scaffold default) |
| L143-147: no Accelerate dependency | no such import or coupling | matches |

## 5. How an agent uses it (VERIFIED recipe)

1. Scaffold one level down: `somnus-debug init-test-harness <repo>/single_test --no-contract` (or keep CONTRACT.md).
2. Replace the block from `TEST_NAME =` down to the `# Harness internals` banner with the project's real test. `recipes/harness_doctor_surface.py` does exactly that splice, for a test that runs the project's pytest, a doctor rescan, and `delta.py` as three named checks.
3. Run `python3 single_test/run_test.py` from anywhere. Read the stdout JSON for the artifact paths, and `manifest.json` for the verdict and checks.
4. If the repo is under the doctor loop, disposition the harness file's template-inherited findings narrowly (H-3).

VERIFIED results (`logs/s4_C5.log`): clean tree → **PASS, exit 0** (checks: project-tests-pass, doctor-ran, no-new-serious-findings; metrics record raw doctor exit 1 and score). After adding `os.system` → **FAIL, exit 1**, `regressions: [('security_risks','risky')]`, and the artifact dir holds `doctor_latest.{md,json}` next to `manifest.json`, `report.md`, `test.log`. With an env var missing → FAIL, 0 checks, `KeyError` traceback in `test.log`.
