#!/usr/bin/env python3
# somnus:metadata:v2
# somnus:
#   schema: "somnus://metadata/core/2.0.0"
#   id: "urn:somnus:artifact:01a19ace-7700-747d-8ec0-cb626c1a2281"
#   revision: 1
#   title: "Onboard a codebase onto somnus-debug with a verified, project-local profile"
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
#       - target_ref: "urn:somnus:artifact:01a19ace-7700-747d-8ec0-cb626c1a2281"
#         aspects: ["content"]
#   time: {}
#   names:
#     slug: "onboard-a-codebase-onto-somnus-debug-with-a-verified-project-local-profile"
#   knowledge:
#     coverage: "artifact"
#     subjects: ["urn:somnus:artifact:01a19ace-7700-747d-8ec0-cb626c1a2281"]
#   access:
#     visibility: "internal"
#     allowed_uses: ["archive", "search", "reason"]
#   ingestion:
#     disposition: "candidate"
#     body_role: "source"
# somnus:end
"""Onboard a codebase onto somnus-debug with a verified, project-local profile.

Plan mode (default) surveys the repository, picks the interpreter that should
run doctor, and, when a doctor config already exists, proves its coverage with
a stateless scan from a throwaway directory. It writes nothing in the repo.

``--apply`` writes ``.somnus-debug/`` (doctor config, pycache config,
dispositions, profile card, local .gitignore) and never overwrites a file.
The profile card is written only after the verification scan passes, so a
repo whose coverage is wrong is never recorded as onboarded.
``--baseline`` records a stateful baseline scan under ``.somnus-debug/runs/``
and refuses to replace an existing one unless ``--force-baseline`` is given.

Why the runner matters: doctor resolves third-party imports with
``importlib.util.find_spec`` in the interpreter that runs it. A CLI installed
outside the project's environment flags every project dependency as a
``missing_imports`` finding. A ``src/`` layout needs nothing extra: doctor
resolves absolute imports of the project's own packages under ``<root>/src``
itself, so onboard no longer exports ``PYTHONPATH=src`` (which made those
imports resolve as third-party and hid dependency cycles).

Exit codes: 0 ok, 1 usage error or baseline refused, 2 coverage failure,
3 somnus-debug unavailable.
Standard library only.
"""

from __future__ import annotations

import argparse
import datetime as dt
import os
import re
import shutil
import subprocess
import sys
import tempfile
from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path

PROFILE_DIR = ".somnus-debug"
FIELDKIT = Path(__file__).resolve().parent.parent

ALWAYS_PRUNE = {
    ".git", ".hg", ".svn", "__pycache__", "node_modules", ".tox", ".nox",
    ".mypy_cache", ".pytest_cache", ".ruff_cache", ".eggs", ".python_doctor",
    PROFILE_DIR, "site-packages", "build", "dist", ".venv", "venv", "env", ".surgeon",
}
BASE_IGNORES = [
    "__pycache__/*", "*.pyc", ".git/*", ".hg/*", ".mypy_cache/*", ".pytest_cache/*",
    ".ruff_cache/*", ".tox/*", ".nox/*", ".venv/*", "venv/*", "env/*", "node_modules/*",
    ".python_doctor/*", f"{PROFILE_DIR}/*", "build/*", "dist/*", ".eggs/*", "site-packages/*",
]
PYCACHE_EXCLUDES = [".git", ".hg", "node_modules", ".venv", "venv", "env", ".tox", ".nox", "site-packages"]
VENV_NAMES = (".venv", "venv", "env")
TEST_DIR_NAMES = {"test", "tests", "testing"}
NATIVE_GATE_FILES = [
    "pyproject.toml", "setup.cfg", "setup.py", "pytest.ini", "tox.ini", "noxfile.py",
    "Makefile", "justfile", ".pre-commit-config.yaml", ".github/workflows",
]
SCAN_LINE = re.compile(r"files=(\d+), issues=(\d+), critical=(\d+), serious=(\d+)")
EXIT_MEANING = {
    0: "gate passed", 1: "serious findings exceed gate", 2: "critical findings",
    4: "configuration or doctor error", 5: "doctor runtime failure",
}


