"""Python Production Doctor: AST-based production-readiness diagnostics.

Original single-file implementation lives in ``core.py`` (moved verbatim
from the repo-root ``python_production_doctor.py`` during packaging; see
that module's docstring for provenance and modification history). This
``__init__`` only re-exports the entry point used by the toolkit CLI.
"""

from __future__ import annotations

from .core import main

__all__ = ["main"]
