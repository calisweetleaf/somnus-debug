#!/usr/bin/env python3
"""Compare two somnus-debug doctor JSON reports and gate on regressions.

Usage:
    delta.py BASELINE.json LATEST.json [--dispositions dispositions.json] [--root DIR] [--json]

Findings match on (category, file, symbol, message), not line number, so code
that only moved is "persisting", not new. A dispositions file records reviewed
findings that are accepted or false positives:

    [{"category": "security_risks", "file": "scripts/*.py", "symbol": "run",
      "reason": "argv list, no shell, fixed executable"}]

``file`` and ``symbol`` are fnmatch globs (``symbol`` optional); ``reason`` is
required. Dispositioned findings never count as regressions, and dispositions
that match nothing are reported as stale.

Coverage regression: the latest scan covers zero files, or a file present in
the baseline is missing from the latest report while it still exists on disk.

Exit codes: 0 clean, 1 new serious/critical finding, 2 coverage regression,
3 input error. Standard library only.
"""

from __future__ import annotations

import argparse
import fnmatch
import json
import sys
from collections import Counter
from dataclasses import dataclass
from pathlib import Path

SEVERITY_ORDER = ("critical", "serious", "minor", "info")
GATING = {"critical", "serious"}


@dataclass(frozen=True)
class Finding:
    """One doctor issue reduced to its line-independent identity."""

    category: str
    file: str
    symbol: str
    message: str
    severity: str
    line: int

    @property
    def key(self) -> tuple[str, str, str, str]:
        """Identity used for matching across runs."""
        return (self.category, self.file, self.symbol, self.message)


@dataclass(frozen=True)
class Disposition:
    """A reviewed, accepted finding pattern."""

    category: str
    file: str
    symbol: str
    reason: str

    def matches(self, finding: Finding) -> bool:
        """Return true when this disposition covers ``finding``."""
        return (
            self.category == finding.category
            and fnmatch.fnmatchcase(finding.file, self.file)
            and fnmatch.fnmatchcase(finding.symbol, self.symbol)
        )


class InputError(Exception):
    """Raised when a report or dispositions file cannot be used."""


def load_report(path: Path) -> dict:
    """Load a doctor JSON report and check the fields delta needs."""
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise InputError(f"cannot read report {path}: {error}") from error
    if not isinstance(data, dict) or "issues" not in data or "summary" not in data or "files" not in data:
        raise InputError(f"{path} is not a somnus-debug doctor JSON report (needs issues, summary, files)")
    return data


def findings(report: dict) -> list[Finding]:
    """Extract findings from a report."""
    return [
        Finding(i["category"], i["file_path"], i.get("symbol", ""), i.get("message", ""), i.get("severity", "info"), int(i.get("line_number", 0)))
        for i in report["issues"]
    ]


def load_dispositions(path: Path | None) -> list[Disposition]:
    """Load and validate a dispositions file."""
    if path is None:
        return []
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise InputError(f"cannot read dispositions {path}: {error}") from error
    if not isinstance(raw, list):
        raise InputError(f"{path} must contain a JSON list")
    result: list[Disposition] = []
    for index, item in enumerate(raw):
        if not isinstance(item, dict) or not all(isinstance(item.get(k), str) and item.get(k) for k in ("category", "file", "reason")):
            raise InputError(f"{path}[{index}] needs non-empty string category, file, and reason")
        result.append(Disposition(item["category"], item["file"], item.get("symbol") or "*", item["reason"]))
    return result


def multiset_diff(left: list[Finding], right: list[Finding]) -> list[Finding]:
    """Return findings in ``left`` whose identity count exceeds ``right``."""
    remaining = Counter(f.key for f in right)
    extra: list[Finding] = []
    for finding in left:
        if remaining[finding.key]:
            remaining[finding.key] -= 1
        else:
            extra.append(finding)
    return extra


def compare(baseline: dict, latest: dict, dispositions: list[Disposition], root: Path) -> dict:
    """Build the full comparison result."""
    base, last = findings(baseline), findings(latest)
    new = multiset_diff(last, base)
    resolved = multiset_diff(base, last)
    used: set[int] = set()

    def covered(finding: Finding) -> bool:
        """Return true when a disposition matches, remembering which ones were used."""
        for index, disposition in enumerate(dispositions):
            if disposition.matches(finding):
                used.add(index)
                return True
        return False

    dispositioned = [f for f in last if covered(f)]
    new_open = [f for f in new if not covered(f)]
    base_files = {f["relative_path"] for f in baseline["files"]}
    last_files = {f["relative_path"] for f in latest["files"]}
    dropped = sorted(p for p in base_files - last_files if (root / p).exists())
    deleted = sorted(p for p in base_files - last_files if not (root / p).exists())
    regressions = [f for f in new_open if f.severity in GATING]
    coverage_failure = latest["summary"].get("files_scanned", 0) == 0 or bool(dropped)
    return {
        "baseline": baseline["summary"], "latest": latest["summary"],
        "baseline_run": baseline.get("run_id", "?"), "latest_run": latest.get("run_id", "?"),
        "new": new_open, "resolved": resolved, "persisting": len(last) - len(new),
        "dispositioned": dispositioned,
        "stale_dispositions": [d for i, d in enumerate(dispositions) if i not in used],
        "regressions": regressions, "uncovered_files": dropped, "deleted_files": deleted,
        "added_files": sorted(last_files - base_files), "coverage_failure": coverage_failure,
        "exit": 2 if coverage_failure else (1 if regressions else 0),
    }


