---
somnus:
  schema: "somnus://metadata/core/2.0.0"
  id: "urn:somnus:artifact:01a19ace-7413-7673-a7f1-660ed55bff3f"
  revision: 1
  title: "somnus-debug — Global Agent Appendix"
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
      - target_ref: "urn:somnus:artifact:01a19ace-7413-7673-a7f1-660ed55bff3f"
        aspects: ["content"]
  time: {}
  names:
    slug: "somnus-debug-global-agent-appendix"
  knowledge:
    coverage: "artifact"
    subjects: ["urn:somnus:artifact:01a19ace-7413-7673-a7f1-660ed55bff3f"]
  access:
    visibility: "internal"
    allowed_uses: ["archive", "search", "reason"]
  ingestion:
    disposition: "candidate"
    body_role: "narrative"
---
# somnus-debug — Global Agent Appendix

This file is the portable instruction surface for making `somnus-debug`
available to agents across projects. It is deliberately an appendix, not a
replacement for a repository's local `AGENTS.md`, test commands, or release
gates.

## Installation and activation are separate

Installing a Python CLI does not make its operating contract visible to every
agent. Use the two independent steps below:

1. Install the CLI. For `doctor` on a real project, install it into that
   project's environment (`<venv>/bin/python -m pip install somnus-debug`):
   the doctor resolves third-party imports in the interpreter that runs it, so
   an isolated install such as `pipx install somnus-debug` reports every
   project dependency as `missing_imports`. An isolated install is fine for
   `structure`, `pycache-clean`, and `init-test-harness`.
2. Copy the appendix block below into the global agent instruction surface or
   into a project's local `AGENTS.md`. That placement is an operator decision:
   this package must not silently rewrite global instructions.

Somnus Debug is published on PyPI; the project page is https://pypi.org/project/somnus-debug/. Install the CLI and activate agent instructions as separate steps. Check the installed command with `somnus-debug --version` because a Git tag version and PyPI package version are distinct.

## Pasteable global instruction block

Paste this block unchanged into the instruction surface you chose.

```markdown
## somnus-debug

`somnus-debug` is an available project-agnostic Python diagnostics toolkit.
Use it as evidence-producing support for repository work; it never overrides
the repository's own AGENTS.md, test commands, or release gates.

- Before hand-writing a Python AST outline, use `somnus-debug structure
  <file.py>` when the target is one Python file and an AST-only view is enough.
- Before calling Python work production-ready, configure and run
  `somnus-debug doctor scan <project-root>` as one diagnostic input. Do not
  treat a green doctor report as full integration, runtime, or release proof.
- Inspect `python_doctor.yaml` before the first scan and pass it with
  `-c python_doctor.yaml`; the doctor never loads it on its own. The
  generated default includes every `*.py`; copied configs with Somnus-style
  `tools/` and `test/` globs can scan zero files, and a zero-file scan exits
  `0`.
- For an unconfigured or disposable project, avoid repository pollution with
  `--no-state`, explicit temporary report paths, and a reviewed config. Normal
  stateful scans create `.python_doctor/` for `history` and `rollback`.
- If SQLite state is unavailable (for example on FUSE, NFS, or a weak-locking
  filesystem), `doctor scan` warns and continues statelessly. Reports remain
  valid for that scan; `history` and `rollback` are unavailable for it.
- Use `somnus-debug pycache-clean --config <cfg> --dry-run` before any live
  cache cleanup. A non-dry-run cleanup is a filesystem mutation and still
  requires the repository's normal authority boundary.
- Use `somnus-debug init-test-harness <target-dir>` only when a project lacks
  an established harness and the scaffold is actually wanted; it creates
  files and refuses overwrite unless forced.

Reference: https://github.com/calisweetleaf/somnus-debug
Detailed agent workflow: that repository's skills/somnus-debug-fieldkit/SKILL.md. Exact flags and troubleshooting: that repository's docs/MANUAL.md.
```

## Verification after activation

Run these three commands where the agent will run the CLI.

```bash
command -v somnus-debug
somnus-debug --version
somnus-debug --help
```

The first command proves PATH exposure; the latter two prove that the unified
dispatcher, not merely the installed distribution metadata, is consumable.
