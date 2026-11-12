# Error handling

This page describes how each tool handles failure internally: where errors are caught, converted, logged, swallowed, or allowed to escape, and what the user sees as a result. The caller-facing exception list is in [04-library-api/exceptions](../04-library-api/exceptions.md). Exit-code tables per command are in [05-cli-and-tools/exit-codes](../05-cli-and-tools/exit-codes.md).

## Doctor: three tiers

This section shows the doctor's layered strategy. Errors are contained at the smallest scope the code allows.

```
Tier 1  per file      FileAnalyzer.analyze      read/decode error -> analysis_read_errors issue
                                                syntax/ValueError -> syntax_errors issue, partial result
                                                TokenError        -> tokenization_errors issue
Tier 2  per worker    ProjectScanner            DoctorError|OSError|RuntimeError|TypeError|ValueError|LookupError
                      (threaded path only)      -> analysis_read_errors "<analysis>" issue
Tier 3  per command   main                      DoctorError -> stderr render + log ERROR -> 4
                                                OSError|RuntimeError|TypeError|ValueError|sqlite3.Error
                                                  -> log CRITICAL with traceback, stderr render -> 5
        (uncaught)                              everything else -> Python traceback
```

[SOURCE-CONFIRMED] `src/somnus_debug/doctor/core.py:1522-1536`, `:1548-1564`, `:1726-1731`, `:2189-2199`. [VERIFIED] each tier:

| Tier | Run | Evidence |
|---|---|---|
| 1 | `broken.py` gives a syntax issue plus a tokenization issue | `/tmp/w1/ex_api.py` |
| 2 | injected `ValueError`; `RecursionError` in `rec2` | `/tmp/w1/ex_serial.py`, `/tmp/w1/rec2` |
| 3 | exits 4 and 5 | [lane-d exit-codes](../_evidence/agent-findings/lane-d-cli-tests/exit-codes.md); `/tmp/w1/rec1` exit 5 |

Gaps in the tiers:

- **Serial path.** Tier 2 is absent when `max_workers == 1` or the project has one file, so a tier-1 escape goes straight to tier 3. [VERIFIED] `/tmp/w1/ex_serial.py`.
- **Post-analysis faults.** A failure in graph building, rendering, or JSON serialization has no per-file containment. The whole command fails at tier 3. [SOURCE-CONFIRMED] `:1709-1714`, `:2078-2080`.
- **Exit code 4 or 5 is not proof that nothing was written.** Tier 3 does not roll back partial writes. If `persist` fails after its file writes, the reports exist but the DB row does not. [SOURCE-CONFIRMED] `:1966-1979`.

## Doctor: rendering of errors

This section explains what an error looks like on screen and in the log.

