# somnus-debug — User Manual

**Package:** `somnus-debug` &nbsp;|&nbsp; **Import name:** `somnus_debug` &nbsp;|&nbsp; **Version:** 0.1.0

This is the operating manual for the toolkit that used to be four loose
scripts (`python_production_doctor.py`, `analyze_python_structure.py`,
`pycache_cleaner.py`, `run_test.py`) copied between projects by hand. It's
now one pip-installable package with one CLI. This document is the
day-to-day reference; `docs/CONTRACT.md` and `docs/OPSEC.md` remain the
governing documents for the test-harness contract and agent security
posture respectively, and `docs/Python_Doctor_QUICKSTART.md` is the deep
reference specifically for the doctor's config surface.

**For agents:** `SKILL/somnus-debug.md` is the short trigger-conditions +
cheat-sheet version of this document, meant to be pointed at from a
project's `AGENTS.md`/`CLAUDE.md` so any agent picks up this toolkit
without re-deriving when to use it. This file is the one that's actually
authoritative on exact flags/behavior — when the two disagree, this one is
right; the SKILL file is the one that's expected to occasionally lag.

---

## 1. Install

From the repo root:

```bash
pip install -e .            # editable — code changes take effect immediately
pip install -e ".[dev]"     # editable + pytest, for running tests/
pip install .                # normal, non-editable install
```

Requires Python ≥ 3.10. Runtime dependency: `pyyaml` (needed by
`pycache-clean` only — `doctor` and `structure` are stdlib-only, doctor
ships its own minimal YAML parser).

