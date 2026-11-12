---
somnus:
  schema: "somnus://metadata/core/2.0.0"
  id: "urn:somnus:artifact:01a19ace-7471-713d-ba68-ce04569536af"
  revision: 1
  title: "somnus-debug — User Manual"
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
      - target_ref: "urn:somnus:artifact:01a19ace-7471-713d-ba68-ce04569536af"
        aspects: ["content"]
  time: {}
  names:
    slug: "somnus-debug-user-manual"
  knowledge:
    coverage: "artifact"
    subjects: ["urn:somnus:artifact:01a19ace-7471-713d-ba68-ce04569536af"]
  access:
    visibility: "internal"
    allowed_uses: ["archive", "search", "reason"]
  ingestion:
    disposition: "candidate"
    body_role: "narrative"
---
# somnus-debug — User Manual

**Package:** `somnus-debug` &nbsp;|&nbsp; **Import name:** `somnus_debug` &nbsp;|&nbsp; **Version:** 0.1.0

This is the operating manual for the toolkit that used to be four loose
scripts (`python_production_doctor.py`, `analyze_python_structure.py`,
`pycache_cleaner.py`, `run_test.py`) copied between projects by hand. It's
now one pip-installable package with one CLI. This document is the
day-to-day reference; `docs/CONTRACT.md` remains the governing document for
the test-harness contract, and `docs/Python_Doctor_QUICKSTART.md` is the deep
reference specifically for the doctor's config surface.

**For agents:** the complete routed skill package is [`skills/somnus-debug-fieldkit/SKILL.md`](../skills/somnus-debug-fieldkit/SKILL.md); its references contain the repeated diagnose–repair–rescan protocol, onboarding guidance, and harness integration. This manual is authoritative for exact CLI flags and behavior; the installed command's own `--help` remains the first check when versions differ.

---

## 1. Install

This section installs the package and confirms the command answers.

From the repo root:

```bash
pip install -e .            # editable — code changes take effect immediately
pip install -e ".[dev]"     # editable + pytest, for running tests/
pip install .                # normal, non-editable install
```

Requires Python ≥ 3.10. Runtime dependency: `pyyaml` (needed by
`pycache-clean` only — `doctor`, `structure`, and `init-test-harness` are
stdlib-only, doctor ships its own minimal YAML parser). The dispatcher loads
only the tool you run, so those three work even when PyYAML is missing;
`somnus-debug pycache-clean` then prints one line naming the missing
dependency and exits `1`.

