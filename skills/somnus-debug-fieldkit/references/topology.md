---
somnus:
  schema: "somnus://metadata/core/2.0.0"
  id: "urn:somnus:artifact:01a19ace-76b2-7515-b671-2c2576a5363a"
  revision: 1
  title: "Toolkit topology"
  classification:
    category: "engineering"
    type: "report"
    role: "informative"
    scope: "component"
    tags: []
  lifecycle:
    status: "draft"
  authority:
    standing: "candidate"
    scopes:
      - target_ref: "urn:somnus:artifact:01a19ace-76b2-7515-b671-2c2576a5363a"
        aspects: ["content"]
  time: {}
  names:
    slug: "toolkit-topology"
  knowledge:
    coverage: "artifact"
    subjects: ["urn:somnus:artifact:01a19ace-76b2-7515-b671-2c2576a5363a"]
  access:
    visibility: "internal"
    allowed_uses: ["archive", "search", "reason"]
  ingestion:
    disposition: "candidate"
    body_role: "narrative"
---
# Toolkit topology

**Domain:** using `somnus-debug` as a project-agnostic Python developer toolkit from inside a separate codebase.

## Load-bearing concepts

These seven ideas explain most of the toolkit's behavior.

### LBC 1 — The command is a dispatcher

`somnus-debug` dispatches to independent tools: `doctor`, `structure`, `pycache-clean`, and `init-test-harness`. Each command owns its own parser and flags. Ask that command's `--help`; do not assume every flag belongs to the top-level CLI.

### LBC 2 — Doctor findings are static-analysis evidence

The doctor parses Python source and checks configured patterns for issues such as stubs, placeholder returns, exception handling, cycles, missing documentation or hints, TODOs, and security-risk calls. It does not execute the target code. It resolves third-party imports with `find_spec` in its own interpreter, so where it runs changes the results; the project's own packages, including those under `src/`, resolve from the scanned files. `test_gaps` is configurable but never emitted in 0.1.0. Findings need interpretation ([findings](findings.md)) and project-native validation.

### LBC 3 — Include patterns define what exists to the scan

The doctor scans only files matching `include_patterns`, then removes matches in `ignore_patterns`. The `init-config` default is `*.py`, but copied Somnus-style configs (`tools/*.py`, `test/*.py`) scan nothing in most repos. Scanning zero files exits 0 and says nothing about code health.

### LBC 4 — Structure is a per-file AST index

`structure` reports classes, nested classes, functions, methods, signatures, decorators, doc summaries, and line spans for a single Python file. It neither imports nor executes the file. It is useful for orientation and change-impact review, not a whole-repository semantic graph.

### LBC 5 — Some commands mutate the target filesystem

`pycache-clean` deletes `__pycache__`, `.pyc`, and `.pyo` targets according to YAML roots and filters. `init-test-harness` writes `run_test.py` and usually `CONTRACT.md`. Treat these as explicit actions with dry-run/overwrite protections.

### LBC 6 — Doctor state is local and conditional

Stateful doctor scans create SQLite state under `state_dir` (`.python_doctor/` by default, `.somnus-debug/state/` in an onboarded profile), enabling `history` and `rollback`. A weak-locking filesystem may cause a warning and stateless continuation. `--no-state` is for deliberate disposable scans; it removes history for that run.

### LBC 7 — The harness is a separate contract

The scaffolded one-test surface defines artifact semantics and acceptance for one project-owned test. It does not decide the project gate, own Accelerate, or require pytest. Use it only when the target repository wants that contract.

## Interface map

Each surface's inputs, outputs, and limits.

