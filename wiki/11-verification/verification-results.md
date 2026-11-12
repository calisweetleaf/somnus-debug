# Verification results

This page gives the exact results of every verification run: the shipped test suites (with commands and pass/fail counts), the reproducible probe set, and the full log of runs made while writing the installation, getting-started, CLI, and verification pages (W2-01 to W2-28). Other pages cite runs by these IDs.

## Headline results

This section gives the numbers most readers want.

| Suite | Command (cwd) | Result | Exit |
|---|---|---|---:|
| repo pytest, Python 3.12.15 | `PYTHONDONTWRITEBYTECODE=1 /tmp/w2/venv/bin/python -m pytest -q -p no:cacheprovider tests/` (`/tmp/w2/repo-copy`, a `tar` copy of the repo without `wiki/` and `.git/`) | **10 passed, 2 failed** in 1.46 s | 1 |
| repo pytest, Python 3.10.22 | same, `/tmp/w2/venv3.10/bin/python` | 10 passed, 2 failed in 4.30 s | 1 |
| repo pytest, Python 3.11.17 | same, `/tmp/w2/venv3.11/bin/python` | 10 passed, 2 failed in 5.14 s | 1 |
| repo pytest (probe P15), 3.12 | same, fresh venv (`/tmp/w2/rp/repo-copy`) | 10 passed, 2 failed in 1.35 s | 1 |
| fieldkit selftest, venv CLI on PATH (3.12) | `env PATH=/tmp/w2/venv/bin:/usr/bin:/bin python3 ../fk/scripts/selftest.py` (`/tmp/w2/fk-run`) | **29/29 passed** | 0 |
| fieldkit selftest, 3.10 / 3.11 venv on PATH | same with `venv3.10` / `venv3.11` | 29/29 / 29/29 (3.11: the first attempt was killed by the sandbox, exit 137; the rerun passed) | 0 |
| fieldkit selftest, `--python /usr/local/bin/python3` + `PYTHONPATH=src` | `env PYTHONPATH=/tmp/w2/repo-copy/src python3 ../fk/scripts/selftest.py --python /usr/local/bin/python3` | 28/29 (FAIL: the src-layout check, because selftest overwrites `PYTHONPATH`) | 1 |
| reproducible probes | `/tmp/w2/probes.sh <repo> /tmp/w2/rp` | 15/15 matched expectations | 0 |

The two pytest failures, on every interpreter:

```text
FAILED tests/test_cli_smoke.py::test_structure_tolerates_type_like_comments
FAILED tests/test_cli_smoke.py::test_structure_self_index - assert 2 == 0
```

Cause: `ast.parse(..., type_comments=True)` at `src/somnus_debug/structure/core.py:210` rejects the header's `#     type: "source-code"` line (`error: invalid syntax (core.py, line 10)`). See [D-01](../DISCOVERY-LEDGER.md#d-01).

These numbers reconcile with the lanes:

- Lane D got 10 passed, 2 failed with the same two tests.
- Lanes D and F got selftest 29/29, and lane D got 28/29 in the `--python` + `PYTHONPATH=src` mode.

[VERIFIED] [lane D test-coverage.md](../_evidence/agent-findings/lane-d-cli-tests/test-coverage.md); [lane F fieldkit.md](../_evidence/agent-findings/lane-f-ext/fieldkit.md). `STATE.md`'s "smoke 12/12" does not hold for this tree. [DISCREPANCY]

## W2 runs

This section is the run log for this page set. All runs used `PYTHONDONTWRITEBYTECODE=1` with cwd under `/tmp/w2`, and none wrote into the repo. `git status --short` in the repo showed only `?? wiki/` before and after.

`/tmp/w2` was wiped by the sandbox at about 00:40 UTC, between W2-19 and W2-20. W2-20 onward ran on a rebuilt venv (same install command) and on rebuilt, smaller fixtures (`fp/calc` with only `add`; `qs/myproj` with only `parse_count`). Outputs quoted on other pages are tagged with the run that produced them.

