# Provenance and version notes

**Research date:** 2026-10-11 (America/Chicago)

This skill was built against the public `calisweetleaf/somnus-debug` repository, default branch `master`, tree/commit `3ad5e8366ab5d527aa45313a1b535e8912a2dcf3`. The repository had no later commit visible at research time. Core reference files: `SKILL/somnus-debug.md`, `docs/MANUAL.md`, `docs/Python_Doctor_QUICKSTART.md`, `docs/AGENTS_APPENDIX.md`, `docs/CONTRACT.md`, `src/somnus_debug/cli.py`, `src/somnus_debug/test_harness/scaffold.py`, and `pyproject.toml`.

## Verification basis (2026-11-01)

- `scripts/selftest.py`: 29/29 against the workstation's `somnus-debug` 0.1.0 on PATH, and 29/29 against a fresh `pip install somnus-debug` from PyPI in a clean venv (`--python`).
- The installed 0.1.0 package, the PyPI 0.1.0 wheel, and the PyPI 0.1.0 sdist are all byte-identical (`diff -r`) to `src/somnus_debug/` at commit `5b6e0c4`. PyPI lists only `0.1.0` (uploaded 2026-09-02). Repository commits after the upload changed docs, README, and the skill, not package code.
- The sharp edges in `SKILL.md`, the triggers in `findings.md`, and the semantics in `onboarding.md` were read from that source (`CodeQualityVisitor`, `handler_is_silent`, `body_is_stub`, `placeholder_return_kind`, `SECURITY_CALLS`, `TODO_PATTERNS`, `ImportResolver`), plus config loading and matching in `doctor/core.py` (`ConfigManager`, `ProjectFileIndex`), report paths in `StateStore.report_paths`, exit codes in `exit_code_for_summary` and `main`, log location in `setup_logging`, and pycache exclude/roots handling in `pycache_cleaner/core.py`.
- The repo-root `python_doctor.yaml` there is a pre-packaging leftover (MANUAL §7.5), excluded from the package build and never read by the CLI unless passed with `-c`. Its `tools/*.py`, `test/*.py`, and speech globs come from the Somnus-MCP layout, so it scans zero files against any other tree. Before 2026-11-01, the packaged `src/somnus_debug/doctor/default_config.yaml` and the MANUAL, QUICKSTART, and AGENTS appendix also described those globs as the default, while `init-config` already emitted `*.py`. The packaged file and docs now match `init-config`, and `tests/test_cli_smoke.py::test_packaged_default_config_matches_init_config` enforces it.
- An earlier private working checkout (pre-rename remote) has the same package code and root scripts. It also holds local operator state (`AGENTS.md`, `PLAN.md`, `STATE.md`, `HANDOFF.md`, `OPSEC.md`) that is intentionally untracked.

## Self-scan of the fieldkit scripts (2026-11-01)

`doctor scan scripts/` reports 6 serious findings, all reviewed and dispositioned. They show what legitimate dispositions look like:

| Finding | Disposition |
|---|---|
| `security_risks` `subprocess.run` in `onboard.run`, `selftest.Harness.cli`, `selftest.config_with` | argv list, no shell, fixed executable (somnus-debug or git) |
| `silent_failures` `delta.main` | CLI boundary: prints the error to stderr and returns exit 3 |
| `broad_exceptions` + `silent_failures` `selftest.main` | Deliberate: a crashed check group is recorded as a FAIL row with its cause, and the run exits 1 |

The remaining minors are `__future__` import false positives, short helpers, and complexity in the three `main`/render functions.

## Version split observed

- GitHub's latest tag visible at research time was `v1.5.0`, whose release title is “PyPi Now Published.”
- The tag points to commit `3ad5e8366ab5d527aa45313a1b535e8912a2dcf3`.
- PyPI's project page listed the uploaded package as `somnus-debug 0.1.0`, released Sep 2, 2026.
- The checked repository `pyproject.toml` also declares `0.1.0`. On 2026-10-19, the maintainer confirmed that Somnus Debug is published on PyPI. This is a publication-status update, not a fresh verification of the latest index version; the linked project page is the public source of truth.
- At the 2026-10-11 research snapshot, the README, short skill, publishing guide, and agent appendix still contained pre-publication claims. The repository's 2026-10-19 update corrected those status statements and routed agents to this fieldkit. Treat the 2026-10-11 wording as historical evidence only, not current installation guidance.

