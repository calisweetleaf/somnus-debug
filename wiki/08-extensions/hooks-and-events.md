# Hooks and events

somnus-debug 0.1.0 has no hooks, callbacks, signals, or event stream. This page states that plainly, shows how the search was done, and lists the artifacts that can stand in for events when you need to react to a scan.

## Finding

This section gives the result and its evidence class.

No hook, callback, observer, signal, or event mechanism exists anywhere in the package or the fieldkit [VERIFIED]. Nothing in `src/somnus_debug/` accepts a callable from the caller, emits a structured event, or calls out to user code. The only thing the tools do while running is write log lines and print summary lines.

## Search scope

This section records what was searched so the negative result can be checked.

| Scope | Method | Result |
|---|---|---|
| `src/somnus_debug/**/*.py` (package source, 0.1.0) | `grep -rniE 'entry_points|pkg_resources|importlib\.metadata|plugin|hook|callback|register|__subclasses__|import_module\('` | No code matches. Run by lane F ([extensions](../_evidence/agent-findings/lane-f-ext/extensions.md), [log](../_evidence/agent-findings/lane-f-ext/logs/s5_library_and_links.log)) and repeated in this wave with the same empty result [VERIFIED] |
| `src/somnus_debug/**` including templates | `grep -rn hook -i` | Two prose mentions in `src/somnus_debug/test_harness/templates/CONTRACT.md:85` and `:145`, both saying hooks are out of the harness's scope [VERIFIED] |
| Installed distribution metadata | `importlib.metadata` entry-point scan | Only the 4 `console_scripts` reference `somnus_debug` [VERIFIED, lane F] |
| `pyproject.toml` | Read `[project.scripts]`, look for `entry-points` tables | 4 scripts, no other entry-point group [SOURCE-CONFIRMED] |
| `skills/somnus-debug-fieldkit/scripts/*.py` | Read in full | Stdlib CLIs; no callback parameters, no hook installation [SOURCE-CONFIRMED] |

The repo-root duplicates (`python_production_doctor.py`, `analyze_python_structure.py`, `pycache_cleaner.py`, `run_test.py`) were not searched separately for this page; they are older copies of the same tools ([D-01](../DISCOVERY-LEDGER.md#d-01), [D-28](../DISCOVERY-LEDGER.md#d-28)) and nothing imports them [UNVERIFIED for hooks specifically].

## Documented hook guidance that is not code

This section separates what the fieldkit references describe from what exists.

`skills/somnus-debug-fieldkit/references/automation.md:48-71` describes "optional hook layers" and a "hook contract for a future adapter": receive the repo root, changed paths, active config and permission boundary; run one scan per edit batch; gate on `delta.py`'s exit code; avoid concurrent scans against the same SQLite state. `references/accelerate-integration.md` describes the same seam for a Somnus Accelerate host. Both are guidance for an adapter someone would write [DOCUMENTED-ONLY]. No adapter ships. The reference also says not to install watchers or pre-commit frameworks by default, and the [AGENTS block](../_evidence/agent-findings/lane-f-ext/fieldkit.md) repeats it (`skills/somnus-debug-fieldkit/templates/AGENTS_APPENDIX.md:53`).

## What you can react to instead

This section lists the observable artifacts a wrapper can poll or read after a run. Each is real and verified; none is pushed to you.

| Artifact | When it appears | What it tells you | Evidence |
|---|---|---|---|
| Process exit code | Every run | Doctor gate verdict (0/1/2), config error (4), runtime failure (5); delta verdict (0/1/2/3) | [VERIFIED] [lane-d exit codes](../_evidence/agent-findings/lane-d-cli-tests/exit-codes.md) |
| stdout summary line `Scan complete: files=N, issues=N, critical=N, serious=N` | Every completed scan | Coverage and counts; `onboard.py` parses exactly this line (`skills/somnus-debug-fieldkit/scripts/onboard.py:88`) | [VERIFIED] [stage 1 log](../09-recipes/_repro/logs/stage1_beginner.log) |
| `Run ID: <id>` line | Stateful scans only | Key into history; not unique within one second ([D-08](../DISCOVERY-LEDGER.md#d-08)) | [VERIFIED] [stage 2 log](../09-recipes/_repro/logs/stage2_intermediate.log), where two scans in one second both printed `20261112T004522Z` |
| JSON report `state_delta` | Every scan | `new_files`, `modified_files`, `deleted_files`, `unchanged_files` against the previous stateful run, by file hash | [VERIFIED] [doctor JSON shape](../_evidence/agent-findings/lane-f-ext/logs/s1_doctor_json_shape.txt) |
| `<state_dir>/reports/latest.{md,json}` | After a stateful scan or a rollback | The current "latest" alias; rollback moves it without rescanning ([D-09](../DISCOVERY-LEDGER.md#d-09)) | [VERIFIED] [stage 5 log](../09-recipes/_repro/logs/stage5_automation.log) |
| `production_doctor.log` in the cwd | Every doctor call, even `--help` | Human log; no debug records, `-v` ignored | [VERIFIED] [D-10](../DISCOVERY-LEDGER.md#d-10) |
| Harness stdout JSON and `manifest.json` | Every `run_test.py` run | Verdict, checks, artifact paths | [VERIFIED] [stage 6 log](../09-recipes/_repro/logs/stage6_integrations.log) |

Logging is not a usable event channel for an embedding host: doctor's `main()` calls `logging.basicConfig(force=True)` and replaces the root handlers with a file handler in the cwd ([D-11](../DISCOVERY-LEDGER.md#d-11)). The [in-process recipe](../09-recipes/programmatic/inprocess-main-isolated.md) shows how to put the host's handlers back.

## Building your own trigger

This section points to the executed patterns that play the role of hooks.

- **Git pre-commit, opt-in, by hand:** [automation/pre-commit-gate](../09-recipes/automation/pre-commit-gate.md). Executed: the hook blocked a commit that added `subprocess.run(..., shell=True)` and allowed a clean one.
- **CI step:** [automation/ci-delta-gate](../09-recipes/automation/ci-delta-gate.md).
- **Agent edit batch:** [agent-workflows](../10-agent-usage/agent-workflows.md) and [automation-contracts](../10-agent-usage/automation-contracts.md).
- **A real callback seam** is a research idea: [experimental-extensions](experimental-extensions.md).

## Sources

This section lists the files, logs and evidence this page rests on.

- [lane-f extensions](../_evidence/agent-findings/lane-f-ext/extensions.md), [lane-f s5 log](../_evidence/agent-findings/lane-f-ext/logs/s5_library_and_links.log)
- `src/somnus_debug/test_harness/templates/CONTRACT.md:85`, `:145`; `pyproject.toml` `[project.scripts]`
- `skills/somnus-debug-fieldkit/references/automation.md:48-71`, `skills/somnus-debug-fieldkit/references/accelerate-integration.md`, `skills/somnus-debug-fieldkit/templates/AGENTS_APPENDIX.md:53`
- `skills/somnus-debug-fieldkit/scripts/onboard.py:88`
- Wave 5 runs: [stage logs](../09-recipes/_repro/README.md)
