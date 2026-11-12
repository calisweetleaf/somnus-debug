# Lane D: experiment log

Every command Lane D ran, in order. All runs went through a small runner (`/tmp/lane-d/x.py`, since wiped with /tmp) that set `PYTHONDONTWRITEBYTECODE=1` and snapshotted files under a WATCH dir before and after each run. `experiments.jsonl` holds the full stdout/stderr (capped at 4 KB) and the new/changed/removed file lists for each run. `$V=/tmp/lane-d/venv/bin` (0.1.0 installed from this repo). `$R=<repo>`. `~/` = `/tmp/lane-d/`. Fixtures are described at the end.

Environment caveats:
- The sandbox tool display rewrites ISO-8601 timestamps into "Wed 2026-11-11 6:12 PM CST" form. The bytes on disk are ISO (I checked with hex). This is not doctor behavior.
- `/tmp/lane-d/` disappeared from the sandbox around 00:20 UTC, after all runs had finished. This file, `experiments.jsonl`, and the other deliverables were already in the findings dir. The /tmp copy of the root `run_test.py --help` artifacts (see install-vs-source.md §7) was lost with it.

## Pre-experiment steps

| Step | cwd | Command | Exit | Result |
|---|---|---|---|---|
| venv | ~/ | `python3 -m venv venv && venv/bin/pip install -q pytest <repo>` | 0 | 4 console scripts; no init-test-harness script |
| pypi | ~/ | `pip download somnus-debug==0.1.0 --no-deps [--no-binary :all:] -d pypi` | 0 | wheel + sdist; see install-vs-source.md |
| tests | ~/repo-copy | `venv/bin/python -m pytest -q -p no:cacheprovider tests/` | 1 | **10 passed, 2 failed** (see test-coverage.md) |
| help | ~/run/help | 31 help invocations (help-surfaces-raw.txt) | 0, except root run_test.py (1) | root `run_test.py --help` executed the test and wrote to `forge/test-runs/` (removed by me) |

## Runs

