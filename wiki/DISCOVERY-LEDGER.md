# Discovery Ledger

This ledger records findings that change what a reader should believe about somnus-debug 0.1.0, as investigated on 2026-11-11 against the uploaded tree (baseline commit `034f46e`). Ordinary documented behavior is not listed here; it lives in the reference sections.

Evidence classes: VERIFIED (executed in a controlled /tmp environment), SOURCE-CONFIRMED (read in source, not exercised), DISCREPANCY (sources disagree), CONDITIONAL, UNVERIFIED, HYPOTHESIS. Line numbers refer to `src/somnus_debug/` at `034f46e` unless a file is named.

Categories: 1 undocumented working capability, 2 hidden configuration, 3 unexpected default or implicit behavior, 4 useful programmatic API, 5 overlooked extension point, 6 unexpected interaction, 7 doc/implementation discrepancy, 8 unreachable or incomplete implementation, 9 operational constraint or failure mode, 10 research direction.

## Executive summary

This section names the findings that matter most, in the order an operator should act on them.

1. **The `structure` tool crashes on every metadata-stamped Python file, including its own source, in the shipped package** (D-01). STATE.md records the fix as done on 2026-11-05, but the fix exists only in the root duplicate `analyze_python_structure.py`. Source, installed wheel, and PyPI 0.1.0 all fail; the repo's own smoke suite is 10 passed / 2 failed, not the 12/12 STATE.md claims.
2. **Doctor's import graph is blind to the most common cycle spelling** (D-06, D-22). `from pkg import mod` resolves to `pkg/__init__.py`, so cycles written that way and missing sibling modules are not reported. In src-layout projects onboarded with `PYTHONPATH=src`, own imports are classed third-party and `dependency_cycles` stays 0.
3. **Doctor's configuration is quieter than the docs imply** (D-02, D-03, D-04, D-05, D-16). No config file is auto-discovered; unquoted `none` is null; the bundled YAML subset parser mis-parses several common forms without error; unknown keys and typos are accepted silently; `detect_test_gaps` does nothing; `ignore_functions` hides security findings.
4. **pycache-clean has a whole-filesystem hazard** (D-14). A scalar `roots: /path` is iterated character by character and normalizes to include `/`. `dry_run: no` deletes. Never verified live (deliberately).
5. **History is lossy and rollback is partial** (D-08, D-09). Two scans in the same second overwrite one another; rollback moves only the `latest` alias.
6. **Embedding doctor in another program is possible and clean if you avoid `main()`** (D-12, D-11). `ProjectScanner(root, ConfigManager(None)).scan({})` returns a structured result with no disk or logging side effects; `main()` replaces the host's logging handlers.
7. **There is no extension API**, but doctor JSON plus the fieldkit `delta.py` gate already form a working CI ratchet (D-19, D-27), with known holes (D-21).

Zero findings were manufactured to fill categories; categories 1 and 5 are thin because the package exposes few hidden surfaces.

<a id="d-01"></a>

## D-01: structure crashes on metadata-stamped files; fix exists only in the root duplicate

This entry records the most consequential regression in the shipped package.

Resolution (discovery-fixes patch, see `TASK.md`): DONE T-20.