- **stderr.** `DoctorError.render()` prints `Doctor failure: …`, then `Remediation: …`, then `Context:` with pretty JSON. Tracebacks are never printed for classified errors. [SOURCE-CONFIRMED] `:113-120`.
- **production_doctor.log.** Exit 4 logs the rendered error at ERROR. Exit 5 logs "Unclassified doctor runtime failure" at CRITICAL with `exc_info=True`. Nothing else is ever logged. A successful run leaves a 0-byte log. [SOURCE-CONFIRMED] `:2192`, `:2196`; [VERIFIED] 0-byte log after `--help` in `/tmp/w1/help`, and traceback-in-log for D44 in [lane-d experiment-log](../_evidence/agent-findings/lane-d-cli-tests/experiment-log.md).
- **Remediation text.** Subclass remediation is always the class default. Command-specific advice placed in `context["remediation"]` appears only inside the JSON context. [VERIFIED] [exceptions](../04-library-api/exceptions.md#doctor-error-hierarchy).

## Doctor: errors it swallows

This section lists places where the doctor intentionally discards an error, which affects what the user can learn from a run.

| Location | Swallowed | Consequence |
|---|---|---|
| `ImportResolver._third_party_exists` (`:1050-1055`) | `ImportError`, `ModuleNotFoundError`, `ValueError`, `AttributeError` from `find_spec` | the import is classified `missing` with no hint that `find_spec` itself failed |
| `safe_relpath` (`:583-588`) | `ValueError` (path outside root) | an absolute path is used as the "relative" path |
| `run_scan` state open (`:2068-2077`) | `StateStoreError` | warning on stderr, stateless run, exit code unaffected ([fallbacks](fallbacks.md)) |
| Unknown config keys (`:816-851`) | not an exception, but silently ignored | typos have no effect ([D-04](../DISCOVERY-LEDGER.md#d-04)) |

Several of the doctor's own handlers are flagged by its own `silent_failures` detector in self-check (11 findings). The reason is that they call `logging.getLogger(NAME).error`, which the detector does not recognize as logging. [VERIFIED] [lane-a architecture §3.3](../_evidence/agent-findings/lane-a-arch-api/architecture.md).

## structure

This section covers the indexer, which has one handler.

`main` catches `OSError` and `SyntaxError` from reading and indexing, prints `error: <exc>`, and returns 2. It catches `OSError` from writing the same way. `UnicodeDecodeError`, a `ValueError`, is not caught: a non-UTF-8 file produces a traceback and exit 1. [SOURCE-CONFIRMED] `src/somnus_debug/structure/core.py:325-346`; [VERIFIED] latin-1 case in [lane-b §2.4](../_evidence/agent-findings/lane-b-config/configuration-findings.md). The type-comment `SyntaxError` ([D-01](../DISCOVERY-LEDGER.md#d-01)) is reported like any other syntax error, so a user cannot tell that the file is actually valid.

## pycache-clean

This section covers the cleaner. It catches broadly and logs at levels that can hide problems.

| Location | Caught | Handling |
|---|---|---|
| `_scan_root` scandir (`:226-231`) | `PermissionError` | WARNING, skip directory |
| `_scan_root` per entry (`:256-258`) | `OSError` | **DEBUG** "Ignoring disappearing entry", invisible unless verbose |
| `_delete_directory` size (`:276-279`) | `Exception` | size 0 |
| `_delete_directory` / `_delete_file` (`:282-286`, `:300-304`) | `Exception` | WARNING, not counted |
| `_get_dir_size` (`:314-320`) | walk errors and `Exception` | ignored |
| `run` missing root (`:211-213`) | n/a | ERROR, continue, exit 0 |
| `main` (`:367-372`) | `Exception` from construction and run | `logging.exception`, `sys.exit(1)` |
| `main` config load (`:355`) | **not caught** | YAML or shape errors give a traceback, exit 1 |
| `setup_logging` (`:329-333`) | `Exception` opening `log_file` | message to stderr, continue without file logging |

[SOURCE-CONFIRMED] each row. [VERIFIED] the missing root exiting 0 and malformed YAML producing a traceback: [lane-d exit-codes](../_evidence/agent-findings/lane-d-cli-tests/exit-codes.md) P01, P06.

By the doctor's own rules, the cleaner's handlers are a problem. [VERIFIED] `/tmp/w1`: `python3 -m somnus_debug.doctor.core scan src/somnus_debug/pycache_cleaner --no-state -o /tmp/...` exited 1 and reported 7 `broad_exceptions` and 8 `silent_failures` in `pycache_cleaner/core.py`, at lines 229, 256, 278, 284, 296, 302, 319, 332, and 370. The silent ones include the `PermissionError` and `OSError` handlers, because they log with `logging.warning`/`logging.debug`, which do not count as error logging.

## init-test-harness and dispatcher

This section covers the two remaining entry points.

- **scaffold**: `FileExistsError` is converted to `error: <exc>` on stderr and exit 1 (`src/somnus_debug/test_harness/scaffold.py:114-118`). This covers both the explicit refusal and the case where the target path is an existing **file**: there `mkdir(exist_ok=True)` raises `FileExistsError` (`[Errno 17] File exists`), which the same handler catches. [VERIFIED] `/tmp/w1`: `main(['afile'])` exited 1 with `error: [Errno 17] File exists: '/tmp/w1/afile'`, matching lane D's H07 ([lane-d exit-codes](../_evidence/agent-findings/lane-d-cli-tests/exit-codes.md)). Other `OSError`s, such as permission errors, propagate. [SOURCE-CONFIRMED]
- **dispatcher**: catches only `SystemExit`. [SOURCE-CONFIRMED] `src/somnus_debug/cli.py:99-104`.

## Sources

This section lists the code, evidence files, and probes this page rests on.

- `src/somnus_debug/doctor/core.py:113-120`, `:583-588`, `:816-851`, `:1050-1055`, `:1520-1564`, `:1709-1731`, `:1966-1979`, `:2068-2080`, `:2184-2199`
- `src/somnus_debug/structure/core.py:323-347`, `src/somnus_debug/pycache_cleaner/core.py:207-372`, `src/somnus_debug/test_harness/scaffold.py:112-125`, `src/somnus_debug/cli.py:85-104`
- [lane-a architecture.md](../_evidence/agent-findings/lane-a-arch-api/architecture.md), [lane-b configuration-findings.md](../_evidence/agent-findings/lane-b-config/configuration-findings.md), [lane-d exit-codes.md](../_evidence/agent-findings/lane-d-cli-tests/exit-codes.md), [lane-d experiment-log.md](../_evidence/agent-findings/lane-d-cli-tests/experiment-log.md)
- Executed probes: `/tmp/w1/ex_api.py`, `/tmp/w1/ex_serial.py`, `/tmp/w1/rec1`, `/tmp/w1/rec2`, `/tmp/w1/help`, `/tmp/w1/afile` (scaffold), `/tmp/w1/dpc/r.json` (doctor over pycache_cleaner)
