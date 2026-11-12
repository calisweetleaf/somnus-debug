#!/usr/bin/env python3
# somnus:metadata:v2
# somnus:
#   schema: "somnus://metadata/core/2.0.0"
#   id: "urn:somnus:artifact:01a19ace-79a0-7054-9b74-e0ee36ffb16a"
#   revision: 1
#   title: "Agnostic Single-Test Harness"
#   classification:
#     category: "engineering"
#     type: "source-code"
#     role: "informative"
#     scope: "component"
#     tags: []
#   lifecycle:
#     status: "draft"
#   authority:
#     standing: "candidate"
#     scopes:
#       - target_ref: "urn:somnus:artifact:01a19ace-79a0-7054-9b74-e0ee36ffb16a"
#         aspects: ["content"]
#   time: {}
#   names:
#     slug: "agnostic-single-test-harness"
#   knowledge:
#     coverage: "artifact"
#     subjects: ["urn:somnus:artifact:01a19ace-79a0-7054-9b74-e0ee36ffb16a"]
#   access:
#     visibility: "internal"
#     allowed_uses: ["archive", "search", "reason"]
#   ingestion:
#     disposition: "candidate"
#     body_role: "source"
# somnus:end
"""
Agnostic Single-Test Harness
============================

Portable repository-local validation surface.

This file intentionally does NOT define what "correct" means for a project.
A project defines that in `execute_test()`. The harness only provides the
stable execution/artifact contract:

    one Python test
        -> actual project/package execution
        -> project-owned acceptance checks
        -> manifest.json   (machine-readable truth)
        -> report.md       (human/model-readable run summary)
        -> test.log        (raw execution truth)
        -> one final PASS/FAIL verdict

Copy this file into a repository (its root or any subdirectory; the project
root is inferred by walking up to .git / pyproject.toml / setup.cfg, or set
with PROJECT_ROOT), edit the PROJECT-SPECIFIC TEST SURFACE, and keep the
artifact machinery boring. `python run_test.py --help` lists the settings.

No pytest, Ruff, lint, typecheck, CI, hash, benchmark, coverage, or other gate
is implied. A project may deliberately invoke any of those *inside its one
test* when they are part of that project's acceptance contract. The shipped
execute_test() (the project's pytest suite if it has one, else a byte-compile
of its Python files) is only a runnable starting point for that one test, not
a gate the harness imposes.

The harness is independent of Accelerate, Somnus-C, any agent framework, and
any repository continuity system.

The purpose of this harness is not to optimize for `test = pass`. It is
intentionally engineered to expose what actually happens when the project
runs.

Daeron's engineering standards are unusually strict because generated code is
expected to match the depth, structure, behavior, and failure semantics of the
surrounding repository rather than merely satisfy a narrow test condition.
This is not an aspirational standard or a substitute for hands-on experience:
it comes from more than 7,200 verified logged hours of personal development
across roughly 75 projects from January 2025 through August 2026, spanning
modern ML, model architecture, inference, training systems, recursive systems,
orchestration, memory, compression, runtime design, and adjacent
infrastructure. Current work is often delegated through coding agents or
developed conversationally, but that delegation sits on top of a large body of
direct implementation experience. Do not reinterpret "vibe coding" here as
permission to simplify, normalize, or lower the implementation standard.

This context matters because coding agents are strongly biased toward making
software look conventionally healthy: adding defensive fallbacks, silent
recovery, stubs, substitute implementations, monkey patches, simplified code
paths, excessive validation gates, hashes, linting, static checks, CI-style
ceremony, or other mechanisms that produce clean signals without proving that
the intended system actually behaved correctly. Those patterns are often
reasonable elsewhere. They are not the default here.

The governing rule is architectural fidelity over superficial completion. No
silent fallbacks. No hidden degradation. No placeholder implementations. No
substitute behavior. No "temporary" monkey patches that become permanent. No
simplifying a difficult subsystem merely to make a test green. If a file
requires several hours of class-by-class repair to make its real execution
correct, that is preferable to rapidly producing a superficially complete
implementation.

Accordingly, this harness is not primarily a developer-gate surface. It is
closer to a controlled beta run. The useful evidence is the execution itself:
what was invoked, which paths were taken, what state changed, what the system
emitted, what it logged, what the terminal showed, where execution diverged
from intent, and what the project actually looked like while operating.

Compilation, imports, exceptions, and hard failures still matter, but they do
not need to be elevated into a forest of separate gates. Under these code
standards, meaningful defects should surface naturally during real execution.
A broken system should break visibly. A correct system should demonstrate
itself through behavior.

Prefer rich runtime evidence over binary ceremony. Do not turn this harness
into hash porn, lint porn, CI theater, or a generic validation framework.
Daeron already maintains separate tools for those concerns. This file exists
to answer a narrower and more valuable question:

    What actually happened when the real project ran?
"""

