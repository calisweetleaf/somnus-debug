# Research Opportunities

This page lists directions suggested by the evidence. Every item is a HYPOTHESIS or a small integration step, not a current capability.

## Directions

This section groups opportunities by the evidence that motivates them.

| Direction | Motivating evidence | Class |
|---|---|---|
| Resolve `from pkg import mod` to the child module before the package | D-06, D-22 | Small fix, HYPOTHESIS on impact |
| Emit `test_gaps` or remove it (PLAN item 5) | D-05 | Decision for Daeron |
| Strict config validation: warn on unknown keys, reject non-bool `dry_run`, require list `roots` | D-04, D-14 | Small integration step |
| Sub-second or UUID run IDs | D-08 | Small fix |
| Logging under `state_dir` instead of cwd; no `force=True` (PLAN item 3) | D-10, D-11 | Public behavior change, needs approval |
| Detector registry so custom checks need no subclassing | D-19 | Research |
| `delta.py` comparing `config_hash` and expiring stale broad dispositions | D-21 | Small integration step |
| Lazy imports in `cli.py` so doctor/structure need no PyYAML | D-13 | Small fix |
| A generic harness template (no cargo) and root inference from the scaffold target | D-15 | Small fix |
| MCP server exposing doctor/structure (Daeron's stated idea) | none present in source | Research; nothing exists today |

## Sources

- [Discovery Ledger](../DISCOVERY-LEDGER.md)
- [Agent findings](../_evidence/README.md)
