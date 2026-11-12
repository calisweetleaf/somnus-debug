# Lane F: `skills/somnus-debug-fieldkit/` (what the scripts actually do)

All paths are relative to `skills/somnus-debug-fieldkit/` unless noted. Script line numbers are real file lines (each script has a 32-line `somnus:metadata` header). Reference-file line numbers are real file lines too (each has a 32-line YAML front matter block).

Runs: `repro/s1_selftest_onboard.sh`, `repro/s2_loop_delta.sh`, `repro/s3_compositions.sh`, with logs in `logs/s1_*`, `logs/s2_*`, `logs/s3_*`. The fixture is a 3-file src-layout project (`src/calc/{__init__,ops}.py`, `tests/test_ops.py`) under `/tmp/lane-f/proj`, a git repo with its own `.venv` holding a non-editable install of the repo.

## 1. `scripts/selftest.py`: contract test (VERIFIED 29/29)

- **CLI:** `selftest.py [--python PY]`. Without `--python` it uses `somnus-debug` on PATH, else exits 3 (`:319-330`).
- **What it does:** builds throwaway fixtures in a `TemporaryDirectory(prefix="sd-selftest-")` and runs 29 checks in 4 groups (`:145-316`): CLI surface (version, `--help` flags of 8 command surfaces, 3 init-config defaults), exit codes and side effects (zero-file → 0, serious → 1, syntax → 2, bad gate → 4, log written to cwd even for `--help`, report lands in project root without `-o`), finding triggers (src-layout missing_imports with and without PYTHONPATH, uninstalled import, `log.warning` silent vs `logger.exception` not, abstractmethod stub, property-setter duplicate, `test_gaps` sentinel, case-insensitive `temp` todo), and other tools (structure writes nothing, pycache dry-run deletes nothing, path-style exclude ignored, scaffold refuses overwrite).
- **Output:** a Markdown PASS/FAIL table on stdout. A crashed group becomes one FAIL row (`:333-337`).
- **Exit:** 0 all pass, 1 any fail, 3 no CLI (`:346`).
- **Writes:** only inside its temp dir (it passes `cwd` into temp subdirs for every call). VERIFIED `logs/s1_selftest.md`: **29/29 passed, exit 0** with `--python /tmp/lane-f/venv/bin/python` (a symlinked venv interpreter works here because selftest only calls `expanduser()`, `:325`).

## 2. `scripts/onboard.py`: survey, runner choice, profile

**CLI** (`:451-459`): `onboard.py [repo] [--apply] [--baseline] [--new-config] [--python PY]`.

**Pipeline:**
1. `survey()` (`:171-216`) walks the tree once and records:
   - Python counts by top-level dir.
   - Venvs, found by `pyvenv.cfg` under **any** dir name. VERIFIED: `tools-env` was found (`logs/s1_onboard_edges.log` E-O5).
   - `*.egg-info` dirs, git-ignored dirs containing `.py` (`git status --ignored`), and src layout (`src/<pkg>/__init__.py`).
   - Existing `python_doctor.y(a)ml` at the root or in `.somnus-debug/`.
   - Harness files, test dirs, native gate files, and AGENTS/CLAUDE/copilot files, plus whether they mention somnus-debug.
   - `ALWAYS_PRUNE` dirs are skipped (`:71-75`).
2. `choose_runner()` (`:233-260`): `--python` → project venvs (`.venv`, `venv`, `env`, then any `pyvenv.cfg` dir) that can `import somnus_debug` → `somnus-debug` on PATH → none (exit 3). A src layout adds `PYTHONPATH=<repo>/src`.
3. Config:
   - Adopts the first **root** `python_doctor.yaml` unless `--new-config` is given (`:477-479`).
   - Otherwise it generates `.somnus-debug/python_doctor.yaml` from the CLI's own `init-config` output. It regex-replaces `include_patterns` (keeps `*.py`), `ignore_patterns` (BASE_IGNORES plus discovered venvs, egg-info and git-ignored dirs) and `state_dir: ".somnus-debug/state"`, and aborts if the default layout changed (`:276-297`).
