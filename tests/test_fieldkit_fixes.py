"""Regression tests for the somnus-debug-fieldkit scripts (onboard.py, delta.py, selftest.py).

The fieldkit scripts are standalone files, not a package, so each test loads
them with importlib (unit level) or runs them as subprocesses (contract level).
Every fixture lives under pytest's tmp_path.
"""

from __future__ import annotations

import importlib.util
import json
import os
import subprocess
import sys
import sysconfig
from pathlib import Path
from types import ModuleType

REPO_ROOT = Path(__file__).resolve().parents[1]
SRC = REPO_ROOT / "src"
SCRIPTS = REPO_ROOT / "skills" / "somnus-debug-fieldkit" / "scripts"


def load_script(name: str) -> ModuleType:
    """Import a fieldkit script by path under a private module name."""
    spec = importlib.util.spec_from_file_location(f"fieldkit_{name}", SCRIPTS / f"{name}.py")
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def env_with_src() -> dict[str, str]:
    """Process environment where any interpreter can import the worktree's somnus_debug."""
    env = os.environ.copy()
    env["PYTHONPATH"] = str(SRC) + (os.pathsep + env["PYTHONPATH"] if env.get("PYTHONPATH") else "")
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    return env


def env_without_pythonpath() -> dict[str, str]:
    """Process environment with PYTHONPATH removed."""
    env = os.environ.copy()
    env.pop("PYTHONPATH", None)
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    return env


def run_script(name: str, *args: str, cwd: Path, env: dict[str, str] | None = None) -> subprocess.CompletedProcess[str]:
    """Run a fieldkit script with the test interpreter."""
    return subprocess.run(
        [sys.executable, str(SCRIPTS / f"{name}.py"), *args],
        cwd=cwd, capture_output=True, text=True, timeout=300, check=False, env=env if env is not None else env_with_src(),
    )


def make_symlinked_venv(base: Path) -> Path:
    """Build a minimal venv whose bin/python is a symlink and whose site-packages can import somnus_debug.

    Only the venv (via a .pth file in its own site-packages) can import somnus_debug;
    the base interpreter the symlink points to cannot. That is the layout that
    exposed onboard's ``--python`` .resolve() bug.
    """
    real = Path(os.path.realpath(sys.executable))
    (base / "bin").mkdir(parents=True)
    python = base / "bin" / "python"
    python.symlink_to(real)
    (base / "pyvenv.cfg").write_text(f"home = {real.parent}\ninclude-system-site-packages = false\n", encoding="utf-8")
    purelib = Path(sysconfig.get_path("purelib", vars={"base": str(base), "platbase": str(base)}))
    purelib.mkdir(parents=True)
    (purelib / "somnus_debug_src.pth").write_text(str(SRC) + "\n", encoding="utf-8")
    return python


def small_project(root: Path) -> Path:
    """Create a tiny flat project with one documented module."""
    (root / "pkg").mkdir(parents=True)
    (root / "pkg" / "__init__.py").write_text('"""Package docstring long enough here."""\n', encoding="utf-8")
    (root / "pkg" / "core.py").write_text(
        '"""Core module docstring long enough."""\n\n\ndef add(a: int, b: int) -> int:\n'
        '    """Add two integers together."""\n    total = a + b\n    if total < 0:\n        total = 0\n'
        '    checked = int(total)\n    return checked\n',
        encoding="utf-8",
    )
    return root


# --- T-30 (D-20): --python keeps the venv symlink; a missing path is a clean exit 3 -------------


def test_onboard_python_keeps_symlinked_venv_interpreter(tmp_path: Path) -> None:
    """A normal (symlinked) venv interpreter is accepted and used as given."""
    python = make_symlinked_venv(tmp_path / "venv")
    env = env_without_pythonpath()
    probe = subprocess.run([str(python), "-c", "import somnus_debug"], capture_output=True, env=env, check=False)
    base_probe = subprocess.run([os.path.realpath(python), "-c", "import somnus_debug"], capture_output=True, env=env, check=False)
    assert probe.returncode == 0 and base_probe.returncode != 0, "fixture must make only the venv able to import somnus_debug"

    repo = small_project(tmp_path / "repo")
    proc = run_script("onboard", str(repo), "--python", str(python), cwd=tmp_path, env=env)
    assert proc.returncode == 0, proc.stdout + proc.stderr
    assert "BLOCKED" not in proc.stdout
    assert f"{python} (--python)" in proc.stdout


