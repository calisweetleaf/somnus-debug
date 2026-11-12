#!/usr/bin/env bash
# Stage 4b: dumps_json(ProjectScanner(...).scan({})) vs the CLI's --json-output for the same tree (needs stage 2 d.json).
source "$(dirname "$0")/env.sh"; set -u
exec > "$LOGS/stage4b_json_parity.log" 2>&1
cd "$W/p"
cat > parity.py <<'P'
import json
from pathlib import Path
from somnus_debug.doctor.core import ConfigManager, ProjectScanner, dumps_json
lib = json.loads(dumps_json(ProjectScanner(Path("/tmp/w4/b1/proj_nobroken"), ConfigManager(None)).scan({})))
cli = json.load(open("/tmp/w4/b1/out/d.json"))   # CLI scan of the same tree with init-config's cfg.yaml
for key in sorted(cli):
    print(key, "equal" if lib[key] == cli[key] else "differs")
P
run "$W/venv/bin/python parity.py"
