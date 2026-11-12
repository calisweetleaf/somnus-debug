# Recipe: wire a project's pytest suite into the single-test harness

**Tier:** small integration step (the shipped test body must be replaced). **Tools:** `init-test-harness`, scaffolded `run_test.py`. **Script:** [surface_pytest.py](../_repro/surface_pytest.py).

Give a project one entry point that runs its tests and always leaves a verdict, a `manifest.json`, a `report.md` and a `test.log` in a fresh run directory, with exit 0 for PASS and 1 for FAIL.

## When to use

This section says what the harness adds over running pytest directly.

When an orchestrator, an agent or a reviewer needs a fixed artifact contract per run: a unique run ID, its own directory, a machine-readable manifest, and a FAIL with artifacts even when the test code raises. The contract is `src/somnus_debug/test_harness/templates/CONTRACT.md` [VERIFIED by lane F against the template]. Skip it if pytest's own output is enough.

## Steps

This section gives the scaffold, the edit, and the run.

```console
cd <repo>
<venv>/bin/python -m somnus_debug.cli init-test-harness single_test         # one level below the repo root, see pitfalls
python3 surface_pytest.py single_test/run_test.py                            # replace TEST_NAME and execute_test()
<venv>/bin/python single_test/run_test.py                                    # use an interpreter that has pytest
```

The edit replaces everything from `TEST_NAME = "` down to the `# Harness internals` banner (lines 195-485 of the template) with:

```python
TEST_NAME = "INVENTORY UNIT TESTS"


def execute_test(ctx: TestContext) -> TestOutcome:
    """Run the project's pytest suite once and turn its exit code into a check."""
    env = dict(os.environ, PYTHONPATH=str(ctx.project_root / "src"))
    proc = subprocess.run([sys.executable, "-m", "pytest", "-q", "tests"], cwd=ctx.project_root,
                          env=env, text=True, capture_output=True, check=False)
    ctx.logger.info("$ pytest -q tests\nexit=%s\n%s", proc.returncode, proc.stdout + proc.stderr)
    (ctx.artifact_dir / "pytest.txt").write_text(proc.stdout + proc.stderr, encoding="utf-8")
    return TestOutcome(
        summary="Project unit tests via pytest.",
        checks=[Check("pytest-exit-zero", proc.returncode == 0, expected=0, observed=proc.returncode)],
        metrics={"pytest_tail": proc.stdout.strip().splitlines()[-1] if proc.stdout.strip() else ""},
    )
```

`TestContext`, `TestOutcome`, `Check`, `os`, `subprocess` and `sys` are already defined or imported in the template [SOURCE-CONFIRMED, `src/somnus_debug/test_harness/templates/run_test.py:115-180`].

## Executed result

This section shows scaffold, refusal, PASS and FAIL.

Executed: yes (`/tmp/w4/proj_h`, copy of the onboarded fixture with its `.venv` holding pytest; [stage 6 log](../_repro/logs/stage6_integrations.log), section N1)

```text
$ .venv/bin/python -m somnus_debug.cli init-test-harness single_test
wrote /tmp/w4/proj_h/single_test/run_test.py
wrote /tmp/w4/proj_h/single_test/CONTRACT.md                                   [exit=0]
$ .venv/bin/python -m somnus_debug.cli init-test-harness single_test
error: refusing to overwrite existing file(s) without --force: .../run_test.py, .../CONTRACT.md   [exit=1]
$ grep -n '^TEST_NAME\|^def execute_test\|# Harness internals' single_test/run_test.py
195:TEST_NAME = "GOLDEN PATH LAYER 1 DATA HIGHWAY RESTORATION"
198:def execute_test(ctx: TestContext) -> TestOutcome:
486:# Harness internals
$ python3 surface_pytest.py single_test/run_test.py
surface applied to single_test/run_test.py
$ .venv/bin/python single_test/run_test.py 2>/dev/null
{ "run_id": "INVENTORY-UNIT-TESTS-20261112-004539-25ca2f", "test_name": "INVENTORY UNIT TESTS", "verdict": "PASS",
  "artifacts": { "manifest": "/tmp/w4/proj_h/test-runs/INVENTORY-UNIT-TESTS-.../manifest.json", "report": ".../report.md", "log": ".../test.log" } }   [exit=0]
$ ls test-runs/*/
manifest.json  pytest.txt  report.md  test.log
PASS [('pytest-exit-zero', True)] {'pytest_tail': '1 passed in 0.01s'} /tmp/w4/proj_h None
# break the test (expected = 4), rerun
FAIL                                                                           [exit=1]
FAIL [('pytest-exit-zero', False)] {'pytest_tail': '1 failed in 0.02s'} /tmp/w4/proj_h None
```

`environment.project_root` is the repo (`/tmp/w4/proj_h`) because the harness sits one directory down [VERIFIED].

## Pitfalls

This section lists the template's traps. Most are [D-15](../../DISCOVERY-LEDGER.md#d-15).

- **Scaffold one level down.** `run_test.py` defaults `PROJECT_ROOT` to the parent of its own directory (`run_test.py:749`). `init-test-harness` defaults to `.`, so a root-level scaffold treats the repo's parent as the project and writes `../test-runs/` outside the repo [VERIFIED by lanes B, D, F]. Or set `PROJECT_ROOT` explicitly.
- **The shipped `execute_test()` is a cargo/gp-cli test.** Unedited, it fails with `FileNotFoundError: 'cargo'` [VERIFIED by lane F, H6].
- **`run_test.py` takes no flags.** `--help` runs the test. Configuration is `PROJECT_ROOT` and `SINGLE_TEST_OUTPUT_DIR` only [VERIFIED by lane F, H8].
- **`sys.executable` must have pytest.** Run the harness with the project's interpreter, not a bare `python3`.
- **The harness file becomes doctor input.** In an onboarded repo the next scan sees `single_test/run_test.py` and its template findings; see [harness-doctor-delta](harness-doctor-delta.md).
- **`KeyboardInterrupt` and `SystemExit` are not caught,** so no manifest is written in those cases (`run_test.py:802`) [SOURCE-CONFIRMED by lane F].

## Sources

This section lists the files, logs and evidence this page rests on.

- [stage 6 log](../_repro/logs/stage6_integrations.log), [surface_pytest.py](../_repro/surface_pytest.py)
- [lane-f harness](../../_evidence/agent-findings/lane-f-ext/harness.md), [lane-b configuration findings §1 item 10](../../_evidence/agent-findings/lane-b-config/configuration-findings.md)
- `src/somnus_debug/test_harness/scaffold.py:62-125`, `src/somnus_debug/test_harness/templates/run_test.py:195-198`, `:486`, `:747-855`
