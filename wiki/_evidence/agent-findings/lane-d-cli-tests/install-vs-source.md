# Lane D: source vs installed vs PyPI

Lane D (CLI/tools/integration), run 2026-11-12 00:10–00:18 UTC. Python 3.12.15 (`/usr/local/bin/python3`). All experiments ran in `/tmp/lane-d/`. Baseline commit `034f46e`.

## 1. Isolated venv install (VERIFIED)

```
cwd=/tmp/lane-d
python3 -m venv venv
./venv/bin/pip install -q pytest /workspace/.../forge/somnus-debug     # exit 0
./venv/bin/pip show somnus-debug   # Version: 0.1.0, Requires: pyyaml, Location: /tmp/lane-d/venv/lib/python3.12/site-packages
```

Installed `entry_points.txt` (`somnus_debug-0.1.0.dist-info/entry_points.txt`):

```
[console_scripts]
somnus-debug = somnus_debug.cli:main
somnus-doctor = somnus_debug.doctor.core:main
somnus-pycache-clean = somnus_debug.pycache_cleaner.core:main
somnus-structure = somnus_debug.structure.core:main
```

- `ls venv/bin | grep -i harness` returns nothing (exit 1). **There is no `somnus-init-test-harness` script.** This is confirmed by `pyproject.toml` `[project.scripts]` and documented in `docs/MANUAL.md:96` ("init-test-harness has no …" standalone script). The command is reachable only as `somnus-debug init-test-harness` or `python -m somnus_debug.test_harness.scaffold`. The `prog` of the second form is still `somnus-debug init-test-harness`, because `scaffold.py` hardcodes it.
- The installed RECORD lists 14 package files plus 4 scripts. No `.python_doctor/`, reports, or logs ship, so the `pyproject.toml` `[tool.hatch.build] exclude` works.
- The install copies the files in `src/somnus_debug/` byte for byte, metadata headers included. The installed `structure/core.py` therefore has `type_comments=True` at line 210, the same line as in the source.
- The non-editable `pip install` of the repo left no build artifacts in the repo. `git status --ignored` showed nothing new from this step.

## 2. PyPI 0.1.0 artifacts (VERIFIED)

```
pip download somnus-debug==0.1.0 --no-deps -d /tmp/lane-d/pypi                  # wheel
pip download somnus-debug==0.1.0 --no-deps --no-binary :all: -d /tmp/lane-d/pypi  # sdist
sha256 somnus_debug-0.1.0-py3-none-any.whl  1e6913e1216fc167c007479b8547e65d685e56c0461d6bf669a1e59a2eed4139
sha256 somnus_debug-0.1.0.tar.gz            4dd3fd5a6b74a5e1d05d16ec60bc1a8eb43bfd13789395187ca9f5d8cb8615d4
```

- The wheel's `somnus_debug/` and the sdist's `src/somnus_debug/` are byte-identical (`diff -rq` gives no output).
- The sdist also ships `.gitignore`, `LICENSE`, `README.md`, `pyproject.toml`, `PKG-INFO`, and `docs/{AGENTS_APPENDIX,CONTRACT,MANUAL,PUBLISHING,Python_Doctor_QUICKSTART}.md`. It has no `tests/` and no `skills/`.
- **The PyPI files carry no `# somnus:metadata:v2` headers** (`grep -rl somnus:metadata` finds 0 files). Every src file in this zip carries one.

## 3. Raw diff: PyPI vs src

All 14 package files differ byte-wise (`diff -rq`). To separate the headers from real changes, I stripped every block from `# somnus:metadata:v2` to `# somnus:end` with `/tmp/lane-d/strip.py` and diffed again:

| File | Real difference after header strip |
|---|---|
| `cli.py`, `__init__.py` ×5, `doctor/core.py`, `pycache_cleaner/core.py`, `structure/core.py`, `test_harness/scaffold.py`, `templates/run_test.py` | **None.** All identical to PyPI. |
| `doctor/default_config.yaml` | **Real change.** PyPI ships the old Somnus-MCP globs (`include_patterns: tools/*.py, tools/native/speech/*.py, test/*.py, test/speech/*.py`; ignores `potential-project-developments/*`, `reports/*`, `test/*/runs/*`). src ships `include_patterns: ["*.py"]` plus `.hg/ .mypy_cache/ .pytest_cache/ .ruff_cache/ .tox/ env/ node_modules/ build/ dist/` ignores. This matches PLAN.md §0, which notes that `5f1a73c` changed only the packaged reference config. |
| `test_harness/templates/CONTRACT.md` | Header only. src adds a 32-line YAML front-matter block (`---` / `somnus:` … `---`), which `strip.py` does not strip. The body is identical. |

So the PyPI 0.1.0 code equals src code (SOURCE-CONFIRMED by diff). The **state-unavailable fallback** in `run_scan` is in PyPI too. The `type_comments=True` call is in PyPI too, at `structure/core.py:178` with no header, versus `:210` in src (a 32-line offset, which is the header).

Consequence (VERIFIED, S05/S06): PyPI `structure` indexes its own headerless source fine (exit 0) but crashes on any stamped file (`stamped.py`, exit 2). Stamping every file in the zip turned this latent bug into a self-crash.

## 4. Root-level duplicates vs src (after header strip)

