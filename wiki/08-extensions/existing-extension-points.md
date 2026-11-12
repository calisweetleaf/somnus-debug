# Existing extension points

This page lists every place where somnus-debug 0.1.0 can be shaped from outside its source, with the tier each one belongs to. "Extension point" is used loosely here: none of these is a plugin interface. They are the seams the code actually exposes.

## Inventory

This section is the full list, one row per seam, with its tier and evidence.

| # | Seam | What you can do through it | Tier | Evidence |
|---|---|---|---|---|
| E1 | Doctor config file (`-c`) | Thresholds, 5 detector toggles, include and ignore globs, `ignore_functions` and `ignore_classes`, per-category severity, exit gate, `state_dir` | Supported now | [VERIFIED] `src/somnus_debug/doctor/core.py:829-849`; [customization](customization.md) |
| E2 | `severity_levels` with an arbitrary category name | Assign a severity to a category that only a custom detector emits | Supported for config; useful only with E9 | [VERIFIED] `src/somnus_debug/doctor/core.py:769-779`, `:792-794`; run in [the custom-detector recipe](../09-recipes/advanced/custom-detector-probe.md) |
| E3 | Doctor JSON report (`--json-output`) | Machine contract: summary, issues, per-file functions and classes with line spans, import graph, state delta | Supported now | [VERIFIED] [doctor JSON shape](../_evidence/agent-findings/lane-f-ext/logs/s1_doctor_json_shape.txt); format in [automation-contracts](../10-agent-usage/automation-contracts.md) |
| E4 | Doctor state directory | Per-run report archive, `latest` alias, SQLite history; reports reusable as delta baselines | Supported now | [VERIFIED] [lane-f compositions, C3'](../_evidence/agent-findings/lane-f-ext/compositions.md) |
| E5 | Fieldkit `dispositions.json` | Record reviewed findings so `delta.py` does not count them as regressions | Supported now | [VERIFIED] `skills/somnus-debug-fieldkit/scripts/delta.py:88-103`, `:129-144` |
| E6 | `delta.py --json` | Machine-readable regression verdict for CI, hooks, harnesses, agents | Supported now | [VERIFIED] `skills/somnus-debug-fieldkit/scripts/delta.py:223-232` |
| E7 | Scaffolded `run_test.py`: `TEST_NAME` and `execute_test()` | The one designed edit point in the package: a project-owned single test with a fixed artifact contract | Supported, but the shipped body must be replaced | [VERIFIED] `src/somnus_debug/test_harness/templates/run_test.py:195-198`; [lane-f harness](../_evidence/agent-findings/lane-f-ext/harness.md) |
| E8 | Library classes (`ProjectScanner`, `ConfigManager`, `FileAnalyzer`, `build_index`, `PycacheCleaner`, `scaffold`) | Run tools in-process, compose results in Python | Small integration step: only `build_index` and the `main` functions are exported; nothing is marked stable | [VERIFIED] [lane-a API reference](../_evidence/agent-findings/lane-a-arch-api/api-reference.md) |
| E9 | `somnus_debug.doctor.core.CodeQualityVisitor` (private) | Subclass and rebind to add a detector | Probe only; rebinds a private global | [VERIFIED + HYPOTHESIS for stability] `src/somnus_debug/doctor/core.py:1143`, `:1542`; [D-19](../DISCOVERY-LEDGER.md#d-19) |
| E10 | Module rule data `TODO_PATTERNS`, `PLACEHOLDER_CONSTANTS`, `SECURITY_CALLS` | Patchable at import time; nothing reads them from config | Probe only | [SOURCE-CONFIRMED] `src/somnus_debug/doctor/core.py:504-514` |
| E11 | `pycache-clean` `targets` key | Changes what the cleaner deletes: plain names are directory targets, names with `*` or `?` are file globs | Supported now, and dangerous | [VERIFIED] `src/somnus_debug/pycache_cleaner/core.py:162`, `:197-199`; run below |
| E12 | `structure` flags and `build_index()` keywords | Trim the index (no line numbers, no module functions), relabel the source | Supported now | [VERIFIED] `src/somnus_debug/structure/core.py:202`; [beginner recipe](../09-recipes/beginner/index-one-file.md) |
| E13 | Fieldkit profile directory `.somnus-debug/` | Project-local config, dispositions, runs, state, and a `PROFILE.md` card agents read first | Supported now | [VERIFIED] [lane-f fieldkit §2](../_evidence/agent-findings/lane-f-ext/fieldkit.md); [onboarding recipe](../09-recipes/intermediate/onboard-a-repo.md) |

## E11 in practice: `targets` turns the cleaner into a general deleter

This section records one run, because the behaviour is easy to miss and destructive.

`CleanerConfig.from_yaml()` copies any key that names a dataclass field, with no type or value check (`src/somnus_debug/pycache_cleaner/core.py:170-180`). `targets` is such a field (`:162`). Entries without wildcards are matched as directory names; entries with wildcards are matched against file names with `fnmatchcase` (`:197-199`, `:263-270`) [SOURCE-CONFIRMED].

Executed: yes (`/tmp/w4/c1`, fixture tree with `a/x.bak`, `a/keep.py`, `a/build_cache/blob`; exit 0; rerun by [the repro driver](../09-recipes/_repro/README.md))

```console
$ cat c.yaml
roots: ["/tmp/w4/c1/tree"]
targets: ["*.bak", "build_cache"]
$ somnus-debug pycache-clean --config c.yaml
[INFO] Starting pycache cleaner (dry_run=False)
[INFO] Scanning root: /tmp/w4/c1/tree
[INFO] Summary: deleted 1 directories, 1 files; freed 0.00 MiB
$ find tree | sort
tree
tree/a
tree/a/keep.py
```

The cleaner deleted a non-cache directory and a non-bytecode file because the config said so [VERIFIED]. A `targets` list containing `*.py` would delete source the same way [HYPOTHESIS, not run]. Together with the other config hazards in [D-14](../DISCOVERY-LEDGER.md#d-14), this means any `pycache.yaml` you did not write is untrusted input: dry-run it first. The fieldkit's generated `pycache.yaml` pins `targets` to the three bytecode defaults and locks `dry_run: true` (`skills/somnus-debug-fieldkit/scripts/onboard.py:300-318`) [SOURCE-CONFIRMED].

## What is not an extension point

This section names things that look like seams but are not.

- **`detect_test_gaps`.** Parsed and validated, read by nothing. Turning it on or off changes nothing [SOURCE-CONFIRMED, [D-05](../DISCOVERY-LEDGER.md#d-05)].
- **The repo-root `python_doctor.yaml`.** Never auto-loaded; only `-c` loads a config [VERIFIED, [D-02](../DISCOVERY-LEDGER.md#d-02)].
- **`src/somnus_debug/doctor/default_config.yaml`.** Reference only; `init-config` emits defaults built from `DEFAULT_CONFIG_DATA` in code [SOURCE-CONFIRMED, [D-23](../DISCOVERY-LEDGER.md#d-23)].
- **`-v` on doctor.** Accepted and ignored; only the literal `--verbose` changes the log level, and doctor emits no debug records, so neither has a visible effect (`src/somnus_debug/doctor/core.py:2179-2186`) [SOURCE-CONFIRMED].
- **Logging as an event stream.** Doctor's `main()` replaces the host's root logging handlers with a file handler in the cwd ([D-11](../DISCOVERY-LEDGER.md#d-11)). It is not a subscription surface; see [hooks-and-events](hooks-and-events.md).

## Sources

This section lists the files, logs and evidence this page rests on.

- [lane-f extensions](../_evidence/agent-findings/lane-f-ext/extensions.md), [lane-f fieldkit](../_evidence/agent-findings/lane-f-ext/fieldkit.md), [lane-f harness](../_evidence/agent-findings/lane-f-ext/harness.md), [lane-f compositions](../_evidence/agent-findings/lane-f-ext/compositions.md)
- [lane-a API reference](../_evidence/agent-findings/lane-a-arch-api/api-reference.md)
- `src/somnus_debug/doctor/core.py:504-514`, `:769-794`, `:829-849`, `:1143`, `:1542`, `:2179-2186`
- `src/somnus_debug/pycache_cleaner/core.py:158-199`, `:263-270`
- `skills/somnus-debug-fieldkit/scripts/delta.py`, `skills/somnus-debug-fieldkit/scripts/onboard.py:300-318`
- Wave 5 run: [repro driver and log](../09-recipes/_repro/README.md)
