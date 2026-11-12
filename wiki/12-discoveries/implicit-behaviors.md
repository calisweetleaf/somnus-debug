# Implicit Behaviors

This page lists what the tools do without being asked: files they create, global state they change, and environment they read.

## Findings

This section indexes the ledger entries in this category; the ledger holds full evidence and reproduction steps.

| ID | Finding | Evidence | Where to read more |
|---|---|---|---|
| [D-10](../DISCOVERY-LEDGER.md#d-10) | `production_doctor.log` in cwd on every doctor call; self-check writes into site-packages; history/rollback create state dirs | VERIFIED | [state and persistence](../01-system/state-and-persistence.md) |
| [D-11](../DISCOVERY-LEDGER.md#d-11) | `logging.basicConfig(force=True)` replaces host logging handlers | VERIFIED | [library overview](../04-library-api/overview.md) |
| [D-26](../DISCOVERY-LEDGER.md#d-26) | `missing_imports` depends on doctor's interpreter and whether cwd is on `sys.path` | VERIFIED | [environment detection](../02-installation/environment-detection.md) |
| [D-17](../DISCOVERY-LEDGER.md#d-17) | Default ignore patterns skip `env`/`build`/`venv`-named dirs at any depth | VERIFIED | [implicit configuration](../06-configuration/implicit-configuration.md) |
| [D-25](../DISCOVERY-LEDGER.md#d-25) | JSON report always written; `-o x.json` collides with the markdown path | VERIFIED | [input/output contracts](../05-cli-and-tools/input-output-contracts.md) |
| [D-14](../DISCOVERY-LEDGER.md#d-14) | pycache-clean roots resolve from cwd; scalar roots iterate per character | VERIFIED | [configuration pitfalls](../06-configuration/configuration-pitfalls.md) |
| [D-15](../DISCOVERY-LEDGER.md#d-15) | Scaffolded harness infers project root two levels above itself | VERIFIED | [harness recipes](../09-recipes/README.md) |


## Sources

- [Discovery Ledger](../DISCOVERY-LEDGER.md)
- [Agent findings](../_evidence/README.md)
