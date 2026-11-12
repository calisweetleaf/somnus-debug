---
somnus:
  schema: "somnus://metadata/core/2.0.0"
  id: "urn:somnus:artifact:01a19ace-7516-720e-9b22-b9e633d115cb"
  revision: 1
  title: "Python Production Doctor - Quick Start Guide"
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
      - target_ref: "urn:somnus:artifact:01a19ace-7516-720e-9b22-b9e633d115cb"
        aspects: ["content"]
  time: {}
  names:
    slug: "python-production-doctor-quick-start-guide"
  knowledge:
    coverage: "artifact"
    subjects: ["urn:somnus:artifact:01a19ace-7516-720e-9b22-b9e633d115cb"]
  access:
    visibility: "internal"
    allowed_uses: ["archive", "search", "reason"]
  ingestion:
    disposition: "candidate"
    body_role: "narrative"
---
# Python Production Doctor - Quick Start Guide

> This file was out of date: it described a `DOCTOR_CONFIG.json` config and a
> flat `-c/-o/-f/-j` flag set that predates the current tool. The doctor now
> takes YAML config (`python_doctor.yaml`) and a subcommand interface
> (`scan`, `init-config`, `history`, `rollback`, `self-check`). Rewritten
> below to match `src/somnus_debug/doctor/core.py` as of the pip-package
> migration.

## Setup

Zero *pip* dependencies for the doctor itself -- it ships its own minimal
YAML parser, so `python python_production_doctor.py ...` never needed
anything beyond the standard library. Installed as part of `somnus-debug`,
it's reachable as:

```bash
somnus-debug doctor <command> [args...]
# or, standalone:
somnus-doctor <command> [args...]
```

(Note: `somnus-debug` as a whole *does* declare a dependency on PyYAML, but
that's for the `pycache-clean` tool, not the doctor. The dispatcher loads
only the tool you run, so `somnus-debug doctor` works without PyYAML.)

## Configuration: `python_doctor.yaml`

Generate a starting config in your project root:

```bash
somnus-debug doctor init-config -o python_doctor.yaml
```

The doctor never loads this file on its own. Without `-c`, every command
uses the built-in defaults, even when `python_doctor.yaml` sits in the
project root, so pass `-c python_doctor.yaml` on every `scan`, `history`, and
`rollback`.

Key fields (the generated file has the full set, without comments):

```yaml
schema_version: "3.0"
min_function_lines: 5
min_class_lines: 6
min_docstring_length: 18
max_cyclomatic_complexity: 12
include_patterns:
  - "*.py"
ignore_patterns:
  - "__pycache__/*"
  - "*.pyc"
  - ".git/*"
  - ".venv/*"
  - "node_modules/*"
  - ".python_doctor/*"
  - "build/*"
  - "dist/*"
ignore_functions:
  - "__repr__"
  - "__str__"
require_module_docstring: true
require_class_docstring: true
require_function_docstring: true
require_parameter_hints: true
require_return_hints: true
detect_unused_imports: true
detect_test_gaps: true
detect_security_risks: true
detect_silent_failures: true
detect_dependency_cycles: true
severity_exit_level: "serious"
max_workers: 4
```

`include_patterns` matters: unlike the old JSON config (which implicitly
scanned everything not excluded), the doctor now scans only files matching
`include_patterns`, then removes anything matching `ignore_patterns`. Point
it at your actual source globs or the scan will come back empty. A `**/`
segment matches zero or more directories (`src/**/*.py` includes files
directly under `src/`), and an empty `include_patterns: []` is a
configuration error (exit `4`).

The bundled YAML reader covers plain `key: value` pairs, quoted scalars,
one-level lists, flow lists, and `{}`. A few rules to know:

- `severity_exit_level: none` works quoted or unquoted; `null` and `~` mean
  the same gate.
- Unknown keys, and unknown categories under `severity_levels`, are reported
  on stderr with the closest valid key (`detect_silent_failure` suggests
  `detect_silent_failures`), then ignored.
- Integers must be plain decimals. A leading-zero value such as `010` stays
  a string and fails validation with exit `4`.
- `#` starts a comment only at the start of a line or after whitespace, so
  `x#y` stays `x#y`.

## Basic usage

These are the everyday commands, one task each.

### Scan a project

```bash
somnus-debug doctor scan /path/to/your/project
somnus-debug doctor /path/to/your/project        # bare path also works: normalized to `scan`
```

### With a specific config

```bash
somnus-debug doctor scan /path/to/project -c python_doctor.yaml
```

### Markdown + JSON output paths

```bash
somnus-debug doctor scan /path/to/project -o report.md --json-output report.json
```

`project_root` must be an existing directory; a missing path or a file exits
`4` and creates nothing.

### Skip SQLite state tracking (no history/rollback for that run)

```bash
somnus-debug doctor scan /path/to/project --no-state
```

### Verbose logging

```bash
somnus-debug doctor scan /path/to/project -v
```

### Scan history / rollback

```bash
somnus-debug doctor history /path/to/project --limit 10
somnus-debug doctor rollback /path/to/project --run-id 20260901T201813Z
```

### Self-check (scan the doctor's own package directory)

```bash
somnus-debug doctor self-check
```

## Command reference

This is the full doctor command tree.

```text
somnus-debug doctor {scan,init-config,history,rollback,self-check}

scan [project_root] [-c CONFIG] [-o OUTPUT] [--json-output JSON_OUTPUT]
     [--no-state] [-v/--verbose]

init-config [-o OUTPUT] [--force]

history [project_root] [-c CONFIG] [--limit N]

rollback [project_root] --run-id RUN_ID [-c CONFIG]

self-check [-c CONFIG] [-o OUTPUT] [--json-output JSON_OUTPUT] [--no-state]
```