class DoctorError(RuntimeError):
    """Doctor could not run with the chosen config; onboard reports it on one line and exits 2."""


@dataclass
class Runner:
    """How to invoke somnus-debug for this repository."""

    argv: list[str]
    kind: str
    note: str

    def shell_prefix(self) -> str:
        """Render the runner as a shell command prefix."""
        # Interpreter paths stay absolute: CPython 3.14 warns when a venv python is invoked via "../.venv".
        return " ".join(self.argv)


@dataclass
class Survey:
    """Facts gathered from the repository before any write."""

    root: Path
    py_by_top: Counter = field(default_factory=Counter)
    root_py: list[str] = field(default_factory=list)
    venvs: list[str] = field(default_factory=list)
    git_ignored_py_dirs: list[str] = field(default_factory=list)
    egg_info: list[str] = field(default_factory=list)
    src_layout: bool = False
    existing_doctor_configs: list[str] = field(default_factory=list)
    has_profile: bool = False
    has_root_state: bool = False
    has_harness: list[str] = field(default_factory=list)
    test_dirs: list[str] = field(default_factory=list)
    native_gates: list[str] = field(default_factory=list)
    agents_files: list[str] = field(default_factory=list)
    agents_mentions_debug: bool = False
    is_git: bool = False

    @property
    def total_py(self) -> int:
        """Total Python files the survey considers project source."""
        return sum(self.py_by_top.values()) + len(self.root_py)


def run(cmd: list[str], cwd: Path, timeout: int = 600, env: dict[str, str] | None = None) -> subprocess.CompletedProcess[str]:
    """Run an argv command (never through a shell) and capture text output."""
    return subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, timeout=timeout, check=False, env=env)


def git_ignored_dirs(root: Path) -> list[str]:
    """Return git-ignored directories (relative, POSIX) that contain Python files.

    Read-only: ``git status`` refreshes and rewrites ``.git/index``; ``ls-files`` with optional
    locks disabled never writes to the repository.
    """
    env = os.environ.copy()
    env["GIT_OPTIONAL_LOCKS"] = "0"
    cmd = ["git", "--no-optional-locks", "-C", str(root), "ls-files", "-z", "--others", "--ignored", "--exclude-standard", "--directory"]
    proc = run(cmd, root, timeout=60, env=env)
    if proc.returncode != 0:
        return []
    found: list[str] = []
    for entry in proc.stdout.split("\0"):
        if not entry.endswith("/"):
            continue
        rel = entry.rstrip("/")
        if Path(rel).name in ALWAYS_PRUNE:
            continue
        if any(name.endswith(".py") for _, _, files in os.walk(root / rel) for name in files):
            found.append(rel)
    return sorted(found)


def survey(root: Path) -> Survey:
    """Walk the repository once and collect onboarding facts."""
    facts = Survey(root=root)
    facts.has_profile = (root / PROFILE_DIR / "PROFILE.md").is_file()
    facts.has_root_state = (root / ".python_doctor").is_dir()
    facts.is_git = (root / ".git").exists()
    facts.has_harness = [name for name in ("run_test.py", "CONTRACT.md") if (root / name).exists()]
    facts.native_gates = [name for name in NATIVE_GATE_FILES if (root / name).exists()]
    src = root / "src"
    facts.src_layout = src.is_dir() and any((child / "__init__.py").exists() for child in src.iterdir() if child.is_dir())
    for name in ("AGENTS.md", "CLAUDE.md", ".github/copilot-instructions.md"):
        path = root / name
        if path.is_file():
            facts.agents_files.append(name)
            if "somnus-debug" in path.read_text(encoding="utf-8", errors="replace"):
                facts.agents_mentions_debug = True
    if facts.is_git:
        facts.git_ignored_py_dirs = git_ignored_dirs(root)
    ignored = set(facts.git_ignored_py_dirs)
    for dirpath, dirnames, filenames in os.walk(root):
        here = Path(dirpath)
        if "pyvenv.cfg" in filenames and here != root:
            facts.venvs.append(here.relative_to(root).as_posix())
            dirnames[:] = []
            continue
        keep = []
        for name in dirnames:
            rel = (here / name).relative_to(root).as_posix()
            if name.endswith(".egg-info"):
                facts.egg_info.append(rel)
            elif name not in ALWAYS_PRUNE and rel not in ignored:
                keep.append(name)
                if name in TEST_DIR_NAMES:
                    facts.test_dirs.append(rel)
        dirnames[:] = keep
        for name in filenames:
            rel = (here / name).relative_to(root).as_posix()
            if name in {"python_doctor.yaml", "python_doctor.yml"} and here in {root, root / PROFILE_DIR}:
                facts.existing_doctor_configs.append(rel)
            if not name.endswith(".py"):
                continue
            if here == root:
                facts.root_py.append(name)
            else:
                facts.py_by_top[rel.split("/", 1)[0]] += 1
    return facts