def test_onboard_python_nonexistent_path_exits_3_without_traceback(tmp_path: Path) -> None:
    """A --python path that does not exist is reported, not a crash."""
    repo = small_project(tmp_path / "repo")
    proc = run_script("onboard", str(repo), "--python", str(tmp_path / "nope" / "python"), cwd=tmp_path)
    assert proc.returncode == 3, proc.stdout + proc.stderr
    assert "Traceback" not in proc.stderr
    assert "no such interpreter" in proc.stdout


# --- T-31 (D-20): a broken doctor config is exit 2 with one line, never a traceback -------------


def doctor_default_config(path: Path) -> str:
    """Return the CLI's own init-config text, written to ``path``."""
    subprocess.run([sys.executable, "-m", "somnus_debug.cli", "doctor", "init-config", "-o", str(path)],
                   cwd=path.parent, capture_output=True, text=True, check=True, timeout=60, env=env_with_src())
    return path.read_text(encoding="utf-8")


def test_onboard_broken_doctor_config_exits_2_one_line(tmp_path: Path) -> None:
    """An adopted root config that doctor rejects ends onboarding with exit 2 and a one-line error."""
    repo = small_project(tmp_path / "repo")
    cfg = repo / "python_doctor.yaml"
    text = doctor_default_config(cfg)
    assert 'severity_exit_level: "serious"' in text
    cfg.write_text(text.replace('severity_exit_level: "serious"', 'severity_exit_level: "bogus"'), encoding="utf-8")
    proc = run_script("onboard", str(repo), "--python", sys.executable, cwd=tmp_path)
    assert proc.returncode == 2, proc.stdout + proc.stderr
    assert "Traceback" not in proc.stderr
    errors = [line for line in proc.stderr.splitlines() if line.strip()]
    assert len(errors) == 1 and errors[0].startswith("error: doctor scan with"), proc.stderr


# --- T-32 (D-20): no PROFILE.md without a passing scan; plan mode never writes .git/index -------


def test_onboard_apply_zero_file_scan_writes_no_profile(tmp_path: Path) -> None:
    """--apply on a tree whose verification scan covers zero files exits 2 and leaves PROFILE.md absent."""
    repo = tmp_path / "repo"
    (repo / "docs").mkdir(parents=True)
    (repo / "docs" / "README.md").write_text("# nothing to scan\n", encoding="utf-8")
    proc = run_script("onboard", str(repo), "--apply", "--baseline", "--python", sys.executable, cwd=tmp_path)
    assert proc.returncode == 2, proc.stdout + proc.stderr
    assert not (repo / ".somnus-debug" / "PROFILE.md").exists()
    assert "PROFILE.md not written" in proc.stdout
    assert "Baseline skipped" in proc.stdout
    assert not (repo / ".somnus-debug" / "runs").exists()
    again = run_script("onboard", str(repo), "--python", sys.executable, cwd=tmp_path)
    assert "profile: False" in again.stdout, again.stdout


def test_onboard_plan_mode_leaves_git_index_untouched(tmp_path: Path) -> None:
    """Plan mode reads git state without refreshing (rewriting) .git/index."""
    repo = small_project(tmp_path / "repo")
    git = ["git", "-c", "user.name=t", "-c", "user.email=t@t", "-C", str(repo)]
    subprocess.run([*git, "init", "-q"], check=True)
    (repo / ".gitignore").write_text("generated/\n", encoding="utf-8")
    (repo / "generated").mkdir()
    (repo / "generated" / "out.py").write_text("X = 1\n", encoding="utf-8")
    subprocess.run([*git, "add", "pkg", ".gitignore"], check=True)
    subprocess.run([*git, "commit", "-q", "-m", "init"], check=True)
    # Make the index's cached stat data stale so any `git status` would refresh and rewrite it.
    tracked = repo / "pkg" / "core.py"
    stat = tracked.stat()
    os.utime(tracked, (stat.st_atime + 10, stat.st_mtime + 10))
    index = repo / ".git" / "index"
    before = (index.read_bytes(), index.stat().st_mtime_ns)
    proc = run_script("onboard", str(repo), "--python", sys.executable, cwd=tmp_path)
    assert proc.returncode == 0, proc.stdout + proc.stderr
    assert "git-ignored-py=['generated']" in proc.stdout
    assert (index.read_bytes(), index.stat().st_mtime_ns) == before


