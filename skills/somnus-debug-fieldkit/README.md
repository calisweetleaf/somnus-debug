# somnus-debug fieldkit

An agent-facing, global skill package for using the existing `somnus-debug` CLI inside individual codebases. The skill and references are global knowledge; configuration, scan state, reports, and any optional hook belong to the target repository.

## Package map

- `SKILL.md` is the entry router. Read it first; it points to the right reference for each task.
- `references/topology.md` maps the toolkit's surfaces and common misreadings.
- `references/commands.md` gives the command contract and exact safe usage.
- `references/doctor-loop.md` defines the required diagnose, repair, rescan loop.
- `references/accelerate-integration.md` explains the boundary with Somnus Accelerate and other harnesses.
- `references/automation.md` describes low-friction host hooks and optional local automation.
- `references/provenance.md` records the repository snapshot and version discrepancies this skill was built against.
- `templates/AGENTS_APPENDIX.md` is the copy-ready block for a global or repo-local `AGENTS.md`.

## Placement

Install the package as a user-level skill, for example under `~/.codex/skills/somnus-debug-fieldkit/`, using the skill loader's normal installation path. Do not install this package into every codebase. A target codebase may receive only its own `AGENTS.md` block, doctor configuration, scan reports, and optional state under the project's own policy.

This package currently covers `somnus-debug` only. Graphify integration is intentionally deferred; the skill does not claim to construct a complete semantic graph of a repository.
