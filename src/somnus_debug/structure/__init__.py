"""analyze_python_structure: class/definition AST indexer.

Original single-file implementation lives in ``core.py`` (moved verbatim
from the repo-root ``analyze_python_structure.py`` during packaging).
"""

from __future__ import annotations

from .core import build_index, main

__all__ = ["build_index", "main"]
