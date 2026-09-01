# somnus-debug

Somnus Sovereign Systems' project-agnostic Python developer toolkit, packaged
as a real pip-installable CLI/library instead of loose scripts copied
between projects.

## Install

```bash
pip install -e .            # editable, for active development
# or, once you want a pinned copy elsewhere:
pip install .
```

Zero runtime dependencies -- every tool in this package is stdlib-only.

## Tools

| Command | What it does |
|---|---|
| `somnus-debug doctor ...` | AST-based production-readiness diagnostics: stubs, placeholder returns, silent exception handling, dependency cycles, docstring/type-hint coverage, security risk patterns, TODOs. Config-driven via `python_doctor.yaml`. |
| `somnus-debug structure <file.py>` | Class-by-class, definition-by-definition AST index of a single Python source file, with source line spans for every class and method/function. Never imports or executes the target file. |
| `somnus-debug pycache-clean ...` | Configurable removal of `__pycache__` dirs and `*.pyc`/`*.pyo` files across one or more directory trees. Dry-run by default via `--dry-run`. |
| `somnus-debug init-test-harness [dir]` | Copies the CONTRACT.md-governed single-test harness (`run_test.py`) into a target repository so it can be hand-edited per-project. |

Every tool is also installed as its own standalone script for muscle-memory
/ CI-script compatibility with how these were invoked before packaging:
`somnus-doctor`, `somnus-structure`, `somnus-pycache-clean`.

Run `somnus-debug --help` or `somnus-debug <command> --help` for full flag
references -- each tool owns its own argparse surface, documented inline.

## Using it as a library

```python
from somnus_debug.structure.core import build_index
from somnus_debug.doctor.core import ProjectScanner, ConfigManager
```

Each `core.py` is the original single-file implementation, moved into the
package rather than rewritten, so anything importable from the standalone
script is importable from `somnus_debug.<tool>.core` too.

## Layout

```
src/somnus_debug/
    cli.py                  unified `somnus-debug <command>` dispatcher
    doctor/core.py           python_production_doctor (moved verbatim)
    doctor/default_config.yaml
    structure/core.py        analyze_python_structure (moved verbatim)
    pycache_cleaner/core.py  pycache_cleaner (moved verbatim)
    test_harness/
        scaffold.py           init-test-harness command
        templates/run_test.py CONTRACT.md-governed harness template
        templates/CONTRACT.md
docs/
    CONTRACT.md               governs run_test.py's artifact contract
    OPSEC.md                  Somnus agent operational security protocol (SUPREME authority)
    Python_Doctor_QUICKSTART.md
tests/                        smoke tests for the packaged CLI
```

## Status

Internal tool. Not published, not intended for a public index. This
repository is `git`-tracked locally for snapshotting/rollback; there is no
configured remote.

See `docs/OPSEC.md` for the operational security constraints that govern
any agent working in this repository.
