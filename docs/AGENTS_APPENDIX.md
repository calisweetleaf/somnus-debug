# somnus-debug — Global Agent Appendix

This file is the portable instruction surface for making `somnus-debug`
available to agents across projects. It is deliberately an appendix, not a
replacement for a repository's local `AGENTS.md`, test commands, or release
gates.

## Installation and activation are separate

Installing a Python CLI does not make its operating contract visible to every
agent. Use the two independent steps below:

1. Install the CLI into the user's tool environment. For a published release,
   prefer `pipx install somnus-debug`; for a locally built wheel, use
   `pipx install /path/to/somnus_debug-<version>-py3-none-any.whl`.
2. Copy the appendix block below into the global agent instruction surface or
   into a project's local `AGENTS.md`. That placement is an operator decision:
   this package must not silently rewrite global instructions.

Before installation, the package is not yet published to PyPI. The source
repository and release state remain authoritative for the available artifact.

## Pasteable global instruction block

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
- Inspect `python_doctor.yaml` before the first scan. The shipped defaults use
  Somnus-style `tools/` and `test/` globs and can otherwise scan zero files.
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
Exact flags and troubleshooting: that repository's docs/MANUAL.md.
```

## Verification after activation

```bash
command -v somnus-debug
somnus-debug --version
somnus-debug --help
```

The first command proves PATH exposure; the latter two prove that the unified
dispatcher, not merely the installed distribution metadata, is consumable.