- **Category:** 7, 9.
- **What:** `structure/core.py:210` calls `ast.parse(source, filename=..., type_comments=True)`. Every Somnus file carries a header line such as `#   type: "source-code"`, which the parser reads as a PEP 484 type comment in an invalid position and raises `SyntaxError`. The root `analyze_python_structure.py:210` drops the flag and works.
- **Why it matters:** `somnus-debug structure` cannot index any file in this repository or any Somnus repo stamped with somnus-metadata. STATE.md ("Verified 2026-11-05") says the fix landed in `src/somnus_debug/structure/core.py`; in this upload it did not. Smoke tests `test_structure_tolerates_type_like_comments` and `test_structure_self_index` fail.
- **Found by:** lead diff of root duplicates vs `src/` (Wave 0); confirmed by lanes A, B, D.
- **Evidence:** [VERIFIED] `somnus-debug structure src/somnus_debug/cli.py` exits 2, `invalid syntax (cli.py, line 9)`; root script on the same file exits 0. Pytest on a /tmp copy: 10 passed, 2 failed. PyPI 0.1.0 has no headers, so it does not crash on its own files, but it carries the same `type_comments=True` line and crashes on any stamped file. See [lane D experiment log](_evidence/agent-findings/lane-d-cli-tests/experiment-log.md), [lane A architecture](_evidence/agent-findings/lane-a-arch-api/architecture.md).
- **Reproduce:** `PYTHONPATH=src python3 -m somnus_debug.cli structure src/somnus_debug/cli.py; echo $?` from a /tmp cwd.
- **Restrictions:** files without `# type:`-shaped comments are unaffected. The fieldkit `selftest.py` misses this because its structure probe uses an unstamped file.
- **Related:** D-24. **Docs:** [command reference](05-cli-and-tools/command-reference.md), [implementation discrepancies](12-discoveries/implementation-discrepancies.md).

<a id="d-02"></a>

## D-02: doctor never auto-loads a configuration file

This entry corrects the README and quickstart impression that `python_doctor.yaml` is picked up automatically.

Resolution (discovery-fixes patch, see `TASK.md`): DECISION T-50 (docs updated in T-40).

- **Category:** 3, 7.
- **What:** `ConfigManager._load_raw` returns built-in defaults when `config_path is None` (`doctor/core.py:797-799`); `run_scan` passes a path only when `-c/--config` is given (`:2063`). `DEFAULT_CONFIG_NAME = "python_doctor.yaml"` (`:81`) is used by `init-config` as the write target, not for discovery.
- **Why it matters:** a project-local `python_doctor.yaml` is silently ignored unless every invocation passes `-c`. The repo-root `python_doctor.yaml` is read by nothing.
- **Evidence:** [VERIFIED] lane B: a config with `severity_exit_level: "none"` in the scanned folder gave exit 1 without `-c` and exit 0 with it.
- **Reproduce:** see [configuration recipes](06-configuration/configuration-recipes.md).
- **Related:** D-03, D-04, D-23. **Docs:** [precedence](06-configuration/precedence.md).

<a id="d-03"></a>

## D-03: unquoted `severity_exit_level: none` is null and exits 4; the `none` and `info` gates are undocumented

This entry records a gate value that only works when quoted.

Resolution (discovery-fixes patch, see `TASK.md`): DONE T-02.

- **Category:** 2, 9.
- **What:** the bundled YAML parser maps bare `none` (and `null`, `~`) to Python `None`, which fails gate validation with a configuration error. Quoted `"none"` disables the gate; `info` is also accepted. Neither value appears in README or MANUAL.
- **Evidence:** [VERIFIED] lanes A and B: unquoted `none` exit 4; `"none"` exit 0; `critical` with a critical finding exit 2.
- **Related:** D-04, D-18. **Docs:** [configuration pitfalls](06-configuration/configuration-pitfalls.md).

<a id="d-04"></a>

## D-04: doctor's YAML subset parser mis-parses common forms and accepts unknown keys silently

This entry documents the zero-dependency parser's contract where it diverges from YAML.

Resolution (discovery-fixes patch, see `TASK.md`): DONE T-03.

- **Category:** 3, 9.
- **What:** lane B compared 48 inputs against PyYAML. Silent divergences include `x#y` truncated to `x`, `["a,b"]` split inside quotes, `'it''s'` read as `its`, `{}` read as a string (so `severity_levels: {}` fails), quoted keys keep their quotes, a BOM corrupts the first key, `010` becomes 10. Unknown top-level keys and unknown severity categories are accepted with no warning, so `detect_silent_failure: false` (typo) does nothing.
- **Evidence:** [VERIFIED] [`yaml_probe.out`](_evidence/agent-findings/lane-b-config/experiments/yaml_probe.out). JSON configs (`.json` suffix) bypass this parser (`:801`) [SOURCE-CONFIRMED].
- **Use:** prefer a `.json` config file, or keep YAML to plain `key: value`, unquoted-safe scalars, and one-level lists.
- **Docs:** [file-based configuration](06-configuration/file-based-configuration.md).

