# Command contract

Use the installed CLI's help first when it differs from this snapshot. This guide is organized by actual command surface, not by a generic debugging workflow.

Pinned source landmarks: [`doctor` manual](https://github.com/calisweetleaf/somnus-debug/blob/3ad5e8366ab5d527aa45313a1b535e8912a2dcf3/docs/MANUAL.md#L81), [doctor state](https://github.com/calisweetleaf/somnus-debug/blob/3ad5e8366ab5d527aa45313a1b535e8912a2dcf3/docs/MANUAL.md#L153), [`structure`](https://github.com/calisweetleaf/somnus-debug/blob/3ad5e8366ab5d527aa45313a1b535e8912a2dcf3/docs/MANUAL.md#L170), [`pycache-clean`](https://github.com/calisweetleaf/somnus-debug/blob/3ad5e8366ab5d527aa45313a1b535e8912a2dcf3/docs/MANUAL.md#L208), [`init-test-harness`](https://github.com/calisweetleaf/somnus-debug/blob/3ad5e8366ab5d527aa45313a1b535e8912a2dcf3/docs/MANUAL.md#L258), and [doctor YAML/report behavior](https://github.com/calisweetleaf/somnus-debug/blob/3ad5e8366ab5d527aa45313a1b535e8912a2dcf3/docs/Python_Doctor_QUICKSTART.md#L26).

## Verify availability

```console
somnus-debug --version
somnus-debug --help
somnus-debug doctor --help
somnus-debug structure --help
somnus-debug pycache-clean --help
somnus-debug init-test-harness --help
```

Do not install into a global or project environment silently. If the CLI is absent, report it and follow the user's installation policy. The package is published on PyPI as `somnus-debug`; the current published package version and Git tag are recorded separately in `provenance.md` because their numbering differs.

## `doctor`

The doctor's exact command tree is:

```text
somnus-debug doctor scan [project_root] [-c CONFIG] [-o OUTPUT] [--json-output PATH] [--no-state] [-v]
somnus-debug doctor init-config [-o OUTPUT] [--force]
somnus-debug doctor history [project_root] [-c CONFIG] [--limit N]
somnus-debug doctor rollback [project_root] --run-id RUN_ID [-c CONFIG]
somnus-debug doctor self-check [-c CONFIG] [-o OUTPUT] [--json-output PATH] [--no-state]
```

Common operations:

```console
somnus-debug doctor init-config -o .somnus-debug/python_doctor.yaml
somnus-debug doctor scan . -c .somnus-debug/python_doctor.yaml -o .somnus-debug/runs/baseline.md --json-output .somnus-debug/runs/baseline.json
somnus-debug doctor scan . -c .somnus-debug/python_doctor.yaml --no-state -o /tmp/somnus-debug-report.md --json-output /tmp/somnus-debug-report.json
somnus-debug doctor history . -c .somnus-debug/python_doctor.yaml --limit 10
somnus-debug doctor self-check
```

Create the parent directory before writing the config or reports. Confirm the output path is inside the active repository's local state area or a deliberate temporary location. `init-config` writes the default. Read and adapt `include_patterns` before the first scan. Do not use `--force` to overwrite an existing config without reviewing and preserving it.

The scan's exit status is gated by `severity_exit_level` (default `serious` in the checked source). A nonzero status can mean findings exceeded the gate or a runtime failure; read the report and log. Setting the threshold lower or excluding files to make a command green is not a fix.

Stateful runs are stored in `.python_doctor/` within the scanned project root. `history` depends on that state. `rollback` restores a previous report as latest and does not change source files.

## `structure`

```console
somnus-debug structure path/to/file.py
somnus-debug structure path/to/file.py -o .somnus-debug/indexes/file-index.md
somnus-debug structure path/to/file.py --update-doc path/to/existing-index.md
```

The index covers one Python file. By default it includes classes, nested classes, module-level functions, methods, signatures, decorators, doc summaries, and line spans. Use flags from `somnus-debug structure --help` for a narrower view. `--update-doc` writes an existing doc in place; check the target first.

Use it before editing dense or unfamiliar Python files and after editing when the definition layout changed. Store generated indexes locally only when they will help the ongoing work; don't generate repository-wide index debris.

## `pycache-clean`

There is no bare-root CLI mode. The YAML config must contain `roots:`. A typical config is:

```yaml
roots:
  - /absolute/path/to/project
exclude:
  - "node_modules/*"
  - ".git/*"
targets:
  - "__pycache__"
  - "*.pyc"
  - "*.pyo"
dry_run: true
verbose: false
max_depth: null
follow_symlinks: false
log_file: null
```

Always preview:

```console
somnus-debug pycache-clean --config .somnus-debug/pycache.yaml --dry-run --verbose
```

Review the listed roots and targets. A live pass deletes matched caches. Only run it when cleanup is in scope and the operator's authorization boundary permits it. Keep a reviewed config with the intended roots; do not widen it casually.

## `init-test-harness`

```console
somnus-debug init-test-harness path/to/repo
somnus-debug init-test-harness . --no-contract
```

The scaffold creates a portable `run_test.py` and, by default, `CONTRACT.md`. It refuses to overwrite existing files. Use it only when the target project lacks an established harness and wants this single-test contract. Never add `--force` just to get past the refusal.

The contract says the project owns its test name, `execute_test()`, real boundary, acceptance checks, and PASS/FAIL decision. A run should produce `manifest.json`, `report.md`, and `test.log` with a unique run ID. Metrics only become gates when project acceptance explicitly makes them so. Exceptions remain failures. Accelerate, CI, a skill, or another orchestrator can invoke this surface without defining its meaning.

## Capability selection

Use `doctor` for repeated Python diagnostics; `structure` for targeted AST maps; `pycache-clean` only for an authorized cleanup; `init-test-harness` only for an accepted project-owned harness. “Use somnus-debug fully” means exercise the tools that fit the work, not run mutation-oriented commands on every session.
