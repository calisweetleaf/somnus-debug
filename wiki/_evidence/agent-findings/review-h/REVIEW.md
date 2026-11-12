# Review H: independent skeptical audit of the somnus-debug wiki

Reviewer: Agent H. Date: 2026-11-11 (America/Chicago), baseline commit `034f46e`. Scope: the full wiki under `forge/somnus-debug/wiki/`, checked against `src/`, `skills/`, `tests/`, and fresh executions.

## Method and environment

- Repo was read-only. `git status --short` showed only `?? wiki/` before and after every run.
- All experiments ran in `/tmp/review-h/` with `PYTHONDONTWRITEBYTECODE=1` and cwd under `/tmp`. They used two venvs:
  - `/tmp/review-h/venv`: `pip install pytest pyyaml <repo>` (non-editable).
  - `/tmp/review-h/nodeps`: `pip install --no-deps <repo>`.
- Source runs used `PYTHONPATH=<repo>/src python3 -m somnus_debug.cli ...`. Python 3.12.15.
- Sandbox display note: the tool display rewrites ISO timestamps into a localized form. The bytes on disk are ISO UTC with `Z`; I checked this by dumping `started_at` with separators replaced. This agrees with the wiki's existing note.

Volume of work:

- 27 DISCOVERY-LEDGER entries re-executed.
- 12 wiki code examples or recipes run verbatim.
- 45 random file:line citations checked, plus about 20 targeted ones.
- 20 random rows of `configuration-registry.tsv` checked.
- All 25 `capability-registry.jsonl` source ranges checked.
- Missed-capability sweep: the AST names, constants, and flags of 9 source files were grepped against the wiki, 367 terms in total.

## (a) Corrections table

Severity:

- **high**: misleads automation or CI into a wrong decision, or contradicts the ledger.
- **med**: a wrong or contradictory fact a careful reader would act on.
- **low**: precision, a citation, or a label.

