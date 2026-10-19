---
name: somnus-debug-fieldkit
description: >
  Operate and onboard the existing somnus-debug CLI inside a target codebase.
  Use for Python diagnostics, structure indexing, bytecode-cache cleanup,
  single-test harness scaffolding, repeated diagnose-fix-rescan work, adding
  the somnus-debug block to AGENTS.md, or coordinating its evidence with
  Somnus Accelerate or another agent harness. This skill is for using and
  maintaining somnus-debug, not developing the somnus-debug package. Current
  scope is somnus-debug only; Graphify is deferred.
---

# somnus-debug fieldkit

Use this skill as the agent's operating map for `somnus-debug` in a codebase. The short route is: **check the local authority and CLI, establish a real baseline, inspect the relevant Python structure, fix work in scope, run the project's own proof, rescan, and repeat until the diagnostic delta is understood and stable.**

## Start here

1. Read the target root `AGENTS.md` and the repository's native instructions, tests, gates, and configuration. Those own the project.
2. Check that the command exists and identify the installed version:

   ```console
   somnus-debug --version
   somnus-debug --help
   ```

   If unavailable, stop at the installation boundary and report that the CLI is unavailable. Follow the user's environment policy; do not silently install packages or change global environments.
3. Route to one reference below. Do not load every reference for a one-command task.

## Semantic router

| Need | Open this | First action |
|---|---|---|
| New repo, first use, or cold start | [topology](references/topology.md) → [commands](references/commands.md) | Map local authority, check the CLI, then establish doctor configuration and a baseline. |
| Python change, production-readiness claim, or repeated debugging | [doctor loop](references/doctor-loop.md) | Run a configured baseline, inspect relevant findings, make the real change, validate, rescan, and loop. |
| Exact flags, subcommands, output, or known failure | [commands](references/commands.md) | Confirm the installed CLI's `--help`; use the command contract. |
| How it fits an existing Accelerate workflow | [Accelerate integration](references/accelerate-integration.md) | Keep task routing, acceptance, and continuity in their existing owners; attach somnus-debug evidence to that work. |
| Hook, watcher, CI, or local automation decision | [automation](references/automation.md) | Adopt the lightest existing host seam; do not install a watcher by default. |
| Version, publication, or documentation conflict | [provenance](references/provenance.md) | Check installed version and current upstream source; do not trust stale README/manual status text. |
| Need a copyable agent-instruction block | [AGENTS appendix](templates/AGENTS_APPENDIX.md) | Append it to the intended instruction surface; preserve existing instructions. |

## Load-bearing rules

1. **The loop is mandatory when code changes.** A scan is not a one-time ceremony. Baseline → targeted inspection → repair → project validation → doctor rescan → compare → repeat while actionable in-scope findings remain or new findings appear. For Python edits, do not close the task without a post-change scan or a plainly stated blocker.
2. **A scan is evidence, not a verdict on the whole system.** `doctor` statically analyzes Python against configured patterns and checks. A passing severity gate is not integration, runtime, security, or release proof. Read and verify each finding before editing.
3. **Configure the real surface.** The generated doctor config's default includes Somnus-style `tools/*.py` and `test/*.py` paths. A zero-file scan is a configuration failure, not a clean bill of health.
4. **Use each tool for its actual boundary.** `structure` indexes one Python file's AST definitions without importing it. `doctor` includes dependency-cycle findings, not a complete codebase graph. `pycache-clean` deletes files. `init-test-harness` writes a project-owned harness and contract.
5. **Preserve the target's existing control plane.** The repository's `AGENTS.md`, test commands, CI, and acceptance criteria remain authoritative. This skill adds a diagnostic route; it does not replace existing routes.
6. **Keep local systems local.** The skill is global. Any `.somnus-debug/` profile, `.python_doctor/` database, report, or optional hook is created only inside the active codebase and only when it helps the current workflow.
7. **No cargo-cult mutations.** Never run cache cleanup live without an explicit cleanup need and a reviewed dry run. Never pass `--force` to harness scaffolding over existing files without explicit authority. Do not install CI, pre-commit, or a watcher just because a template exists.

## The operating loop

Use [doctor-loop.md](references/doctor-loop.md) for the complete protocol. The loop has two layers:

- **Agent loop:** use actual findings to drive implementation and keep scanning after meaningful Python edits.
- **Tool loop:** use `doctor history` when state is available, re-index changed or dense files with `structure`, and preserve baseline/final reports under a project-local location when useful.

Stop when the requested work is complete, project-native validation passes, the final diagnostic delta is reviewed, every in-scope finding is fixed or explicitly dispositioned with evidence, and no new actionable regression remains. Do not expand a bounded task into an endless cleanup of unrelated heuristics.

## Scope boundary

This release intentionally excludes Graphify. Do not present AST indexes, import-cycle checks, or doctor reports as a complete semantic code graph. A future Graphify layer can be added as a separate route while keeping the `somnus-debug` loop intact.

## Source authority

For exact behavior, check the active installation's `somnus-debug <command> --help`, then the matching version's upstream manual. The bundled references summarize the source snapshot recorded in [provenance.md](references/provenance.md); update those references when the active upstream behavior materially changes.
