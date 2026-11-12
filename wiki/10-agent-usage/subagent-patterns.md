# Subagent patterns

This page covers splitting somnus-debug work across several agents or processes at once: what can safely run in parallel, what must have one owner, and what breaks when two scans share state. The fieldkit's own guidance is one line, "avoid concurrent scans against the same SQLite state" (`skills/somnus-debug-fieldkit/references/automation.md:67`); this page shows why with runs.

## What breaks when subagents share state

This section records the parallel runs made for this page.

Executed: yes (`/tmp/w4/par`, a copy of the onboarded fixture; two scans launched in the same shell instant; [stage 6d log](../09-recipes/_repro/logs/stage6d_parallel.log))

| Run | Setup | Observed |
|---|---|---|
| P-A | two stateful scans, same `state_dir`, state directory freshly deleted | one scan recorded `Run ID: 20261112T010112Z`; the other printed `Warning: local SQLite state is unavailable; continuing without history or rollback (Unable to initialize state database.)` and ran stateless. Both exit 1. History: 1 row |
| P-A2 | two stateful scans, same `state_dir`, database already present | both printed `Run ID: 20261112T010113Z`; history kept one row for that ID |
| P-B | two `--no-state` scans, each in its own cwd with its own `-o`/`--json-output` | both completed; identical `issues`; each cwd got its own `production_doctor.log` |

What this means [VERIFIED for these runs; race-dependent, so the exact outcome of P-A is CONDITIONAL on timing]:

- Concurrent stateful scans lose history silently: either one falls back to stateless (with only a stderr warning and an unchanged exit code), or both share a per-second run ID and `INSERT OR REPLACE` keeps one ([D-08](../DISCOVERY-LEDGER.md#d-08), [D-28](../DISCOVERY-LEDGER.md#d-28)).
- Scans themselves are deterministic and independent; with private outputs and `--no-state` they are safe to run in parallel.
- Two scans writing the same `-o` path, or running in the same cwd, would overwrite each other's report or interleave one log file [HYPOTHESIS from the write paths; not run].

## Ownership rules

This section assigns each artifact to one agent.

| Artifact | Owner | Others |
|---|---|---|
| `.somnus-debug/python_doctor.yaml`, `pycache.yaml` | orchestrator (and only with a recorded reason) | read |
| `runs/baseline.*` | orchestrator; moved only by the [ratchet](../09-recipes/advanced/quality-ratchet.md) | read |
| `dispositions.json` | orchestrator merges; subagents propose entries with reasons | propose |
| `state/` (history) | at most one stateful scanner at a time | `--no-state` only |
| per-subagent outputs | each subagent, in its own directory (e.g. `runs/<agent>/` or a temp dir) | — |
| the code under edit | one subagent per file at a time | read |

## Pattern S1: orchestrator gates, workers edit

This section is the default split for a change touching several areas.

1. The orchestrator onboards (or reads `PROFILE.md`) and owns the slice baseline.
2. Each worker gets a disjoint set of files, makes its change, and runs the project's tests for its area.
3. Each worker may self-check with a `--no-state` scan into its own directory and a `delta.py` against the shared baseline. Since the scan covers the whole tree, a worker sees other workers' in-progress edits as well; it should filter `regressions` to its own files before acting.
4. When workers finish, the orchestrator runs the single authoritative stateful scan and `delta.py`, merges proposed dispositions (rejecting broad ones), and decides.

Executed: no as a multi-agent run. Steps 3-4 use only commands executed in this wave ([P-B](../09-recipes/_repro/logs/stage6d_parallel.log), [baseline-delta-loop](../09-recipes/intermediate/baseline-delta-loop.md)).

## Pattern S2: read-only analysis fan-out

This section splits triage, which is safe to parallelize fully.

From one `runs/latest.json` and one `runs/delta.json`, give each subagent a subset of `regressions` (by file or by category) and the slice from [findings-to-source-slices](../09-recipes/advanced/findings-to-source-slices.md). Each returns a proposed outcome: fix, disposition (with the exact entry and reason), out of scope, or unverified. No subagent runs doctor. The stale-report guard in `findings_to_slices.py` (exit 2 when any scanned file's hash changed) tells a subagent its slice is out of date [VERIFIED].

## Pattern S3: per-package scans

This section covers splitting one large repo by subtree.

Doctor scans one root per call. Separate `--no-state` scans per package root can run in parallel into separate directories. Caveats: module names are indexed from the scan root, so cross-package imports resolve differently than in a whole-repo scan (see [src-layout-cycle-check](../09-recipes/advanced/src-layout-cycle-check.md)), and `delta.py` must compare reports from the same root, or every file counts as dropped [HYPOTHESIS for the delta consequence, from `skills/somnus-debug-fieldkit/scripts/delta.py:176-181`].

## Handoff contract between agents

This section is what a subagent should return so the orchestrator does not have to re-run anything.

```text
{ cli_version, runner, config_path, config_hash (from the report),
  report_json (absolute path), files_scanned,
  delta_exit, regressions: [...from delta --json...],
  proposed_dispositions: [{category, file, symbol, reason}],
  native_tests: {command, exit},
  unverified: [text] }
```

Every field comes from an artifact defined in [automation-contracts](automation-contracts.md). Including `config_hash` lets the orchestrator reject a delta computed under a different config ([D-21](../DISCOVERY-LEDGER.md#d-21)). [Design guidance; HYPOTHESIS as a format, nothing in the toolchain consumes it.]

## Sources

This section lists the files, logs and evidence this page rests on.

- [stage 6d log](../09-recipes/_repro/logs/stage6d_parallel.log)
- `skills/somnus-debug-fieldkit/references/automation.md:59-71`, `skills/somnus-debug-fieldkit/scripts/delta.py:176-181`
- [lane-a API reference, State](../_evidence/agent-findings/lane-a-arch-api/api-reference.md), [lane-d exit codes](../_evidence/agent-findings/lane-d-cli-tests/exit-codes.md)
