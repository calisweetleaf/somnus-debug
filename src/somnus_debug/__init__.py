# somnus:metadata:v2
# somnus:
#   schema: "somnus://metadata/core/2.0.0"
#   id: "urn:somnus:artifact:01a19ace-7779-77f9-bb91-8c2021b92bd6"
#   revision: 1
#   title: "somnusdebug: Somnus Sovereign Systems' Python developer toolkit"
#   classification:
#     category: "engineering"
#     type: "source-code"
#     role: "informative"
#     scope: "component"
#     tags: []
#   lifecycle:
#     status: "draft"
#   authority:
#     standing: "candidate"
#     scopes:
#       - target_ref: "urn:somnus:artifact:01a19ace-7779-77f9-bb91-8c2021b92bd6"
#         aspects: ["content"]
#   time: {}
#   names:
#     slug: "somnusdebug-somnus-sovereign-systems-python-developer-toolkit"
#   knowledge:
#     coverage: "artifact"
#     subjects: ["urn:somnus:artifact:01a19ace-7779-77f9-bb91-8c2021b92bd6"]
#   access:
#     visibility: "internal"
#     allowed_uses: ["archive", "search", "reason"]
#   ingestion:
#     disposition: "candidate"
#     body_role: "source"
# somnus:end
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

from importlib import metadata as _metadata

# The single source of truth for the version is pyproject.toml; an installed
# distribution exposes it through its metadata.  Running from a source tree
# (PYTHONPATH=src, no install) has no distribution, so fall back to the
# release this tree was cut from.
_SOURCE_TREE_VERSION = "0.1.0"

try:
    __version__ = _metadata.version("somnus-debug")
except _metadata.PackageNotFoundError:
    __version__ = _SOURCE_TREE_VERSION

__all__ = ["__version__"]
