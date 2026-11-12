# Recipe: prove the installed CLI still matches the fieldkit (`selftest.py`)

**Tier:** supported now. **Script:** `skills/somnus-debug-fieldkit/scripts/selftest.py`. **Writes:** only inside its own temp directory.

Check, in one command, that the somnus-debug you are about to rely on behaves the way the fieldkit's references say: flags, exit codes, side effects, and the known detector quirks.

## When to use

This section says when to run it.

After installing or upgrading somnus-debug, after switching interpreters, and whenever a fieldkit reference and the CLI seem to disagree. The fieldkit's rule is that the CLI wins and the reference gets updated (`skills/somnus-debug-fieldkit/SKILL.md:129`, `references/automation.md:45`).

## Steps

This section gives the command.

```console
python3 <fieldkit>/scripts/selftest.py --python <interpreter-with-somnus-debug>   # or omit --python to use somnus-debug on PATH
```

## Executed result

This section shows a full pass and the no-CLI case.

Executed: yes (`/tmp/w4/n3`, against `/tmp/w4/venv/bin/python`; [stage 6 log](../_repro/logs/stage6_integrations.log), section N3)

```text
$ python3 selftest.py --python /tmp/w4/venv/bin/python > selftest.md; tail -2 selftest.md; grep -c '^| PASS' selftest.md
29/29 passed.
29                                                                             [exit=0]
$ env PATH=/usr/bin:/bin python3 selftest.py
somnus-debug not found. Install: pip install somnus-debug (or pass --python).  [exit=3]
$ ls
selftest.md                                                                    # nothing else left behind
```

The report is a Markdown table, one row per check: result, check name, observed value, and the fieldkit reference it proves. The first rows from this run:

```text
| PASS | --version answers | 0.1.0 | `references/install.md` |
| PASS | doctor scan --help flags | all documented flags present | `references/commands.md` |
```

## What the 29 checks cover

This section summarizes the four groups (`skills/somnus-debug-fieldkit/scripts/selftest.py:145-316`) [SOURCE-CONFIRMED; 29/29 VERIFIED].

| Group | Examples |
|---|---|
| CLI surface | `--version`; `--help` flags of 8 command surfaces; 3 `init-config` defaults |
| Exit codes and side effects | zero files → 0; serious → 1; syntax error → 2; bad gate → 4; log written to the cwd even for `--help`; report lands in the project root without `-o` |
| Finding triggers | src-layout `missing_imports` with and without `PYTHONPATH`; uninstalled import; `log.warning` silent vs `logger.exception` not; abstract-method stub; property-setter duplicate; `test_gaps` never emitted; case-insensitive `temp` todo |
| Other tools | `structure` writes nothing; pycache dry run deletes nothing; path-style exclude ignored; scaffold refuses overwrite |

Exit codes: 0 all pass, 1 any fail, 3 no CLI (`:319-346`).

## Pitfalls

This section lists what a pass does not prove.

- **The `structure` check uses an unstamped file,** so 29/29 passes while `structure` crashes on every metadata-stamped file ([D-01](../../DISCOVERY-LEDGER.md#d-01)) [VERIFIED by lane D]. Run [index-one-file](../beginner/index-one-file.md) on a stamped file if that matters to you.
- **A pass describes this interpreter only.** `missing_imports` depends on which interpreter runs doctor ([D-26](../../DISCOVERY-LEDGER.md#d-26)).
- **`--python` here accepts a symlinked venv interpreter** (it only calls `expanduser()`, `:325`), unlike `onboard.py --python`, which rejects it ([D-20](../../DISCOVERY-LEDGER.md#d-20)) [VERIFIED: selftest passed above with the same interpreter onboard rejected in [onboard-a-repo](../intermediate/onboard-a-repo.md)].

## Sources

This section lists the files, logs and evidence this page rests on.

- [stage 6 log](../_repro/logs/stage6_integrations.log)
- [lane-f fieldkit §1](../../_evidence/agent-findings/lane-f-ext/fieldkit.md), [lane-f selftest output](../../_evidence/agent-findings/lane-f-ext/logs/s1_selftest.md), [lane-d README item 7](../../_evidence/agent-findings/lane-d-cli-tests/README.md)
- `skills/somnus-debug-fieldkit/scripts/selftest.py:145-346`, `skills/somnus-debug-fieldkit/SKILL.md:93-101`, `:129`