from __future__ import annotations

# --- Harness internals (do not remove) ---
import argparse
import json
import logging
import os
import platform
import subprocess
import sys
import time
import traceback
import uuid
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping, Sequence

# --- Used by the shipped execute_test() — remove if unused in your project ---
import tempfile


# ============================================================================
# Stable harness types
# ============================================================================

@dataclass(frozen=True)
class Check:
    """One package-owned acceptance condition."""

    name: str
    passed: bool
    detail: str = ""
    expected: Any = None
    observed: Any = None


@dataclass
class TestOutcome:
    """
    Structured result returned by the project-specific test.

    `checks` determine PASS/FAIL. `metrics` and `evidence` record what happened
    without themselves becoming acceptance criteria.
    """

    summary: str
    checks: list[Check]
    metrics: dict[str, Any] = field(default_factory=dict)
    evidence: dict[str, Any] = field(default_factory=dict)
    notes: list[str] = field(default_factory=list)

    @property
    def passed(self) -> bool:
        """True only when at least one check exists and every check passed."""
        return bool(self.checks) and all(check.passed for check in self.checks)


@dataclass(frozen=True)
class TestContext:
    """Runtime context supplied to the project-specific test."""

    run_id: str
    project_root: Path
    artifact_dir: Path
    logger: logging.Logger


# ============================================================================
# PROJECT-SPECIFIC TEST SURFACE
# Edit this section when installing the harness into a repository.
#
# The shipped execute_test() is a generic, runnable starting point: it runs
# the project's pytest suite when the project has one, otherwise it
# byte-compiles every Python file under the project root. Replace it with the
# one test that exercises the real boundary your project means to prove.
#
# Configuration (environment variables; see `python run_test.py --help`):
#   PROJECT_ROOT           — override the inferred project root. Default: the
#                            nearest directory, starting at this file's own
#                            directory and walking up, that contains .git,
#                            pyproject.toml or setup.cfg; else this file's
#                            directory.
#   SINGLE_TEST_OUTPUT_DIR — override the artifact output directory. Default:
#                            <project_root>/test-runs/. A relative value is
#                            resolved against the project root.
# ============================================================================

TEST_NAME = "PROJECT TEST SUITE"

# Directories never byte-compiled by the fallback check (virtualenvs, VCS and
# tool caches, vendored trees). Matched against paths relative to the root.
_COMPILE_EXCLUDE = (
    r"(^|[/\\])(\.git|\.hg|\.svn|\.venv|venv|\.tox|\.nox|node_modules|"
    r"site-packages|__pypackages__|test-runs)([/\\]|$)"
)


def _pytest_signal(project_root: Path) -> str | None:
    """Return why the project looks pytest-driven, or None if it does not."""
    if (project_root / "tests").is_dir():
        return "tests/ directory"
    if (project_root / "pytest.ini").is_file():
        return "pytest.ini"
    if (project_root / "conftest.py").is_file():
        return "conftest.py"
    for name, marker in (
        ("pyproject.toml", "[tool.pytest.ini_options]"),
        ("setup.cfg", "[tool:pytest]"),
        ("tox.ini", "[pytest]"),
    ):
        path = project_root / name
        if path.is_file() and marker in path.read_text(encoding="utf-8", errors="replace"):
            return f"{marker} in {name}"
    return None


