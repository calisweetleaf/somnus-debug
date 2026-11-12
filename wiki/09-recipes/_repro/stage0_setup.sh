#!/usr/bin/env bash
# Stage 0: /tmp/w4 scratch: one standalone venv (repo + pytest), fixtures b1 (flat, lane-a files) and proj (src layout, own .venv, git).
source "$(dirname "$0")/env.sh"; set -u
exec > "$LOGS/stage0_setup.log" 2>&1
rm -rf "$W" && mkdir -p "$W" && cd "$W"
run "python3 -m venv venv && venv/bin/pip install -q '$REPO' pytest 2>&1 | { grep -v notice || true; }"
run "venv/bin/somnus-debug --version"
LA=$REPO/wiki/_evidence/agent-findings/lane-a-arch-api/fixture/proj
mkdir -p b1/proj b1/out
for f in $(cd "$LA" && find . -name '*.txt'); do mkdir -p "b1/proj/$(dirname "$f")"; cp "$LA/$f" "b1/proj/${f%.txt}"; done
cp -r b1/proj b1/proj_nobroken && rm b1/proj_nobroken/pkg/broken.py b1/proj_nobroken/pkg/todo_mod.py
mkdir -p proj/src/inventory proj/tests && cd proj
cat > src/inventory/__init__.py <<'P'
"""Inventory package: a tiny stock ledger used as a doctor fixture."""
P
cat > src/inventory/store.py <<'P'
"""Stock store with add and remove operations."""
import logging

logger = logging.getLogger(__name__)


def add_stock(levels: dict[str, int], sku: str, qty: int) -> int:
    """Add quantity to a SKU and return the new level."""
    current = levels.get(sku, 0)
    updated = current + qty
    if updated < 0:
        updated = 0
    levels[sku] = updated
    return updated


def parse_qty(raw: str) -> int:
    """Parse a quantity string, logging and re-raising on failure."""
    try:
        value = int(raw)
    except ValueError:
        logger.exception("bad quantity %s", raw)
        raise
    return value
P
cat > tests/test_store.py <<'P'
"""Tests for the stock store."""
from inventory.store import add_stock


def test_add_stock() -> None:
    """Adding stock increases the level."""
    levels: dict[str, int] = {}
    result = add_stock(levels, "a", 3)
    expected = 3
    assert result == expected
    assert levels["a"] == 3
P
printf '[project]\nname="inventory"\nversion="0"\n' > pyproject.toml
echo ".venv/" > .gitignore
git init -q && git add -A && git -c user.email=a@b -c user.name=x commit -qm init
run "python3 -m venv .venv && .venv/bin/pip install -q '$REPO' pytest 2>&1 | { grep -v notice || true; }"
run "find $W -maxdepth 3 -not -path '*/venv*' -not -path '*/.venv*' -not -path '*/.git*' | sort"
