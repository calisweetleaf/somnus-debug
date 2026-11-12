# Lane D: test coverage inventory

## 1. Repo test suite results (VERIFIED)

```
cwd=/tmp/lane-d/repo-copy   (cp -a of the repo, wiki/ removed)
/tmp/lane-d/venv/bin/python -m pytest -q -p no:cacheprovider tests/
......F..F..                                                             [100%]
FAILED tests/test_cli_smoke.py::test_structure_tolerates_type_like_comments
FAILED tests/test_cli_smoke.py::test_structure_self_index - AssertionError: a...
2 failed, 10 passed in 1.10s          exit=1
```

The tests put `REPO_ROOT/src` on `PYTHONPATH` (`tests/test_cli_smoke.py:_run`), so they exercised the copy's **src**, not the venv install.

Both failures have one cause: `src/somnus_debug/structure/core.py:210` still passes `type_comments=True`.
- `test_structure_tolerates_type_like_comments` (`tests/test_cli_smoke.py:138-147`): `error: invalid syntax (header.py, line 3)`, rc 2.
- `test_structure_self_index` (`tests/test_cli_smoke.py:160-165`): `error: invalid syntax (core.py, line 10)`, rc 2. Line 10 is `#     type: "source-code"` in its own metadata header.

STATE.md claims "After: smoke 12/12". **DISCREPANCY**: this zip gives 10/12. The regression test exists, but the src fix it guards does not.

Side effects of running the suite (VERIFIED on the copy): it wrote `production_doctor.log` to the repo root and `__pycache__/` under `src/**` and `tests/`. That matches STATE.md's "Known gaps" note. Running pytest in the real repo would pollute it.

## 2. What the 12 smoke tests cover

| Test | What it proves | Depth |
|---|---|---|
| `test_top_level_help` | dispatcher help, rc 0 | plumbing |
| `test_unknown_command_exits_nonzero` | rc 2 | plumbing |
| `test_structure_help` | structure help text | plumbing |
| `test_doctor_help` | rc 0 only | plumbing |
| `test_doctor_scan_degrades_when_sqlite_state_is_unavailable` | state DB is a directory → warning, rc 0, default report paths in project root | behavior (one path) |
| `test_packaged_default_config_matches_init_config` | packaged yaml == init-config output after header strip | drift guard |
| `test_structure_tolerates_type_like_comments` | header-shaped comments don't crash structure | regression, **FAILS** |
| `test_pycache_clean_help` | rc 0 | plumbing |
| `test_init_test_harness_help` | rc 0 | plumbing |
| `test_structure_self_index` | structure on its own core.py | e2e, **FAILS** |
| `test_init_test_harness_scaffolds_into_tmp` | both files written | behavior |
| `test_init_test_harness_refuses_overwrite_without_force` | rc 1, file untouched | behavior. Contains a no-op assert `... or True` (`assert "hand-edited" not in … or True`); the real check is the next line |

## 3. Fieldkit selftest (`skills/somnus-debug-fieldkit/scripts/selftest.py`)

- **29/29 PASS** against the venv CLI on PATH (F01).
- **28/29** with `--python /usr/local/bin/python3` + `PYTHONPATH=src` (F02c). The src-layout check overwrites `PYTHONPATH`, which is a harness limitation.
- **1/24** with a PyYAML-less interpreter (F02).

It covers:
- the help-flag surface of every (sub)command
- init-config defaults (`*.py`, `.python_doctor`, gate serious)
- exit codes 0, 1, 2, 4
- the log file in CWD and the default report location
- src-layout `missing_imports`; uninstalled third-party `missing_imports`
- silent_failures name sensitivity; abstractmethod-as-stub; property-setter-as-duplicate
- the `test_gaps` never-emitted sentinel; case-insensitive todos
- structure writes nothing by default
- pycache dry-run deletes nothing; path-style excludes ignored
- harness scaffold + refuse-overwrite

**Blind spot:** its structure fixture has no metadata header, so selftest passes while `structure` crashes on every stamped file in this repo.

## 4. Coverage matrix: per command

Legend: **T** = repo pytest, **S** = selftest, **L** = exercised only by this lane, **—** = nothing.

