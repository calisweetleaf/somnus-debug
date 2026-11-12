# Implementation Discrepancies

This page lists every place where source, tests, installed package, PyPI, operator notes, and docs disagree.

## Findings

This section indexes the ledger entries in this category; the ledger holds full evidence and reproduction steps.

| ID | Finding | Evidence | Where to read more |
|---|---|---|---|
| [D-01](../DISCOVERY-LEDGER.md#d-01) | STATE.md says structure fix landed in src; it is only in the root duplicate; smoke 10/12 not 12/12 | DISCREPANCY, VERIFIED | [verification results](../11-verification/verification-results.md) |
| [D-02](../DISCOVERY-LEDGER.md#d-02) | README/QUICKSTART imply config auto-load; none exists | DISCREPANCY, VERIFIED | [precedence](../06-configuration/precedence.md) |
| [D-05](../DISCOVERY-LEDGER.md#d-05) | MANUAL lists test gaps; never emitted | DISCREPANCY, VERIFIED | [known limitations](../11-verification/known-limitations.md) |
| [D-09](../DISCOVERY-LEDGER.md#d-09) | Rollback restores only the alias | DISCREPANCY, VERIFIED | [state transitions](../07-internals/state-transitions.md) |
| [D-14](../DISCOVERY-LEDGER.md#d-14) | pycache docstring promises Windows long paths and `$VAR` expansion; no code | DISCREPANCY, SOURCE-CONFIRMED | [configuration pitfalls](../06-configuration/configuration-pitfalls.md) |
| [D-15](../DISCOVERY-LEDGER.md#d-15) | Harness described as portable; template is a cargo test | DISCREPANCY, VERIFIED | [tooling integration](../05-cli-and-tools/tooling-integration.md) |
| [D-20](../DISCOVERY-LEDGER.md#d-20) | onboarding reference documents `--python`, which rejects symlinked venvs; bad config exit 1 not 2 | DISCREPANCY, VERIFIED | [failure recovery](../10-agent-usage/failure-recovery.md) |
| [D-23](../DISCOVERY-LEDGER.md#d-23) | PyPI default_config.yaml has old MCP globs; version in two places | DISCREPANCY, VERIFIED | [package layout](../02-installation/package-layout.md) |
| [D-25](../DISCOVERY-LEDGER.md#d-25) | MANUAL: JSON only if requested; always written | DISCREPANCY, VERIFIED | [input/output contracts](../05-cli-and-tools/input-output-contracts.md) |
| [D-28](../DISCOVERY-LEDGER.md#d-28) | Root doctor duplicate lacks the SQLite fallback | DISCREPANCY, VERIFIED | [fallbacks](../07-internals/fallbacks.md) |

## Smaller documentation discrepancies

This section lists doc-only mismatches found by lane F's line-by-line reconciliation ([doc-reconciliation.md](../_evidence/agent-findings/lane-f-ext/doc-reconciliation.md)).

- `docs/OPSEC.md` is linked from README and MANUAL and does not exist. `STATE.md` and `PLAN.md` exist in this upload but are gitignored upstream, so their links are dead on GitHub and PyPI.
- MANUAL's `src/**/*.py` example skips files directly under `src/`; its pycache `node_modules/*` exclude never matches.
- MANUAL says `init-config` output has comments; it does not. It says "10 tests"; there are 12. A structure "written to" message is described that never prints.
- MANUAL says each `core.py` is unmodified in substance from its root original; structure and doctor differ (D-01, D-28).
- `docs/AGENTS_APPENDIX.md` recommends `pipx install`; the fieldkit install reference recommends installing into the project venv.

## Sources

- [Discovery Ledger](../DISCOVERY-LEDGER.md)
- [Agent findings](../_evidence/README.md)
