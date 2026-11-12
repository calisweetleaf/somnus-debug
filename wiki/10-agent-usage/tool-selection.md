# Tool selection

This page maps the questions an agent actually has to the somnus-debug tool or fieldkit script that answers them, and names the question each tool cannot answer. Use it before reaching for a command.

## Question → tool

This section is the routing table.

| The agent needs to know… | Use | Not | Evidence |
|---|---|---|---|
| Is this repo set up for somnus-debug, and how do I run it here? | Read `.somnus-debug/PROFILE.md`; if absent, `onboard.py <repo>` (plan mode) | Guessing the interpreter; `somnus-debug` on PATH when a project venv exists | [onboard-a-repo](../09-recipes/intermediate/onboard-a-repo.md) [VERIFIED] |
| Did my change introduce new problems? | Rescan + `delta.py baseline latest --dispositions …` | Doctor's own exit code (it is 1 for any old serious finding) | [baseline-delta-loop](../09-recipes/intermediate/baseline-delta-loop.md) [VERIFIED] |
| What production-readiness problems exist in this tree? | `doctor scan … --json-output`, then read `issues[]` | The Markdown report for parsing; the score as a quality measure | [first-scan](../09-recipes/beginner/first-scan.md) [VERIFIED] |
| Where is function X and how long is it? | Doctor JSON `files[].functions[]` (whole project), or `structure <file>` (one file) | `structure` on a metadata-stamped file (crashes, [D-01](../DISCOVERY-LEDGER.md#d-01)) | [findings-to-source-slices](../09-recipes/advanced/findings-to-source-slices.md) [VERIFIED] |
| Which lines should I read for this finding? | `findings_to_slices.py latest.json delta.json` | Opening whole files | same |
| Do the project's tests pass? | The project's own test command, or a harness that runs it | Doctor (never emits `test_gaps`, [D-05](../DISCOVERY-LEDGER.md#d-05)) | [harness-pytest](../09-recipes/integrations/harness-pytest.md) [VERIFIED] |
| Tests and static gate as one verdict? | Scaffolded harness with the 3-check surface | Two separate exit codes glued in prose | [harness-doctor-delta](../09-recipes/integrations/harness-doctor-delta.md) [VERIFIED] |
| Are there import cycles? | `dependency_graph.cycles`; in a src layout, a second scan rooted at `src/` | The profile scan in a src layout (reports 0, [D-22](../DISCOVERY-LEDGER.md#d-22)); any claim about `from pkg import mod` cycles ([D-06](../DISCOVERY-LEDGER.md#d-06)) | [src-layout-cycle-check](../09-recipes/advanced/src-layout-cycle-check.md) [VERIFIED] |
| Is this finding a false positive? | `skills/somnus-debug-fieldkit/references/findings.md`, then a narrow disposition | Lowering the category's severity | [D-07](../DISCOVERY-LEDGER.md#d-07) |
| Does the installed CLI still behave as documented? | `selftest.py --python <interp>` | Trusting the references after an upgrade | [fieldkit-selftest](../09-recipes/integrations/fieldkit-selftest.md) [VERIFIED] |
| What happened in earlier scans? | `doctor history .. -c python_doctor.yaml` | Assuming every scan is listed (same-second collisions, [D-08](../DISCOVERY-LEDGER.md#d-08)) | [history-and-rollback](../09-recipes/automation/history-and-rollback.md) [VERIFIED] |
| Can stale bytecode be hiding an import error? | `pycache-clean --dry-run` with the profile's `pycache.yaml`, then an authorized live run | Running it to change doctor results (it does not) | [pycache-dry-run](../09-recipes/beginner/pycache-dry-run.md) [VERIFIED] |

## What each tool costs

This section lists side effects, so an agent can pick the cheapest tool that answers.

| Tool | Writes | Reads | Typical use frequency |
|---|---|---|---|
| `doctor scan` | `production_doctor.log` in cwd (always); reports at `-o`/`--json-output` (else project root); `state_dir` unless `--no-state` | all included `*.py` under the root | once per repair batch |
| `doctor history` / `rollback` | `state_dir` (rollback moves the `latest` alias) | `state_dir` | at handoff, for audit |
| `doctor self-check` | reports and state **inside the installed package directory** ([D-10](../DISCOVERY-LEDGER.md#d-10)) | the package's own `doctor/` | avoid in agent loops |
| `structure` | nothing unless `-o` / `--update-doc` | one file | as needed |
| `pycache-clean` | deletes matching files on a live run | configured roots | rarely, with authorization |
| `init-test-harness` | `run_test.py`, `CONTRACT.md` | package templates | once per repo, with authorization |
| `onboard.py` | `.somnus-debug/` on `--apply`; nothing in plan mode | the tree, git status | once, plus plan mode when the tree changes shape |
| `delta.py` | nothing | two reports, dispositions | after every rescan |
| `selftest.py` | its own temp dir only | — | after install or upgrade |

Sources: [lane-d command reference](../_evidence/agent-findings/lane-d-cli-tests/command-reference.md), [lane-f fieldkit](../_evidence/agent-findings/lane-f-ext/fieldkit.md) [VERIFIED]; `structure` and `pycache` dry-run write behaviour re-proven by `selftest.py` in this wave.

## Which entry point to call

This section chooses between the dispatcher, per-tool scripts, and `python -m`.

- **Prefer `<project-venv>/bin/python -m somnus_debug.cli …`.** It pins the interpreter that resolves imports, which is what onboard writes into the profile.
- **`somnus-debug` (dispatcher)** imports every tool, so it needs PyYAML even for `doctor` ([D-13](../DISCOVERY-LEDGER.md#d-13)). `somnus-doctor` alone is stdlib-only [VERIFIED by lane B].
- **There is no `somnus-init-test-harness` script;** use `somnus-debug init-test-harness` [VERIFIED by lane D].
- **Library imports** are for hosts that need objects: [programmatic-invocation](programmatic-invocation.md).

## Sources

This section lists the files, logs and evidence this page rests on.

- [lane-d command reference](../_evidence/agent-findings/lane-d-cli-tests/command-reference.md), [lane-d README](../_evidence/agent-findings/lane-d-cli-tests/README.md), [lane-b configuration findings](../_evidence/agent-findings/lane-b-config/configuration-findings.md), [lane-f fieldkit](../_evidence/agent-findings/lane-f-ext/fieldkit.md)
- `skills/somnus-debug-fieldkit/SKILL.md:79-91` (the fieldkit's own router)
- [recipes execution log](../09-recipes/execution-log.md)
