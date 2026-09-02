# SKILL/somnus-debug.md

**Domain:** Python project diagnostics, structure indexing, cache hygiene, test-harness scaffolding.
**Audience:** any autonomous agent working in a Python repo with `somnus-debug` available (Claude Code, Codex, Kimi, or any future execution engine — this file has no Claude-specific assumptions).
**Authority:** below OPSEC.md in the Somnus layer hierarchy. Nothing here overrides an OPSEC constraint; if they conflict, OPSEC wins.
**Deep reference:** `docs/MANUAL.md` in the [somnus-debug repo](https://github.com/calisweetleaf/somnus-debug) — every flag, every config field, worked examples, troubleshooting. This file is the trigger conditions and cheat sheet; MANUAL.md is the source of truth for exact syntax. When this file and MANUAL.md disagree, MANUAL.md is right (this file goes stale faster).
**Global activation:** `docs/AGENTS_APPENDIX.md` is the canonical pasteable
appendix. Installing a CLI alone does not hydrate agent instructions; an
operator must deliberately place that appendix in the intended global or
repository-local instruction surface.

## What this is

`somnus-debug` is a pip-installable toolkit: `pip install -e .` from the repo
(not yet on public PyPI — see that repo's `docs/PUBLISHING.md` for status).
Four tools behind one CLI: `doctor` (AST-based production-readiness
diagnostics), `structure` (class/definition AST indexer), `pycache-clean`
(bytecode cache removal), `init-test-harness` (scaffolds the CONTRACT.md
single-test harness into a repo).

## When to reach for it (trigger conditions)

- **Before claiming a Python file or project is "done," "production-ready,"
  or "clean"** — run `somnus-debug doctor scan <path>` first. Don't assert
  readiness from a manual read-through when a real AST scan is one command
  away.
- **Before writing a new one-off script to inspect a file's classes/methods**
  (grepping for `def `/`class `, manually counting lines, hand-building an
  outline) — use `somnus-debug structure <file.py>` instead. It's AST-only
  (never imports/executes the target), gives real line spans, and is
  already built and tested. Don't reinvent it.
- **Before writing a new one-off script to find/delete `__pycache__` or
  `.pyc` clutter** — use `somnus-debug pycache-clean` (config-driven, has a
  `--dry-run`) instead of an ad-hoc `find ... -exec rm`.
- **When setting up validation for a new or unfamiliar project** and no
  test harness convention already exists — `somnus-debug init-test-harness`
  scaffolds the CONTRACT.md-governed `run_test.py` pattern rather than
  inventing a new one per project.
- **Do NOT** reach for this toolkit if the target project already has its
  own established linting/test/diagnostic tooling and no one asked for
  this one specifically — this augments Somnus workflows, it doesn't
  replace a project's existing standards uninvited.

## Cheat sheet

```
somnus-debug doctor init-config -o python_doctor.yaml   # first-time setup; edit include_patterns before scanning
somnus-debug doctor scan . -o report.md --json-output report.json
somnus-debug doctor self-check                            # sanity-check the doctor against its own package

somnus-debug structure path/to/file.py                    # print class/def index to stdout
somnus-debug structure path/to/file.py -o INDEX.md         # write it to a file

somnus-debug pycache-clean --config config.yaml --dry-run  # always dry-run first
somnus-debug pycache-clean --config config.yaml            # then actually clean

somnus-debug init-test-harness <target-dir>                # refuses to overwrite an existing hand-edited copy
```

Full flag reference, config file formats, exit codes, troubleshooting:
`docs/MANUAL.md`.

## Known limits, worth knowing before you rely on this

- `pycache-clean` needs a YAML config file (`roots:` is required, no bare
  path fallback) — it will not run against a directory with no config.
- `doctor`'s default `include_patterns` targets `tools/*.py`/`test/*.py`
  (Somnus-repo convention) — point it at the real project's source globs or
  the scan comes back empty.
- If SQLite state cannot initialize on a network, FUSE, or weak-locking
  filesystem, `doctor scan` continues with a warning and writes normal report
  files without `history`/`rollback` state. Use `--no-state` for deliberate
  one-off scans.
- Not yet on public PyPI — `pip install somnus-debug` doesn't work yet;
  it's `git clone` + `pip install -e .` for now.

---

## Addendum block — paste this into a project's `AGENTS.md` or `CLAUDE.md`

Everything below the line is meant to be copied verbatim into another
project's agent-instructions file so any agent working there picks up
`somnus-debug` automatically, without needing this file re-explained each
time.

```markdown
## somnus-debug toolkit

This project has `somnus-debug` available. Before hand-rolling a Python AST inspection
script, a `__pycache__` cleanup script, or asserting a Python file/project is
production-ready without running a real scan — use the toolkit instead:

- `somnus-debug doctor scan <path>` before calling Python code "production
  ready" or "done."
- `somnus-debug structure <file.py>` instead of manually outlining a file's
  classes/methods.
- `somnus-debug pycache-clean --config <cfg> --dry-run` instead of ad-hoc
  find/rm for cache cleanup.

Do not let a green `doctor` scan replace the project's own integration or
release verification. Configure its source globs before the first scan; use
`--no-state` with explicit temporary report paths for disposable diagnostics.
If SQLite state is unavailable, the scan continues statelessly with a warning.

Full reference: `docs/AGENTS_APPENDIX.md`, `SKILL/somnus-debug.md`, and
`docs/MANUAL.md` in that repo.
```
