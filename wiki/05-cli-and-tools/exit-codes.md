# Exit codes

This page lists every exit code each somnus-debug surface can return, the condition behind it, and the evidence. It ends with guidance for callers who have to tell the codes apart.

## Summary matrix

This section gives the one-screen view; the per-tool sections below give conditions and evidence.

| Code | dispatcher `somnus-debug` | `doctor` | `structure` | `pycache-clean` | `init-test-harness` | scaffolded `run_test.py` |
|---:|---|---|---|---|---|---|
| 0 | help, version | gate passed (including zero files scanned); history/rollback/init-config success | index produced | finished (including a missing root) | files written | PASS |
| 1 | uncaught exception in a tool; PyYAML missing | gate tripped on serious (default gate), or any finding under the `minor`/`info` gates | uncaught exception (for example `UnicodeDecodeError`) | config not found; any error inside the cleaner; malformed YAML (traceback) | destination exists; target is a file | FAIL |
| 2 | unknown command | **critical** finding under the `serious`/`critical` gates, **or** an argparse error | any handled error (missing file, syntax error, stamped header, write error) **or** an argparse error | argparse error | argparse error | (not used) |
| 3 | (not used) | (not used) | (not used) | (not used) | (not used) | (not used) |
| 4 | (passed through) | `DoctorError`: bad or missing config, missing root only with `--no-state` or an uncreatable path (with state on, a writable missing root is created, scanned as 0 files, exit 0: [D-29](../DISCOVERY-LEDGER.md#d-29)), init-config target exists, unknown run ID, state DB unusable for history/rollback, unwritable output | (not used) | (not used) | (not used) | (not used) |
| 5 | (passed through) | unclassified `OSError`/`RuntimeError`/`TypeError`/`ValueError`/`sqlite3.Error`, for example a `RecursionError` on the serial path | (not used) | (not used) | (not used) | (not used) |

The dispatcher passes tool exit codes through unchanged (`src/somnus_debug/cli.py:99-104`).

## Dispatcher

This section covers codes produced by `somnus-debug` itself.

| Condition | Exit | Evidence |
|---|---:|---|
| no args, `-h`, `--help`, `-V`, `--version` | 0 | [VERIFIED] W2-01 |
| unknown command (help printed on stderr) | 2 | [VERIFIED] lane D C01 |
| tool returned int N or raised `SystemExit(N)` | N | [SOURCE-CONFIRMED] `src/somnus_debug/cli.py:99-104` |
| tool raised `SystemExit` with a non-int code | 1 | [SOURCE-CONFIRMED] `cli.py:101` |
| tool returned a non-int (pycache-clean returns `None`) | 0 | [SOURCE-CONFIRMED] `cli.py:104` |
| tool raised any other exception | 1 (Python traceback) | [VERIFIED] lane D P06/P07; W2-09 |
| PyYAML not importable (any subcommand, including `doctor --help`) | 1 | [VERIFIED] W2-05 (Python 3.13 without PyYAML) |

## doctor

This section covers `doctor scan`, `init-config`, `history`, `rollback`, and `self-check`.

The gate function (`exit_code_for_summary`, `src/somnus_debug/doctor/core.py:2046-2058`):

```python
if gate == "none":     return 0
if gate == "critical": return 2 if critical else 0
if gate == "serious":  return 2 if critical else (1 if serious else 0)
if gate == "minor":    return 1 if critical or serious or minor else 0
if gate == "info":     return 1 if total else 0
return 1
```

(Quoted from source. `Executed: no` as a standalone snippet; its behavior is verified below.)

| Condition | Exit | Evidence |
|---|---:|---|
| gate passed, including **zero files scanned** | 0 | [VERIFIED] lane D D17/D38; W2-14 baseline (`serious=0`) |
| default gate `serious`: serious findings, no critical | 1 | [VERIFIED] W2-10 (`serious=2` -> 1) |
| `serious` or `critical` gate: any critical finding | 2 | [VERIFIED] W2-08 (`def oops(:` -> 2) |
| gate `minor` or `info` with any finding, **even critical** | 1 | [VERIFIED] W2-08 (critical file, `"minor"` gate -> 1) |
| gate `minor`, only info-level findings | 0 | [VERIFIED] lane F doc-reconciliation P4 |
| gate `"none"` (quoted) | 0 | [VERIFIED] W2-08 |
| gate `none` **unquoted** (parsed as null) | 4 | [VERIFIED] W2-08: `Configuration value must be a non-empty string.`, context `"value": "None"`. See [D-03](../DISCOVERY-LEDGER.md#d-03) |
| argparse error (unknown flag, `--limit abc`, missing `--run-id`, `doctor --version`) | 2 | [VERIFIED] W2-08 (`--bogus`); lane D D11, D19, D20, D42, C02 |
| `DoctorError`: missing root under `--no-state` or an uncreatable/non-directory path (a writable missing root with state on exits 0, [D-29](../DISCOVERY-LEDGER.md#d-29)), missing config, malformed JSON config, non-bool for a bool key, invalid gate, init-config target exists, unknown run ID, unusable state DB for history/rollback, unwritable output | 4 | [VERIFIED] W2-08 (missing root, run with `--no-state` per review-h re-run), W2-16 (unknown run ID), W2-21 (missing config); lane D D16, D18, D21, D23, D26_bogus, D33, D34, D40, D41, D43 |
| malformed **YAML** config | structural errors (bad indent, missing colon, mixed list/map, missing child block) exit 4; unbalanced flow/quote text is kept as a literal string, accepted by string keys and rejected (exit 4) by int/bool/list keys; defaults are never substituted [VERIFIED review-h; `src/somnus_debug/doctor/core.py:619-643,681-723`] | [VERIFIED] lane D D30. See [D-04](../DISCOVERY-LEDGER.md#d-04) |
| state DB unusable during `scan` | warning on stderr, then the gate result (not 4) | [VERIFIED] lane D D39 |
| `RecursionError` (or another classified runtime error) on the **serial** analysis path, i.e. `max_workers: 1` or a one-file project | 5, no report | [VERIFIED] lane D D44; narrowed in [execution-model](../01-system/execution-model.md) |
| the same error on the threaded path (two or more files) | the file gets a critical `analysis_read_errors` issue; the scan completes and exits by the gate | [VERIFIED] see [execution-model](../01-system/execution-model.md) |
| exception types outside the two tiers (for example `KeyError`) | traceback, exit 1 | [SOURCE-CONFIRMED] `:2184-2199`; not triggered |
| `self-check` on the installed doctor | 1 (17 serious findings on itself) | [VERIFIED] lane D D14 |

Exit 3 is never produced by doctor. `docs/MANUAL.md` section 3.4 documents only "0 / non-zero" and does not mention the `none` or `info` gates. [DOCUMENTED-ONLY] vs [SOURCE-CONFIRMED].

## structure

This section covers `somnus-debug structure` and `somnus-structure`.

| Condition | Exit | Evidence |
|---|---:|---|
| index written to stdout or to `-o`/`--update-doc` | 0 | [VERIFIED] W2-15, W2-22 |
| missing file, directory, syntax error, stamped metadata header, output `OSError` | 2 (`error: ...` on stderr) | [VERIFIED] W2-15 (stamped); lane D S14, S15, S17. See [D-01](../DISCOVERY-LEDGER.md#d-01) |
| argparse error (no source, `-o` with `--update-doc`, unknown flag, `--version`) | 2 | [VERIFIED] lane D S13, S16, C03 |
| non-UTF-8 source | 1 (uncaught `UnicodeDecodeError`) | [VERIFIED] W2-09 |

Usage errors and analysis errors share code 2.

## pycache-clean

This section covers `somnus-debug pycache-clean` and `somnus-pycache-clean`.

| Condition | Exit | Evidence |
|---|---:|---|
| success, dry-run or real | 0 | [VERIFIED] W2-18 |
| a configured root does not exist (logged as ERROR) | **0** | [VERIFIED] lane D P01, P03 |
| config file not found | 1 | [VERIFIED] lane D P04 |
| `roots: []`, or any exception inside the cleaner (logged traceback) | 1 | [VERIFIED] lane D P05 |
| malformed YAML or a non-mapping top level (uncaught traceback) | 1 | [VERIFIED] lane D P06, P07 |
| wrong-typed value such as `max_depth: "2"` | 1 | [VERIFIED] lane B P7 |
| argparse error | 2 | [VERIFIED] lane D P08, P10 |

## init-test-harness

This section covers the scaffolder.

| Condition | Exit | Evidence |
|---|---:|---|
| files written | 0 | [VERIFIED] W2-19 |
| a destination exists and `--force` is not given; target path is an existing file | 1 | [VERIFIED] lane D H02, H05, H07 |
| argparse error | 2 | [VERIFIED] lane D H06 |

## Scaffolded run_test.py

This section covers the copied harness program.

| Condition | Exit | Evidence |
|---|---:|---|
| verdict PASS | 0 | [VERIFIED] W2-19 (edited harness under `tools/`) |
| verdict FAIL, including the unedited cargo test and any `--help` (argv is ignored) | 1 | [VERIFIED] W2-19; lane D H09 |
| `KeyboardInterrupt`/`SystemExit` inside `execute_test` | not caught; no manifest | [SOURCE-CONFIRMED] lane F [harness.md](../_evidence/agent-findings/lane-f-ext/harness.md) H-5 |

## Fieldkit scripts

This section lists the documented and observed codes of the three fieldkit scripts.

| Script | 0 | 1 | 2 | 3 |
|---|---|---|---|---|
| `selftest.py` | all checks pass | any check fails | (not used) | CLI unavailable |
| `onboard.py` | ok | usage error or bad repo path; **also** a doctor config error (traceback; the docs promise 2) | coverage failure (zero files) | CLI unavailable |
| `delta.py` | clean | new serious/critical finding; **also** a malformed issue object (traceback) | coverage regression; **also** argparse usage errors | input error |

[VERIFIED] W2-04 (selftest 0 and 1); W2-14/W2-17 (delta 1 and 0); lane D F01-F03, O01-O08, T01-T08; lane F [fieldkit.md](../_evidence/agent-findings/lane-f-ext/fieldkit.md) OB-2, D5, D8. See [D-20](../DISCOVERY-LEDGER.md#d-20) and [D-21](../DISCOVERY-LEDGER.md#d-21).

## Telling codes apart as a caller

This section gives the disambiguation rules automation needs, because several codes are overloaded. See [D-18](../DISCOVERY-LEDGER.md#d-18).

- **doctor 2: findings or usage?** An argparse error writes no report and prints `usage:` plus `error:` on stderr. A critical-gate result always prints `Scan complete:` on stdout and writes the JSON. Check for the JSON file or the `Scan complete:` line. [VERIFIED] W2-21, where the gate script uses the JSON's existence.
- **doctor 1 under `minor`/`info`: is there a critical?** Read `summary.critical_issues` from the JSON. The exit code alone does not say.
- **doctor 0 with `files=0`**: a zero-file scan passes every gate. Always check `summary.files_scanned > 0`. See [D-17](../DISCOVERY-LEDGER.md#d-17).
- **structure 2**: there is no reliable machine signal. Parse stderr for `error: invalid syntax` (an analysis failure) versus `usage:` (argparse).
- **pycache-clean 0**: it does not mean every root existed. Search the output for `[ERROR] Root path does not exist`.
- **delta.py 2**: it can mean coverage regression or bad arguments. Validate arguments before calling it.

## Sources

This section lists the code and evidence this page draws on.

- `src/somnus_debug/cli.py:99-122`
- `src/somnus_debug/doctor/core.py:2046-2058`, `:2184-2201`
- `src/somnus_debug/structure/core.py:323-347`
- `src/somnus_debug/pycache_cleaner/core.py:349-372`
- `src/somnus_debug/test_harness/scaffold.py:112-125`
- [lane D exit-codes.md](../_evidence/agent-findings/lane-d-cli-tests/exit-codes.md), [experiment-log.md](../_evidence/agent-findings/lane-d-cli-tests/experiment-log.md)
- [lane B configuration-findings.md](../_evidence/agent-findings/lane-b-config/configuration-findings.md)
- [lane F fieldkit.md](../_evidence/agent-findings/lane-f-ext/fieldkit.md), [harness.md](../_evidence/agent-findings/lane-f-ext/harness.md), [doc-reconciliation.md](../_evidence/agent-findings/lane-f-ext/doc-reconciliation.md)
- [execution-model](../01-system/execution-model.md) (serial-path narrowing of exit 5)
- W2 runs: [verification-results](../11-verification/verification-results.md#w2-runs)
