# Execution model

This page describes how the tools run: in which process, on which threads, in what order, and how deterministic the output is. It matters most for the doctor, which is the only tool with concurrency.

## One process, synchronous entry points

This section states the basic model shared by all four tools.

Every tool is a synchronous function called in the current process. Nothing spawns subprocesses (the scaffolded `run_test.py` template is the exception, and it is not part of the package's runtime), nothing uses `asyncio`, and nothing forks. [SOURCE-CONFIRMED] grep for `asyncio|multiprocessing|subprocess` over `src/somnus_debug/**/*.py` finds only `SECURITY_CALLS` string literals in `src/somnus_debug/doctor/core.py:514` and the template. The only concurrency primitive is the doctor's `ThreadPoolExecutor` (`src/somnus_debug/doctor/core.py:1724`).

Running through `somnus-debug` adds one layer: the dispatcher swaps `sys.argv` for the duration of the call (`src/somnus_debug/cli.py:96-104`). That swap is process-global, so calling `cli.main` from two threads at once is unsafe. [HYPOTHESIS] based on the source; not exercised.

## Doctor: where threads are used

This section explains the doctor's thread pool, the only parallel part of the system.

`ProjectScanner._analyze_files` (`src/somnus_debug/doctor/core.py:1716-1732`):

1. `max_workers = min(config.max_workers, max(1, n_files))`. Default `max_workers` is 4 (`:499`).
2. If that is 1, files are analyzed serially in sorted order on the calling thread.
3. Otherwise a `ThreadPoolExecutor(max_workers)` runs `FileAnalyzer(path, index, cm).analyze` per file. Results are collected with `as_completed` and then sorted by `relative_path`.

Each `FileAnalyzer` builds its own `SourceReader`, `ImportResolver`, `DiagnosticIssueFactory`, and `CodeQualityVisitor`, so no mutable state is shared between workers. The shared objects (`ProjectFileIndex`, `ConfigManager`, `DoctorConfig`) are only read during the scan; `DoctorConfig` is a frozen dataclass. [SOURCE-CONFIRMED] `:1510-1518`, `:1527`, `:1542`, `:208`.

The work is CPU-bound Python (tokenize, `ast.parse`, AST walks) and runs under the GIL, so threads give little speedup beyond overlapping file I/O. [HYPOTHESIS] not benchmarked; see [caching-and-performance](../07-internals/caching-and-performance.md).

## Doctor: the serial path drops the error wrapper

This section documents an asymmetry between the threaded and serial paths that changes how failures surface.

On the threaded path, an exception of type `DoctorError`, `OSError`, `RuntimeError`, `TypeError`, `ValueError`, or `LookupError` raised by one file's analysis is converted into a synthetic `analysis_read_errors` issue for that file, and the scan continues (`:1726-1731`, `:1734-1738`). On the serial path there is no `try`: the exception propagates to `main`, which returns 4 (`DoctorError`) or 5 (the classified runtime types), and no report is written.

The serial path is taken whenever `max_workers` is 1 **or the project has exactly one Python file**.

[VERIFIED] `/tmp/w1/ex_serial.py` (exit 0): with `FileAnalyzer.analyze` patched to raise `ValueError`, a two-file project produced two `analysis_read_errors` issues ("Analyzer execution failed: ValueError: injected"), while a one-file project let the `ValueError` escape `ProjectScanner.scan`. This narrows [D-18](../DISCOVERY-LEDGER.md#d-18), which records that a `RecursionError` aborts the whole scan with exit 5 ([lane-d experiment D44](../_evidence/agent-findings/lane-d-cli-tests/experiment-log.md)). The abort happens only on the serial path. [VERIFIED] in `/tmp/w1` with a 20,000-term `1+1+...` expression and `python3 -m somnus_debug.doctor.core scan <dir> --no-state`:

| Project | Exit | Outcome |
|---|---:|---|
| `rec1/`: `deep.py` only | 5 | `Unclassified runtime failure: RecursionError: maximum recursion depth exceeded during ast construction`; no report |
| `rec2/`: `deep.py` plus `ok.py` | 2 | scan completes; `deep.py` gets one critical `analysis_read_errors` issue, "Analyzer execution failed: RecursionError ..." |

`RecursionError` subclasses `RuntimeError`, which the worker wrapper catches.

## Ordering and determinism

This section says which outputs are stable from run to run and which are not.

| Output | Ordering rule | Source |
|---|---|---|
| discovered files | sorted by relative POSIX path | `src/somnus_debug/doctor/core.py:982` |
| `ProjectAnalysisResult.files` | sorted by `relative_path` after the pool | `:1732`, `:1755` |
| per-file `issues` | `dedupe_issues`: sorted by (file, line, `severity.value` string, category, symbol) | `:1361-1371` |
| project `issues` | sorted by (file, line, category) | `:1714` |
| cycles | `canonical_cycle` rotation, set, then sorted | `:1682-1687`, `:1644` |
| JSON | `json.dumps(sort_keys=True)` | `:578-580` |

Within one line, per-file ordering uses the severity string, so the order is alphabetical (`critical` < `info` < `minor` < `serious`), not by severity rank. [SOURCE-CONFIRMED] `:1371`; [lane-a architecture §3.3](../_evidence/agent-findings/lane-a-arch-api/architecture.md).

Not deterministic between runs:

- `run_id`, `started_at`, and `finished_at` come from the clock.
- `modified_time` is the file mtime.
- Import classification depends on the interpreter running the doctor: `third_party` is decided by `importlib.util.find_spec` in that process (`:1050-1055`), and stdlib membership by `sys.stdlib_module_names` plus `sys.builtin_module_names` (`:1001`). [VERIFIED] [D-26](../DISCOVERY-LEDGER.md#d-26).

Given the same tree, config, and interpreter, issues and summary counts are reproducible. [VERIFIED] two consecutive stateful scans of the same fixture gave identical counts (37 issues, 2 critical, 13 serious) in `/tmp/w1/ex_state.py`.

## Run identity and time

This section explains how a run is named, because the name is also the database key.

`run_id = utc_now().strftime("%Y%m%dT%H%M%SZ")` has one-second resolution (`:82`, `:530-532`). It is the primary key of `runs` and the name of the per-run report directory, and every insert is `INSERT OR REPLACE`. Two scans of one project within the same second therefore leave one run. [VERIFIED] `/tmp/w1/cli`: two back-to-back `doctor scan proj` runs (both exit 2) left one row in `runs`, and `history` listed one run. Same result in [lane-a architecture §3.4](../_evidence/agent-findings/lane-a-arch-api/architecture.md). See [D-08](../DISCOVERY-LEDGER.md#d-08).

## Other tools

This section covers the execution model of the three smaller tools in one place.

- **structure**: one file, one `ast.parse`, no threads. Pure apart from reading the input and writing the output. [SOURCE-CONFIRMED] `src/somnus_debug/structure/core.py:323-347`.
- **pycache-clean**: single-threaded, iterative depth-first traversal with an explicit stack of `(path, depth)`. Deletions happen during traversal, so a crash midway leaves a partially cleaned tree. Per-entry `OSError` is swallowed at DEBUG level. [SOURCE-CONFIRMED] `src/somnus_debug/pycache_cleaner/core.py:220-258`.
- **init-test-harness**: checks every destination for existence first, then writes. Not atomic: a failure on the second write leaves the first file in place. [SOURCE-CONFIRMED] `src/somnus_debug/test_harness/scaffold.py:75-88`.

## Sources

This section lists the code, evidence files, and probes this page rests on.

- `src/somnus_debug/doctor/core.py:82`, `:208`, `:530`, `:578`, `:982`, `:1050-1055`, `:1361-1371`, `:1510-1546`, `:1682-1738`
- `src/somnus_debug/cli.py:85-104`, `src/somnus_debug/structure/core.py:323-347`, `src/somnus_debug/pycache_cleaner/core.py:220-258`, `src/somnus_debug/test_harness/scaffold.py:62-88`
- [lane-a architecture.md §3](../_evidence/agent-findings/lane-a-arch-api/architecture.md), [lane-d experiment-log.md](../_evidence/agent-findings/lane-d-cli-tests/experiment-log.md)
- Executed probes: `/tmp/w1/ex_serial.py`, `/tmp/w1/ex_state.py`, `/tmp/w1/cli` (CLI runs)
