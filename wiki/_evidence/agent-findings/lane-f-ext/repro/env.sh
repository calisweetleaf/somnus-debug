# Shared paths for lane-f repro stages. Source me.
export REPO=/workspace/projects/69c23182-5d69-4d5c-ae10-5cdad587b9d3/forge/somnus-debug
export LANE=$REPO/wiki/_evidence/agent-findings/lane-f-ext
export FK=$REPO/skills/somnus-debug-fieldkit
export W=/tmp/lane-f
export LOGS=$LANE/logs
export SD="$W/venv/bin/python -m somnus_debug.cli"           # standalone install (symlinked venv, has pytest)
export PRUN="env PYTHONPATH=$W/proj/src $W/proj/.venv/bin/python -m somnus_debug.cli"  # profile runner equivalent
REGRESS_RISKY='\n\ndef risky(cmd: str) -> int:\n    """Run a shell command string directly."""\n    import os\n    status = os.system(cmd)\n    checked = int(status)\n    result = checked + 0\n    return result\n'
log() { echo "$*" >> "$L"; }
