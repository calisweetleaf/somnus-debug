## somnus-debug fieldkit

Use the global `somnus-debug-fieldkit` skill when the CLI applies to Python work in this repository. This is a supplemental diagnostic route; keep this repository's `AGENTS.md`, project tests, CI, acceptance criteria, and security policy authoritative.

### Required diagnose–repair–rescan loop

For any task that changes Python code, use `somnus-debug` iteratively:

1. Check `somnus-debug --version` and the command's `--help`; inspect this repo's doctor config and confirm its `include_patterns` cover the Python files in scope.
2. Run a doctor baseline before editing. Preserve the report/state locally when useful; use `--no-state` only for a disposable scan and report that it has no history.
3. Use `somnus-debug structure <file.py>` to orient on unfamiliar or structurally central Python files. Read source and tests; the index is AST structure, not runtime behavior.
4. Verify and classify relevant doctor findings. Fix actionable in-scope issues as part of the real task; record evidence-based dispositions for findings that are false positives or out of scope.
5. Run the repository's actual tests/build/acceptance gate and run doctor again after meaningful fixes. Compare the report with baseline and repeat while in-scope actionable findings remain, edited files are uncovered, or a new actionable regression appears.
6. Before handoff, review the final scan, its coverage, doctor history if available, and the native project gate. State any remaining finding or unavailable proof plainly.

Do not treat a green doctor severity gate as proof of integration, runtime behavior, security, or release readiness. A zero-file scan means the config is wrong for this repo. Do not lower thresholds or exclude files to obtain a green result.

### Tool boundaries

- `doctor` is configured Python static diagnostics; it is not a complete codebase graph.
- `structure` indexes one Python file's AST definitions and line spans; it does not import or execute the file.
- `pycache-clean` deletes matched caches. Always run `--dry-run`, inspect configured roots/exclusions, and perform a live pass only when cleanup is in scope and authorized.
- `init-test-harness` writes a project-owned `run_test.py` and usually `CONTRACT.md`. Use only if the repo wants that contract and lacks an established harness; never force-overwrite existing files without explicit authority.

Keep any doctor config, scan reports, `.python_doctor/` state, or optional hook inside this repository and follow its existing ignore/retention policy. Do not install a watcher, pre-commit system, dependency, or global tool automatically. In Somnus Accelerate, put the scan and native gate in the active packet's validation/evidence flow; Accelerate continues to own routing and task acceptance.

Exact flags: run `somnus-debug <command> --help`; see the global skill references and upstream [somnus-debug manual](https://github.com/calisweetleaf/somnus-debug/blob/master/docs/MANUAL.md).
