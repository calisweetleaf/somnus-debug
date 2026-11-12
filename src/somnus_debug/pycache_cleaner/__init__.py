# somnus:metadata:v2
# somnus:
#   schema: "somnus://metadata/core/2.0.0"
#   id: "urn:somnus:artifact:01a19ace-7863-705c-98f8-6ae4b578dfd3"
#   revision: 1
#   title: "pycachecleaner: configurable pycache/.pyc/.pyo removal"
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
#       - target_ref: "urn:somnus:artifact:01a19ace-7863-705c-98f8-6ae4b578dfd3"
#         aspects: ["content"]
#   time: {}
#   names:
#     slug: "pycachecleaner-configurable-pycache-pyc-pyo-removal"
#   knowledge:
#     coverage: "artifact"
#     subjects: ["urn:somnus:artifact:01a19ace-7863-705c-98f8-6ae4b578dfd3"]
#   access:
#     visibility: "internal"
#     allowed_uses: ["archive", "search", "reason"]
#   ingestion:
#     disposition: "candidate"
#     body_role: "source"
# somnus:end
"""pycache_cleaner: configurable __pycache__/*.pyc/*.pyo removal.

Original single-file implementation lives in ``core.py`` (moved verbatim
from the repo-root ``pycache_cleaner.py`` during packaging).
"""

from __future__ import annotations

from .core import main

__all__ = ["main"]
