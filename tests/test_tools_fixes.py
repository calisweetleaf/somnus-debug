"""Regression tests for lane P2 fixes (structure, pycache-clean, dispatcher,
package init, test-harness template).

Each test pins one defect from wiki/DISCOVERY-LEDGER.md (D-IDs in the test
docstrings). Every test works only inside pytest's ``tmp_path`` so nothing is
written into the repository.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import textwrap
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
SRC_ROOT = REPO_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))


def _env(extra: dict[str, str] | None = None) -> dict[str, str]:
    environment = os.environ.copy()
    environment["PYTHONPATH"] = str(SRC_ROOT) + os.pathsep + environment.get("PYTHONPATH", "")
    environment["PYTHONDONTWRITEBYTECODE"] = "1"
    if extra:
        environment.update(extra)
    return environment


def _cli(*args: str, cwd: Path, env: dict[str, str] | None = None) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, "-m", "somnus_debug.cli", *args],
        cwd=cwd,
        capture_output=True,
        text=True,
        timeout=60,
        env=_env(env),
    )


# ---------------------------------------------------------------------------
# structure (T-20, T-21, T-22)
# ---------------------------------------------------------------------------

STAMPED_SOURCE = textwrap.dedent(
    '''\
    # somnus:metadata:v2
    # somnus:
    #   classification:
    #     type: "source-code"
    # somnus:end
    """Stamped module."""


    class Stamped:
        def run(self) -> int:
            return 1
    '''
)


def test_structure_indexes_metadata_stamped_file(tmp_path: Path) -> None:
    """D-01: a `#   type: "..."` header line must not be parsed as a type comment."""
    target = tmp_path / "stamped.py"
    target.write_text(STAMPED_SOURCE, encoding="utf-8")
    result = _cli("structure", str(target), cwd=tmp_path)
    assert result.returncode == 0, result.stderr
    assert "class `Stamped`" in result.stdout
    assert "def run(self) -> int:" in result.stdout




NESTED_IN_FUNCTION = textwrap.dedent(
    '''\
    def factory():
        class Outer:
            def a(self):
                pass

            class Inner:
                def b(self):
                    pass

        return Outer


    class Top:
        def c(self):
            pass

        class TopInner:
            def d(self):
                pass
    '''
)


def test_structure_class_in_class_in_function_rendered_once() -> None:
    """D-24: Inner (class in class in function) is rendered and counted exactly once."""
    from somnus_debug.structure.core import build_index

    rendered = build_index(NESTED_IN_FUNCTION, source_name="nested.py")
    # Real definitions: factory, Outer.a, Inner.b, Top.c, TopInner.d -> 5.
    assert "- Definitions emitted (module-level functions and class methods): 5" in rendered
    assert "- Class declarations: 4 (1 top-level, 3 nested)" in rendered
    assert rendered.count("class `Inner`") == 1
    assert rendered.count("def b(self):") == 1
    assert rendered.count("class `Outer`") == 1
    assert rendered.count("class `TopInner`") == 1




def test_structure_undecodable_file_is_handled_error(tmp_path: Path) -> None:
    """D-34: a non-UTF-8 file exits 2 with a one-line error, no traceback."""
    target = tmp_path / "latin1.py"
    target.write_bytes(b"# caf\xe9\nx = 1\n")
    result = _cli("structure", str(target), cwd=tmp_path)
    assert result.returncode == 2
    assert "Traceback" not in result.stderr
    errors = [line for line in result.stderr.splitlines() if line.startswith("error:")]
    assert len(errors) == 1, result.stderr
    assert "latin1.py" in errors[0]
    assert "UTF-8" in errors[0]


# ---------------------------------------------------------------------------
# pycache-clean configuration (T-23)
# ---------------------------------------------------------------------------


def _make_tree(root: Path) -> Path:
    """Create ``root/pkg/__pycache__/m.cpython.pyc`` and return the cache dir."""
    cache = root / "pkg" / "__pycache__"
    cache.mkdir(parents=True)
    (cache / "m.cpython-312.pyc").write_bytes(b"\0" * 16)
    (root / "pkg" / "m.py").write_text("x = 1\n", encoding="utf-8")
    return cache


def _write_config(path: Path, body: str) -> Path:
    path.write_text(textwrap.dedent(body), encoding="utf-8")
    return path


def _clean(config: Path, *extra: str, cwd: Path, env: dict[str, str] | None = None):
    return _cli("pycache-clean", "--config", str(config), *extra, cwd=cwd, env=env)


def test_cleaner_rejects_scalar_roots_library() -> None:
    """D-14: a scalar `roots` string must never be iterated per character."""
    from somnus_debug.pycache_cleaner.core import CleanerConfig, ConfigError, PycacheCleaner

    with pytest.raises(ConfigError, match="roots"):
        PycacheCleaner(CleanerConfig(roots="/tmp/somewhere"))  # type: ignore[arg-type]


def test_cleaner_rejects_scalar_roots_cli(tmp_path: Path) -> None:
    """D-14: scalar `roots` is a config error (exit 1) from the CLI."""
    config = _write_config(tmp_path / "c.yaml", "roots: zz\ndry_run: true\n")
    result = _clean(config, cwd=tmp_path)
    assert result.returncode == 1, (result.stdout, result.stderr)
    assert "roots" in result.stderr
    assert "list" in result.stderr


@pytest.mark.parametrize(
    "body, key",
    [
        ('dry_run: "false"\n', "dry_run"),
        ("dry_run: 0\n", "dry_run"),
        ('follow_symlinks: "yes"\n', "follow_symlinks"),
        ('verbose: "true"\n', "verbose"),
        ("max_depth: -1\n", "max_depth"),
        ("max_depth: true\n", "max_depth"),
        ('max_depth: "3"\n', "max_depth"),
        ("exclude: node_modules\n", "exclude"),
        ("targets: __pycache__\n", "targets"),
        ("targets: [1, 2]\n", "targets"),
        ("log_file: 5\n", "log_file"),
    ],
)
def test_cleaner_rejects_mistyped_values(tmp_path: Path, body: str, key: str) -> None:
    """D-14/D-31: mistyped values are config errors (exit 1) and nothing is deleted."""
    project = tmp_path / "proj"
    cache = _make_tree(project)
    config = _write_config(tmp_path / "c.yaml", f"roots:\n  - {project}\n" + body)
    result = _clean(config, cwd=tmp_path)
    assert result.returncode == 1, (result.stdout, result.stderr)
    assert key in result.stderr
    assert cache.is_dir()


def test_cleaner_rejects_negative_max_depth_flag(tmp_path: Path) -> None:
    """D-34: `--max-depth -1` is rejected instead of silently doing nothing."""
    project = tmp_path / "proj"
    cache = _make_tree(project)
    config = _write_config(tmp_path / "c.yaml", f"roots:\n  - {project}\n")
    result = _clean(config, "--max-depth", "-1", cwd=tmp_path)
    assert result.returncode == 2, (result.stdout, result.stderr)
    assert "max-depth" in result.stderr
    assert cache.is_dir()


def test_cleaner_unknown_key_keeps_logging(tmp_path: Path) -> None:
    """D-14: an unknown key warns without disabling INFO output, --verbose and log_file."""
    project = tmp_path / "proj"
    cache = _make_tree(project)
    log_file = tmp_path / "clean.log"
    config = _write_config(
        tmp_path / "c.yaml",
        f"roots:\n  - {project}\nlog_file: {log_file}\nbogus_key: 1\n",
    )
    result = _clean(config, "--verbose", cwd=tmp_path)
    assert result.returncode == 0, (result.stdout, result.stderr)
    assert "Ignoring unknown config key 'bogus_key'" in result.stdout
    assert "Starting pycache cleaner" in result.stdout
    assert "Summary:" in result.stdout
    assert "[DEBUG]" in result.stdout  # --verbose took effect
    logged = log_file.read_text(encoding="utf-8")
    assert "bogus_key" in logged and "Summary:" in logged
    assert not cache.exists()


def test_cleaner_expands_env_vars_in_roots(tmp_path: Path) -> None:
    """D-14: `$VARS` in roots are expanded, as the docstring promises."""
    project = tmp_path / "proj"
    cache = _make_tree(project)
    config = _write_config(tmp_path / "c.yaml", "roots:\n  - $CLEAN_TARGET\n")
    result = _clean(config, cwd=tmp_path, env={"CLEAN_TARGET": str(project)})
    assert result.returncode == 0, (result.stdout, result.stderr)
    assert f"Scanning root: {project}" in result.stdout
    assert not cache.exists()


def test_cleaner_expands_home_in_roots(tmp_path: Path) -> None:
    """`~` in roots expands to $HOME."""
    project = tmp_path / "home" / "proj"
    cache = _make_tree(project)
    config = _write_config(tmp_path / "c.yaml", "roots:\n  - ~/proj\n")
    result = _clean(config, cwd=tmp_path, env={"HOME": str(tmp_path / "home")})
    assert result.returncode == 0, (result.stdout, result.stderr)
    assert f"Scanning root: {project}" in result.stdout
    assert not cache.exists()


def test_cleaner_relative_roots_resolve_from_cwd(tmp_path: Path) -> None:
    """Decision kept: relative roots resolve against the working directory."""
    from somnus_debug.pycache_cleaner.core import CleanerConfig

    cfg = CleanerConfig(roots=["proj"])
    old = Path.cwd()
    os.chdir(tmp_path)
    try:
        cfg.normalize()
    finally:
        os.chdir(old)
    assert cfg.roots == [str((tmp_path / "proj").resolve())]


# ---------------------------------------------------------------------------
# pycache-clean exclude matching (T-24)
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("pattern", ["node_modules", "node_modules/*"])
def test_cleaner_exclude_matches_name_and_relative_path(tmp_path: Path, pattern: str) -> None:
    """D-14: `node_modules/*` (as in the MANUAL) and bare `node_modules` both exclude it."""
    project = tmp_path / "proj"
    kept = _make_tree(project / "node_modules")
    removed = _make_tree(project / "src")
    config = _write_config(
        tmp_path / "c.yaml", f"roots:\n  - {project}\nexclude:\n  - '{pattern}'\n"
    )
    result = _clean(config, cwd=tmp_path)
    assert result.returncode == 0, (result.stdout, result.stderr)
    assert kept.is_dir()
    assert not removed.exists()


def test_cleaner_exclude_relative_path_is_specific(tmp_path: Path) -> None:
    """A path pattern excludes only that path, not every directory with the same name."""
    project = tmp_path / "proj"
    kept = _make_tree(project / "vendor" / "keep")
    removed = _make_tree(project / "other" / "keep")
    config = _write_config(
        tmp_path / "c.yaml", f"roots:\n  - {project}\nexclude:\n  - vendor/keep\n"
    )
    result = _clean(config, cwd=tmp_path)
    assert result.returncode == 0, (result.stdout, result.stderr)
    assert kept.is_dir()
    assert not removed.exists()


# ---------------------------------------------------------------------------
# pycache-clean dry-run wording, missing roots, module hygiene (T-25)
# ---------------------------------------------------------------------------


def test_cleaner_dry_run_says_would(tmp_path: Path) -> None:
    """D-14: dry-run output says "Would remove" / "would delete", never "Removed"/"deleted"."""
    project = tmp_path / "proj"
    cache = _make_tree(project)
    (project / "stray.pyc").write_bytes(b"\0")
    config = _write_config(tmp_path / "c.yaml", f"roots:\n  - {project}\ndry_run: true\n")
    result = _clean(config, "--verbose", cwd=tmp_path)
    assert result.returncode == 0, (result.stdout, result.stderr)
    assert f"Would remove directory {cache}" in result.stdout
    assert f"Would remove file {project / 'stray.pyc'}" in result.stdout
    assert "Summary: would delete 1 directories, 1 files" in result.stdout
    assert "Removed" not in result.stdout
    assert "Summary: deleted" not in result.stdout
    assert cache.is_dir()


def test_cleaner_live_run_says_removed(tmp_path: Path) -> None:
    project = tmp_path / "proj"
    cache = _make_tree(project)
    config = _write_config(tmp_path / "c.yaml", f"roots:\n  - {project}\n")
    result = _clean(config, "--verbose", cwd=tmp_path)
    assert result.returncode == 0, (result.stdout, result.stderr)
    assert f"Removed directory {cache}" in result.stdout
    assert "Summary: deleted 1 directories" in result.stdout
    assert not cache.exists()


def test_cleaner_missing_root_exits_1_after_other_roots(tmp_path: Path) -> None:
    """D-14: a missing root is an error exit, but the remaining roots still run."""
    project = tmp_path / "proj"
    cache = _make_tree(project)
    missing = tmp_path / "does-not-exist"
    config = _write_config(
        tmp_path / "c.yaml", f"roots:\n  - {missing}\n  - {project}\n"
    )
    result = _clean(config, cwd=tmp_path)
    assert result.returncode == 1, (result.stdout, result.stderr)
    assert str(missing) in result.stdout
    assert not cache.exists()


def test_cleaner_module_compiles_without_syntax_warning() -> None:
    """D-14: the module docstring no longer carries an invalid escape (\\`) or the
    unimplemented Windows long-path claim."""
    import warnings

    path = SRC_ROOT / "somnus_debug" / "pycache_cleaner" / "core.py"
    source = path.read_text(encoding="utf-8")
    with warnings.catch_warnings():
        warnings.simplefilter("error")
        compile(source, str(path), "exec")
    assert "long path" not in source.lower()
    assert "\\\\?\\" not in source


# ---------------------------------------------------------------------------
# dispatcher without PyYAML, console scripts (T-26)
# ---------------------------------------------------------------------------

_NO_YAML_RUNNER = (
    "import sys; sys.modules['yaml'] = None; "
    "from somnus_debug.cli import main; raise SystemExit(main(sys.argv[1:]))"
)


def _cli_without_yaml(*args: str, cwd: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, "-c", _NO_YAML_RUNNER, *args],
        cwd=cwd,
        capture_output=True,
        text=True,
        timeout=60,
        env=_env(),
    )


def test_dispatcher_runs_doctor_structure_harness_without_pyyaml(tmp_path: Path) -> None:
    """D-13: only pycache-clean needs PyYAML; the other subcommands must not import it."""
    target = tmp_path / "mod.py"
    target.write_text("class A:\n    def f(self):\n        pass\n", encoding="utf-8")
    structure = _cli_without_yaml("structure", str(target), cwd=tmp_path)
    assert structure.returncode == 0, structure.stderr
    assert "class `A`" in structure.stdout
    doctor = _cli_without_yaml("doctor", "--help", cwd=tmp_path)
    assert doctor.returncode == 0, doctor.stderr
    harness = _cli_without_yaml("init-test-harness", "--help", cwd=tmp_path)
    assert harness.returncode == 0, harness.stderr


def test_dispatcher_pycache_clean_without_pyyaml_is_clean_error(tmp_path: Path) -> None:
    result = _cli_without_yaml("pycache-clean", "--dry-run", cwd=tmp_path)
    assert result.returncode == 1
    assert "pycache-clean requires PyYAML" in result.stderr
    assert "Traceback" not in result.stderr


def test_every_subcommand_has_console_script() -> None:
    """D-13/T-26: the dispatcher help promises a standalone script per command."""
    tomllib = pytest.importorskip("tomllib")  # stdlib on Python >= 3.11

    scripts = tomllib.loads((REPO_ROOT / "pyproject.toml").read_text(encoding="utf-8"))[
        "project"
    ]["scripts"]
    assert scripts["somnus-init-test-harness"] == "somnus_debug.test_harness.scaffold:main"
    from somnus_debug import cli

    for name in ("doctor", "structure", "pycache-clean", "init-test-harness"):
        assert f"somnus-{name}" in scripts
        assert f"somnus-{name}" in cli._TOP_LEVEL_HELP


# ---------------------------------------------------------------------------
# package version (T-27)
# ---------------------------------------------------------------------------


def _version_with(patch: str) -> str:
    code = (
        "import importlib.metadata as md\n"
        f"{patch}\n"
        "import somnus_debug\n"
        "assert somnus_debug.__all__ == ['__version__']\n"
        "print(somnus_debug.__version__)\n"
    )
    result = subprocess.run(
        [sys.executable, "-c", code], capture_output=True, text=True, timeout=60, env=_env()
    )
    assert result.returncode == 0, result.stderr
    return result.stdout.strip()


def test_version_comes_from_distribution_metadata() -> None:
    """D-23: __version__ follows the installed distribution, not a second literal."""
    patch = (
        "def _version(name):\n"
        "    assert name == 'somnus-debug'\n"
        "    return '9.8.7'\n"
        "md.version = _version"
    )
    assert _version_with(patch) == "9.8.7"


def test_version_falls_back_when_not_installed() -> None:
    patch = (
        "def _version(name):\n"
        "    raise md.PackageNotFoundError(name)\n"
        "md.version = _version"
    )
    assert _version_with(patch) == "0.1.0"


# ---------------------------------------------------------------------------
# test-harness template (T-28) and scaffold help (T-29)
# ---------------------------------------------------------------------------

MANIFEST_KEYS = {
    "schema_version", "run_id", "test_name", "verdict", "started_at_utc",
    "finished_at_utc", "elapsed_s", "environment", "acceptance", "result",
    "error", "artifacts",
}


def _scaffold(target: Path) -> Path:
    from somnus_debug.test_harness.scaffold import scaffold

    scaffold(target)
    return target / "run_test.py"


def _harness_env(extra: dict[str, str] | None = None) -> dict[str, str]:
    environment = {
        k: v for k, v in os.environ.items()
        if k not in ("PROJECT_ROOT", "SINGLE_TEST_OUTPUT_DIR", "PYTHONPATH")
    }
    if extra:
        environment.update(extra)
    return environment


def _run_harness(runner: Path, *args: str, cwd: Path, env: dict[str, str] | None = None):
    result = subprocess.run(
        [sys.executable, str(runner), *args],
        cwd=cwd,
        capture_output=True,
        text=True,
        timeout=120,
        env=_harness_env(env),
    )
    return result


def _summary(result: subprocess.CompletedProcess[str]) -> dict:
    start = result.stdout.index("{")
    return json.loads(result.stdout[start:])


def _pytest_repo(root: Path, *, passing: bool = True) -> Path:
    (root / "tests").mkdir(parents=True)
    (root / "pyproject.toml").write_text("[project]\nname = 'demo'\nversion = '0'\n", encoding="utf-8")
    body = "def test_ok():\n    assert 1 + 1 == 2\n" if passing else "def test_bad():\n    assert False\n"
    (root / "tests" / "test_demo.py").write_text(body, encoding="utf-8")
    return root


def test_harness_at_repo_root_keeps_artifacts_inside_repo(tmp_path: Path) -> None:
    """D-15: scaffolded at the repo root, the project root is the repo, not its parent."""
    repo = _pytest_repo(tmp_path / "repo")
    runner = _scaffold(repo)
    elsewhere = tmp_path / "elsewhere"
    elsewhere.mkdir()
    result = _run_harness(runner, cwd=elsewhere)
    assert result.returncode == 0, (result.stdout, result.stderr)
    summary = _summary(result)
    assert summary["verdict"] == "PASS"
    manifest_path = Path(summary["artifacts"]["manifest"])
    assert manifest_path.parent.parent == repo / "test-runs"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert set(manifest) == MANIFEST_KEYS
    assert manifest["test_name"] == "PROJECT TEST SUITE"
    assert manifest["environment"]["project_root"] == str(repo)
    assert manifest["acceptance"]["checks"][0]["name"] == "project-pytest-suite-passes"
    assert manifest["result"]["evidence"]["mode"] == "pytest"
    for name in ("report.md", "test.log"):
        assert (manifest_path.parent / name).is_file()
    assert not (tmp_path / "test-runs").exists()


def test_harness_in_subdirectory_walks_up_to_repo(tmp_path: Path) -> None:
    repo = _pytest_repo(tmp_path / "repo")
    runner = _scaffold(repo / "tools" / "single_test")
    result = _run_harness(runner, cwd=tmp_path)
    assert result.returncode == 0, (result.stdout, result.stderr)
    manifest = json.loads(Path(_summary(result)["artifacts"]["manifest"]).read_text(encoding="utf-8"))
    assert manifest["environment"]["project_root"] == str(repo)


def test_harness_failing_pytest_is_fail_verdict(tmp_path: Path) -> None:
    repo = _pytest_repo(tmp_path / "repo", passing=False)
    runner = _scaffold(repo)
    result = _run_harness(runner, cwd=tmp_path)
    assert result.returncode == 1
    manifest = json.loads(Path(_summary(result)["artifacts"]["manifest"]).read_text(encoding="utf-8"))
    assert manifest["verdict"] == "FAIL"
    assert manifest["error"] is None
    assert manifest["acceptance"]["failed_checks"] == 1


def test_harness_compileall_fallback_without_markers(tmp_path: Path) -> None:
    """No pytest suite: byte-compile the project (venvs excluded) without writing bytecode into it."""
    project = tmp_path / "proj"
    (project / "pkg").mkdir(parents=True)
    (project / "pkg" / "good.py").write_text("x = 1\n", encoding="utf-8")
    (project / ".venv" / "lib").mkdir(parents=True)
    (project / ".venv" / "lib" / "broken.py").write_text("def (:\n", encoding="utf-8")
    runner = _scaffold(project)
    result = _run_harness(runner, cwd=tmp_path)
    assert result.returncode == 0, (result.stdout, result.stderr)
    manifest = json.loads(Path(_summary(result)["artifacts"]["manifest"]).read_text(encoding="utf-8"))
    assert manifest["environment"]["project_root"] == str(project)
    assert manifest["result"]["evidence"]["mode"] == "compileall"
    assert manifest["acceptance"]["checks"][0]["name"] == "project-python-files-compile"
    assert not list(project.rglob("__pycache__"))

    (project / "pkg" / "bad.py").write_text("def (:\n", encoding="utf-8")
    failed = _run_harness(runner, cwd=tmp_path)
    assert failed.returncode == 1
    assert _summary(failed)["verdict"] == "FAIL"


def test_harness_help_prints_usage_and_does_not_run(tmp_path: Path) -> None:
    repo = _pytest_repo(tmp_path / "repo")
    runner = _scaffold(repo)
    for flag in ("-h", "--help"):
        result = _run_harness(runner, flag, cwd=tmp_path)
        assert result.returncode == 0, result.stderr
        assert "PROJECT_ROOT" in result.stdout
        assert "SINGLE_TEST_OUTPUT_DIR" in result.stdout
    assert not (repo / "test-runs").exists()
    assert not (tmp_path / "test-runs").exists()


def test_harness_relative_output_dir_resolves_against_project_root(tmp_path: Path) -> None:
    """D-34: relative SINGLE_TEST_OUTPUT_DIR is under the project root, not cwd."""
    repo = _pytest_repo(tmp_path / "repo")
    runner = _scaffold(repo)
    cwd = tmp_path / "cwd"
    cwd.mkdir()
    result = _run_harness(runner, cwd=cwd, env={"SINGLE_TEST_OUTPUT_DIR": "artifacts/runs"})
    assert result.returncode == 0, (result.stdout, result.stderr)
    manifest_path = Path(_summary(result)["artifacts"]["manifest"])
    assert manifest_path.parent.parent == repo / "artifacts" / "runs"
    assert not (cwd / "artifacts").exists()


def test_harness_project_root_env_override(tmp_path: Path) -> None:
    repo = _pytest_repo(tmp_path / "repo")
    other = _pytest_repo(tmp_path / "other")
    runner = _scaffold(repo)
    result = _run_harness(runner, cwd=tmp_path, env={"PROJECT_ROOT": str(other)})
    assert result.returncode == 0, (result.stdout, result.stderr)
    manifest_path = Path(_summary(result)["artifacts"]["manifest"])
    assert manifest_path.parent.parent == other / "test-runs"


def test_harness_template_has_no_project_specific_test() -> None:
    template = (
        SRC_ROOT / "somnus_debug" / "test_harness" / "templates" / "run_test.py"
    ).read_text(encoding="utf-8")
    assert "cargo" not in template
    assert "gp-cli" not in template
    assert "GOLDEN PATH" not in template


def test_scaffold_help_states_destination_and_root_inference(tmp_path: Path) -> None:
    """T-29: --help names the default destination and how run_test.py finds the project root."""
    result = _cli("init-test-harness", "--help", cwd=tmp_path)
    assert result.returncode == 0, result.stderr
    text = " ".join(result.stdout.split())
    assert "somnus-debug init-test-harness" in text
    assert "default: the current directory" in text
    assert "PROJECT_ROOT" in text
    assert ".git, pyproject.toml or setup.cfg" in text
    assert "SINGLE_TEST_OUTPUT_DIR" in text
    assert not (tmp_path / "run_test.py").exists()