def render(result: dict) -> str:
    """Render the comparison as Markdown."""
    b, l = result["baseline"], result["latest"]
    rows = [("files scanned", "files_scanned"), ("total", "total_issues"), ("critical", "critical_issues"),
            ("serious", "serious_issues"), ("minor", "minor_issues"), ("production score", "production_score")]
    out = [f"# doctor delta: {result['baseline_run']} -> {result['latest_run']}", "", "| Metric | Baseline | Latest | Change |", "|---|---|---|---|"]
    for label, key in rows:
        before, after = b.get(key, 0), l.get(key, 0)
        out.append(f"| {label} | {before} | {after} | {after - before:+d} |")
    verdict = {0: "CLEAN: no new serious/critical findings, coverage intact.", 1: "REGRESSION: new serious/critical findings.", 2: "COVERAGE REGRESSION: fix scan coverage before trusting this delta."}[result["exit"]]
    out += ["", f"**{verdict}**", "",
            f"New (open): {len(result['new'])} · Resolved: {len(result['resolved'])} · Persisting: {result['persisting']} · Dispositioned: {len(result['dispositioned'])}"]
    if result["uncovered_files"]:
        out += ["", "## Files dropped from coverage (still on disk)", *[f"- `{p}`" for p in result["uncovered_files"]]]
    if result["deleted_files"]:
        out += ["", "## Files deleted since baseline", *[f"- `{p}`" for p in result["deleted_files"]]]
    if result["added_files"]:
        out += ["", "## Files newly covered", *[f"- `{p}`" for p in result["added_files"]]]
    for title, items in (("New findings", result["new"]), ("Resolved findings", result["resolved"])):
        if not items:
            continue
        out += ["", f"## {title}", "", "| Severity | Category | Location | Symbol | Message |", "|---|---|---|---|---|"]
        for f in sorted(items, key=lambda x: (SEVERITY_ORDER.index(x.severity) if x.severity in SEVERITY_ORDER else 9, x.file, x.line)):
            out.append(f"| {f.severity} | `{f.category}` | `{f.file}:{f.line}` | `{f.symbol}` | {f.message} |")
    if result["stale_dispositions"]:
        out += ["", "## Stale dispositions (match nothing; remove or fix)", *[f"- `{d.category}` `{d.file}` `{d.symbol}`: {d.reason}" for d in result["stale_dispositions"]]]
    return "\n".join(out) + "\n"


def as_json(result: dict) -> str:
    """Render the comparison as JSON."""
    def item(f: Finding) -> dict:
        """Serialize one finding for JSON output."""
        return {"severity": f.severity, "category": f.category, "file": f.file, "line": f.line, "symbol": f.symbol, "message": f.message}
    payload = {k: v for k, v in result.items() if k not in {"new", "resolved", "dispositioned", "regressions", "stale_dispositions"}}
    payload.update({k: [item(f) for f in result[k]] for k in ("new", "resolved", "regressions")})
    payload["dispositioned"] = len(result["dispositioned"])
    payload["stale_dispositions"] = [vars(d) for d in result["stale_dispositions"]]
    return json.dumps(payload, indent=2) + "\n"


def main(argv: list[str] | None = None) -> int:
    """Entry point; see the module docstring for exit codes."""
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("baseline", type=Path)
    parser.add_argument("latest", type=Path)
    parser.add_argument("--dispositions", type=Path, help="JSON list of reviewed findings (category, file, symbol?, reason)")
    parser.add_argument("--root", type=Path, help="project root for coverage checks (default: latest report's project_root)")
    parser.add_argument("--json", action="store_true", help="emit JSON instead of Markdown")
    args = parser.parse_args(argv)
    try:
        baseline, latest = load_report(args.baseline), load_report(args.latest)
        dispositions = load_dispositions(args.dispositions if args.dispositions and args.dispositions.exists() else None)
        if args.dispositions and not args.dispositions.exists():
            print(f"note: {args.dispositions} not found; continuing without dispositions", file=sys.stderr)
    except InputError as error:
        print(f"error: {error}", file=sys.stderr)
        return 3
    root = (args.root or Path(latest.get("project_root", "."))).resolve()
    result = compare(baseline, latest, dispositions, root)
    sys.stdout.write(as_json(result) if args.json else render(result))
    return result["exit"]


if __name__ == "__main__":
    raise SystemExit(main())
