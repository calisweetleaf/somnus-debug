"""somnus_debug: Somnus Sovereign Systems' Python developer toolkit.

A pip-installable toolbox of project-agnostic diagnostic and maintenance
tools originally maintained as loose scripts. Each tool keeps its original
single-file implementation (moved, not rewritten) under its own submodule;
this package only adds the installable surface and a unified CLI on top.

Tools currently in the toolkit:
    doctor              -- python_production_doctor: AST-based production
                            readiness diagnostics (stubs, placeholders,
                            silent failures, dependency cycles,
                            docstring/type-hint coverage, and more).
    structure           -- analyze_python_structure: class-by-class,
                            definition-by-definition AST index of a Python
                            source file, with line spans.
    pycache-clean       -- pycache_cleaner: configurable removal of
                            __pycache__ directories and *.pyc/*.pyo files
                            across one or more directory trees.
    init-test-harness   -- scaffolds the CONTRACT.md-governed single-test
                            harness (run_test.py) into a target repository.
"""

from __future__ import annotations

__version__ = "0.1.0"

__all__ = ["__version__"]
