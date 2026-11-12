# Latent Interfaces

This page lists internal machinery that is reachable from Python and useful, but is not declared public.

## Findings

This section indexes the ledger entries in this category; the ledger holds full evidence and reproduction steps.

| ID | Finding | Evidence | Where to read more |
|---|---|---|---|
| [D-12](../DISCOVERY-LEDGER.md#d-12) | `ProjectScanner`, `ConfigManager`, `ProjectAnalysisResult` (doctor/core.py:1695, :782) | VERIFIED | [internal interfaces](../04-library-api/internal-interfaces.md) |
| [D-19](../DISCOVERY-LEDGER.md#d-19) | `CodeQualityVisitor` (doctor/core.py:1143) as a subclassing seam | VERIFIED | [customization](../08-extensions/customization.md) |

## Declared exports versus reachable names

This section states the actual public boundary.

`somnus_debug.__all__` is `["__version__"]` (`src/somnus_debug/__init__.py:59`). Each tool's `__init__.py` re-exports its `main` and a few names; lane A verified each import. Everything else, including the scanner, resolver, state store, and report writers, is importable from `somnus_debug.<tool>.core` but carries no stability promise. See [public API](../04-library-api/public-api.md) and [api index](../04-library-api/api-index.md).

## Sources

- [Discovery Ledger](../DISCOVERY-LEDGER.md)
- [Agent findings](../_evidence/README.md)
