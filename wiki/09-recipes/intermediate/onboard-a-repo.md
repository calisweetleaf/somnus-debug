# Recipe: onboard a repository with the fieldkit

**Tier:** supported now. **Tools:** fieldkit `onboard.py`, `doctor`. **Writes:** `.somnus-debug/` in the target repo, on `--apply` only.

Give a repository a project-local somnus-debug profile: the right interpreter, a config whose coverage is proven, a dry-run-locked cache config, an empty dispositions file, a baseline, and a `PROFILE.md` card with the exact commands.

## When to use

This section says when to onboard and when not to.

Once per repository, before the first Python change you want gated. Rerun plan mode when the tree changes shape. Do not use `--force`-style overwrites: onboard never overwrites its five profile files, and you regenerate one by deleting it deliberately.

## Steps

This section gives the two commands and what to read between them.

```console
python3 <fieldkit>/scripts/onboard.py <repo>                      # plan: survey, runner, coverage proof if a config exists; writes nothing
python3 <fieldkit>/scripts/onboard.py <repo> --apply --baseline   # write .somnus-debug/ and record a stateful baseline
```

`<fieldkit>` is `skills/somnus-debug-fieldkit` in this repo. Between the two runs, read the runner line and the noise list. If the project has a venv without somnus-debug, onboard says so and falls back to PATH, where every third-party import becomes `missing_imports` noise ([D-26](../../DISCOVERY-LEDGER.md#d-26)).

## Executed result

This section shows a full onboarding of a src-layout fixture.

Executed: yes (`/tmp/w4/proj`, git repo with `src/inventory/{__init__,store}.py`, `tests/test_store.py`, its own `.venv` holding a non-editable install of this repo; [stage 2 log](../_repro/logs/stage2_intermediate.log), section I1)

```text
$ python3 onboard.py proj
# somnus-debug onboarding plan: /tmp/w4/proj
- Python files in scope: 3 (root: 0; by top dir: {'src': 2, 'tests': 1})
- src layout: True; existing doctor configs: none; root .python_doctor/: False; profile: False
- note: src/ layout detected: scans run with PYTHONPATH=src so the project's own packages resolve.
- runner: project environment .venv (somnus-debug 0.1.0)
Doctor config: .somnus-debug/python_doctor.yaml (generate on --apply)
Plan only; nothing written. Rerun with --apply --baseline ...              [exit=0]
$ git -C proj status --short
                                                                            # clean: plan mode wrote nothing
$ python3 onboard.py proj --apply --baseline
Verify scan: files=3 issues=0 critical=0 serious=0 exit=0 (gate passed)
Baseline: files=3 issues=0 serious=0 critical=0 exit=0 run_id=20261112T004521Z
Wrote:
- /tmp/w4/proj/.somnus-debug/python_doctor.yaml
- /tmp/w4/proj/.somnus-debug/pycache.yaml
- /tmp/w4/proj/.somnus-debug/dispositions.json
- /tmp/w4/proj/.somnus-debug/.gitignore
- /tmp/w4/proj/.somnus-debug/PROFILE.md
Next: append .../templates/AGENTS_APPENDIX.md to this repo's agent instructions ...   [exit=0]
$ find .somnus-debug -type f | sort
.somnus-debug/.gitignore  PROFILE.md  dispositions.json  production_doctor.log  pycache.yaml  python_doctor.yaml
.somnus-debug/runs/baseline.{json,md}
.somnus-debug/state/reports/20261112T004521Z/production_doctor_report.{json,md}
.somnus-debug/state/reports/latest.{json,md}  .somnus-debug/state/state.sqlite3
$ python3 onboard.py proj --apply
Kept existing (not overwritten): python_doctor.yaml, pycache.yaml, dispositions.json, .gitignore, PROFILE.md   [exit=0]
```

The only change to the repo is the new `.somnus-debug/` directory; its `.gitignore` keeps `state/`, `runs/` and the log out of git [VERIFIED]. What each file holds, and the PROFILE card's shape, are documented in [agent-quickstart](../../10-agent-usage/agent-quickstart.md) and lane F's [generated PROFILE.md copy](../../_evidence/agent-findings/lane-f-ext/logs/s1_PROFILE.md.txt).

## How onboard decides

This section summarizes the algorithm, so its output can be checked.

1. **Survey** (`skills/somnus-debug-fieldkit/scripts/onboard.py:171-216`): Python counts per top-level dir; venvs by `pyvenv.cfg` under any name; `*.egg-info`; git-ignored dirs holding `.py`; `src/<pkg>/__init__.py`; existing `python_doctor.y(a)ml` at the root.
2. **Runner** (`:233-260`): `--python` → project venvs (`.venv`, `venv`, `env`, then any `pyvenv.cfg` dir) that can `import somnus_debug` → `somnus-debug` on PATH → none (exit 3). A src layout adds `PYTHONPATH=<repo>/src`.
3. **Config** (`:276-297`, `:477-479`): adopt the first root `python_doctor.yaml` unless `--new-config`; otherwise generate from the CLI's own `init-config`, forcing `include_patterns: ["*.py"]`, base ignores plus discovered noise, and `state_dir: ".somnus-debug/state"`.
4. **Verify** (`:503-509`): a stateless scan from a temp cwd; exit ≥ 4 or `files == 0` is a coverage failure (exit 2); fewer files than surveyed is a warning.
5. **Baseline** (`:518-522`): a stateful scan from `.somnus-debug/` into `runs/baseline.{md,json}`, only when verify passed.

Exit codes: 0 ok, 1 usage or bad path, 2 coverage failure, 3 no usable somnus-debug (`:50`) [SOURCE-CONFIRMED; 0 and 3 VERIFIED in this wave].

## Pitfalls

This section lists the defects that change what you should do. All are recorded as [D-20](../../DISCOVERY-LEDGER.md#d-20) unless noted.

- **`--python` rejects a normal venv interpreter.** It calls `.resolve()`, which follows `venv/bin/python` to the system interpreter and loses the venv. Executed in this wave: `onboard.py proj --python /tmp/w4/venv/bin/python` → `BLOCKED: no usable somnus-debug. Nothing written.`, exit 3 [VERIFIED, [stage 6 log](../_repro/logs/stage6_integrations.log)]. Put somnus-debug in the project's own `.venv` and let auto-detection find it, or use a `python -m venv --copies` interpreter.
- **A doctor config error crashes onboard** with a traceback and exit 1 rather than the documented exit 2 [VERIFIED by lane F].
- **`--apply` writes `PROFILE.md` even when verification fails**, and the card then records the zero-file verify scan; no baseline is written and nothing says so [VERIFIED by lane F]. Check the `Verify scan:` line yourself.
- **`--baseline` reruns overwrite `runs/baseline.*`.** The no-overwrite rule covers only the five profile files; `run_scan` writes the baseline with `-o` directly (`:518-520`) [SOURCE-CONFIRMED; reconciles lane D's "rerun overwrites the baseline" with lane F's "never overwrites"].
- **An adopted root config can scan zero files.** This repo's own root `python_doctor.yaml` carries Somnus-specific globs and scans 0 files on other trees; pass `--new-config` ([D-02](../../DISCOVERY-LEDGER.md#d-02)) [VERIFIED by lane F].
- **src layout blinds cycle detection** under the generated runner ([D-22](../../DISCOVERY-LEDGER.md#d-22)); see [advanced/src-layout-cycle-check](../advanced/src-layout-cycle-check.md).
- **PROFILE commands are absolute paths.** Regenerate the card after moving the repo or the fieldkit.

## Sources

This section lists the files, logs and evidence this page rests on.

- [stage 2 log](../_repro/logs/stage2_intermediate.log), [stage 6 log](../_repro/logs/stage6_integrations.log)
- [lane-f fieldkit §2](../../_evidence/agent-findings/lane-f-ext/fieldkit.md), [lane-d README](../../_evidence/agent-findings/lane-d-cli-tests/README.md)
- `skills/somnus-debug-fieldkit/scripts/onboard.py:50`, `:171-260`, `:276-297`, `:397-530`; `skills/somnus-debug-fieldkit/references/onboarding.md`
