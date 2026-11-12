"""Replace a scaffolded run_test.py's project surface with a pytest-only execute_test().

Usage: surface_pytest.py <path/to/run_test.py>
Replaces everything from `TEST_NAME = "` down to the `# Harness internals` banner.
"""
import sys
from pathlib import Path

SURFACE = '''TEST_NAME = "INVENTORY UNIT TESTS"


def execute_test(ctx: TestContext) -> TestOutcome:
    """Run the project's pytest suite once and turn its exit code into a check."""
    env = dict(os.environ, PYTHONPATH=str(ctx.project_root / "src"))
    proc = subprocess.run([sys.executable, "-m", "pytest", "-q", "tests"], cwd=ctx.project_root,
                          env=env, text=True, capture_output=True, check=False)
    ctx.logger.info("$ pytest -q tests\\nexit=%s\\n%s", proc.returncode, proc.stdout + proc.stderr)
    (ctx.artifact_dir / "pytest.txt").write_text(proc.stdout + proc.stderr, encoding="utf-8")
    return TestOutcome(
        summary="Project unit tests via pytest.",
        checks=[Check("pytest-exit-zero", proc.returncode == 0, expected=0, observed=proc.returncode)],
        metrics={"pytest_tail": proc.stdout.strip().splitlines()[-1] if proc.stdout.strip() else ""},
    )


'''
target = Path(sys.argv[1])
text = target.read_text(encoding="utf-8")
start = text.index('TEST_NAME = "')
end = text.index("# ============================================================================\n# Harness internals")
target.write_text(text[:start] + SURFACE + text[end:], encoding="utf-8")
print(f"surface applied to {target}")
