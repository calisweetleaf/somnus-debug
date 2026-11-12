# Capability Atlas

This atlas lists every capability the investigation established, grouped by function, with how to invoke it, its exposure, and its verification status. The machine-readable form is [`_evidence/capability-registry.jsonl`](_evidence/capability-registry.jsonl); this page is generated from it.

Exposure: `public` means a console script, CLI flag, or package export; `internal` means importable but not declared; `recipe` means a verified composition kept in the evidence tree; `public (skill script)` means a fieldkit script, which ships in the repo but not in the wheel.

## Cli

This section covers the cli capabilities.

| ID | Capability | Exposure | Invocation | Verification | Discoveries | Page |
|---|---|---|---|---|---|---|
| `CAP-DISPATCH` | Unified somnus-debug dispatcher | public | `somnus-debug <cmd> [args]` | VERIFIED | [D-13](DISCOVERY-LEDGER.md#d-13) | [page](05-cli-and-tools/command-reference.md) |

## Diagnostics

This section covers the diagnostics capabilities.

| ID | Capability | Exposure | Invocation | Verification | Discoveries | Page |
|---|---|---|---|---|---|---|
| `CAP-DOCTOR-SCAN` | Doctor project scan | public | `somnus-debug doctor scan [root] [-c CFG] [-o MD] [--json-output JSON] [--no-state] [--verbose]` | VERIFIED |  | [page](05-cli-and-tools/command-reference.md) |
| `CAP-DOCTOR-SELFCHECK` | Doctor self-check | public | `somnus-debug doctor self-check [-o] [--json-output] [--no-state]` | VERIFIED | [D-10](DISCOVERY-LEDGER.md#d-10), [D-07](DISCOVERY-LEDGER.md#d-07) | [page](05-cli-and-tools/command-reference.md) |
| `CAP-DOCTOR-IMPORTGRAPH` | Import graph: missing imports and cycles | internal (via scan) | `scan categories missing_imports, dependency_cycles` | VERIFIED (with gaps) | [D-06](DISCOVERY-LEDGER.md#d-06), [D-22](DISCOVERY-LEDGER.md#d-22), [D-26](DISCOVERY-LEDGER.md#d-26) | [page](07-internals/call-chains.md) |
| `CAP-DOCTOR-DETECTORS` | AST detectors (19 emitted categories) | internal (via scan) | `scan` | VERIFIED | [D-05](DISCOVERY-LEDGER.md#d-05), [D-07](DISCOVERY-LEDGER.md#d-07), [D-16](DISCOVERY-LEDGER.md#d-16) | [page](07-internals/call-chains.md) |

## Configuration

This section covers the configuration capabilities.

| ID | Capability | Exposure | Invocation | Verification | Discoveries | Page |
|---|---|---|---|---|---|---|
| `CAP-DOCTOR-INITCFG` | Doctor init-config | public | `somnus-debug doctor init-config [-o PATH] [--force]` | VERIFIED | [D-02](DISCOVERY-LEDGER.md#d-02) | [page](06-configuration/file-based-configuration.md) |
| `CAP-DOCTOR-YAML` | Zero-dependency YAML subset parser | internal | `-c file.yaml` | VERIFIED | [D-04](DISCOVERY-LEDGER.md#d-04), [D-03](DISCOVERY-LEDGER.md#d-03) | [page](06-configuration/file-based-configuration.md) |
| `CAP-DOCTOR-JSONCFG` | JSON config files | public (undocumented) | `-c file.json` | VERIFIED | [D-04](DISCOVERY-LEDGER.md#d-04) | [page](06-configuration/file-based-configuration.md) |

## State

This section covers the state capabilities.

| ID | Capability | Exposure | Invocation | Verification | Discoveries | Page |
|---|---|---|---|---|---|---|
| `CAP-DOCTOR-HISTORY` | Doctor history | public | `somnus-debug doctor history [root] [--limit N]` | VERIFIED | [D-08](DISCOVERY-LEDGER.md#d-08), [D-28](DISCOVERY-LEDGER.md#d-28) | [page](07-internals/state-transitions.md) |
| `CAP-DOCTOR-ROLLBACK` | Doctor rollback of latest alias | public | `somnus-debug doctor rollback [root] --run-id ID` | VERIFIED | [D-09](DISCOVERY-LEDGER.md#d-09) | [page](07-internals/state-transitions.md) |
| `CAP-DOCTOR-STATE` | SQLite run state (runs, file_snapshots, report_aliases) | internal | `implicit in scan; StateStore class` | VERIFIED | [D-08](DISCOVERY-LEDGER.md#d-08), [D-28](DISCOVERY-LEDGER.md#d-28) | [page](01-system/state-and-persistence.md) |

## Library

This section covers the library capabilities.

| ID | Capability | Exposure | Invocation | Verification | Discoveries | Page |
|---|---|---|---|---|---|---|
| `CAP-DOCTOR-LIB` | Side-effect-free doctor embedding | internal | `ProjectScanner(Path(root), ConfigManager(None\|Path)).scan(previous_index)` | VERIFIED | [D-12](DISCOVERY-LEDGER.md#d-12) | [page](10-agent-usage/programmatic-invocation.md) |
| `CAP-STRUCTURE-LIB` | structure build_index as a function | public | `from somnus_debug.structure import build_index` | VERIFIED | [D-27](DISCOVERY-LEDGER.md#d-27) | [page](04-library-api/functions.md) |

## Automation

This section covers the automation capabilities.

| ID | Capability | Exposure | Invocation | Verification | Discoveries | Page |
|---|---|---|---|---|---|---|
| `CAP-DOCTOR-GATE` | Severity exit gate | public | `severity_exit_level config` | VERIFIED | [D-03](DISCOVERY-LEDGER.md#d-03), [D-18](DISCOVERY-LEDGER.md#d-18) | [page](05-cli-and-tools/exit-codes.md) |

## Reporting

This section covers the reporting capabilities.

| ID | Capability | Exposure | Invocation | Verification | Discoveries | Page |
|---|---|---|---|---|---|---|
| `CAP-DOCTOR-SCORE` | Health score 100-20c-8s-2m-i | internal (in report) | `report summary.score` | SOURCE-CONFIRMED |  | [page](07-internals/implementation-notes.md) |

## Indexing

This section covers the indexing capabilities.

| ID | Capability | Exposure | Invocation | Verification | Discoveries | Page |
|---|---|---|---|---|---|---|
| `CAP-STRUCTURE` | Single-file class/def structure index | public | `somnus-debug structure FILE [-o OUT \| --update-doc DOC] ...` | VERIFIED (broken on stamped files) | [D-01](DISCOVERY-LEDGER.md#d-01), [D-24](DISCOVERY-LEDGER.md#d-24) | [page](05-cli-and-tools/command-reference.md) |

## Maintenance

This section covers the maintenance capabilities.

| ID | Capability | Exposure | Invocation | Verification | Discoveries | Page |
|---|---|---|---|---|---|---|
| `CAP-PYCACHE` | pycache/pyc/pyo cleaner | public | `somnus-debug pycache-clean [--config F] [--dry-run] [--verbose] [--max-depth N] [--follow-symlinks]` | VERIFIED (/tmp only) | [D-14](DISCOVERY-LEDGER.md#d-14) | [page](05-cli-and-tools/command-reference.md) |

## Test-Harness

This section covers the test-harness capabilities.

| ID | Capability | Exposure | Invocation | Verification | Discoveries | Page |
|---|---|---|---|---|---|---|
| `CAP-HARNESS-SCAFFOLD` | init-test-harness scaffold | public | `somnus-debug init-test-harness [dest] [--force] ...` | VERIFIED | [D-15](DISCOVERY-LEDGER.md#d-15) | [page](05-cli-and-tools/command-reference.md) |
| `CAP-HARNESS-RUN` | Single-test harness runtime (run_test.py) | public (template) | `python run_test.py` | VERIFIED | [D-15](DISCOVERY-LEDGER.md#d-15) | [page](09-recipes/README.md) |

## Fieldkit

This section covers the fieldkit capabilities.

| ID | Capability | Exposure | Invocation | Verification | Discoveries | Page |
|---|---|---|---|---|---|---|
| `CAP-FK-ONBOARD` | Fieldkit onboard.py | public (skill script) | `python onboard.py [REPO] [--apply] [--baseline] [--new-config] [--python PY]` | VERIFIED | [D-20](DISCOVERY-LEDGER.md#d-20), [D-22](DISCOVERY-LEDGER.md#d-22) | [page](10-agent-usage/agent-quickstart.md) |
| `CAP-FK-DELTA` | Fieldkit delta.py regression gate | public (skill script) | `python delta.py BASELINE LATEST [--dispositions FILE] [--root DIR] [--json]` | VERIFIED | [D-21](DISCOVERY-LEDGER.md#d-21), [D-27](DISCOVERY-LEDGER.md#d-27) | [page](10-agent-usage/automation-contracts.md) |
| `CAP-FK-SELFTEST` | Fieldkit selftest.py (29 behavior pins) | public (skill script) | `python selftest.py [--python PY]` | VERIFIED 29/29 |  | [page](11-verification/test-architecture.md) |

## Composition

This section covers the composition capabilities.

| ID | Capability | Exposure | Invocation | Verification | Discoveries | Page |
|---|---|---|---|---|---|---|
| `CAP-COMP-RATCHET` | Quality ratchet: doctor JSON + delta + history | recipe | `shell recipe` | VERIFIED | [D-27](DISCOVERY-LEDGER.md#d-27) | [page](08-extensions/composition-patterns.md) |
| `CAP-COMP-SLICES` | Structure-driven targeted reading | recipe | `python recipe` | VERIFIED | [D-27](DISCOVERY-LEDGER.md#d-27), [D-01](DISCOVERY-LEDGER.md#d-01) | [page](08-extensions/composition-patterns.md) |

## Extension

This section covers the extension capabilities.

| ID | Capability | Exposure | Invocation | Verification | Discoveries | Page |
|---|---|---|---|---|---|---|
| `CAP-EXT-CUSTOM-DETECTOR` | Custom detector via CodeQualityVisitor subclass | internal | `monkeypatch recipe` | VERIFIED | [D-19](DISCOVERY-LEDGER.md#d-19) | [page](08-extensions/customization.md) |

## Side effects at a glance

This section lists, per capability, what it writes or changes, because that decides where it is safe to run.

| ID | Side effects | Failure behavior |
|---|---|---|
| `CAP-DISPATCH` | rewrites/restores sys.argv | unknown command exit 2; missing PyYAML exit 1 |
| `CAP-DOCTOR-SCAN` | production_doctor.log in cwd; <root>/production_doctor_report.{md,json}; <root>/.python_doctor/state.sqlite3 unless --no-state | config errors exit 4; runtime 5; uncaught types traceback |
| `CAP-DOCTOR-INITCFG` | writes file | exists without --force exit 4 |
| `CAP-DOCTOR-HISTORY` | creates .python_doctor/ on fresh tree | state unavailable exit 4 (no fallback) |
| `CAP-DOCTOR-ROLLBACK` | rewrites latest alias | unknown id exit 4 |
| `CAP-DOCTOR-SELFCHECK` | writes into installed package directory | read-only install exit 4 unless -o; rejects -v (exit 2) |
| `CAP-DOCTOR-LIB` | none observed | ConfigurationError / DoctorError subclasses |
| `CAP-DOCTOR-STATE` | persistent db | fallback in scan only |
| `CAP-DOCTOR-IMPORTGRAPH` | none observed | misses from-import cycles |
| `CAP-DOCTOR-DETECTORS` | none observed | false positives D-07 |
| `CAP-DOCTOR-GATE` | none observed | unquoted none exit 4 |
| `CAP-DOCTOR-SCORE` | none observed | weights hard-coded |
| `CAP-DOCTOR-YAML` | none observed | silent mis-parses |
| `CAP-DOCTOR-JSONCFG` | none observed | bad JSON exit 4 |
| `CAP-STRUCTURE` | writes -o/--update-doc target | exit 2 on any error; crashes on stamped files |
| `CAP-STRUCTURE-LIB` | none observed | SyntaxError on stamped files |
| `CAP-PYCACHE` | DELETES files | missing config exit 1; missing root exit 0; negative --max-depth is a silent no-op |
| `CAP-HARNESS-SCAFFOLD` | writes 2 files | exists without --force exit 1 |
| `CAP-HARNESS-RUN` | writes test-runs/ two levels up by default | ignores --help |
| `CAP-FK-ONBOARD` | writes .somnus-debug/ profile + baseline on --apply | exit 1/2/3; bugs D-20 |
| `CAP-FK-DELTA` | none observed | holes D-21 |
| `CAP-FK-SELFTEST` | temp dirs | misses D-01 |
| `CAP-COMP-RATCHET` | baseline file | holds on regression/stale |
| `CAP-COMP-SLICES` | none observed | refuses when files changed |
| `CAP-EXT-CUSTOM-DETECTOR` | none observed | breaks on refactor |

## Sources

- [capability-registry.jsonl](_evidence/capability-registry.jsonl)
- [Discovery Ledger](DISCOVERY-LEDGER.md)
