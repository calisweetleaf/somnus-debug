# Lane F: reconciling `docs/*.md` and `README.md` with the source

Verdicts:
- **match**: source or run agrees.
- **DISCREPANCY**: source or run contradicts the doc.
- **documented-only**: no code behind it (policy, a planned feature, an external fact, or a file absent from this checkout).
- **partial**: mostly right, with a material omission.

Doc line numbers are real file lines (each doc has a 32-line front matter block). Source refs are `src/somnus_debug/...` unless they start with another top-level dir. "Run" points to a log in `logs/`. CONTRACT.md is reconciled in `harness.md` §4; only its cross-doc items appear here.

## Dead or absent references

| Reference | Where | Status |
|---|---|---|
| `docs/OPSEC.md` | README.md:363 (layout), README.md:383 (link), MANUAL.md:41, MANUAL.md:410 | **absent**. Only dead relative link found by the checker (`logs/s5_library_and_links.log`). |
| `STATE.md`, `PLAN.md` | README.md:369-370 | **present in this zip** (root). The brief's "dead link" lead is CONDITIONAL: they are absent from the public tree per `skills/.../references/provenance.md:84` and are not in the sdist include list (`pyproject.toml` `[tool.hatch.build.targets.sdist]`). |
| `SKILL/somnus-debug.md` ("compact compatibility entry") | MANUAL.md:46 | **absent** (no `SKILL/` dir) |
| `packaging.md` "project memory" | MANUAL.md:229, :417; PUBLISHING.md:135 | external, not in repo (documented-only) |

## README.md

| Doc claim | Source / run | Verdict |
|---|---|---|
| :74 Python 3.10–3.12 badge | `pyproject.toml` `requires-python >=3.10`, classifiers 3.10/3.11/3.12; tested here only on 3.12.15 | match (others UNVERIFIED) |
| :77 badge "Tests 10/10 passing"; :358 "10 real subprocess CLI smoke tests" | `tests/test_cli_smoke.py` has **12** `def test_` functions (`logs/s6_doc_probes.log` P10). Pass/fail is lane D's. | DISCREPANCY (count) |
| :176-177 only dependency is pyyaml, and only for pycache-clean; doctor and structure are stdlib-only | `pycache_cleaner/core.py:151` (`import yaml` in try); structure and doctor import only the stdlib (`structure/core.py:50-55`, `doctor/core.py:51-72`) | match |
| :199 doctor detects stubs, placeholders, silent handlers, cycles, docstring and hint coverage, security, TODOs | all have emitters in `doctor/core.py` (`CodeQualityVisitor`, `_token_diagnostics`, `_attach_cycles`) | match |
| :200 structure never imports or executes the target | `structure/core.py` uses `ast.parse` only (`:210`) | match |
| :201 pycache-clean "Dry-run by default via `--dry-run`" | `CleanerConfig.dry_run` defaults to **False** (`pycache_cleaner/core.py:163`). Dry-run happens only with the flag or the config key (`:357-358`). | DISCREPANCY (wording implies a default) |
| :204-205 "Every tool is also installed as its own script: somnus-doctor, somnus-structure, somnus-pycache-clean" | 3 scripts; `init-test-harness` has none (`pyproject.toml` `[project.scripts]`; `logs/s5_library_and_links.log`). MANUAL.md:96-97 says so explicitly. | partial ("every") |
| :216-217 transcript `doctor scan . -o report.md` → one line | real output is 5 lines (scan, MD path, JSON path, state latest, run ID) (`doctor/core.py:2087-2093`) | illustrative / partial |
| :219-220 `structure … -o CORE_INDEX.md` prints "Class Index … written to CORE_INDEX.md" | `-o` writes silently with 0 bytes of output (`structure/core.py:337-342`; P7) | DISCREPANCY (transcript) |
| :222-223 pycache dry-run prints "deleted N directories … # dry run — nothing actually removed" | dry-run logs "Removed directory …" and "Summary: deleted 2 directories" while deleting nothing (`logs/s4_C4.log`) | match (the misleading wording is real) |
| :330 root-level legacy scripts "harmless, just redundant" | the root duplicates differ from `src/` (brief lead: structure `type_comments`, doctor main); not reconciled by this lane | UNVERIFIED (lane A/B) |
| :335-337 library imports `build_index`, `ProjectScanner`, `ConfigManager`, `PycacheCleaner`, `CleanerConfig` | all importable (`logs/s5_library_and_links.log`) | match |
| :350, :371 fieldkit is the canonical agent skill | present | match |
| :358 tests listed under `src/somnus_debug/` | tests live at repo-root `tests/` | DISCREPANCY (layout) |
| :363, :383 OPSEC.md | absent | dead |