| ID | cwd | Command | Exit | Artifacts (new/changed/removed) | Interpretation |
|---|---|---|---|---|---|
| D01 | `~/fx/w1` | `$V/somnus-debug doctor scan .` | 2 | new: fx/w1/.python_doctor/reports/20261112T001259Z/production_doctor_report.json, fx/w1/.python_doctor/reports/20261112T001259Z/production_doctor_report.md, fx/w1/.python_doctor/reports/latest.json, fx/w1/.python_doctor/reports/latest.md, fx/w1/.python_doctor/state.sqlite3, fx/w1/production_doctor.log … | Baseline scan of fixture proj (state on): 90 issues, critical from broken.py. Writes 2 root reports + .python_doctor/ state + empty production_doctor.log in CWD. |
| D02 | `~/fx/proj2` | `$V/somnus-debug doctor scan . --no-state` | 2 | new: fx/proj2/production_doctor.log, fx/proj2/production_doctor_report.json, fx/proj2/production_doctor_report.md | proj2 detector coverage: security, complexity, short class, incomplete_methods, all 6 debt markers, read error. `from pkg import x` cycle MISSED. Read error counted as syntax_error_files. |
| D03 | `~/fx/proj3` | `$V/somnus-debug doctor scan . --no-state` | 1 | new: fx/proj3/production_doctor.log, fx/proj3/production_doctor_report.json, fx/proj3/production_doctor_report.md | proj3: `import pkg.b` form, so the cycle is detected. Serious-only → exit 1. |
| D04 | `~/fx/w2` | `$V/somnus-debug doctor scan . --no-state` | 2 | new: fx/w2/production_doctor.log, fx/w2/production_doctor_report.json, fx/w2/production_doctor_report.md | PYTHONPATH=src resolves src-layout own imports (missing_imports 3→1). |
| D05a | `~/fx/tp` | `$V/somnus-debug doctor scan . --no-state` | 0 | new: fx/tp/production_doctor.log, fx/tp/production_doctor_report.json, fx/tp/production_doctor_report.md | venv interpreter has pytest → third_party resolved. |
| D05b | `~/fx/tp` | `env PYTHONPATH=$R/src python3 -m somnus_debug.cli doctor scan . --no-state` | 1 | chg: fx/tp/production_doctor_report.json, fx/tp/production_doctor_report.md | system python lacks pytest → missing_imports serious. Resolution depends on doctor interpreter. |
| D06 | `~/fx/w1` | `$V/somnus-debug doctor scan .` | 2 | new: fx/w1/.python_doctor/reports/20261112T001411Z/production_doctor_report.json, fx/w1/.python_doctor/reports/20261112T001411Z/production_doctor_report.md; chg: fx/w1/.python_doctor/reports/latest.json, fx/w1/.python_doctor/reports/latest.md, fx/w1/.python_doctor/state.sqlite3, fx/w1/production_doctor_report.json, fx/w1/production_doctor_report.md | 2nd stateful scan after an edit: state_delta.modified_files=[helpers.py]. New run dir. |
| D07 | `~/fx/w1` | `$V/somnus-debug doctor history .` | 0 | — | history lists 2 runs. |
| D08 | `~/fx/w1` | `$V/somnus-debug doctor history . --limit 1` | 0 | — | --limit 1 honored. |
| D09 | `~/fx/w1` | `$V/somnus-debug doctor rollback . --run-id 20261112T001259Z` | 0 | chg: fx/w1/.python_doctor/reports/latest.json, fx/w1/.python_doctor/reports/latest.md, fx/w1/.python_doctor/state.sqlite3 | rollback rewrites latest.{md,json} and the alias. |
| D10 | `~/fx/w1` | `$V/somnus-debug doctor rollback . --run-id NOPE` | 4 | chg: fx/w1/production_doctor.log | unknown run-id → DoctorError exit 4. |
| D11 | `~/fx/w1` | `$V/somnus-debug doctor rollback .` | 2 | — | missing --run-id → argparse 2. |
| D12 | `~/fx/w1` | `$V/somnus-debug doctor history ~/fx/proj2` | 0 | — | history on a never-scanned project: "No recorded runs found." exit 0. Creates .python_doctor/state.sqlite3 there (outside WATCH, observed by ls). |
| D13 | `~/fx/w1` | `two scans back-to-back same second` | see | two raw shell runs; see stdout | Two scans in the same second: identical Run ID. DB keeps 1 row (INSERT OR REPLACE), so history is silently lost. |
| D14 | `~/run/sc` | `$V/somnus-debug doctor self-check` | 1 | new: venv/lib/python3.12/site-packages/somnus_debug/doctor/.python_doctor/reports/20261112T001446Z/production_doctor_report.json, venv/lib/python3.12/site-packages/somnus_debug/doctor/.python_doctor/reports/20261112T001446Z/production_doctor_report.md, venv/lib/python3.12/site-packages/somnus_debug/doctor/.python_doctor/reports/latest.json, venv/lib/python3.12/site-packages/somnus_debug/doctor/.python_doctor/reports/latest.md, venv/lib/python3.12/site-packages/somnus_debug/doctor/.python_doctor/state.sqlite3, venv/lib/python3.12/site-packages/somnus_debug/doctor/self_check_report.json … | self-check writes self_check_report.* and .python_doctor/ INTO site-packages/somnus_debug/doctor/. 17 serious on itself → exit 1. |
| D15 | `~/run/sc` | `$V/somnus-doctor self-check --no-state -o ~/run/sc/sc.md --json-output ~/run/sc/sc.json` | 1 | — | self-check --no-state -o/--json-output redirects outputs. Nothing written to the package dir. |
| D16 | `~/run/err` | `$V/somnus-debug doctor scan ~/does-not-exist --no-state` | 4 | new: run/err/production_doctor.log | nonexistent root → exit 4. |
| D17 | `~/run/err` | `$V/somnus-debug doctor scan ~/run/err/empty --no-state` | 0 | new: run/err/empty/production_doctor_report.json, run/err/empty/production_doctor_report.md | empty dir → files=0 exit 0. |
| D18 | `~/run/err` | `$V/somnus-debug doctor scan ~/fx/proj/src/mypkg/helpers.py --no-state -o ~/run/err/file.md --json-output ~/run/err/file.json` | 4 | chg: run/err/production_doctor.log | file as root → exit 4. |
| D19 | `~/run/err` | `$V/somnus-debug doctor --bogus` | 2 | — | unknown doctor flag → 2. |
| D20 | `~/run/err` | `$V/somnus-debug doctor scan --bogus` | 2 | — | unknown scan flag → 2 (error attributed to the parent parser). |
| D21 | `~/run/err` | `$V/somnus-debug doctor scan . -c ~/run/err/missing.yaml --no-state` | 4 | chg: run/err/production_doctor.log | missing config → 4. |
| D22 | `~/run/err` | `$V/somnus-debug doctor init-config -o ~/run/err/cfg.yaml` | 0 | new: run/err/cfg.yaml | init-config -o writes. |
| D23 | `~/run/err` | `$V/somnus-debug doctor init-config -o ~/run/err/cfg.yaml` | 4 | chg: run/err/production_doctor.log | init-config refuses overwrite → 4. |
| D24 | `~/run/err` | `$V/somnus-debug doctor init-config -o ~/run/err/cfg.yaml --force` | 0 | chg: run/err/cfg.yaml | --force overwrites. |
| D25 | `~/run/err` | `$V/somnus-debug doctor init-config` | 0 | new: run/err/python_doctor.yaml | default name python_doctor.yaml in CWD. |
| D26_none | `~/run/cfg` | `$V/somnus-debug doctor scan p -c ~/run/cfg/g_none.yaml --no-state -o ~/run/cfg/o_none.md --json-output ~/run/cfg/o_none.json` | 0 | new: run/cfg/o_none.json, run/cfg/o_none.md, run/cfg/production_doctor.log | gate none → 0 despite critical. |
| D26_critical | `~/run/cfg` | `$V/somnus-debug doctor scan p -c ~/run/cfg/g_critical.yaml --no-state -o ~/run/cfg/o_critical.md --json-output ~/run/cfg/o_critical.json` | 2 | new: run/cfg/o_critical.json, run/cfg/o_critical.md | gate critical → 2. |
| D26_serious | `~/run/cfg` | `$V/somnus-debug doctor scan p -c ~/run/cfg/g_serious.yaml --no-state -o ~/run/cfg/o_serious.md --json-output ~/run/cfg/o_serious.json` | 2 | new: run/cfg/o_serious.json, run/cfg/o_serious.md | gate serious → 2. |
| D26_minor | `~/run/cfg` | `$V/somnus-debug doctor scan p -c ~/run/cfg/g_minor.yaml --no-state -o ~/run/cfg/o_minor.md --json-output ~/run/cfg/o_minor.json` | 1 | new: run/cfg/o_minor.json, run/cfg/o_minor.md | gate minor → 1 despite critical=2. |
| D26_info | `~/run/cfg` | `$V/somnus-debug doctor scan p -c ~/run/cfg/g_info.yaml --no-state -o ~/run/cfg/o_info.md --json-output ~/run/cfg/o_info.json` | 1 | new: run/cfg/o_info.json, run/cfg/o_info.md | gate info → 1 despite critical=2. |
| D26_bogus | `~/run/cfg` | `$V/somnus-debug doctor scan p -c ~/run/cfg/g_bogus.yaml --no-state -o ~/run/cfg/o_bogus.md --json-output ~/run/cfg/o_bogus.json` | 4 | chg: run/cfg/production_doctor.log | invalid gate → 4. |
| D27 | `~/run/cfg` | `$V/somnus-debug doctor scan p --no-state -o ~/run/cfg/auto.md --json-output ~/run/cfg/auto.json` | 2 | new: run/cfg/auto.json, run/cfg/auto.md | python_doctor.yaml (gate none) in the project root is NOT auto-read → exit 2. |
| D27b | `~/run/cfg/p` | `$V/somnus-debug doctor scan . --no-state -o ~/run/cfg/auto2.md --json-output ~/run/cfg/auto2.json` | 2 | new: run/cfg/auto2.json, run/cfg/auto2.md, run/cfg/p/production_doctor.log | same with CWD=project root → still not read. |
| D28 | `~/run/cfg` | `$V/somnus-debug doctor scan p -c ~/run/cfg/partial.yaml --no-state -o ~/run/cfg/x.md --json-output ~/run/cfg/x.json` | 0 | new: run/cfg/x.json, run/cfg/x.md | partial YAML merges with defaults (gate none → 0). |
| D29 | `~/run/cfg` | `$V/somnus-debug doctor scan p -c ~/run/cfg/b2.yaml --no-state -o ~/run/cfg/x.md --json-output ~/run/cfg/x.json` | 2 | chg: run/cfg/x.json, run/cfg/x.md | unknown config key silently accepted. |
| D30 | `~/run/cfg` | `$V/somnus-debug doctor scan p -c ~/run/cfg/bad.yaml --no-state -o ~/run/cfg/x.md --json-output ~/run/cfg/x.json` | 2 | chg: run/cfg/x.json, run/cfg/x.md | malformed YAML `schema_version: [` silently accepted. Defaults used. |
| D31 | `~/run/cfg` | `$V/somnus-debug doctor scan p -c ~/run/cfg/cfg.json --no-state -o ~/run/cfg/x.md --json-output ~/run/cfg/x.json` | 4 | chg: run/cfg/production_doctor.log | First attempt: my helper failed to create cfg.json → exit 4 "Configuration file does not exist". |
| D31 | `~/run/cfg` | `$V/somnus-debug doctor scan p -c ~/run/cfg/cfg.json --no-state -o ~/run/cfg/x.md --json-output ~/run/cfg/x.json` | 0 | chg: run/cfg/x.json, run/cfg/x.md | JSON config, gate none → 0. |
| D32 | `~/run/cfg` | `$V/somnus-debug doctor scan p -c ~/run/cfg/part.json --no-state -o ~/run/cfg/x.md --json-output ~/run/cfg/x.json` | 0 | chg: run/cfg/x.json, run/cfg/x.md | partial JSON include_patterns narrows the scan to 1 file. |
| D33 | `~/run/cfg` | `$V/somnus-debug doctor scan p -c ~/run/cfg/badj.json --no-state -o ~/run/cfg/x.md --json-output ~/run/cfg/x.json` | 4 | chg: run/cfg/production_doctor.log | malformed JSON → 4. |
| D34 | `~/run/cfg` | `$V/somnus-debug doctor scan p -c ~/run/cfg/badbool.yaml --no-state -o ~/run/cfg/x.md --json-output ~/run/cfg/x.json` | 4 | chg: run/cfg/production_doctor.log | non-bool → 4. |
| D35 | `~/run/cfg/p` | `$V/somnus-doctor --no-state -o ~/run/cfg/leg.md --json-output ~/run/cfg/leg.json` | 2 | new: run/cfg/leg.json, run/cfg/leg.md | legacy flags-first `somnus-doctor --no-state …` → scan . (cwd). |
| D36 | `~/run/cfg` | `$V/somnus-doctor p --no-state -o ~/run/cfg/leg2.md --json-output ~/run/cfg/leg2.json` | 2 | new: run/cfg/leg2.json, run/cfg/leg2.md | legacy positional `somnus-doctor p`. |
| D37 | `~/run/cfg` | `$V/somnus-debug doctor p --no-state -o ~/run/cfg/leg3.md --json-output ~/run/cfg/leg3.json` | 2 | new: run/cfg/leg3.json, run/cfg/leg3.md | legacy positional via dispatcher. |
| D38 | `~/run/x5/e` | `$V/somnus-debug doctor` | 0 | new: run/x5/e/.python_doctor/reports/20261112T001530Z/production_doctor_report.json, run/x5/e/.python_doctor/reports/20261112T001530Z/production_doctor_report.md, run/x5/e/.python_doctor/reports/latest.json, run/x5/e/.python_doctor/reports/latest.md, run/x5/e/.python_doctor/state.sqlite3, run/x5/e/production_doctor.log … | `somnus-debug doctor` with no args = stateful scan of CWD. |
| D39 | `~/run/x5` | `$V/somnus-debug doctor scan p -o ~/run/x5/c.md --json-output ~/run/x5/c.json` | 2 | new: run/x5/c.json, run/x5/c.md, run/x5/production_doctor.log | garbage state.sqlite3: scan degrades with a stderr warning, reports written, gate exit. |
| D40 | `~/run/x5` | `$V/somnus-debug doctor history p` | 4 | chg: run/x5/production_doctor.log | history on garbage DB → 4. |
| D41 | `~/run/x5` | `$V/somnus-debug doctor rollback p --run-id X` | 4 | chg: run/x5/production_doctor.log | rollback on garbage DB → 4. |
| D42 | `~/run/x5` | `$V/somnus-debug doctor history p --limit abc` | 2 | — | --limit abc → 2. |
| D43 | `~/run/x5` | `$V/somnus-debug doctor scan p --no-state -o ~/run/x5/ro/sub/r.md --json-output ~/run/x5/ro/r.json` | 4 | chg: run/x5/production_doctor.log | unwritable -o dir → 4. |
| D44 | `~/run/x5b` | `$V/somnus-debug doctor scan p --no-state` | 5 | new: run/x5b/production_doctor.log | 20k-term expression → RecursionError → whole scan aborts with exit 5. Traceback in log. |
| S01 | `~/run/st` | `$V/somnus-debug structure ~/fx/proj/src/mypkg/stamped.py` | 2 | — | installed dispatcher crashes on stamped file (type_comments). |
| S02 | `~/run/st` | `$V/somnus-structure ~/fx/proj/src/mypkg/stamped.py` | 2 | — | installed somnus-structure: same crash. |
| S03 | `~/run/st` | `env PYTHONPATH=$R/src python3 -m somnus_debug.cli structure ~/fx/proj/src/mypkg/stamped.py` | 2 | — | source via PYTHONPATH: same crash. |
| S04 | `~/run/st` | `python3 $R/analyze_python_structure.py ~/fx/proj/src/mypkg/stamped.py` | 0 | — | root analyze_python_structure.py succeeds on stamped file. |
| S05 | `~/run/st` | `env PYTHONPATH=~/pypi/whl python3 -m somnus_debug.cli structure ~/fx/proj/src/mypkg/stamped.py` | 2 | — | PyPI wheel crashes on stamped file. |
| S06 | `~/run/st` | `env PYTHONPATH=~/pypi/whl python3 -m somnus_debug.cli structure ~/pypi/whl/somnus_debug/structure/core.py` | 0 | — | PyPI wheel indexes its own headerless core.py fine. |
| S07 | `~/run/st` | `$V/somnus-debug structure $R/src/somnus_debug/structure/core.py` | 2 | — | src structure crashes on its own core.py (header line 10). |
| S08 | `~/run/st` | `python3 $R/analyze_python_structure.py $R/src/somnus_debug/structure/core.py` | 0 | — | root script indexes src core.py fine. |
| S09 | `~/run/st` | `$V/somnus-debug structure ~/fx/proj/src/mypkg/issues.py` | 0 | — | full index of issues.py. Property/setter and overloads listed with decorators. |
| S10 | `~/run/st` | `$V/somnus-debug structure ~/fx/proj/src/mypkg/issues.py --no-line-numbers --no-module-functions --source-label LABEL.py` | 0 | — | flags honored. Count still includes the omitted module functions. |
| S11 | `~/run/st` | `$V/somnus-debug structure ~/fx/proj/src/mypkg/issues.py -o ~/run/st/out/idx.md` | 0 | new: run/st/out/idx.md | -o creates parent dirs. |
| S12 | `~/run/st` | `$V/somnus-debug structure ~/fx/proj/src/mypkg/issues.py --update-doc ~/run/st/never-existed.md` | 0 | new: run/st/never-existed.md | --update-doc creates a file that did not exist. |
| S13 | `~/run/st` | `$V/somnus-debug structure ~/fx/proj/src/mypkg/issues.py -o a.md --update-doc b.md` | 2 | — | -o + --update-doc → 2. |
| S14 | `~/run/st` | `$V/somnus-debug structure ~/run/st/missing.py` | 2 | — | missing file → 2. |
| S15 | `~/run/st` | `$V/somnus-debug structure ~/fx/proj/src/mypkg/broken.py` | 2 | — | syntax error → 2. |
| S16 | `~/run/st` | `$V/somnus-debug structure` | 2 | — | no source → 2. |
| S17 | `~/run/st` | `$V/somnus-debug structure ~/fx/proj/src/mypkg` | 2 | — | directory → 2. |
| P01 | `~/run/pc` | `$V/somnus-debug pycache-clean --dry-run` | 0 | new: run/pc/clean.log | dry-run via default ./config.yaml. Summary says "deleted". Missing root → ERROR, exit 0. log_file created. |
| P02 | `~/run/pc` | `$V/somnus-debug pycache-clean --dry-run --verbose` | 0 | chg: run/pc/clean.log | dry-run --verbose says "Removed …" for every item, though nothing was deleted. |
| P03 | `~/run/pc` | `$V/somnus-pycache-clean --config ~/run/pc/config.yaml` | 0 | chg: run/pc/clean.log; rm: run/pc/tree/a/__pycache__/m.cpython-312.pyc, run/pc/tree/a/b/c/__pycache__/n.pyc, run/pc/tree/a/b/old.pyo, run/pc/tree/a/loose.pyc | real run via standalone script: 2 dirs + 2 files removed. Excludes respected. |
| P04 | `~/run/pc2/empty` | `$V/somnus-debug pycache-clean` | 1 | — | no config.yaml in CWD → 1. |
| P05 | `~/run/pc2` | `$V/somnus-debug pycache-clean --config ~/run/pc2/noroots.yaml` | 1 | — | roots: [] → 1 with logged traceback. |
| P06 | `~/run/pc2` | `$V/somnus-debug pycache-clean --config ~/run/pc2/bad.yaml` | 1 | — | malformed YAML → uncaught traceback, 1. |
| P07 | `~/run/pc2` | `$V/somnus-debug pycache-clean --config ~/run/pc2/list.yaml` | 1 | — | YAML list → AttributeError traceback, 1. |
| P08 | `~/run/pc2` | `$V/somnus-debug pycache-clean --max-depth x` | 2 | — | bad --max-depth → 2. |
| P09 | `~/run/pc2` | `$V/somnus-debug pycache-clean --config ~/run/pc2/d.yaml --max-depth 0 --verbose` | 0 | rm: run/pc2/t/__pycache__/b.pyc | unknown-key warning pre-empts logging setup, so all INFO/verbose output is lost. --max-depth 0 cleans only the top level. |
| P10 | `~/run/pc2` | `$V/somnus-debug pycache-clean --bogus` | 2 | — | unknown flag → 2. |
| H01 | `~/run/th` | `$V/somnus-debug init-test-harness repo` | 0 | new: run/th/repo/CONTRACT.md, run/th/repo/run_test.py | scaffold writes run_test.py + CONTRACT.md. |
| H02 | `~/run/th` | `$V/somnus-debug init-test-harness repo` | 1 | — | refuses overwrite → 1. |
| H03 | `~/run/th` | `$V/somnus-debug init-test-harness repo --force --no-contract` | 0 | chg: run/th/repo/run_test.py | --force --no-contract overwrites run_test.py only. |
| H04 | `~/run/th` | `$V/somnus-debug init-test-harness newdir/sub --no-contract` | 0 | new: run/th/newdir/sub/run_test.py | creates missing target dirs. |
| H05 | `~/run/th/repo` | `$V/somnus-debug init-test-harness` | 1 | — | default target "." refuses (files exist). |
| H06 | `~/run/th` | `$V/somnus-debug init-test-harness --bogus` | 2 | — | unknown flag → 2. |
| H07 | `~/run/th` | `$V/somnus-debug init-test-harness afile` | 1 | — | target is a file → 1. |
| H08 | `~/run/th/repo` | `python3 run_test.py` | 1 | new: run/th/test-runs/GOLDEN-PATH-LAYER-1-DATA-HIGHWAY-RESTORATION-20261112-001634-bafcdc/manifest.json, run/th/test-runs/GOLDEN-PATH-LAYER-1-DATA-HIGHWAY-RESTORATION-20261112-001634-bafcdc/report.md, run/th/test-runs/GOLDEN-PATH-LAYER-1-DATA-HIGHWAY-RESTORATION-20261112-001634-bafcdc/test.log | scaffolded run_test.py at repo root: artifacts land in <repo>/../test-runs. Default cargo test FAILs. |
| H09 | `~/run/th/repo` | `env PROJECT_ROOT=~/run/th/repo python3 run_test.py --help` | 1 | new: run/th/repo/test-runs/GOLDEN-PATH-LAYER-1-DATA-HIGHWAY-RESTORATION-20261112-001634-e01893/manifest.json, run/th/repo/test-runs/GOLDEN-PATH-LAYER-1-DATA-HIGHWAY-RESTORATION-20261112-001634-e01893/report.md, run/th/repo/test-runs/GOLDEN-PATH-LAYER-1-DATA-HIGHWAY-RESTORATION-20261112-001634-e01893/test.log | --help ignored. PROJECT_ROOT override puts artifacts under the repo. |
| H10 | `~/run/th/repo2` | `python3 tools/run_test.py` | 0 | new: run/th/repo2/test-runs/GOLDEN-PATH-LAYER-1-DATA-HIGHWAY-RESTORATION-20261112-001634-592189/manifest.json, run/th/repo2/test-runs/GOLDEN-PATH-LAYER-1-DATA-HIGHWAY-RESTORATION-20261112-001634-592189/report.md, run/th/repo2/test-runs/GOLDEN-PATH-LAYER-1-DATA-HIGHWAY-RESTORATION-20261112-001634-592189/test.log | edited harness at <repo>/tools/: PASS, exit 0, artifacts in <repo>/test-runs. |
| C01 | `~/run/disp` | `$V/somnus-debug not-a-command` | 2 | — | unknown command → 2. |
| C02 | `~/run/disp` | `$V/somnus-debug doctor --version` | 2 | new: run/disp/production_doctor.log | doctor --version → normalized to scan → 2. Log created. |
| C03 | `~/run/disp` | `$V/somnus-debug structure --version` | 2 | — | structure --version → 2. |
| C04 | `~/run/disp` | `$V/python -m somnus_debug --help` | 1 | — | no somnus_debug.__main__ → 1. |
| C05 | `~/run/disp` | `$V/python -m somnus_debug.doctor --help` | 1 | — | no doctor.__main__ → 1. |
| C06 | `~/run/disp` | `$V/python -m somnus_debug.structure.core --help` | 0 | — | structure.core runnable via -m, with a RuntimeWarning. |
| C07 | `~/run/disp` | `$V/somnus-debug --help extra` | 0 | — | extra args after --help ignored. |
| F01 | `~/fk` | `env PATH=~/venv/bin:/usr/bin:/bin python3 somnus-debug-fieldkit/scripts/selftest.py` | 0 | — | fieldkit selftest 29/29 against the venv CLI on PATH. |
| F02 | `~/fk` | `env PYTHONPATH=~/repo-copy/src PATH=/usr/bin:/bin:/usr/local/bin python3 somnus-debug-fieldkit/scripts/selftest.py --python python3` | 1 | — | selftest --python with /usr/bin/python3 (no PyYAML): 1/24, because the dispatcher import of pycache_cleaner fails. |
| F03 | `~/fk` | `env PATH=/usr/bin:/bin python3 somnus-debug-fieldkit/scripts/selftest.py` | 3 | — | no CLI on PATH → selftest exit 3. |
| F02b | `~/fk` | `env PYTHONPATH=~/repo-copy/src /usr/bin/python3 -m somnus_debug.cli doctor --help` | 1 | — | yaml-less interpreter: even `doctor --help` fails via the dispatcher. |
| F02c | `~/fk` | `env PYTHONPATH=~/repo-copy/src /usr/local/bin/python3 somnus-debug-fieldkit/scripts/selftest.py --python /usr/local/bin/python3` | 1 | — | selftest --python with PYTHONPATH=src: 28/29. The src-layout check fails because selftest overwrites PYTHONPATH (harness artifact). |
| O01 | `~/run/ob` | `python3 fk/onboard.py repo` | 0 | — | onboard plan on fixture repo: src layout detected, PATH runner, nothing written. |
| O02 | `~/run/ob` | `python3 fk/onboard.py repo --apply --baseline` | 0 | new: run/ob/repo/.somnus-debug/.gitignore, run/ob/repo/.somnus-debug/PROFILE.md, run/ob/repo/.somnus-debug/dispositions.json, run/ob/repo/.somnus-debug/production_doctor.log, run/ob/repo/.somnus-debug/pycache.yaml, run/ob/repo/.somnus-debug/python_doctor.yaml … | --apply --baseline: writes .somnus-debug/{python_doctor.yaml,pycache.yaml,dispositions.json,.gitignore,PROFILE.md}, state/, runs/baseline.*. production_doctor.log lands in .somnus-debug/. |
| O03 | `~/run/ob` | `python3 fk/onboard.py repo --apply --baseline` | 0 | chg: run/ob/repo/.somnus-debug/runs/baseline.json, run/ob/repo/.somnus-debug/runs/baseline.md, run/ob/repo/.somnus-debug/state/reports/20261112T001726Z/production_doctor_report.json, run/ob/repo/.somnus-debug/state/reports/20261112T001726Z/production_doctor_report.md, run/ob/repo/.somnus-debug/state/reports/latest.json, run/ob/repo/.somnus-debug/state/reports/latest.md … | rerun: profile files kept, baseline rewritten (same-second run_id reused). |
| O04 | `/tmp/lane-d` | `python3 fk/onboard.py ~/run/ob2` | 2 | chg: run/ob2/.git/index | plan mode on repo copy: adopts root python_doctor.yaml → 0 files → FAIL exit 2. .git/index touched. |
| O05 | `~/run/ob3` | `env PATH=/usr/bin:/bin /usr/local/bin/python3 fk/onboard.py ~/run/ob3` | 3 | — | no CLI → 3. |
| O06 | `~/run/ob3` | `/usr/local/bin/python3 fk/onboard.py ~/run/ob3/nope` | 1 | — | bad repo path → 1. |
| O07 | `~/run/ob3` | `/usr/local/bin/python3 fk/onboard.py ~/run/ob3 --baseline` | 3 | — | --baseline without CLI → 3. |
| O08 | `~/run/ob3` | `python3 fk/onboard.py ~/run/ob3 --apply` | 2 | new: run/ob3/.somnus-debug/.gitignore, run/ob3/.somnus-debug/PROFILE.md, run/ob3/.somnus-debug/dispositions.json, run/ob3/.somnus-debug/pycache.yaml, run/ob3/.somnus-debug/python_doctor.yaml | --apply on empty dir writes the profile despite the zero-file FAIL (exit 2). |
| T01 | `~/run/ob` | `python3 fk/delta.py ~/run/ob/repo/.somnus-debug/runs/baseline.json ~/run/ob/same.json` | 0 | — | delta on identical reports → 0 CLEAN. |
| T02 | `~/run/ob` | `python3 fk/delta.py ~/run/ob/repo/.somnus-debug/runs/baseline.json ~/run/ob/l1.json` | 1 | — | new eval/bare-except → 1 REGRESSION. |
| T03 | `~/run/ob` | `python3 fk/delta.py ~/run/ob/repo/.somnus-debug/runs/baseline.json ~/run/ob/l1.json --dispositions ~/run/ob/disp.json` | 0 | — | dispositions suppress findings. Stale disposition reported. 0. |
| T04 | `~/run/ob` | `python3 fk/delta.py ~/run/ob/repo/.somnus-debug/runs/baseline.json ~/run/ob/drop.json` | 2 | — | dropped files still on disk → 2. |
| T05 | `~/run/ob` | `python3 fk/delta.py ~/run/ob/repo/.somnus-debug/runs/baseline.json ~/run/ob/zero.json --json` | 2 | — | zero-file latest with --json → 2. |
| T06 | `~/run/ob` | `python3 fk/delta.py ~/run/ob/repo/.somnus-debug/runs/baseline.json ~/run/ob/missing.json` | 3 | — | missing report → 3. |
| T07 | `~/run/ob` | `python3 fk/delta.py ~/run/ob/repo/.somnus-debug/runs/baseline.json ~/run/ob/bad.json` | 3 | — | malformed JSON → 3. |
| T08 | `~/run/ob` | `python3 fk/delta.py ~/run/ob/repo/.somnus-debug/runs/baseline.json ~/run/ob/l1.json --dispositions ~/run/ob/disp_noreason.json` | 3 | — | disposition without reason → 3. |

