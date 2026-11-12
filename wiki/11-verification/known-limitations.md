# Known limitations

This page lists the limits of somnus-debug 0.1.0 that a user or agent must plan around, grouped by tool, with severity and workaround. It also lists the limits of this wiki's verification itself. Each limit links to its discovery entry where one exists.

## Severity key

This section defines the labels.

- **Blocking**: the tool fails on normal input.
- **Misleading**: the tool succeeds but reports something untrue, or hides a problem.
- **Hazard**: the tool can damage files or state.
- **Friction**: annoying, but harmless once known.

## doctor

This section lists doctor's limits.

| Limit | Severity | Workaround | Evidence |
|---|---|---|---|
| a config file is never auto-loaded | Misleading | always pass `-c` | [D-02](../DISCOVERY-LEDGER.md#d-02); lane D D27 |
| unquoted `none` gate is null -> exit 4; the `none` and `info` gates are undocumented | Friction | quote values | [D-03](../DISCOVERY-LEDGER.md#d-03); W2-08 |
| minimal YAML parser: malformed lines and unknown keys accepted silently | Misleading | validate config externally | [D-04](../DISCOVERY-LEDGER.md#d-04) |
| `test_gaps` / `detect_test_gaps` do nothing | Misleading | none; do not rely on test-gap findings | [D-05](../DISCOVERY-LEDGER.md#d-05) |
| `from pkg import mod` resolves to `pkg/__init__.py`, so such cycles and missing siblings are missed | Misleading | prefer `import pkg.mod` when cycle detection matters | [D-06](../DISCOVERY-LEDGER.md#d-06) |
| false positives: `return 1` as placeholder; stubs on abstract/Protocol/overload; duplicates on property setters and overloads; frozen dataclasses as short classes; `__future__`/`__all__` as unused imports; name-sensitive `silent_failures` | Misleading | disposition narrowly | [D-07](../DISCOVERY-LEDGER.md#d-07) |
| no hardcoded-secret detection; `print` is not a detector; security checks are call-name only | Misleading | use a dedicated secret scanner | lane D detector table |
| same-second scans overwrite each other in history | Hazard (history loss) | space scans at least 1 s apart | [D-08](../DISCOVERY-LEDGER.md#d-08); W2-17 |
| rollback moves only the `latest` alias | Misleading | read `.python_doctor/reports/latest.json`, not the root report | [D-09](../DISCOVERY-LEDGER.md#d-09); W2-16 |
| writes `production_doctor.log` to cwd on every call; `self-check` writes into the installed package | Friction / Hazard on read-only installs | scratch cwd; `self-check --no-state -o ... --json-output ...` | [D-10](../DISCOVERY-LEDGER.md#d-10) |
| replaces the host process's logging handlers (`basicConfig(force=True)`) | Hazard for embedders | use `ProjectScanner` directly | [D-11](../DISCOVERY-LEDGER.md#d-11); W2-20 |
| `ignore_functions` / `check_nested_functions: false` also hide security findings in skipped bodies | Misleading | keep both narrow | [D-16](../DISCOVERY-LEDGER.md#d-16) |
| default ignores skip `env/`, `build/`, `venv/` directories at any depth; empty `include_patterns` scans 0 files and passes | Misleading | review coverage; assert `files_scanned > 0` | [D-17](../DISCOVERY-LEDGER.md#d-17) |
| exit 2 means both "critical finding" and "usage error"; uncaught exception types become tracebacks; one pathological file can abort a serial-path scan with exit 5 | Misleading | check for the JSON / `Scan complete:` line | [D-18](../DISCOVERY-LEDGER.md#d-18) |
| no plugin/detector API | Friction | subclass `CodeQualityVisitor` (private) | [D-19](../DISCOVERY-LEDGER.md#d-19) |
| src layout plus `PYTHONPATH=src` classifies own imports as third-party, so `dependency_cycles` reads 0 | Misleading | scan cycles once without `PYTHONPATH` and ignore the `missing_imports` noise | [D-22](../DISCOVERY-LEDGER.md#d-22) |
| `-o report.json` loses the Markdown | Friction | pass both `-o` and `--json-output` | [D-25](../DISCOVERY-LEDGER.md#d-25); W2-23 |
| `missing_imports` depends on the interpreter, `PYTHONPATH`, and invocation form (cwd is on `sys.path` only under `python -m`) | Misleading | fixed interpreter and invocation form; neutral cwd | [D-26](../DISCOVERY-LEDGER.md#d-26); W2-25 |
| `history`/`rollback` need a working SQLite; the root duplicate has no fallback even for scan | Friction | use the packaged doctor | [D-28](../DISCOVERY-LEDGER.md#d-28) |
| `-v` is ignored and `--verbose` has nothing to log | Friction | none needed | W2-07 |
| no report `schema_version`; JSON shape is unversioned | Friction for consumers | pin the somnus-debug version | [input-output-contracts](../05-cli-and-tools/input-output-contracts.md#stability-notes) |

## structure

This section lists structure's limits.

| Limit | Severity | Workaround | Evidence |
|---|---|---|---|
| crashes (exit 2) on any comment line shaped like a type comment, which includes every `# somnus:metadata:v2` header, so all files in this repo | **Blocking** | use the root `analyze_python_structure.py` | [D-01](../DISCOVERY-LEDGER.md#d-01); W2-15, W2-26 |
| non-UTF-8 source gives a traceback, exit 1 | Friction | re-encode | W2-09 |
| nested class inside a class inside a function is rendered and counted twice | Misleading | none | [D-24](../DISCOVERY-LEDGER.md#d-24) |
| `--no-module-functions` still counts the omitted functions in the header | Friction | ignore the count | lane D S10 |
| one file per call, no directory mode | Friction | loop in shell | `src/somnus_debug/structure/core.py:280-320` |

## pycache-clean

This section lists the cleaner's limits.

| Limit | Severity | Workaround | Evidence |
|---|---|---|---|
| no type checks: `dry_run: no` runs live; a scalar `roots` is iterated per character (can include `/`) | **Hazard** | YAML list of absolute roots; `--dry-run` first | [D-14](../DISCOVERY-LEDGER.md#d-14) |
| exclude matches basenames only; path-style patterns silently do nothing | Hazard | bare names | [D-14](../DISCOVERY-LEDGER.md#d-14); selftest check 28 |
| an unknown key silences all logging (deletion still happens) | Misleading | no unknown keys | [D-14](../DISCOVERY-LEDGER.md#d-14); lane D P09 |
| dry-run output says "Removed"/"deleted"; a missing root exits 0 | Misleading | read the header; grep for `[ERROR]` | W2-18; lane D P01 |
| roots relative to cwd; no `$VAR` expansion; no Windows long-path code | Friction | absolute paths | [D-14](../DISCOVERY-LEDGER.md#d-14) |
| no path argument; config required | Friction | write a config | [command-reference](../05-cli-and-tools/command-reference.md#pycache-clean) |
| `SyntaxWarning` on uncached import (from any `somnus-debug` subcommand) | Friction | `PYTHONWARNINGS=ignore` | W2-01 |

## init-test-harness and run_test.py

This section lists the harness's limits.

| Limit | Severity | Workaround | Evidence |
|---|---|---|---|
| root placement writes `test-runs/` outside the repo | Hazard (writes outside the repo) | scaffold into a subdirectory or set `PROJECT_ROOT` | [D-15](../DISCOVERY-LEDGER.md#d-15); W2-19 |
| template test is project-specific (cargo gp-cli) and fails out of the box | Friction | replace `execute_test` | W2-19 |
| template ignores `--help` and executes | Friction | none | lane D H09 |
| template adds 9 serious doctor findings once inside a scanned tree | Misleading | disposition or ignore | W2-19; lane F H-3 |
| every scaffolded copy inherits the template's artifact URNs | Friction | edit the header | lane D section 5 |
| no `somnus-init-test-harness` script | Friction | `somnus-debug init-test-harness` | W2-02 |

## Dispatcher and packaging

This section lists cross-cutting limits.

| Limit | Severity | Workaround | Evidence |
|---|---|---|---|
| PyYAML is required for every dispatcher subcommand | Blocking without PyYAML | `somnus-doctor` / `-m somnus_debug.doctor.core` | [D-13](../DISCOVERY-LEDGER.md#d-13); W2-05 |
| version hard-coded in two places; PyPI default config differs (reference-only) | Friction | none | [D-23](../DISCOVERY-LEDGER.md#d-23) |
| no `python -m somnus_debug` | Friction | `python -m somnus_debug.cli` | lane D C04 |

## Fieldkit

This section lists the agent scripts' limits.

| Limit | Severity | Workaround | Evidence |
|---|---|---|---|
| `onboard.py --python` rejects symlinked venv interpreters; a config error crashes with exit 1; `PROFILE.md` is written even when verification fails | Misleading | rely on venv auto-detection; check the verification line | [D-20](../DISCOVERY-LEDGER.md#d-20) |
| `delta.py`: a stale broad disposition absorbs regressions; `config_hash` is not compared; usage errors exit 2; a malformed report gives a traceback | Misleading | ratchet only with zero stale dispositions; same config for both scans | [D-21](../DISCOVERY-LEDGER.md#d-21) |
| selftest misses the structure stamped-file crash | Misleading | also run [verification step 5](../02-installation/verification.md#step-5-check-for-the-structure-stamped-file-crash) | W2-04 |

## Limits of this verification

This section states what this wiki could not establish.

- Only Linux aarch64 was available. Every platform claim beyond it is unverified.
- `/tmp` was wiped mid-wave (around 00:40 UTC), and lane D lost its `/tmp` the same way. The W2 fixtures and venvs had to be rebuilt partway through. All outputs quoted on these pages were captured before each wipe and are reproduced inline. Probes that rebuild everything are on [reproducible-probes](reproducible-probes.md).
- The sandbox display layer rewrites ISO timestamps in tool output, so doctor's `completed_at` values in quoted history lines are elided. The bytes on disk were checked to be ISO-8601 (W2-12).
- Behaviors in [untested-behaviors](untested-behaviors.md) tier 2 were never executed.

## Sources

This section lists the code and evidence this page draws on.

- [DISCOVERY-LEDGER](../DISCOVERY-LEDGER.md) entries D-01 to D-28 as linked
- [lane D README.md](../_evidence/agent-findings/lane-d-cli-tests/README.md), [command-reference.md](../_evidence/agent-findings/lane-d-cli-tests/command-reference.md); [lane B configuration-findings.md](../_evidence/agent-findings/lane-b-config/configuration-findings.md); [lane F fieldkit.md](../_evidence/agent-findings/lane-f-ext/fieldkit.md), [harness.md](../_evidence/agent-findings/lane-f-ext/harness.md)
- W2 runs: [verification-results](verification-results.md#w2-runs)
