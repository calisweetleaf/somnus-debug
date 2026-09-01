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
that's for the `pycache-clean` tool, not the doctor.)

## Configuration: `python_doctor.yaml`

Generate a starting config in your project root:

```bash
somnus-debug doctor init-config -o python_doctor.yaml
```

Key fields (see the generated file for the full set with comments):

```yaml
schema_version: "3.0"
min_function_lines: 5
min_class_lines: 6
min_docstring_length: 18
max_cyclomatic_complexity: 12
include_patterns:
  - "tools/*.py"
  - "test/*.py"
ignore_patterns:
  - "__pycache__/*"
  - "*.pyc"
  - ".git/*"
  - ".venv/*"
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
it at your actual source globs or the scan will come back empty.

## Basic usage

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
   / minor), overall readiness gate.
2. **Code quality metrics** -- docstring and type-hint coverage.
3. **File-by-file analysis** -- issues per file with line numbers.
4. **Dependency graph findings** -- import cycles, unresolved/missing
   imports.
5. **Action plan** -- what to fix first, ordered by severity.

State (run history, rollback targets) is stored under `.python_doctor/`
in the scanned project root unless `--no-state` is passed.

## Exit codes

Exit code is gated by `severity_exit_level` in the config (default:
`"serious"` -- any serious-or-worse finding fails the run). Set it to
`"critical"` to only fail on critical issues, or `"minor"` to fail on
anything at all.

- `0`: scan completed at or below the configured gate
- non-zero: gate exceeded, or a `DoctorError`/unclassified runtime failure
  (see `production_doctor.log` in the working directory)

## Tips

1. **Run before each commit:**

   ```bash
   somnus-debug doctor scan . && git commit -m "your message"
   ```

2. **Add to CI/CD:**

   ```yaml
   - name: Code Health Check
     run: somnus-debug doctor scan . --json-output report.json
   ```

3. **Tune thresholds** in `python_doctor.yaml`: `min_function_lines`,
   `min_docstring_length`, `max_cyclomatic_complexity`, `severity_levels`.

4. **Ignore specific functions/classes:** add names to `ignore_functions` /
   `ignore_classes` in the config.

5. **Scope what gets scanned:** `include_patterns` is the primary lever --
   narrow or widen it before touching `ignore_patterns`.

## Troubleshooting

**Scan finds 0 files?**
Check `include_patterns` -- it must actually match your project's real
source layout (the shipped default targets `tools/*.py` and `test/*.py`,
which is Somnus-repo-specific, not universal).

**Scanning too much / too slow?**
Tighten `include_patterns`, add more `ignore_patterns`, or raise
`max_workers` (`-j` is not a flag here -- `max_workers` is config-only).

**False positives on short functions/classes?**
Raise `min_function_lines` / `min_class_lines`, or add specific names to
`ignore_functions` / `ignore_classes`.

## Files generated

- Markdown report (`-o`, default path set by the tool if omitted)
- JSON report (`--json-output`, if requested)
- `production_doctor.log` in the current working directory (always)
- `.python_doctor/` state directory in the scanned project root (unless
  `--no-state`)

## Integration ideas

- **Pre-commit hook:** block commits with critical issues.
- **CI/CD gate:** fail the pipeline on `severity_exit_level` breach.
- **Rollback on regression:** `somnus-debug doctor rollback <root> --run-id <id>`
  to restore a previous report as latest without re-scanning.