**If `pip install` can't reach the package index** (proxy/network
restrictions), see [Troubleshooting §7.3](#73-pip-install--e--fails-to-reach-the-package-index).

Once installed, `somnus-debug` is on your PATH inside that environment.
Confirm with:

```bash
somnus-debug --version
somnus-debug --help
```

`--version` reports the installed distribution's version. Run from a source
tree with no installed distribution (`PYTHONPATH=src`), it falls back to
`0.1.0`.

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
`somnus-structure`, `somnus-pycache-clean`, and `somnus-init-test-harness`.

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
missing docstrings/type hints, TODOs, and security-risk patterns.

Test gaps are not reported. `detect_test_gaps` and a `test_gaps` severity
exist in the configuration and are validated, but no code emits the
category, so a clean scan says nothing about test coverage.

`from pkg import name` resolves to the submodule `pkg/name.py` when one
exists, so cycles and missing modules written that way are found. In a `src/`
layout, the project's own packages under `src/` resolve locally without
`PYTHONPATH`. Security-risk calls are still reported inside functions the
config skips (`ignore_functions`, or nested functions when
`check_nested_functions` is false); every other category stays suppressed
there.

### 3.1 First run in a project

```bash
cd /path/to/some/project
somnus-debug doctor init-config -o python_doctor.yaml
```

**Review coverage before your first real scan.** The generated default
includes every `*.py` under the project root (fnmatch `*` crosses `/`),
minus standard ignores: VCS, caches, virtualenvs, `node_modules`, `build`,
and `dist`. Add `ignore_patterns` for vendored, generated, or fixture code,
or narrow `include_patterns` to your real source globs, e.g.:

```yaml
include_patterns:
  - "src/**/*.py"
  - "tests/**/*.py"
```

A `**/` segment matches zero or more directories, so `src/**/*.py` also
matches files directly under `src/`. An empty list (`include_patterns: []`) is a configuration
error and exits `4`.

**The doctor never loads a config file on its own.** Without `-c`, every
command uses the built-in defaults, even when `python_doctor.yaml` sits in
the project root. Pass `-c python_doctor.yaml` on every `scan`, `history`,
and `rollback`.

The bundled YAML reader handles plain `key: value` pairs, quoted scalars,
one-level lists, flow lists, and `{}`. Unknown top-level keys and unknown
`severity_levels` categories are reported on stderr with the closest valid
key (for example `detect_silent_failure` suggests `detect_silent_failures`)
and are otherwise ignored. Integers must be plain decimals: a leading-zero
value such as `010` stays a string and fails validation with exit `4`.
### 3.2 Commands

```bash
somnus-debug doctor scan [project_root] [-c CONFIG] [-o OUTPUT] [--json-output PATH] [--no-state] [-v]
somnus-debug doctor init-config [-o OUTPUT] [--force]
somnus-debug doctor history [project_root] [-c CONFIG] [--limit N]
somnus-debug doctor rollback [project_root] --run-id RUN_ID [-c CONFIG]
somnus-debug doctor self-check [-c CONFIG] [-o OUTPUT] [--json-output PATH] [--no-state]
```

`project_root` defaults to `.` everywhere it appears. It must be an existing
directory: a missing path, or a file, exits `4` and creates nothing. `history`
and `rollback` on a directory that was never scanned create nothing either;
`history` prints `No recorded runs found.` and `rollback` exits `4`.

A bare path with no subcommand is also accepted and normalized to `scan`:

```bash
somnus-debug doctor .          # same as: somnus-debug doctor scan .
```

### 3.3 Everyday use

```bash
# Standard scan with the project's config, markdown + JSON output
somnus-debug doctor scan . -c python_doctor.yaml -o report.md --json-output report.json

# Verbose, no SQLite state tracking for this one-off run
somnus-debug doctor scan . -v --no-state

# What did the last 5 scans look like?
somnus-debug doctor history . --limit 5

# Restore a previous run's report as "latest" without rescanning
somnus-debug doctor rollback . --run-id 20260901T201813Z

# Sanity-check the doctor against its own package
somnus-debug doctor self-check
```

Both reports are always written. Without `-o` they go to
`<project_root>/production_doctor_report.md` and `.json`. With `-o` and no
`--json-output`, JSON goes next to the markdown with a `.json` suffix; when
`-o` itself ends in `.json`, that path receives the JSON and the markdown
goes to the same stem with `.md`. Giving `-o` and `--json-output` the same
path exits `4` before scanning.

### 3.4 Exit codes

Gated by `severity_exit_level` in the config (default `"serious"`):

| Code | Meaning |
|---|---|
| `0` | No finding at or above the gate (always `0` under the `none` gate) |
| `1` | A non-critical finding at or above the gate |
| `2` | A critical finding, under every gate except `none`; also an argparse usage error |
| `4` | Configuration or doctor error (bad config, missing root, unknown run ID, unusable state database) |
| `5` | Any other runtime failure; the traceback goes to `production_doctor.log` in the current working directory |

Gate values: `"critical"` fails only on critical findings; `"serious"` on
serious or critical; `"minor"` adds minor findings; `"info"` adds info
findings; `none` never fails on findings. `none` works quoted or unquoted, and
`null` and `~` mean the same. A file the analyzer fails on is reported as an
`analysis_read_errors` finding (critical), not a crash. A zero-file scan
exits `0`; check `files=` in the summary line.

### 3.5 State

Unless `--no-state` is passed, each scan writes SQLite-backed state under
`.python_doctor/` in the scanned project root — that's what `history` and
`rollback` read from.

Run IDs are UTC timestamps (`20260901T201813Z`). A second scan in the same
second against the same state gets `-1`, the next `-2`, and so on, so no run
overwrites another in history.

`rollback` repoints the `latest` alias and rewrites
`.python_doctor/reports/latest.{md,json}`; the next scan's state delta is
computed against that run. It does not touch the `-o` or project-root
reports, and it never changes source files.

Every doctor invocation, including `--help`, appends to
`production_doctor.log` in the current working directory. Run the doctor from
a directory where that file is welcome.

If SQLite cannot initialize (for example, on a filesystem with weak locking
or unsupported WAL behavior), `scan` emits a warning and completes in
stateless mode. The Markdown and JSON reports are still written, but that run
is not available to `history` or `rollback`. Use `--no-state` when this is
intentional and you do not want a fallback warning.

For the full config field reference (severity levels, per-check toggles,
worker count, etc.), see `docs/Python_Doctor_QUICKSTART.md`.

---

## 4. `structure` — class/definition index

This section covers the one-file AST index.

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

`-o` and `--update-doc` write the file and print nothing. Comments that look
like type comments (such as Somnus metadata headers) are fine. A file that is
not valid UTF-8, or does not parse, exits `2` with a one-line `error:`
message.

> Note: this is the tool Daeron's project notes call for expanding with a
> `--both` flag and per-definition line-count stacking — that expansion is
> planned but **not done yet** (see `packaging.md` in project memory for
> status). Today it already does class-then-methods with line spans by
> default; the planned work is a richer combined report, not new base
> functionality.

---

## 5. `pycache-clean` — bytecode cache removal

This section covers the only command that deletes files.

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

Each `exclude` pattern is matched (case-sensitive `fnmatch`) against a
directory's name and against its path relative to the scanned root, so
`node_modules/*` skips `<root>/node_modules` and a bare `node_modules` skips
that name at any depth.

Values are type-checked before anything runs: `roots`, `exclude`, and
`targets` must be lists of strings (a scalar `roots: /path` is rejected),
`dry_run`, `verbose`, and `follow_symlinks` must be real booleans (`"false"`
is rejected), and `max_depth` must be a non-negative integer or `null`. A
rejected config exits `1`. `roots` and `log_file` expand `~` and `$VAR` /
`${VAR}`; relative roots resolve against the current working directory, not
the config file's directory. Without `--config`, the CLI reads
`./config.yaml`.

### 5.2 Flags (override the config for one run)

```bash
somnus-debug pycache-clean --config config.yaml [--dry-run] [--verbose] [--max-depth N] [--follow-symlinks]
```

A dry run ends with
`Summary: would delete N directories, M files; would free X MiB`; a live run
ends with `Summary: deleted ...; freed ...`. With `--verbose`, each match is
logged as `Would remove ...` or `Removed ...`. A root that does not exist or is not a
directory is logged as an error, the other roots are still processed, and
the run exits `1`. A negative `--max-depth` is a usage error (exit `2`).

**Always dry-run before a live run against anything you care about:**

```bash
somnus-debug pycache-clean --config config.yaml --dry-run --verbose
# review the output, then:
somnus-debug pycache-clean --config config.yaml --verbose
```

---

## 6. `init-test-harness` — scaffold the single-test harness

This section covers copying the single-test harness into a project.

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

The repository root and any subdirectory both work. The copied `run_test.py`
finds its project root at run time: `$PROJECT_ROOT` if set, otherwise the
nearest directory at or above `run_test.py` containing `.git`,
`pyproject.toml`, or `setup.cfg`, otherwise its own directory. Artifacts go
to `<project root>/test-runs/<run id>/`, or under `$SINGLE_TEST_OUTPUT_DIR`
(relative values resolve against the project root). The shipped
`execute_test()` is a generic starting point: it runs `python -m pytest -q`
when the project has a pytest suite and `python -m compileall -q` otherwise.
`python run_test.py --help` prints these settings without running the test.
See `docs/CONTRACT.md` for the full contract.

---

## 7. Troubleshooting

These are the failures operators meet most often, with their fixes.

### 7.1 `doctor scan` finds 0 files

Your `include_patterns` doesn't match this project's real layout, or an
`ignore_patterns` entry prunes it. The generated default (`*.py`) matches
every Python file, so zero files usually means a copied config with
Somnus-style globs such as `tools/*.py` and `test/*.py`. This repository's
root-level `python_doctor.yaml` is one of those pre-packaging leftovers (see
7.5); it is not the package default. A zero-file scan exits `0`, so check
`files=` in the summary line. Fix it in your `python_doctor.yaml`, and pass
that file with `-c`: the doctor does not load it on its own.

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
package was verified working). They do not receive the fixes made in
`src/somnus_debug/`, so their behavior differs from the installed commands.
Safe to delete once you've confirmed `src/somnus_debug/` is what you're
actually using.