## docs/MANUAL.md

| Doc claim | Source / run | Verdict |
|---|---|---|
| :35 version 0.1.0 | `pyproject.toml`, `__init__.py:57` | match |
| :41-44 CONTRACT.md and OPSEC.md are governing docs | CONTRACT present, OPSEC absent | partial / dead |
| :46 `SKILL/somnus-debug.md` remains | absent | dead |
| :60-62 pyyaml only for pycache-clean; doctor has its own YAML parser | `MinimalYamlParser` (`doctor/core.py:646`) | match |
| :94-97 3 standalone scripts; init-test-harness has no alias | `pyproject.toml` | match |
| :110-113 doctor reports "… and test gaps" | **no emitter for `test_gaps`** (only config keys at `doctor/core.py:470`, `:493`, `:840`); selftest sentinel | DISCREPANCY |
| :122-125 default includes every `*.py` minus VCS, caches, venvs, node_modules, build, dist | `DEFAULT_CONFIG_DATA` (`doctor/core.py:458-459`) | match |
| :126-132 example `include_patterns: "src/**/*.py"` | fnmatch has no `**`. `src/**/*.py` needs ≥2 slashes, so `src/top.py` is silently excluded (P2: only `src/pkg/mod.py` scanned) | DISCREPANCY (misleading example) |
| :137-141 command tree | `build_parser` (`doctor/core.py:2130-2162`); selftest flag checks | match |
| :144-149 bare path is normalized to `scan` | `normalize_argv` (`doctor/core.py:2165-2176`) | match (SOURCE-CONFIRMED) |
| :170-176 exit codes "0 / non-zero" | actual 0/1/2/4/5 (`doctor/core.py:2046-2058`, `:2195-2203`); selftest | partial (under-specified) |
| :178-179 `"minor"` fails "on anything at all" | the minor gate ignores info-only results (P4: exit 0 with 1 info finding) | partial |
| :183-185 state under `.python_doctor/` in the scanned project root | `StateStore.__init__` (`doctor/core.py:1919-1925`) | match |
| :187-191 SQLite failure → warning plus stateless continuation | `run_scan` catches `StateStoreError` only from `previous_file_index` (`doctor/core.py:2066-2076`); lane D test `test_doctor_scan_degrades…` | match for init failure; a failure in `persist` is not caught (SOURCE-CONFIRMED) |
| :200-204 structure is AST-only, works on files with broken deps | `structure/core.py:202-210` | match |
| :216-217 `-o` and `--update-doc` are "same idea" | both write the same render (`structure/core.py:337-341`); `--update-doc` also creates a missing file (P8) | match |
| :227-232 `--both` expansion planned, not done | no such flag | documented-only (plan) |
| :239-240, :320-323 config-file driven; error "No roots specified in configuration" | `pycache_cleaner/core.py:195` raises `ValueError` with that text | match |
| :254-256 example `exclude: "node_modules/*"`, `".git/*"` | excludes match **dir names** via `fnmatchcase(name, pat)` (`pycache_cleaner/core.py:263`, `:270`); path-style never matches (selftest) | DISCREPANCY (the example doesn't work) |
| :261 CLI `--dry-run` forces true | `pycache_cleaner/core.py:357-358` | match |
| :268 unknown keys warn and are ignored | `pycache_cleaner/core.py:179` | match (SOURCE-CONFIRMED) |
| :288-304 scaffold copies, refuses overwrite without `--force` | `scaffold.py:62-88`; H2/H4 | match |
| :291 "only TEST_NAME and execute_test() are project-specific" | true, but the shipped `execute_test` is a gp-cli/cargo test (harness.md H-1) | partial |
| :297 `init-test-harness .` (current directory) | root scaffold → `PROJECT_ROOT` = parent dir → artifacts outside the repo (harness.md H-2) | DISCREPANCY (outcome) |
| :312-318 zero files usually means copied Somnus globs; the root `python_doctor.yaml` is one | onboard adopting it → files=0 (`logs/s1_onboard_edges.log` E-O1) | match |
| :333 "9-test smoke suite" | 12 test functions now | stale |
| :364-369 root scripts are leftovers, safe to delete | not this lane | UNVERIFIED |
| :375-377 core.py "unmodified in substance"; anything from the old script is importable | duplicates diverge (brief lead) | UNVERIFIED (lane A) |
| :382-385 `build_index(source, source_name=...)` | signature `build_index(source, *, source_name, include_lines=True, include_module_functions=True)` (`structure/core.py:202-208`) | match |
| :387-389 imports incl. `DoctorConfig`, `scaffold` | present (`doctor/core.py:208`; `logs/s5_library_and_links.log`) | match |
| :409-410 CONTRACT "SUPREME for that scope", OPSEC "SUPREME overall" | governance statement; OPSEC absent | documented-only / dead |

## docs/Python_Doctor_QUICKSTART.md

| Doc claim | Source / run | Verdict |
|---|---|---|
| :44-46 doctor has zero pip deps; root `python_production_doctor.py` works standalone | stdlib imports only | match (root script not run) |
| :52 `somnus-doctor` standalone | `pyproject.toml` | match |
| :66 "see the generated file for the full set **with comments**" | `init-config` output has **0** comment lines (P1; `doctor/core.py:854-923`) | DISCREPANCY |
| :68-99 field excerpt | subset of `default_yaml()` | match |
| :102-105 only `include_patterns` are scanned, minus ignores | `ProjectFileIndex._discover` (`doctor/core.py:967-982`) | match |
| :113 bare path → scan | `normalize_argv` | match |
| :147-151 self-check scans the doctor's own package directory | yes, **and writes `self_check_report.{md,json}` into site-packages** (`doctor/core.py:2123-2127`; `logs/s4_C8_selfcheck.log`) | partial (side effect omitted) |
| :155-170 command reference | `build_parser` | match |
| :176-182 report has Summary, "Code quality metrics — docstring and type-hint coverage", file-by-file, dependency findings, action plan | actual sections: Summary, Issue Categories, Local State Delta, Dependency Map (+missing, cycles), Suspiciously Short Classes/Functions, Full Issue Index, File Diagnostics, Recommended Action Plan (`doctor/core.py:1783-1914`). There is **no docstring or type-hint coverage section**. | partial |
| :184-185 state under `.python_doctor/` | match | match |
| :189-196 exit codes "0 / non-zero" | 0/1/2/4/5 | partial |
| :203 `doctor scan . && git commit` | works as a gate, but writes `production_doctor_report.{md,json}` into the project root and state into `.python_doctor/` (`doctor/core.py:1955-1962`) | partial (pollution unmentioned) |
| :208-211 CI step `doctor scan . --json-output report.json` | gates on the raw doctor exit, so it fails on **pre-existing** serious findings. The fieldkit says gate on `delta.py` instead (`references/automation.md:65`). | partial (the two docs conflict) |
| :216-217 ignore specific functions or classes by name | `ignore_functions` hides the function **and its nested defs**; `ignore_classes` hides class-level checks only, and methods are still flagged (P5, P6) | partial |
| :233 `max_workers` is config-only, no `-j` | `build_parser` has no `-j` | match |
| :241 Markdown report default path when `-o` is omitted | `<project_root>/production_doctor_report.md` (`doctor/core.py:1960`) | match |
| :242 "JSON report (`--json-output`, **if requested**)" | JSON is **always** written (default `md.with_suffix('.json')`, `doctor/core.py:1961`; P3) | DISCREPANCY |
| :243 `production_doctor.log` always in cwd | `setup_logging` (`doctor/core.py:2179-2181`); selftest | match |
| :251-252 "Rollback on regression … restore a previous report as latest" | restores the report alias only; it also re-bases the next scan's `state_delta` (`logs/s3_C1_C3.log` C3g). Not a code rollback. | match (+ undocumented effect) |

## docs/PUBLISHING.md

| Doc claim | Source | Verdict |
|---|---|---|
| :35 published on PyPI (2026-10-19) | external fact; lane D checked PyPI | documented-only (this lane) |
| :41-43 `[project.urls]` points to calisweetleaf/somnus-debug | `pyproject.toml` | match |
| :47-48 authors has name only, no email | `pyproject.toml` `authors` | match |
| :52-54 sdist includes only src, README, LICENSE, docs/** | `[tool.hatch.build.targets.sdist] include` | match (SOURCE-CONFIRMED). The wheel has `packages=["src/somnus_debug"]`. |
| :112 `pyproject.toml` version is the "single source of truth (no dynamic versioning)" | a second hard-coded copy exists: `__version__ = "0.1.0"` (`__init__.py:57`, used by `--version`). They agree today (P9). | DISCREPANCY (two sources) |
| :125-127 MIT license, classifiers, 3.10–3.12, console scripts | `pyproject.toml` | match |
| :129-132 hatch build excludes runtime artifacts | `[tool.hatch.build] exclude` | match. Note: `self-check` writes `self_check_report.md` (matched by `*_report.md`) into site-packages *after* install, outside packaging scope. |
| :133-136 build, editable install, wheel install, twine verified | install of the repo dir verified here (`logs/s0_setup.log`); twine not run | partial |
| :137-138 pyyaml is the one real runtime dep | match | match |
| :145-149 GitHub and PyPI sanitizers degrade the styled README | README.md now keeps the CSS/SVG inside HTML comments and renders native Markdown (README.md:39-42, :86-90) | stale (the README was adapted) |

## docs/AGENTS_APPENDIX.md

| Doc claim | Source / fieldkit | Verdict |
|---|---|---|
| :45-47 "prefer `pipx install somnus-debug`" | an isolated tool env means doctor resolves third-party imports in the wrong interpreter, giving `missing_imports` noise. The fieldkit says to install into the project venv (`skills/.../references/install.md:43-52`; selftest's missing_imports checks). | DISCREPANCY (conflicts with fieldkit) |
| :68-70 generated default includes every `*.py`; Somnus-style globs → zero files exit 0 | selftest "zero-file scan exits 0" | match |
| :71-73 avoid pollution with `--no-state` and explicit report paths; stateful scans create `.python_doctor/` | match | match |
| :74-76 SQLite unavailable → warning plus stateless | `doctor/core.py:2066-2076` | match |
| :77-79 pycache dry-run first | match | match |
| :80-82 init-test-harness refuses overwrite unless forced | H2/H4 | match |
| :85 relative link `../skills/somnus-debug-fieldkit/SKILL.md` **inside the pasteable block** | resolves in this repo; dead once pasted into another repo's AGENTS.md | partial (portability) |
| (whole file) vs `skills/.../templates/AGENTS_APPENDIX.md` | two different appendices: the docs one is a global "use it as evidence" block; the fieldkit one is the profile/loop block (`.somnus-debug/PROFILE.md`, delta). README.md:374 points to the docs one; the fieldkit SKILL points to its own. | documented divergence |

## docs/CONTRACT.md (cross-doc items only)

| Doc claim | Verdict |
|---|---|
| :123 "Copy this directory into the repository" vs scaffold default `.` | DISCREPANCY in combination (harness.md H-2) |
| :61-70 stable contract items | match (harness.md §4) |
