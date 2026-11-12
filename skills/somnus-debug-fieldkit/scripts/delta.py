#!/usr/bin/env python3
# somnus:metadata:v2
# somnus:
#   schema: "somnus://metadata/core/2.0.0"
#   id: "urn:somnus:artifact:01a19ace-76e1-74a0-b075-f99dac0c1363"
#   revision: 1
#   title: "Compare two somnus-debug doctor JSON reports and gate on regressions"
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
#       - target_ref: "urn:somnus:artifact:01a19ace-76e1-74a0-b075-f99dac0c1363"
#         aspects: ["content"]
#   time: {}
#   names:
#     slug: "compare-two-somnus-debug-doctor-json-reports-and-gate-on-regressions"
#   knowledge:
#     coverage: "artifact"
#     subjects: ["urn:somnus:artifact:01a19ace-76e1-74a0-b075-f99dac0c1363"]
#   access:
#     visibility: "internal"
#     allowed_uses: ["archive", "search", "reason"]
#   ingestion:
#     disposition: "candidate"
#     body_role: "source"
# somnus:end
"""Compare two somnus-debug doctor JSON reports and gate on regressions.

Usage:
    delta.py BASELINE.json LATEST.json [--dispositions dispositions.json] [--root DIR]
             [--allow-config-change] [--json]

Findings match on (category, file, symbol, message), not line number, so code
that only moved is "persisting", not new. A dispositions file records reviewed
findings that are accepted or false positives:

    [{"category": "security_risks", "file": "scripts/*.py", "symbol": "run",
      "reason": "argv list, no shell, fixed executable"}]

``file`` and ``symbol`` are fnmatch globs (``symbol`` optional); ``reason`` is
required. A disposition is *exact* when ``file`` and ``symbol`` are both given
without glob characters; any other entry is *broad*. A finding that persists
from the baseline is excused by any matching disposition. A finding that is new
in the latest scan is excused only by an exact disposition: a broad one never
absorbs a new finding, and a new serious/critical finding it would have matched
is reported as a regression with a note. Dispositions that excuse nothing are
reported as stale.

Both reports must carry the same ``config_hash``: a config change (for example a
severity remap) can hide a regression, so a mismatch is an input error unless
``--allow-config-change`` is given, in which case it is reported.

Coverage regression: the latest scan covers zero files, or a file present in
the baseline is missing from the latest report while it still exists on disk.

Exit codes: 0 clean, 1 new serious/critical finding, 2 coverage regression,
3 input error (usage, unreadable or malformed report or dispositions, config
change without --allow-config-change). Standard library only.
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
GLOB_CHARS = set("*?[")
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

    @property
    def exact(self) -> bool:
        """True when file and symbol name one place literally (no glob characters)."""
        return not (GLOB_CHARS & set(self.file)) and not (GLOB_CHARS & set(self.symbol))

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
    if not isinstance(data["issues"], list) or not isinstance(data["summary"], dict) or not isinstance(data["files"], list):
        raise InputError(f"{path}: issues and files must be lists and summary an object")
    for index, item in enumerate(data["files"]):
        if not isinstance(item, dict) or not isinstance(item.get("relative_path"), str):
            raise InputError(f"{path}: files[{index}] needs a string relative_path")
    for key in ("files_scanned", "total_issues", "critical_issues", "serious_issues", "minor_issues", "production_score"):
        if key in data["summary"] and (isinstance(data["summary"][key], bool) or not isinstance(data["summary"][key], int)):
            raise InputError(f"{path}: summary.{key} must be a number")
    try:
        findings(data)
    except (TypeError, ValueError, KeyError, AttributeError) as error:
        raise InputError(f"{path}: malformed issue ({type(error).__name__}: {error})") from error
    return data


def findings(report: dict) -> list[Finding]:
    """Extract findings from a report; raises on an issue lacking category or file_path."""
    result: list[Finding] = []
    for index, i in enumerate(report["issues"]):
        if not isinstance(i, dict) or not isinstance(i.get("category"), str) or not isinstance(i.get("file_path"), str):
            raise KeyError(f"issues[{index}] needs string category and file_path")
        result.append(Finding(i["category"], i["file_path"], str(i.get("symbol", "")), str(i.get("message", "")), str(i.get("severity", "info")), int(i.get("line_number", 0) or 0)))
    return result


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
    return multiset_split(left, right)[1]


def multiset_split(left: list[Finding], right: list[Finding]) -> tuple[list[Finding], list[Finding]]:
    """Split ``left`` into (also in ``right``, extra beyond ``right``) by identity count."""
    remaining = Counter(f.key for f in right)
    shared: list[Finding] = []
    extra: list[Finding] = []
    for finding in left:
        if remaining[finding.key]:
            remaining[finding.key] -= 1
            shared.append(finding)
        else:
            extra.append(finding)
    return shared, extra


def config_check(baseline: dict, latest: dict, allow_change: bool) -> dict:
    """Compare the reports' config_hash; raise InputError on a change unless allowed."""
    before, after = baseline.get("config_hash"), latest.get("config_hash")
    changed = not (isinstance(before, str) and before and before == after)
    if changed and not allow_change:
        raise InputError(
            f"config_hash differs (baseline {before or 'missing'}, latest {after or 'missing'}); a config change can hide "
            "regressions. Rescan both with the same config, or pass --allow-config-change to compare anyway."
        )
    return {"baseline": before, "latest": after, "changed": changed}


