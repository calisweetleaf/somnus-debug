"""pycache_cleaner: configurable __pycache__/*.pyc/*.pyo removal.

Original single-file implementation lives in ``core.py`` (moved verbatim
from the repo-root ``pycache_cleaner.py`` during packaging).
"""

from __future__ import annotations

from .core import main

__all__ = ["main"]