# --- T-33 (D-34): --baseline never overwrites without --force-baseline ----------------------------


def test_onboard_baseline_refuses_overwrite_without_force(tmp_path: Path) -> None:
    """A recorded baseline survives a rerun; --force-baseline re-records it; doctor exit 1 still records."""
    repo = small_project(tmp_path / "repo")
    (repo / "pkg" / "stub.py").write_text(
        '"""Module docstring long enough here."""\n\n\ndef work(value: int) -> int:\n    """Do the work for real someday."""\n    pass\n',
        encoding="utf-8",
    )
    first = run_script("onboard", str(repo), "--apply", "--baseline", "--python", sys.executable, cwd=tmp_path)
    assert first.returncode == 0, first.stdout + first.stderr
    baseline = repo / ".somnus-debug" / "runs" / "baseline.json"
    assert baseline.exists()
    assert json.loads(baseline.read_text(encoding="utf-8"))["summary"]["serious_issues"] >= 1  # doctor exit 1 still records
    recorded = (baseline.read_bytes(), baseline.stat().st_mtime_ns)

    again = run_script("onboard", str(repo), "--baseline", "--python", sys.executable, cwd=tmp_path)
    assert again.returncode == 1, again.stdout + again.stderr
    assert "--force-baseline" in again.stderr
    assert (baseline.read_bytes(), baseline.stat().st_mtime_ns) == recorded

    forced = run_script("onboard", str(repo), "--baseline", "--force-baseline", "--python", sys.executable, cwd=tmp_path)
    assert forced.returncode == 0, forced.stdout + forced.stderr
    assert baseline.stat().st_mtime_ns != recorded[1]


def test_onboard_help_documents_exit_codes_and_force_baseline(tmp_path: Path) -> None:
    """--help carries the exit-code table and the baseline policy."""
    proc = run_script("onboard", "--help", cwd=tmp_path)
    assert proc.returncode == 0
    assert "--force-baseline" in proc.stdout and "exit codes:" in proc.stdout
    assert "even if" in proc.stdout and "doctor exits 1" in proc.stdout


# --- T-34 (D-21): delta.py gate holes ------------------------------------------------------------


def issue(category: str, file: str, symbol: str, severity: str = "serious", message: str = "m", line: int = 1) -> dict:
    """One doctor issue object as it appears in a JSON report."""
    return {"category": category, "severity": severity, "file_path": file, "line_number": line, "symbol": symbol, "message": message}


def report(path: Path, issues: list[dict], config_hash: str | None = "cfg-a", files: tuple[str, ...] = ("src/a.py", "src/b.py")) -> Path:
    """Write a minimal doctor JSON report and return its path."""
    data = {
        "run_id": path.stem, "project_root": str(path.parent),
        "summary": {"files_scanned": len(files), "total_issues": len(issues), "critical_issues": 0,
                    "serious_issues": sum(1 for i in issues if i["severity"] == "serious"), "minor_issues": 0, "production_score": 90},
        "issues": issues, "files": [{"relative_path": f} for f in files],
    }
    if config_hash is not None:
        data["config_hash"] = config_hash
    path.write_text(json.dumps(data), encoding="utf-8")
    return path


def delta(tmp_path: Path, *args: str) -> subprocess.CompletedProcess[str]:
    """Run delta.py with --root pointing at an empty tmp tree (no dropped-file coverage noise)."""
    return run_script("delta", *args, "--root", str(tmp_path / "empty-root"), cwd=tmp_path)


def test_delta_config_hash_change_is_input_error_unless_allowed(tmp_path: Path) -> None:
    """A severity remap in the latest config cannot launder a regression silently."""
    base = report(tmp_path / "base.json", [], config_hash="cfg-a")
    latest = report(tmp_path / "latest.json", [issue("stubs", "src/a.py", "work", severity="info")], config_hash="cfg-b")
    proc = delta(tmp_path, str(base), str(latest))
    assert proc.returncode == 3, proc.stdout + proc.stderr
    assert "config_hash differs" in proc.stderr and "Traceback" not in proc.stderr
    allowed = delta(tmp_path, str(base), str(latest), "--allow-config-change", "--json")
    assert allowed.returncode == 0, allowed.stdout + allowed.stderr
    assert json.loads(allowed.stdout)["config_hash"]["changed"] is True
    missing = report(tmp_path / "nohash.json", [], config_hash=None)
    assert delta(tmp_path, str(missing), str(base)).returncode == 3


