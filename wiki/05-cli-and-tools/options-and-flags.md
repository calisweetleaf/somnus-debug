# Options and flags

This page indexes every command-line flag and positional argument by tool, with its default, its real effect, and any gap between the help text and the behavior. The verbatim help is in [command-reference](command-reference.md). Configuration-file keys are covered in [06-configuration/complete-option-reference](../06-configuration/complete-option-reference.md).

## Dispatcher flags

This section lists the flags `somnus-debug` handles before routing.

| Flag | Position | Effect | Evidence |
|---|---|---|---|
| `-h`, `--help` | first token only | prints the top-level help, exit 0; anything after it is ignored | [VERIFIED] W2-01; lane D C07 |
| `-V`, `--version` | first token only | prints `0.1.0`, exit 0 | [VERIFIED] W2-01 |

Any other first token must be a subcommand name. Flags after the subcommand belong to that tool. [SOURCE-CONFIRMED] `src/somnus_debug/cli.py:107-125`.

## doctor scan

This section lists the scan flags.

| Flag | Default | Effect | Notes and evidence |
|---|---|---|---|
| `project_root` (positional) | `.` | directory to scan, resolved against cwd | must exist when `--no-state` is used (else exit 4); with state on, a missing writable path is created and scanned empty, exit 0 ([D-29](../DISCOVERY-LEDGER.md#d-29)). [VERIFIED] W2-08; lane D D18 |
| `-c`, `--config` | none: built-in defaults | YAML (`.yaml`/`.yml`, doctor's own minimal parser) or JSON (`.json`) config, deep-merged over defaults | the **only** way to apply a config, since there is no auto-discovery. [VERIFIED] lane D D27. Lists replace defaults wholesale; only `severity_levels` merges key by key. [SOURCE-CONFIRMED] `src/somnus_debug/doctor/core.py:726-734` |
| `-o`, `--output` | `<project_root>/<report_basename>.md` | Markdown report path; parents created | also sets the default JSON path (suffix swapped). `-o x.json` alone makes the JSON overwrite the Markdown. [VERIFIED] W2-23 |
| `--json-output` | `<md path with .json suffix>` | JSON report path | [SOURCE-CONFIRMED] `:1953-1960` |
| `--no-state` | off | skip SQLite state; write only the two report files | [VERIFIED] W2-10 |
| `-v`, `--verbose` | off | help says "enable debug logging" | `-v` does nothing (only the literal `--verbose` is checked, `:2186`). `--verbose` sets DEBUG, but doctor emits no debug records. [VERIFIED] W2-07: the log was 0 bytes in all three cases. [DISCREPANCY] help vs behavior |

There are no flags for include/ignore patterns, gate, workers, or any other config key. Those live only in the config file. [SOURCE-CONFIRMED] `build_parser`, `:2130-2162`.

## doctor init-config

This section lists the init-config flags.

| Flag | Default | Effect | Evidence |
|---|---|---|---|
| `-o`, `--output` | `python_doctor.yaml` (relative to **cwd**) | where to write the default YAML | [VERIFIED] W2-13; lane D D25 |
| `--force` | off | overwrite an existing file; without it, an existing target exits 4 | [VERIFIED] lane D D23, D24 |

## doctor history

This section lists the history flags.

| Flag | Default | Effect | Evidence |
|---|---|---|---|
| `project_root` | `.` | project whose state to read | [VERIFIED] W2-14 |
| `-c`, `--config` | defaults | only `state_dir`/`reports_dir` matter here; pass the same config you scanned with | [SOURCE-CONFIRMED] `:2106-2110`, `:1919-1925` |
| `--limit` | 10 | number of runs shown, newest first; non-int is an argparse exit 2 | [VERIFIED] lane D D08, D42 |

## doctor rollback

This section lists the rollback flags.

| Flag | Default | Effect | Evidence |
|---|---|---|---|
| `project_root` | `.` | project whose state to change | [VERIFIED] W2-16 |
| `--run-id` | **required** | run to make `latest` again; unknown ID exits 4, missing flag exits 2 | [VERIFIED] W2-16; lane D D11 |
| `-c`, `--config` | defaults | locates state (`state_dir`) | [SOURCE-CONFIRMED] `:2113-2120` |

## doctor self-check

This section lists the self-check flags.

| Flag | Default | Effect | Evidence |
|---|---|---|---|
| `-c`, `--config` | defaults | config for the self-scan | [SOURCE-CONFIRMED] `:2123-2127` |
| `-o`, `--output` | `<doctor package dir>/self_check_report.md` | redirect the Markdown report | [VERIFIED] lane D D15 |
| `--json-output` | derived from `-o` | redirect the JSON report | [VERIFIED] lane D D15 |
| `--no-state` | off | without it, `.python_doctor/` is created **inside the package directory** | [VERIFIED] lane D D14 |

## structure

This section lists the indexer flags.

| Flag | Default | Effect | Evidence |
|---|---|---|---|
| `source` (positional) | required | one Python file, read as UTF-8 | [VERIFIED] W2-15; a non-UTF-8 file gives a traceback, exit 1 (W2-09) |
| `-o`, `--output` | stdout | write the index to a file (parents created); prints nothing | [VERIFIED] W2-22 |
| `--update-doc PATH` | none | same as `-o`. Despite "Regenerate an existing", it creates a missing file. Mutually exclusive with `-o` | [VERIFIED] lane D S12, S13 |
| `--no-line-numbers` | off | drop `(lines a-b)` spans | [VERIFIED] lane D S10 |
| `--source-label` | input path | name used in the `# Class Index for` heading | [VERIFIED] lane D S10 |
| `--no-module-functions` | off | omit module-level functions from the body; the header count still includes them | [VERIFIED] lane D S10 |

## pycache-clean

This section lists the cleaner flags. Every flag can only make a setting stricter or more verbose relative to the config, apart from `--max-depth`, which replaces the configured value.

| Flag | Default | Effect | Evidence |
|---|---|---|---|
| `--config` | `config.yaml` (relative to **cwd**) | YAML config, the only source of `roots` | [VERIFIED] W2-18; lane D P04 |
| `--dry-run` | from config | forces `dry_run = True`. There is no flag that forces a live run | [SOURCE-CONFIRMED] `src/somnus_debug/pycache_cleaner/core.py:356-358` |
| `--verbose` | from config | forces `verbose = True`. It is lost entirely if the config has an unknown key | [VERIFIED] W2-18; lane D P09 |
| `--max-depth N` | from config | overrides recursion depth; `0` cleans only targets directly under each root | [VERIFIED] lane D P09 |
| `--follow-symlinks` | from config | forces symlink following | [UNVERIFIED] behavior not exercised |

There is no positional root or `--root` flag.

## init-test-harness

This section lists the scaffolder flags.

| Flag | Default | Effect | Evidence |
|---|---|---|---|
| `target` (positional) | `.` | directory to write into; created if missing | [VERIFIED] W2-19; lane D H04 |
| `--force` | off | overwrite existing `run_test.py`/`CONTRACT.md` | [VERIFIED] lane D H03 |
| `--no-contract` | off | write only `run_test.py` | [VERIFIED] W2-19 |

The default target `.` combined with the template's `PROJECT_ROOT` default puts test artifacts outside the repo. Pass a subdirectory instead. See [command-reference](command-reference.md#init-test-harness).

## Scaffolded run_test.py

This section records that the harness has no flags.

`run_test.py` parses no argv. Its only knobs are the environment variables `PROJECT_ROOT` and `SINGLE_TEST_OUTPUT_DIR`. [SOURCE-CONFIRMED] `src/somnus_debug/test_harness/templates/run_test.py:186-193`, `:590`, `:749`. [VERIFIED] lane D H09.

## Flags that do not exist

This section lists flags that users commonly expect but that are absent, so nobody wastes a run looking for them.

| Expected flag | Status |
|---|---|
| `doctor scan --include/--exclude` | absent; use config keys |
| `doctor scan --gate`/`--fail-on` | absent; use `severity_exit_level` in config |
| `doctor scan -j/--workers` | absent; use `max_workers` in config |
| `doctor --version` | absent; normalized to `scan . --version`, argparse exit 2 |
| `structure --version`, `structure --both` | absent (exit 2); `--both` is planned only (MANUAL 4) |
| `pycache-clean <path>` / `--no-dry-run` | absent |
| `somnus-init-test-harness` script | absent |

[VERIFIED] lane D C02, C03; [SOURCE-CONFIRMED] the parsers cited above.

## Sources

This section lists the code and evidence this page draws on.

- `src/somnus_debug/cli.py:107-125`
- `src/somnus_debug/doctor/core.py:726-734`, `:1953-1960`, `:2096-2186`
- `src/somnus_debug/structure/core.py:280-347`
- `src/somnus_debug/pycache_cleaner/core.py:337-366`
- `src/somnus_debug/test_harness/scaffold.py:91-109`; `templates/run_test.py:186-193`, `:749`
- [lane D command-reference.md](../_evidence/agent-findings/lane-d-cli-tests/command-reference.md), [experiment-log.md](../_evidence/agent-findings/lane-d-cli-tests/experiment-log.md)
- [lane B configuration-findings.md](../_evidence/agent-findings/lane-b-config/configuration-findings.md)
- W2 runs: [verification-results](../11-verification/verification-results.md#w2-runs)
