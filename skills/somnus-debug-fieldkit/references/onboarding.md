---
somnus:
  schema: "somnus://metadata/core/2.0.0"
  id: "urn:somnus:artifact:01a19ace-7663-71ce-a2a6-3338e626ca28"
  revision: 1
  title: "Onboarding: set up somnus-debug in a codebase"
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
      - target_ref: "urn:somnus:artifact:01a19ace-7663-71ce-a2a6-3338e626ca28"
        aspects: ["content"]
  time: {}
  names:
    slug: "onboarding-set-up-somnus-debug-in-a-codebase"
  knowledge:
    coverage: "artifact"
    subjects: ["urn:somnus:artifact:01a19ace-7663-71ce-a2a6-3338e626ca28"]
  access:
    visibility: "internal"
    allowed_uses: ["archive", "search", "reason"]
  ingestion:
    disposition: "candidate"
    body_role: "narrative"
---
# Onboarding: set up somnus-debug in a codebase

Use this when a repository has no `.somnus-debug/PROFILE.md`, or when the user asks to set up, onboard, or wire in somnus-debug. The goal is a project-local profile that any later agent can operate from without rediscovering anything.

## Onboarded means

A repository is onboarded when all nine of these hold.

1. A doctor config (`.somnus-debug/python_doctor.yaml`, or an adopted existing one) scans the repo's real Python, with `files=` greater than 0.
2. A **runner** is chosen: the project venv's `python -m somnus_debug.cli` when it has somnus-debug, otherwise `somnus-debug` on PATH. A `src/` layout needs nothing extra: doctor resolves the project's own packages under `src/` natively, and onboard exports no `PYTHONPATH`.
3. Doctor state lives in `.somnus-debug/state/` (via `state_dir`), not in a stray root `.python_doctor/`.
4. `.somnus-debug/pycache.yaml` has absolute roots and name-based excludes, with `dry_run: true`.
5. `.somnus-debug/dispositions.json` exists (initially `[]`) for reviewed false positives.
6. `.somnus-debug/PROFILE.md` records the runner, coverage, the exact loop commands, and the verification scan.
7. `.somnus-debug/.gitignore` excludes `state/`, `runs/`, and logs. Configs, dispositions, and the profile are tracked.
8. A stateful baseline exists at `.somnus-debug/runs/baseline.{md,json}`.
9. The repo's agent instructions carry the block from `templates/AGENTS_APPENDIX.md`.

## Procedure

Run plan mode first, read it, then apply.

```console
somnus-debug --version || <venv>/bin/python -m somnus_debug.cli --version
python3 <skill-dir>/scripts/onboard.py <repo>                       # plan: survey, runner, coverage proof; writes nothing
python3 <skill-dir>/scripts/onboard.py <repo> --apply --baseline    # write profile, prove coverage, baseline
```

Plan mode writes nothing; its git checks are read-only and never refresh `.git/index`.

Exit codes:

| Code | Meaning |
|---|---|
| `0` | ok |
| `1` | usage error, bad repo path, or `--baseline` refused because `runs/baseline.{md,json}` exists (pass `--force-baseline` to re-record it) |
| `2` | coverage failure: zero files scanned, or a doctor or config error (printed as one `error:` line). With `--apply`, no `PROFILE.md` is written and `--baseline` reports `Baseline skipped` |
| `3` | no usable somnus-debug, including a `--python` path that does not exist (nothing written) |

`--python` keeps a venv interpreter's symlink, so `<venv>/bin/python` runs with that venv's packages. A baseline is recorded when the verification scan covers files and doctor runs, even if doctor exits `1` or `2`: findings are what a baseline records.

1. **Read the runner notes.** "Project environment lacks somnus-debug" means doctor will see the wrong dependencies. Recommend `<venv>/bin/python -m pip install somnus-debug` (ask first; it's the user's env), then rerun. Force a specific interpreter with `--python`.
2. **Read the coverage.** Check the per-directory counts and the noise list (venvs found by `pyvenv.cfg`, `*.egg-info`, git-ignored directories that contain Python). For uncaught vendored, generated, or fixture code, add `"<dir>/*"` to `ignore_patterns` and rerun plan mode.
3. **Existing root config.** onboard adopts it and scans with it. `FAIL: zero files scanned` means its globs don't fit this tree. Either fix it deliberately with the user's agreement, or pass `--new-config` and leave the old file alone. Never silently rewrite a root config.
4. **Read the baseline report**, not just its exit code. Exit 1 on an early repo is normal: stubs and placeholders are serious by default. Pre-disposition obvious false positives (abstract-method stubs, property setters, safe subprocess calls) using [findings](findings.md).
5. **Append the AGENTS block** to the repo's instructions through the configured editor, preserving what's already there.
6. **Don't** add CI, pre-commit, watchers, or a test harness during onboarding. Those are separate opt-ins.

onboard never overwrites a file, except `runs/baseline.{md,json}` when `--force-baseline` is given. To regenerate any other file, delete or edit it deliberately.

## Manual setup (if the script can't run)

These steps build the same profile by hand.

1. `mkdir -p .somnus-debug/runs`; from a temp dir, run `sd doctor init-config -o <repo>/.somnus-debug/python_doctor.yaml`.
2. Keep `include_patterns: ["*.py"]`; add repo-specific `ignore_patterns` and `".somnus-debug/*"`; set `state_dir: ".somnus-debug/state"`.
3. Write `pycache.yaml`, `dispositions.json` (`[]`), and `.gitignore` as described above.
4. `cd .somnus-debug && sd doctor scan .. -c python_doctor.yaml -o runs/baseline.md --json-output runs/baseline.json`; confirm `files=` > 0.
5. Write `PROFILE.md` with the runner, coverage, and commands.

## Pattern semantics (0.1.0 source)

These matching rules decide what a scan and a cleanup cover.

- Doctor matches `fnmatch` against both the repo-relative POSIX path and the bare filename. `*` crosses `/`: `src/*.py` matches `src/a/b/c.py`, and `*.py` matches every Python file. A `**/` segment also matches zero directories, so `src/**/*.py` includes files directly under `src/`. An empty `include_patterns` list is a configuration error (exit `4`).
- An ignore pattern ending in `/*` also prunes any directory with that **name** at any depth: `build/*` ignores `src/pkg/build/` too. Use a longer relative path (`src/pkg/build/*`) when a nested match is wrong.
- `pycache-clean` `exclude` entries match a directory's **name** or its path relative to the root: `node_modules` skips that name at any depth, `node_modules/*` only `<root>/node_modules`. Relative `roots` resolve against the caller's cwd, not the config file; `~` and `$VAR` are expanded.

## After onboarding

Every later session: read `PROFILE.md`, then follow [doctor-loop.md](doctor-loop.md). When the tree changes shape, rerun `onboard.py <repo>` in plan mode.
