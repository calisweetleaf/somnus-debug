"""Regression tests for the doctor-core fixes of lane P1 (discovery ledger D-IDs).

Each test drives ``somnus_debug.doctor.core`` in-process against a tmp_path
fixture and pins one behavior that the 0.1.0 discovery wave recorded as a
defect. Tests change into tmp_path so the doctor log never lands in the repo.
"""

from __future__ import annotations

import json
import os
import sqlite3
import subprocess
import sys
import textwrap
from pathlib import Path

import pytest

from somnus_debug.doctor import core

SRC_ROOT = Path(__file__).resolve().parent.parent / "src"


@pytest.fixture(autouse=True)
def _isolated_cwd(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Run every test from a private working directory."""
    work = tmp_path / "_cwd"
    work.mkdir()
    monkeypatch.chdir(work)


def write(path: Path, text: str) -> Path:
    """Write dedented text, creating parent directories."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(textwrap.dedent(text).lstrip("\n"), encoding="utf-8")
    return path


def run_doctor(*argv: str) -> int:
    """Invoke the doctor CLI entry point in-process."""
    return core.main(list(argv))


def scan_json(project: Path, tmp_path: Path, *extra: str, config: Path | None = None) -> tuple[int, dict]:
    """Run a stateless scan and return (exit code, parsed JSON report)."""
    out = tmp_path / "_out" / "report.md"
    args = ["scan", str(project), "--no-state", "-o", str(out), *extra]
    if config is not None:
        args += ["-c", str(config)]
    code = run_doctor(*args)
    return code, json.loads(out.with_suffix(".json").read_text(encoding="utf-8"))


def parse_yaml(tmp_path: Path, text: str, name: str = "cfg.yaml") -> object:
    """Parse text with the bundled YAML subset parser."""
    path = tmp_path / name
    path.write_bytes(text.encode("utf-8"))
    return core.MinimalYamlParser(path).parse()


def categories(report: dict) -> list[tuple[str, str]]:
    """Return (category, symbol) pairs from a JSON report."""
    return [(issue["category"], issue["symbol"]) for issue in report["issues"]]


# T-01 (D-29): read-only and scan commands must not create a missing project root.


def test_scan_missing_root_exits_4_and_creates_nothing(tmp_path: Path) -> None:
    missing = tmp_path / "typo_root"
    assert run_doctor("scan", str(missing)) == 4
    assert not missing.exists()


def test_scan_root_that_is_a_file_exits_4(tmp_path: Path) -> None:
    afile = write(tmp_path / "file.py", "x = 1\n")
    assert run_doctor("scan", str(afile)) == 4
    assert not (tmp_path / ".python_doctor").exists()


def test_history_and_rollback_missing_root_exit_4(tmp_path: Path) -> None:
    missing = tmp_path / "nope"
    assert run_doctor("history", str(missing)) == 4
    assert run_doctor("rollback", str(missing), "--run-id", "x") == 4
    assert not missing.exists()


def test_history_on_unscanned_root_is_read_only(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    project = tmp_path / "proj"
    project.mkdir()
    assert run_doctor("history", str(project)) == 0
    assert "No recorded runs found." in capsys.readouterr().out
    assert run_doctor("rollback", str(project), "--run-id", "20000101T000000Z") == 4
    assert not (project / ".python_doctor").exists()


def test_history_with_unusable_state_db_exits_4(tmp_path: Path) -> None:
    """D-28 / T-11: history has no stateless fallback; a broken DB is a clear exit 4."""
    project = tmp_path / "proj"
    (project / ".python_doctor" / "state.sqlite3").mkdir(parents=True)
    assert run_doctor("history", str(project)) == 4
    assert run_doctor("rollback", str(project), "--run-id", "x") == 4


# T-02 (D-03): unquoted none/null/~ for severity_exit_level is the "none" gate.


@pytest.mark.parametrize("spelling", ["none", "null", "~", "Null", '"none"', "info"])
def test_severity_exit_level_null_spellings(tmp_path: Path, spelling: str) -> None:
    project = tmp_path / "proj"
    write(project / "m.py", "def f():\n    pass\n")
    config = write(tmp_path / "doctor.yaml", f"severity_exit_level: {spelling}\n")
    code, _ = scan_json(project, tmp_path, config=config)
    assert code == (1 if spelling == "info" else 0)
    expected = "info" if spelling == "info" else "none"
    assert core.ConfigManager(config).config.severity_exit_level == expected


# T-03 (D-04): YAML subset parser fixes (cases from lane B yaml_probe.py / W3 probe.py).


@pytest.mark.parametrize(
    ("case", "text", "expected"),
    [
        ("Y10 unquoted hash no space", "a: x#y", {"a": "x#y"}),
        ("Y09 quoted hash and trailing comment", 'a: "x # y"\nb: x # comment', {"a": "x # y", "b": "x"}),
        ("Y45 quoted value trailing comment", "a: 'x' # c", {"a": "x"}),
        ("Y55 single-quoted hash", "a: 'x#y'", {"a": "x#y"}),
        ("apostrophe in plain scalar then comment", "a: don't # c", {"a": "don't"}),
        ("Y11 flow list", 'a: ["*.py", "src/*.py"]', {"a": ["*.py", "src/*.py"]}),
        ("Y12 comma inside quotes", 'a: ["a,b", "c"]', {"a": ["a,b", "c"]}),
        ("Y14 nested flow list", "a: [[1,2],3]", {"a": [[1, 2], 3]}),
        ("hash inside flow list quotes", 'a: ["#x", y]  # c', {"a": ["#x", "y"]}),
        ("Y26 single-quoted escape", "a: 'it''s'", {"a": "it's"}),
        ("single quotes keep backslashes", "a: 'C:\\new'", {"a": "C:\\new"}),
        ("Y27 double-quoted escape", 'a: "x\\ny"', {"a": "x\ny"}),
        ("empty flow mapping", "severity_levels: {}", {"severity_levels": {}}),
        ("empty flow mapping with space", "a: { }", {"a": {}}),
        ("Y18 quoted key", '"a b": 1', {"a b": 1}),
        ("single-quoted key with colon", "'k:v': 2", {"k:v": 2}),
        ("Y43 BOM", "\ufeffa: 1", {"a": 1}),
        ("Y28 leading-zero int kept as string", "c: 010", {"c": "010"}),
        ("Y29 leading zeros kept as string", "a: 007", {"a": "007"}),
        ("zero and negatives stay ints", "a: 0\nb: -1\nc: +5\nd: -0", {"a": 0, "b": -1, "c": 5, "d": 0}),
        ("Y01 plain int", "a: 5", {"a": 5}),
        ("Y06 nulls unchanged", "a: null\nb: ~", {"a": None, "b": None}),
    ],
)
def test_yaml_subset_parser(tmp_path: Path, case: str, text: str, expected: object) -> None:
    assert parse_yaml(tmp_path, text) == expected, case


def test_yaml_invalid_single_quote_is_rejected(tmp_path: Path) -> None:
    with pytest.raises(core.ConfigurationError):
        parse_yaml(tmp_path, "a: 'it's'")


def test_empty_severity_levels_mapping_is_valid(tmp_path: Path) -> None:
    config = write(tmp_path / "doctor.yaml", "severity_levels: {}\n")
    manager = core.ConfigManager(config)
    assert manager.config.severity_levels["stubs"] is core.Severity.SERIOUS


def test_bom_config_applies_first_key(tmp_path: Path) -> None:
    config = tmp_path / "doctor.yaml"
    config.write_bytes("\ufeffmax_workers: 1\n".encode("utf-8"))
    assert core.ConfigManager(config).config.max_workers == 1


def test_unknown_keys_warn_with_suggestion(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    config = write(
        tmp_path / "doctor.yaml",
        """
        detect_silent_failure: false
        totally_unrelated_option: 3
        severity_levels:
          stub: info
        """,
    )
    manager = core.ConfigManager(config)
    err = capsys.readouterr().err
    assert "detect_silent_failure" in err and "'detect_silent_failures'" in err
    assert "totally_unrelated_option" in err
    assert "stub" in err and "'stubs'" in err
    assert manager.config.detect_silent_failures is True


def test_unknown_keys_warn_for_json_config(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    config = tmp_path / "doctor.json"
    config.write_text(json.dumps({"max_worker": 2}), encoding="utf-8")
    core.ConfigManager(config)
    assert "'max_workers'" in capsys.readouterr().err


def test_known_keys_do_not_warn(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    config = tmp_path / "doctor.yaml"
    config.write_text(core.ConfigManager.default_yaml(), encoding="utf-8")
    core.ConfigManager(config)
    assert capsys.readouterr().err == ""


# T-04 (D-06, D-22): from-import child modules and src-layout resolution.

DOC = '"""Module docstring long enough for doctor."""\n'


def _cycle_project(root: Path, a_import: str, b_import: str) -> Path:
    write(root / "pkg" / "__init__.py", DOC)
    write(root / "pkg" / "a.py", DOC + a_import + "\n")
    write(root / "pkg" / "b.py", DOC + b_import + "\n")
    return root


@pytest.mark.parametrize(
    ("a_import", "b_import"),
    [("from pkg import b", "from pkg import a"), ("from . import b", "from . import a")],
)
def test_from_import_cycle_is_detected(tmp_path: Path, a_import: str, b_import: str) -> None:
    project = _cycle_project(tmp_path / "proj", a_import, b_import)
    _, report = scan_json(project, tmp_path)
    assert report["summary"]["dependency_cycles"] == 1
    assert report["dependency_graph"]["cycles"] == [["pkg/a.py", "pkg/b.py"]]


def test_from_import_of_missing_submodule_is_missing(tmp_path: Path) -> None:
    project = tmp_path / "proj"
    write(project / "pkg" / "__init__.py", DOC + "VALUE = 1\n")
    write(project / "pkg" / "a.py", DOC + "from . import ghost\nfrom . import VALUE\nprint(ghost, VALUE)\n")
    _, report = scan_json(project, tmp_path)
    missing = [edge["imported_module"] for edge in report["dependency_graph"]["missing_imports"]]
    assert missing == ["pkg.ghost"]
    assert ("missing_imports", "pkg.ghost") in categories(report)


def test_from_import_of_name_defined_in_init_resolves(tmp_path: Path) -> None:
    project = tmp_path / "proj"
    write(project / "pkg" / "__init__.py", DOC + "from .impl import helper as aliased\n\n\ndef func() -> int:\n    return 41\n")
    write(project / "pkg" / "impl.py", DOC + "def helper() -> int:\n    return 7\n")
    write(project / "main.py", DOC + "from pkg import func, aliased, impl\nprint(func, aliased, impl)\n")
    _, report = scan_json(project, tmp_path)
    assert report["dependency_graph"]["missing_imports"] == []
    targets = sorted(edge["target_file"] for edge in report["dependency_graph"]["edges"] if edge["source_file"] == "main.py")
    assert targets == ["pkg/__init__.py", "pkg/impl.py"]


@pytest.mark.parametrize("with_pythonpath", [False, True])
def test_src_layout_cycle_detected_regardless_of_pythonpath(tmp_path: Path, with_pythonpath: bool) -> None:
    project = tmp_path / "repo"
    write(project / "src" / "pkg" / "__init__.py", DOC)
    write(project / "src" / "pkg" / "a.py", DOC + "import pkg.b\n")
    write(project / "src" / "pkg" / "b.py", DOC + "from pkg import a\n")
    out = tmp_path / "out" / "r.md"
    env = os.environ.copy()
    paths = [str(SRC_ROOT)] + ([str(project / "src")] if with_pythonpath else [])
    env["PYTHONPATH"] = os.pathsep.join(paths)
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    code = "import sys; from somnus_debug.doctor.core import main; raise SystemExit(main(sys.argv[1:]))"
    subprocess.run([sys.executable, "-c", code, "scan", str(project), "--no-state", "-o", str(out)], cwd=tmp_path, env=env, capture_output=True, text=True, timeout=60)
    report = json.loads(out.with_suffix(".json").read_text(encoding="utf-8"))
    assert report["dependency_graph"]["cycles"] == [["src/pkg/a.py", "src/pkg/b.py"]]
    assert report["dependency_graph"]["missing_imports"] == []


# T-05 (D-07): detector precision.


def _scan_source(tmp_path: Path, source: str, config_text: str | None = None) -> dict:
    project = tmp_path / "proj"
    write(project / "m.py", source)
    config = write(tmp_path / "doctor.yaml", config_text) if config_text else None
    return scan_json(project, tmp_path, config=config)[1]


@pytest.mark.parametrize(
    "handler",
    [
        "logger.warning('x')",
        "LOGGER.critical('x')",
        "self.log.error('x')",
        "self.logger.exception('x')",
        "log.exception('x')",
        "logging.warn('x')",
        "audit_log.log(40, 'x')",
        "raise",
    ],
)
def test_logged_or_reraised_handler_is_not_silent(tmp_path: Path, handler: str) -> None:
    source = f'''
    """Module docstring long enough for doctor."""


    def run(self) -> None:
        """Run work and report failure diagnostics."""
        try:
            work()
        except ValueError:
            {handler}
            cleanup()
    '''
    report = _scan_source(tmp_path, source)
    assert "silent_failures" not in [c for c, _ in categories(report)]


def test_handler_with_non_log_call_is_still_silent(tmp_path: Path) -> None:
    source = '''
    """Module docstring long enough for doctor."""


    def run(self) -> None:
        """Run work and report failure diagnostics."""
        try:
            work()
        except ValueError:
            cleanup()
            metrics.error_count()
    '''
    assert ("silent_failures", "run") in categories(_scan_source(tmp_path, source))


def test_abstract_protocol_overload_bodies_are_not_stubs(tmp_path: Path) -> None:
    source = '''
    """Module docstring long enough for doctor."""
    import abc
    import typing
    from abc import ABC, abstractmethod
    from typing import Protocol, overload


    class Base(ABC):
        """Abstract base contract for the fixture."""

        @abstractmethod
        def a(self) -> int:
            """Return a value from the subclass."""
            ...

        @abc.abstractmethod
        def b(self) -> int:
            """Return a value from the subclass."""
            raise NotImplementedError


    class Reader(Protocol):
        """Structural reader protocol for the fixture."""

        def read(self) -> bytes:
            """Read bytes from the source stream."""
            ...


    @overload
    def conv(x: int) -> int: ...
    @typing.overload
    def conv(x: str) -> str: ...
    def conv(x: object) -> object:
        """Convert a value to its canonical form."""
        value = x
        return value


    def real_stub() -> None:
        """A genuine stub that must still be flagged."""
        pass
    '''
    found = categories(_scan_source(tmp_path, source))
    stubs = sorted(symbol for category, symbol in found if category == "stubs")
    assert stubs == ["real_stub"]
    assert not [s for c, s in found if c == "duplicate_definitions"]


def test_property_setter_and_deleter_are_not_duplicates(tmp_path: Path) -> None:
    source = '''
    """Module docstring long enough for doctor."""


    class Box:
        """A box holding one value for the fixture."""

        @property
        def value(self) -> int:
            """Return the stored value."""
            return self._value

        @value.setter
        def value(self, new: int) -> None:
            """Store a new value."""
            self._value = new

        @value.deleter
        def value(self) -> None:
            """Remove the stored value."""
            del self._value

        def twice(self) -> int:
            """Return a placeholder first definition."""
            return self._value * 2

        def twice(self) -> int:
            """Return the real duplicate definition."""
            return self._value + self._value
    '''
    dups = [s for c, s in categories(_scan_source(tmp_path, source)) if c == "duplicate_definitions"]
    assert dups == ["Box.twice"]


def test_dataclass_call_form_is_recognised(tmp_path: Path) -> None:
    source = '''
    """Module docstring long enough for doctor."""
    import dataclasses
    from dataclasses import dataclass


    @dataclass(frozen=True)
    class Point:
        """A frozen point for the fixture."""

        x: int


    @dataclasses.dataclass(slots=True)
    class Pair:
        """A slotted pair for the fixture."""

        a: int
    '''
    report = _scan_source(tmp_path, source)
    assert "suspicious_short_classes" not in [c for c, _ in categories(report)]
    assert all(item["is_dataclass"] for item in report["files"][0]["classes"])


def test_future_import_and_dunder_all_are_not_unused(tmp_path: Path) -> None:
    source = '''
    """Module docstring long enough for doctor."""
    from __future__ import annotations

    from os import path, sep
    from sys import argv

    __all__ = ["path"]
    __all__ += ("sep",)
    '''
    unused = [s for c, s in categories(_scan_source(tmp_path, source)) if c == "unused_imports"]
    assert unused == ["argv"]


@pytest.mark.parametrize(
    ("value", "flagged"),
    [("1", False), ("1.0", False), ("0.0", False), ("True", True), ("False", True), ("0", True), ("None", True), ('""', True), ("2", False)],
)
def test_placeholder_returns_compare_type_and_value(tmp_path: Path, value: str, flagged: bool) -> None:
    source = f'''
    """Module docstring long enough for doctor."""


    def answer() -> object:
        """Return the fixture answer value."""
        return {value}
    '''
    found = ("placeholder_returns", "answer") in categories(_scan_source(tmp_path, source))
    assert found is flagged


def test_findings_in_private_functions_use_own_qualname(tmp_path: Path) -> None:
    source = '''
    """Module docstring long enough for doctor."""


    class Worker:
        """Worker that runs one fixture task."""

        def _step(self) -> None:
            try:
                eval("1")
            except Exception:
                pass

            def _inner() -> None:
                pass

            def _inner() -> None:
                pass


    def _helper() -> None:
        try:
            run()
        except Exception:
            pass
    '''
    found = categories(_scan_source(tmp_path, source))
    assert ("security_risks", "Worker._step") in found
    assert ("silent_failures", "Worker._step") in found
    assert ("broad_exceptions", "_helper") in found
    assert ("silent_failures", "_helper") in found
    assert ("duplicate_definitions", "Worker._step._inner") in found


# T-06 (D-08, D-32): run ids are unique per state DB.


def test_same_second_scans_keep_two_history_rows(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]) -> None:
    project = tmp_path / "proj"
    write(project / "m.py", DOC + "VALUE = 1\n")
    monkeypatch.setattr(core, "utc_now_text", lambda: "20261111T120000Z")
    out = tmp_path / "out" / "r.md"
    assert run_doctor("scan", str(project), "-o", str(out)) == 0
    assert run_doctor("scan", str(project), "-o", str(out)) == 0
    assert run_doctor("scan", str(project), "-o", str(out)) == 0
    with sqlite3.connect(project / ".python_doctor" / "state.sqlite3") as conn:
        ids = sorted(row[0] for row in conn.execute("SELECT run_id FROM runs"))
        latest = conn.execute("SELECT run_id FROM report_aliases WHERE alias = 'latest'").fetchone()[0]
    assert ids == ["20261111T120000Z", "20261111T120000Z-1", "20261111T120000Z-2"]
    assert latest == "20261111T120000Z-2"
    assert json.loads(out.with_suffix(".json").read_text(encoding="utf-8"))["run_id"] == "20261111T120000Z-2"
    for run_id in ids:
        assert (project / ".python_doctor" / "reports" / run_id / "production_doctor_report.json").exists()
    capsys.readouterr()
    assert run_doctor("rollback", str(project), "--run-id", "20261111T120000Z") == 0


# T-07 (D-18): exit codes.


@pytest.mark.parametrize(("gate", "expected"), [("critical", 2), ("serious", 2), ("minor", 2), ("info", 2), ("none", 0)])
def test_critical_findings_exit_2_under_every_tripping_gate(tmp_path: Path, gate: str, expected: int) -> None:
    project = tmp_path / "proj"
    write(project / "broken.py", "def f(:\n")
    config = write(tmp_path / "doctor.yaml", f'severity_exit_level: "{gate}"\n')
    code, report = scan_json(project, tmp_path, config=config)
    assert report["summary"]["critical_issues"] >= 1
    assert code == expected


@pytest.mark.parametrize(("gate", "expected"), [("critical", 0), ("serious", 1), ("minor", 1), ("info", 1)])
def test_serious_findings_exit_1_when_gate_trips(tmp_path: Path, gate: str, expected: int) -> None:
    project = tmp_path / "proj"
    write(project / "m.py", DOC + "\n\ndef stub() -> None:\n    \"\"\"A genuine stub for the gate fixture.\"\"\"\n    pass\n")
    config = write(tmp_path / "doctor.yaml", f'severity_exit_level: "{gate}"\n')
    code, report = scan_json(project, tmp_path, config=config)
    assert report["summary"]["critical_issues"] == 0 and report["summary"]["serious_issues"] >= 1
    assert code == expected


def test_unclassified_exception_maps_to_exit_5_without_traceback(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]) -> None:
    project = tmp_path / "proj"
    write(project / "m.py", DOC)

    def boom(self: object, previous: object) -> None:
        raise AttributeError("synthetic analyzer defect")

    monkeypatch.setattr(core.ProjectScanner, "scan", boom)
    assert run_doctor("scan", str(project), "--no-state", "-o", str(tmp_path / "r.md")) == 5
    err = capsys.readouterr().err
    assert "Doctor failure: Unclassified runtime failure: AttributeError: synthetic analyzer defect" in err
    assert "Traceback" not in err


@pytest.mark.parametrize("files", [1, 2])
def test_serial_path_analyzer_error_becomes_finding(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, files: int) -> None:
    project = tmp_path / "proj"
    for index in range(files):
        write(project / f"m{index}.py", DOC)
    config = write(tmp_path / "doctor.yaml", "max_workers: 1\n")
    original = core.FileAnalyzer.analyze

    def analyze(self: core.FileAnalyzer) -> core.FileAnalysisResult:
        if self.path.name == "m0.py":
            raise RecursionError("maximum recursion depth exceeded")
        return original(self)

    monkeypatch.setattr(core.FileAnalyzer, "analyze", analyze)
    code, report = scan_json(project, tmp_path, config=config)
    assert code == 2
    errors = [issue for issue in report["issues"] if issue["category"] == "analysis_read_errors"]
    assert [(e["file_path"], e["symbol"], e["details"]["error_type"]) for e in errors] == [("m0.py", "<analysis>", "RecursionError")]
    assert report["summary"]["files_scanned"] == files


# T-08 (D-16, D-30): skip settings never hide security_risks.


def test_eval_in_repr_is_reported_with_default_config(tmp_path: Path) -> None:
    source = '''
    """Module docstring long enough for doctor."""


    class Thing:
        """A thing with a dangerous repr for the fixture."""

        value = 1

        def __repr__(self):
            return eval("'Thing'")
    '''
    found = categories(_scan_source(tmp_path, source))
    assert ("security_risks", "Thing.__repr__") in found
    assert not [c for c, s in found if s == "Thing.__repr__" and c != "security_risks"]


def test_ignore_functions_and_nested_skip_keep_security_only(tmp_path: Path) -> None:
    source = '''
    """Module docstring long enough for doctor."""
    import os


    def skipped(cmd):
        try:
            os.system(cmd)
        except Exception:
            pass


    def outer() -> None:
        """Run an outer function that hides a nested one."""

        def inner(code):
            exec(code)

        inner("1")
    '''
    config = 'ignore_functions: ["skipped"]\ncheck_nested_functions: false\n'
    found = categories(_scan_source(tmp_path, source, config))
    assert ("security_risks", "skipped") in found
    assert ("security_risks", "outer.inner") in found
    assert not [c for c, s in found if s in {"skipped", "outer.inner"} and c != "security_risks"]


def test_skipped_bodies_respect_detect_security_risks_false(tmp_path: Path) -> None:
    source = '''
    """Module docstring long enough for doctor."""


    class Thing:
        """A thing with a dangerous repr for the fixture."""

        value = 1

        def __repr__(self):
            return eval("'Thing'")
    '''
    found = categories(_scan_source(tmp_path, source, "detect_security_risks: false\n"))
    assert "security_risks" not in [c for c, _ in found]


# T-09 (D-17): empty include_patterns is an error; **/ matches zero directories.


def test_empty_include_patterns_is_configuration_error(tmp_path: Path) -> None:
    project = tmp_path / "proj"
    write(project / "m.py", DOC)
    config = write(tmp_path / "doctor.yaml", "include_patterns: []\n")
    assert run_doctor("scan", str(project), "--no-state", "-c", str(config), "-o", str(tmp_path / "r.md")) == 4


def test_double_star_matches_files_directly_in_dir(tmp_path: Path) -> None:
    project = tmp_path / "proj"
    for rel in ["src/c.py", "src/a/b.py", "src/a/x/y.py", "other/z.py", "top.py"]:
        write(project / rel, DOC)
    config = write(tmp_path / "doctor.yaml", 'include_patterns: ["src/**/*.py"]\n')
    _, report = scan_json(project, tmp_path, config=config)
    assert sorted(f["relative_path"] for f in report["files"]) == ["src/a/b.py", "src/a/x/y.py", "src/c.py"]


def test_double_star_ignore_pattern_matches_zero_directories(tmp_path: Path) -> None:
    project = tmp_path / "proj"
    for rel in ["gen/c.py", "gen/a/b.py", "keep.py"]:
        write(project / rel, DOC)
    config = write(tmp_path / "doctor.yaml", 'ignore_patterns: ["gen/**/*.py"]\n')
    _, report = scan_json(project, tmp_path, config=config)
    assert [f["relative_path"] for f in report["files"]] == ["keep.py"]


# T-10 (D-25): -o report.json never overwrites the markdown report.


@pytest.mark.parametrize("state", [True, False])
def test_json_output_path_does_not_collide_with_markdown(tmp_path: Path, state: bool) -> None:
    project = tmp_path / "proj"
    write(project / "m.py", DOC)
    target = tmp_path / "out" / "report.json"
    args = ["scan", str(project), "-o", str(target)] + ([] if state else ["--no-state"])
    assert run_doctor(*args) == 0
    assert json.loads(target.read_text(encoding="utf-8"))["summary"]["files_scanned"] == 1
    assert (tmp_path / "out" / "report.md").read_text(encoding="utf-8").startswith(("<style>", "# Python Production Doctor Report"))


def test_explicit_identical_md_and_json_paths_are_rejected(tmp_path: Path) -> None:
    project = tmp_path / "proj"
    write(project / "m.py", DOC)
    same = str(tmp_path / "r.md")
    assert run_doctor("scan", str(project), "--no-state", "-o", same, "--json-output", same) == 4


# T-12 (D-34): ConfigManager.replace validates and recomputes config_hash.


def test_config_manager_replace_validates_and_rehashes() -> None:
    manager = core.ConfigManager(None)
    original_hash = manager.config_hash
    updated = manager.replace(max_workers=1, include_patterns=("src/*.py",), severity_levels={**manager.config.severity_levels, "stubs": core.Severity.INFO})
    assert updated is manager.config
    assert manager.config.max_workers == 1
    assert manager.config.include_patterns == ("src/*.py",)
    assert manager.severity("stubs") is core.Severity.INFO
    assert manager.config_hash != original_hash
    twin = core.ConfigManager(None)
    twin.replace(max_workers=1, include_patterns=("src/*.py",), severity_levels={**manager.config.severity_levels, "stubs": core.Severity.INFO})
    assert twin.config_hash == manager.config_hash


def test_config_manager_replace_rejects_invalid_values_atomically() -> None:
    manager = core.ConfigManager(None)
    before = (manager.config, manager.config_hash, dict(manager.raw_config))
    with pytest.raises(core.ConfigurationError):
        manager.replace(max_workers=0)
    with pytest.raises(core.ConfigurationError):
        manager.replace(no_such_field=True)
    assert (manager.config, manager.config_hash, dict(manager.raw_config)) == before


def test_config_hash_matches_fresh_manager_for_same_settings(tmp_path: Path) -> None:
    config = write(tmp_path / "doctor.yaml", "max_workers: 2\n")
    replaced = core.ConfigManager(None)
    replaced.replace(max_workers=2)
    assert replaced.config_hash == core.ConfigManager(config).config_hash
