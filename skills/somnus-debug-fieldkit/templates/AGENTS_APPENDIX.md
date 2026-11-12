---
somnus:
  schema: "somnus://metadata/core/2.0.0"
  id: "urn:somnus:artifact:01a19ace-7752-737a-a2db-45ae5ef93913"
  revision: 1
  title: "somnus-debug"
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
      - target_ref: "urn:somnus:artifact:01a19ace-7752-737a-a2db-45ae5ef93913"
        aspects: ["content"]
  time: {}
  names:
    slug: "somnus-debug"
  knowledge:
    coverage: "artifact"
    subjects: ["urn:somnus:artifact:01a19ace-7752-737a-a2db-45ae5ef93913"]
  access:
    visibility: "internal"
    allowed_uses: ["archive", "search", "reason"]
  ingestion:
    disposition: "candidate"
    body_role: "narrative"
---
## somnus-debug

This repository uses the global `somnus-debug-fieldkit` skill for Python diagnostics. It is a supplemental evidence route. This file's other instructions, the project tests, CI, and acceptance criteria stay authoritative.

**Profile:** `.somnus-debug/PROFILE.md` has the runner, config, coverage, and exact commands. Read it before using somnus-debug here. Run doctor from `.somnus-debug/`.

### For any task that changes Python

1. Baseline before the first edit: the profile's `doctor scan ... -o runs/baseline.md --json-output runs/baseline.json`.
2. Make the change, then run this repo's real tests and gates.
3. Rescan to `runs/latest.*`, then run `delta.py runs/baseline.json runs/latest.json --dispositions dispositions.json` from the skill's `scripts/`.
4. Triage every new finding, and every persisting one in touched code: fix it, mark it out of scope, disposition it in `dispositions.json` with a reason, or flag it unverified. The skill's `references/findings.md` has the real fixes and known false positives.
5. Repeat until `delta.py` exits 0 (or each remaining new serious finding is explained) and the native gate passes. In the handoff, state the CLI version, the delta verdict, and the dispositions added.

### Never

- Treat a green doctor run as integration, runtime, security, or release proof. It is static analysis, and it does not measure test coverage.
- Trust a scan without checking `files=`. Zero files exits 0 and means the config is wrong.
- Lower severities or gates, exclude source, or rename around a check to get a green result.
- Run `pycache-clean` live without a reviewed dry run and authorization, or pass `--force` to `init-test-harness`.
- Install watchers, hooks, CI jobs, or packages without the owner's decision.

If `.somnus-debug/PROFILE.md` is missing, onboard first with the skill's `scripts/onboard.py <repo>` (plan mode), then `--apply --baseline`.
