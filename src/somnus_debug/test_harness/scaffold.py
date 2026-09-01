"""Scaffold the CONTRACT.md-governed single-test harness into a repository.

``run_test.py`` (see ``templates/run_test.py``) is deliberately NOT an
importable library module: per ``docs/CONTRACT.md`` it is a portable
artifact-producing contract that is meant to be copied into a repository
and then hand-edited (only the `TEST_NAME` constant and `execute_test()`
function are project-specific). Packaging it as an import would break that
contract -- every project needs its own physically-owned copy to edit.

This module packages the template as data and provides the
``init-test-harness`` command, which does the copying for you and refuses
to silently clobber a repo that already has its own edited copy.
"""

from __future__ import annotations

import argparse
import sys
from importlib import resources
from pathlib import Path
from typing import Sequence

_TEMPLATE_FILES = ("run_test.py", "CONTRACT.md")


def _template_text(name: str) -> str:
    return resources.files("somnus_debug.test_harness.templates").joinpath(name).read_text(encoding="utf-8")


def scaffold(target_dir: Path, *, force: bool = False, with_contract: bool = True) -> list[Path]:
    """Copy the test-harness template into ``target_dir``.

    Returns the list of paths written. Raises FileExistsError (without
    writing anything) if a destination file already exists and ``force``
    is not set -- an existing run_test.py in a target repo has almost
    certainly been hand-edited per CONTRACT.md and must not be overwritten
    silently.
    """
    target_dir = target_dir.resolve()
    names = _TEMPLATE_FILES if with_contract else ("run_test.py",)
    destinations = [target_dir / name for name in names]

    if not force:
        existing = [dest for dest in destinations if dest.exists()]
        if existing:
            joined = ", ".join(str(path) for path in existing)
            raise FileExistsError(
                f"refusing to overwrite existing file(s) without --force: {joined}"
            )

    target_dir.mkdir(parents=True, exist_ok=True)
    written: list[Path] = []
    for name, dest in zip(names, destinations):
        dest.write_text(_template_text(name), encoding="utf-8")
        written.append(dest)
    return written


def _parse_args(argv: Sequence[str] | None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="somnus-debug init-test-harness",
        description="Copy the CONTRACT.md single-test harness (run_test.py) into a target repository.",
    )
    parser.add_argument(
        "target",
        type=Path,
        nargs="?",
        default=Path("."),
        help="Directory to write run_test.py (and CONTRACT.md) into (default: current directory)",
    )
    parser.add_argument("--force", action="store_true", help="Overwrite existing files at the destination")
    parser.add_argument(
        "--no-contract",
        action="store_true",
        help="Only write run_test.py; skip copying CONTRACT.md alongside it",
    )
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = _parse_args(argv)
    try:
        written = scaffold(args.target, force=args.force, with_contract=not args.no_contract)
    except FileExistsError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    for path in written:
        print(f"wrote {path}")
    print(
        "\nNext: edit TEST_NAME and execute_test() in run_test.py for this project. "
        "See CONTRACT.md for what the harness does and does not own."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
