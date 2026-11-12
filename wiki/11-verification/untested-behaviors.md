# Untested behaviors

This page lists behaviors that no automated check covers, in two tiers:

1. behaviors verified by hand in this wiki but with no pytest or selftest guarding them, so they can regress silently
2. behaviors nobody has executed at all

For each one it names the cheapest test that would close the gap.

## Tier 1: verified once, unguarded

This section lists the highest-value gaps, where a regression would go unnoticed.

| Behavior | Last verified | Suggested automated check |
|---|---|---|
| detector output for 12 categories with no check anywhere: `tokenization_errors`, `analysis_read_errors`, `unused_imports`, `dependency_cycles`, `placeholder_returns`, `incomplete_methods`, `suspicious_short_classes`, `broad_exceptions`, `security_risks`, `missing_docstrings`, `type_hint_gaps`, `complexity` | lane D fixtures proj, proj2, proj3 | one golden-fixture pytest per category asserting `(category, file, line, symbol)` |
| `minor`/`info` gates return 1 with critical findings | W2-08 | parametrized gate test over `exit_code_for_summary` |
| unquoted `none` gate -> exit 4 | W2-08 | config parse test |
| no config auto-discovery | lane D D27 | scan with a root `python_doctor.yaml` set to `"none"`, expect a non-zero exit |
| malformed YAML accepted silently | lane D D30 | parser test (currently would assert the defect) |
| `history`, `rollback`, unknown run ID -> 4 | W2-14, W2-16 | stateful pytest in `tmp_path` |
| same-second run-ID collision drops history | W2-17 | two scans with a frozen clock, expect 2 rows (fails today; [D-08](../DISCOVERY-LEDGER.md#d-08)) |
| rollback leaves root reports untouched | W2-16 | assert on both run IDs |
| `self-check` writes into the package directory | lane D D14 | run self-check from an installed wheel in a temp venv, assert nothing is written under site-packages (fails today) |
| `production_doctor.log` replaces host logging handlers | W2-20 | in-process test of `cli.main` |
| `-o x.json` collision | W2-23 | assert both files exist (fails today; [D-25](../DISCOVERY-LEDGER.md#d-25)) |
| exit 5 on the serial path vs per-file issue on the threaded path | lane D D44; [execution-model](../01-system/execution-model.md) | two fixtures, expected 5 and 2 |
| `structure` on non-UTF-8 input (traceback, exit 1) | W2-09 | expect exit 2 with `error:` (fails today) |
| `structure` flags `--no-line-numbers`, `--source-label`, `--no-module-functions`, `--update-doc` | lane D S10, S12 | golden-output tests |
| pycache-clean real deletion, excludes, `--max-depth` | W2-18; lane D P03, P09 | temp-tree test |
| pycache-clean missing root exits 0 | lane D P01 | assert the exit and the `[ERROR]` line |
| pycache-clean unknown key silences logging | lane D P09 | assert the Summary line is present (fails today) |
| pycache-clean type coercions (`dry_run: no`, scalar `roots`) | lane B | config validation test (fails today) |
| scaffolded `run_test.py` placement default | W2-19 | scaffold to `tmp/x`, run it, assert the artifacts are under `tmp/x` (fails today; [D-15](../DISCOVERY-LEDGER.md#d-15)) |
| dispatcher needs PyYAML for doctor | W2-05 | run under `sys.modules['yaml']=None`, expect doctor help rc 0 (fails today; [D-13](../DISCOVERY-LEDGER.md#d-13)) |
| import resolution depends on invocation form (cwd on `sys.path` under `-m`) | W2-25 | two invocations, same expected classification (fails today; [D-26](../DISCOVERY-LEDGER.md#d-26)) |
| `onboard.py` and `delta.py` edge cases | lane D O/T series; lane F | the fieldkit has no tests of its own beyond selftest |

## Tier 2: never executed

This section lists behaviors that no lane and no W2 run exercised. Claims about them in this wiki are SOURCE-CONFIRMED or HYPOTHESIS only.

| Behavior | Why not run | What is known |
|---|---|---|
| `pycache-clean --follow-symlinks`, including symlink loops | not prioritized | flag parsed (`src/somnus_debug/pycache_cleaner/core.py:345`); traversal behavior [UNVERIFIED] |
| Windows: paths, long paths, log handling | Linux-only sandbox | long-path support absent in code ([SOURCE-CONFIRMED] `:64`) |
| macOS, Linux x86_64 | sandbox is Linux aarch64 | no platform branches in code |
| Python < 3.10 | not available | declared unsupported |
| Python 3.13 **with** PyYAML through the dispatcher | only a PyYAML-less 3.13 was available | doctor and structure modules work on 3.13 (W2-05) |
| `pip install -e .` (editable) | would write into the repo | documented in README and MANUAL only |
| doctor exit 5 via `sqlite3.Error` during `persist` | not reproduced | `persist` errors are not caught by the scan fallback ([SOURCE-CONFIRMED] lane F doc-reconciliation, MANUAL section 3.5 row) |
| exception types outside doctor's two tiers (for example `KeyError`) reaching `main` | no trigger found | would produce a raw traceback, exit 1 ([SOURCE-CONFIRMED] `src/somnus_debug/doctor/core.py:2189-2201`) |
| `max_workers` values above the file count, performance on large trees | no large fixture | capped at file count (`:1720`); speed [HYPOTHESIS] |
| `run_test.py` interrupted by `KeyboardInterrupt` | interactive | not caught, so no manifest ([SOURCE-CONFIRMED] lane F H-5) |
| concurrent `cli.main` calls from threads | not attempted | `sys.argv` swap is process-global ([HYPOTHESIS]) |
| `history` ordering across days on a normal host | sandbox runs within one day | ordered by the `completed_at` TEXT column, which is ISO-8601 and therefore lexically sortable ([SOURCE-CONFIRMED]) |
| uninstall leaving self-check artifacts in site-packages | not attempted | [HYPOTHESIS] from pip's RECORD-based uninstall |

## Sources

This section lists the code and evidence this page draws on.

- [lane D test-coverage.md](../_evidence/agent-findings/lane-d-cli-tests/test-coverage.md) sections 4-5; [experiment-log.md](../_evidence/agent-findings/lane-d-cli-tests/experiment-log.md) "Not run / blocked"
- [lane F fieldkit.md](../_evidence/agent-findings/lane-f-ext/fieldkit.md), [harness.md](../_evidence/agent-findings/lane-f-ext/harness.md), [doc-reconciliation.md](../_evidence/agent-findings/lane-f-ext/doc-reconciliation.md)
- [lane B configuration-findings.md](../_evidence/agent-findings/lane-b-config/configuration-findings.md)
- `src/somnus_debug/doctor/core.py:1720`, `:2189-2201`; `src/somnus_debug/pycache_cleaner/core.py:64`, `:345`
- W2 runs: [verification-results](verification-results.md#w2-runs)
