# somnus:metadata:v2
# somnus:
#   schema: "somnus://metadata/core/2.0.0"
#   id: "urn:somnus:artifact:01a19ace-78b6-72d5-bfdf-76b549e54d14"
#   revision: 1
#   title: "analyzepythonstructure: class/definition AST indexer"
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
#       - target_ref: "urn:somnus:artifact:01a19ace-78b6-72d5-bfdf-76b549e54d14"
#         aspects: ["content"]
#   time: {}
#   names:
#     slug: "analyzepythonstructure-class-definition-ast-indexer"
#   knowledge:
#     coverage: "artifact"
#     subjects: ["urn:somnus:artifact:01a19ace-78b6-72d5-bfdf-76b549e54d14"]
#   access:
#     visibility: "internal"
#     allowed_uses: ["archive", "search", "reason"]
#   ingestion:
#     disposition: "candidate"
#     body_role: "source"
# somnus:end
"""analyze_python_structure: class/definition AST indexer.

Original single-file implementation lives in ``core.py`` (moved verbatim
from the repo-root ``analyze_python_structure.py`` during packaging).
"""

from __future__ import annotations

from .core import build_index, main

__all__ = ["build_index", "main"]