def test_delta_broad_stale_disposition_does_not_absorb_new_finding(tmp_path: Path) -> None:
    """Lane F L7: a broad entry that matched nothing in the baseline must not mute a new serious finding."""
    base = report(tmp_path / "base.json", [issue("stubs", "src/a.py", "old", severity="serious")])
    latest = report(tmp_path / "latest.json", [
        issue("stubs", "src/a.py", "old", severity="serious"),
        issue("security_risks", "src/b.py", "run", severity="serious", message="os.system call"),
    ])
    disp = tmp_path / "dispositions.json"
    disp.write_text(json.dumps([
        {"category": "security_risks", "file": "src/*", "reason": "broad, matches nothing in baseline"},
        {"category": "stubs", "file": "src/*", "symbol": "old", "reason": "broad, covers a baseline finding"},
    ]), encoding="utf-8")
    proc = delta(tmp_path, str(base), str(latest), "--dispositions", str(disp), "--json")
    assert proc.returncode == 1, proc.stdout + proc.stderr
    out = json.loads(proc.stdout)
    assert [r["symbol"] for r in out["regressions"]] == ["run"]
    assert out["dispositioned"] == 1  # the persisting baseline stub is still excused by the broad entry
    assert out["broad_blocked"][0]["disposition"]["file"] == "src/*"
    assert [d["category"] for d in out["stale_dispositions"]] == ["security_risks"]
    md = delta(tmp_path, str(base), str(latest), "--dispositions", str(disp))
    assert "broad disposition would have excused" in md.stdout and "counted as a regression" in md.stdout


def test_delta_exact_disposition_still_excuses_new_finding(tmp_path: Path) -> None:
    """An exact (category + file + symbol) disposition may excuse a finding that is new."""
    base = report(tmp_path / "base.json", [])
    latest = report(tmp_path / "latest.json", [issue("security_risks", "src/b.py", "run")])
    disp = tmp_path / "dispositions.json"
    disp.write_text(json.dumps([{"category": "security_risks", "file": "src/b.py", "symbol": "run", "reason": "argv list, no shell"}]), encoding="utf-8")
    proc = delta(tmp_path, str(base), str(latest), "--dispositions", str(disp), "--json")
    assert proc.returncode == 0, proc.stdout + proc.stderr
    out = json.loads(proc.stdout)
    assert out["dispositioned"] == 1 and out["stale_dispositions"] == []


def test_delta_usage_error_exits_3(tmp_path: Path) -> None:
    """argparse errors are input errors (3), not coverage regressions (2)."""
    proc = run_script("delta", "only-one-arg.json", cwd=tmp_path)
    assert proc.returncode == 3, proc.stderr
    assert "usage:" in proc.stderr


def test_delta_malformed_report_exits_3_without_traceback(tmp_path: Path) -> None:
    """An issue lacking category, or a non-numeric summary, is exit 3 with a message."""
    good = report(tmp_path / "good.json", [])
    bad_issue = report(tmp_path / "bad_issue.json", [{"severity": "serious", "file_path": "src/a.py"}])
    proc = delta(tmp_path, str(good), str(bad_issue))
    assert proc.returncode == 3, proc.stdout + proc.stderr
    assert "Traceback" not in proc.stderr and "malformed issue" in proc.stderr
    bad_summary = tmp_path / "bad_summary.json"
    data = json.loads(good.read_text(encoding="utf-8"))
    data["summary"]["files_scanned"] = "three"
    bad_summary.write_text(json.dumps(data), encoding="utf-8")
    proc = delta(tmp_path, str(good), str(bad_summary))
    assert proc.returncode == 3 and "Traceback" not in proc.stderr, proc.stderr
    bad_files = tmp_path / "bad_files.json"
    data["summary"]["files_scanned"] = 2
    data["files"] = [{"path": "x"}]
    bad_files.write_text(json.dumps(data), encoding="utf-8")
    proc = delta(tmp_path, str(good), str(bad_files))
    assert proc.returncode == 3 and "Traceback" not in proc.stderr, proc.stderr


def test_delta_help_has_exit_code_table(tmp_path: Path) -> None:
    """--help documents all four exit codes and the new flag."""
    proc = run_script("delta", "--help", cwd=tmp_path)
    assert proc.returncode == 0
    for needle in ("exit codes:", "  0  clean", "  1  regression", "  2  coverage regression", "  3  input error", "--allow-config-change"):
        assert needle in proc.stdout


