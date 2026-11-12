# Environment matrix

This page records every environment in which somnus-debug 0.1.0 evidence was produced: interpreters, install modes, invocation forms, and dependency availability. It shows how results varied across them, so a reader can judge whether a claim transfers to their setup.

## Host

This section fixes the machine-level facts shared by all runs.

| Item | Value |
|---|---|
| OS | Debian GNU/Linux 13 (trixie) |
| Arch | aarch64 (`uname -sm`: `Linux aarch64`) |
| Default system Pythons | `/usr/local/bin/python3` = 3.12.15 (PyYAML 6.0.2); `/usr/bin/python3` = 3.13.5 (no PyYAML) |
| Extra Pythons (W2 only) | 3.10.22 and 3.11.17 via `uv python install` into `/tmp/w2/uvpy` |
| Repo baseline | commit `034f46e` (the uploaded zip) |
| Sandbox quirks | `/tmp` was wiped during lane D's wave and again around 00:40 UTC in W2; the tool display rewrites ISO-8601 timestamps |

[VERIFIED] W2-05, W2-06; lane D [experiment-log.md](../_evidence/agent-findings/lane-d-cli-tests/experiment-log.md) caveats.

## Interpreter x install mode

This section is the core matrix. Cells give the observed result.

| Interpreter | Install mode | Dispatcher `somnus-debug` | doctor | structure plain / stamped | pytest suite | selftest |
|---|---|---|---|---|---|---|
| 3.10.22 | venv, `pip install <repo>` | works | 7 issues, exit 1 | 0 / 2 | 10 pass, 2 fail | 29/29 |
| 3.11.17 | venv, `pip install <repo>` | works | 7 issues, exit 1 | 0 / 2 | 10 pass, 2 fail | 29/29 (rerun) |
| 3.12.15 | venv, `pip install <repo>` (W2, lanes A/D/F) | works | 7 issues, exit 1 | 0 / 2 | 10 pass, 2 fail | 29/29 |
| 3.12.15 | system, `PYTHONPATH=src` (lane B, W2-01) | works; `SyntaxWarning` on stderr | works | 0 / 2 | n/a | 28/29 with `--python` (harness artifact) |
| 3.12.15 | `PYTHONPATH=<pypi wheel>` (lane D) | works | works | own headerless source 0; stamped 2 | n/a | n/a |
| 3.13.5 | system, `PYTHONPATH=src`, **no PyYAML** | **fails**, exit 1 (`No module named 'yaml'`) | works via `-m somnus_debug.doctor.core`: 7 issues, exit 1 | `-m somnus_debug.structure.core` 0 | n/a | 1/24 (lane D F02) |

Doctor column = the quickstart fixture scan, where one was run. The 3.10/3.11/3.12 issue tuples were identical. [VERIFIED] W2-03 to W2-06; lane D F02/F02c, S05/S06.

## Invocation form

This section shows that the invocation form changes import resolution.

| Form | `sys.path[0]` | Effect on doctor | Evidence |
|---|---|---|---|
| console script (`somnus-debug`, `somnus-doctor`) | the script's directory (`venv/bin`) | cwd modules are **not** importable, so they count as missing | [VERIFIED] W2-25: `('cwdhelper', 'missing')`, exit 1 |
| `python -m somnus_debug.cli` / `.doctor.core` | the cwd | cwd modules count as third-party | [VERIFIED] W2-25: `('cwdhelper', 'third_party')`, exit 0 |
| in-process `cli.main([...])` | the host's | the host's `sys.path`; logging hijacked | [VERIFIED] W2-20 |
| in-process `ProjectScanner(...).scan({})` | the host's | no logging or disk side effects | [VERIFIED] W2-20; lane A |

See [D-26](../DISCOVERY-LEDGER.md#d-26).

## Dependency availability

This section shows what changes when optional pieces are missing.

| Missing piece | Effect | Evidence |
|---|---|---|
| PyYAML | every dispatcher subcommand fails; `somnus-doctor`/`somnus-structure` and their `-m` forms work; pycache-clean cannot run | [VERIFIED] W2-05; lane A `venv-noyaml` |
| pytest in doctor's interpreter | `import pytest` in scanned code becomes a serious `missing_imports` | [VERIFIED] lane D D05a/b |
| usable SQLite state DB | scan warns and continues; history/rollback exit 4 | [VERIFIED] lane D D39-D41 |
| `cargo` | the unedited harness template FAILs | [VERIFIED] W2-19 |
| `somnus-debug` on PATH | selftest and onboard exit 3 | [VERIFIED] lane D F03, O05 |

## Per-lane environments

This section lists where each evidence lane ran, so citations can be traced.

| Lane | Environment | Notes |
|---|---|---|
| A (architecture, API) | `/tmp/lane-a/venv` (3.12, non-editable install); `venv-noyaml` (`--no-deps`) | in-process probes |
| B (configuration) | system 3.12 with `PYTHONPATH=<repo>/src`, `PYTHONWARNINGS=ignore` | self-check on a copy of `src/` |
| D (CLI, tests) | `/tmp/lane-d/venv` (3.12, plus pytest); system 3.13 without PyYAML; PyPI wheel via `PYTHONPATH` | `/tmp/lane-d` was wiped after its runs |
| F (extensions, fieldkit) | `/tmp/lane-f/venv` plus a fixture repo with its own `.venv` | `--copies` venv needed for `onboard --python` |
| W2 (this page set) | `/tmp/w2/venv` (3.12), `venv3.10`, `venv3.11`, system 3.13 | rebuilt after the `/tmp` wipe |

## Sources

This section lists the code and evidence this page draws on.

- [lane A architecture.md](../_evidence/agent-findings/lane-a-arch-api/architecture.md); [lane B configuration-findings.md](../_evidence/agent-findings/lane-b-config/configuration-findings.md); [lane D install-vs-source.md](../_evidence/agent-findings/lane-d-cli-tests/install-vs-source.md), [experiment-log.md](../_evidence/agent-findings/lane-d-cli-tests/experiment-log.md); [lane F fieldkit.md](../_evidence/agent-findings/lane-f-ext/fieldkit.md)
- `src/somnus_debug/cli.py:55-58`; `src/somnus_debug/doctor/core.py:1001`, `:1050-1055`
- W2 runs: [verification-results](verification-results.md#w2-runs)
