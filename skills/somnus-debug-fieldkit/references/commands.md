---
somnus:
  schema: "somnus://metadata/core/2.0.0"
  id: "urn:somnus:artifact:01a19ace-75d5-7489-b419-9cec8f06899f"
  revision: 1
  title: "Command contract"
  classification:
    category: "engineering"
    type: "report"
    role: "informative"
    scope: "component"
    tags: []
  lifecycle:
    status: "draft"
  authority:
    standing: "candidate"
    scopes:
      - target_ref: "urn:somnus:artifact:01a19ace-75d5-7489-b419-9cec8f06899f"
        aspects: ["content"]
  time: {}
  names:
    slug: "command-contract"
  knowledge:
    coverage: "artifact"
    subjects: ["urn:somnus:artifact:01a19ace-75d5-7489-b419-9cec8f06899f"]
  access:
    visibility: "internal"
    allowed_uses: ["archive", "search", "reason"]
  ingestion:
    disposition: "candidate"
    body_role: "narrative"
---
# Command contract

Use the installed CLI's help first when it differs from this snapshot. `scripts/selftest.py` proves every flag, default, exit code, and side effect listed here against the installed CLI. This guide is organized by command surface. `somnus-debug <cmd>` and `<python> -m somnus_debug.cli <cmd>` are interchangeable; in an onboarded repo, use the runner from `PROFILE.md` (see [install](install.md)).