def venv_python(venv: Path) -> Path | None:
    """Return the interpreter inside a virtualenv directory, if present."""
    for candidate in (venv / "bin" / "python", venv / "Scripts" / "python.exe"):
        if candidate.exists():
            return candidate
    return None


def has_somnus_debug(python: Path) -> bool:
    """Return true when ``python`` can import somnus_debug."""
    with tempfile.TemporaryDirectory() as tmp:
        try:
            return run([str(python), "-c", "import somnus_debug"], Path(tmp), timeout=60).returncode == 0
        except OSError:
            return False


def choose_runner(facts: Survey, explicit_python: str | None) -> tuple[Runner | None, list[str]]:
    """Pick the interpreter that should run doctor and explain the choice."""
    notes: list[str] = []
    if facts.src_layout:
        notes.append("src/ layout detected: doctor resolves the project's own packages under src/ itself; no PYTHONPATH is exported.")
    if explicit_python:
        # abspath, not resolve(): a venv's bin/python is a symlink to the base interpreter, and
        # following it drops the venv's site-packages (and somnus-debug with them).
        python = Path(os.path.abspath(Path(explicit_python).expanduser()))
        if not python.is_file():
            notes.append(f"--python {explicit_python}: no such interpreter ({python}).")
            return None, notes
        if not has_somnus_debug(python):
            notes.append(f"{python} cannot import somnus_debug. Install it there: {python} -m pip install somnus-debug")
            return None, notes
        return Runner([str(python), "-m", "somnus_debug.cli"], "explicit", f"{python} (--python)"), notes
    venv_candidates = [facts.root / name for name in VENV_NAMES] + [facts.root / rel for rel in facts.venvs]
    for venv in dict.fromkeys(venv_candidates):
        python = venv_python(venv)
        if python is None:
            continue
        if has_somnus_debug(python):
            return Runner([str(python), "-m", "somnus_debug.cli"], "project-env", f"project environment {venv.relative_to(facts.root)}"), notes
        notes.append(
            f"Project environment {venv.relative_to(facts.root)} lacks somnus-debug. Third-party imports will only "
            f"resolve if it runs there: {python.relative_to(facts.root)} -m pip install somnus-debug (ask before installing)."
        )
    if shutil.which("somnus-debug"):
        notes.append("Using somnus-debug from PATH. Its interpreter, not the project's, resolves third-party imports; expect missing_imports for project dependencies it cannot see.")
        return Runner(["somnus-debug"], "path", "somnus-debug on PATH"), notes
    notes.append("somnus-debug is not installed. Install with `pip install somnus-debug` (into the project environment when one exists), following the operator's install policy.")
    return None, notes


def cli_version(runner: Runner) -> str:
    """Return the version string reported by the runner."""
    with tempfile.TemporaryDirectory() as tmp:
        proc = run([*runner.argv, "--version"], Path(tmp), timeout=60)
    return (proc.stdout.strip() or proc.stderr.strip() or "unknown").splitlines()[0]


def ignore_patterns(facts: Survey) -> list[str]:
    """Build doctor ignore patterns: defaults plus repo-specific noise."""
    extra = [f"{rel}/*" for rel in facts.venvs + facts.egg_info + facts.git_ignored_py_dirs]
    return list(dict.fromkeys(BASE_IGNORES + extra))


