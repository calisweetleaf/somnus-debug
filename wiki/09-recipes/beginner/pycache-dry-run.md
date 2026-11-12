# Recipe: preview a bytecode cleanup with `pycache-clean`

**Tier:** supported now. **Tool:** `pycache-clean`. **Mutates files:** only on a live run.

See exactly which `__pycache__` directories and `.pyc` files the cleaner would remove, with a config that cannot delete anything by accident.

## When to use

This section says when cleaning bytecode is worth doing.

Before running a test harness or the project's own tests, when stale bytecode could hide an import error at runtime. It is not useful before a doctor scan: doctor only reads `*.py` and ignores `__pycache__/*` and `*.pyc` by default, and lane F found identical issue sets with and without bytecode present [VERIFIED, [lane-f compositions C4](../../_evidence/agent-findings/lane-f-ext/compositions.md)].

## Steps

This section gives the config and the commands. `sd` is `/tmp/w4/venv/bin/python -m somnus_debug.cli`.

```yaml
# clean.yaml
roots:
  - "/tmp/w4/b3/tree"        # absolute: relative roots resolve against the cwd, not this file
exclude:
  - node_modules             # directory NAMES only; "node_modules/*" never matches
dry_run: true                # locks the config to preview mode
```

```console
sd pycache-clean --config clean.yaml --dry-run --verbose
find tree -type f | sort      # confirm nothing was removed
```

## Executed result

This section shows the preview and proves it deleted nothing.

Executed: yes (`/tmp/w4/b3`, tree with `pkg/__pycache__/m.cpython-312.pyc`, `pkg/stray.pyc`, `node_modules/__pycache__/x.pyc`; [stage 1 log](../_repro/logs/stage1_beginner.log), section B3)

```text
$ sd pycache-clean --config clean.yaml --dry-run --verbose
[INFO] Starting pycache cleaner (dry_run=True)
[INFO] Scanning root: /tmp/w4/b3/tree
[DEBUG] Skipping excluded directory: /tmp/w4/b3/tree/node_modules
[DEBUG] Deleting directory: /tmp/w4/b3/tree/pkg/__pycache__ (0.00 MiB)
[INFO] Removed directory /tmp/w4/b3/tree/pkg/__pycache__
[DEBUG] Deleting file: /tmp/w4/b3/tree/pkg/stray.pyc (0.00 KiB)
[INFO] Removed file /tmp/w4/b3/tree/pkg/stray.pyc
[INFO] Summary: deleted 1 directories, 1 files; freed 0.00 MiB              [exit=0]
$ find tree -type f | sort
tree/node_modules/__pycache__/x.pyc
tree/pkg/__pycache__/m.cpython-312.pyc
tree/pkg/stray.pyc                                                           # all three still present
$ sd pycache-clean --config clean.yaml          # no --dry-run flag; the config's dry_run: true still holds
[INFO] Starting pycache cleaner (dry_run=True)
[INFO] Summary: deleted 1 directories, 1 files; freed 0.00 MiB              [exit=0]
```

Read the dry-run log as "would remove": it says "Removed" and "deleted" even though nothing was touched ([D-14](../../DISCOVERY-LEDGER.md#d-14)) [VERIFIED].

## Going live

This section is the deliberate step that deletes files.

Edit the config to `dry_run: false` (or remove the line) and run without `--dry-run`. There is no `--no-dry-run` flag; CLI flags can only force dry-run on [VERIFIED by lane B]. The fieldkit's generated `.somnus-debug/pycache.yaml` is dry-run locked for the same reason, and its rules say never to run the cleaner live without a reviewed dry run and authorization (`skills/somnus-debug-fieldkit/templates/AGENTS_APPENDIX.md:52`).

## Pitfalls

This section lists the config hazards that turn a cleanup into data loss.

- Values are not type-checked: `dry_run: no` is false and deletes; `dry_run: "false"` is truthy and stays dry while the log prints `dry_run=false` ([D-14](../../DISCOVERY-LEDGER.md#d-14)) [VERIFIED by lane B].
- `roots: /some/path` written as a scalar is iterated character by character and can include `/` as a root ([D-14](../../DISCOVERY-LEDGER.md#d-14)) [VERIFIED by lane A, constructor only].
- `targets` is user-settable and deletes any matching name, not just bytecode ([existing-extension-points E11](../../08-extensions/existing-extension-points.md#e11-in-practice-targets-turns-the-cleaner-into-a-general-deleter)) [VERIFIED in this wave].
- A missing root is logged as an error and still exits 0 [VERIFIED by lane D].
- The default `--config` is `./config.yaml` in the cwd.
- A cold import prints a `SyntaxWarning: invalid escape sequence` from `pycache_cleaner/core.py:64`; harmless, visible whenever bytecode caching is off [VERIFIED in this wave].

## Sources

This section lists the files, logs and evidence this page rests on.

- [stage 1 log](../_repro/logs/stage1_beginner.log), [stage 6 log](../_repro/logs/stage6_integrations.log) (E11)
- [lane-b configuration findings §1 items 7-9](../../_evidence/agent-findings/lane-b-config/configuration-findings.md), [lane-d exit codes](../../_evidence/agent-findings/lane-d-cli-tests/exit-codes.md)
- `src/somnus_debug/pycache_cleaner/core.py:158-199`, `skills/somnus-debug-fieldkit/templates/AGENTS_APPENDIX.md:52`