4. `--apply` writes, never overwriting (`write_new`, `:415-422`): the doctor config, `pycache.yaml` (absolute root, name-only excludes, `dry_run: true`), `dispositions.json` (`[]`), `.gitignore` (`state/ runs/ *.log`), then `PROFILE.md`.
5. A verification scan runs `--no-state`, from a temp cwd, into a temp report whenever a config exists, plan mode included (`:503-509`). Then `report_scan` decides: exit ≥ 4 means FAIL, `files==0` means FAIL (→ 2), and fewer files than surveyed means WARN (`:435-448`).
6. `--baseline` runs a **stateful** scan with cwd `.somnus-debug/` into `runs/baseline.{md,json}`, only if the verify status is 0 (`:518-522`).

**Exit codes:** 0 ok, 1 usage, 2 coverage failure, 3 no CLI (`:50`).

**Files written** (VERIFIED `logs/s1_onboard.log` O2): `.somnus-debug/{.gitignore, PROFILE.md, dispositions.json, pycache.yaml, python_doctor.yaml, production_doctor.log, runs/baseline.{md,json}, state/state.sqlite3, state/reports/<run_id>/production_doctor_report.{md,json}, state/reports/latest.{md,json}}`. Git sees `.somnus-debug/` untracked, with `runs/`, `state/` and the log ignored. Plan mode left `git status` clean. Re-apply reported "Kept existing (not overwritten)" for all 5 files (O3).

**Generated artifacts:** copies are in `logs/s1_PROFILE.md.txt`, `logs/s1_profile_python_doctor.yaml.txt`, `logs/s1_profile_pycache.yaml.txt`.

### onboard.py findings

| # | Finding | Class | Evidence |
|---|---|---|---|
| OB-1 | **`--python` with a normal (symlinked) venv interpreter is rejected.** `Path(explicit_python).expanduser().resolve()` follows `venv/bin/python → /usr/local/bin/python3.12`, which drops the venv, and then reports that `/usr/local/bin/python3.12 cannot import somnus_debug` → BLOCKED, exit 3. It works only with `python -m venv --copies` interpreters. That makes the documented "Force a specific interpreter with `--python`" (`references/onboarding.md:59`) broken for the default venv layout on Linux and macOS. (Project-venv auto-detection is unaffected: `venv_python()` does not resolve.) | VERIFIED / DISCREPANCY | `scripts/onboard.py:240`; `logs/s1_onboard.log` O0b (exit 3) vs O0c (`--copies`, exit 0) |
| OB-2 | **A doctor config error crashes onboard with a traceback and exit 1.** `run_scan` raises `RuntimeError` when stdout has no `Scan complete` line, so `report_scan`'s `exit >= 4` branch is unreachable. The docs promise exit 2 ("coverage failure (zero files or doctor error)"). | VERIFIED / DISCREPANCY | `scripts/onboard.py:403-405` vs `:440-442`; `references/onboarding.md:57`; `logs/s1_onboard_edges.log` E-O2 |
| OB-3 | **`--apply` still writes `PROFILE.md` when verification fails.** Adopting this repo's root `python_doctor.yaml` (Somnus globs) scans 0 files and exits 2. Yet `pycache.yaml`, `dispositions.json`, `.gitignore` and `PROFILE.md` are written, and the card records `Verification scan: files=0 … exit=0 (gate passed)`. The next run reports `profile: True`, and SKILL.md's start-here rule ("Present: read it … Go to the loop", `SKILL.md:55`) would treat the repo as onboarded. No baseline is written, and nothing says it was skipped. | VERIFIED | `scripts/onboard.py:515-518`; `logs/s1_onboard_edges.log` E-O1, E-O1b |
| OB-4 | `--baseline` is silently skipped whenever verify status ≠ 0. No message is printed. | SOURCE-CONFIRMED (seen in E-O1) | `scripts/onboard.py:518` |
| OB-5 | The repo's own root `python_doctor.yaml` is adopted by default and scans zero files on a normal tree, which confirms MANUAL §7.1 and provenance.md. | VERIFIED | `logs/s1_onboard_edges.log` E-O1 |
| OB-6 | The PROFILE commands are absolute and machine-specific (interpreter path and fieldkit path). PROFILE.md tells you to regenerate it after a move. | VERIFIED | `logs/s1_PROFILE.md.txt`; `scripts/onboard.py:389-393` |
| OB-7 | The PROFILE date uses `dt.date.today()` (host-local; the sandbox is UTC, so the card says 2026-11-12 while it is 2026-11-11 CST). Cosmetic. | VERIFIED | `logs/s1_PROFILE.md.txt` |