def doctor_config_text(facts: Survey, runner: Runner) -> str:
    """Generate doctor YAML from the CLI's own default, then retarget coverage and state."""
    with tempfile.TemporaryDirectory() as tmp:
        target = Path(tmp) / "default.yaml"
        proc = run([*runner.argv, "doctor", "init-config", "-o", str(target)], Path(tmp), timeout=60)
        if proc.returncode != 0:
            raise DoctorError(f"doctor init-config failed (exit {proc.returncode}): {first_error_line(proc.stderr)}")
        text = target.read_text(encoding="utf-8")
    include_block = 'include_patterns:\n  - "*.py"\n'
    ignore_block = "ignore_patterns:\n" + "".join(f'  - "{p}"\n' for p in ignore_patterns(facts))
    text, n_inc = re.subn(r"include_patterns:\n(?:  - .*\n)+", include_block, text)
    text, n_ign = re.subn(r"ignore_patterns:\n(?:  - .*\n)+", ignore_block, text)
    text, n_state = re.subn(r"^state_dir: .*$", f'state_dir: "{PROFILE_DIR}/state"', text, flags=re.M)
    if (n_inc, n_ign, n_state) != (1, 1, 1):
        raise DoctorError("default doctor config layout changed; update onboard.py before generating a profile")
    header = (
        f"# Generated by somnus-debug-fieldkit onboard.py on {dt.date.today().isoformat()}.\n"
        "# Coverage = include \"*.py\" minus ignore_patterns (fnmatch; '*' crosses '/';\n"
        "# 'name/*' also prunes any directory called 'name' at any depth).\n"
        "# Edit coverage here, then rerun onboard.py in plan mode. Never lower gates to go green.\n"
    )
    return header + text


def pycache_config_text(facts: Survey) -> str:
    """Generate a dry-run-locked pycache cleaner config rooted at this repo."""
    excludes = list(dict.fromkeys(PYCACHE_EXCLUDES + [Path(v).name for v in facts.venvs]))
    lines = [
        "# Generated by somnus-debug-fieldkit onboard.py. roots must be absolute: relative roots",
        "# resolve against the caller's cwd, not this file. exclude matches directory NAMES only.",
        "# dry_run is locked true; a live pass requires a deliberate, authorized edit to false.",
        "roots:",
        f'  - "{facts.root.as_posix()}"',
        "exclude:",
        *[f'  - "{name}"' for name in excludes],
        "targets:",
        '  - "__pycache__"',
        '  - "*.pyc"',
        '  - "*.pyo"',
        "dry_run: true",
        "verbose: false",
        "max_depth: null",
        "follow_symlinks: false",
        "log_file: null",
        "",
    ]
    return "\n".join(lines)