def execute_test(ctx: TestContext) -> TestOutcome:
    """
    Execute ONE meaningful project/package validation.

    Replace this function in the target repository.
    Use _run_command() from harness internals for subprocess invocation.

    Requirements:
      1. Exercise the real boundary the project means to prove.
      2. Return explicit acceptance checks.
      3. Put measurements in `metrics`, not in PASS/FAIL unless the project
         explicitly defines a threshold.
      4. Put useful structured observations in `evidence`.
      5. Do not fan out into unrelated "good practice" checks.

    Example shape:

        result = package.do_real_thing(...)
        return TestOutcome(
            summary="Native package path completed.",
            checks=[
                Check(
                    name="expected-result",
                    passed=result.value == 42,
                    expected=42,
                    observed=result.value,
                ),
            ],
            metrics={"elapsed_ms": result.elapsed_ms},
            evidence={"trace_length": len(result.trace)},
        )

    Shipped default: if the project has a pytest suite (a tests/ directory or
    pytest configuration), run `python -m pytest -q` in the project root and
    require exit 0. Otherwise run `python -m compileall -q` over the project
    (virtualenvs and tool directories excluded) with bytecode redirected to a
    temporary directory, so the repository is not written to, and require
    exit 0.
    """
    reason = _pytest_signal(ctx.project_root)
    with tempfile.TemporaryDirectory(prefix="single-test-pycache-") as pycache_prefix:
        if reason is not None:
            mode = "pytest"
            command = [sys.executable, "-m", "pytest", "-q"]
            check_name = "project-pytest-suite-passes"
        else:
            mode = "compileall"
            reason = "no pytest suite detected"
            command = [sys.executable, "-m", "compileall", "-q", "-x", _COMPILE_EXCLUDE, "."]
            check_name = "project-python-files-compile"
        env = dict(os.environ, PYTHONPYCACHEPREFIX=pycache_prefix)
        started = time.perf_counter()
        completed = _run_command(
            command, cwd=ctx.project_root, logger=ctx.logger, expected=None, env=env
        )
        elapsed_s = time.perf_counter() - started

    output_lines = completed.stdout.splitlines()
    return TestOutcome(
        summary=(
            f"Ran `{' '.join(command[1:])}` in {ctx.project_root} "
            f"({reason}); exit code {completed.returncode}."
        ),
        checks=[
            Check(
                name=check_name,
                passed=completed.returncode == 0,
                detail=f"{mode} selected because: {reason}",
                expected=0,
                observed=completed.returncode,
            ),
        ],
        metrics={"command_elapsed_s": round(elapsed_s, 6), "output_lines": len(output_lines)},
        evidence={
            "mode": mode,
            "selection_reason": reason,
            "command": command,
            "cwd": str(ctx.project_root),
            "output_tail": output_lines[-40:],
        },
        notes=[
            "This is the template's generic default test; replace execute_test() "
            "with the project's real boundary test.",
            "Full command output is in test.log.",
        ],
    )


# ============================================================================
# Harness internals
# ============================================================================

SCHEMA_VERSION = "1.0"


