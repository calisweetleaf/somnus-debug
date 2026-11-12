# Design invariants

This page lists the rules the code is built to hold, checks each one against the source and the experiments, and records where it breaks. A rule stated in a docstring or the doctor's own header is treated as intended. It is marked as holding only when the code or a run shows it.

## Invariant table

This section gives each invariant, its verdict, and the evidence in one place.

| # | Invariant (intended) | Stated at | Verdict | Evidence |
|---|---|---|---|---|
| I1 | The doctor never modifies the scanned source files | report footer `src/somnus_debug/doctor/core.py:1797`; module docstring | **Holds** for source files. It does write artifacts into the scanned tree (reports, `.python_doctor/`) | [SOURCE-CONFIRMED] the only writes are `write_text_atomic`/`copy_file_atomic` to report and state paths (`:2012-2031`) |
| I2 | Analysis is static: target code is never imported or executed | structure docstring `src/somnus_debug/structure/core.py:36-38`; doctor uses `ast`/`tokenize` | **Holds** for target code. The doctor does call `importlib.util.find_spec(top_level)`, which can import parent packages of dotted names, but it only passes the top-level name | [SOURCE-CONFIRMED] `:1050-1055`; `find_spec` on a top-level name does not execute the module [HYPOTHESIS for edge cases such as `.pth` hooks] |
| I3 | Failures become structured evidence, not silent continuation | doctor docstring ("forced failures into structured evidence") | **Partly holds**. Unreadable files, syntax errors, and tokenization errors become critical issues. Worker exceptions become issues **only on the threaded path**. Uncaught exception types escape `main` as tracebacks | [VERIFIED] `/tmp/w1/ex_serial.py`; [execution-model](execution-model.md#doctor-the-serial-path-drops-the-error-wrapper); [D-18](../DISCOVERY-LEDGER.md#d-18) |
| I4 | Configuration is immutable once validated | `DoctorConfig` is `@dataclass(frozen=True)` (`:207-208`) | **Holds** for `DoctorConfig`. Not for pycache: `PycacheCleaner.__init__` mutates the caller's `CleanerConfig` in place | [SOURCE-CONFIRMED] `src/somnus_debug/pycache_cleaner/core.py:182-193`; [VERIFIED] [lane-a api-reference §3](../_evidence/agent-findings/lane-a-arch-api/api-reference.md) |
| I5 | Artifact writes are atomic | `write_text_atomic` (`:2012-2020`) | **Holds per file** (temp file plus `replace`). Not across the run: six files and three SQL statements are not one transaction | [SOURCE-CONFIRMED] `:1964-1979` |
| I6 | JSON output is deterministic | `dumps_json(sort_keys=True)` (`:578-580`) | **Holds** for key order and issue order. Timestamps, `run_id`, mtimes, and interpreter-dependent import classes vary | [VERIFIED] identical counts across runs in `/tmp/w1/ex_state.py`; [execution-model](execution-model.md#ordering-and-determinism) |
| I7 | State belongs to the scanned project | `StateStore` roots at `project_root/state_dir` (`:1919-1925`) | **Holds by default**. Breaks for `self-check`, which writes into the installed package directory, and for absolute or `..` `state_dir` values | [VERIFIED] [lane-a architecture §3.6](../_evidence/agent-findings/lane-a-arch-api/architecture.md); [lane-b configuration-findings §4](../_evidence/agent-findings/lane-b-config/configuration-findings.md) |
| I8 | One run, one history record | `run_id` primary key | **Breaks** within one second: `INSERT OR REPLACE` overwrites | [VERIFIED] [D-08](../DISCOVERY-LEDGER.md#d-08) |
| I9 | Rollback restores the previous report | `rollback` help "restore a previous report as latest" | **Partly holds**: only `reports/latest.*` and the alias move; the project-root report does not | [VERIFIED] [D-09](../DISCOVERY-LEDGER.md#d-09) |
| I10 | The library does not interfere with its host | not stated | **Holds for the scan engine**, which never logs, prints, or writes. **Breaks for `main()`**: `basicConfig(force=True)` replaces the host's root handlers, and a log file appears in the cwd | [VERIFIED] [D-11](../DISCOVERY-LEDGER.md#d-11), [D-12](../DISCOVERY-LEDGER.md#d-12) |
| I11 | Each tool keeps its own argparse surface; the dispatcher never re-declares flags | `src/somnus_debug/cli.py:35-41` | **Holds**: the dispatcher forwards argv untouched | [SOURCE-CONFIRMED] `src/somnus_debug/cli.py:85-104` |
| I12 | The structure indexer accepts any parseable Python file | test `tests/test_cli_smoke.py:138` | **Breaks** in `src/` on files whose comments look like type comments, including every metadata-stamped file | [VERIFIED] [D-01](../DISCOVERY-LEDGER.md#d-01); `/tmp/w1/ex_misc.py` |
| I13 | `init-test-harness` never clobbers an edited copy | `src/somnus_debug/test_harness/scaffold.py:63-70` | **Holds**: an existence check precedes any write | [VERIFIED] [lane-a api-reference §4](../_evidence/agent-findings/lane-a-arch-api/api-reference.md) |
| I14 | Config errors fail loudly | `ConfigurationError` paths | **Partly holds**: type and shape errors exit 4. Unknown keys, misspelled categories, and several YAML forms are accepted silently | [VERIFIED] [D-04](../DISCOVERY-LEDGER.md#d-04) |

## Invariants the code relies on without enforcing

This section names assumptions that are not checked anywhere and fail quietly when violated.

- **One project per state directory.** No query filters by `project_root` (`:1942-2009`). [SOURCE-CONFIRMED]
- **One doctor process per project at a time.** The atomic temp name `.<name>.tmp` is fixed, and nothing locks. [SOURCE-CONFIRMED] `:2016`; consequence [HYPOTHESIS].
- **History is read with the same config as the scan.** `history` and `rollback` re-read `state_dir` from their own `-c`. [VERIFIED] [lane-b configuration-findings §2.1](../_evidence/agent-findings/lane-b-config/configuration-findings.md).
- **The scanning interpreter matches the project's runtime.** Third-party resolution uses the doctor's own `sys.path`. [VERIFIED] [D-26](../DISCOVERY-LEDGER.md#d-26).
- **Detector names in config match emitted names.** `severity_levels` accepts any category string, and `detect_test_gaps` is validated but never read. [VERIFIED] [D-05](../DISCOVERY-LEDGER.md#d-05).

## Using this page

This section says how to apply the table when building on the toolkit.

If you embed the doctor, rely on I1, I2, I4, I6, and the scan-engine half of I10, and call `ProjectScanner` directly rather than `main()`. If you build CI gates, design around I3, I8, and the shared meaning of exit code 2. If you run several scans quickly, account for I8. [public-api](../04-library-api/public-api.md) and [error-handling](../07-internals/error-handling.md) give the concrete calls.

## Sources

This section lists the code, evidence files, and probes this page rests on.

- `src/somnus_debug/doctor/core.py:207-208`, `:578-580`, `:1050-1055`, `:1716-1738`, `:1916-2031`, `:2179-2199`
- `src/somnus_debug/cli.py:35-41`, `:85-104`; `src/somnus_debug/structure/core.py:36-38`, `:210`; `src/somnus_debug/pycache_cleaner/core.py:182-193`; `src/somnus_debug/test_harness/scaffold.py:62-88`; `tests/test_cli_smoke.py:138`
- [lane-a architecture.md](../_evidence/agent-findings/lane-a-arch-api/architecture.md), [lane-a api-reference.md](../_evidence/agent-findings/lane-a-arch-api/api-reference.md), [lane-b configuration-findings.md](../_evidence/agent-findings/lane-b-config/configuration-findings.md)
- Executed probes: `/tmp/w1/ex_serial.py`, `/tmp/w1/ex_state.py`, `/tmp/w1/ex_misc.py`
