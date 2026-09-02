"""Smoke tests for the packaged somnus-debug CLI.

These are intentionally shallow: they prove the package installs, the
dispatcher routes to each tool, and each tool's own --help/entry point
still works after being moved under src/somnus_debug. They are not a
replacement for exercising each tool's actual diagnostic logic.
"""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent


def _run(*args: str, cwd: Path | None = None) -> subprocess.CompletedProcess[str]:
    environment = os.environ.copy()
    source_root = str(REPO_ROOT / "src")
    environment["PYTHONPATH"] = source_root + os.pathsep + environment.get("PYTHONPATH", "")
    return subprocess.run(
        [sys.executable, "-m", "somnus_debug.cli", *args],
        cwd=cwd or REPO_ROOT,
        capture_output=True,
        text=True,
        timeout=30,
        env=environment,
    )


def test_top_level_help() -> None:
    result = _run("--help")
    assert result.returncode == 0
    assert "somnus-debug" in result.stdout
    assert "doctor" in result.stdout


def test_unknown_command_exits_nonzero() -> None:
    result = _run("not-a-real-command")
    assert result.returncode == 2


def test_structure_help() -> None:
    result = _run("structure", "--help")
    assert result.returncode == 0
    assert "Index Python classes" in result.stdout


def test_doctor_help() -> None:
    result = _run("doctor", "--help")
    assert result.returncode == 0


def test_doctor_scan_degrades_when_sqlite_state_is_unavailable(tmp_path: Path) -> None:
    """Scan reports normally when the optional SQLite state database cannot open."""
    config_source = REPO_ROOT / "src" / "somnus_debug" / "doctor" / "default_config.yaml"
    config_path = tmp_path / "doctor.yaml"
    config_path.write_text(
        config_source.read_text(encoding="utf-8").replace(
            'state_dir: ".python_doctor"',
            'state_dir: "state"',
        ),
        encoding="utf-8",
    )
    state_root = tmp_path / "state"
    state_root.mkdir()
    (state_root / "state.sqlite3").mkdir()

    result = _run("doctor", "scan", str(tmp_path), "--config", str(config_path), cwd=tmp_path)

    assert result.returncode == 0
    assert "Warning: local SQLite state is unavailable" in result.stderr
    assert "Scan complete:" in result.stdout
    assert (tmp_path / "production_doctor_report.md").exists()
    assert (tmp_path / "production_doctor_report.json").exists()


def test_pycache_clean_help() -> None:
    result = _run("pycache-clean", "--help")
    assert result.returncode == 0


def test_init_test_harness_help() -> None:
    result = _run("init-test-harness", "--help")
    assert result.returncode == 0


def test_structure_self_index() -> None:
    """Run the structure indexer against its own core.py as an end-to-end check."""
    target = REPO_ROOT / "src" / "somnus_debug" / "structure" / "core.py"
    result = _run("structure", str(target))
    assert result.returncode == 0
    assert "Class Index for" in result.stdout


def test_init_test_harness_scaffolds_into_tmp(tmp_path: Path) -> None:
    result = _run("init-test-harness", str(tmp_path))
    assert result.returncode == 0
    assert (tmp_path / "run_test.py").exists()
    assert (tmp_path / "CONTRACT.md").exists()


def test_init_test_harness_refuses_overwrite_without_force(tmp_path: Path) -> None:
    (tmp_path / "run_test.py").write_text("# hand-edited, do not clobber\n", encoding="utf-8")
    result = _run("init-test-harness", str(tmp_path))
    assert result.returncode == 1
    assert "hand-edited" not in (tmp_path / "run_test.py").read_text(encoding="utf-8") or True
    # The real assertion: our template text was NOT written over the hand-edited file.
    assert (tmp_path / "run_test.py").read_text(encoding="utf-8") == "# hand-edited, do not clobber\n"
