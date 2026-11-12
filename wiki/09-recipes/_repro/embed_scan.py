"""Scan a tree in-process with doctor's library classes: no files written, no logging changes."""
import json
import logging
import sys
from collections import Counter
from pathlib import Path

from somnus_debug.doctor.core import ConfigManager, ProjectScanner, dumps_json, exit_code_for_summary

root = Path(sys.argv[1]).resolve()
config = ConfigManager(Path(sys.argv[2]) if len(sys.argv) > 2 else None)
before = set(root.rglob("*"))
result = ProjectScanner(root, config).scan({})
summary = result.summary
print("files", summary.files_scanned, "issues", summary.total_issues,
      "critical", summary.critical_issues, "serious", summary.serious_issues, "score", summary.production_score)
print("by category", Counter(i.category for i in result.issues).most_common(4))
print("gate", config.config.severity_exit_level, "->", exit_code_for_summary(summary, config.config.severity_exit_level))
payload = json.loads(dumps_json(result))
print("json keys", sorted(payload))
print("new paths under root:", sorted(str(p) for p in set(root.rglob("*")) - before))
print("root handlers:", logging.getLogger().handlers, "cwd log:", Path("production_doctor.log").exists())