def profile_text(facts: Survey, runner: Runner, version: str, config_rel: str, scan: dict[str, str] | None, notes: list[str]) -> str:
    """Render PROFILE.md: the per-repo operating card future agents read first."""
    profile_dir = facts.root / PROFILE_DIR
    sd = runner.shell_prefix()
    cfg = Path(config_rel).name if config_rel.startswith(PROFILE_DIR + "/") else f"../{config_rel}"
    delta = f"python3 {FIELDKIT / 'scripts' / 'delta.py'}"
    top = "\n".join(f"| `{name}/` | {count} |" for name, count in facts.py_by_top.most_common()) or "| (none) | 0 |"
    root_files = ", ".join(f"`{n}`" for n in sorted(facts.root_py)) or "none"
    noise = facts.venvs + facts.egg_info + facts.git_ignored_py_dirs
    scan_text = "not run"
    if scan:
        scan_text = f"files={scan['files']}, issues={scan['issues']}, critical={scan['critical']}, serious={scan['serious']}, exit={scan['exit']} ({scan['meaning']})"
    note_text = "\n".join(f"- {n}" for n in notes) or "- none"
    return f"""# somnus-debug profile

Generated {dt.date.today().isoformat()} by somnus-debug-fieldkit `onboard.py` with somnus-debug `{version}`.
Agents read this card before using somnus-debug here. Project tests, CI, and `AGENTS.md` remain the acceptance authority.

## Runner

{runner.note}. Every command below runs from `.somnus-debug/` so `production_doctor.log` stays out of the repo root.

{note_text}

## Layout

| Path | Purpose | Tracked |
|---|---|---|
| `{config_rel}` | Doctor config: coverage, thresholds, gate | yes |
| `.somnus-debug/dispositions.json` | Reviewed findings that are accepted or false positives, with reasons | yes |
| `.somnus-debug/pycache.yaml` | Cache-cleaner config, dry-run locked | yes |
| `.somnus-debug/PROFILE.md` | This card | yes |
| `.somnus-debug/state/` | Doctor SQLite history and per-run reports | no |
| `.somnus-debug/runs/` | Named baseline and latest reports | no |

## Coverage at onboarding

| Directory | .py files |
|---|---|
{top}

- Root-level Python files: {root_files}
- src layout: {"yes; doctor resolves the project's own packages under src/ natively (no PYTHONPATH)" if facts.src_layout else "no"}
- Ignored as non-project noise: {", ".join(f"`{n}`" for n in noise) or "none detected"}
- Test directories: {", ".join(f"`{t}`" for t in facts.test_dirs) or "none detected"}
- Native gate files: {", ".join(f"`{g}`" for g in facts.native_gates) or "none detected; read AGENTS.md"}
- Single-test harness: {", ".join(f"`{h}`" for h in facts.has_harness) or "absent"}
- Verification scan: {scan_text}

## Loop commands

```console
cd .somnus-debug
{sd} doctor scan .. -c {cfg} -o runs/baseline.md --json-output runs/baseline.json   # before edits
{sd} doctor scan .. -c {cfg} -o runs/latest.md --json-output runs/latest.json       # after each repair batch
{delta} runs/baseline.json runs/latest.json --dispositions dispositions.json          # new / resolved / regressions
{sd} doctor history .. -c {cfg} --limit 10
{sd} structure ../path/to/file.py
{sd} pycache-clean --config pycache.yaml --dry-run --verbose
```

`delta.py` exit codes: 0 clean, 1 new serious/critical finding, 2 coverage regression, 3 input error.
Doctor exit codes: 0 gate passed, 1 serious, 2 critical, 4 config/doctor error, 5 runtime failure. A zero-file scan exits 0.
Finding meanings, real fixes, and known false positives: `{FIELDKIT / 'references' / 'findings.md'}`.

## Maintenance

- Tree changed shape (new package, vendored drop): edit `ignore_patterns`, then `python3 {FIELDKIT / 'scripts' / 'onboard.py'} ..` (plan mode).
- Repo moved or cloned: regenerate `pycache.yaml` (absolute roots) and this card.
- Re-onboarding never overwrites; delete or edit files deliberately.
"""


def first_error_line(stderr: str) -> str:
    """Return doctor's own one-line failure message from stderr, or the last non-empty line."""
    lines = [line.strip() for line in stderr.splitlines() if line.strip()]
    for line in lines:
        if line.startswith("Doctor failure:"):
            return line
    return lines[-1] if lines else "no output on stderr"


def run_scan(runner: Runner, root: Path, config: Path, stateful: bool, out_md: Path, cwd: Path) -> dict[str, str]:
    """Run a doctor scan with ``cwd`` as the log location and summarize the result."""
    cmd = [*runner.argv, "doctor", "scan", str(root), "-c", str(config), "-o", str(out_md), "--json-output", str(out_md.with_suffix(".json"))]
    if not stateful:
        cmd.append("--no-state")
    proc = run(cmd, cwd)
    match = SCAN_LINE.search(proc.stdout)
    if match is None:
        raise DoctorError(f"doctor scan with {config} failed (exit {proc.returncode}): {first_error_line(proc.stderr)}")
    files, issues, critical, serious = match.groups()
    run_id = re.search(r"Run ID: (\S+)", proc.stdout)
    return {
        "files": files, "issues": issues, "critical": critical, "serious": serious,
        "exit": str(proc.returncode), "meaning": EXIT_MEANING.get(proc.returncode, "unknown"),
        "report": str(out_md), "run_id": run_id.group(1) if run_id else "stateless", "stderr": proc.stderr.strip(),
    }


