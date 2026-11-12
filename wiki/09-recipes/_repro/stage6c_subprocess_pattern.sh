#!/usr/bin/env bash
# Stage 6c: the agent subprocess wrapper from 10-agent-usage/programmatic-invocation.md (needs stages 2-5).
source "$(dirname "$0")/env.sh"; set -u
exec > "$LOGS/stage6c_subprocess_pattern.log" 2>&1
rm -rf "$W/s6c" && mkdir -p "$W/s6c" && cd "$W/s6c"
run "python3 $HERE/doctor_scan_subprocess.py $W/proj $W/proj/.venv/bin/python $W/proj/.somnus-debug/python_doctor.yaml out"
cp "$W/proj/.somnus-debug/python_doctor.yaml" bad.yaml && sed -i 's/^severity_exit_level: .*/severity_exit_level: "bogus"/' bad.yaml
run "python3 $HERE/doctor_scan_subprocess.py $W/proj $W/proj/.venv/bin/python bad.yaml out2"
run "ls; ls out; git -C $W/proj status --short"
