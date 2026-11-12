# somnus:metadata:v2
# somnus:
#   schema: "somnus://metadata/core/2.0.0"
#   id: "urn:somnus:artifact:01a19ace-77c0-70ee-ba80-5883808d1cd3"
#   revision: 1
#   title: "Python Production Doctor: AST-based production-readiness diagnostics"
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
#       - target_ref: "urn:somnus:artifact:01a19ace-77c0-70ee-ba80-5883808d1cd3"
#         aspects: ["content"]
#   time: {}
#   names:
#     slug: "python-production-doctor-ast-based-production-readiness-diagnostics"
#   knowledge:
#     coverage: "artifact"
#     subjects: ["urn:somnus:artifact:01a19ace-77c0-70ee-ba80-5883808d1cd3"]
#   access:
#     visibility: "internal"
#     allowed_uses: ["archive", "search", "reason"]
#   ingestion:
#     disposition: "candidate"
#     body_role: "source"
# somnus:end
"""Python Production Doctor: AST-based production-readiness diagnostics.

Original single-file implementation lives in ``core.py`` (moved verbatim
from the repo-root ``python_production_doctor.py`` during packaging; see
that module's docstring for provenance and modification history). This
``__init__`` only re-exports the entry point used by the toolkit CLI.
"""

from __future__ import annotations

from .core import main

__all__ = ["main"]