<a id="d-05"></a>

## D-05: `test_gaps` is configured, validated, and never emitted

This entry records a configured category with no producer.

Resolution (discovery-fixes patch, see `TASK.md`): DECISION T-51.

- **Category:** 8, 7.
- **What:** `detect_test_gaps` is a config field (`:229`, default `True` at `:470`), validated (`:840`), with severity `serious` (`:493`), but no code reads it or emits `test_gaps`. MANUAL lists test gaps as reported.
- **Evidence:** [VERIFIED] setting it false changes nothing (lane B); 19 of 20 categories have an emitter (lane A map). `selftest.py` holds a sentinel that fails once it is emitted.
- **Docs:** [unreachable implementations in implementation-discrepancies](12-discoveries/implementation-discrepancies.md).

<a id="d-06"></a>

## D-06: `from pkg import mod` resolves to `pkg/__init__.py`, hiding cycles and missing modules

This entry records the import-resolution gap behind missed cycles.

Resolution (discovery-fixes patch, see `TASK.md`): DONE T-04.

- **Category:** 9.
- **What:** `ImportResolver._resolve_local` returns the exact module match first (`:1034-1036`); for `from pkg import b` the exact match is `pkg/__init__.py`, so the child `pkg/b.py` is never considered. `from . import ghost` likewise resolves to the package and counts as resolved.
- **Evidence:** [VERIFIED] lane A: an a/b cycle written with `from pkg import X` scored 0 issues, exit 0; the same cycle written `import pkg.a` / `import pkg.b` is detected, exit 1. Lane F reproduced in a src-layout repo.
- **Related:** D-22, D-26.

<a id="d-07"></a>

## D-07: detector false positives with deterministic triggers

This entry collects detector behaviors that operators will meet as noise.

Resolution (discovery-fixes patch, see `TASK.md`): DONE T-05.

- **Category:** 9.
- **What, all [VERIFIED] on fixtures (lanes A, D, F):**
  - `silent_failures` is cleared only by a `raise` or a call spelled exactly `logging.error`, `logging.exception`, `logger.error` or `logger.exception` (`src/somnus_debug/doctor/core.py:1486-1488`); `logger.warning`, `*.critical`, `self.log.error`, and `log.exception` all count as silent.
  - `stubs` flags `@abstractmethod`, `Protocol`, and `@overload` bodies.
  - `duplicate_definitions` flags property setters and overload groups.
  - `@dataclass(frozen=True)` is not recognized as a dataclass, so short-class checks fire (`:1192`); doctor's own `self-check` flags its own dataclasses.
  - `from __future__ import annotations` and `__all__` re-exports are reported as unused imports.
  - `placeholder_returns` flags `return 1` because `1 == True` matches `PLACEHOLDER_CONSTANTS` (`:513`, `:1458`).
  - Findings inside private functions are attributed to the enclosing class or `<module>`.
- **Use:** disposition them via the fieldkit (see [findings playbook routes](10-agent-usage/failure-recovery.md)).

<a id="d-08"></a>

## D-08: same-second scans overwrite each other in history

This entry records a silent history-loss condition.

Resolution (discovery-fixes patch, see `TASK.md`): DONE T-06.

- **Category:** 9.
- **What:** run IDs come from `utc_now().strftime(RUN_ID_FORMAT)` with one-second resolution (`:532`), and inserts are `INSERT OR REPLACE` (`:1975-1977`).
- **Evidence:** [VERIFIED] lanes A and D: two scans within one second leave one history row.
- **Restrictions:** matters for scripted loops and CI matrices, not interactive use.

<a id="d-09"></a>

## D-09: rollback moves only the `latest` alias

This entry clarifies what `doctor rollback` actually restores.

Resolution (discovery-fixes patch, see `TASK.md`): DECISION T-52.

