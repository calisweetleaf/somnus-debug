# Doctor loop: baseline, repair, rescan, repeat

This is the core operating protocol. A Python change is not complete merely because an initial `doctor` command ran.

## 0. Establish authority and coverage

- Identify the active project root.
- Read root `AGENTS.md`, relevant directory instructions, existing tests, CI, and any task packet.
- Check `somnus-debug --version` and `somnus-debug doctor --help`.
- Inspect existing `python_doctor.yaml`, `.somnus-debug/` data, and `.python_doctor/` state before generating or replacing anything.
- If doctor config is absent, initialize a project-local config in a local directory; preserve any config already present. Review and adapt `include_patterns` to actual Python source and tests. Include all in-scope directories and retain ignore rules appropriate to the project.
- Confirm that the configured scan includes at least one real in-scope Python file. A zero-file run is a setup failure.

## 1. Baseline before changes

Run a stateful scan when local SQLite works and the project can retain `.python_doctor/` state. Use report output under a project-local run folder if the reports will be useful to the task. Use `--no-state` and explicit temporary output paths for a disposable one-off; that run cannot participate in history/rollback.

Record:

- version of CLI and config path;
- files scanned and findings by severity;
- report paths and whether SQLite state succeeded;
- existing project gate status, if the task has a relevant baseline.

The baseline separates pre-existing findings from regressions introduced by this work.

## 2. Orient at the relevant code surface

For each task-relevant Python file that is unfamiliar, large, or structurally central, run `somnus-debug structure <file.py>`. Read the actual source and tests around the indexed definitions. The index gives line and definition orientation; it does not establish behavior or data flow by itself.

Do not index every Python file by default. Select files from the task boundary and doctor findings.

## 3. Triage findings before editing

For each relevant finding, verify it against source and target-project contracts. Classify it as:

- actionable and in scope;
- real but outside this task;
- false positive or misconfigured check;
- unverified because required inputs or runtime evidence are absent.

Preserve evidence and reasoning for any disposition. Do not silence a finding by weakening thresholds, excluding the containing tree, or rewriting docs without fixing the underlying issue. If the checker is wrong, document why and keep the project policy intact.

## 4. Make the real change and run the real gate

Implement the requested code change. Run the target repository's own tests, build, or acceptance commands as defined by its instructions. Doctor supplements them; it does not substitute for them. If a test harness is absent, do not add one automatically. Use `init-test-harness` only when the project wants the contract and the user-authorized task includes that setup.

After meaningful Python edits, re-index the modified or newly coupled files with `structure` when structure review helps verify the change.

## 5. Rescan and compare

Run the same doctor config and scan scope after changes. Preserve a final report when useful. Compare against the baseline and, when SQLite state exists, inspect `somnus-debug doctor history <root> --limit N`.

Check:

- all in-scope actionable baseline findings are addressed or explicitly dispositioned;
- no new actionable serious/critical finding was introduced;
- changed file coverage is present in the scan;
- tool exit status matches the report and configured severity gate;
- project-native validation passes.

If SQLite failed but reports were written, note that the scan completed statelessly; do not imply history exists. `rollback` is only for report history and should not be used to hide a worse source state.

## 6. Loop condition

Return to triage and repair if an in-scope finding remains actionable, an iteration adds a new actionable finding, the scan did not cover the edited files, or project validation fails. Repeat the rescan after every meaningful repair batch until the result is stable.

Close when the requested implementation is complete, native gates pass, the final scan is comparable and reviewed, and every in-scope finding is fixed or has a clear evidence-based disposition. Keep unrelated backlog visible without expanding scope indefinitely.

## Long-running work

For a multi-hour session, treat each work slice as another loop iteration: update the baseline/final reports as the actual work changes, keep the same scope/config unless a justified coverage change is recorded, and use doctor history to recover trend. Do not rely on memory of an earlier scan; reopen the report tied to the active slice.