def _run_command(
    command: list[str],
    *,
    cwd: Path,
    logger: logging.Logger,
    expected: int | None = 0,
    env: Mapping[str, str] | None = None,
) -> subprocess.CompletedProcess[str]:
    """
    Run a subprocess, log the invocation and output, and raise on unexpected exit.

    Available to execute_test() as a first-class harness utility. Replaces the
    pattern of defining a local `run()` closure inside execute_test() — pull it
    out so sub-helpers inside complex tests can reach it too.

    Args:
        command:  Argv list passed to subprocess.run.
        cwd:      Working directory for the process (typically ctx.project_root).
        logger:   Logger to record the command and its output.
        expected: Expected exit code; raises RuntimeError on mismatch. Pass
                  None to return the result whatever the exit code (the
                  caller then records it as a Check).
        env:      Environment for the process (default: inherit).
    """
    logger.info("$ %s", " ".join(command))
    completed = subprocess.run(
        command,
        cwd=cwd,
        env=None if env is None else dict(env),
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=False,
    )
    logger.info("exit=%s\n%s", completed.returncode, completed.stdout)
    if expected is not None and completed.returncode != expected:
        raise RuntimeError(
            f"command exited {completed.returncode}, expected {expected}: "
            f"{' '.join(command)}\n{completed.stdout}"
        )
    return completed


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _slug(value: str) -> str:
    cleaned = "".join(c.lower() if c.isalnum() else "-" for c in value).strip("-")
    while "--" in cleaned:
        cleaned = cleaned.replace("--", "-")
    return cleaned or "test"


def _json_safe(value: Any) -> Any:
    """Recursively convert common values to JSON-safe representations."""
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    if isinstance(value, Path):
        return str(value)
    if isinstance(value, Mapping):
        return {str(k): _json_safe(v) for k, v in value.items()}
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        return [_json_safe(v) for v in value]
    return str(value)


