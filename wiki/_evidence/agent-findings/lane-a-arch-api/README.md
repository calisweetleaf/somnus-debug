# Lane A+C findings (index, reconstructed)

This index was reconstructed by the lead from lane A's final report after a sandbox reset (about 00:40 UTC, 2026-11-12) removed the lane's original `README.md` and `undocumented-primitives.md`. The surviving files are the primary evidence.

## Surviving files

This section lists what remains and what it holds.

- [architecture.md](architecture.md): module boundaries, call graphs, lifecycle, state ownership.
- [api-reference.md](api-reference.md): callable surfaces, six executed library examples, CLI run table with exit codes.
- [symbols.tsv](symbols.tsv): 256 symbols in `src/`.
- `examples/ex1`-`ex7` (`.py.txt`): executed example scripts.
- `fixture/proj/**.py.txt`: the scan fixture, renamed so a doctor scan of the repo will not ingest its deliberately broken file.
- `ast_enum.py.txt`: the AST enumeration script.

## Lane A headline findings (from its final report)

This section preserves the lane's conclusions; each is integrated in the ledger.

- structure crashes on every stamped file (D-01); nested class double count (D-24).
- `from pkg import X` resolves to `pkg/__init__.py`, hiding cycles and missing siblings (D-06).
- Detector false positives incl. frozen dataclass, `__future__`/`__all__` unused imports, private-function attribution (D-07); `test_gaps` never emitted (D-05).
- Exit codes 0/1/2/4/5, argparse 2 overlap, `-v` ignored (D-18).
- SQLite WAL state, per-second run ids with INSERT OR REPLACE (D-08), rollback alias-only (D-09), fallback scan-only (D-28).
- cwd log, self-check writes into site-packages, `basicConfig(force=True)` (D-10, D-11); clean embedding via `ProjectScanner` (D-12).
- pycache scalar-roots hazard, missing long-path code (D-14); PyYAML needed by dispatcher (D-13).
- Harness template project-specific and misplaced by default (D-15).
- `pycache_cleaner/core.py:64` SyntaxWarning on compile; MANUAL references missing `docs/OPSEC.md`.
