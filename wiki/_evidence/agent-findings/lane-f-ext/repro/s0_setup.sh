#!/usr/bin/env bash
# Stage 0: scratch workspace, three installs of the repo (non-editable), fixture project.
source "$(dirname "$0")/env.sh"; set -u
rm -rf $W && mkdir -p $W && cd $W
L=$LOGS/s0_setup.log; : > $L
python3 -m venv venv && venv/bin/pip install -q "$REPO" pytest >>$L 2>&1; log "venv install exit=$?"
python3 -m venv --copies venvc && venvc/bin/pip install -q "$REPO" >>$L 2>&1; log "venvc (--copies) install exit=$?"
mkdir -p proj/src/calc proj/tests && cd proj
cat > src/calc/__init__.py <<'P'
"""Calculator package with a small arithmetic surface."""
P
cat > src/calc/ops.py <<'P'
"""Arithmetic operations used by the calculator package."""
import logging

logger = logging.getLogger(__name__)


def add(a: int, b: int) -> int:
    """Add two integers and clamp negatives to zero."""
    total = a + b
    if total < 0:
        total = 0
    checked = int(total)
    return checked


def parse(value: str) -> int:
    """Parse an integer and record failures properly."""
    try:
        parsed = int(value)
    except ValueError:
        logger.exception("bad value %s", value)
        raise
    return parsed
P
cat > tests/test_ops.py <<'P'
"""Tests for the arithmetic operations module."""
from calc.ops import add


def test_add() -> None:
    """Check that add sums two values correctly."""
    result = add(1, 2)
    expected = 3
    assert result == expected
    assert isinstance(result, int)
P
printf '[project]\nname="calc"\nversion="0"\n' > pyproject.toml
echo ".venv/" > .gitignore
git init -q && git add -A && git -c user.email=a@b -c user.name=x commit -qm init
python3 -m venv .venv && .venv/bin/pip install -q "$REPO" >>$L 2>&1; log "proj/.venv install exit=$?"
log "venv/bin/python -> $(readlink venv/bin/python 2>/dev/null || readlink $W/venv/bin/python)"
log "$(ls -l $W/venv/bin/python $W/venvc/bin/python)"
log "somnus-debug --version: $($W/venv/bin/somnus-debug --version)"
grep -v "notice" $L > $L.tmp; mv $L.tmp $L
