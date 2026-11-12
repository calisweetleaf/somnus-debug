"""Recipe C5: the project-owned execute_test() for a scaffolded run_test.py that
composes the project's real tests + doctor scan + delta.py into ONE harness run.

Install: `somnus-debug init-test-harness <repo>/single_test --no-contract`
(put it one level below the repo root: run_test.py defaults PROJECT_ROOT to
the PARENT of its own directory), then replace everything from `TEST_NAME =`
down to the `# Harness internals` banner with this file's PROJECT SURFACE
block (apply_surface.py below does exactly that, nothing else).

Env: SD_PYTHON (interpreter with somnus-debug), FIELDKIT (skill dir),
TEST_PYTHON (interpreter with pytest). Doctor runs from .somnus-debug/ so
its log stays there.
"""
# ---- PROJECT SURFACE (pasted into run_test.py) ----
SURFACE = r'''
TEST_NAME = "CALC REAL TESTS PLUS DOCTOR DELTA"


def execute_test(ctx: TestContext) -> TestOutcome:
    """Run the project's pytest suite, a doctor rescan, and delta.py as named checks."""
    profile = ctx.project_root / ".somnus-debug"
    sd_python = os.environ["SD_PYTHON"]
    fieldkit = Path(os.environ["FIELDKIT"])
    env = dict(os.environ, PYTHONPATH=str(ctx.project_root / "src"))
    tests = subprocess.run([os.environ["TEST_PYTHON"], "-m", "pytest", "-q", "tests"], cwd=ctx.project_root, env=env, text=True, capture_output=True, check=False)
    ctx.logger.info("$ pytest -q tests\nexit=%s\n%s", tests.returncode, tests.stdout + tests.stderr)
    latest_md = ctx.artifact_dir / "doctor_latest.md"
    latest_json = ctx.artifact_dir / "doctor_latest.json"
    scan = subprocess.run([sd_python, "-m", "somnus_debug.cli", "doctor", "scan", "..", "-c", "python_doctor.yaml", "-o", str(latest_md), "--json-output", str(latest_json)], cwd=profile, env=env, text=True, capture_output=True, check=False)
    ctx.logger.info("$ doctor scan\nexit=%s\n%s%s", scan.returncode, scan.stdout, scan.stderr)
    delta = subprocess.run([sys.executable, str(fieldkit / "scripts" / "delta.py"), str(profile / "runs" / "baseline.json"), str(latest_json), "--dispositions", str(profile / "dispositions.json"), "--json"], text=True, capture_output=True, check=False)
    ctx.logger.info("$ delta.py --json\nexit=%s\n%s%s", delta.returncode, delta.stdout, delta.stderr)
    verdict = json.loads(delta.stdout) if delta.stdout.strip().startswith("{") else {}
    summary = json.loads(latest_json.read_text(encoding="utf-8"))["summary"] if latest_json.exists() else {}
    return TestOutcome(
        summary="Project tests, doctor rescan, and baseline delta in one run.",
        checks=[
            Check("project-tests-pass", tests.returncode == 0, expected=0, observed=tests.returncode),
            Check("doctor-ran", scan.returncode < 4 and summary.get("files_scanned", 0) > 0, expected="exit<4 and files>0", observed={"exit": scan.returncode, "files": summary.get("files_scanned")}),
            Check("no-new-serious-findings", delta.returncode == 0, expected=0, observed={"exit": delta.returncode, "regressions": verdict.get("regressions")}),
        ],
        metrics={"doctor_exit_raw": scan.returncode, "production_score": summary.get("production_score"), "total_issues": summary.get("total_issues")},
        evidence={"delta": verdict, "doctor_report": str(latest_md)},
    )

'''

if __name__ == "__main__":
    import re
    import sys
    from pathlib import Path

    target = Path(sys.argv[1])
    text = target.read_text(encoding="utf-8")
    start = text.index('TEST_NAME = "')
    end = text.index("# ============================================================================\n# Harness internals")
    target.write_text(text[:start] + SURFACE.lstrip("\n") + "\n" + text[end:], encoding="utf-8")
    print(f"surface applied to {target}")