| ID | What | Command / setup (abridged) | Exit(s) | Key observation |
|---|---|---|---|---|
| W2-01 | help re-capture from source | `PYTHONPATH=<repo>/src python3 -m somnus_debug.cli [--help/-V/--version/<cmd> --help]` x13, cwd `/tmp/w2/help` | all 0 | all 13 bodies identical to lane D's installed capture (SyntaxWarning lines excluded); a 0-byte `production_doctor.log` appeared in cwd |
| W2-02 | install | `python3 -m venv venv; pip install pytest <repo>` | 0 | 4 `somnus-*` scripts, no harness script; METADATA `Requires-Python >=3.10`, `Requires-Dist: pyyaml`; RECORD listed; standalone usage lines captured |
| W2-03 | repo pytest 3.12 | see headline table | 1 | 10 passed, 2 failed; log written at the copy's root |
| W2-04 | selftest | see headline table | 0; 1 | 29/29; 28/29 in `--python` + `PYTHONPATH=src` mode |
| W2-05 | Python 3.13 without PyYAML | `PYTHONPATH=src /usr/bin/python3 -m somnus_debug.cli doctor --help`; `-m somnus_debug.doctor.core --help`; `-m somnus_debug.structure.core --help`; `-m somnus_debug.doctor.core scan <qs> --no-state` | 1; 0; 0; 1 | dispatcher `ModuleNotFoundError: yaml`; direct modules fine; scan `files=3, issues=7, critical=0, serious=2` |
| W2-06 | 3.10.22 / 3.11.17 matrix | `uv python install 3.10 3.11`; venvs; pytest, doctor fixture scan, structure plain/stamped, selftest | see [compatibility](../02-installation/compatibility.md) | identical results to 3.12; issue tuples equal across versions |
| W2-07 | `-v` / `--verbose` | `doctor scan <qs> --no-state -o out/r.md [ ""/-v/--verbose ]` | 1, 1, 1 | log 0 bytes in all three |
| W2-08 | gates and errors | unquoted `none` -> 4; `"none"` -> 0; `def oops(:` default gate -> 2; with `"minor"` -> 1; `--bogus` -> 2; missing root -> 4 (this case requires `--no-state` or an uncreatable path; with state on a writable missing root exits 0, D-29) | as listed | log appended the two exit-4 renders |
| W2-09 | structure non-UTF-8 | `printf 'x = "caf\xe9"\n' > latin.py; somnus-debug structure latin.py`; `somnus-structure latin.py` | 1; 1 | uncaught `UnicodeDecodeError` traceback |
| W2-10 | quickstart scan, no state | `somnus-debug doctor scan . --no-state` in `qs/myproj` (3 files) | 1 | `files=3, issues=7, critical=0, serious=2`; root has the log plus 2 reports |
| W2-11 | stateful scan | `somnus-debug doctor scan .` | 1 | five `.python_doctor/` files; `Run ID: 20261112T003638Z` |
| W2-12 | JSON shape | Python walk of `production_doctor_report.json`; `od -c` of `started_at` | 0 | key tree in [input-output-contracts](../05-cli-and-tools/input-output-contracts.md); bytes `2026-11-12T00:36:08.553690Z`; score 74 |
| W2-13 | init-config | `doctor init-config -o fp/calc/python_doctor.yaml` | 0 | default YAML captured verbatim |
| W2-14 | first-project loop | scan without and with `PYTHONPATH=src`; baseline; add `evaluate()`; rescan; history; `delta.py` | 1, 0, 1, 0, 1 | `missing_imports` only without `PYTHONPATH`; edge `calc.ops third_party`; delta REGRESSION with 4 new |
| W2-15 | structure | plain file; stamped copy; root script on stamped; doctor on stamped | 0; 2; 0; 1 | `error: invalid syntax (stamped.py, line 9)`; doctor does not crash |
| W2-16 | rollback | `rollback --run-id 20261112T003752Z`; `--run-id NOPE` | 0; 4 | `latest.json` moved, root report did not |
| W2-17 | fix and collision | remove `evaluate`, rescan, `delta --json`; two same-second scans in `probe/coll` | 0; 0; both `Run ID: 20261112T003816Z` | `runs` table holds 1 row |
| W2-18 | pycache-clean | dry run, dry run `--verbose`, real run on `pc/tree` | 0, 0, 0 | dry run deleted nothing; real run removed 1 dir plus 1 file; excluded `node_modules` kept |
| W2-19 | harness | `init-test-harness .`, run; `init-test-harness tools --no-contract`, splice, run; doctor rescan | 0, 1; 0, 0; 1 | root placement wrote `/tmp/w2/hs/test-runs/`; PASS after splice; template adds 9 serious, 8 minor |
| W2-20 | in-process | `cli.main([...])` with a host StreamHandler; `ProjectScanner(...).scan({})` | rc 1 | handlers `['StreamHandler'] -> ['FileHandler']`; library scan clean |
| W2-21 | CI gate script | `gate.sh` on a clean project, a findings project, a missing config | 0, 1, 3 | project root untouched; log in the output dir |
| W2-22 | structure `-o` | `structure app/core.py -o CORE_INDEX.md` | 0 | file written (403 bytes), nothing printed |
| W2-23 | `-o report.json` | `doctor scan <qs> --no-state -o report.json` | 1 | both stdout lines name `report.json`; one file, JSON content |
| W2-24 | fieldkit `--help` | `selftest.py`, `onboard.py`, `delta.py` `--help` | 0, 0, 0 | verbatim help in [command-reference](../05-cli-and-tools/command-reference.md#fieldkit-scripts-skillssomnus-debug-fieldkitscripts) |
| W2-25 | invocation form vs import resolution | project imports `cwdhelper`, which exists only in cwd; console script vs `python -m somnus_debug.cli` | 1; 0 | `missing` vs `third_party` |
| W2-26 | verification step 5 | 32-line header plus a 3-line function; `structure` | 2 | `error: invalid syntax (stamped.py, line 9)` |
| W2-27 | selftest rerun | same as W2-04 | 0 | 29/29; check list captured |
| W2-28 | probe script | [reproducible-probes](reproducible-probes.md) | 0 | 15/15 as expected; repo `git status` unchanged |

Also run: minimal-examples checks in `/tmp/w2/min`. JSON config with gate `"none"` gave exit 0. `python -m somnus_debug.cli --version` gave exit 0. Library calls to `build_index`, `scaffold`, and `ConfigManager` gave exit 0. See [minimal-examples](../03-getting-started/minimal-examples.md).

## What was not verified

This section lists the gaps in this page set's own evidence.

- Editable install (`pip install -e .`), not run to keep the repo read-only.
- PyPI install (lane D downloaded and ran the artifacts but did not `pip install` them).
- Platforms other than Linux aarch64.
- `pycache-clean --follow-symlinks`.
- 3.13 with PyYAML through the dispatcher.

Full list: [untested-behaviors](untested-behaviors.md).

## Sources

This section lists the code and evidence this page draws on.

- `tests/test_cli_smoke.py`; `skills/somnus-debug-fieldkit/scripts/selftest.py`; `STATE.md`
- `src/somnus_debug/structure/core.py:210`
- [lane D test-coverage.md](../_evidence/agent-findings/lane-d-cli-tests/test-coverage.md), [experiment-log.md](../_evidence/agent-findings/lane-d-cli-tests/experiment-log.md); [lane F fieldkit.md](../_evidence/agent-findings/lane-f-ext/fieldkit.md)
