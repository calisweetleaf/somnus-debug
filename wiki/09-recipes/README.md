# Recipes

Nineteen task-shaped recipes for somnus-debug 0.1.0 and its fieldkit, each executed in `/tmp` against a fixture with the real command, an output excerpt and the exit code. Every recipe says its tier: **supported now** (shipped tools plus shell or stdlib glue), **small integration step** (user code, a defect workaround, or a non-exported import), or a private-API **probe**. Research ideas are not recipes; they live in [experimental-extensions](../08-extensions/experimental-extensions.md).

## How to read a recipe

This section explains the shared layout and conventions.

Each recipe has: tier, goal, when to use, steps, an "Executed result" block marked `Executed: yes (where, which log)`, pitfalls, and sources. Exit codes appear as `[exit=N]` at the end of an output line, copied from the run log. `sd` means `/tmp/w4/venv/bin/python -m somnus_debug.cli` (equivalent to the `somnus-debug` script); `pr` means the profile runner `onboard.py` printed, `env PYTHONPATH=../src <repo>/.venv/bin/python -m somnus_debug.cli`; `<fieldkit>` is `skills/somnus-debug-fieldkit`.

All runs, with exit codes per command: [execution-log](execution-log.md). How to rerun them: [_repro](_repro/README.md).

## Beginner

This section is for a first contact with each tool.

| Recipe | Tier | What you get |
|---|---|---|
| [first-scan](beginner/first-scan.md) | supported now | A doctor scan with a config, reports outside the project, findings read from JSON |
| [index-one-file](beginner/index-one-file.md) | supported now | A `structure` index of one file, and the stamped-file crash |
| [pycache-dry-run](beginner/pycache-dry-run.md) | supported now | A dry-run-locked bytecode cleanup preview that provably deletes nothing |

## Intermediate

This section covers the fieldkit's everyday loop.

| Recipe | Tier | What you get |
|---|---|---|
| [onboard-a-repo](intermediate/onboard-a-repo.md) | supported now | `.somnus-debug/` profile, proven coverage, baseline, PROFILE card |
| [baseline-delta-loop](intermediate/baseline-delta-loop.md) | supported now | Change → rescan → `delta.py` → fix or disposition, until delta exits 0 |
| [severity-and-gate-tuning](intermediate/severity-and-gate-tuning.md) | supported now | Severity remap and exit gate, with the three silent config traps |

## Advanced

This section composes the tools into stronger gates and sharper reading.

| Recipe | Tier | What you get |
|---|---|---|
| [quality-ratchet](advanced/quality-ratchet.md) | supported now | Baseline promoted only on a clean delta with no stale dispositions |
| [findings-to-source-slices](advanced/findings-to-source-slices.md) | supported now | Only the definitions that regressed, with a stale-report guard |
| [src-layout-cycle-check](advanced/src-layout-cycle-check.md) | supported now | Real `dependency_cycles` in a src layout, where the profile runner reports 0 |
| [custom-detector-probe](advanced/custom-detector-probe.md) | **probe, private API** | A prototype finding category; not an extension API ([D-19](../DISCOVERY-LEDGER.md#d-19)) |

## Programmatic

This section uses the package from Python.

| Recipe | Tier | What you get |
|---|---|---|
| [embedded-scan](programmatic/embedded-scan.md) | small integration step | `ProjectScanner` results as objects, no disk or logging side effects; JSON identical to the CLI's |
| [index-stamped-file](programmatic/index-stamped-file.md) | small integration step | `build_index` on metadata-stamped files, line numbers preserved |
| [inprocess-main-isolated](programmatic/inprocess-main-isolated.md) | small integration step | Doctor's `main()` in-process, host logging and cwd restored |

## Automation

This section turns the loop into unattended gates.

| Recipe | Tier | What you get |
|---|---|---|
| [ci-delta-gate](automation/ci-delta-gate.md) | supported now | A CI step: 0 clean, 1 regression, 2 coverage, 3 doctor did not run |
| [pre-commit-gate](automation/pre-commit-gate.md) | supported now, opt-in | A hand-installed git hook that blocks commits adding serious findings |
| [history-and-rollback](automation/history-and-rollback.md) | supported now | Run history as an audit trail; state reports as delta baselines; what rollback does not do |

## Integrations

This section connects somnus-debug to test runs and to its own contract test.

| Recipe | Tier | What you get |
|---|---|---|
| [harness-pytest](integrations/harness-pytest.md) | small integration step | The single-test harness running a project's pytest suite with a fixed artifact contract |
| [harness-doctor-delta](integrations/harness-doctor-delta.md) | small integration step | One verdict over tests, doctor coverage and the delta gate |
| [fieldkit-selftest](integrations/fieldkit-selftest.md) | supported now | 29 checks that the installed CLI matches the fieldkit's claims |

There is no MCP, editor or hosted-CI integration in 0.1.0 ([plugin-integration](../08-extensions/plugin-integration.md)).

## Fixtures

This section names the fixtures so results can be compared across recipes.

| Fixture | Built by | Contents |
|---|---|---|
| `/tmp/w4/b1/proj` | stage 0, from [lane-a fixture](../_evidence/agent-findings/lane-a-arch-api/fixture/proj/pkg/b.py.txt) | 6 files: deliberate stubs, abstract/Protocol/overload bodies, property setter, syntax error, todos, imports of missing modules |
| `/tmp/w4/b1/proj_nobroken` | stage 0 | the same minus `broken.py` and `todo_mod.py` (4 files) |
| `/tmp/w4/proj` | stage 0 | src-layout `inventory` package, 1 pytest test, git repo, own `.venv` with this repo and pytest; onboarded in stage 2 |

## Sources

This section lists the files, logs and evidence this page rests on.

- [execution-log](execution-log.md), [_repro](_repro/README.md)
- [lane-f compositions](../_evidence/agent-findings/lane-f-ext/compositions.md), [lane-f recipes](../_evidence/agent-findings/lane-f-ext/recipes/)
