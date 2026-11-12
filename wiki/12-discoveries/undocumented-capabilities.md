# Undocumented Capabilities

This page lists behaviors that work today but that README.md and docs/MANUAL.md do not describe. Each item was executed in /tmp unless marked otherwise.

## Findings

This section indexes the ledger entries in this category; the ledger holds full evidence and reproduction steps.

| ID | Finding | Evidence | Where to read more |
|---|---|---|---|
| [D-12](../DISCOVERY-LEDGER.md#d-12) | Embed doctor without side effects through `ProjectScanner(root, ConfigManager(None)).scan({})` | VERIFIED | [programmatic invocation](../10-agent-usage/programmatic-invocation.md) |
| [D-27](../DISCOVERY-LEDGER.md#d-27) | Doctor JSON plus fieldkit `delta.py` form a CI ratchet; structure spans give targeted definition slices | VERIFIED | [composition patterns](../08-extensions/composition-patterns.md) |
| [D-03](../DISCOVERY-LEDGER.md#d-03) | `severity_exit_level` accepts quoted `"none"` (gate off) and `info` | VERIFIED | [configuration pitfalls](../06-configuration/configuration-pitfalls.md) |
| [D-19](../DISCOVERY-LEDGER.md#d-19) | Severity can be assigned to any category name; a subclassed `CodeQualityVisitor` adds a category end to end (private) | VERIFIED | [existing extension points](../08-extensions/existing-extension-points.md) |
| [D-04](../DISCOVERY-LEDGER.md#d-04) | A `.json` config file bypasses the YAML subset parser entirely | SOURCE-CONFIRMED | [file-based configuration](../06-configuration/file-based-configuration.md) |

## Also undocumented but ordinary

This section lists smaller surfaces that exist without documentation and do not rise to a ledger entry.

- `doctor history --limit N` and `doctor rollback --run-id ID` are only described in `--help` [VERIFIED, lane D help capture].
- Doctor reports carry per-file hashes and a `config_hash`, usable as change-detection keys [VERIFIED, lane F `s1_doctor_json_shape.txt`].
- Reusable internals such as the import resolver, project file index, report writers, and state store are callable from `somnus_debug.doctor.core` but internal; see [internal interfaces](../04-library-api/internal-interfaces.md) and [api index](../04-library-api/api-index.md). (Lane A catalogued 18 such primitives in `undocumented-primitives.md`; that file was lost in a sandbox reset on 2026-11-12 00:40 UTC, and W1 rebuilt the coverage from source.)

## Sources

- [Discovery Ledger](../DISCOVERY-LEDGER.md)
- [Agent findings](../_evidence/README.md)
