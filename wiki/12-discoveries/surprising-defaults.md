# Surprising Defaults

This page lists defaults whose effect differs from what a reader would assume from the option name or the docs.

## Findings

This section indexes the ledger entries in this category; the ledger holds full evidence and reproduction steps.

| ID | Finding | Evidence | Where to read more |
|---|---|---|---|
| [D-02](../DISCOVERY-LEDGER.md#d-02) | No config file is discovered; built-in defaults apply unless `-c` is passed | VERIFIED | [defaults](../06-configuration/defaults.md) |
| [D-05](../DISCOVERY-LEDGER.md#d-05) | `detect_test_gaps: true` by default, with no effect | VERIFIED | [hidden and conditional options](../06-configuration/hidden-and-conditional-options.md) |
| [D-17](../DISCOVERY-LEDGER.md#d-17) | Empty `include_patterns` scans nothing and exits 0 | VERIFIED | [configuration pitfalls](../06-configuration/configuration-pitfalls.md) |
| [D-15](../DISCOVERY-LEDGER.md#d-15) | `init-test-harness` targets `.`, which places artifacts outside the repo | VERIFIED | [command reference](../05-cli-and-tools/command-reference.md) |
| [D-18](../DISCOVERY-LEDGER.md#d-18) | Gate `minor`/`info` exits 1 even with criticals present | VERIFIED | [exit codes](../05-cli-and-tools/exit-codes.md) |

## Verbosity flag

This section records a flag whose default and effect are both surprising.

`doctor scan -v` is accepted by argparse but ignored: `setup_logging` checks for the literal string `--verbose` in argv before parsing (`src/somnus_debug/doctor/core.py:2179-2186`). `--verbose` sets the file handler to DEBUG, but the module contains no `logger.debug` calls, so neither flag changes output [SOURCE-CONFIRMED by lead grep; VERIFIED no-change by lanes B and D].

## Sources

- [Discovery Ledger](../DISCOVERY-LEDGER.md)
- [Agent findings](../_evidence/README.md)