| id | page | claim as written | problem | correct statement | evidence | sev |
|---|---|---|---|---|---|---|
| H-01 | 05-cli-and-tools/exit-codes.md (matrix row 4 "bad root"; doctor table row "missing or non-directory root ... 4") | missing root gives exit 4 | Unconditional. This contradicts D-29 and 07-internals/fallbacks.md. With state on (the default), a missing writable root is created by `StateStore.initialize()` (`mkdir(parents=True)`), scanned as 0 files, and exits 0. | "Missing root: exit 4 only with `--no-state` or when the path cannot be created. With state on, a writable missing root is created and the 0-file scan exits 0 (D-29)." | `core.py:1927-1932`, `:2068-2070`, `:967-972`. Ran `doctor scan ./typo_root -o r.md` -> exit 0, `typo_root/.python_doctor/` created. `--no-state` -> exit 4 "Project root does not exist." | **high** |
| H-02 | 05-cli-and-tools/options-and-flags.md:22 | `project_root` "must be an existing directory, else exit 4" | Same contradiction as H-01 | "must exist with `--no-state`; with state on, a missing writable path is created and scanned empty (exit 0, D-29)" | same as H-01 | **high** |
| H-03 | _evidence/command-observations.md (doctor scan, col 4) | "config, path, or state error" -> 4 | "path" is conditional (H-01). "State error" is wrong for `scan`, which warns and continues stateless, so the gate decides the exit. Only history and rollback exit 4 on a broken DB (D-28). | "config error; missing root only with `--no-state`; unwritable report path" | Ran a garbage `state.sqlite3` scan -> stderr warning, exit 2 (critical present). `history` on the same root -> 4. `core.py:2068-2077` | med |
| H-04 | 05-cli-and-tools/input-output-contracts.md:46; 11-verification/verification-results.md W2-08 row | "W2-08 (missing root ...)"; "missing root -> 4" | The run's `--no-state` condition is not recorded, so readers generalize it | Record that W2-08's missing-root case needs `--no-state` (or was an uncreatable path), and link D-29 | same as H-01 | med |
| H-05 | 05-cli-and-tools/exit-codes.md:62 | malformed YAML config: "not detected; the scan runs on defaults and exits by the gate" | Overgeneralized from one input (`schema_version: [`). Structural errors raise `ConfigurationError`, exit 4: bad indentation, a line without a colon, mixed list/map, a missing child block. Flow-ish garbage is not replaced by defaults. It is kept as a literal string and then either passes a `str` key or fails validation (exit 4). | "Structural YAML errors exit 4. Unbalanced flow or quote syntax is read as a literal string, so `str` keys accept it silently and int, bool, and list keys fail with exit 4. Defaults are not substituted." | `core.py:681-723`, `:619-643`. Ran `-c` with `max_workers: 2\n  bad_indent: 3` -> 4 "Unexpected indentation."; `just a string line` -> 4 "Expected key followed by colon."; `key: [unclosed` -> 0; `a: "unterminated` -> 0 | med |
| H-06 | DISCOVERY-LEDGER.md D-07, line 104 | "`silent_failures` accepts only handlers whose call names are spelled `logging.*`/`logger.*`" | Overstates what counts as logging. Only `logging.error`, `logging.exception`, `logger.error`, `logger.exception` (or any `raise`) clear the flag. `logger.warning(...)`, `logging.critical(...)`, `logger.critical(...)` are counted silent. functions.md has it right, so the two pages contradict. | "accepts only `raise` or a call spelled exactly `logging.error/exception` or `logger.error/exception`; `logger.warning`, `*.critical`, `self.log.error`, `log.exception` all count as silent" | `core.py:1486-1488`. Ran a handler with `logger.warning(...); return -2` -> `silent_failures` at line 14 | med |
| H-07 | 10-agent-usage/automation-contracts.md (exit table, `structure` row, col 1) | "—" (no exit 1) | Contradicts exit-codes.md and D-34: a non-UTF-8 source raises an uncaught `UnicodeDecodeError`, exit 1 | `structure` exit 1 = uncaught exception, for example a non-UTF-8 source | Ran `structure bad.py` (bytes `\xff\xfe`) -> exit 1, `UnicodeDecodeError`; `structure/core.py:326-334` catches only `OSError, SyntaxError` | med |
| H-08 | _evidence/capability-registry.jsonl CAP-DOCTOR-GATE (and generated CAPABILITY-ATLAS) | sources `core.py:477`, `core.py:2100-2130` | 2100-2130 is `run_init_config`/`run_history`/`run_rollback`/`run_self_check`. The gate function is elsewhere. | `core.py:477` (default gate), `core.py:2046-2058` (`exit_code_for_summary`), `core.py:819-820` (validation) | `sed -n 2046,2058p` | med |
| H-09 | capability-registry.jsonl CAP-STRUCTURE-LIB; CAPABILITY-ATLAS "Library" table | exposure "internal", invocation `from somnus_debug.structure.core import build_index` | `build_index` is a package export (`structure/__init__.py` `__all__ = ["build_index", "main"]`), so by the atlas's own definition it is `public`. public-api.md calls it "the only exported library function". The exposure labels contradict each other. | exposure `public` (package export); invocation `from somnus_debug.structure import build_index` | `src/somnus_debug/structure/__init__.py:39-43` | med |
| H-10 | Many pages (about 218 `[VERIFIED ... W3 ...]` tags; about 150 `/tmp/w1/...` references) | VERIFIED via W3 probe IDs (E1-E10, G*, M*, H*, P*, OB*, R*) and W1 scripts (`/tmp/w1/ex_api.py`, `ex_state.py`, `ex_serial.py`, ...) | No retained record: neither the scripts nor a W1/W3 run table with command, cwd, exit, and output exist in the wiki (verification-results.md has a table only for W2). /tmp was wiped. Under the BRIEF's definition these are VERIFIED claims without recorded execution. I re-ran a sample and every one held (see section e). | Add W1 and W3 run tables (command, cwd, exit, key output) to verification-results.md, or archive the probe scripts under `_evidence/`, or relabel the unreproduced ones as SOURCE-CONFIRMED with "executed, record lost" | `grep -rl ex_api.py wiki` gives 11 referencing pages and 0 copies; `grep -n W3 11-verification/verification-results.md` gives 0 hits | med |
| H-11 | capability-registry.jsonl CAP-DOCTOR-INITCFG | source `core.py:885-930` | `default_yaml()` spans 853-923. 924-930 is `ProjectFileIndex`. | `core.py:853-923`, `:2096-2103`, `:2142-2145` | sed | low |
| H-12 | capability-registry.jsonl CAP-DOCTOR-JSONCFG; CAPABILITY-ATLAS | source `core.py:801`; verification SOURCE-CONFIRMED | Off by one: the JSON branch is 802-811. The label is stale: precedence.md already has [VERIFIED W3 E6a], and I verified it. | `core.py:802-811`; VERIFIED | `-c gate-none.json` -> exit 0, `cm.config.severity_exit_level == "none"` | low |
| H-13 | 01-system/state-and-persistence.md:22 and Sources | defaults `state_dir/reports_dir/report_basename` at `core.py:494-496` | 494-496 are the severity entries `todos`/`missing_docstrings`/`suspicious_short_functions` | `core.py:474-476` | sed | low |
| H-14 | DISCOVERY-LEDGER.md D-14, line 188 | "one unknown key raises inside setup and silences later logging" | Nothing raises. `from_yaml` calls `logging.warning` before `setup_logging`, so the root logger is implicitly configured (stderr, WARNING). The later `basicConfig` is then a no-op. Other pages (lifecycle, pitfalls, fallbacks) describe this correctly. | "one unknown key triggers a pre-setup `logging.warning` that implicitly configures the root logger at WARNING; the later `basicConfig` is a no-op, so INFO, the summary, `--verbose`, and `log_file` are lost" | `pycache_cleaner/core.py:175-179`, `:334`, `:355-365`. Ran a config with `bogus: 1` + `--verbose` -> only `WARNING:root:Ignoring unknown config key 'bogus'`, exit 0 | low |
| H-15 | 06-configuration/precedence.md:108 | `--max-depth 0` -> "0 (root-level files only)" | Root-level target **directories** are deleted too, because they are handled before the depth check of their children | "only the root itself: its matching files and its direct `__pycache__`-style target dirs" | `pycache_cleaner/core.py:233-244`. `--max-depth 0` dry run on root with `a.pyc` + `__pycache__/` -> "deleted 1 directories, 1 files" | low |
| H-16 | 05-cli-and-tools/input-output-contracts.md:136 | `markdown_include_css: false` "block is meant to be omitted ... [UNVERIFIED]" | Now verified, with a nuance: the `<style>` block is omitted, but the HTML terminal `<div class="t">` banner is still emitted (as implementation-notes says) | "[VERIFIED review-h] `false` drops `<style>`; the `<div class=\"t\">` terminal block remains" | `grep -c '<style>'` 0 vs 1; `grep -c '<div class="t"'` 1 in both | low |
| H-17 | 03-getting-started/minimal-examples.md (JSON-config block and Python block outputs) | names fixture `/tmp/w2/qs/myproj`; output `files=2, issues=2, critical=0, serious=1`; last index lines `parse_count` | Those outputs came from the rebuilt post-wipe fixture (verification-results: "`qs/myproj` with only `parse_count`"), not the quickstart fixture the page names. On the quickstart fixture you get `files=2, issues=6, critical=0, serious=2` and `export_report`. | Say the outputs are from the reduced W2-20+ fixture, or re-run on the quickstart fixture and update the numbers | Ran both blocks on the exact quickstart fixture | low |
| H-18 | 09-recipes/programmatic/inprocess-main-isolated.md | "Executed result" shows `handlers before/during/after`, `main() returned 1`, `host: ...`, `cwd log here` | The page's snippet prints none of those lines. That output is from `_repro/inprocess_main.py`, which has extra prints. The snippet itself prints only doctor's 3 stdout lines. | Label the output as `_repro/inprocess_main.py`, or add the print lines to the snippet | Ran the extracted snippet (3 lines, exit 0) and the repro script (matches the page) | low |
| H-19 | 04-library-api/public-api.md:212 | `scaffold -> ['sc/repo/single_test/run_test.py', ...]` | `scaffold()` returns absolute `PosixPath` objects. The shown output is relativized/stringified, and that is not stated. | `[PosixPath('/abs/.../sc/repo/single_test/run_test.py'), PosixPath('/abs/.../CONTRACT.md')]` | ran the snippet | low |
| H-20 | DISCOVERY-LEDGER.md D-34 (onboard bullet) | "only the five profile files are never overwritten, `onboard.py:518-520`" | 518-520 is the `--baseline` branch. Non-overwrite is `write_new` at `onboard.py:415-422`, called at `:495-501` and `:515-516`. | cite `onboard.py:415-422,495-501,515-516` (no-overwrite) and `:518-520` (baseline rewrite) | sed | low |
| H-21 | _evidence/configuration-registry.tsv row "root duplicate python_production_doctor.py" | `python_production_doctor.py:81,2130-2162` | The root file is 11 lines shorter after the scan-fallback block. Its parser is `2119-2151`. | `python_production_doctor.py:81,2119-2151` | `grep -n "def build_parser" python_production_doctor.py` -> 2119 | low |
| H-22 | 05-cli-and-tools/exit-codes.md Sources / table | `:2189-2201` | `main()` ends at 2199 | `:2184-2199` | sed | low |

