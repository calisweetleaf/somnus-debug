"""Extension probe E-1: add a doctor detector WITHOUT editing somnus_debug.

There is no registry, entry point, or hook. This works only by subclassing the
private CodeQualityVisitor and rebinding the module global that
FileAnalyzer.analyze() looks up at call time (doctor/core.py:1542). It is a
monkeypatch against internals, not a supported API: any refactor can break it.

Custom category severity comes from the normal config: parse_severities()
accepts any category name (doctor/core.py:769-779); unmapped categories default
to MINOR (core.py:792-794). Usage:
    python ext_custom_detector.py <project_root> <config.yaml> <out_prefix>
"""
from __future__ import annotations

import ast
import sys

from somnus_debug.doctor import core


class PrintCallVisitor(core.CodeQualityVisitor):
    """CodeQualityVisitor plus a `print_calls` category."""

    def visit_Call(self, node: ast.Call) -> None:  # noqa: N802 (ast API)
        """Flag bare print() calls, then run the stock call checks."""
        if core.dotted_name(node.func) == "print":
            self.issues.append(self.issue_factory.create(
                "print_calls", node.lineno, node.col_offset, self._current_symbol(),
                "print() call in library code.", "Use the module logger.", {"call": "print"}))
        super().visit_Call(node)


core.CodeQualityVisitor = PrintCallVisitor  # rebinding the global is the whole "extension point"

if __name__ == "__main__":
    root, config, out = sys.argv[1:4]
    raise SystemExit(core.main(["scan", root, "-c", config, "--no-state", "-o", f"{out}.md", "--json-output", f"{out}.json"]))
