"""Recipe C2: structure index -> targeted reading.

Runs `somnus-debug structure <file>` (stdout only, writes nothing), parses the
"(lines A-B)" spans, and prints only the source of the requested definitions.
Usage: structure_slice.py <runner-python> <file.py> <name> [<name> ...]
Names match the bare def/class name shown in the index (methods appear as
`def name(` under their class heading).
"""
from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

ENTRY = re.compile(r"`(?:async def|def|class) (\w+)[^`]*`.*?\(lines (\d+)-(\d+)\)")


def main(argv: list[str]) -> int:
    """Print the source spans of the named definitions; exit 1 if any is missing."""
    python, source, names = argv[0], Path(argv[1]), set(argv[2:])
    proc = subprocess.run([python, "-m", "somnus_debug.cli", "structure", str(source)], capture_output=True, text=True, check=False)
    if proc.returncode != 0:
        print(proc.stderr, file=sys.stderr)
        return 2
    lines = source.read_text(encoding="utf-8").splitlines()
    found: set[str] = set()
    for match in ENTRY.finditer(proc.stdout):
        name, start, end = match.group(1), int(match.group(2)), int(match.group(3))
        if name in names:
            found.add(name)
            print(f"--- {source}:{start}-{end} ({name})")
            print("\n".join(f"{n:>5}  {lines[n - 1]}" for n in range(start, end + 1)))
    missing = names - found
    if missing:
        print(f"not in index: {sorted(missing)}", file=sys.stderr)
    return 1 if missing else 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
