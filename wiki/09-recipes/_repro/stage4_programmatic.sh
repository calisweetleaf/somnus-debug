#!/usr/bin/env bash
# Stage 4 (programmatic): P1 embedded scan, P2 build_index on a stamped file, P3 in-process main() with isolation.
source "$(dirname "$0")/env.sh"; set -u
exec > "$LOGS/stage4_programmatic.log" 2>&1
rm -rf "$W/p" && mkdir -p "$W/p" && cd "$W/p" && cp -r "$W/b1/proj_nobroken" proj
echo "## P1 embedded scan"
run "$W/venv/bin/python $HERE/embed_scan.py proj"
run "ls"
echo; echo "## P2 build_index on a metadata-stamped file"
cp "$REPO/src/somnus_debug/test_harness/scaffold.py" stamped_scaffold.py
run "$W/venv/bin/python $HERE/index_any.py stamped_scaffold.py"
run "grep -n '^def scaffold' stamped_scaffold.py"
echo; echo "## P3 doctor main() in-process"
run "$W/venv/bin/python $HERE/inprocess_main.py proj work/out"
run "ls; ls work/out"