- **Category:** 7, 9.
- **What:** rollback rewrites the `report_aliases` `latest` row and `reports/latest.*` (`:2006`). Project-root reports are not touched; the next scan's delta is computed against the rolled-back run.
- **Evidence:** [VERIFIED] lane A; [VERIFIED] rollback to a valid run exit 0, unknown run exit 4 (lanes A, F).

<a id="d-10"></a>

## D-10: doctor writes into the caller's cwd and into its own package directory

This entry lists the implicit writes an operator must expect.

Resolution (discovery-fixes patch, see `TASK.md`): DECISION T-53 (test-suite side DONE T-13).

- **Category:** 3.
- **What:** every `main()` call creates `./production_doctor.log` (`:2181`), including `--help`; `self-check` writes reports and `.python_doctor/state.sqlite3` into the installed package directory (site-packages under pip), and exits 4 on a read-only install unless `-o` is given; `history` and `rollback` create `.python_doctor/` on a fresh tree.
- **Evidence:** [VERIFIED] lanes A, B, D.

<a id="d-11"></a>

## D-11: `main()` replaces the host program's logging configuration

This entry warns library consumers.

Resolution (discovery-fixes patch, see `TASK.md`): DECISION T-53.

- **Category:** 3, 6.
- **What:** `setup_logging` calls `logging.basicConfig(..., force=True)` with a single file handler (`:2181`), removing every existing root handler in the calling process.
- **Evidence:** [VERIFIED] in-process (lane A).
- **Use:** embed via D-12 instead.

<a id="d-12"></a>

## D-12: clean embedding path through `ProjectScanner`

This entry records the best programmatic interface discovered.

Resolution (discovery-fixes patch, see `TASK.md`): NOTE; API status is DECISION T-54.

- **Category:** 4, 1.
- **What:** `ProjectScanner(Path(root), ConfigManager(None)).scan({})` returns a `ProjectAnalysisResult` (files, issues, summary, graph) without writing files, creating state, or touching logging. Pass `ConfigManager(Path("cfg.json"))` for a config, and a previous `{relative_path: hash}` index for change tracking.
- **Evidence:** [VERIFIED] lane A example ex2 ([example](_evidence/agent-findings/lane-a-arch-api/examples/ex2_doctor_lib.py.txt)).
- **Restrictions:** internal, not exported from `somnus_debug.doctor.__init__` as a declared API; may change without notice.
- **Docs:** [programmatic invocation](10-agent-usage/programmatic-invocation.md), [public API](04-library-api/public-api.md).

<a id="d-13"></a>

## D-13: PyYAML is required by every dispatcher subcommand

This entry corrects the "doctor and structure are stdlib-only" reading.

Resolution (discovery-fixes patch, see `TASK.md`): DONE T-26.

- **Category:** 9, 6.
- **What:** `cli.py:55-58` imports all four tools at startup; `pycache_cleaner/core.py:151` imports `yaml`. Without PyYAML, `somnus-debug doctor` and `somnus-debug structure` fail too (exit 1). The standalone `somnus-doctor` and `somnus-structure` scripts do not import the cleaner [SOURCE-CONFIRMED].
- **Evidence:** [VERIFIED] `--no-deps` venv (lanes A, D).

<a id="d-14"></a>

## D-14: pycache-clean configuration hazards

This entry records the cleaner's config behaviors that can delete more than intended.

Resolution (discovery-fixes patch, see `TASK.md`): DONE T-23, T-24, T-25; relative roots DECISION T-59.