# --- T-35 (D-22): no PYTHONPATH=src for the doctor scan; profile records native src handling ----


def src_layout_project(root: Path) -> Path:
    """Create a src-layout project whose package imports itself absolutely."""
    (root / "src" / "calc").mkdir(parents=True)
    (root / "src" / "calc" / "__init__.py").write_text('"""Calculator package docstring here."""\n', encoding="utf-8")
    (root / "src" / "calc" / "ops.py").write_text(
        '"""Operations module docstring long enough."""\nfrom calc import __name__ as package_name\n\n\n'
        'def label() -> str:\n    """Return the package label text."""\n    name = str(package_name)\n'
        '    if not name:\n        name = "calc"\n    result = name.upper()\n    return result\n',
        encoding="utf-8",
    )
    return root


def test_onboard_scan_env_has_no_src_pythonpath(tmp_path: Path, monkeypatch) -> None:
    """The verification/baseline scan command runs without PYTHONPATH=<repo>/src."""
    onboard = load_script("onboard")
    repo = src_layout_project(tmp_path / "repo")
    facts = onboard.survey(repo)
    assert facts.src_layout
    monkeypatch.setattr(onboard, "has_somnus_debug", lambda python: True)
    runner, notes = onboard.choose_runner(facts, sys.executable)
    assert runner is not None
    assert not any("PYTHONPATH=src" in note for note in notes)
    calls: list[tuple[list[str], dict[str, str] | None]] = []

    def fake_run(cmd: list[str], cwd: Path, timeout: int = 600, env: dict[str, str] | None = None) -> subprocess.CompletedProcess[str]:
        calls.append((cmd, env))
        return subprocess.CompletedProcess(cmd, 0, "Scan complete: files=2, issues=0, critical=0, serious=0\n", "")

    monkeypatch.setattr(onboard, "run", fake_run)
    onboard.run_scan(runner, repo, repo / "python_doctor.yaml", stateful=False, out_md=tmp_path / "verify.md", cwd=tmp_path)
    cmd, env = calls[-1]
    assert "scan" in cmd
    effective = env if env is not None else os.environ
    assert str(repo / "src") not in effective.get("PYTHONPATH", "").split(os.pathsep)


def test_onboard_profile_records_native_src_layout(tmp_path: Path) -> None:
    """PROFILE.md says src layout is handled by doctor and its commands carry no PYTHONPATH."""
    repo = src_layout_project(tmp_path / "repo")
    proc = run_script("onboard", str(repo), "--apply", "--python", sys.executable, cwd=tmp_path)
    profile = repo / ".somnus-debug" / "PROFILE.md"
    assert profile.exists(), proc.stdout + proc.stderr
    text = profile.read_text(encoding="utf-8")
    assert "src layout: yes; doctor resolves the project's own packages under src/ natively" in text
    assert "PYTHONPATH=" not in text


# --- T-36: selftest pins the fixed behaviors and runs from any cwd -------------------------------

UPDATED_SELFTEST_CHECKS = (
    "src layout: own imports resolve without PYTHONPATH",
    "silent_failures: swallowed except flagged; log.exception and self.logger.error not",
    "abstractmethod / Protocol / @overload bodies not flagged as stubs",
    "property setter not flagged as duplicate_definitions",
    "test_gaps is not emitted by 0.1.0 (sentinel)",
    "structure indexes a metadata-stamped file",
)


def test_selftest_relative_python_runs_every_group_and_has_updated_checks(tmp_path: Path) -> None:
    """A relative --python works (no crashed groups) and the updated checks are present.

    Pass/fail of the updated checks depends on the doctor/structure fixes in lanes
    P1/P2, so this test pins the check set and the harness, not their verdicts.
    """
    relative = os.path.relpath(sys.executable, tmp_path)
    proc = run_script("selftest", "--python", relative, cwd=tmp_path)
    assert proc.returncode in (0, 1), proc.stdout + proc.stderr
    assert "crashed" not in proc.stdout, proc.stdout
    rows = [line for line in proc.stdout.splitlines() if line.startswith(("| PASS |", "| FAIL |"))]
    assert len(rows) == 30, proc.stdout
    for name in UPDATED_SELFTEST_CHECKS:
        assert f"| {name} |" in proc.stdout, name
    assert "| PASS | serious finding exits 1 |" in proc.stdout  # stubs detector still live
