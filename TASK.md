# TASK: somnus-debug discovery fixes

This is the work list built from every discovery (D-01 to D-34) in `wiki/DISCOVERY-LEDGER.md`. Each task is either already in the patch (`somnus-debug-discovery-fixes.patch`), waiting on an operator decision, or recorded as a note with no code change. Code is the authority. When this list and the code disagree, the code wins, and this file gets fixed.

## Apply the patch

This section is the command sequence for the operator machine. The patch is a squashed diff against the upload baseline (the tree of the somnus-debug zip delivered on 2026-11-11, git baseline `034f46e` in the forge copy). Apply it on that same tree.

```bash
cd somnus-debug                      # the checkout the zip came from
git switch -c forge/2026-11-11-discovery-fixes
git apply --check somnus-debug-discovery-fixes.patch   # dry run; must print nothing
git apply --index somnus-debug-discovery-fixes.patch
python -m pytest -q                  # expect: 163 passed (3.10: 162 passed, 1 skipped)
python skills/somnus-debug-fieldkit/scripts/selftest.py --python "$(command -v python)"   # expect 30/30
git commit -m "Apply discovery fixes T-01..T-40 (see TASK.md)"
```

If `git apply --check` rejects a hunk, the local tree has drifted from the zip. Try `git apply --3way` first, then read the rejected file against the hunk by hand. The patch carries `wiki/`, `TASK.md`, code, tests, and docs together. It does not touch the root duplicate scripts.

## Patch workflow for agents

This section is the read, improve, rewrite loop any agent follows so the patch file stays the single handoff artifact.

1. Read `TASK.md`, then apply the current patch to a clean baseline tree on a scratch branch (commands above).
2. Pick one open task (status `OPEN` or `DECISION` once decided). Work only on the files that task names.
3. Add a regression test that fails before the change and passes after. Run the full suite from a directory outside the repo with `PYTHONDONTWRITEBYTECODE=1`, because doctor writes `production_doctor.log` into the current directory.
4. Commit one task per commit: `T-NN (D-XX): what changed`, with the proving command and result in the body.
5. Regenerate the patch against the baseline and overwrite the file:
   `git diff --binary 034f46e HEAD -- . > somnus-debug-discovery-fixes.patch`
   (on the operator machine, replace `034f46e` with the commit that holds the untouched zip tree).
6. Update this file: flip the task status, add the commit subject, and record any new discovery as a new task with its evidence.
7. Do not delete `__pycache__/` or logs that are not yours. Leave the tree clean before regenerating.

## Status legend

This section defines the four states a task can be in.

| Status | Meaning |
| --- | --- |
| DONE | Fixed in the patch, with a regression test, full suite green |
| DECISION | Needs the operator's call before code; options listed |
| OPEN | Agreed work not in the patch yet |
| NOTE | Documented behavior or positive finding; no code change planned |

## Verification at patch time

This section records what was proved when the patch was cut, so the next agent can confirm nothing regressed.

- Full suite: 163 passed on Python 3.11.17, 3.12.15 and 3.13; 162 passed with 1 skipped on 3.10.22 (the `tomllib` check skips there). Baseline was 10 passed, 2 failed.
- New tests: `tests/test_doctor_fixes.py`, `tests/test_tools_fixes.py`, `tests/test_fieldkit_fixes.py`. Every new test was run against the unfixed code first and failed, apart from a handful of guard checks that pin unchanged behavior.
- Fieldkit selftest: 30/30 (baseline 29/29 against old expectations; five checks were flipped to the fixed behavior and one added).
- `src/` scanned with old vs patched doctor: 130 to 107 issues, from detector precision fixes only.
- Not run: Windows, Python below 3.10, a live pycache-clean with a scalar root, GitHub rendering, comparison with the canonical remote `calisweetleaf/somnus-debug` master.

## Doctor core

This section covers `src/somnus_debug/doctor/core.py` and its tests.