## 3. `scripts/delta.py`: regression gate

**CLI** (`:235-243`): `delta.py BASELINE.json LATEST.json [--dispositions F] [--root DIR] [--json]`. It is read-only and writes nothing.

**Algorithm** (`:159-191`):
- Finding identity is `(category, file_path, symbol, message)`, with no line number (`:82-85`).
- `new` and `resolved` are multiset differences (`:147-156`), so duplicates count.
- A disposition matches on `category ==` plus `fnmatchcase(file)` plus `fnmatchcase(symbol)` (symbol defaults to `*`), applied to **every** latest finding. The first match wins and is marked used.
- `regressions` = new, not dispositioned, and severity ∈ {critical, serious}.
- Coverage failure = latest `files_scanned == 0`, **or** a baseline file missing from latest while it still exists on disk (root = `--root` or latest `project_root`). Files deleted from disk are reported, not failed.
- Exit: 2 if coverage failure, else 1 if regressions, else 0. Bad input exits 3.

**Data formats (JSON schemas, informal):**

```text
doctor report (input; produced by `doctor scan --json-output`, see logs/s1_doctor_json_shape.txt)
{ run_id, project_root, started_at, finished_at, config_hash,
  summary: {files_scanned, total_issues, critical_issues, serious_issues, minor_issues, info_issues,
            syntax_error_files, missing_imports, dependency_cycles, suspicious_short_classes,
            suspicious_short_functions, production_score},
  issues: [{category, severity, file_path, line_number, column_offset, symbol, message, evidence, remediation, details}],
  files:  [{relative_path, file_path, file_hash(sha256), size_bytes, modified_time, syntax_valid, metrics,
            issues, imports, import_edges, functions:[{qualname,kind,line_number,end_line_number,
            executable_line_count,statement_count,cyclomatic_complexity,return_count,argument_count,
            missing_type_hints,has_docstring,decorators}], classes, code_map}],
  dependency_graph: {nodes, edges:[{source_file,target_file,imported_module,classification,status,confidence,line_number,raw}],
                     missing_imports, cycles, mermaid},
  state_delta: {new_files, modified_files, deleted_files, unchanged_files} }
delta.py needs only: issues[].{category,file_path,symbol?,message?,severity?,line_number?}, summary, files[].relative_path, project_root?, run_id?

dispositions.json (input)
[ {"category": str (required, exact), "file": fnmatch glob (required), "symbol": fnmatch glob (optional, default "*"),
   "reason": str (required, non-empty)} ]

delta --json (output)
{ baseline: <summary>, latest: <summary>, baseline_run, latest_run, persisting: int,
  uncovered_files: [path], deleted_files: [path], added_files: [path], coverage_failure: bool, exit: 0|1|2,
  new: [{severity,category,file,line,symbol,message}], resolved: [...], regressions: [...],
  dispositioned: int, stale_dispositions: [{category,file,symbol,reason}] }
```

"Baseline" is just a doctor JSON report kept at `runs/baseline.json`. There is no separate baseline format. Doctor's own per-run state reports (`<state_dir>/reports/<run_id>/production_doctor_report.json`, `latest.json`) have the same shape and work as delta inputs (VERIFIED `logs/s3_C1_C3.log` C3e).

