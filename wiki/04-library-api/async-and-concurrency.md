# Async and concurrency

This page states what concurrency the library uses and what is safe to do from threads or async code. The short answer: there is no async API, the doctor uses a private thread pool, and several entry points touch process-global state.

## No async API

This section records the search for async code and its result.

No function in `src/somnus_debug/` is `async def`. Nothing imports `asyncio`, and there are no callbacks or event hooks. [SOURCE-CONFIRMED] grep for `async |await |asyncio` over `src/somnus_debug/**/*.py`: the only hit is the string `"async def"` that the structure indexer prints for async functions (`src/somnus_debug/structure/core.py:90`). The doctor analyzes `async def` targets: `visit_AsyncFunctionDef` records `kind="async_function"` (`src/somnus_debug/doctor/core.py:1211-1213`).

To call the library from async code, run the blocking call in a worker thread:

```python
import asyncio
from pathlib import Path
from somnus_debug.doctor import core as d

async def scan(root: str):
    cm = d.ConfigManager(None)
    return await asyncio.to_thread(lambda: d.ProjectScanner(Path(root), cm).scan({}))

print(asyncio.run(scan("proj")).summary.total_issues)
```

Executed: yes (`/tmp/w1/ex_async.py`, lane-a fixture, exit 0). It printed `37`.

## The doctor's thread pool

This section describes the only concurrency inside the package.

`ProjectScanner._analyze_files` runs `FileAnalyzer.analyze` for each file in a `concurrent.futures.ThreadPoolExecutor` sized `min(max_workers, n_files)`. The pool is not used when that number is 1. [SOURCE-CONFIRMED] `src/somnus_debug/doctor/core.py:1716-1732`. Behavior that follows from this:

- **No shared mutable state between workers.** Each worker gets its own `FileAnalyzer`, which builds its own resolver, factory, and visitor. The shared `ProjectFileIndex`, `ConfigManager`, and frozen `DoctorConfig` are only read. [SOURCE-CONFIRMED] `:1510-1518`, `:1527`, `:1542`.
- **Errors are contained per file only on the threaded path.** [VERIFIED] `/tmp/w1/ex_serial.py`. See [execution-model](../01-system/execution-model.md#doctor-the-serial-path-drops-the-error-wrapper).
- **Result order is fixed.** Results are re-sorted by relative path. [SOURCE-CONFIRMED] `:1732`.
- **No real speedup is expected.** The work is pure-Python AST processing under the GIL. [HYPOTHESIS] Not benchmarked; see [caching-and-performance](../07-internals/caching-and-performance.md).
- **No cancellation or timeout.** A pathological file blocks its worker until it finishes or raises. [SOURCE-CONFIRMED]

`max_workers` is config-only; there is no CLI flag. `max_workers: 1` forces the serial path. [SOURCE-CONFIRMED] `:499`, [lane-b configuration-findings §2.1](../_evidence/agent-findings/lane-b-config/configuration-findings.md).

## Thread safety of entry points

This section rates each entry point for concurrent use within one process.

| Entry point | Safe to call concurrently? | Why |
|---|---|---|
| `ConfigManager(...)` | yes | reads a file and returns new objects |
| `ProjectScanner(...).scan(...)` | yes, for different instances | no globals are written; uses its own pool. `importlib.util.find_spec` takes the import lock [SOURCE-CONFIRMED] |
| `MarkdownReportWriter.render`, `dumps_json`, `exit_code_for_summary`, AST predicates | yes | pure |
| `build_index` | yes | pure |
| `StateStore` on one project | **no** | a fixed temp filename `.<name>.tmp` (`:2016`), `INSERT OR REPLACE` keyed by one-second `run_id`, no locking. SQLite WAL serializes the SQL, but report files can race [HYPOTHESIS] |
| `doctor.main` | **no** | `logging.basicConfig(force=True)` swaps the process-wide root handlers; it writes `./production_doctor.log` relative to the process cwd [SOURCE-CONFIRMED] `:2179-2181` |
| `cli.main` | **no** | assigns `sys.argv` for the duration of the call [SOURCE-CONFIRMED] `src/somnus_debug/cli.py:96-104` |
| `PycacheCleaner.run` | **no** for overlapping roots | concurrent deletes in the same tree; logging goes through the root logger, which auto-configures [VERIFIED] handler install in `/tmp/w1` |
| `scaffold` | **no** for the same target | the existence check and the write are not atomic (check-then-act) [SOURCE-CONFIRMED] `src/somnus_debug/test_harness/scaffold.py:75-88` |

## Multiple processes

This section covers running several doctor processes against one project, as CI matrices and agents sometimes do.

There is no lock file. Two processes that scan the same project share `.python_doctor/state.sqlite3`. SQLite WAL handles concurrent connections safely. The design still leaves two hazards:

- If both runs land in the same UTC second, they get the same `run_id`, and one overwrites the other. [VERIFIED] [D-08](../DISCOVERY-LEDGER.md#d-08) (sequential case).
- Both write `production_doctor_report.md` and `latest.*` through the same temporary name. [HYPOTHESIS]

Give each run its own `--json-output`/`-o` path, or use `--no-state` for parallel jobs. [HYPOTHESIS] This is a mitigation derived from the source; it was not stress-tested.

## Sources

This section lists the code, evidence files, and probes this page rests on.

- `src/somnus_debug/doctor/core.py:499`, `:1211-1213`, `:1510-1546`, `:1716-1732`, `:2012-2020`, `:2179-2181`
- `src/somnus_debug/cli.py:85-104`, `src/somnus_debug/structure/core.py:90`, `src/somnus_debug/test_harness/scaffold.py:75-88`
- [lane-b configuration-findings.md](../_evidence/agent-findings/lane-b-config/configuration-findings.md), [lane-a architecture.md §3](../_evidence/agent-findings/lane-a-arch-api/architecture.md)
- Executed probes: `/tmp/w1/ex_async.py`, `/tmp/w1/ex_serial.py`
