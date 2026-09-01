#!/usr/bin/env python3
"""Generate a class-by-class, definition-by-definition index for a Python file.

The analyzer is deliberately AST-only: it parses source without importing or
executing it, so optional runtime dependencies (Torch, CUDA extensions, model
packages, and so on) are not required.

Examples
--------
    python analyze_python_structure.py inference_optimizations.py
    python analyze_python_structure.py inference_optimizations.py \
        --update-doc INFERENCE_OPTIMIZATIONS_CLASS_INDEX.txt
    python analyze_python_structure.py some_module.py -o some_module_index.md
"""

from __future__ import annotations

import argparse
import ast
import re
import sys
from pathlib import Path
from typing import Iterable, Optional, Sequence


def _one_line(value: str) -> str:
    """Collapse source/docstring whitespace for compact index entries."""
    return re.sub(r"\s+", " ", value.strip())


def _doc_summary(node: ast.AST) -> Optional[str]:
    """Return the first paragraph of a node's docstring, if present."""
    body = getattr(node, "body", None)
    if not body or not isinstance(body[0], ast.Expr):
        return None
    value = body[0].value
    if not isinstance(value, ast.Constant) or not isinstance(value.value, str):
        return None
    paragraphs = value.value.strip().split("\n\n")
    return _one_line(paragraphs[0]) if paragraphs and paragraphs[0].strip() else None


def _unparse(node: ast.AST) -> str:
    """Unparse an AST node with a readable fallback for older Python versions."""
    try:
        return ast.unparse(node)
    except AttributeError:  # pragma: no cover - Python 3.9+ is expected.
        return ast.dump(node, annotate_fields=False)


def _signature(node: ast.FunctionDef | ast.AsyncFunctionDef) -> str:
    """Render a function signature without its body."""
    # Unparsing the whole FunctionDef is tempting, but it includes decorators
    # and splitting that result at the first colon corrupts annotations such
    # as ``Dict[str, Any]``.  Reconstruct the signature from the AST fields.
    arguments = _one_line(_unparse(node.args))
    returns = f" -> {_one_line(_unparse(node.returns))}" if node.returns else ""
    prefix = "async def" if isinstance(node, ast.AsyncFunctionDef) else "def"
    return f"{prefix} {node.name}({arguments}){returns}:"


def _decorators(node: ast.AST) -> list[str]:
    return [_one_line(_unparse(item)) for item in getattr(node, "decorator_list", [])]


def _line_span(node: ast.AST) -> str:
    start = getattr(node, "lineno", "?")
    end = getattr(node, "end_lineno", start)
    return f"{start}-{end}" if start != end else str(start)


def _class_header(node: ast.ClassDef) -> str:
    bases = [_one_line(_unparse(base)) for base in node.bases]
    return f"class `{node.name}`" + (f"({', '.join(bases)})" if bases else "")


def _definition_lines(
    node: ast.FunctionDef | ast.AsyncFunctionDef,
    *,
    indent: str,
    include_lines: bool,
) -> list[str]:
    signature = _signature(node)
    lines = [f"{indent}- `{signature}`"]
    if include_lines:
        lines[-1] += f" (lines {_line_span(node)})"
    for decorator in _decorators(node):
        lines.append(f"{indent}  - Decorator: `{decorator}`")
    doc = _doc_summary(node)
    if doc:
        lines.append(f"{indent}  - {doc}")
    return lines


def _iter_classes(body: Iterable[ast.stmt]) -> Iterable[ast.ClassDef]:
    """Yield classes in source order, including nested classes."""
    for node in body:
        if isinstance(node, ast.ClassDef):
            yield node
            yield from _iter_classes(node.body)


def _count_indexed_definitions(classes: Iterable[ast.ClassDef], module_functions: Iterable[ast.AST]) -> int:
    """Count the definitions that the renderer actually emits."""
    total = sum(1 for _ in module_functions)
    for node in classes:
        total += sum(
            isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef))
            for child in node.body
        )
        total += _count_indexed_definitions(
            (child for child in node.body if isinstance(child, ast.ClassDef)),
            (),
        )
    return total


def _render_class(
    node: ast.ClassDef,
    *,
    include_lines: bool,
    nested: bool = False,
    occurrence_label: str = "",
    occurrence_map: Optional[dict[int, str]] = None,
) -> list[str]:
    heading = "###" if nested else "##"
    lines = [f"{heading} {_class_header(node)}"]
    label = occurrence_label or (occurrence_map or {}).get(id(node), "")
    if label:
        lines[-1] += f" ({label})"
    if include_lines:
        lines[-1] += f" (lines {_line_span(node)})"
    doc = _doc_summary(node)
    lines.append(f"**Doc**: {doc or '_No class docstring._'}")

    definitions = [
        child
        for child in node.body
        if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef))
    ]
    if definitions:
        lines.append("")
        for definition in definitions:
            lines.extend(
                _definition_lines(
                    definition,
                    indent="",
                    include_lines=include_lines,
                )
            )
    else:
        lines.extend(["", "- _No methods._"])

    nested_classes = [child for child in node.body if isinstance(child, ast.ClassDef)]
    for child in nested_classes:
        lines.extend(
            [
                "",
                *(_render_class(
                    child,
                    include_lines=include_lines,
                    nested=True,
                    occurrence_map=occurrence_map,
                )),
            ]
        )
    return lines