| Root file | vs src counterpart | Difference |
|---|---|---|
| `python_production_doctor.py` | `src/somnus_debug/doctor/core.py` | **Differs in `run_scan`.** src (`core.py:2062-2075`) wraps `store.previous_file_index()` in `try/except StateStoreError`, prints `Warning: local SQLite state is unavailable; continuing without history or rollback (...)` to stderr, and carries on with `state_enabled=False`. Root (`python_production_doctor.py:2066`) is `previous = store.previous_file_index() if not args.no_state else {}` with no fallback. The tested behavior `test_doctor_scan_degrades_when_sqlite_state_is_unavailable` therefore exists only in src/PyPI. |
| `analyze_python_structure.py` | `src/somnus_debug/structure/core.py` | **Differs at line 210.** Root: `ast.parse(source, filename=source_name)`. src: `ast.parse(source, filename=source_name, type_comments=True)`. |
| `pycache_cleaner.py` | `src/.../pycache_cleaner/core.py` | Identical after header strip. |
| `run_test.py` | `src/.../test_harness/templates/run_test.py` | Identical after header strip. |
| `python_doctor.yaml` | `src/.../doctor/default_config.yaml` | Root yaml equals the **PyPI** default_config (the old MCP globs), not the src one. |

## 5. DISCREPANCY: the "type_comments fixed 2026-11-05" claim

`STATE.md` ("Verified 2026-11-05") says the flag was dropped in both `src/somnus_debug/structure/core.py` and the root `analyze_python_structure.py`. In this zip it was dropped **only in the root duplicate**. src, the installed wheel built from src, and PyPI all still parse with `type_comments=True`.

VERIFIED:
- S01, S02, S03, and S07 all exit 2 with `error: invalid syntax (<file>, line N)`. N is the line of `#     type: "source-code"` in the header: line 9 in the fixture, line 10 in `structure/core.py`. They cover `somnus-debug structure` and `somnus-structure` (installed), `PYTHONPATH=src python3 -m somnus_debug.cli structure` (source), and the run on structure's own `core.py`.
- S04 and S08: root `analyze_python_structure.py` on the same files exits 0 with a full index.
- The repo test suite agrees: 2 of 12 smoke tests fail for exactly this reason (see `test-coverage.md`).

Explanation (HYPOTHESIS): the "fixed" tree was a different checkout (the Hark workspace on 2026-11-05). The uploaded zip has the root fix and the new regression test, but not the src fix.

## 6. Interpreter and runtime distinctions (VERIFIED)

- **PyYAML hard-couples every command.** `cli.py:56` imports `pycache_cleaner.core` eagerly, and that module does `import yaml` at import time (`pycache_cleaner/core.py:151`). Under `/usr/bin/python3` (3.13.5, no PyYAML), `PYTHONPATH=src /usr/bin/python3 -m somnus_debug.cli doctor --help` exits 1 with `PyYAML is required…` plus a traceback (F02b). Doctor itself is stdlib-only, but it cannot be reached through the dispatcher without PyYAML. `somnus-doctor` (direct entry) would avoid this (CONDITIONAL; not run under a yaml-less interpreter).
- **SyntaxWarning on cold import.** `pycache_cleaner/core.py:64` has the docstring escape `` ``\\?\`` `` → `SyntaxWarning: invalid escape sequence '\`'`. It prints to stderr whenever the module compiles without a cached `.pyc`. Seen in root `pycache_cleaner.py --help`, in the PyPI wheel via PYTHONPATH (S05/S06), and in source runs with `PYTHONDONTWRITEBYTECODE=1`. Every `somnus-debug` subcommand imports this module, so all of them can emit it.
- **Third-party import resolution depends on doctor's interpreter.** The same `tp.py` (`import pytest; import yaml`) gives `issues=0` / exit 0 under the venv CLI (pytest installed) but `pytest → missing` (serious) / exit 1 under system python with PYTHONPATH=src (D05a/D05b).
- **No `__main__`.** `python -m somnus_debug` and `python -m somnus_debug.doctor` exit 1 (C04/C05). `python -m somnus_debug.structure.core` works but emits a runpy `RuntimeWarning` (C06).

## 7. Workspace hygiene observations

- At 00:12:03–04 UTC, `__pycache__/` directories appeared under the **real repo's** `src/somnus_debug/**` (`git status --ignored` shows `!! src/somnus_debug/**/__pycache__/`). I did not create them in a way I can attribute. My only source-path invocations against the real `src` came later (help capture ~00:12:2x, then structure S03/S07 with `PYTHONDONTWRITEBYTECODE=1`). Possibly another lane. **Not deleted**, per the brief's no-cleanup rule. The lead should decide.
- My help-capture step ran the **root `run_test.py --help`** with cwd `/tmp/lane-d/run/help`. The script ignores argv and executed its cargo test anyway. Its default `PROJECT_ROOT` is `Path(__file__).parent.parent`, so it wrote `forge/test-runs/GOLDEN-PATH-…-001227-e542a7/{manifest.json,report.md,test.log}` **outside the repo, in the project's `forge/` directory**. I copied it to `/tmp/lane-d/evidence/root-run_test-help-artifacts/` and removed the `forge/test-runs/` directory I had created. The repo itself was untouched. (That /tmp copy was later lost when `/tmp/lane-d/` vanished from the sandbox at about 00:20 UTC. The verdict was FAIL: `FileNotFoundError: 'cargo'`. Run ID `GOLDEN-PATH-LAYER-1-DATA-HIGHWAY-RESTORATION-20261112-001227-e542a7`. Full stdout is in `help-surfaces-raw.txt`.)
