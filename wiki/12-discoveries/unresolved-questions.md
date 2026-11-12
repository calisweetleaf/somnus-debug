# Unresolved Questions

This page lists what the investigation could not settle and the evidence that would settle each item.

## Open items

This section is the working list; each item names its blocker.

| Question | Status | Evidence needed |
|---|---|---|
| Does the package work on Python 3.10 and 3.11 as `pyproject.toml` claims? | Largely settled: VERIFIED by W2 that smoke gives 10 passed / 2 failed (D-01) and selftest 29/29 on 3.10.22, 3.11.17 and 3.12.15 | Python below 3.10 and 3.13 with PyYAML through the dispatcher remain unverified. |
| Windows behavior: case-insensitive pattern matching, path separators, long paths | UNVERIFIED | A Windows runner. Long-path code is absent (D-14). |
| `follow_symlinks: true` in pycache-clean with a symlink loop | UNVERIFIED | Bounded /tmp loop fixture with a timeout. |
| Does a live pycache-clean run with scalar `roots: /x` actually sweep from `/`? | UNVERIFIED (deliberately) | Only in a disposable container; constructor evidence already shows `/` in roots. |
| Exit 5 from a database error path, and the `_execution_error` worker path | SOURCE-CONFIRMED only | Fault injection (read-only state db mid-run). |
| `history` ordering with stored timestamps | Settled: W2 confirmed on disk (`od -c`) that timestamps are ISO-8601 with `Z`; lane F's localized view was a display artifact | none |
| Does GitHub render the README correctly (PLAN item 4) | UNVERIFIED | Live GitHub view; outside scope. |
| Whether the canonical `calisweetleaf/somnus-debug` master matches this upload | UNVERIFIED | Clone and diff; not done to keep the investigation offline from the remote. |

## Sources

- [Discovery Ledger](../DISCOVERY-LEDGER.md)
- [Agent findings](../_evidence/README.md)
