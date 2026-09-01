#!/usr/bin/env python3
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

Copy this directory into a repository, edit the PROJECT-SPECIFIC TEST SURFACE,
and keep the artifact machinery boring.

No pytest, Ruff, lint, typecheck, CI, hash, benchmark, coverage, or other gate
is implied. A project may deliberately invoke any of those *inside its one
test* when they are part of that project's acceptance contract.

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
import json
import logging
import os
import platform
import sys
import time
import traceback
import uuid
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping, Sequence

# --- Common in execute_test() — remove if unused in your project ---
import hashlib
import shutil
import sqlite3
import subprocess
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
# Configuration (environment variables):
#   PROJECT_ROOT           — override the inferred repository root
#                            (default: two levels above this file)
#   SINGLE_TEST_OUTPUT_DIR — override the artifact output directory
#                            (default: <project_root>/test-runs/)
# ============================================================================

TEST_NAME = "GOLDEN PATH LAYER 1 DATA HIGHWAY RESTORATION"


def execute_test(ctx: TestContext) -> TestOutcome:
    """
    Execute ONE meaningful project/package validation.

    Replace this function in the target repository.
    Use _run_command() from harness internals for subprocess invocation.

    # TODO: Replace the implementation below with your project's test.
    # Everything after this docstring is specific to gp-cli / Golden Path.

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
    """
    metadata = json.loads(
        _run_command(
            ["cargo", "metadata", "--no-deps", "--format-version", "1", "--locked"],
            cwd=ctx.project_root,
            logger=ctx.logger,
        ).stdout
    )
    _run_command(
        ["cargo", "build", "-p", "gp-cli", "--release", "--locked"],
        cwd=ctx.project_root,
        logger=ctx.logger,
    )
    gp = Path(metadata["target_directory"]) / "release" / "gp"
    if not gp.is_file():
        raise FileNotFoundError(f"built gp binary is missing at {gp}")

    def digest(path: Path) -> str:
        return hashlib.sha256(path.read_bytes()).hexdigest()

    with tempfile.TemporaryDirectory(prefix="gp-layer1-") as temp:
        workspace = Path(temp) / "workspace"
        workspace.mkdir()
        _run_command([str(gp), "-w", str(workspace), "demo"], cwd=ctx.project_root, logger=ctx.logger)

        fabric = workspace / ".gp"
        expected_paths = {
            "major": fabric / "major.db",
            "tooling": fabric / "minor" / "tooling.db",
            "rejects": fabric / "minor" / "rejects.db",
            "telemetry": fabric / "minor" / "telemetry.db",
        }
        physical_layout = all(path.is_file() for path in expected_paths.values())

        major = sqlite3.connect(f"file:{expected_paths['major']}?mode=ro", uri=True)
        try:
            mounts = {
                role: (path, schema_kind, status)
                for role, path, schema_kind, status in major.execute(
                    "SELECT role,path,schema_kind,status FROM mounts"
                )
            }
            event_hashes = major.execute(
                "SELECT prev_hash,event_hash FROM events ORDER BY seq"
            ).fetchall()
            state_hashes = major.execute(
                "SELECT state_hash FROM committed_states ORDER BY session_id,state_seq"
            ).fetchall()
            event_lanes = dict(
                major.execute("SELECT lane,COUNT(*) FROM events GROUP BY lane").fetchall()
            )
        finally:
            major.close()

        expected_mounts = {
            role: (f"minor/{role}.db", "gp-minor/1", "active")
            for role in ("tooling", "rejects", "telemetry")
        }
        mount_contract = mounts == expected_mounts
        distinct_chains = bool(event_hashes and state_hashes) and (
            event_hashes[-1][1] != state_hashes[-1][0]
        )

        before_verify = {name: digest(path) for name, path in expected_paths.items()}
        verified = _run_command(
            [str(gp), "-w", str(workspace), "--json", "verify"],
            cwd=ctx.project_root,
            logger=ctx.logger,
        )
        verify_report = json.loads(verified.stdout)
        after_verify = {name: digest(path) for name, path in expected_paths.items()}
        readonly_verify = before_verify == after_verify

        damaged = Path(temp) / "missing-minor"
        shutil.copytree(workspace, damaged)
        missing_telemetry = damaged / ".gp" / "minor" / "telemetry.db"
        missing_telemetry.unlink()
        damaged_verify = _run_command(
            [str(gp), "-w", str(damaged), "--json", "verify"],
            cwd=ctx.project_root,
            logger=ctx.logger,
            expected=2,
        )
        damaged_report = json.loads(damaged_verify.stdout)
        missing_reported = any(
            issue.get("check") == "minor_database"
            and issue.get("subject") == "telemetry"
            for issue in damaged_report.get("issues", [])
        )
        verify_did_not_recreate = not missing_telemetry.exists()

        reopen = subprocess.run(
            [str(gp), "-w", str(damaged), "status"],
            cwd=ctx.project_root,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            check=False,
        )
        ctx.logger.info("$ gp damaged status\nexit=%s\n%s", reopen.returncode, reopen.stdout)
        reopen_failed_loud = (
            reopen.returncode != 0
            and "mounted minor ledger" in reopen.stdout
            and not missing_telemetry.exists()
        )

        damaged_schema = Path(temp) / "missing-minor-schema"
        shutil.copytree(workspace, damaged_schema)
        damaged_tooling = damaged_schema / ".gp" / "minor" / "tooling.db"
        tooling = sqlite3.connect(damaged_tooling)
        try:
            tooling.execute("DROP TABLE tool_calls")
            tooling.commit()
        finally:
            tooling.close()
        schema_verify = _run_command(
            [str(gp), "-w", str(damaged_schema), "--json", "verify"],
            cwd=ctx.project_root,
            logger=ctx.logger,
            expected=2,
        )
        schema_report = json.loads(schema_verify.stdout)
        missing_schema_reported = any(
            issue.get("check") == "minor_schema"
            and issue.get("subject") == "tooling"
            and "tool_calls" in issue.get("detail", "")
            for issue in schema_report.get("issues", [])
        )
        schema_reopen = subprocess.run(
            [str(gp), "-w", str(damaged_schema), "status"],
            cwd=ctx.project_root,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            check=False,
        )
        ctx.logger.info(
            "$ gp missing-schema status\nexit=%s\n%s",
            schema_reopen.returncode,
            schema_reopen.stdout,
        )
        tooling = sqlite3.connect(f"file:{damaged_tooling}?mode=ro", uri=True)
        try:
            schema_healed = bool(
                tooling.execute(
                    "SELECT EXISTS(SELECT 1 FROM sqlite_master "
                    "WHERE type='table' AND name='tool_calls')"
                ).fetchone()[0]
            )
        finally:
            tooling.close()
        schema_reopen_failed_loud = (
            schema_reopen.returncode != 0
            and "missing required table" in schema_reopen.stdout
        )

        checks = [
            Check(
                "physical-four-database-layout",
                physical_layout,
                expected=list(str(path) for path in expected_paths.values()),
                observed={name: path.is_file() for name, path in expected_paths.items()},
            ),
            Check(
                "built-in-minor-mount-contract",
                mount_contract,
                expected=expected_mounts,
                observed=mounts,
            ),
            Check(
                "separate-event-and-state-chains",
                distinct_chains,
                expected="non-empty distinct event and committed-state chain heads",
                observed={
                    "event_rows": len(event_hashes),
                    "state_rows": len(state_hashes),
                    "event_head": event_hashes[-1][1] if event_hashes else None,
                    "state_head": state_hashes[-1][0] if state_hashes else None,
                },
            ),
            Check(
                "workspace-fsck-passes",
                verify_report.get("issues") == [],
                expected={"issues": []},
                observed=verify_report,
            ),
            Check(
                "workspace-fsck-is-read-only",
                readonly_verify,
                expected=before_verify,
                observed=after_verify,
            ),
            Check(
                "missing-minor-is-verifier-visible",
                missing_reported,
                expected="minor_database issue for telemetry",
                observed=damaged_report.get("issues"),
            ),
            Check(
                "missing-minor-is-not-recreated",
                verify_did_not_recreate and reopen_failed_loud,
                expected="verify preserves absence and normal reopen fails loud",
                observed={
                    "exists_after_verify": missing_telemetry.exists(),
                    "reopen_exit": reopen.returncode,
                    "reopen_output": reopen.stdout,
                },
            ),
            Check(
                "missing-minor-schema-is-not-healed",
                missing_schema_reported
                and schema_reopen_failed_loud
                and not schema_healed,
                expected=(
                    "verify reports missing tooling table and normal reopen "
                    "fails without recreating it"
                ),
                observed={
                    "verify_issues": schema_report.get("issues"),
                    "reopen_exit": schema_reopen.returncode,
                    "reopen_output": schema_reopen.stdout,
                    "tool_calls_exists_after_reopen": schema_healed,
                },
            ),
        ]
        return TestOutcome(
            summary=(
                "The real gp CLI exercised the Layer 1 Data Highway, its exact "
                "major/minor layout, both hash chains, read-only whole-workspace "
                "fsck, and fail-loud evidence-loss boundary."
            ),
            checks=checks,
            metrics={
                "events": len(event_hashes),
                "committed_states": len(state_hashes),
                "event_lanes": event_lanes,
            },
            evidence={
                "gp_binary": str(gp),
                "verify_report": verify_report,
                "damaged_verify_report": damaged_report,
                "damaged_schema_verify_report": schema_report,
                "database_sha256_before_verify": before_verify,
                "database_sha256_after_verify": after_verify,
            },
            notes=[
                "The test uses disposable /tmp workspaces and does not exercise the out-of-scope python/ projection.",
                "The damaged copy is intentionally missing telemetry.db to prove evidence loss cannot be healed silently.",
                "A second damaged copy is intentionally missing tooling.tool_calls to prove schema loss cannot be healed silently.",
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
    expected: int = 0,
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
        expected: Expected exit code; raises RuntimeError on mismatch.
    """
    logger.info("$ %s", " ".join(command))
    completed = subprocess.run(
        command,
        cwd=cwd,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=False,
    )
    logger.info("exit=%s\n%s", completed.returncode, completed.stdout)
    if completed.returncode != expected:
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

    # Safe for repeated invocation in the same interpreter.
    for handler in list(logger.handlers):
        logger.removeHandler(handler)
        try:
            handler.close()
        except Exception:
            pass

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


def _default_output_root(project_root: Path) -> Path:
    override = os.environ.get("SINGLE_TEST_OUTPUT_DIR")
    if override:
        return Path(override).expanduser().resolve()
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


def main() -> int:
    project_root = Path(
        os.environ.get("PROJECT_ROOT", Path(__file__).resolve().parent.parent)
    ).expanduser().resolve()

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
