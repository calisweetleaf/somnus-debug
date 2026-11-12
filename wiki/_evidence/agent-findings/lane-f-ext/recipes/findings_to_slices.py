"""Recipe C2b: delta.py --json -> doctor JSON code_map -> source slices to read.

For each NEW finding in a delta.py --json result, look up the enclosing
function/class span in the latest doctor JSON report (files[].functions /
files[].classes carry qualname, line_number, end_line_number) and print the
source an agent needs to read, instead of the whole file. No structure call
needed: doctor's JSON already contains a project-wide definition index.
Usage: findings_to_slices.py <latest.json> <delta.json> [--all]   (--all: include minor)
Exit 2 if any scanned file's sha256 no longer matches the report's file_hash.
"""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path


def main(argv: list[str]) -> int:
    """Print source slices for new findings; exit 0, or 2 on a stale report."""
    report = json.loads(Path(argv[0]).read_text(encoding="utf-8"))
    delta = json.loads(Path(argv[1]).read_text(encoding="utf-8"))
    include_minor = "--all" in argv
    root = Path(report["project_root"])
    spans: dict[tuple[str, str], tuple[int, int]] = {}
    stale = []
    for file in report["files"]:
        on_disk = root / file["relative_path"]
        if file.get("file_hash") and (not on_disk.exists() or hashlib.sha256(on_disk.read_bytes()).hexdigest() != file["file_hash"]):
            stale.append(file["relative_path"])
        for item in [*file.get("functions", []), *file.get("classes", [])]:
            spans[(file["relative_path"], item["qualname"])] = (item["line_number"], item["end_line_number"])
    if stale:
        print(f"STALE REPORT: files changed since the scan: {stale}. Rescan first.", file=sys.stderr)
        return 2
    for finding in delta["new"]:
        if not include_minor and finding["severity"] not in {"critical", "serious"}:
            continue
        span = spans.get((finding["file"], finding["symbol"]))
        print(f"### {finding['severity']} {finding['category']} {finding['file']}:{finding['line']} {finding['symbol']}: {finding['message']}")
        if span is None:
            print("    (no definition span for this symbol; read around the line)")
            continue
        lines = (root / finding["file"]).read_text(encoding="utf-8").splitlines()
        print("\n".join(f"{n:>5}  {lines[n - 1]}" for n in range(span[0], span[1] + 1)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
