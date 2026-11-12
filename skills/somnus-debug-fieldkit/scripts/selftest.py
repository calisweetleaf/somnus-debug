#!/usr/bin/env python3
# somnus:metadata:v2
# somnus:
#   schema: "somnus://metadata/core/2.0.0"
#   id: "urn:somnus:artifact:01a19ace-7737-7032-be74-945a3b76faa0"
#   revision: 1
#   title: "Contract test: prove the installed somnus-debug still behaves the way this skill says"
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
#       - target_ref: "urn:somnus:artifact:01a19ace-7737-7032-be74-945a3b76faa0"
#         aspects: ["content"]
#   time: {}
#   names:
#     slug: "contract-test-prove-the-installed-somnus-debug-still-behaves-the-way-this-skill"
#   knowledge:
#     coverage: "artifact"
#     subjects: ["urn:somnus:artifact:01a19ace-7737-7032-be74-945a3b76faa0"]
#   access:
#     visibility: "internal"
#     allowed_uses: ["archive", "search", "reason"]
#   ingestion:
#     disposition: "candidate"
#     body_role: "source"
# somnus:end
"""Contract test: prove the installed somnus-debug still behaves the way this skill says.

Every claim the fieldkit makes about flags, defaults, exit codes, file side
effects, and finding triggers is checked here against throwaway fixtures in a
temp directory. Run it after installing or upgrading somnus-debug, or whenever
behavior looks different from the references. A FAIL means the skill and the
CLI disagree: trust the CLI, then update the reference named in the check.

Usage:
    selftest.py [--python /path/to/python]   # interpreter with somnus-debug installed
                                             # default: somnus-debug on PATH

Exit codes: 0 all checks pass, 1 at least one check failed, 3 CLI unavailable.
Standard library only; touches nothing outside its temp directory.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import textwrap
from dataclasses import dataclass
from pathlib import Path

HELP_FLAGS: dict[tuple[str, ...], tuple[str, ...]] = {
    ("doctor", "scan"): ("--config", "--output", "--json-output", "--no-state", "--verbose"),
    ("doctor", "init-config"): ("--output", "--force"),
    ("doctor", "history"): ("--config", "--limit"),
    ("doctor", "rollback"): ("--run-id", "--config"),
    ("doctor", "self-check"): ("--config", "--output", "--json-output", "--no-state"),
    ("structure",): ("--output", "--update-doc", "--no-line-numbers", "--source-label", "--no-module-functions"),
    ("pycache-clean",): ("--config", "--dry-run", "--verbose", "--max-depth", "--follow-symlinks"),
    ("init-test-harness",): ("--force", "--no-contract"),
}
SCAN_LINE = re.compile(r"files=(\d+), issues=(\d+), critical=(\d+), serious=(\d+)")


@dataclass
class Check:
    """One verified claim."""

    name: str
    reference: str
    passed: bool
    observed: str


class Harness:
    """Runs somnus-debug against fixtures and records checks."""

    def __init__(self, argv: list[str], work: Path) -> None:
        """Store the runner argv and the temp workspace."""
        self.argv = argv
        self.work = work
        self.checks: list[Check] = []

    def cli(self, *args: str, cwd: Path | None = None, env: dict[str, str] | None = None) -> subprocess.CompletedProcess[str]:
        """Invoke somnus-debug with argv (no shell) from ``cwd``."""
        cwd = cwd or self.work
        cwd.mkdir(parents=True, exist_ok=True)
        return subprocess.run([*self.argv, *args], cwd=cwd, capture_output=True, text=True, timeout=300, check=False, env=env)

    def record(self, name: str, reference: str, passed: bool, observed: str) -> None:
        """Append a check result."""
        self.checks.append(Check(name, reference, passed, observed))

    def project(self, name: str, files: dict[str, str]) -> Path:
        """Create a fixture project and return its root."""
        root = self.work / name
        for rel, content in files.items():
            path = root / rel
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(textwrap.dedent(content), encoding="utf-8")
        root.mkdir(parents=True, exist_ok=True)
        return root

    def scan(self, root: Path, config: Path | None = None, env: dict[str, str] | None = None) -> tuple[int, dict, str]:
        """Stateless scan with explicit outputs; return exit code, JSON report, stdout+stderr."""
        out = self.work / "reports" / f"{root.name}.md"
        # updated for T-36: never read a previous scan's report when this scan writes none.
        out.with_suffix(".json").unlink(missing_ok=True)
        args = ["doctor", "scan", str(root), "--no-state", "-o", str(out), "--json-output", str(out.with_suffix(".json"))]
        if config:
            args += ["-c", str(config)]
        proc = self.cli(*args, cwd=self.work / "cwd", env=env)
        report = json.loads(out.with_suffix(".json").read_text(encoding="utf-8")) if out.with_suffix(".json").exists() else {}
        return proc.returncode, report, proc.stdout + proc.stderr


def categories(report: dict) -> set[str]:
    """Return the set of finding categories in a report."""
    return {issue["category"] for issue in report.get("issues", [])}


def config_with(work: Path, name: str, replacements: dict[str, str], argv: list[str]) -> Path:
    """Write an init-config default with line-level replacements applied."""
    path = work / f"{name}.yaml"
    subprocess.run([*argv, "doctor", "init-config", "-o", str(path)], cwd=work, capture_output=True, text=True, check=True, timeout=60)
    text = path.read_text(encoding="utf-8")
    for old, new in replacements.items():
        if old not in text:
            raise RuntimeError(f"init-config output no longer contains {old!r}")
        text = text.replace(old, new)
    path.write_text(text, encoding="utf-8")
    return path


def check_cli_surface(h: Harness) -> None:
    """Flags, version, and init-config defaults."""
    version = h.cli("--version")
    h.record("--version answers", "references/install.md", version.returncode == 0, version.stdout.strip() or version.stderr.strip())
    for command, flags in HELP_FLAGS.items():
        proc = h.cli(*command, "--help")
        missing = [flag for flag in flags if flag not in proc.stdout]
        h.record(f"{' '.join(command)} --help flags", "references/commands.md", proc.returncode == 0 and not missing, "missing: " + ", ".join(missing) if missing else "all documented flags present")
    cfg = h.work / "default.yaml"
    h.cli("doctor", "init-config", "-o", str(cfg))
    text = cfg.read_text(encoding="utf-8") if cfg.exists() else ""
    h.record("init-config include is *.py", "references/commands.md", 'include_patterns:\n  - "*.py"\n' in text, "found" if "*.py" in text else "missing")
    h.record("init-config state_dir .python_doctor", "references/commands.md", 'state_dir: ".python_doctor"' in text, "found" if "state_dir" in text else "missing")
    h.record("init-config gate serious", "references/commands.md", 'severity_exit_level: "serious"' in text, "found" if "severity_exit_level" in text else "missing")


def check_exit_codes_and_side_effects(h: Harness) -> None:
    """Exit codes 0/1/2/4, zero-file behavior, log and default report locations."""
    clean = h.project("clean", {"pkg/__init__.py": '"""Package docstring long enough here."""\n'})
    nomatch = config_with(h.work, "nomatch", {'  - "*.py"': '  - "tools/*.py"'}, h.argv)
    code, report, _ = h.scan(clean, nomatch)
    h.record("zero-file scan exits 0", "SKILL.md sharp edges", code == 0 and report.get("summary", {}).get("files_scanned") == 0, f"exit={code} files={report.get('summary', {}).get('files_scanned')}")

    stub = h.project("stub", {"mod.py": '"""Module docstring long enough here."""\n\n\ndef work(value: int) -> int:\n    """Do the work for real someday."""\n    pass\n'})
    code, report, _ = h.scan(stub)
    h.record("serious finding exits 1", "references/commands.md", code == 1 and "stubs" in categories(report), f"exit={code} categories={sorted(categories(report))}")

    broken = h.project("broken", {"bad.py": "def broken(:\n"})
    code, report, _ = h.scan(broken)
    h.record("critical (syntax) exits 2", "references/commands.md", code == 2 and "syntax_errors" in categories(report), f"exit={code}")

    bad_cfg = config_with(h.work, "badgate", {'severity_exit_level: "serious"': 'severity_exit_level: "bogus"'}, h.argv)
    code, _, output = h.scan(clean, bad_cfg)
    h.record("invalid config exits 4", "references/commands.md", code == 4, f"exit={code}")

    logdir = h.work / "logcwd"
    logdir.mkdir()
    h.cli("doctor", "--help", cwd=logdir)
    h.record("doctor writes production_doctor.log to cwd (even --help)", "SKILL.md sharp edges", (logdir / "production_doctor.log").exists(), "present" if (logdir / "production_doctor.log").exists() else "absent")

    default_out = h.project("defaultout", {"m.py": '"""Module docstring long enough here."""\n'})
    h.cli("doctor", "scan", str(default_out), "--no-state", cwd=h.work / "cwd")
    landed = (default_out / "production_doctor_report.md").exists()
    h.record("scan without -o writes report into project root", "SKILL.md sharp edges", landed, "present" if landed else "absent")


def check_finding_triggers(h: Harness) -> None:
    """Trigger rules and known false positives documented in findings.md."""
    src = h.project("srclayout", {
        "src/pkg/__init__.py": '"""Package docstring long enough here."""\n',
        "src/pkg/core.py": '"""Core module docstring long enough."""\n\n\ndef add(a: int, b: int) -> int:\n    """Add two integers together."""\n    total = a + b\n    if total < 0:\n        total = 0\n    checked = int(total)\n    return checked\n',
        "tests/test_core.py": '"""Tests for the core module here."""\nfrom pkg.core import add\n\n\ndef test_add() -> None:\n    """Check that add sums values."""\n    result = add(1, 2)\n    expected = 3\n    assert result == expected\n    assert isinstance(result, int)\n',
    })
    # updated for T-36 (D-22, lane P1 T-04): doctor resolves <root>/src packages itself; no PYTHONPATH needed.
    _, plain, _ = h.scan(src)
    scanned = plain.get("summary", {}).get("files_scanned", 0)
    h.record("src layout: own imports resolve without PYTHONPATH", "references/findings.md#missing_imports",
             scanned > 0 and "missing_imports" not in categories(plain), f"files={scanned} missing_imports={'missing_imports' in categories(plain)}")

    third = h.project("thirdparty", {"m.py": '"""Module docstring long enough here."""\nimport zz_definitely_not_installed_pkg\n'})
    _, report, _ = h.scan(third)
    h.record("uninstalled third-party import -> missing_imports", "references/findings.md#missing_imports", "missing_imports" in categories(report), str(sorted(categories(report))))

    # updated for T-36 (D-07, lane P1): error-level logging through any logger name is not silent.
    silent = h.project("silent", {"m.py": textwrap.dedent('''\
        """Module docstring long enough here."""
        import logging

        log = logging.getLogger(__name__)


        def swallows(value: str) -> int:
            """Parse and hide the failure entirely."""
            try:
                parsed = int(value)
            except ValueError:
                parsed = -1
            return parsed


        def records(value: str) -> int:
            """Parse and record failure through a short logger name."""
            try:
                parsed = int(value)
            except ValueError:
                log.exception("bad value %s", value)
                parsed = -1
            return parsed


        class Parser:
            """Parses values and logs through an attribute logger."""

            def __init__(self) -> None:
                """Bind the instance logger here."""
                self.logger = logging.getLogger(__name__)
                self.count = 0

            def parse(self, value: str) -> int:
                """Parse and record failure through self.logger."""
                try:
                    parsed = int(value)
                except ValueError:
                    self.logger.error("bad value %s", value)
                    parsed = -1
                self.count += 1
                return parsed
        ''')})
    _, report, _ = h.scan(silent)
    flagged = {i["symbol"] for i in report.get("issues", []) if i["category"] == "silent_failures"}
    h.record("silent_failures: swallowed except flagged; log.exception and self.logger.error not", "references/findings.md#silent_failures",
             "swallows" in flagged and "records" not in flagged and "Parser.parse" not in flagged, f"flagged={sorted(flagged)}")

    shapes = h.project("shapes", {"m.py": textwrap.dedent('''\
        """Module docstring long enough here."""
        import abc
        from typing import Protocol, overload


        class Runnable(Protocol):
            """Structural contract for runners."""

            def run(self) -> int:
                """Run the operation for real."""
                ...


        @overload
        def scale(value: int) -> int: ...
        @overload
        def scale(value: float) -> float: ...
        def scale(value: float) -> float:
            """Scale a number by two safely."""
            doubled = value * 2
            if doubled < 0:
                doubled = 0
            result = doubled
            return result


        class Base(abc.ABC):
            """Abstract base with one contract."""

            @abc.abstractmethod
            def run(self) -> int:
                """Run the operation for real."""
                ...


        class Box:
            """Holds a value behind a property."""

            def __init__(self) -> None:
                """Create an empty box here."""
                self._value = 0
                self._ready = False
                self._count = 0
                self._name = "box"

            @property
            def value(self) -> int:
                """Return the stored value."""
                current = self._value
                if current < 0:
                    current = 0
                result = int(current)
                return result

            @value.setter
            def value(self, new: int) -> None:
                """Store a new value safely."""
                checked = int(new)
                if checked < 0:
                    checked = 0
                self._value = checked
                self._count += 1
        ''')})
    _, report, _ = h.scan(shapes)
    cats = {(i["category"], i["symbol"]) for i in report.get("issues", [])}
    # updated for T-36 (D-07, lane P1): declared-abstract bodies and property setters are not findings.
    stubs = sorted(c for c in cats if c[0] == "stubs")
    h.record("abstractmethod / Protocol / @overload bodies not flagged as stubs", "references/findings.md#stubs",
             bool(report.get("summary")) and not any(c[1] in {"Base.run", "Runnable.run", "scale"} for c in stubs), str(stubs))
    duplicates = sorted(c for c in cats if c[0] == "duplicate_definitions")
    h.record("property setter not flagged as duplicate_definitions", "references/findings.md#duplicate_definitions",
             bool(report.get("summary")) and ("duplicate_definitions", "Box.value") not in cats, str(duplicates))

    untested = h.project("untested", {"lib/a.py": '"""Library module docstring long enough."""\n\n\ndef double(value: int) -> int:\n    """Double the value carefully."""\n    result = value * 2\n    if result < 0:\n        result = 0\n    final = int(result)\n    return final\n'})
    _, report, _ = h.scan(untested)
    h.record("test_gaps is not emitted by 0.1.0 (sentinel)", "references/findings.md#test_gaps", "test_gaps" not in categories(report), "not emitted" if "test_gaps" not in categories(report) else "EMITTED: update findings.md")

    todo = h.project("todo", {"m.py": '"""Module docstring long enough here."""\n# runs in a temp dir\nVALUE = 1\n'})
    _, report, _ = h.scan(todo)
    h.record("todos match case-insensitively (\"temp\" in prose)", "references/findings.md#todos", "todos" in categories(report), str(sorted(categories(report))))


def check_other_tools(h: Harness) -> None:
    """structure, pycache-clean, and init-test-harness contracts."""
    target = h.project("structure", {"m.py": '"""Module docstring."""\n\n\nclass Alpha:\n    """A class."""\n\n    def beta(self) -> int:\n        """A method."""\n        return 1\n'})
    before = set(target.rglob("*"))
    proc = h.cli("structure", str(target / "m.py"), cwd=target)
    h.record("structure prints index to stdout and writes nothing", "references/commands.md", proc.returncode == 0 and "Alpha" in proc.stdout and set(target.rglob("*")) == before, f"exit={proc.returncode}")

    # updated for T-36 (D-01, lane P2): a somnus:metadata header line like `#   type: "source-code"` is a comment, not a type comment.
    stamped = h.project("stamped", {"m.py": textwrap.dedent('''\
        #!/usr/bin/env python3
        # somnus:metadata:v2
        # somnus:
        #   schema: "somnus://metadata/core/2.0.0"
        #   classification:
        #     category: "engineering"
        #     type: "source-code"
        # somnus:end
        """Stamped module docstring."""


        class Gamma:
            """A class in a stamped file."""

            def delta(self) -> int:
                """A method."""
                return 1
        ''')})
    proc = h.cli("structure", str(stamped / "m.py"), cwd=stamped)
    h.record("structure indexes a metadata-stamped file", "references/commands.md", proc.returncode == 0 and "Gamma" in proc.stdout, f"exit={proc.returncode} {(proc.stderr.strip().splitlines() or [''])[-1][:120]}")

    cache_root = h.project("pycache", {"pkg/__pycache__/x.cpython.pyc": "x", "keep/node_modules/__pycache__/y.pyc": "y"})
    cfg = h.work / "pycache.yaml"
    cfg.write_text(f'roots:\n  - "{cache_root}"\nexclude:\n  - "node_modules/*"\ntargets:\n  - "__pycache__"\ndry_run: false\n', encoding="utf-8")
    proc = h.cli("pycache-clean", "--config", str(cfg), "--dry-run", "--verbose", cwd=h.work / "cwd")
    survived = (cache_root / "pkg" / "__pycache__").exists()
    path_style_ignored = "node_modules/__pycache__" in proc.stderr + proc.stdout
    h.record("pycache-clean --dry-run deletes nothing", "references/commands.md", proc.returncode == 0 and survived, f"exit={proc.returncode} survived={survived}")
    h.record("pycache exclude 'node_modules/*' is root-anchored (nested node_modules kept)", "references/commands.md", path_style_ignored, "nested dir not excluded" if path_style_ignored else "nested dir excluded")

    harness_dir = h.work / "harness"
    first = h.cli("init-test-harness", str(harness_dir))
    second = h.cli("init-test-harness", str(harness_dir))
    wrote = (harness_dir / "run_test.py").exists() and (harness_dir / "CONTRACT.md").exists()
    h.record("init-test-harness writes run_test.py + CONTRACT.md, refuses overwrite", "references/commands.md", first.returncode == 0 and wrote and second.returncode != 0, f"first={first.returncode} second={second.returncode}")


def main(argv: list[str] | None = None) -> int:
    """Run every check and print a Markdown table."""
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--python", help="interpreter with somnus-debug installed (runs python -m somnus_debug.cli)")
    args = parser.parse_args(argv)
    if args.python:
        # updated for T-36: absolute (symlinks kept), since every check runs from a temp cwd.
        runner = [os.path.abspath(Path(args.python).expanduser()), "-m", "somnus_debug.cli"]
    elif shutil.which("somnus-debug"):
        runner = ["somnus-debug"]
    else:
        print("somnus-debug not found. Install: pip install somnus-debug (or pass --python).", file=sys.stderr)
        return 3
    with tempfile.TemporaryDirectory(prefix="sd-selftest-") as tmp:
        h = Harness(runner, Path(tmp))
        for group in (check_cli_surface, check_exit_codes_and_side_effects, check_finding_triggers, check_other_tools):
            try:
                group(h)
            except Exception as error:  # A crashed group is itself a failed check, reported with its cause.
                h.record(f"{group.__name__} crashed", "scripts/selftest.py", False, f"{type(error).__name__}: {error}")
    failed = [c for c in h.checks if not c.passed]
    print(f"# somnus-debug fieldkit selftest ({' '.join(runner)})\n")
    print("| Result | Check | Observed | Reference |\n|---|---|---|---|")
    for c in h.checks:
        print(f"| {'PASS' if c.passed else 'FAIL'} | {c.name} | {c.observed} | `{c.reference}` |")
    print(f"\n{len(h.checks) - len(failed)}/{len(h.checks)} passed.")
    if failed:
        print("A FAIL means the installed CLI and the skill disagree. Trust the CLI and update the referenced file.")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