def build_index(
    source: str,
    *,
    source_name: str,
    include_lines: bool = True,
    include_module_functions: bool = True,
) -> str:
    """Build a deterministic Markdown/plain-text index from Python source."""
    tree = ast.parse(source, filename=source_name, type_comments=True)
    classes = [node for node in tree.body if isinstance(node, ast.ClassDef)]
    all_classes = sorted(
        (node for node in ast.walk(tree) if isinstance(node, ast.ClassDef)),
        key=lambda node: (getattr(node, "lineno", 0), getattr(node, "col_offset", 0)),
    )
    rendered_class_ids = {id(node) for node in _iter_classes(tree.body)}
    scoped_classes = [node for node in all_classes if id(node) not in rendered_class_ids]
    by_name: dict[str, list[ast.ClassDef]] = {}
    for node in all_classes:
        by_name.setdefault(node.name, []).append(node)
    occurrence_map: dict[int, str] = {}
    for name_nodes in by_name.values():
        if len(name_nodes) > 1:
            for index, node in enumerate(name_nodes, start=1):
                occurrence_map[id(node)] = f"occurrence {index}/{len(name_nodes)}"
    module_functions = [
        node
        for node in tree.body
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
    ]
    total_definitions = _count_indexed_definitions(
        [*classes, *scoped_classes], module_functions
    )
    top_level_class_count = len(classes)
    nested_class_count = len(all_classes) - top_level_class_count

    lines = [
        f"# Class Index for `{Path(source_name).name}`",
        "",
        "Generated by `analyze_python_structure.py` using Python's AST; the source is never imported or executed.",
        "",
        f"- Class declarations: {len(all_classes)} ({top_level_class_count} top-level, {nested_class_count} nested)",
        f"- Definitions emitted (module-level functions and class methods): {total_definitions}",
        "",
    ]

    if classes:
        for index, node in enumerate(classes):
            if index:
                lines.append("")
            lines.extend(
                _render_class(
                    node,
                    include_lines=include_lines,
                    occurrence_map=occurrence_map,
                )
            )
    else:
        lines.append("_No classes found._")

    if scoped_classes:
        lines.extend(["", "## Classes nested in functions or other scopes", ""])
        for index, node in enumerate(scoped_classes):
            if index:
                lines.append("")
            lines.extend(
                _render_class(
                    node,
                    include_lines=include_lines,
                    nested=True,
                    occurrence_map=occurrence_map,
                )
            )

    if include_module_functions:
        lines.extend(["", "## Module-level functions", ""])
        if module_functions:
            for node in module_functions:
                lines.extend(
                    _definition_lines(node, indent="", include_lines=include_lines)
                )
        else:
            lines.append("_No module-level functions found._")

    return "\n".join(lines).rstrip() + "\n"


def _parse_args(argv: Optional[Sequence[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Index Python classes and their definitions without executing the module."
    )
    parser.add_argument("source", type=Path, help="Python source file to analyze")
    destination = parser.add_mutually_exclusive_group()
    destination.add_argument(
        "-o",
        "--output",
        type=Path,
        help="Write the generated index to this path",
    )
    destination.add_argument(
        "--update-doc",
        type=Path,
        metavar="PATH",
        help="Regenerate an existing documentation/index file at PATH",
    )
    parser.add_argument(
        "--no-line-numbers",
        action="store_true",
        help="Omit source line spans from headings and definition entries",
    )
    parser.add_argument(
        "--source-label",
        help="Name shown in the generated heading instead of the input filename",
    )
    parser.add_argument(
        "--no-module-functions",
        action="store_true",
        help="Only emit classes and their methods",
    )
    return parser.parse_args(argv)


def main(argv: Optional[Sequence[str]] = None) -> int:
    args = _parse_args(argv)
    try:
        source = args.source.read_text(encoding="utf-8")
        rendered = build_index(
            source,
            source_name=args.source_label or str(args.source),
            include_lines=not args.no_line_numbers,
            include_module_functions=not args.no_module_functions,
        )
    except (OSError, SyntaxError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    destination = args.output or args.update_doc
    try:
        if destination:
            destination.parent.mkdir(parents=True, exist_ok=True)
            destination.write_text(rendered, encoding="utf-8")
        else:
            sys.stdout.write(rendered)
    except OSError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