`project_root` defaults to `.` wherever it appears.

## Understanding the report

The markdown report includes:

1. **Summary** -- files scanned, issue counts by severity (critical / serious
   / minor), syntax-error files, missing imports, cycles, short classes and
   functions.
2. **Issue Categories** -- counts per finding category.
3. **Local State Delta** -- what changed since the previous stateful run.
4. **Dependency Map** -- missing or unresolved imports and dependency cycles.
5. **Suspiciously Short Classes** and **Suspiciously Short Functions**.
6. **Full Issue Index** -- every finding in one list.
7. **File Diagnostics** -- per-file metrics and each issue with its line.
8. **Recommended Action Plan** -- what to fix first, grouped by severity.

There is no docstring or type-hint coverage section; gaps show up as
`missing_docstrings` and `type_hint_gaps` findings. `test_gaps` is a
configured category that the doctor never emits, so the report says nothing
about test coverage.

`from pkg import name` resolves to `pkg/name.py` when that submodule exists,
and in a `src/` layout the project's own packages resolve locally without
`PYTHONPATH`, so cycles written either way are found.

State (run history, rollback targets) is stored under `.python_doctor/`
in the scanned project root unless `--no-state` is passed. Run IDs are UTC
timestamps; a second scan in the same second gets a `-1` suffix (then `-2`,
and so on) instead of overwriting the first.

## Exit codes

Exit code is gated by `severity_exit_level` in the config (default:
`"serious"` -- any serious-or-worse finding fails the run). Set it to
`"critical"` to only fail on critical issues, `"minor"` to also fail on minor
findings, `"info"` to also fail on info findings, or `none` to never fail on
findings.

| Code | Meaning |
|---|---|
| `0` | No finding at or above the gate (always `0` under `none`) |
| `1` | A non-critical finding at or above the gate |
| `2` | A critical finding, under every gate except `none`; also an argparse usage error |
| `4` | `DoctorError`: bad config, missing root, unknown run ID, unusable state |
| `5` | Any other runtime failure (traceback in `production_doctor.log` in the working directory) |

A file the analyzer fails on becomes a critical `analysis_read_errors`
finding, not a crash. A zero-file scan exits `0`.

## Tips

These habits keep the doctor useful as a gate.

1. **Run before each commit:**

   ```bash
   somnus-debug doctor scan . -c python_doctor.yaml && git commit -m "your message"
   ```

2. **Add to CI/CD:**

   ```yaml
   - name: Code Health Check
     run: somnus-debug doctor scan . -c python_doctor.yaml --json-output report.json
   ```

   This gates on every serious finding, including ones that predate the
   change. To gate only on new findings, compare two JSON reports with the
   fieldkit's `delta.py` (see `skills/somnus-debug-fieldkit/references/doctor-loop.md`).

3. **Tune thresholds** in `python_doctor.yaml`: `min_function_lines`,
   `min_docstring_length`, `max_cyclomatic_complexity`, `severity_levels`.

4. **Ignore specific functions/classes:** add names to `ignore_functions` /
   `ignore_classes` in the config. Security-risk calls (`eval`, `exec`,
   `subprocess.run`, and the rest) inside an ignored function, or a nested
   function skipped by `check_nested_functions: false`, are still reported.

5. **Scope what gets scanned:** `include_patterns` is the primary lever --
   narrow or widen it before touching `ignore_patterns`.

## Troubleshooting

These are the common surprises and their fixes.

**Config seems ignored?**
The doctor loads a config only from `-c`. A `python_doctor.yaml` in the
project root is not picked up automatically.

**Scan finds 0 files?**
Check `include_patterns` -- it must actually match your project's real
source layout. The generated default (`*.py`) matches everything, so zero
files usually means a copied config with Somnus-style globs (`tools/*.py`,
`test/*.py`) or an `ignore_patterns` entry that prunes your source. A
zero-file scan exits `0`; check `files=` in the summary line.

**Scanning too much / too slow?**
Tighten `include_patterns`, add more `ignore_patterns`, or raise
`max_workers` (`-j` is not a flag here -- `max_workers` is config-only).

**False positives on short functions/classes?**
Raise `min_function_lines` / `min_class_lines`, or add specific names to
`ignore_functions` / `ignore_classes`.

## Files generated

Every scan writes these files.

- Markdown report (`-o`; default `<project_root>/production_doctor_report.md`)
- JSON report, always: `--json-output` when given, otherwise next to the
  markdown with a `.json` suffix. When `-o` ends in `.json`, that path gets
  the JSON and the markdown goes to the same stem with `.md`; the same path
  for both exits `4`.
- `production_doctor.log` in the current working directory (always, even
  for `--help`)
- `.python_doctor/` state directory in the scanned project root (unless
  `--no-state`)

## Integration ideas

These are ways to wire the doctor into existing workflows.

- **Pre-commit hook:** block commits with critical issues.
- **CI/CD gate:** fail the pipeline on `severity_exit_level` breach.
- **Rollback on regression:** `somnus-debug doctor rollback <root> --run-id <id>`
  repoints the `latest` alias and `.python_doctor/reports/latest.{md,json}`
  to a previous run without re-scanning, and the next scan's delta is
  computed against it. It does not touch `-o` or project-root reports, or
  any source file.