For every target codebase, ask the actual installed CLI for `--version` and each command's `--help`. Do not assume the Git tag version equals the package version. If installed behavior differs from this guide, update the guide from the matching current source before relying on an unfamiliar flag.

## Repository source map

| Topic | Source |
|---|---|
| Toolkit overview and command list | [README at the research snapshot](https://github.com/calisweetleaf/somnus-debug/blob/3ad5e8366ab5d527aa45313a1b535e8912a2dcf3/README.md) |
| Trigger conditions and old short skill | [SKILL/somnus-debug.md](https://github.com/calisweetleaf/somnus-debug/blob/3ad5e8366ab5d527aa45313a1b535e8912a2dcf3/SKILL/somnus-debug.md) |
| Exact CLI flags, config behavior, state, cleanup, and harness usage | [Manual lines 81–169: doctor](https://github.com/calisweetleaf/somnus-debug/blob/3ad5e8366ab5d527aa45313a1b535e8912a2dcf3/docs/MANUAL.md#L81), [170–207: structure](https://github.com/calisweetleaf/somnus-debug/blob/3ad5e8366ab5d527aa45313a1b535e8912a2dcf3/docs/MANUAL.md#L170), [208–257: pycache-clean](https://github.com/calisweetleaf/somnus-debug/blob/3ad5e8366ab5d527aa45313a1b535e8912a2dcf3/docs/MANUAL.md#L208), and [258–279: harness](https://github.com/calisweetleaf/somnus-debug/blob/3ad5e8366ab5d527aa45313a1b535e8912a2dcf3/docs/MANUAL.md#L258) |
| Doctor YAML schema and finding interpretation | [Config at line 26](https://github.com/calisweetleaf/somnus-debug/blob/3ad5e8366ab5d527aa45313a1b535e8912a2dcf3/docs/Python_Doctor_QUICKSTART.md#L26), [report at line 137](https://github.com/calisweetleaf/somnus-debug/blob/3ad5e8366ab5d527aa45313a1b535e8912a2dcf3/docs/Python_Doctor_QUICKSTART.md#L137), [exit codes at line 152](https://github.com/calisweetleaf/somnus-debug/blob/3ad5e8366ab5d527aa45313a1b535e8912a2dcf3/docs/Python_Doctor_QUICKSTART.md#L152) |
| Existing portable agent appendix | [docs/AGENTS_APPENDIX.md](https://github.com/calisweetleaf/somnus-debug/blob/3ad5e8366ab5d527aa45313a1b535e8912a2dcf3/docs/AGENTS_APPENDIX.md) |
| Test-surface meaning and Accelerate relationship | [Stable contract at line 25](https://github.com/calisweetleaf/somnus-debug/blob/3ad5e8366ab5d527aa45313a1b535e8912a2dcf3/docs/CONTRACT.md#L25), [Accelerate at line 109](https://github.com/calisweetleaf/somnus-debug/blob/3ad5e8366ab5d527aa45313a1b535e8912a2dcf3/docs/CONTRACT.md#L109) |
| CLI dispatch and current subcommands | [src/somnus_debug/cli.py line 28](https://github.com/calisweetleaf/somnus-debug/blob/3ad5e8366ab5d527aa45313a1b535e8912a2dcf3/src/somnus_debug/cli.py#L28) |
| Harness overwrite behavior | [src/somnus_debug/test_harness/scaffold.py line 30](https://github.com/calisweetleaf/somnus-debug/blob/3ad5e8366ab5d527aa45313a1b535e8912a2dcf3/src/somnus_debug/test_harness/scaffold.py#L30) |
| Package name/version, runtime dependency, scripts | [pyproject.toml](https://github.com/calisweetleaf/somnus-debug/blob/3ad5e8366ab5d527aa45313a1b535e8912a2dcf3/pyproject.toml) |
| Published package | [PyPI: somnus-debug](https://pypi.org/project/somnus-debug/) |

The checked repository README links to `STATE.md`, `PLAN.md`, and `docs/OPSEC.md`; those paths were absent from the public default-branch tree at this snapshot. They exist only as untracked local operator state. They are private continuity, not public release content. Always apply the target codebase's actual authority and security instructions.

## Refresh rule

On a new skill revision, compare the current `master` tree, latest GitHub release/tag, `pyproject.toml`, PyPI release history, and the installed CLI docs. Update this note and command references when behavior or package availability changes. Preserve observed source and inferred interpretation as separate claims.
