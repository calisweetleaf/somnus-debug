# Lane D (CLI/Tools/Integration) + E (Tests/Runtime/Failure modes)

Files:
- `command-reference.md`: verbatim help for every surface, behavior, output contracts, artifacts, detector results
- `exit-codes.md`
- `experiment-log.md` + `experiments.jsonl` (raw stdout/stderr/file deltas per run)
- `test-coverage.md`
- `install-vs-source.md`
- `help-surfaces-raw.txt`

Top findings (all VERIFIED by execution unless noted):
1. **Repo tests: 10 passed, 2 failed.** Both failures come from `structure`'s `type_comments=True`, which is still present in `src/somnus_debug/structure/core.py:210`. The 2026-11-05 fix exists only in the root `analyze_python_structure.py`. src, the venv install, and PyPI 0.1.0 all crash (exit 2) on any metadata-stamped file, including their own source. This contradicts STATE.md's "smoke 12/12".
2. **PyPI 0.1.0 code is identical to src after stripping the metadata headers.** The only real difference is the reference-only `default_config.yaml` (PyPI has the old MCP globs). Root `python_production_doctor.py` lacks src's SQLite-unavailable fallback. There is no `somnus-init-test-harness` script.
3. **Doctor defects:**
   - `return 1` is flagged as a serious `placeholder_returns` (`1 == True` in `PLACEHOLDER_CONSTANTS`).
   - Same-second scans share a run ID, and `INSERT OR REPLACE` silently drops history.
   - Gates `minor`/`info` return 1 even when critical findings exist.
   - Malformed YAML config is silently accepted.
   - `python_doctor.yaml` is never auto-discovered.
   - `-v`/`--verbose` does nothing, and the log stays empty on success.
   - One pathological file (RecursionError) aborts the whole scan with exit 5.
   - `from pkg import mod` import cycles are missed.
   - There is no hardcoded-secret detection, and print is not a detector.
   - `test_gaps` is never emitted.
   - stubs/duplicates false positives on abstractmethod, Protocol, overload, and property setter are confirmed. `silent_failures` is name-sensitive.
   - `self-check` writes reports and state into the installed package directory.
4. **The dispatcher hard-requires PyYAML for every subcommand.** It imports pycache_cleaner eagerly, so doctor is unusable via `somnus-debug` without PyYAML. pycache_cleaner also emits a `SyntaxWarning` on cold import.
5. **pycache-clean:**
   - Dry-run output says "Removed… / deleted N" even though nothing is deleted.
   - A missing root still exits 0.
   - Bad YAML gives an uncaught traceback.
   - An unknown config key silences all subsequent logging (`basicConfig` pre-empted).
6. **init-test-harness / run_test.py:**
   - The template ignores `--help` and executes.
   - Its default `PROJECT_ROOT` is `__file__/../..`, so scaffolding at a repo root (as MANUAL shows) writes artifacts to `<repo>/../test-runs/`.
   - The default test is a cargo/gp-cli test that fails out of the box.
   - Scaffolded files carry the template's artifact URNs.
7. **Fieldkit:**
   - selftest passes 29/29 against the installed CLI, but its structure check has a blind spot for stamped files.
   - onboard and delta exit codes match their docs.
   - onboard `--apply` writes the profile even when verification fails, and a rerun overwrites the baseline.