## Fixtures

- `fx/proj` (src layout): `src/mypkg/issues.py` contains:
  - bare except; silent except; except with `obj.logger.error`; except with `log.exception`; proper `logger.exception` + raise
  - TODO stub; NotImplementedError; `...` stub; print
  - duplicate `dup` returning 1 and 2; property + setter; `abc.abstractmethod`; Protocol; 3× `ov` with @overload
  - `from mypkg.helpers import helper_fn`; `import totally_missing_module_xyz`
  - `API_KEY = "sk-live-…"`; `password = "hunter2hunter2"`
  - Other files: `helpers.py`; `broken.py` (`def oops(:`); `stamped.py` (the real 32-line header copied from `src/somnus_debug/cli.py:1-32`, with `#     type: "source-code"` at line 9); `tests/test_helpers.py`.
- `fx/proj2` (flat):
  - `pkg/a.py` ↔ `pkg/b.py` cycle via `from pkg import x`
  - `pkg/risky.py`: pickle.loads, subprocess.run shell=True, os.system, eval, `except Exception`, CC=16 function, docstring-only class, ABC with 2 abstract methods + partial subclass, FIXME/HACK/XXX/TEMP/WIP/lowercase todo
  - `pkg/badenc.py` (non-UTF-8 bytes)
- `fx/proj3`: proj2 minus badenc, with the cycle rewritten as `import pkg.b as b` / `import pkg.a as a`.
- `fx/tp/tp.py`: `import pytest; import yaml`.

## Not run / blocked

- `pycache-clean --follow-symlinks` with a symlink loop: not exercised (UNVERIFIED).
- A doctor exit 5 from a sqlite3.Error during `persist`: not reproduced. Exit 5 was reached only via RecursionError (D44).
- Windows long-path behavior of pycache-clean: not testable here.
- Python 3.10/3.11 (pyproject claims >=3.10): only 3.12 (venv) and 3.13 (/usr/bin/python3, no PyYAML) were available.
