# Somnus Accelerate integration

`somnus-debug` and Somnus Accelerate have separate operational jobs and connect cleanly through evidence.

| Concern | Owner |
|---|---|
| Task routing, authority mapping, packet boundary, continuity, and next action | Somnus Accelerate / target root `AGENTS.md` |
| Python static diagnostics, per-file AST index, cache cleaner, optional test-harness scaffold | `somnus-debug` |
| Acceptance semantics and release gate | The target repository's existing test, CI, contract, and operator policy |
| Host event timing and persistence | Existing host hooks, when deliberately configured |

## Integration pattern

1. Let the Accelerate router load this skill when Python diagnostics or the CLI apply. Append the block in `templates/AGENTS_APPENDIX.md`; do not replace or reorder the target router.
2. Keep `somnus-debug` findings, reports, config path, and CLI version inside the active task packet's evidence/validation fields. Record the final scan and native gate result in the existing continuity surface.
3. Use the task packet's real acceptance condition. A doctor severity gate is one diagnostic signal, not the task's complete `Validation` section.
4. Run the doctor loop at the task's meaningful Python boundaries: baseline before mutation, rescan after fixes, and final check before handoff. Reuse existing repo configs and gates.
5. Maintain Accelerate's existing test or gate. The somnus-debug `CONTRACT.md` explicitly allows an orchestrator to discover and invoke its single-test surface, while leaving acceptance meaning to the project.

## Harness boundary

The `somnus-debug init-test-harness` scaffold is optional. Accelerate does not require it. If a target already has a test harness, golden-path gate, CI validation, or project-owned `run_test.py`, preserve it. If a task explicitly adopts the scaffold, let the project define its test and acceptance criteria in the scaffold's designated edit points; do not let the scaffold redefine Accelerate packet structure.

## Host automation seam

When Accelerate or another host provides hooks, use a thin event contract:

- **Before task execution:** resolve project root and expose the `somnus-debug` route plus active doctor config.
- **After a meaningful Python edit:** record the touched files and schedule/perform a doctor rescan at a coherent validation boundary. Do not scan every intermediate keystroke or partially written file.
- **Before handoff:** attach final diagnostic report, scan coverage, installed version, native test result, dispositions, and next action to the active packet.

The target repository owns semantics. Host automation assembles and persists evidence; it does not change thresholds, claim a pass, or rewrite task acceptance. Avoid installing hooks or daemons until an existing Accelerate/host seam is identified and the project opts into it.