def compare(baseline: dict, latest: dict, dispositions: list[Disposition], root: Path, config: dict | None = None) -> dict:
    """Build the full comparison result."""
    base, last = findings(baseline), findings(latest)
    persisting, new = multiset_split(last, base)
    resolved = multiset_diff(base, last)
    used: set[int] = set()

    def excuse(finding: Finding, exact_only: bool) -> bool:
        """Return true when a usable disposition matches, remembering which ones excused something."""
        for index, disposition in enumerate(dispositions):
            if disposition.matches(finding) and (disposition.exact or not exact_only):
                used.add(index)
                return True
        return False

    dispositioned = [f for f in persisting if excuse(f, exact_only=False)]
    new_open: list[Finding] = []
    for finding in new:
        if excuse(finding, exact_only=True):
            dispositioned.append(finding)
        else:
            new_open.append(finding)
    # A broad disposition never excuses a new finding; say which ones it would have muted.
    broad_blocked = [
        (finding, disposition) for finding in new_open
        for disposition in dispositions if not disposition.exact and disposition.matches(finding)
    ]
    base_files = {f["relative_path"] for f in baseline["files"]}
    last_files = {f["relative_path"] for f in latest["files"]}
    dropped = sorted(p for p in base_files - last_files if (root / p).exists())
    deleted = sorted(p for p in base_files - last_files if not (root / p).exists())
    regressions = [f for f in new_open if f.severity in GATING]
    coverage_failure = latest["summary"].get("files_scanned", 0) == 0 or bool(dropped)
    return {
        "baseline": baseline["summary"], "latest": latest["summary"],
        "baseline_run": baseline.get("run_id", "?"), "latest_run": latest.get("run_id", "?"),
        "new": new_open, "resolved": resolved, "persisting": len(persisting),
        "dispositioned": dispositioned, "broad_blocked": broad_blocked,
        "config_hash": config or {"baseline": baseline.get("config_hash"), "latest": latest.get("config_hash"),
                                  "changed": baseline.get("config_hash") != latest.get("config_hash")},
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
    if result["config_hash"]["changed"]:
        out += ["", f"**Config changed** (`{result['config_hash']['baseline']}` -> `{result['config_hash']['latest']}`), allowed by --allow-config-change: severities and coverage may differ between the two scans."]
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
    if result["broad_blocked"]:
        out += ["", "## New findings a broad disposition would have excused (not excused: broad entries only cover baseline findings)",
                *[f"- {f.severity} `{f.category}` `{f.file}:{f.line}` `{f.symbol}` matched broad `{d.file}` `{d.symbol}` ({d.reason}); "
                  + ("counted as a regression" if f.severity in GATING else "listed as new") for f, d in result["broad_blocked"]]]
    if result["stale_dispositions"]:
        out += ["", "## Stale dispositions (excuse nothing; remove or fix)", *[f"- `{d.category}` `{d.file}` `{d.symbol}`: {d.reason}" for d in result["stale_dispositions"]]]
    return "\n".join(out) + "\n"


def as_json(result: dict) -> str:
    """Render the comparison as JSON."""
    def item(f: Finding) -> dict:
        """Serialize one finding for JSON output."""
        return {"severity": f.severity, "category": f.category, "file": f.file, "line": f.line, "symbol": f.symbol, "message": f.message}
    payload = {k: v for k, v in result.items() if k not in {"new", "resolved", "dispositioned", "regressions", "stale_dispositions", "broad_blocked"}}
    payload.update({k: [item(f) for f in result[k]] for k in ("new", "resolved", "regressions")})
    payload["dispositioned"] = len(result["dispositioned"])
    payload["stale_dispositions"] = [vars(d) for d in result["stale_dispositions"]]
    payload["broad_blocked"] = [{"finding": item(f), "disposition": vars(d)} for f, d in result["broad_blocked"]]
    return json.dumps(payload, indent=2) + "\n"


class Parser(argparse.ArgumentParser):
    """ArgumentParser whose usage errors exit 3 (input error), keeping 2 for coverage regression."""

    def error(self, message: str) -> None:  # type: ignore[override]
        """Print usage and the error to stderr, then exit 3."""
        self.print_usage(sys.stderr)
        self.exit(3, f"{self.prog}: error: {message}\n")


EPILOG = """exit codes:
  0  clean: no new serious/critical finding, coverage intact
  1  regression: a new serious/critical finding not excused by an exact disposition
  2  coverage regression: latest scanned zero files, or a baseline file still on
     disk is no longer scanned
  3  input error: bad arguments, unreadable or malformed report or dispositions,
     or config_hash differs without --allow-config-change
"""


def main(argv: list[str] | None = None) -> int:
    """Entry point; see the module docstring for exit codes."""
    parser = Parser(description=__doc__.splitlines()[0], epilog=EPILOG, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("baseline", type=Path)
    parser.add_argument("latest", type=Path)
    parser.add_argument("--dispositions", type=Path, help="JSON list of reviewed findings (category, file, symbol?, reason)")
    parser.add_argument("--root", type=Path, help="project root for coverage checks (default: latest report's project_root)")
    parser.add_argument("--allow-config-change", action="store_true", help="compare reports whose config_hash differs (reported, not an error)")
    parser.add_argument("--json", action="store_true", help="emit JSON instead of Markdown")
    args = parser.parse_args(argv)
    try:
        baseline, latest = load_report(args.baseline), load_report(args.latest)
        dispositions = load_dispositions(args.dispositions if args.dispositions and args.dispositions.exists() else None)
        if args.dispositions and not args.dispositions.exists():
            print(f"note: {args.dispositions} not found; continuing without dispositions", file=sys.stderr)
        config = config_check(baseline, latest, args.allow_config_change)
    except InputError as error:
        print(f"error: {error}", file=sys.stderr)
        return 3
    if config["changed"]:
        print(f"note: config_hash differs ({config['baseline']} -> {config['latest']}); compared anyway (--allow-config-change)", file=sys.stderr)
    root = (args.root or Path(str(latest.get("project_root", ".")))).resolve()
    result = compare(baseline, latest, dispositions, root, config)
    sys.stdout.write(as_json(result) if args.json else render(result))
    return result["exit"]


if __name__ == "__main__":
    raise SystemExit(main())