## (b) Missed-capability list

The wiki is unusually complete. Of 367 source names, flags, and constants, 30 have no wiki mention, and all but those listed below are private helpers inside the fieldkit scripts or cargo flags inside the harness template. These behaviors are absent or only implied:

1. **Negative `max_depth` / `--max-depth -1` makes pycache-clean a silent no-op.** The root itself is skipped by the depth check, it still logs `Summary: deleted 0`, and exits 0. [VERIFIED] dry run with `--max-depth -1` gave "deleted 0 directories, 0 files". `pycache_cleaner/core.py:233-234`. Not in any page.
2. **`doctor self-check` rejects `-v/--verbose`** (argparse exit 2). Only `scan` declares the flag (`core.py:2140` vs `:2156-2160`). options-and-flags.md lists the self-check flags without saying `-v` is an error. [VERIFIED] exit 2.
3. **`--max-depth 0` also deletes root-level target dirs** (see H-15). This is a precision gap, not a missing capability.
4. Fieldkit internals with no mention, all private and low value: `delta.py` `InputError`, `load_report`, `load_dispositions`, `multiset_diff`, `as_json`; `onboard.py` `EXIT_MEANING`, `NATIVE_GATE_FILES`, `TEST_DIR_NAMES`, `git_ignored_dirs`, `write_new`, `doctor_config_text`, `pycache_config_text`, `profile_text`; `selftest.py` `check_*` functions. `onboard.py`'s `NATIVE_GATE_FILES`/`TEST_DIR_NAMES` drive what the survey reports, so a one-line mention in the onboarding page would close the gap.

