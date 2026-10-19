# somnus-debug agent skill entry

This legacy path remains as a compact compatibility entry for existing links. The canonical, detailed agent skill is now the complete [somnus-debug fieldkit](../skills/somnus-debug-fieldkit/SKILL.md), with its routed references and copy-ready [AGENTS appendix](../skills/somnus-debug-fieldkit/templates/AGENTS_APPENDIX.md).

## Activation

When the global `somnus-debug-fieldkit` skill is available, load it for Python diagnostics, AST structure orientation, authorized cache cleanup, optional test-harness scaffolding, or repeated diagnose–repair–rescan work. If it is not installed, use the linked repository copy as the reference package; do not pretend the skill is installed merely because the source exists here.

The fieldkit does not replace the target repository's `AGENTS.md`, tests, CI, acceptance criteria, or security policy. Read its entry router first and follow only the references needed for the task.

## CLI availability

Somnus Debug is published on PyPI. Install the CLI into the environment authorized by the operator, for example:

```console
pip install somnus-debug
somnus-debug --version
somnus-debug --help
```

Do not silently install it or alter a global environment. Check the installed command and its subcommand help before relying on flags. The fieldkit provenance keeps PyPI package versions distinct from Git tag versions; do not infer one numbering scheme from the other.

Exact CLI behavior remains documented in [docs/MANUAL.md](../docs/MANUAL.md), and this repository's operational security policy remains in [docs/OPSEC.md](../docs/OPSEC.md).
