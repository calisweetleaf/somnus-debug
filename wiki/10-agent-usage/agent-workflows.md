# Agent workflows

This page gives end-to-end sequences an agent can follow for the common jobs, each assembled from steps that were executed in this wave. They follow the fieldkit's loop (`skills/somnus-debug-fieldkit/references/doctor-loop.md`) and add the checks the code showed are necessary.

## W1: first contact with an unknown repo

This section is the sequence for a repo with no `.somnus-debug/`.

1. `<venv>/bin/python -m somnus_debug.cli --version` → `0.1.0`. If no venv has it, ask before installing.
2. `python3 <fieldkit>/scripts/selftest.py --python <venv>/bin/python` → `29/29 passed.` [VERIFIED].
3. `python3 <fieldkit>/scripts/onboard.py <repo>` (plan). Read `runner:` and `Python files in scope`. If a root `python_doctor.yaml` exists, expect it to be adopted; if its verify scan shows `files=0`, rerun with `--new-config`.
4. `onboard.py <repo> --apply --baseline`. Require `Verify scan: files=N` with N > 0 and a `Baseline:` line [VERIFIED, [onboard-a-repo](../09-recipes/intermediate/onboard-a-repo.md)].
5. Read `.somnus-debug/runs/baseline.md` (or `.json`). Pre-disposition only known false positives, each narrowly, with a reason: the ones `skills/somnus-debug-fieldkit/references/findings.md` lists (abstract-method, `Protocol` and `@overload` stubs, property-setter duplicates), plus `@dataclass(frozen=True)` short classes, which that reference wrongly says are exempt ([D-07](../DISCOVERY-LEDGER.md#d-07); [lane-f fieldkit §5](../_evidence/agent-findings/lane-f-ext/fieldkit.md)).
6. Propose appending `templates/AGENTS_APPENDIX.md` to the repo's agent instructions; edit only with the owner's agreement.
7. Do not add CI, hooks, watchers or the harness during onboarding (`references/onboarding.md`, step 6).

## W2: a Python change with a gate

This section is the everyday loop, as one sequence.

1. Read `PROFILE.md`; use its runner (`pr`) and paths.
2. If this is a new work slice, take a fresh baseline: `pr doctor scan .. -c python_doctor.yaml -o runs/baseline.md --json-output runs/baseline.json`. Note `files=`.
3. Orient: for each file you will touch, read its definitions from `runs/baseline.json` `files[].functions[]`, or run `pr structure ../path.py` on unstamped files.
4. Make the change. Run the project's own tests.
5. Rescan to `runs/latest.*`. Wait at least one second after the previous stateful scan ([D-08](../DISCOVERY-LEDGER.md#d-08)).
6. `delta.py runs/baseline.json runs/latest.json --dispositions dispositions.json --json > runs/delta.json`.
7. Branch on the exit code: 0 → step 9; 1 → step 8; 2 → fix coverage or the command line; 3 → rescan or fix inputs.
8. For each entry in `regressions`, print its slice (`findings_to_slices.py runs/latest.json runs/delta.json`), then fix, disposition with a reason, or record as out of scope or unverified. Go to step 4.
9. Check `stale_dispositions` is empty; remove any stale entries.
10. Hand off: CLI version, runner, baseline and latest `files_scanned` and counts, delta verdict, dispositions added with reasons, native test result, anything unverified.

Executed: yes, steps 2-9 on the fixture ([baseline-delta-loop](../09-recipes/intermediate/baseline-delta-loop.md), [findings-to-source-slices](../09-recipes/advanced/findings-to-source-slices.md)).

## W3: close a slice and move the baseline

This section promotes the baseline safely.

1. Rescan immediately before closing.
2. `ratchet_promote.sh <repo> <fieldkit>`: it promotes only when delta exits 0 and `stale_dispositions` is empty, archiving the old baseline under `runs/archive/` [VERIFIED, [quality-ratchet](../09-recipes/advanced/quality-ratchet.md)].
3. Optionally record `pr doctor history .. -c python_doctor.yaml --limit 5` in the handoff as the run trend.

## W4: review someone else's change

This section uses the same tools read-only.

1. Check out the base commit; scan to `runs/base-review.json` with the profile config and `--no-state`.
2. Check out the change; scan to `runs/head-review.json` with the **same** config.
3. Compare `config_hash` in both reports; if they differ, the config changed in the diff, and severities may have moved ([D-21](../DISCOVERY-LEDGER.md#d-21)).
4. `delta.py runs/base-review.json runs/head-review.json --dispositions dispositions.json --json`; report `regressions` with slices, and any dispositions the change added.

Executed: no as a sequence. Each command was run in this wave in other recipes; the two-checkout flow itself was not exercised [UNVERIFIED as a whole].

## W5: tests and static gate as one verdict for an orchestrator

This section is for a host that wants one PASS/FAIL.

1. With authorization, `init-test-harness <repo>/single_test --no-contract`.
2. Splice the three-check surface (project tests, doctor ran with files > 0, delta clean).
3. Disposition the harness file's template findings narrowly.
4. Run `python3 single_test/run_test.py` with `SD_PYTHON`, `FIELDKIT`, `TEST_PYTHON` set; read the stdout JSON for the manifest path and `manifest.json` for the verdict and checks.

Executed: yes ([harness-doctor-delta](../09-recipes/integrations/harness-doctor-delta.md)): FAIL on template findings, PASS after dispositions, FAIL on an `os.system` regression.

## What not to automate

This section lists actions an agent should leave to a person.

- Live `pycache-clean`, `init-test-harness --force`, installing packages into the project's environment, and adding hooks, CI jobs or watchers (`skills/somnus-debug-fieldkit/SKILL.md:110`, `templates/AGENTS_APPENDIX.md:52-53`).
- Editing `python_doctor.yaml` severities or gates to get a green result (`SKILL.md:109`).
- Running `doctor self-check` inside an installed environment: it writes into the package directory ([D-10](../DISCOVERY-LEDGER.md#d-10)).

## Sources

This section lists the files, logs and evidence this page rests on.

- `skills/somnus-debug-fieldkit/SKILL.md:50-129`, `references/doctor-loop.md`, `references/onboarding.md`, `references/findings.md`, `templates/AGENTS_APPENDIX.md`
- [lane-f fieldkit](../_evidence/agent-findings/lane-f-ext/fieldkit.md), [lane-f compositions](../_evidence/agent-findings/lane-f-ext/compositions.md)
- [recipes execution log](../09-recipes/execution-log.md)
