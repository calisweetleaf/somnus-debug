# somnus-debug fieldkit

A global agent skill for setting up and operating the `somnus-debug` CLI (`pip install somnus-debug`) inside individual Python codebases. The skill is global knowledge plus tested scripts. Configuration, state, reports, and dispositions belong to each target repository's `.somnus-debug/` profile.

## Package map

```text
SKILL.md                         entry router: start-here decision, loop commands, rules, sharp edges
references/
  install.md                     pip install, which environment, runners, verification
  onboarding.md                  what "onboarded" means; onboard.py procedure; manual fallback
  doctor-loop.md                 baseline -> change -> rescan -> delta -> triage protocol
  findings.md                    every doctor category: trigger, real fix, false positives, evasions
  commands.md                    command contract: flags, outputs, side effects, exit codes
  topology.md                    what each tool is and is not; interface and flow map
  accelerate-integration.md      evidence boundary with Somnus Accelerate and other harnesses
  automation.md                  hook and CI decisions; adapter contract
  provenance.md                  what this skill was verified against, and how to refresh it
scripts/
  onboard.py                     survey + runner choice + coverage proof + .somnus-debug/ profile
  delta.py                       baseline vs latest finding diff and regression gate
  selftest.py                    29-check contract test of every behavioral claim in the skill
templates/
  AGENTS_APPENDIX.md             copy-ready block for a repo's AGENTS.md
```

All scripts are standard-library Python 3.10+, call subprocesses with argv lists (never a shell), and are exercised end to end before each skill revision.

## Placement

Install the folder wherever the agent host loads user skills, for example `~/.factory/skills/somnus-debug-fieldkit/` or `~/.codex/skills/.../somnus-debug-fieldkit/`. Keep every installed copy identical to the canonical source in the somnus-debug repository (`skills/somnus-debug-fieldkit/`). A target codebase receives only its `.somnus-debug/` profile and an `AGENTS.md` block, never a copy of the skill.

## Validate after install or upgrade

```console
python3 scripts/selftest.py                      # against somnus-debug on PATH
python3 scripts/selftest.py --python .venv/bin/python
```

Graphify integration is deferred. The skill never presents AST indexes or import-cycle checks as a complete semantic graph.