**If `pip install` can't reach the package index** (proxy/network
restrictions), see [Troubleshooting §7.3](#73-pip-install--e--fails-to-reach-the-package-index).

Once installed, `somnus-debug` is on your PATH inside that environment.
Confirm with:

```bash
somnus-debug --version
somnus-debug --help
```

---

## 2. The unified CLI

Every tool hangs off one dispatcher:

```bash
somnus-debug <command> [command-specific args...]
```

| Command | Purpose |
|---|---|
| `doctor` | AST-based production-readiness diagnostics |
| `structure` | Class/definition index of a single Python file |
| `pycache-clean` | Remove `__pycache__` / `*.pyc` / `*.pyo` across directory trees |
| `init-test-harness` | Scaffold the CONTRACT.md single-test harness into a repo |

Each command owns its **own** `--help` and its own flag surface — the
dispatcher just routes to it unchanged, so anything you knew about the old
standalone scripts still applies. Every command is also installed as its
own script for muscle memory / old CI scripts: `somnus-doctor`,
`somnus-structure`, `somnus-pycache-clean` (init-test-harness has no
standalone alias — it's new).

```bash
somnus-debug doctor --help
somnus-debug structure --help
somnus-debug pycache-clean --help
somnus-debug init-test-harness --help
```

---

## 3. `doctor` — production-readiness diagnostics

Scans Python source with the AST (never imports/executes it) and reports
stubs, placeholder returns, silent exception handling, dependency cycles,
missing docstrings/type hints, TODOs, security-risk patterns, and test
gaps.

### 3.1 First run in a project

```bash
cd /path/to/some/project
somnus-debug doctor init-config -o python_doctor.yaml
```

**Edit `include_patterns` before your first real scan.** The shipped
default targets `tools/*.py` and `test/*.py` (a Somnus-repo convention) —
if your project doesn't have those directory names, the scan will come
back with zero files. Point it at your real source globs, e.g.:

```yaml
include_patterns:
  - "src/**/*.py"
  - "tests/**/*.py"
```

### 3.2 Commands

```bash
somnus-debug doctor scan [project_root] [-c CONFIG] [-o OUTPUT] [--json-output PATH] [--no-state] [-v]
somnus-debug doctor init-config [-o OUTPUT] [--force]
somnus-debug doctor history [project_root] [-c CONFIG] [--limit N]
somnus-debug doctor rollback [project_root] --run-id RUN_ID [-c CONFIG]
somnus-debug doctor self-check [-c CONFIG] [-o OUTPUT] [--json-output PATH] [--no-state]
```

`project_root` defaults to `.` everywhere it appears. A bare path with no
subcommand is also accepted and normalized to `scan`:

```bash
somnus-debug doctor .          # same as: somnus-debug doctor scan .
```

### 3.3 Everyday use

```bash
# Standard scan, markdown + JSON output
somnus-debug doctor scan . -o report.md --json-output report.json

# Verbose, no SQLite state tracking for this one-off run
somnus-debug doctor scan . -v --no-state

# What did the last 5 scans look like?
somnus-debug doctor history . --limit 5

# Restore a previous run's report as "latest" without rescanning
somnus-debug doctor rollback . --run-id 20260901T201813Z

# Sanity-check the doctor against its own package
somnus-debug doctor self-check
```

### 3.4 Exit codes

Gated by `severity_exit_level` in the config (default `"serious"`):

- `0` — scan completed at or below the configured severity gate
- non-zero — gate exceeded, or a runtime failure (check
  `production_doctor.log` in the current working directory)

Set `severity_exit_level: "critical"` to only fail CI on critical issues,
or `"minor"` to fail on anything at all.

### 3.5 State

Unless `--no-state` is passed, each scan writes SQLite-backed state under
`.python_doctor/` in the scanned project root — that's what `history` and
`rollback` read from.

If SQLite cannot initialize (for example, on a filesystem with weak locking
or unsupported WAL behavior), `scan` emits a warning and completes in
stateless mode. The Markdown and JSON reports are still written, but that run
is not available to `history` or `rollback`. Use `--no-state` when this is
intentional and you do not want a fallback warning.

For the full config field reference (severity levels, per-check toggles,
worker count, etc.), see `docs/Python_Doctor_QUICKSTART.md`.

---

## 4. `structure` — class/definition index

Produces a deterministic Markdown index of every class, nested class, and
function (module-level and per-class) in a single Python file, with source
line spans. AST-only — never imports the target file, so it works even on
files with missing/broken runtime dependencies (Torch, CUDA extensions,
etc).

```bash
somnus-debug structure path/to/file.py                       # print to stdout
somnus-debug structure path/to/file.py -o INDEX.md            # write to a file
somnus-debug structure path/to/file.py --update-doc INDEX.md  # regenerate an existing index in place
```

Flags:

| Flag | Effect |
|---|---|
| `-o / --output PATH` | Write the index to PATH instead of stdout |
| `--update-doc PATH` | Same idea, phrased as "regenerate this existing doc" |
| `--no-line-numbers` | Omit source line spans |
| `--source-label NAME` | Override the filename shown in the generated heading |
| `--no-module-functions` | Only emit classes + their methods, skip module-level functions |

Output includes, per class: docstring summary, every method with its
signature, decorators, doc summary, and line span; nested classes render as
sub-sections. A trailing "Module-level functions" section covers anything
outside a class, unless `--no-module-functions` is set.

> Note: this is the tool Daeron's project notes call for expanding with a
> `--both` flag and per-definition line-count stacking — that expansion is
> planned but **not done yet** (see `packaging.md` in project memory for
> status). Today it already does class-then-methods with line spans by
> default; the planned work is a richer combined report, not new base
> functionality.

---

## 5. `pycache-clean` — bytecode cache removal

Deletes `__pycache__` directories and `*.pyc`/`*.pyo` files across one or
more directory trees. **Config-file driven** — there is no way to just
pass a root on the command line, you need a YAML config first.

### 5.1 Config file

```bash
somnus-debug pycache-clean --config config.yaml --dry-run
```

`config.yaml`:

```yaml
roots:
  - /path/to/project/one
  - /path/to/project/two
exclude:
  - "node_modules/*"
  - ".git/*"
targets:
  - "__pycache__"
  - "*.pyc"
  - "*.pyo"
dry_run: true          # CLI --dry-run overrides this to true; omit/false to actually delete
verbose: false
max_depth: null         # null = unlimited; 0 = root only; 1 = one level down; etc.
follow_symlinks: false
log_file: null           # path to also append log output to, or null
```

Unknown keys are logged as warnings and ignored, not fatal.

### 5.2 Flags (override the config for one run)

```bash
somnus-debug pycache-clean --config config.yaml [--dry-run] [--verbose] [--max-depth N] [--follow-symlinks]
```

**Always dry-run before a live run against anything you care about:**

```bash
somnus-debug pycache-clean --config config.yaml --dry-run --verbose
# review the output, then:
somnus-debug pycache-clean --config config.yaml --verbose
```

---

## 6. `init-test-harness` — scaffold the single-test harness

Copies `run_test.py` (and `CONTRACT.md`, unless `--no-contract`) into a
target repository. `run_test.py` is *not* an importable library module —
per `docs/CONTRACT.md` it's meant to be copied into each project and
hand-edited (only `TEST_NAME` and `execute_test()` are project-specific).
Packaging it as an import would break that contract, so this command does
the copying instead.

```bash
somnus-debug init-test-harness path/to/repo
somnus-debug init-test-harness .                 # current directory
somnus-debug init-test-harness . --no-contract    # skip copying CONTRACT.md
somnus-debug init-test-harness . --force          # overwrite an existing run_test.py/CONTRACT.md
```

**Refuses to overwrite silently.** If `run_test.py` or `CONTRACT.md`
already exist at the destination (almost certainly hand-edited per the
contract), it errors out and writes nothing unless you pass `--force`.

---

## 7. Troubleshooting

### 7.1 `doctor scan` finds 0 files

Your `include_patterns` doesn't match this project's real layout. The
shipped default (`tools/*.py`, `test/*.py`) is Somnus-repo-specific, not
universal. Fix it in your `python_doctor.yaml`.

### 7.2 `pycache-clean` errors "No roots specified in configuration"

`roots:` is empty or missing in your config YAML — it's required, there's
no CLI fallback.

### 7.3 `pip install -e .` fails to reach the package index

If your network is proxied/restricted (a 403 from the proxy on
`pypi.org`/`files.pythonhosted.org` is the usual symptom), `pip` can't
fetch the `hatchling` build backend declared in `pyproject.toml`. Options:

- Install from an environment with normal network access (this is how the
  package was originally verified — a full install, wheel build, and
  9-test smoke suite all passed there).
- Get the org's egress allowlist to permit PyPI for this machine, then
  retry.
- If you have `hatchling` cached/available from another install, `pip
  install -e . --no-build-isolation` skips fetching build dependencies and
  uses whatever's already in the current environment.

### 7.4 `git init` / `git commit` stuck on a stale lock

If a previous automated pass left `.git/index.lock` behind (this can
happen when a sandboxed shell isn't allowed to delete files, so a
half-finished `git init` can't clean up after itself), git will refuse to
do anything with:

```
fatal: Unable to create '.../.git/index.lock': File exists.
```

First make sure no Git process is still operating in that repository. Then,
from a real terminal with normal delete permissions, remove only the stale
lock:

```bash
rm .git/index.lock
```

Do not delete `.git` to recover a stale lock; that discards repository state
instead of repairing the interrupted operation.

### 7.5 Old root-level scripts are still there next to `src/`

`python_production_doctor.py`, `analyze_python_structure.py`,
`pycache_cleaner.py`, `run_test.py`, `python_doctor.yaml` at the repo root
are pre-packaging leftovers, kept intentionally until you're ready to
delete them (not auto-removed, to avoid destroying anything before the
package was verified working). Safe to delete once you've confirmed
`src/somnus_debug/` is what you're actually using.

---

## 8. Using it as a library

Every `core.py` is the original single-file implementation, unmodified in
substance — anything importable from the old standalone script is
importable from the packaged module:

```python
from somnus_debug.structure.core import build_index

index_markdown = build_index(
    open("some_module.py").read(),
    source_name="some_module.py",
)

from somnus_debug.doctor.core import ProjectScanner, ConfigManager, DoctorConfig
from somnus_debug.pycache_cleaner.core import PycacheCleaner, CleanerConfig
from somnus_debug.test_harness.scaffold import scaffold  # programmatic init-test-harness
```

---

## 9. Repository layout

```
pyproject.toml              package metadata, deps, entry points
README.md                   short version of this manual
src/somnus_debug/
    cli.py                   `somnus-debug <command>` dispatcher
    doctor/core.py            = old python_production_doctor.py
    doctor/default_config.yaml = old python_doctor.yaml
    structure/core.py         = old analyze_python_structure.py
    pycache_cleaner/core.py   = old pycache_cleaner.py
    test_harness/scaffold.py + templates/{run_test.py, CONTRACT.md}
tests/test_cli_smoke.py      installable-CLI smoke tests (help text, dispatch routing,
                              structure self-index, scaffold + overwrite-refusal)
docs/
    CONTRACT.md               governs run_test.py's artifact contract — SUPREME for that scope
    OPSEC.md                  Somnus agent operational security protocol — SUPREME overall
    Python_Doctor_QUICKSTART.md   full config-field reference for `doctor`
    MANUAL.md                 this file
```

---

*Package created 2026-09-01. See project memory (`packaging.md`) for the
full decision log, verification record, and open items from that build.*