def _setup_logger(log_file: Path) -> logging.Logger:
    logger = logging.getLogger("agnostic.single_test")
    logger.setLevel(logging.DEBUG)
    logger.propagate = False

    # Safe for repeated invocation in the same interpreter. A handler from an
    # earlier run that cannot be closed is a real fault and is not swallowed.
    for handler in list(logger.handlers):
        logger.removeHandler(handler)
        handler.close()

    file_handler = logging.FileHandler(log_file, mode="w", encoding="utf-8")
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(
        logging.Formatter(
            "%(asctime)s %(levelname)-8s [%(name)s] %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
    )

    # stderr = human-readable progress; stdout = machine-parseable final JSON.
    # This keeps the two streams separable when running as a subprocess.
    console_handler = logging.StreamHandler(sys.stderr)
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(
        logging.Formatter("%(asctime)s %(levelname)-8s %(message)s", datefmt="%H:%M:%S")
    )

    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    return logger


_ROOT_MARKERS = (".git", "pyproject.toml", "setup.cfg")


def _infer_project_root(runner: Path) -> Path:
    """
    Resolve the project root for this run.

    $PROJECT_ROOT wins. Otherwise walk up from the directory holding this file
    to the first directory containing .git, pyproject.toml or setup.cfg, so the
    harness works both at the repository root and in a subdirectory of it;
    with no marker anywhere, use this file's own directory.
    """
    override = os.environ.get("PROJECT_ROOT")
    if override:
        return Path(override).expanduser().resolve()
    start = runner.resolve().parent
    for candidate in (start, *start.parents):
        if any((candidate / marker).exists() for marker in _ROOT_MARKERS):
            return candidate
    return start


def _default_output_root(project_root: Path) -> Path:
    """Artifact root: $SINGLE_TEST_OUTPUT_DIR (relative = under the project root) or <root>/test-runs."""
    override = os.environ.get("SINGLE_TEST_OUTPUT_DIR")
    if override:
        return (project_root / Path(override).expanduser()).resolve()
    return project_root / "test-runs"


def _build_manifest(
    *,
    ctx: TestContext,
    started_at: datetime,
    finished_at: datetime,
    elapsed_s: float,
    outcome: TestOutcome | None,
    error: dict[str, Any] | None,
) -> dict[str, Any]:
    verdict = "PASS" if outcome is not None and outcome.passed and error is None else "FAIL"

    checks = []
    if outcome is not None:
        checks = [_json_safe(asdict(check)) for check in outcome.checks]

    return {
        "schema_version": SCHEMA_VERSION,
        "run_id": ctx.run_id,
        "test_name": TEST_NAME,
        "verdict": verdict,
        "started_at_utc": started_at.isoformat(),
        "finished_at_utc": finished_at.isoformat(),
        "elapsed_s": round(elapsed_s, 6),
        "environment": {
            "python": sys.version,
            "python_executable": sys.executable,
            "platform": platform.platform(),
            "cwd": str(Path.cwd()),
            "project_root": str(ctx.project_root),
            "runner": str(Path(__file__).resolve()),
        },
        "acceptance": {
            "total_checks": len(checks),
            "passed_checks": sum(1 for c in checks if c.get("passed") is True),
            "failed_checks": sum(1 for c in checks if c.get("passed") is False),
            "checks": checks,
        },
        "result": {
            "summary": outcome.summary if outcome else None,
            "metrics": _json_safe(outcome.metrics) if outcome else {},
            "evidence": _json_safe(outcome.evidence) if outcome else {},
            "notes": _json_safe(outcome.notes) if outcome else [],
        },
        "error": _json_safe(error),
        "artifacts": {
            "manifest": "manifest.json",
            "report": "report.md",
            "log": "test.log",
        },
    }


def _render_report(manifest: Mapping[str, Any]) -> str:
    """
    Produce a factual Markdown run summary.

    This report is intentionally conservative. An agent/operator may extend it
    after consuming both manifest.json and test.log, but interpretation must not
    rewrite the machine verdict or hide failed checks.
    """
    verdict = manifest["verdict"]
    acceptance = manifest["acceptance"]
    result = manifest["result"]
    error = manifest.get("error")

    lines = [
        f"# {manifest['test_name']} — {verdict}",
        "",
        f"**Run ID:** `{manifest['run_id']}`  ",
        f"**Started:** {manifest['started_at_utc']}  ",
        f"**Finished:** {manifest['finished_at_utc']}  ",
        f"**Elapsed:** {manifest['elapsed_s']:.6f}s  ",
        f"**Verdict:** **{verdict}**",
        "",
        "## Test Result",
        "",
        result.get("summary") or "No summary was returned.",
        "",
        "## Acceptance Checks",
        "",
    ]

    checks = acceptance.get("checks", [])
    if checks:
        lines += [
            "| Check | Result | Expected | Observed | Detail |",
            "|---|---:|---|---|---|",
        ]
        for check in checks:
            expected = json.dumps(check.get("expected"), default=str)
            observed = json.dumps(check.get("observed"), default=str)
            detail = str(check.get("detail") or "").replace("|", "\\|")
            status = "PASS" if check.get("passed") else "FAIL"
            lines.append(
                f"| {check.get('name')} | **{status}** | `{expected}` | `{observed}` | {detail} |"
            )
    else:
        lines.append("No acceptance checks were returned.")

    metrics = result.get("metrics") or {}
    lines += ["", "## Measurements", ""]
    if metrics:
        lines.append("```json")
        lines.append(json.dumps(metrics, indent=2, default=str))
        lines.append("```")
    else:
        lines.append("No measurements recorded.")

    evidence = result.get("evidence") or {}
    lines += ["", "## Structured Evidence", ""]
    if evidence:
        lines.append("```json")
        lines.append(json.dumps(evidence, indent=2, default=str))
        lines.append("```")
    else:
        lines.append("No structured evidence recorded.")

    notes = result.get("notes") or []
    if notes:
        lines += ["", "## Notes", ""]
        for note in notes:
            lines.append(f"- {note}")

    if error:
        lines += [
            "",
            "## Execution Failure",
            "",
            f"**Type:** `{error.get('type', 'Unknown')}`",
            "",
            f"**Message:** {error.get('message', '')}",
            "",
            "```text",
            error.get("traceback", ""),
            "```",
        ]

    lines += [
        "",
        "## Artifact Roles",
        "",
        "- `manifest.json` — machine-readable run truth and final verdict.",
        "- `report.md` — human/model-readable interpretation surface.",
        "- `test.log` — raw execution/logging surface for diagnosis.",
        "",
        "The report may explain the manifest; it must not silently override it.",
        "",
    ]
    return "\n".join(lines)


_USAGE_EPILOG = """\
Runs the single project test defined in execute_test() and writes
manifest.json, report.md and test.log into a fresh per-run directory.
Exit status: 0 when the verdict is PASS, 1 when it is FAIL.

environment variables:
  PROJECT_ROOT            project root; default: nearest directory at or above
                          this file containing .git, pyproject.toml or
                          setup.cfg, else this file's directory
  SINGLE_TEST_OUTPUT_DIR  artifact root; default: <project_root>/test-runs;
                          relative values resolve against the project root
"""


def _parse_args(argv: Sequence[str] | None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog=Path(__file__).name,
        description=f"Agnostic single-test harness: {TEST_NAME}",
        epilog=_USAGE_EPILOG,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    """Run the project test once, write the three artifacts, return 0 on PASS else 1."""
    _parse_args(argv)
    project_root = _infer_project_root(Path(__file__))

    started_at = _utc_now()
    run_id = (
        f"{_slug(TEST_NAME).upper()}-"
        f"{started_at.strftime('%Y%m%d-%H%M%S')}-"
        f"{uuid.uuid4().hex[:6]}"
    )

    artifact_dir = _default_output_root(project_root) / run_id
    artifact_dir.mkdir(parents=True, exist_ok=False)

    log_file = artifact_dir / "test.log"
    manifest_file = artifact_dir / "manifest.json"
    report_file = artifact_dir / "report.md"

    logger = _setup_logger(log_file)
    ctx = TestContext(
        run_id=run_id,
        project_root=project_root,
        artifact_dir=artifact_dir,
        logger=logger,
    )

    logger.info("=" * 72)
    logger.info("%s", TEST_NAME)
    logger.info("Run ID: %s", run_id)
    logger.info("Artifacts: %s", artifact_dir)
    logger.info("=" * 72)

    t0 = time.perf_counter()
    outcome: TestOutcome | None = None
    error: dict[str, Any] | None = None

    try:
        outcome = execute_test(ctx)
        if not isinstance(outcome, TestOutcome):
            raise TypeError(
                f"execute_test() must return TestOutcome, got {type(outcome).__name__}"
            )
        if not outcome.checks:
            raise ValueError(
                "execute_test() returned no acceptance checks; an empty test cannot PASS."
            )

        for check in outcome.checks:
            logger.info(
                "[%s] %s%s",
                "PASS" if check.passed else "FAIL",
                check.name,
                f" — {check.detail}" if check.detail else "",
            )
    except Exception as exc:
        error = {
            "type": type(exc).__name__,
            "message": str(exc),
            "traceback": traceback.format_exc(),
        }
        logger.exception("Test execution failed")

    elapsed_s = time.perf_counter() - t0
    finished_at = _utc_now()

    manifest = _build_manifest(
        ctx=ctx,
        started_at=started_at,
        finished_at=finished_at,
        elapsed_s=elapsed_s,
        outcome=outcome,
        error=error,
    )

    manifest_file.write_text(
        json.dumps(manifest, indent=2, sort_keys=False, ensure_ascii=False, default=str)
        + "\n",
        encoding="utf-8",
    )
    report_file.write_text(_render_report(manifest), encoding="utf-8")

    verdict = manifest["verdict"]
    logger.info("=" * 72)
    logger.info("FINAL VERDICT: %s", verdict)
    logger.info("manifest.json: %s", manifest_file)
    logger.info("report.md:     %s", report_file)
    logger.info("test.log:      %s", log_file)
    logger.info("=" * 72)

    print()
    print(
        json.dumps(
            {
                "run_id": run_id,
                "test_name": TEST_NAME,
                "verdict": verdict,
                "elapsed_s": manifest["elapsed_s"],
                "artifacts": {
                    "manifest": str(manifest_file),
                    "report": str(report_file),
                    "log": str(log_file),
                },
            },
            indent=2,
        )
    )

    return 0 if verdict == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
