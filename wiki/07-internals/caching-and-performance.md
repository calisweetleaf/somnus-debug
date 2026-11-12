# Caching and performance

This page states what the toolkit caches (almost nothing), where its time goes, and how it scales. The numbers come from one measured run, described in "Measured cost" below. Everything else is read from source.

## What is cached

This section lists every reuse of computed results, which is a short list.

| Item | Cached? | Detail |
|---|---|---|
| Analysis results between runs | **no** | Every scan re-reads and re-analyzes every file. The state DB stores hashes for the delta report only; unchanged files are not skipped. [SOURCE-CONFIRMED] `src/somnus_debug/doctor/core.py:1705-1732` (no use of `previous_index` before analysis) |
| Parsed config | per `ConfigManager` instance | Built once per command. [SOURCE-CONFIRMED] |
| Stdlib name set | **rebuilt per file** | `ImportResolver.__init__` builds `set(sys.stdlib_module_names) | set(sys.builtin_module_names)` for each `FileAnalyzer`. [SOURCE-CONFIRMED] `:998-1001`, `:1518` |
| `find_spec` results | indirectly | `importlib` caches finders and `sys.modules` hits, but the doctor itself keeps no memo of third-party lookups. [SOURCE-CONFIRMED] `:1050-1055` |
| Module map | per scan | Built once by `ProjectFileIndex` and shared read-only by all workers. [SOURCE-CONFIRMED] |
| Bytecode | n/a | The package never compiles targets; `ast.parse` only. |

The state store's file hashes could support incremental scans, but the code does not use them that way. [SOURCE-CONFIRMED]

## Work per file

This section breaks down one file's analysis, so you can see what dominates.

1. Read with `tokenize.open`: one full read, with encoding detection.
2. Tokenize the whole source again, for TODO comments.
3. `ast.parse`.
4. One `ImportCollector` walk plus one `LoadedNameCollector` walk.
5. One `CodeQualityVisitor` walk. For each function it also runs `ast.walk(node)` twice, once in `cyclomatic_complexity` and once for `return_count`. Nested functions are walked again by every enclosing function. Each exception handler gets a synthetic module walk.
6. `stat`, then `stable_hash_file`: a **second full read** of the file, in 1 MiB chunks.

[SOURCE-CONFIRMED] `src/somnus_debug/doctor/core.py:1520-1546`, `:1254-1255`, `:1423-1433`, `:1485-1487`, `:1588-1595`. Per-function `ast.walk` makes deeply nested code roughly quadratic in nesting depth. [HYPOTHESIS] from the code shape; not benchmarked.

The hash is taken after the analysis, not over the same bytes that were analyzed. A file edited mid-scan can get a hash that does not match its findings. [SOURCE-CONFIRMED] `:1523` vs `:1595`; the race itself was not observed.

## Project-level costs

This section covers the steps that scale with the whole project rather than one file.

- **Cycle detection.** A DFS from every node, with path length capped below 30 and an early stop once at least 100 cycles exist after a start node finishes. `visiting` is reset per start node, so worst-case cost is exponential in graph density. The caps bound the depth, not the branching. [SOURCE-CONFIRMED] `:1634-1656`. Typical import graphs are sparse. [HYPOTHESIS]
- **Report size.** The JSON includes every file's imports, edges, functions, classes, and `code_map`. Every issue appears twice: top level and per file. The Markdown has a section per file with an evidence block per issue.
- **Memory.** All `FileAnalysisResult` objects, the full JSON string, and the full Markdown string are held in memory before writing. [SOURCE-CONFIRMED] `:2078-2086`.

## Measured cost

This section gives one real measurement and what it shows about the thread pool.

Setup: a copy of this repository's `src/`, `skills/`, `tests/`, and root `*.py`, plus four extra copies of `src/`. That is 68 Python files and 26,596 lines. The run used `ConfigManager(None)` with `max_workers` overridden by `dataclasses.replace`, Python 3.12.15, on a 2-CPU sandbox (`nproc` = 2).

| `max_workers` | Files | Issues | Scan | Render (md + json) | Markdown | JSON |
|---:|---:|---:|---:|---:|---:|---:|
| 1 | 68 | 809 | 1.05 s | 0.09 s | 642 KiB | 2798 KiB |
| 2 | 68 | 809 | 1.11 s | 0.09 s | 642 KiB | 2798 KiB |
| 4 | 68 | 809 | 1.21 s | 0.13 s | 642 KiB | 2798 KiB |
| 8 | 68 | 809 | 1.15 s | 0.10 s | 642 KiB | 2798 KiB |

[VERIFIED] `/tmp/w1/ex_perf.py`, exit 0, single run per row (wall clock; no repetition, so differences of about 0.1 s are noise).

Readings:

- Threads gave **no speedup**. The serial path was the fastest, as expected for GIL-bound AST work.
- Throughput is roughly 25k lines per second on this machine.
- The JSON report is about 4.4 times the size of the Markdown and roughly 100 times the size of the source it describes (about 2.8 MB for about 26.6k lines).

Practical advice that follows:

- `max_workers: 1` costs nothing in speed. It does remove per-file error containment ([execution-model](../01-system/execution-model.md#doctor-the-serial-path-drops-the-error-wrapper)), so do not choose it for robustness.
- Large monorepos should expect JSON reports of tens of MB. [HYPOTHESIS] extrapolated.

## Other tools

This section notes the performance shape of the remaining tools.

- **structure**: one parse and a few walks per file. `ast.walk` over the whole tree for scoped classes. Negligible. [SOURCE-CONFIRMED]
- **pycache-clean**: one `os.scandir` per directory. `_get_dir_size` runs `os.walk` over each target directory before deleting it, even in dry runs, so cost scales with cached-file count. No parallelism. [SOURCE-CONFIRMED] `src/somnus_debug/pycache_cleaner/core.py:274-321`.
- **scaffold**: two small file writes.

## Sources

This section lists the code, evidence files, and probes this page rests on.

- `src/somnus_debug/doctor/core.py:998-1001`, `:1050-1055`, `:1254-1255`, `:1423-1433`, `:1485-1487`, `:1520-1546`, `:1588-1595`, `:1634-1656`, `:1705-1732`, `:2078-2086`
- `src/somnus_debug/pycache_cleaner/core.py:274-321`
- Executed probe: `/tmp/w1/ex_perf.py` (setup commands: copy of repo `src/`, `skills/`, `tests/`, root `*.py`, and `src/` copied four times into `/tmp/w1/perf`)