| Surface | Receives | Produces / changes | Boundary |
|---|---|---|---|
| `doctor scan` | Project root + doctor YAML + optional output paths | Markdown/JSON findings; `.python_doctor/` state unless `--no-state` | Python diagnostics, not full correctness proof |
| `doctor history` | Root/config + limit | Prior run summaries from local SQLite | Requires usable stored state |
| `doctor rollback` | Root/config + run ID | Repoints the `latest` alias and `reports/latest.*` to an earlier run | Does not revert source code or `-o` reports |
| `doctor self-check` | Installed toolkit | Doctor's self-check scan and report | Checks doctor behavior against its own package |
| `structure` | One `.py` file | Definition index to stdout or file | AST only; one file at a time |
| `pycache-clean` | YAML roots/targets/excludes + dry-run choice | Dry-run plan or cache deletion | Destructive when live |
| `init-test-harness` | Target directory + overwrite flags | Project-owned `run_test.py`, optionally `CONTRACT.md` | Refuses overwrite unless `--force` |
| `scripts/onboard.py` | Repo root | `.somnus-debug/` profile, coverage proof, baseline | Never overwrites, except the baseline with `--force-baseline`; plan mode writes nothing |
| `scripts/delta.py` | Two doctor JSON reports with the same `config_hash` + dispositions | New/resolved/persisting findings, coverage verdict, exit 0/1/2/3 | Reads only |
| `scripts/selftest.py` | Installed CLI | 30 PASS/FAIL contract checks | Temp dir only |

## Dependency and flow map

How the CLI, the agent, and the project's own gates feed each other.

```mermaid
flowchart TD
  A[Target AGENTS and native gates] --> B[Installed somnus-debug CLI]
  B --> C[Doctor configuration]
  C --> D[Baseline and repeated scan evidence]
  B --> E[Structure index of relevant Python files]
  D --> F[Agent triage and code change]
  E --> F
  F --> G[Project tests and acceptance]
  G --> H[Doctor rescan and delta review]
  H -->|actionable findings remain| F
  H -->|stable and dispositioned| I[Handoff with evidence]
  B --> J[Optional cleanup or harness scaffold]
```

## Complexity distribution

Where to slow down.

| Surface | Density | Slow down because |
|---|---|---|
| Doctor config and coverage | DENSE | Incorrect include patterns can produce a convincing empty scan. |
| Finding triage | DENSE | Heuristics can be false positives; blindly fixing them can cause scope creep or regressions. |
| Doctor history/rollback | MEDIUM | State depends on local SQLite; rollback concerns reports, not source. |
| Structure index | MEDIUM | Useful for local architecture, easy to overstate as whole-repo graphing. |
| Pycache cleanup | DENSE | A live pass deletes files and roots are controlled by YAML. |
| Harness scaffold | MEDIUM | It writes a contract surface and protects existing hand-edited files. |

## Anti-concepts

What each result is not.

| Looks like | Actual boundary |
|---|---|
| A clean doctor exit | The configured severity gate passed; other correctness gates remain. |
| `doctor` dependency-cycle results | Selected import/cycle diagnostics, not a complete code graph. |
| `structure` output | A single-file AST index, not runtime call behavior or repository-wide architecture. |
| `doctor rollback` | Report-history restoration, not a source-control rollback. |
| `init-test-harness` | Optional project-owned test scaffold, not a required Accelerate installation. |
| A config that includes no files | Invalid coverage for the current task, not a passing scan. |
| No `test_gaps` findings | 0.1.0 never emits them; doctor says nothing about test coverage. |
| A `missing_imports` flood | Doctor runs outside the project env, so third-party dependencies are not importable from its interpreter. |

## Entry vectors

Where to start for each kind of task.

- **Cold repo:** read target instructions → check CLI/version → look for `.somnus-debug/PROFILE.md` → if absent, `scripts/onboard.py` plan then `--apply --baseline` ([onboarding](onboarding.md)) → add the AGENTS block.
- **Python implementation task:** read doctor loop → baseline → inspect touched files with `structure` → implement → native validation → rescan → `delta.py` → triage with `findings.md` → repeat.
- **After install or upgrade:** run `scripts/selftest.py`; fix any reference it names.
- **Cleanup request:** read command safety in `commands.md` → inspect roots/exclusions → dry-run → obtain authority for live cleanup → run and verify.
- **Harness request:** inspect existing tests and acceptance → read `CONTRACT.md` summary in `commands.md` → scaffold only if the repo wants it.
- **Accelerate repo:** read `accelerate-integration.md` and place findings/artifacts in the active packet's existing evidence flow.
- **Version discrepancy:** check `provenance.md` and live upstream files; installed CLI behavior wins for flags.