**Verified behavior** (`logs/s2_loop.log`, `logs/s2_delta_edges.log`):

| Case | Result |
|---|---|
| L2 stub plus silent failure added, and `test_add` moved 4 lines | exit 1; 3 new (2 serious, 1 minor); `test_add` counted as **persisting** (line-independence confirmed) |
| L3 one narrow disposition plus one broad unused entry | exit 1 (stub still open); broad entry listed as stale |
| L6 stub fixed | exit 0 **while doctor itself exits 1** (the dispositioned serious finding remains). Delta and doctor gates disagree by design. |
| **L7 new `os.system` call while the "stale" broad disposition `{security_risks, src/*}` is still in the file** | **exit 0: the regression was silently absorbed.** A stale-but-broad disposition is a latent mute for future findings. Stale entries do not affect the exit code; only the "Done means" checklist (`SKILL.md:125`, `references/doctor-loop.md:94`) asks you to delete them. |
| D1 latest config ignores `tests/*` | exit 2; `tests/test_ops.py` listed as dropped. Its findings are shown as **"Resolved"**, which is misleading but superseded by the coverage verdict |
| D2 zero-file latest (doctor exit 0) | exit 2 |
| **D3 new stub; latest config remaps `stubs: info`** | **exit 0.** `delta.py` never compares `config_hash` (it differs, as verified) and doesn't recompute severities, so a config change in the latest scan can launder a regression. D3b (same code, profile config) → exit 1. |
| D4 `{}` as report | exit 3 |
| **D5 argparse usage error** | **exit 2**, which collides with "coverage regression" (argparse default) |
| D6 disposition without `reason` | exit 3 |
| D7 dispositions path missing | note on stderr, continues without dispositions (stricter, so it fails safe) |
| **D8 issue object lacking `category`** | **`KeyError` traceback, exit 1**, indistinguishable from "regression"; documented input errors are 3 |
| D9 rename `safe_int → lenient_int` | the old disposition goes stale and the finding returns as new → exit 1 (identity includes symbol and message) |

## 4. `templates/AGENTS_APPENDIX.md`

This is a 23-line Markdown block meant to be pasted into a repo's `AGENTS.md`. It points to `.somnus-debug/PROFILE.md`, the 5-step loop, and the "Never" list. No script appends it: onboard only prints a "Next:" hint (`scripts/onboard.py:528-529`). It differs from `docs/AGENTS_APPENDIX.md` (see doc-reconciliation.md).

## 5. Reconciling `references/*.md` and `SKILL.md` with the code

