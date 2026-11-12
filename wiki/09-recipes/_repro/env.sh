# Shared settings for the 09-recipes repro stages. Source me.
export REPO=/workspace/projects/69c23182-5d69-4d5c-ae10-5cdad587b9d3/forge/somnus-debug
export FK=$REPO/skills/somnus-debug-fieldkit
export REC=$REPO/wiki/_evidence/agent-findings/lane-f-ext/recipes
export HERE=$REPO/wiki/09-recipes/_repro
export LOGS=$HERE/logs
export W=/tmp/w4
export PYTHONDONTWRITEBYTECODE=1
set -o pipefail   # a pipeline reports the first failing command, so [exit=N] is the tool's code
export SD="$W/venv/bin/python -m somnus_debug.cli"
# run CMD...: echo the command, run it, print its exit code (the log is the evidence)
run() { echo "\$ $*"; eval "$@"; local rc=$?; echo "[exit=$rc]"; return 0; }
