# Provenance and version notes

**Research date:** 2026-10-11 (America/Chicago)

This skill was built against the public `calisweetleaf/somnus-debug` repository, default branch `master`, tree/commit `3ad5e8366ab5d527aa45313a1b535e8912a2dcf3`. The repository had no later commit visible at research time. Core reference files: `SKILL/somnus-debug.md`, `docs/MANUAL.md`, `docs/Python_Doctor_QUICKSTART.md`, `docs/AGENTS_APPENDIX.md`, `docs/CONTRACT.md`, `src/somnus_debug/cli.py`, `src/somnus_debug/test_harness/scaffold.py`, and `pyproject.toml`.

## Version split observed

- GitHub's latest tag visible at research time was `v1.5.0`, whose release title is “PyPi Now Published.”
- The tag points to commit `3ad5e8366ab5d527aa45313a1b535e8912a2dcf3`.
- PyPI's project page listed the uploaded package as `somnus-debug 0.1.0`, released Sep 2, 2026.
- The checked repository `pyproject.toml` also declares `0.1.0`. On 2026-10-19, the maintainer confirmed that Somnus Debug is published on PyPI. This is a publication-status update, not a fresh verification of the latest index version; the linked project page is the public source of truth.
- Some GitHub README/manual text still says publication has not happened and labels older build status. Those statements conflict with the PyPI project listing and the release. Treat them as stale documentation, not installation truth.

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

The checked repository README links to `STATE.md`, `PLAN.md`, and `docs/OPSEC.md`; those paths were absent from the recursive default-branch tree inspected at this snapshot. Do not invent their contents. Always apply the target codebase's actual authority and security instructions.

## Refresh rule

On a new skill revision, compare the current `master` tree, latest GitHub release/tag, `pyproject.toml`, PyPI release history, and the installed CLI docs. Update this note and command references when behavior or package availability changes. Preserve observed source and inferred interpretation as separate claims.