| Task | Discovery | Status | Change |
| --- | --- | --- | --- |
| T-01 | D-29 | DONE | Missing or non-directory root exits 4 before any state is created. history on a never-scanned root prints "No recorded runs found." and exits 0; rollback exits 4; neither creates `.python_doctor/`. |
| T-02 | D-03 | DONE | Unquoted `none`, `null`, `~` for `severity_exit_level` mean the `none` gate. |
| T-03 | D-04 | DONE | Parser: `#` comments only at line start or after whitespace and never in quotes; flow lists split outside quotes; `''` escape; `{}` is an empty mapping; quoted keys; BOM stripped; leading-zero ints such as `010` stay strings. Unknown keys and severity categories warn on stderr with the closest valid key. |
| T-04 | D-06, D-22 | DONE | `from X import name` tries submodule `X.name` before `X/__init__.py`; a name that is neither is a missing import. Modules under `<root>/src` resolve without the `src.` prefix, so src-layout cycles show regardless of PYTHONPATH. |
| T-05 | D-07 | DONE | silent_failures accepts any logger-like receiver; stubs skip abstractmethod, overload and Protocol bodies; duplicates skip property setter/deleter and overload groups; `@dataclass(...)` call form recognised; `__future__` and `__all__` names never unused; placeholder returns compare by type (`return 1` is not `True`); private-function findings name the function. |
| T-06 | D-08, D-32 | DONE | Run id collisions get `-1`, `-2`; the report directory is the claim, so parallel scans cannot share an id. |
| T-07 | D-18 | DONE | Critical findings exit 2 under every gate except `none`; uncaught exceptions exit 5 with the traceback in the log only; serial-path analyzer errors become `analysis_read_errors` findings. |
| T-08 | D-16, D-30 | DONE | `security_risks` still reported inside `ignore_functions` and skipped nested functions; other categories stay suppressed. |
| T-09 | D-17 | DONE | Empty `include_patterns` exits 4; `dir/**/*.py` also matches files directly in `dir`. |
| T-10 | D-25 | DONE | `-o report.json` writes `report.json` and `report.md`; identical `-o` and `--json-output` paths exit 4 before scanning. |
| T-11 | D-28 | DONE | No code change: history and rollback on an unusable state DB already exit 4. Pinned by `test_history_with_unusable_state_db_exits_4`. |
| T-12 | D-34 | DONE | `ConfigManager.replace(**changes)` validates and recomputes `config_hash`. |
| T-13 | D-10 | DONE | Smoke tests run outside the repo, so the suite no longer drops `production_doctor.log` into the checkout. The doctor behavior itself is D-10 under Decisions. |
| T-14 | D-32 | OPEN | Two scans starting at once on a brand-new state DB can still drop one to stateless mode with a warning. Fix: create the schema with `BEGIN IMMEDIATE` and retry on `database is locked`. |

## Structure, pycache-clean, dispatcher, harness

This section covers the remaining packaged tools and the `somnus-debug` dispatcher.

| Task | Discovery | Status | Change |
| --- | --- | --- | --- |
| T-20 | D-01 | DONE | `structure/core.py` drops `type_comments=True`; metadata-stamped files parse. The two failing smoke tests pass. |
| T-21 | D-24 | DONE | A class in a class in a function renders and counts once. |
| T-22 | D-34 | DONE | Undecodable source exits 2 with one line, no traceback. |
| T-23 | D-14, D-31, D-34 | DONE | pycache-clean validates types: `roots` must be a list (a scalar no longer iterates characters toward `/`), booleans must be booleans, `max_depth` an int >= 0; unknown keys warn after logging is configured; `~` and `$VARS` expand in roots. New `ConfigError`, `CleanerConfig.load()`, `CleanerConfig.validate()`. |
| T-24 | D-14 | DONE | `exclude` matches the directory name or its root-relative path. |
| T-25 | D-14 | DONE | Dry run says "would remove"; a missing root makes the run exit 1; the unimplemented Windows long-path claim and the invalid escape are gone. |
| T-26 | D-13 | DONE | Dispatcher imports tools lazily; only pycache-clean needs PyYAML and says so cleanly. New `somnus-init-test-harness` console script. |
| T-27 | D-23 | DONE | `__version__` comes from distribution metadata, with "0.1.0" as the source-tree fallback. |
| T-28 | D-15, D-34 | DONE | Harness template infers the project root (`PROJECT_ROOT`, else nearest `.git`/`pyproject.toml`/`setup.cfg`), runs pytest when the project has tests or compileall otherwise, handles `--help`, and resolves relative output dirs against the root. The manifest contract is unchanged. |
| T-29 | D-15 | DONE | `init-test-harness --help` states the default destination and root inference. |
| T-37 | D-34 | OPEN | `PycacheCleaner.run()` adds a stderr handler when the host process has no logging configured. Library callers should get no handler. |
| T-38 | D-31 | DECISION | `targets` lets pycache-clean delete any named directory. Options: (a) keep and document, (b) restrict to cache-like names unless `--allow-any-target`, (c) remove `targets`. |

## Fieldkit

This section covers `skills/somnus-debug-fieldkit/scripts/`.

