# Recipe: opt-in git pre-commit gate

**Tier:** supported now, installed by hand. **Script:** [pre-commit.sh](../_repro/pre-commit.sh). **Needs:** an onboarded repo with a project `.venv` and `runs/baseline.json`.

Block a local commit that adds a new serious or critical finding, using the same delta gate as CI, without installing any hook framework.

## When to use

This section says when a hook is appropriate at all.

Only when the repo owner decides they want commit-time blocking. somnus-debug ships no hook and no installer, and the fieldkit says not to add hooks, CI or watchers by default (`skills/somnus-debug-fieldkit/references/automation.md:57`, `skills/somnus-debug-fieldkit/templates/AGENTS_APPENDIX.md:53`). Prove the [baseline-delta loop](../intermediate/baseline-delta-loop.md) is useful in the repo first.

## The hook

This section is the whole script; copy it to `.git/hooks/pre-commit` and make it executable.

```bash
#!/usr/bin/env bash
# Set FIELDKIT to the somnus-debug-fieldkit directory. Scans the WORKING TREE, not the staged index.
git diff --cached --name-only --diff-filter=ACMR | grep -q '\.py$' || exit 0
cd "$(git rev-parse --show-toplevel)/.somnus-debug" || exit 1
PYTHONPATH=../src ../.venv/bin/python -m somnus_debug.cli doctor scan .. -c python_doctor.yaml --no-state \
  -o runs/precommit.md --json-output runs/precommit.json > /dev/null
rc=$?
[ "$rc" -ge 4 ] && { echo "pre-commit: doctor failed to run (exit $rc)"; exit 1; }
python3 "$FIELDKIT/scripts/delta.py" runs/baseline.json runs/precommit.json --dispositions dispositions.json --json \
  | python3 -c 'import json,sys; d=json.load(sys.stdin); [print("pre-commit regression:", r["category"], r["file"], r["line"], r["symbol"]) for r in d["regressions"]]; sys.exit(d["exit"])'
```

Design choices: it skips commits with no staged `.py` file; it uses `--no-state` so commits do not grow doctor's history; it writes into the git-ignored `runs/`; it prints one line per regression from `delta.py --json`.

## Executed result

This section shows one blocked commit and one allowed commit.

Executed: yes (`/tmp/w4/proj`, after the profile was committed; `FIELDKIT` exported; [stage 5 log](../_repro/logs/stage5_automation.log), section T2)

```text
# staged: run_tool() calling subprocess.run(cmd, shell=True)
$ git commit -qm 'add run_tool'
pre-commit regression: security_risks src/inventory/store.py 48 run_tool       [exit=1]
$ git log --oneline
4dfb26a profile + fixes
bbe78fb init                                                                   # commit was blocked
# run_tool removed; staged: new src/inventory/notes.py
$ git commit -qm 'add notes'                                                   [exit=0]
$ git log --oneline
59b8833 add notes
4dfb26a profile + fixes
bbe78fb init
```

## Pitfalls

This section lists the hook's known gaps.

- **Working tree, not index.** Doctor scans files on disk, so unstaged edits count and partially staged files are judged by their unstaged state. A stash-based variant would fix this [HYPOTHESIS, not built].
- **Delta exit 2 blocks the commit** for both coverage loss and a delta usage error; the hook prints nothing in either case. Run `delta.py` by hand to see which.
- **Hard-coded runner.** It assumes a src layout and a project `.venv`; copy the runner from your `PROFILE.md` instead.
- **Speed.** Each commit runs a full scan. On large trees, prefer CI ([ci-delta-gate](ci-delta-gate.md)).
- **`git commit --no-verify` bypasses it,** like any client-side hook.

## Sources

This section lists the files, logs and evidence this page rests on.

- [stage 5 log](../_repro/logs/stage5_automation.log), [pre-commit.sh](../_repro/pre-commit.sh)
- `skills/somnus-debug-fieldkit/references/automation.md:48-71`, `skills/somnus-debug-fieldkit/templates/AGENTS_APPENDIX.md:53`
- [lane-f compositions C1](../../_evidence/agent-findings/lane-f-ext/compositions.md)