Checked and found **already documented**:

- `-v` vs `--verbose` (`:2186`)
- the SyntaxWarning at `pycache_cleaner/core.py:64`
- the `SECURITY_CALLS` alias evasion (`from subprocess import run`)
- case-insensitive TODO markers
- `ignore_classes` scope
- the `import pkg.ghost` parent-prefix masking (registries-and-discovery.md:63-64)
- `syntax_error_files` counting read errors
- `incomplete_methods` name collisions
- `history --limit 0/-1`
- an absolute `state_dir`
- dynamic-import records
- the PYTHONPATH/`find_spec` dependence
- the skills being absent from the wheel

## (c) Contradictions list

| # | Pages | Contradiction | Which is right |
|---|---|---|---|
| C-1 | exit-codes.md (rows 4, 61), options-and-flags.md:22, input-output-contracts.md:46, verification-results.md W2-08, command-observations.md vs DISCOVERY-LEDGER D-29, 07-internals/fallbacks.md:12, implementation-notes.md:14, initialization.md:53 | missing root gives 4 vs missing root gives 0 when state is on | D-29 (re-verified). See H-01 through H-04. |
| C-2 | command-observations.md ("state error" -> 4 for scan) vs D-28, state-and-persistence.md:109, exit-codes.md ("state DB unusable during scan: warning, gate result") | scan exit on a broken state DB | D-28: scan falls back; only history and rollback exit 4 |
| C-3 | automation-contracts.md (`structure` exit 1 = —) vs exit-codes.md, D-34, command-observations.md | structure exit 1 | exit 1 exists (non-UTF-8) |
| C-4 | DISCOVERY-LEDGER D-07 ("`logging.*`/`logger.*`") vs 04-library-api/functions.md (handler_is_silent: only `.error`/`.exception`) | which logging calls clear `silent_failures` | functions.md (re-verified with `logger.warning`) |
| C-5 | DISCOVERY-LEDGER D-14 ("raises inside setup") vs lifecycle.md:64, configuration-pitfalls.md:53, fallbacks.md:51 (a pre-setup warning) | mechanism of the unknown-key logging loss | the warning mechanism |
| C-6 | CAPABILITY-ATLAS / registry CAP-STRUCTURE-LIB "internal" vs public-api.md ("exported"), `structure/__init__.py` `__all__` | exposure of `build_index` | public (package export) |
| C-7 | CAPABILITY-ATLAS CAP-DOCTOR-JSONCFG "SOURCE-CONFIRMED" vs precedence.md "[VERIFIED W3 E6a]" | verification class of JSON configs | VERIFIED |
| C-8 | exit-codes.md:62 ("malformed YAML not detected") vs 06-configuration/file-based-configuration.md and D-04 (the parser raises on structural errors) | malformed YAML handling | structural errors exit 4 (H-05) |