| Claim (file:line) | Code / run | Verdict |
|---|---|---|
| `SKILL.md:12,99` and `references/install.md:78`: selftest has 29 checks | 29 records; 29/29 run | matches (VERIFIED) |
| `SKILL.md:77,98`, `references/doctor-loop.md:66-71`: delta exits 0 clean / 1 regression / 2 coverage / 3 input | true for its own logic; argparse usage → 2 (D5); malformed issue → traceback 1 (D8) | partial DISCREPANCY |
| `SKILL.md:97`, `references/onboarding.md:57`: onboard exits 2 on "zero files or doctor error" | zero files → 2 ✓; doctor error → traceback, exit 1 (OB-2) | DISCREPANCY |
| `references/onboarding.md:59`: "Force a specific interpreter with `--python`" | broken for symlinked venvs (OB-1) | DISCREPANCY |
| `references/onboarding.md:66`, `SKILL.md:97`: onboard never overwrites | VERIFIED O3 | matches |
| `SKILL.md:101`, `README.md:58` (fieldkit): scripts "never write outside their stated targets" | onboard writes only `.somnus-debug/` plus temp dirs; selftest temp only; delta writes nothing | matches (VERIFIED) |
| `references/onboarding.md:39-47` ("Onboarded means" 1-9) | items 1-8 produced on the happy path; item 9 (AGENTS block) is manual; on coverage failure items 6-8 are inconsistent (OB-3) | partial |
| `references/doctor-loop.md:73`: "Findings match on category + file + symbol + message, so code that only moved isn't new" | VERIFIED L2 | matches |
| `references/findings.md:136-146`: narrow dispositions; stale ones reported | reported ✓; but a stale broad one still mutes new findings (L7). Not stated anywhere. | documented-only risk (gap) |
| `references/automation.md:65`: "gate on `delta.py`'s exit code rather than the raw doctor exit" | correct and necessary (L6: doctor 1, delta 0) | matches |
| `references/commands.md:76`: without `-o`, reports go to the project root; the log goes to cwd; no config auto-discovery | VERIFIED by selftest | matches |
| `references/commands.md:80`: "`rollback` restores a previous report as latest and does not change source files" | VERIFIED C3d (alias plus `latest.{md,json}` only). Also changes the hash index the **next** scan's `state_delta` is computed against (C3g) — not documented. | matches (+ undocumented effect) |
| `references/commands.md:101`, `references/onboarding.md:80`: pycache excludes match names only | VERIFIED by selftest | matches |
| `references/onboarding.md:78-79`: fnmatch `*` crosses `/`; `name/*` prunes dirs named `name` at any depth | `doctor/core.py:937-947`; P2 shows `src/**/*.py` does **not** match `src/top.py` (needs 2 slashes) | matches; MANUAL example misleads (see doc table) |
| `references/findings.md:50-56`: severity table and score formula | `doctor/core.py:481-500`, `:1772` | matches |
| `references/findings.md:83` (stubs FP list: "Decorators are not consulted") | `body_is_stub` ignores decorators, `doctor/core.py:1436-1448`; selftest proves the abstractmethod case | matches |
| `references/findings.md:94` (`suspicious_short_classes` exempts dataclass) | `@dataclass(frozen=True)` **not** exempt (X9) | DISCREPANCY (missing FP) |
| `references/findings.md:97-99` (silent_failures name-sensitive) | `doctor/core.py:1471-1487`; selftest | matches |
| `references/findings.md:105-107` (security dotted-name list and evasions) | `doctor/core.py:514`, `:1229` | matches |
| `references/findings.md:110` (test_gaps never emitted) | no emitter; selftest sentinel | matches |
| `references/findings.md:60-62` (private fns skipped, bodies still visited) | `doctor/core.py:1239-1241`. Unstated consequence: findings in them get the parent symbol, e.g. `<module>` | matches (+ gap) |
| `references/topology.md:74`: "self-check checks doctor behavior against its own package" | it does, **and writes reports into site-packages** (C8) | partial (side effect undocumented) |
| `references/provenance.md:42`: PyPI wheel/sdist byte-identical to src at `5b6e0c4` | not re-verified here (lane D owns install-vs-source) | UNVERIFIED (this lane) |
| `references/provenance.md:84`: README links STATE.md, PLAN.md, docs/OPSEC.md that are absent from the public tree | in this zip, STATE.md and PLAN.md **exist**; only `docs/OPSEC.md` is dead (link check) | CONDITIONAL (true for the public tree, not this checkout) |
| `references/install.md:52`: onboard detects `.venv`, `venv`, `env`, or any `pyvenv.cfg` dir | VERIFIED E-O5 | matches |

## Sandbox caveat

In this sandbox, `datetime.isoformat()` returns a localized string ("Wed 2026-11-11 6:22 PM CST (UTC-06:00)"), even for UTC-aware datetimes. So doctor's `started_at`/`finished_at`/`completed_at` values in the logs are not ISO strings (`logs/s3_C1_C3.log` C3h). Run IDs (strftime) are unaffected. Because `history` orders by the `completed_at` TEXT column, the ordering observed here is CONDITIONAL. It was correct within one day in this sandbox, but on a normal host the column is ISO-8601 and sorts lexically.
