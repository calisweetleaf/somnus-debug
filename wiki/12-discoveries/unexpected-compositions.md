# Unexpected Compositions

This page lists interactions between capabilities, both useful ones and conflicts.

## Findings

This section indexes the ledger entries in this category; the ledger holds full evidence and reproduction steps.

| ID | Finding | Evidence | Where to read more |
|---|---|---|---|
| [D-27](../DISCOVERY-LEDGER.md#d-27) | Verified chains: doctor JSON to delta gate, structure slices, findings to slices, ratchet, state reports as baselines | VERIFIED | [composition patterns](../08-extensions/composition-patterns.md) |
| [D-22](../DISCOVERY-LEDGER.md#d-22) | Conflict: onboard's `PYTHONPATH=src` makes own imports third-party; cycles go to 0 | VERIFIED | [agent workflows](../10-agent-usage/agent-workflows.md) |
| [D-13](../DISCOVERY-LEDGER.md#d-13) | Coupling: dispatcher imports pycache cleaner, so doctor needs PyYAML via `somnus-debug` | VERIFIED | [dependency map](../01-system/dependency-map.md) |
| [D-21](../DISCOVERY-LEDGER.md#d-21) | Gate interaction: severity remap in config silently relaxes `delta.py` | VERIFIED | [automation contracts](../10-agent-usage/automation-contracts.md) |

## Neutral compositions

This section records combinations tested and found to have no effect.

Running `pycache-clean` before doctor changes nothing: doctor never scans bytecode [VERIFIED, lane F `compositions.md`]. The scaffolded harness adds 9 serious findings to the next doctor scan unless dispositioned (D-15).

## Sources

- [Discovery Ledger](../DISCOVERY-LEDGER.md)
- [Agent findings](../_evidence/README.md)
