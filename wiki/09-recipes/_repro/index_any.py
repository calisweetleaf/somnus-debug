"""Index a Python file with structure.build_index, blanking a somnus metadata header first.

build_index parses with type_comments=True, so header lines such as
'#     type: "source-code"' raise SyntaxError. Replacing the header block with
empty lines keeps every line number unchanged.
"""
import sys
from pathlib import Path

from somnus_debug.structure import build_index

path = Path(sys.argv[1])
lines = path.read_text(encoding="utf-8").splitlines(keepends=True)
try:
    build_index("".join(lines), source_name=path.name)
    print("plain build_index: ok")
except SyntaxError as error:
    print(f"plain build_index: SyntaxError: {error}")
if lines and lines[0].startswith("# somnus:metadata"):
    end = next(i for i, line in enumerate(lines) if line.startswith("# somnus:end"))
    lines[: end + 1] = ["\n"] * (end + 1)
print("\n".join(build_index("".join(lines), source_name=path.name).splitlines()[:14]))
