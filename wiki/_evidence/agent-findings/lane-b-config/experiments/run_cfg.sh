#!/bin/bash
# usage: run_cfg.sh LABEL 'yaml text' [extra args]
label=$1; text=$2; shift 2
d=/tmp/lane-b/cfg/$label; rm -rf $d; mkdir -p $d; cp -r /tmp/lane-b/proj/pkg $d/
printf '%b' "$text" > $d/c.yaml
cd $d
out=$(python3 -m somnus_debug.cli doctor scan . --no-state -c c.yaml "$@" 2>&1); ec=$?
echo "[$label] exit=$ec :: $(echo "$out" | head -3 | tr '\n' ' ' | cut -c1-330)"
