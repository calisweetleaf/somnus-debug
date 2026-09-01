"""Unified dispatcher for the somnus-debug toolkit.

Each tool in this package (`doctor`, `structure`, `pycache-clean`,
`init-test-harness`) keeps its own independent argparse surface -- that is
intentional, since they were built and are still usable as standalone
scripts. This module is a thin router: it picks the subcommand off argv[0]
and hands the remaining arguments to that tool's own ``main()`` untouched,
rather than re-declaring every flag in a second parser that could drift out
of sync with the real one.

Installed as the ``somnus-debug`` console script. Individual tools are also
installed as their own scripts (``somnus-doctor``, ``somnus-structure``,
``somnus-pycache-clean``) for muscle-memory / CI-script compatibility with
how they were invoked before packaging.
"""

from __future__ import annotations

import sys
from typing import Sequence

from . import __version__
from .doctor.core import main as _doctor_main
from .pycache_cleaner.core import main as _pycache_main
from .structure.core import main as _structure_main
from .test_harness.scaffold import main as _scaffold_main

_SUBCOMMANDS = {
    "doctor": ("somnus-debug doctor", _doctor_main),
    "structure": ("somnus-debug structure", _structure_main),
    "pycache-clean": ("somnus-debug pycache-clean", _pycache_main),
    "init-test-harness": ("somnus-debug init-test-harness", _scaffold_main),
}

_TOP_LEVEL_HELP = f"""\
somnus-debug {__version__} -- Somnus Sovereign Systems Python developer toolkit

Usage:
    somnus-debug <command> [command args...]

Commands:
    doctor              Production-readiness diagnostics (AST-based).
    structure            Class/definition index for a single Python file.
    pycache-clean        Remove __pycache__/*.pyc/*.pyo across directory trees.
    init-test-harness    Scaffold the CONTRACT.md single-test harness into a repo.

Each command owns its own --help; run e.g. `somnus-debug doctor --help`.
Every command is also installed as its own script (somnus-doctor,
somnus-structure, somnus-pycache-clean).
"""


def _run_subcommand(name: str, argv: Sequence[str]) -> int:
    """Rewrite sys.argv for the target tool's own argparse and invoke it.

    The wrapped tools were written as standalone scripts: some accept an
    explicit ``argv`` parameter, others parse ``sys.argv`` internally. We
    normalize by always setting ``sys.argv`` to what the tool would have
    seen if invoked directly (its own program name plus the remaining
    args), so both calling conventions behave identically to running the
    original script.
    """
    prog, entry_point = _SUBCOMMANDS[name]
    old_argv = sys.argv
    sys.argv = [prog, *argv]
    try:
        result = entry_point(list(argv)) if name != "pycache-clean" else entry_point()
    except SystemExit as exc:
        return int(exc.code) if isinstance(exc.code, int) else 1
    finally:
        sys.argv = old_argv
    return int(result) if isinstance(result, int) else 0


def main(argv: Sequence[str] | None = None) -> int:
    """Entry point for the ``somnus-debug`` console script."""
    argv = list(sys.argv[1:] if argv is None else argv)

    if not argv or argv[0] in ("-h", "--help"):
        print(_TOP_LEVEL_HELP)
        return 0
    if argv[0] in ("-V", "--version"):
        print(__version__)
        return 0

    command, rest = argv[0], argv[1:]
    if command not in _SUBCOMMANDS:
        print(f"somnus-debug: unknown command {command!r}\n", file=sys.stderr)
        print(_TOP_LEVEL_HELP, file=sys.stderr)
        return 2

    return _run_subcommand(command, rest)


if __name__ == "__main__":
    raise SystemExit(main())
