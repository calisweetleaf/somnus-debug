# Coverage Report

This report states the investigation's scope, what was inspected and how deeply, what was verified, and what remains open, using counts with stated denominators rather than percentages.

## Scope

This section defines the denominator.

- **In scope:** all 46 tracked files of the 2026-11-11 upload (baseline `034f46e`): 12 package source modules plus package data in `src/somnus_debug/`, 4 root duplicates and `python_doctor.yaml`, `tests/test_cli_smoke.py`, the fieldkit (`skills/somnus-debug-fieldkit/`, 3 scripts and 12 docs), `docs/` (5), `README.md`, `pyproject.toml`, operator files `STATE.md` and `PLAN.md`, assets and licenses.
- **Runtime comparison:** source tree, a non-editable /tmp venv install, and the PyPI 0.1.0 artifacts (downloaded, diffed).
- **Out of scope:** Daeron's local checkouts and `~/.local/bin` install named in STATE.md (unreachable), the GitHub remote, other Somnus systems (Plot v0.7 and somnus-metadata get their own runs).

## Source coverage

This section counts inspection depth per file; the per-file table is [`_evidence/source-coverage.tsv`](_evidence/source-coverage.tsv).

| Depth | Files | Meaning |
|---|---|---|
| executed | 16 | code run in /tmp by at least one lane (all package modules, tests, fieldkit scripts) |
| diffed | 5 | root duplicates and root config compared line by line with `src/` |
| read | 20 | docs, fieldkit references, manifests, templates read and reconciled claim by claim |
| listed | 5 | assets, licenses, `.gitignore`: inventoried only, no behavioral content |

All 256 symbols in `src/` are enumerated by AST ([symbol index](13-reference/symbol-index.md)); 143 are documented with stability tiers in the [api index](04-library-api/api-index.md).

## Interface and configuration coverage

This section counts the surfaces established.

| Surface | Count | Status |
|---|---|---|
| Console scripts | 4 | all executed |
| Dispatcher subcommands | 4 (+5 doctor sub-subcommands) | all executed, help captured verbatim |
| Fieldkit scripts | 3 | all executed, every documented exit code confirmed |
| Configuration surfaces | 131 registry rows | 103 VERIFIED, 28 SOURCE-CONFIRMED ([registry](_evidence/configuration-registry.tsv)) |
| Doctor finding categories | 20 configured | 19 emitters mapped to lines; `test_gaps` has none (D-05) |
| Capabilities | 25 | [atlas](CAPABILITY-ATLAS.md) |
| Discoveries | 34 | [ledger](DISCOVERY-LEDGER.md) |
| Recipes | 19 | all executed |
| Hooks, plugins, entry-point groups, MCP | 0 found | search scope: all of `src/`, installed entry points, fieldkit ([plugin integration](08-extensions/plugin-integration.md)) |

## Call paths traced

This section lists the end-to-end traces documented.

Dispatcher to each tool; doctor `scan` (config load, file discovery, per-file analysis, each detector, import graph, scoring, state, report rendering, exit gate); `init-config`, `history`, `rollback`, `self-check`; structure `build_index` and render; pycache cleaner traversal and delete; scaffold copy; harness run; fieldkit onboard, delta, selftest. See [call chains](07-internals/call-chains.md) and [state transitions](07-internals/state-transitions.md).

## Tests and experiments

This section summarizes executed evidence; details in [verification manifest](_evidence/verification-manifest.md).

- Smoke suite: 10 passed, 2 failed on Python 3.10, 3.11 and 3.12 (D-01).
- Fieldkit selftest: 29/29 on 3.10, 3.11, 3.12.
- Experiment sets: about 200 recorded runs across lanes ([experiment log](_evidence/experiment-log.md)).

## Template sections and how they apply

This section accounts for every section of the mission's baseline structure.

All baseline pages exist. Pages whose subject is absent from the codebase say so with their search scope rather than inventing content: [hooks-and-events](08-extensions/hooks-and-events.md), [plugin-integration](08-extensions/plugin-integration.md), [async-and-concurrency](04-library-api/async-and-concurrency.md) (no async API; a thread pool exists), [registries-and-discovery](07-internals/registries-and-discovery.md) (no registry; only file discovery and a hard-coded severity table). Added beyond the template: `09-recipes/execution-log.md`, `09-recipes/_repro/`, `wiki-index.json`, `_evidence/source-files.tsv`, `_evidence/agent-findings/w3-config-probes/`.

## Delegation that actually occurred

This section records the real division of labor.

Four research lanes ran in parallel (A+C, B, D+E, F), then four page writers (W1-W4), then one independent reviewer (H). The lead did coordination, reconciliation of lane disagreements, the ledger, atlas, discovery views, evidence indexes, and applied the review corrections. No other agents were involved.

## Review outcome

This section records the skeptical reviewer's verdict and what changed.

Reviewer H declined to certify the first draft on two high-severity errors (missing-root exit code stated as always 4) and eight medium items. All 21 actionable corrections were applied; the remaining item (H-10, unarchived run records after the sandbox reset) is disclosed in the [verification manifest](_evidence/verification-manifest.md). With those applied, the reviewer's stated blockers are cleared; a second review pass was not run.

## Remaining gaps

This section lists what is still open; each is tracked in [unresolved questions](12-discoveries/unresolved-questions.md).

Windows behavior; Python below 3.10; live scalar-roots pycache run (withheld); symlink loops; fault-injected exit 5; concurrent stress beyond two scans; GitHub rendering; comparison with the canonical remote; ledger entries D-19 to D-23, D-26, D-27, D-32 were not independently re-run by the reviewer (they rest on lane F and W4 logs).

## Modification boundary

This section confirms nothing outside `wiki/` changed.

`git status` against baseline `034f46e` shows only `?? wiki/`. Investigation side effects outside the repo (`forge/test-runs/` from executing the root `run_test.py`, `__pycache__/` under `src/` from `PYTHONPATH` runs) were removed after confirming they were not part of the upload.
