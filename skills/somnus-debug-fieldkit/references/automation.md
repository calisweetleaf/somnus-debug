# Low-friction automation

The skill's required loop is the first automation layer: agent instructions create repeatable events without adding background processes or changing a repository's build system.

## Recommended event cadence

| Event | Action |
|---|---|
| Agent starts a Python code task | Check CLI/version, config, target instructions, and baseline coverage. |
| A meaningful Python edit is complete | Re-index affected files where useful and run a doctor scan before declaring the slice verified. |
| A diagnostic repair is made | Run the project test/gate and doctor again; compare deltas and repeat if actionable findings remain. |
| Before commit or handoff | Run a final doctor scan and the repository's actual gate; record reports and any dispositions. |
| A codebase is first onboarded | Add the `AGENTS.md` appendix, initialize a project-local doctor profile only if absent, and tune coverage to the real tree. |

## Optional hook layers

Use the least intrusive layer the target already supports:

1. **Agent/router instruction** — reference this skill from existing `AGENTS.md`; this works across agents and requires no runtime watcher.
2. **Somnus Accelerate packet** — place scan and native-gate commands in the active packet's validation section.
3. **Existing pre-commit or CI** — add a doctor command only after the config is stable, project globs are verified, and the team wants the severity gate to block that boundary. Route temporary reports outside tracked source or into a project-local ignored state path according to local policy.
4. **Host post-edit callback** — trigger after a batch of Python writes, not each token or partial save. Debounce edits and avoid overlapping scans.

Do not install an always-on filesystem watcher or new pre-commit framework by default. First prove the normal loop is useful in that codebase. A watcher that repeatedly scans temporary states creates noise and can make an in-progress implementation look like a regression.

## Hook contract for a future adapter

An adapter should receive the repository root, changed paths, active config, task/packet id if available, and permission boundary. It should:

- ignore changes outside configured Python scope;
- run one coherent scan per completed edit batch;
- preserve the CLI exit status and report path;
- emit findings as evidence without auto-fixing code or changing config;
- avoid concurrent scans against the same SQLite state;
- update the owning task/packet with the result;
- stop or report clearly if the CLI/config is missing.

The adapter should not alter doctor thresholds, clean caches, scaffold tests, or add files without an explicit repository-level setup decision.

## Expansion seam

This package currently covers `somnus-debug` only. Future Graphify work should add an independently routed reference and explicit data-flow boundary, then compose it with this loop. Preserve the distinction between per-file AST indexing, import diagnostics, and an actual repository graph.