I found no contradiction in doctor's gate semantics, default values, or default severities across pages. They all match `core.py:451-502`, `:2046-2058`.

## (d) Examples and recipes run (verbatim, in /tmp/review-h)

| # | Source page / block | Result vs page |
|---|---|---|
| 1 | 03-getting-started/quickstart.md step 2-3 (fixture + `doctor scan . --no-state`) | **match**: `files=3, issues=7, critical=0, serious=2`, exit 1. Same 7 findings and lines; score 74. |
| 2 | quickstart step 4 (stateful scan + history) | **match**: Run ID line present; history lists the run |
| 3 | quickstart step 5 (structure plain / stamped / root duplicate / doctor on stamped / `-o`) | **match**: 0 / 2 (`invalid syntax (stamped.py, line 9)`) / 0 / doctor exit 1 with 6 issues / `-o` prints nothing |
| 4 | quickstart step 6 (pycache-clean dry run then real) | **match**: "deleted 1 directories, 1 files" both times; `node_modules/x/__pycache__` and `keep.py` kept |
| 5 | quickstart step 7 (`init-test-harness .` + `run_test.py`) | **match**: FAIL, exit 1, manifest under `<parent>/test-runs/` |
| 6 | 04-library-api/public-api.md `build_index` block | **match**: 3 classes (1 top, 2 nested), 2 definitions, `LI` rendered twice, SyntaxError on the type-comment line. Extra check: with a method in `LI`, definitions = 3 (double count). |
| 7 | public-api.md pycache library block | **match**: `1 1 15`, roots made absolute |
| 8 | public-api.md `scaffold` block | **match** in behavior; the displayed return value is relativized (H-19) |
| 9 | 04-library-api/functions.md predicates block | **match**: `5 1 True` / `True` |
| 10 | 09-recipes/programmatic/embedded-scan.md | **match**: no new paths, `root handlers: []`, no cwd log, gate -> 1 |
| 11 | 09-recipes/programmatic/index-stamped-file.md | **match**: plain SyntaxError line 9; blanked index puts `scaffold` at 62-88 |
| 12 | 09-recipes/programmatic/inprocess-main-isolated.md | snippet works (exit 0, reports written) but prints only 3 lines; the page's output belongs to `_repro/inprocess_main.py` (H-18) |
| 13 | 09-recipes/automation/ci-delta-gate.md (after `onboard.py --apply --baseline`) | **match**: clean -> 0; added `os.system` -> REGRESSION, exit 1; `severity_exit_level: "bogus"` -> doctor 4, gate 3 |
| 14 | 03-getting-started/minimal-examples.md JSON-config block + Python block | runs; **numbers differ** on the named fixture (H-17) |
| 15 | 11-verification/reproducible-probes.md probe script | **15/15 match** (P1-P14 + pytest 10 passed / 2 failed); repo `git status` unchanged |

## (e) Claims checked and confirmed

**Ledger re-executions (27).** Each result is [VERIFIED review-h], with the command and exit recorded in this lane's working notes. Here are the key results:

- **D-01**: `structure src/somnus_debug/cli.py` exit 2; the root duplicate exits 0. Pytest on a /tmp copy: 10 passed, 2 failed (`test_structure_tolerates_type_like_comments`, `test_structure_self_index`).
- **D-02**: `"none"` in the project's `python_doctor.yaml` without `-c` gives 1; with `-c` gives 0.
- **D-03**: unquoted `none` gives 4 "must be a non-empty string"; `info` is accepted.
- **D-04**: the parser diverges from PyYAML on 7 of 8 inputs (`x#y`, `["a,b"]`, `'it''s'`, `{}`, quoted key, BOM, `010`). Duplicate keys: last wins.
- **D-05**: `detect_test_gaps: false` gives an identical summary; the field is only defined, defaulted, and validated (grep).
- **D-06**: the `from pkg import x` cycle gives 0 cycles, exit 0; the `import pkg.x` cycle gives 1, exit 1. `from . import ghost` and `import pkg.phantom` are both classed `local` -> `pkg/__init__.py`.
- **D-07**, all six sub-claims re-observed:
  - `__future__` reported as an unused import;
  - frozen dataclass flagged short;
  - `@abstractmethod` `...` flagged as a stub;
  - property setter flagged as a duplicate;
  - `return 1` flagged as a placeholder;
  - `log.exception` handler counted silent.
- **D-08**: two in-process scans in the same second share one run_id; the `runs` table has 1 row.
- **D-09**: rollback moves only the alias and `latest.*`; an unknown ID gives 4.
- **D-10**: `--help` creates `production_doctor.log`. `history` on a missing path creates `.python_doctor/`. Read-only package copy: `self-check` gives 4; with `-o` it gives 1 plus a fallback warning.
- **D-11**: after `main()`, root handlers are `[FileHandler production_doctor.log]`.
- **D-12**: `ProjectScanner(...).scan({})` writes no files and keeps the host handler.
- **D-13**: `--no-deps` venv: `somnus-debug doctor --help` gives 1 (`No module named 'yaml'`); `somnus-doctor --help` and `somnus-structure --help` give 0.
- **D-14**:
  - scalar `roots` normalizes to include `/`;
  - `dry_run: no` loads as False (a live delete);
  - `"false"` is truthy;
  - `exclude: ["node_modules/*"]` does not match;
  - a missing root exits 0;
  - dry run with `--verbose` logs "Removed";
  - an unknown key silences INFO (wording issue: H-14).
- **D-15**: scaffolded at the root, artifacts land in `../test-runs/`; FAIL, exit 1.
- **D-16**: `check_nested_functions: false` and `ignore_functions: [outer]` both hide `eval` in the nested function.
- **D-17**: `pkg/env/e.py` not scanned; `src/**/*.py` matched nothing; `include_patterns: []` scanned 0 files, exit 0.
- **D-18**:
  - RecursionError, one file: exit 5;
  - two files: `analysis_read_errors`, exit 2;
  - unknown command: 2;
  - `--bogus`: 2.
- **D-24**: nested-in-nested class rendered twice and counted twice.
- **D-25**: `-o rep.json` leaves one file, with JSON content.
- **D-28**: garbage `state.sqlite3`: scan warns and exits 2 (critical present); `history` gives 4.
- **D-29**: missing root (stateful) is created and exits 0; `--no-state` gives 4.
- **D-30**: `eval` in `__repr__` not reported under defaults; `eval` in `run` is.
- **D-31**: `targets: ["*.bak"]` counts the `.bak` file.
- **D-33**: library JSON equals CLI JSON except timestamps (run_id equal in the same second).
- **D-34**: `structure` on a non-UTF-8 file gives exit 1, `UnicodeDecodeError`.

Not re-executed (left as the lanes recorded them): D-19, D-20, D-21, D-22, D-23, D-26, D-27, D-32. D-20 and D-34's onboard bullets were checked against source (`onboard.py:240`, `:405`, `:495-520`), and the source agrees.

**Other confirmed claims.**