---

## 8. Using it as a library

Every `core.py` started as the original single-file implementation and has
since been fixed in place; the public names of the old standalone scripts
are importable from the packaged modules:

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

To change a loaded doctor configuration, call
`ConfigManager.replace(**changes)`. Each keyword names a `DoctorConfig`
field; the result is validated like a config file and `config_hash` is
recomputed. An unknown field or invalid value raises `ConfigurationError`
and leaves the manager unchanged. Assigning `ConfigManager.config` directly
skips validation.

---

## 9. Repository layout

The package source, tests, and docs sit in three top-level directories.

```
pyproject.toml              package metadata, deps, entry points
README.md                   short version of this manual
src/somnus_debug/
    cli.py                   `somnus-debug <command>` dispatcher
    doctor/core.py            = old python_production_doctor.py
    doctor/default_config.yaml = reference copy of `doctor init-config` output (test-enforced)
    structure/core.py         = old analyze_python_structure.py
    pycache_cleaner/core.py   = old pycache_cleaner.py
    test_harness/scaffold.py + templates/{run_test.py, CONTRACT.md}
tests/                      pytest suite: installable-CLI smoke tests (help text,
                              dispatch routing, structure self-index, scaffold +
                              overwrite-refusal) and per-tool regression tests
docs/
    CONTRACT.md               governs run_test.py's artifact contract — SUPREME for that scope
    Python_Doctor_QUICKSTART.md   full config-field reference for `doctor`
    MANUAL.md                 this file
```

---

*Package created 2026-09-01. See project memory (`packaging.md`) for the
full decision log, verification record, and open items from that build.*