Pinned source landmarks: [`doctor` manual](https://github.com/calisweetleaf/somnus-debug/blob/3ad5e8366ab5d527aa45313a1b535e8912a2dcf3/docs/MANUAL.md#L81), [doctor state](https://github.com/calisweetleaf/somnus-debug/blob/3ad5e8366ab5d527aa45313a1b535e8912a2dcf3/docs/MANUAL.md#L153), [`structure`](https://github.com/calisweetleaf/somnus-debug/blob/3ad5e8366ab5d527aa45313a1b535e8912a2dcf3/docs/MANUAL.md#L170), [`pycache-clean`](https://github.com/calisweetleaf/somnus-debug/blob/3ad5e8366ab5d527aa45313a1b535e8912a2dcf3/docs/MANUAL.md#L208), [`init-test-harness`](https://github.com/calisweetleaf/somnus-debug/blob/3ad5e8366ab5d527aa45313a1b535e8912a2dcf3/docs/MANUAL.md#L258), and [doctor YAML/report behavior](https://github.com/calisweetleaf/somnus-debug/blob/3ad5e8366ab5d527aa45313a1b535e8912a2dcf3/docs/Python_Doctor_QUICKSTART.md#L26).

## Verify availability

Confirm the CLI and every subcommand answer before relying on them.

```console
somnus-debug --version
somnus-debug --help
somnus-debug doctor --help
somnus-debug structure --help
somnus-debug pycache-clean --help
somnus-debug init-test-harness --help
```

Install with `pip install somnus-debug` (PyPI), preferably into the project's environment so doctor resolves the project's imports ([install](install.md)). Do not install silently into an environment you don't own. The Git tag and package version numbers differ; see `provenance.md`.

## `doctor`

The doctor's exact command tree is:

```text
somnus-debug doctor scan [project_root] [-c CONFIG] [-o OUTPUT] [--json-output PATH] [--no-state] [-v]
somnus-debug doctor init-config [-o OUTPUT] [--force]
somnus-debug doctor history [project_root] [-c CONFIG] [--limit N]
somnus-debug doctor rollback [project_root] --run-id RUN_ID [-c CONFIG]
somnus-debug doctor self-check [-c CONFIG] [-o OUTPUT] [--json-output PATH] [--no-state]
```

Common operations in an onboarded repo (see [onboarding](onboarding.md); `PROFILE.md` holds the repo's exact lines). Run them from `.somnus-debug/` so the doctor log lands there:

```console
cd .somnus-debug
somnus-debug doctor scan .. -c python_doctor.yaml -o runs/baseline.md --json-output runs/baseline.json
somnus-debug doctor scan .. -c python_doctor.yaml -o runs/latest.md --json-output runs/latest.json
somnus-debug doctor scan .. -c python_doctor.yaml --no-state -o /tmp/sd-report.md --json-output /tmp/sd-report.json
somnus-debug doctor history .. -c python_doctor.yaml --limit 10
```

`init-config` writes the CLI's default YAML (`include_patterns: ["*.py"]`, state in `.python_doctor/`). Prefer `scripts/onboard.py`, which generates from that default and retargets ignores and `state_dir`. Do not use `--force` to overwrite an existing config without reviewing and preserving it.

The project root must be an existing directory; a missing path or a file exits `4` and creates nothing. `history` on a never-scanned root prints `No recorded runs found.` and creates nothing.

Output locations: both reports are always written. Without `-o`, they go to `<project_root>/production_doctor_report.md` and `.json`. With `-o` alone, JSON goes to the same stem with `.json`; an `-o` ending in `.json` receives the JSON and the markdown goes to the same stem with `.md`. The same path for `-o` and `--json-output` exits `4`. Stateful runs also write `<state_dir>/reports/<run_id>/` and `<state_dir>/reports/latest.md`. Every doctor invocation, including `--help`, writes `production_doctor.log` to the current working directory. Without `-c`, built-in defaults apply; there is no config auto-discovery.

The scan's exit status is gated by `severity_exit_level` (default `serious`; also `critical`, `minor`, `info`, and `none`, which works quoted or unquoted):

| Code | Meaning |
|---|---|
| `0` | No finding at or above the gate; always `0` under `none` |
| `1` | A non-critical finding at or above the gate |
| `2` | A critical finding, under every gate except `none`; also an argparse usage error |
| `4` | Configuration or doctor error: invalid config, empty `include_patterns`, missing root, unknown run ID, unusable state |
| `5` | Any other runtime failure; traceback in `production_doctor.log` |

A file the analyzer fails on becomes a critical `analysis_read_errors` finding, not a crash. A zero-file scan exits `0`, so always check `files=` in the summary line. Setting the threshold lower or excluding files to make a command green is not a fix.

Stateful runs are stored in `state_dir` under the scanned project root (`.python_doctor/` by default, `.somnus-debug/state/` in an onboarded profile). `history` depends on that state. Run IDs are UTC timestamps; a same-second rescan gets a `-1` suffix (then `-2`, and so on). `rollback` repoints the `latest` alias and rewrites `<state_dir>/reports/latest.{md,json}`; it does not touch `-o` reports or source files, and the next scan's state delta is computed against the rolled-back run.

## `structure`

`structure` indexes one Python file without importing it.

```console
somnus-debug structure path/to/file.py
somnus-debug structure path/to/file.py -o .somnus-debug/indexes/file-index.md
somnus-debug structure path/to/file.py --update-doc path/to/existing-index.md
```

The index covers one Python file. By default it includes classes, nested classes, module-level functions, methods, signatures, decorators, doc summaries, and line spans. Use flags from `somnus-debug structure --help` for a narrower view. `--update-doc` writes an existing doc in place; check the target first. `-o` and `--update-doc` print nothing. A file that is not valid UTF-8 or does not parse exits `2` with a one-line `error:` message.

Use it before editing dense or unfamiliar Python files and after editing when the definition layout changed. Store generated indexes locally only when they will help the ongoing work; don't generate repository-wide index debris.

## `pycache-clean`

There is no bare-root CLI mode. The YAML config must contain `roots:`. A typical config is:

```yaml
roots:
  - /absolute/path/to/project
exclude:            # matched (fnmatchcase) against the directory name and its root-relative path
  - "node_modules"  # a bare name skips it at any depth; "node_modules/*" skips only <root>/node_modules
  - ".git"
  - ".venv"
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

Relative `roots` resolve against the caller's working directory, not the config file, so keep them absolute. `roots` and `log_file` expand `~` and `$VAR`. Types are checked before anything runs (lists of strings, real booleans, `max_depth` a non-negative integer or `null`); a rejected config exits `1`. A dry run ends with `Summary: would delete ...; would free ...`. A root that does not exist is logged, the other roots are still processed, and the run exits `1`. Without PyYAML, `somnus-debug pycache-clean` prints one line naming it and exits `1`; the other commands do not need it. Without `--config`, the CLI looks for `./config.yaml`. The onboarded `pycache.yaml` sets `dry_run: true`; the CLI has no flag to force a live pass, so a live run requires a deliberate, authorized edit of that value.

Review the listed roots and targets. A live pass deletes matched caches. Only run it when cleanup is in scope and the operator's authorization boundary permits it. Keep a reviewed config with the intended roots; do not widen it casually.

## `init-test-harness`

`init-test-harness` copies the single-test harness into a project that wants it.

```console
somnus-debug init-test-harness path/to/repo
somnus-debug init-test-harness . --no-contract
```

The scaffold creates a portable `run_test.py` and, by default, `CONTRACT.md`; `somnus-init-test-harness` is the same command. It refuses to overwrite existing files. The repo root or any subdirectory works: `run_test.py` finds its project root at run time (`$PROJECT_ROOT`, else the nearest directory upward with `.git`, `pyproject.toml`, or `setup.cfg`) and writes artifacts to `<project root>/test-runs/<run id>/`. The shipped test is a generic placeholder (`pytest -q` when a pytest suite exists, else `compileall`); `python run_test.py --help` prints the settings without running it. Use it only when the target project lacks an established harness and wants this single-test contract. Never add `--force` just to get past the refusal.

The contract says the project owns its test name, `execute_test()`, real boundary, acceptance checks, and PASS/FAIL decision. A run should produce `manifest.json`, `report.md`, and `test.log` with a unique run ID. Metrics only become gates when project acceptance explicitly makes them so. Exceptions remain failures. Accelerate, CI, a skill, or another orchestrator can invoke this surface without defining its meaning.

## Capability selection

Use `doctor` for repeated Python diagnostics; `structure` for targeted AST maps; `pycache-clean` only for an authorized cleanup; `init-test-harness` only for an accepted project-owned harness. “Use somnus-debug fully” means exercise the tools that fit the work, not run mutation-oriented commands on every session.