| Task | Discovery | Status | Change |
| --- | --- | --- | --- |
| T-30 | D-20 | DONE | `onboard --python` keeps venv symlinks; a missing interpreter exits 3 cleanly. |
| T-31 | D-20 | DONE | A broken doctor config during onboarding exits 2 with one line. |
| T-32 | D-20 | DONE | `--apply` writes no `PROFILE.md` without a passing, non-empty scan; plan mode uses read-only git and never rewrites `.git/index`. |
| T-33 | D-34 | DONE | `--baseline` refuses to overwrite `runs/baseline.*` without `--force-baseline`. |
| T-34 | D-21 | DONE | `delta.py` compares `config_hash` (exit 3 unless `--allow-config-change`); broad glob dispositions excuse only persisting findings, never new ones; usage errors and malformed reports exit 3. |
| T-35 | D-22 | DONE | Onboard stops exporting `PYTHONPATH=src`; the profile records that doctor handles src layout natively. |
| T-36 | selftest | DONE | Selftest checks updated to the fixed behavior; relative `--python` works; metadata-stamped structure check added; the pycache exclude check is renamed to what it now proves (root-anchored path pattern). 30 checks. |

## Documentation

This section covers public docs and the wiki.

| Task | Discovery | Status | Change |
| --- | --- | --- | --- |
| T-40 | all | DONE | README, MANUAL, QUICKSTART, CONTRACT, AGENTS_APPENDIX and fieldkit references synced with the patched behavior; dead links fixed; open items stated honestly. |
| T-41 | ledger | DONE | `wiki/DISCOVERY-LEDGER.md` carries a resolution line per discovery pointing at its task. The rest of the wiki still describes 0.1.0 as uploaded, which is its job. |
| T-43 | fieldkit | OPEN | `skills/somnus-debug-fieldkit/SKILL.md` frontmatter description still says "29-check"; the body and selftest say 30. Left because the header block was held byte-identical. |
| T-42 | H-10 | OPEN | Archive the W1 example runs under `wiki/_evidence/` to close review item H-10. |

## Decisions

This section lists what needs the operator's call before any code. Each has the options found during the archaeology.

| Task | Discovery | Question | Options |
| --- | --- | --- | --- |
| T-50 | D-02 | Should doctor auto-load a config? | (a) keep explicit `-c` only, documented (current); (b) auto-load `<root>/python_doctor.yaml` when present, with `--no-config` to opt out. |
| T-51 | D-05 | `test_gaps` is configured but never emitted. | (a) implement the detector; (b) remove the key and category. |
| T-52 | D-09 | Rollback moves only the `latest` alias. | (a) document as alias-only (current); (b) also restore project-root reports from the chosen run. |
| T-53 | D-10, D-11 | Implicit writes and logging takeover. | (a) keep; (b) log under `.python_doctor/` or the user state dir, write nothing to cwd, and configure logging only on the CLI path without `force=True`; self-check writes to a temp dir. |
| T-54 | D-12, D-33, D-19 | Public embedding and extension API. | (a) keep internal; (b) declare `ProjectScanner`/`ConfigManager` public and add a detector registration hook. |
| T-55 | D-17 | Default ignore list skips any `env`, `build`, `venv` dir at any depth. | (a) keep; (b) anchor to the root (`/env/` only). |
| T-56 | D-18 | argparse usage errors exit 2, same as the critical gate. | (a) keep; (b) map usage errors to 4. |
| T-57 | D-23 | Root duplicate scripts (`python_production_doctor.py`, `analyze_python_structure.py`, `pycache_cleaner.py`, `run_test.py`, `python_doctor.yaml`) drift from `src/`. | (a) delete them; (b) turn each into a thin shim over `src/`. |
| T-58 | D-23 | Release. | Bump to 0.1.1 and republish once decisions land; PyPI 0.1.0 still ships D-01. |
| T-59 | D-14 | pycache-clean relative roots resolve against cwd. | (a) keep (current, pinned by a test); (b) resolve against the config file's directory. |

## Notes

This section lists discoveries that need no code change.

| Discovery | Note |
| --- | --- |
| D-12, D-33 | Side-effect-free embedding via `ProjectScanner(Path(root), ConfigManager(None)).scan({})`; library JSON equals CLI JSON apart from run id and timestamps. |
| D-26 | `missing_imports` depends on the interpreter and cwd; T-04 removes the src-layout half. Run doctor with the project's own interpreter. |
| D-27 | Verified compositions (doctor JSON to delta gate, structure slices, ratchet); recipes in `wiki/09-recipes/`. |
| D-34 | Thread pool gave no speedup on 68 files with 2 CPUs (1.05 s serial vs 1.21 s with 4 workers). Measure on real hardware before tuning `max_workers`. |
