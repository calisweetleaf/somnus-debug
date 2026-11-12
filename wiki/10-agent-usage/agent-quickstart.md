# Agent quickstart

This page is for an AI coding agent (or a person scripting one) that has to use somnus-debug on a Python repository. It gives the start-of-session procedure, the loop, and the rules that keep the results honest, all tied to runs in this wiki. The fieldkit skill at `skills/somnus-debug-fieldkit/` is the operating manual this page is based on; where its text and the code disagree, this page says so.

## What the toolchain is, for an agent

This section sets expectations before any command.

- **Four tools behind one CLI:** `doctor` (static production-readiness findings), `structure` (one-file AST index), `pycache-clean` (deletes bytecode), `init-test-harness` (writes a single-test scaffold). Two of them mutate files.
- **The fieldkit adds three stdlib scripts:** `onboard.py` (profile + baseline), `delta.py` (regression gate), `selftest.py` (29 behaviour checks).
- **Doctor is evidence, not a verdict.** It is static analysis only, never measures test coverage (`test_gaps` is never emitted), and the project's own tests and CI decide acceptance (`skills/somnus-debug-fieldkit/SKILL.md:106`) [SOURCE-CONFIRMED; [D-05](../DISCOVERY-LEDGER.md#d-05)].
- **No MCP server, no plugin API, no hooks.** Everything is a subprocess and files ([plugin-integration](../08-extensions/plugin-integration.md)).

## Start of every session

This section is the checklist, in order. It follows `SKILL.md:50-64`.

1. **Authority.** Read the repo's `AGENTS.md`, tests, CI and task. They own acceptance.
2. **CLI.** `somnus-debug --version`, or `<venv>/bin/python -m somnus_debug.cli --version`. Expect `0.1.0`. If missing, do not install silently; ask.
3. **Profile.** Look for `.somnus-debug/PROFILE.md`.
   - Present: read it. It holds the runner, config, coverage and exact commands. Go to the loop.
   - Absent: onboard (next section).
4. **After an install or upgrade,** run `python3 <fieldkit>/scripts/selftest.py --python <interpreter>`; expect `29/29 passed.`, exit 0 [VERIFIED, [fieldkit-selftest](../09-recipes/integrations/fieldkit-selftest.md)].

## Onboard (once per repo)

This section is the two-step onboarding.

```console
python3 <fieldkit>/scripts/onboard.py <repo>                      # plan: writes nothing; read runner and coverage
python3 <fieldkit>/scripts/onboard.py <repo> --apply --baseline   # writes .somnus-debug/, records runs/baseline.*
```

Check the output yourself, because onboard has known holes ([D-20](../DISCOVERY-LEDGER.md#d-20)):

- `runner:` should be the project environment. If it says PATH, `missing_imports` will be noise.
- `Verify scan: files=N` must be greater than 0 and close to the surveyed count. `--apply` writes `PROFILE.md` even when this fails.
- A `Baseline:` line must appear. If it does not, verification failed and no baseline exists.
- Do not pass `--python <venv>/bin/python` for a normal venv; onboard resolves the symlink and rejects it (exit 3) [VERIFIED in this wave].

Then append `skills/somnus-debug-fieldkit/templates/AGENTS_APPENDIX.md` to the repo's agent instructions, preserving what is there. onboard only prints a reminder; nothing appends it for you [SOURCE-CONFIRMED, `onboard.py:528-529`]. Executed walkthrough: [onboard-a-repo](../09-recipes/intermediate/onboard-a-repo.md).

## The loop, for any Python change

This section is the core procedure. Run from `.somnus-debug/`; `pr` is the profile runner.

```console
cd .somnus-debug
pr doctor scan .. -c python_doctor.yaml -o runs/baseline.md --json-output runs/baseline.json   # once per slice, before edits (onboard did the first)
# ...make the change, run the project's own tests...
pr doctor scan .. -c python_doctor.yaml -o runs/latest.md --json-output runs/latest.json
python3 <fieldkit>/scripts/delta.py runs/baseline.json runs/latest.json --dispositions dispositions.json
```

Branch on `delta.py`'s exit code, not doctor's: 0 clean, 1 new serious or critical, 2 coverage regression (or a usage error), 3 bad input. For each new finding and each persisting one in code you touched: fix it, mark it out of scope, disposition it in `dispositions.json` with a reason, or say it is unverified. Repeat until delta exits 0 and the native gate passes [VERIFIED, [baseline-delta-loop](../09-recipes/intermediate/baseline-delta-loop.md)].

## Rules that keep results honest

This section restates the fieldkit's load-bearing rules with the evidence behind each.

| Rule | Why (evidence) |
|---|---|
| Check `files=` on every scan | A zero-file scan exits 0 ([D-17](../DISCOVERY-LEDGER.md#d-17)) |
| Always pass `-c`, `-o` and `--json-output`; run from `.somnus-debug/` or a temp dir | No config auto-discovery; reports default to the project root; the log goes to the cwd ([D-02](../DISCOVERY-LEDGER.md#d-02), [D-10](../DISCOVERY-LEDGER.md#d-10)) |
| Run doctor in the project's environment | Import resolution uses the running interpreter ([D-26](../DISCOVERY-LEDGER.md#d-26)) |
| Never lower severities or gates, exclude source, or rename around a check | `SKILL.md:109`; a config change between scans also hides regressions from delta ([D-21](../DISCOVERY-LEDGER.md#d-21)) |
| Dispositions narrow: one file, explicit symbol, a reason | Broad entries absorb new findings and never go stale while they match [VERIFIED, [customization](../08-extensions/customization.md#dispositions-the-fieldkits-customization-layer)] |
| `pycache-clean` live only after a reviewed dry run and authorization; never `init-test-harness --force` without authority | Both delete or overwrite files (`SKILL.md:110`) |
| No CI, hooks or watchers by default | `SKILL.md:110`; `references/automation.md:57` |
| Do not present `structure` output or doctor cycles as a semantic graph | `SKILL.md:129`; doctor misses `from pkg import mod` cycles ([D-06](../DISCOVERY-LEDGER.md#d-06)) |

## Done means

This section is the handoff condition, from `SKILL.md:123-125`.

The change is complete; the native tests and gates pass; the final scan covers every edited file; `delta.py` exits 0, or every remaining new serious finding is explained; `dispositions.json` has no stale entries. The handoff states the CLI version, the runner, the delta verdict, the dispositions added with reasons, and anything that could not be verified. A ready-made sequence: [agent-workflows](agent-workflows.md).

## Where to go next

This section routes by need.

- Which tool for which question: [tool-selection](tool-selection.md).
- Calling the tools from code: [programmatic-invocation](programmatic-invocation.md).
- Formats to parse: [automation-contracts](automation-contracts.md).
- Splitting work across subagents: [subagent-patterns](subagent-patterns.md).
- When something fails: [failure-recovery](failure-recovery.md).

## Sources

This section lists the files, logs and evidence this page rests on.

- `skills/somnus-debug-fieldkit/SKILL.md:46-129`, `skills/somnus-debug-fieldkit/references/onboarding.md`, `skills/somnus-debug-fieldkit/references/doctor-loop.md`, `skills/somnus-debug-fieldkit/templates/AGENTS_APPENDIX.md`
- `skills/somnus-debug-fieldkit/scripts/onboard.py:528-529`
- [lane-f fieldkit](../_evidence/agent-findings/lane-f-ext/fieldkit.md)
- Wave 5 runs: [recipes execution log](../09-recipes/execution-log.md)