- **Category:** 9, 2.
- **What:**
  - scalar `roots: /path` is iterated per character (`:184`) and normalizes to include `/` [VERIFIED by constructing the config object only; `run()` was never called];
  - `exclude` matches bare directory names, so the MANUAL's `node_modules/*` never matches [VERIFIED];
  - values are not type-checked: `dry_run: no` is a live delete under PyYAML 1.1 booleans and `dry_run: "false"` is truthy [VERIFIED];
  - one unknown key triggers a `logging.warning` before `setup_logging`, which implicitly configures the root logger at WARNING, so the later `basicConfig` is a no-op and INFO lines, the summary, `--verbose`, and `log_file` output are lost (`pycache_cleaner/core.py:175-179,334,355-365`) [VERIFIED];
  - relative roots resolve from cwd, not the config's directory; `$VARS` are not expanded despite the docstring [VERIFIED];
  - the documented Windows `\\?\` long-path support (`:64`) has no code [SOURCE-CONFIRMED absence, grep];
  - dry-run output says "Removed" and "deleted N" [VERIFIED];
  - a missing root logs an error and exits 0 [VERIFIED].
- **Use:** always pass roots as a YAML list of absolute paths and run `dry_run: true` first.

<a id="d-15"></a>

## D-15: the scaffolded test harness is project-specific and lands outside the repo by default

This entry records why `init-test-harness` output fails out of the box.

Resolution (discovery-fixes patch, see `TASK.md`): DONE T-28, T-29.

- **Category:** 7, 9.
- **What:** the template's `TEST_NAME` is "GOLDEN PATH LAYER 1 DATA HIGHWAY RESTORATION" and it runs `cargo build -p gp-cli` (`test_harness/templates/run_test.py:195-255`). Its project root is two levels above the file, while `init-test-harness` writes to `.` by default, so `test-runs/` lands in the repo's parent. It ignores `--help` and runs. The scaffolded file adds 9 serious doctor findings. Configuration is only the `PROJECT_ROOT` and runs-dir environment variables (`:188-192`).
- **Evidence:** [VERIFIED] lanes A, B, D, F. With the test replaced and the file under `<repo>/tools/`, it passes (exit 0).

<a id="d-16"></a>

## D-16: `ignore_functions` and `check_nested_functions: false` hide security findings

This entry records that skip settings are not severity filters.

Resolution (discovery-fixes patch, see `TASK.md`): DONE T-08.

- **Category:** 2, 9.
- **What:** both skip the whole body; an `eval` inside a listed function disappears (9 issues to 3 in lane B's fixture).
- **Evidence:** [VERIFIED] lane B.

<a id="d-17"></a>

## D-17: default ignores and empty includes silently shrink coverage

This entry records coverage traps that pass CI.

Resolution (discovery-fixes patch, see `TASK.md`): DONE T-09; default ignore list DECISION T-55.

- **Category:** 3, 9.
- **What:** default ignore patterns skip directories named `env`, `build`, `venv` and similar at any depth (`pkg/env/e.py` never scanned); `src/**/*.py` misses `src/c.py`; empty `include_patterns` scans 0 files and exits 0.
- **Evidence:** [VERIFIED] lane B. The fieldkit `delta.py` catches zero-file and coverage-drop cases (exit 2) [VERIFIED lane F].

<a id="d-18"></a>

## D-18: exit-code overloading and escape paths

This entry records exit-code ambiguities that matter for automation.

Resolution (discovery-fixes patch, see `TASK.md`): DONE T-07; argparse exit 2 DECISION T-56.

- **Category:** 9.
- **What:** exit 2 means both "critical gate tripped" and "argparse usage error"; with gate `minor` or `info`, exit is 1 even when criticals exist; exception types outside the classified set escape as raw tracebacks; a RecursionError (deep expression) aborts the scan with exit 5 only on the serial path (one file, or `max_workers: 1`); with two or more files on the thread pool it becomes one `analysis_read_errors` finding (exit 2) [VERIFIED, W1]. See also D-29.
- **Evidence:** [VERIFIED] lanes A, D; [SOURCE-CONFIRMED] `main()` at `:2184-2200`.
- **Docs:** [exit codes](05-cli-and-tools/exit-codes.md).

<a id="d-19"></a>

## D-19: no extension API; a custom detector works only through private subclassing

This entry answers "can I add a check without editing core".

Resolution (discovery-fixes patch, see `TASK.md`): DECISION T-54.

- **Category:** 5, 8.
- **What:** no registry, entry-point discovery, hook, or callback exists in `src/somnus_debug/` (grep and installed entry points). Detectors are methods on `CodeQualityVisitor`, instantiated by name in `FileAnalyzer` (`:1542`). Subclassing it and patching the reference worked end to end (JSON, score, gate, delta). Score weights are hard-coded (`:1772`). Severity can be set for any category name (unmapped default minor, `:794`).
- **Evidence:** [VERIFIED] [ext_custom_detector.py](_evidence/agent-findings/lane-f-ext/recipes/ext_custom_detector.py). Not a public contract.

<a id="d-20"></a>

## D-20: fieldkit `onboard.py` defects

This entry records onboarding failures an agent will hit.

Resolution (discovery-fixes patch, see `TASK.md`): DONE T-30, T-31, T-32.

- **Category:** 9.
- **What:** `--python` with a normal (symlinked) venv interpreter is rejected with exit 3 because `.resolve()` leaves the venv (`onboard.py:240`); only `venv --copies` works. A broken doctor config crashes with a traceback, exit 1 (`:405`), not the documented 2. `--apply` writes `PROFILE.md` even when the check scan finds zero files, so a rerun treats the repo as onboarded and skips the baseline. Plan mode touched `.git/index` on the repo copy.
- **Evidence:** [VERIFIED] lanes D, F.

<a id="d-21"></a>

## D-21: fieldkit `delta.py` gate holes

This entry records ways a regression passes the delta gate.

Resolution (discovery-fixes patch, see `TASK.md`): DONE T-34.

- **Category:** 9.
- **What:** a broad disposition matching nothing today is only reported stale and still absorbs a later regression (exit 0); `config_hash` is never compared, so a severity remap in the new config lets a new finding pass; usage error exit 2 equals coverage regression; a malformed report raises a traceback (exit 1, reads as regression). Matching ignores line numbers (moved code persists) [VERIFIED, by design].
- **Evidence:** [VERIFIED] lane F logs `s2_*`.

<a id="d-22"></a>

## D-22: src-layout onboarding makes the project's own imports third-party

This entry records a composition conflict between onboard and doctor.

Resolution (discovery-fixes patch, see `TASK.md`): DONE T-04, T-35.

- **Category:** 6.
- **What:** onboard's runner sets `PYTHONPATH=src`; doctor then resolves own absolute imports via `find_spec` as third-party, so `dependency_cycles` stays 0. Scanning with `src/` as the project root detects the cycle.
- **Evidence:** [VERIFIED] lane F.

<a id="d-23"></a>

## D-23: version and packaged-config drift

This entry records release-surface drift.

Resolution (discovery-fixes patch, see `TASK.md`): DONE T-27; root duplicates DECISION T-57, release T-58.

- **Category:** 7.
- **What:** PyPI 0.1.0 code equals `src/` once metadata headers are stripped; only `default_config.yaml` differs (PyPI ships the old MCP globs). It is reference-only, so runtime behavior is the same. The version is hard-coded in both `pyproject.toml` and `__init__.py:57`; the git tag is `v1.5.0` per PLAN.md.
- **Evidence:** [VERIFIED] lane D `pip download` diff ([install-vs-source](_evidence/agent-findings/lane-d-cli-tests/install-vs-source.md)).

<a id="d-24"></a>

## D-24: structure double-renders a class nested in a class in a function

This entry records an indexer counting bug.

Resolution (discovery-fixes patch, see `TASK.md`): DONE T-21.

- **Category:** 9.
- **Evidence:** [VERIFIED] lane A: 7 definitions reported, 6 real (measured with the root script, since the src copy crashes on stamped fixtures).

<a id="d-25"></a>

## D-25: `-o report.json` overwrites the markdown report; JSON is always written

This entry records an output-path collision.

Resolution (discovery-fixes patch, see `TASK.md`): DONE T-10.

- **Category:** 3, 7.
- **What:** doctor derives both report paths from `-o`; a `.json` output path makes the markdown and JSON targets collide. MANUAL says JSON is "only if requested"; it is always written.
- **Evidence:** [VERIFIED] lanes B, F.

<a id="d-26"></a>

## D-26: `missing_imports` depends on the interpreter and cwd

This entry records environment-sensitive results.

Resolution (discovery-fixes patch, see `TASK.md`): NOTE (src-layout half DONE T-04).

- **Category:** 6, 9.
- **What:** third-party resolution uses `importlib.util.find_spec` in doctor's own interpreter; `python -m` (cwd on `sys.path`) gave 0 issues where a console-script run gave `missing_imports`.
- **Evidence:** [VERIFIED] lane B (reproduced with `python -P`); W2 sharpened it: the same import read as `missing` (exit 1) under one invocation and `third_party` (exit 0) under the other.

<a id="d-27"></a>

## D-27: verified compositions

This entry records capability chains that already work without new code.

Resolution (discovery-fixes patch, see `TASK.md`): NOTE.

- **Category:** 6, 1.
- **What, all [VERIFIED] by lane F:** doctor JSON into `delta.py` as a CI gate (clean 0, regression 1, config error 3); structure line spans used to print only named definitions; delta output mapped to definition slices (refuses if files changed since scan); a ratchet that promotes the baseline only on clean delta, with doctor history as audit trail; doctor's per-run state reports used directly as delta baselines.
- **Docs:** [composition patterns](08-extensions/composition-patterns.md), [recipes](09-recipes/README.md).

<a id="d-28"></a>

## D-28: the SQLite-unavailable fallback covers scan only

This entry records partial degradation.

Resolution (discovery-fixes patch, see `TASK.md`): DONE T-11 (no change needed).

- **Category:** 9, 7.
- **What:** `run_scan` catches `StateStoreError` and continues without history (`:2066-2077`); `history` has no such fallback and exits 4. The root `python_production_doctor.py` lacks the fallback entirely.
- **Evidence:** [VERIFIED] lane A (broken-state scan exit 2 with findings, history exit 4).

<a id="d-29"></a>

## D-29: a mistyped scan root passes CI, and serial-path analyzer errors escape

This entry records two failure modes found in Wave 5 that narrow D-18.

Resolution (discovery-fixes patch, see `TASK.md`): DONE T-01, T-07.

- **Category:** 9, 3.
- **What:** with state enabled, a missing but writable project root is created during state setup, scanned as empty (0 files), and exits 0; `history` on such a path also creates `.python_doctor/` there. Only `--no-state` or an uncreatable path yields exit 4. Separately, when `max_workers` is 1 or the project has one file, an analyzer exception escapes the scan instead of becoming a per-file finding.
- **Evidence:** [VERIFIED] W1, via `somnus_debug.doctor.core.main` in /tmp ([error handling](07-internals/error-handling.md), [fallbacks](07-internals/fallbacks.md)). This corrects lane A's "missing root: 4", which held only for its conditions.
- **Use:** in CI, assert the root exists before scanning, or gate with fieldkit `delta.py`, which fails zero-file scans (exit 2).

<a id="d-30"></a>

## D-30: the default `ignore_functions` hides `eval`/`exec` in `__repr__` and `__str__`

This entry extends D-16 to the out-of-box configuration.

Resolution (discovery-fixes patch, see `TASK.md`): DONE T-08.

- **Category:** 3, 9.
- **What:** the default `ignore_functions` is `[__repr__, __str__]`; their bodies are skipped entirely, so a security call inside either is never reported.
- **Evidence:** [VERIFIED] W3 ([configuration pitfalls](06-configuration/configuration-pitfalls.md)).

<a id="d-31"></a>

## D-31: pycache-clean `targets` makes it a general-purpose deleter

This entry extends D-14.

Resolution (discovery-fixes patch, see `TASK.md`): DONE T-23 validation; targets scope DECISION T-38.

- **Category:** 2, 9.
- **What:** the `targets` key controls which names are deleted; a test run deleted a `*.bak` file and a non-cache directory.
- **Evidence:** [VERIFIED] W4 in /tmp ([recipes execution log](09-recipes/execution-log.md)). A `targets: ["*.py"]` run was deliberately not executed.

<a id="d-32"></a>

## D-32: concurrent stateful scans lose history

This entry extends D-08 to parallel agents.

Resolution (discovery-fixes patch, see `TASK.md`): DONE T-06; fresh-DB race OPEN T-14.

- **Category:** 9, 6.
- **What:** two stateful scans launched together on a fresh state DB: one silently fell back to stateless with only a warning. On an existing DB both got the same run id and history kept one row. `--no-state` scans with private output paths are safe in parallel.
- **Evidence:** [VERIFIED] W4 ([subagent patterns](10-agent-usage/subagent-patterns.md)).

<a id="d-33"></a>

## D-33: library JSON equals CLI JSON

This entry records a useful equivalence for embedders.

Resolution (discovery-fixes patch, see `TASK.md`): NOTE.

- **Category:** 4.
- **What:** `dumps_json(ProjectScanner(root, ConfigManager(None)).scan({}))` matches the CLI's `--json-output` in every key except `run_id`, `started_at`, and `finished_at`, so an embedded scan can feed `delta.py` directly.
- **Evidence:** [VERIFIED] W4 ([embedded scan recipe](09-recipes/programmatic/embedded-scan.md)).

<a id="d-34"></a>

## D-34: smaller Wave 5 findings

This entry groups lower-impact findings from the page writers.

Resolution (discovery-fixes patch, see `TASK.md`): DONE T-12, T-22, T-23, T-28, T-33; logging handler OPEN T-37.

- `structure` on a non-UTF-8 file raises an uncaught `UnicodeDecodeError` (exit 1, not 2) [VERIFIED W2, lane B].
- `PycacheCleaner.run()` in a process with no logging configured adds a stderr handler to the root logger [VERIFIED W1].
- Assigning a new config to `ConfigManager.config` (e.g. via `dataclasses.replace`) skips validation and leaves `config_hash` describing the old config [VERIFIED W1, W3].
- A relative `SINGLE_TEST_OUTPUT_DIR` in the harness resolves against cwd, not the project root [VERIFIED W3].
- onboard `--python` with a nonexistent path crashes with a traceback (exit 1); a doctor exit of 1 still allows `--baseline`; `--baseline` reruns overwrite `runs/baseline.*` (only the five profile files are never overwritten, `onboard.py:415-422,495-501,515-516`; baseline rewrite at `:518-520`) [VERIFIED W3, W4].
- Doctor's thread pool gave no speedup on a 2-CPU sandbox (68 files: serial 1.05 s, 4 workers 1.21 s) [VERIFIED W1, one measurement].
- `pycache-clean --max-depth -1` (any negative) silently does nothing; `doctor self-check -v` is rejected with exit 2 because only `scan` defines `-v` [VERIFIED review-h].
- Doctor-only modules run without PyYAML when invoked directly (`python -m somnus_debug.doctor.core`), including on Python 3.13 [VERIFIED W2].

## Operator-environment note

This section records side effects the investigation itself caused, for transparency.

A sandbox reset around 00:40 UTC on 2026-11-12 wiped /tmp and two lane A files (`README.md`, reconstructed by the lead, and `undocumented-primitives.md`, whose coverage W1 rebuilt from source); writers re-ran their examples afterwards. Running sources with `PYTHONPATH=src` created `__pycache__/` under `src/somnus_debug/` (gitignored, absent from the upload); the lead removed them after confirming they were not in the zip. Lane D's capture of the root `run_test.py --help` executed the shipped test (D-15) and wrote `forge/test-runs/` outside the repo; lane D removed that directory. No tracked file was modified (`git status` shows only `?? wiki/`).

## Sources

- [Lane A](_evidence/agent-findings/lane-a-arch-api/README.md), [Lane B](_evidence/agent-findings/lane-b-config/configuration-findings.md), [Lane D](_evidence/agent-findings/lane-d-cli-tests/README.md), [Lane F](_evidence/agent-findings/lane-f-ext/README.md)
- `STATE.md`, `PLAN.md` (operator files in the upload)