def write_new(path: Path, text: str, written: list[str], skipped: list[str]) -> None:
    """Write a file only if it does not already exist."""
    if path.exists():
        skipped.append(path.as_posix())
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    written.append(path.as_posix())


def print_survey(facts: Survey) -> None:
    """Print the survey as a compact Markdown plan."""
    print(f"# somnus-debug onboarding plan: {facts.root}")
    print(f"- Python files in scope: {facts.total_py} (root: {len(facts.root_py)}; by top dir: {dict(facts.py_by_top.most_common())})")
    print(f"- Noise to ignore: venvs={facts.venvs} egg-info={facts.egg_info} git-ignored-py={facts.git_ignored_py_dirs}")
    print(f"- src layout: {facts.src_layout}; existing doctor configs: {facts.existing_doctor_configs or 'none'}; root .python_doctor/: {facts.has_root_state}; profile: {facts.has_profile}")
    print(f"- Test dirs: {facts.test_dirs or 'none'}; harness files: {facts.has_harness or 'none'}; native gate files: {facts.native_gates or 'none'}")
    print(f"- Agent instruction files: {facts.agents_files or 'none'}; mention somnus-debug: {facts.agents_mentions_debug}")


def report_scan(scan: dict[str, str], total_py: int) -> int:
    """Print a verification scan and return 2 on coverage failure, else 0."""
    print(f"\nVerify scan: files={scan['files']} issues={scan['issues']} critical={scan['critical']} serious={scan['serious']} exit={scan['exit']} ({scan['meaning']})")
    if scan["stderr"]:
        print(f"stderr: {scan['stderr']}")
    if int(scan["exit"]) >= 4:
        print("FAIL: doctor could not run with this config.")
        return 2
    if int(scan["files"]) == 0:
        print("FAIL: zero files scanned. Coverage is wrong; fix include/ignore patterns before trusting any result.")
        return 2
    if int(scan["files"]) < total_py:
        print(f"WARN: scanned {scan['files']} of {total_py} surveyed files; confirm the gap is intentional.")
    return 0


def main(argv: list[str] | None = None) -> int:
    """Entry point; see the module docstring for modes and exit codes."""
    parser = argparse.ArgumentParser(
        description=__doc__.splitlines()[0],
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "exit codes:\n"
            "  0  ok\n"
            "  1  usage error, bad repo path, or --baseline refused (baseline exists, no --force-baseline)\n"
            "  2  coverage failure: zero files scanned, or doctor/config error\n"
            "  3  no usable somnus-debug (missing interpreter, or it cannot import somnus_debug)\n"
            "\n"
            "baseline: recorded when the verification scan covers files and doctor runs, even if\n"
            "doctor exits 1 or 2 (findings are what a baseline records). An existing\n"
            "runs/baseline.{md,json} is never replaced unless --force-baseline is given."
        ),
    )
    parser.add_argument("repo", nargs="?", default=".", help="repository root (default: cwd)")
    parser.add_argument("--apply", action="store_true", help="write .somnus-debug/ files that do not exist yet")
    parser.add_argument("--baseline", action="store_true", help="record a stateful baseline scan into .somnus-debug/runs/ (refuses to replace an existing one)")
    parser.add_argument("--force-baseline", action="store_true", help="with --baseline, replace an existing runs/baseline.{md,json}")
    parser.add_argument("--new-config", action="store_true", help="generate .somnus-debug/python_doctor.yaml even if a root config exists")
    parser.add_argument("--python", help="interpreter that has somnus-debug installed (default: project venv, then PATH)")
    args = parser.parse_args(argv)
    try:
        return onboard(args)
    except DoctorError as error:
        # Documented contract: a doctor/config error is a coverage failure (exit 2), one line, no traceback.
        print(f"error: {error}", file=sys.stderr)
        return 2