| Behavior | T | S | L |
|---|---|---|---|
| dispatcher help / version / unknown cmd | T | S (version) | L |
| dispatcher PyYAML coupling (doctor unusable without PyYAML) | — | — | L (F02b) |
| doctor scan exit 0 / 1 / 2 | — (only rc 0 in the degrade test) | S | L |
| doctor exit 4 (bad config) | — | S | L (9 distinct causes) |
| doctor exit 5 | — | — | L (D44 RecursionError) |
| gates none / critical / minor / info | — | — | L (minor/info collapse critical → 1) |
| config: JSON, partial, unknown key, malformed YAML silently accepted, no auto-discovery | — | — | L |
| `--no-state`, `-o`, `--json-output` | T (implicit) | S | L |
| state persist, history, rollback, unknown run-id | — | — | L |
| run-id same-second collision overwrite | — | — | L (D13) |
| corrupt state DB: scan degrades; history/rollback → 4 | T (dir-as-DB variant, scan only) | — | L |
| self-check (writes into package dir) | — | — | L |
| production_doctor.log in CWD | — | S | L (stays 0 bytes on success; `-v` no effect) |
| init-config write / refuse / force / default name | T (write) | S | L |
| structure stdout index | T (fails) | S | L |
| structure `-o`, `--update-doc`, `--no-line-numbers`, `--source-label`, `--no-module-functions` | — | flags only | L |
| structure error paths (missing, dir, syntax, mutual exclusion) | — | — | L |
| structure on stamped files | T (fails) | — | L |
| pycache-clean real deletion | — | — | L (P03) |
| pycache-clean dry-run | — | S | L (misleading "Removed/deleted" wording) |
| pycache-clean config errors, missing root exit 0, unknown-key log suppression, max-depth | — | — | L |
| `--follow-symlinks` | — | flag only | — (UNVERIFIED) |
| init-test-harness scaffold / refuse / force / no-contract / mkdir | T | S | L |
| scaffolded run_test.py execution, PROJECT_ROOT default (`<repo>/..`) | — | — | L (H08–H10) |
| root duplicate scripts | — | — | L (help + structure) |
| onboard.py / delta.py | — | — | L (all documented exit codes) |

## 5. Coverage matrix: per doctor detector

| Category | T | S | L (fixture) | Notes |
|---|---|---|---|---|
| syntax_errors | — | S | L | |
| tokenization_errors | — | — | L | Emitted alongside syntax error |
| analysis_read_errors | — | — | L | Inflates `syntax_error_files` |
| missing_imports | — | S | L | Interpreter-dependent; src layout needs PYTHONPATH |
| unused_imports | — | — | L | |
| dependency_cycles | — | — | L | Missed for `from pkg import mod` cycles |
| stubs | — | S | L | Also fires on abstractmethod/Protocol/overload |
| placeholder_returns | — | — | L | **`return 1` flagged (1 == True)** |
| incomplete_methods | — | — | L | Same-file only (SOURCE `_check_abstracts`) |
| suspicious_short_classes | — | — | L | |
| suspicious_short_functions | — | S (incidental) | L | |
| silent_failures | — | S | L | Name-sensitive |
| broad_exceptions | — | — | L | |
| security_risks | — | — | L | Call-name list only; no secret detection |
| test_gaps | — | S (sentinel: not emitted) | L (not emitted) | Configured, never produced |
| todos | — | S | L | All 6 markers |
| missing_docstrings | — | — | L | |
| type_hint_gaps | — | — | L | |
| complexity | — | — | L | |
| duplicate_definitions | — | S | L | Property setter / overload false positives |

**Bottom line:** the repo's pytest suite has no detector logic tests at all. Every detector-level guarantee rests on the fieldkit selftest (8 of 20 categories checked) or on this lane's ad-hoc fixtures. Twelve categories have no automated check anywhere, in either pytest or selftest: `tokenization_errors`, `analysis_read_errors`, `unused_imports`, `dependency_cycles`, `placeholder_returns`, `incomplete_methods`, `suspicious_short_classes`, `broad_exceptions`, `security_risks`, `missing_docstrings`, `type_hint_gaps`, `complexity`. Neither does the whole state/history/rollback subsystem.