- `exit_code_for_summary` quoted verbatim (`core.py:2046-2058`).
- `DoctorConfig` is frozen with 29 fields. Field counts: `SummaryCounts` 12, `FileMetrics` 13, `DiagnosticIssue` 10, `FunctionDiagnostic` 12, `ClassDiagnostic` 12.
- The JSON report key tree in input-output-contracts.md matches a fresh report at every level, including `functions[]` and `imports[]` (via dataclass fields). The score formula and the value 74 are right.
- SQLite DDL is verbatim (`sqlite_master` on a live DB), and `journal_mode` is `wal`. `write_text_atomic` and `copy_file_atomic` use a fixed `.<name>.tmp` name.
- `normalize_argv` behavior. `-v` has no effect; `--verbose` gives a 0-byte log.
- `self-check` on the installed package gives `files=2`, `serious=17`, exit 1.
- `history --limit 0` gives "No recorded runs found."; `--limit -1` lists all.
- `max_report_evidence_lines: 1` gives a 1-line evidence. An absolute `state_dir` is honored.
- `init-config` output has no `#` lines; a second `init-config` without `--force` gives 4.
- A JSON config gate `"none"` works.
- `ignore_classes` covers only class-level findings.
- TODO patterns are case-insensitive and comment-only.
- `SECURITY_CALLS` is matched by exact dotted name.
- Dispatcher passthrough is `cli.py:99-104`; pycache-clean returning `None` maps to 0.
- The wheel RECORD has no `skills/`. MANUAL §8 names `ProjectScanner`, `ConfigManager`, and `DoctorConfig`, which justifies their "documented" status on public-api.md.
- defaults.md values: every in-code default matches `core.py:451-502` and `CleanerConfig` `:160-167`. Also checked: `onboard.py:149`/`:156`/`:230` (600 s and 60 s timeouts), `:288`, `:454`; `delta.py:143`, `:252`; `selftest.py:322-330`.
- precedence.md: no auto-discovery, list replacement vs per-category mapping merge, CLI pycache flags only able to set True, `-o`/`-c` resolved against cwd. History/rollback config coupling: confirmed in source (`:2108`, `:2115`).
- configuration-registry.tsv, 20 random rows (seed 7). All defined_at/read_at lines and defaults are correct except one (H-21): `--update-doc`, `detect_unused_imports`, `init-config -o`, `self-check`, `min_docstring_length`, `SCHEMA_VERSION`, `history --limit`, selftest `--python`, root `python_doctor.yaml`, `--json-output`, `min_function_lines`, `--apply`, structure source encoding, history/rollback coupling, `RUN_ID_FORMAT`, `min_class_lines`, `run_test.py` argv, `rollback --run-id`, `check_private_functions`.
- 45 random file:line citations (seed 42, from 1161 explicit `file.py:N` citations): all 45 point at the claimed code. The citation errors I found came from targeted checks: H-08, H-11, H-12, H-13, H-20, H-21, H-22.
- capability-registry.jsonl, all 25 entries: ranges are correct or acceptably loose, except CAP-DOCTOR-GATE (H-08), CAP-DOCTOR-INITCFG (H-11), and CAP-DOCTOR-JSONCFG (H-12).

## (f) Verdict on certification

**Coverage cannot be certified yet. It is close.** Breadth is excellent: the missed-capability sweep found only two minor behaviors, and every ledger finding I re-ran reproduced. Four things block certification:

1. **H-01 through H-04 (high/med).** Five pages state that a missing root exits 4 with no condition, while the ledger's own D-29 says the stateful default exits 0. That is the kind of error that makes a CI gate silently pass, so it must be fixed before the exit-code pages can be relied on.
2. **H-05, H-06, H-07 (med).** Three more wrong or contradictory facts in machine-facing tables and the ledger.
3. **H-10 (med, epistemic).** About 370 VERIFIED tags rest on W1 and W3 probes with no retained command, exit, or output record. My sample re-runs all held, but the BRIEF's definition of VERIFIED is not met for those tags as written. Either add W1/W3 run tables, or archive the probe scripts, or relabel.
4. **Exposure labels (H-09, C-6).** They must be made consistent so the public/internal API boundary is unambiguous.

The low-severity items (H-11 through H-22) can be fixed in the same pass, but none of them blocks certification.

Not covered by this review:

- the fieldkit `delta.py` edge cases (D-21) and `onboard.py --python` symlink behavior (D-20);
- the Python 3.10, 3.11, and 3.13 matrix;
- the PyPI diff (D-23);
- the parallel-scan race (D-32).

I took these from the lanes' records without re-execution.