def onboard(args: argparse.Namespace) -> int:
    """Survey, choose a runner, verify coverage, and write the profile per ``args``."""
    root = Path(args.repo).expanduser().resolve()
    if not root.is_dir():
        print(f"error: {root} is not a directory", file=sys.stderr)
        return 1
    facts = survey(root)
    print_survey(facts)
    runner, notes = choose_runner(facts, args.python)
    for note in notes:
        print(f"- note: {note}")
    if runner is None:
        print("\nBLOCKED: no usable somnus-debug. Nothing written.")
        return 3
    version = cli_version(runner)
    print(f"- runner: {runner.note} (somnus-debug {version})")

    profile_dir = root / PROFILE_DIR
    root_configs = [c for c in facts.existing_doctor_configs if not c.startswith(PROFILE_DIR)]
    use_existing = bool(root_configs) and not args.new_config
    config_rel = root_configs[0] if use_existing else f"{PROFILE_DIR}/python_doctor.yaml"
    config_path = root / config_rel
    if use_existing:
        state = "adopt existing root config; verify its coverage (or pass --new-config)"
    elif config_path.exists():
        state = "existing profile config"
    else:
        state = "generate on --apply"
    print(f"\nDoctor config: {config_rel} ({state})")

    if args.baseline and not args.apply and not config_path.exists():
        print("error: no doctor config yet; use --apply first", file=sys.stderr)
        return 1
    existing_baseline = [p for p in (profile_dir / "runs" / "baseline.md", profile_dir / "runs" / "baseline.json") if p.exists()]
    if args.baseline and existing_baseline and not args.force_baseline:
        print(f"error: {existing_baseline[0]} exists; a baseline is never replaced silently. Pass --force-baseline to re-record it.", file=sys.stderr)
        return 1

    written: list[str] = []
    skipped: list[str] = []
    if args.apply:
        profile_dir.mkdir(exist_ok=True)
        if not use_existing:
            write_new(config_path, doctor_config_text(facts, runner), written, skipped)
        write_new(profile_dir / "pycache.yaml", pycache_config_text(facts), written, skipped)
        write_new(profile_dir / "dispositions.json", "[]\n", written, skipped)
        write_new(profile_dir / ".gitignore", "state/\nruns/\n*.log\n", written, skipped)

    scan: dict[str, str] | None = None
    status = 0
    if config_path.exists():
        # A stateless scan from a throwaway cwd writes nothing inside the repository.
        with tempfile.TemporaryDirectory() as tmp:
            scan = run_scan(runner, root, config_path, stateful=False, out_md=Path(tmp) / "verify.md", cwd=Path(tmp))
        status = report_scan(scan, facts.total_py)

    if not args.apply and not args.baseline:
        print("\nPlan only; nothing written. Rerun with --apply --baseline to write the profile and record a baseline.")
        return status

    if args.apply:
        if scan is not None and status == 0:
            write_new(profile_dir / "PROFILE.md", profile_text(facts, runner, version, config_rel, scan, notes), written, skipped)
        else:
            # Without a verified scan the card would mark the repo as onboarded; leave it absent so a rerun retries.
            print("\nPROFILE.md not written: the verification scan failed. Fix coverage, then rerun with --apply.")
            status = status or 2

    if args.baseline and status != 0:
        print("\nBaseline skipped: the verification scan failed.")
    elif args.baseline:
        (profile_dir / "runs").mkdir(parents=True, exist_ok=True)
        base = run_scan(runner, root, config_path, stateful=True, out_md=profile_dir / "runs" / "baseline.md", cwd=profile_dir)
        print(f"\nBaseline: files={base['files']} issues={base['issues']} serious={base['serious']} critical={base['critical']} exit={base['exit']} run_id={base['run_id']}")
        print(f"Report: {base['report']}")

    if written:
        print("\nWrote:\n" + "\n".join(f"- {p}" for p in written))
    if skipped:
        print("\nKept existing (not overwritten):\n" + "\n".join(f"- {p}" for p in skipped))
    if args.apply and not facts.agents_mentions_debug:
        print(f"\nNext: append {FIELDKIT / 'templates' / 'AGENTS_APPENDIX.md'} to this repo's agent instructions through the configured editor.")
    return status


if __name__ == "__main__":
    raise SystemExit(main())
