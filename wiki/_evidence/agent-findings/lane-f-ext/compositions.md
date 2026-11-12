# Lane F: compositions of verified capabilities

Classification:
- **supported now**: works with shipped tools plus shell glue and no code changes; recipe executed.
- **small integration step**: works, but needs user-authored glue code or a workaround for a known defect.
- **research idea**: not built; would need new code.

All recipes live in `recipes/`, all runs in `repro/s3_compositions.sh`, `repro/s4_harness_more.sh` and `repro/s5_extension_probes.sh`, with logs in `logs/`. Runner used: `PRUN = env PYTHONPATH=<proj>/src <proj>/.venv/bin/python -m somnus_debug.cli`, which is exactly what onboard wrote into PROFILE.md (`logs/s1_PROFILE.md.txt`).

## Summary

| # | Composition | Class | Verified result |
|---|---|---|---|
| C1 | doctor JSON → `delta.py` regression gate (CI / pre-handoff) | supported now | clean 0 · regression 1 · doctor config error → 3 (`logs/s3_C1_C3.log`) |
| C2 | structure index → targeted reading | supported now | prints only the named definitions' source spans (`logs/s3_C2.log` C2a) |
| C2b | delta `--json` → doctor JSON `files[].functions/classes` spans → read only offending definitions (with stale-report guard) | supported now (recipe is ~50 lines of glue) | slice printed for the new finding; stale report → exit 2 (`logs/s3_C2.log` C2b/C2c) |
| C3 | quality ratchet: promote baseline only on clean delta with no stale dispositions; history and rollback as audit | supported now | held on regression and on stale entries, advanced on clean, old baseline archived (`logs/s3_C1_C3.log` C3a/C3b) |
| C3' | doctor state reports (`state/reports/<run_id>/…json`, `latest.json` after rollback) as delta baselines | supported now | rolled-back `latest.json` vs regression scan → exit 1 (C3e) |
| C4 | pycache-clean before doctor | works, **no effect on doctor** | identical issue sets with and without `.pyc` (`logs/s4_C4.log`) |
| C5 | harness + doctor: one `run_test.py` run = project tests + doctor rescan + delta, as named checks | small integration step | clean PASS/0, regression FAIL/1, artifacts include doctor report (`logs/s4_C5.log`) |
| C6 | custom detector + severity map + delta | small integration step (private-API monkeypatch) | custom `print_calls` critical → doctor exit 2, delta flags it (`logs/s5_ext.log` X3/X5) |
| C7 | onboard's src-layout runner + `dependency_cycles` | **anti-composition** (they conflict) | `PYTHONPATH=src` turns intra-package absolute imports into `third_party`, so cycles = 0; scanning `src/` as root finds the cycle (`logs/s4_C7.log`) |
| C8 | agent orientation: doctor JSON as a project-wide definition index (no per-file structure calls) | supported now (C2b uses it) | `files[].functions[]` carry qualname, start and end lines, complexity (`logs/s1_doctor_json_shape.txt`) |
| R1 | delta that also compares `config_hash` and recomputes severities from one config | research idea | needed: D3 shows a latest-config severity remap launders a regression |
| R2 | real detector plug-in seam (entry points or config-listed visitor classes) | research idea | see `extensions.md` |
| R3 | structure for a whole tree, or a merged structure + doctor graph ("Graphify") | research idea | the fieldkit defers it explicitly (`SKILL.md:129`) |

## C1: doctor JSON → delta gate (supported now)

Recipe: `recipes/ci_delta_gate.sh <repo> <fieldkit> <runner…>`.
1. Runs from `.somnus-debug/` so the log stays there.
2. Rescans to `runs/latest.*` without `set -e`, because doctor exits 1 on pre-existing serious findings.
3. Treats doctor exit ≥ 4 as a hard failure (exit 3).
4. Exits with `delta.py`'s code.

```console
bash recipes/ci_delta_gate.sh /tmp/lane-f/proj "$FK" env PYTHONPATH=/tmp/lane-f/proj/src /tmp/lane-f/proj/.venv/bin/python -m somnus_debug.cli
```

Run log (`logs/s3_C1_C3.log`):

```text
### C1a clean tree        doctor exit=1  CLEAN  delta exit=0  recipe exit=0
### C1b regression (os.system)  doctor exit=1  REGRESSION  | serious | security_risks | src/calc/ops.py:47 | risky |  delta exit=1  recipe exit=1
### C1c broken config     doctor exit=4  "doctor failed to run"  recipe exit=3
### C1d clean again       doctor exit=1  delta exit=0  recipe exit=0
```

Caveats, all verified in `fieldkit.md` §3:
- Delta exit 2 also means an argparse usage error.
- A malformed report crashes delta with exit 1.
- A broad disposition, even a stale one, silently absorbs future regressions (L7).
- A latest scan run under a different config can downgrade a finding below the gate (D3). In CI, pin `-c .somnus-debug/python_doctor.yaml` and keep it under review.

## C2: structure → targeted reading (supported now)

Recipe: `recipes/structure_slice.py <python> <file.py> <name>…`. It runs `structure` (stdout only, writes nothing), parses `(lines A-B)`, and prints just those source spans. It exits 1 if a name is not in the index.

```text
### C2a structure_slice add parse nonexistent
not in index: ['nonexistent']
--- proj/src/calc/ops.py:7-13 (add)      … 7 lines …
--- proj/src/calc/ops.py:16-23 (parse)   … 8 lines …
exit=1
```

**C2b (doctor-native variant):** `recipes/findings_to_slices.py <latest.json> <delta.json> [--all]`.
1. Joins `delta --json` `new[]` to `latest.files[].functions/classes` by `(relative_path, qualname)`.
2. Prints the enclosing definition only.
3. First checks every scanned file's sha256 against `file_hash` and refuses (exit 2) if the tree moved since the scan. This guard was added after the first run hit an `IndexError` on a stale report.

```text
### C2b on a report whose file has changed since → STALE REPORT: files changed since the scan: ['src/calc/ops.py']. exit=2
### C2c fresh → ### serious security_risks src/calc/ops.py:47 risky: …  (lines 44-50 printed)  exit=0
```

Limitation: findings attributed to `<module>` (module-level code, or anything inside a private function) have no span. The recipe says so and points to the line instead.

## C3: ratchet + history/rollback (supported now)

Recipe: `recipes/ratchet_promote.sh <repo> <fieldkit>`. It runs `delta --json`. Only when exit = 0 **and** `stale_dispositions` is empty does it archive `runs/baseline.*` to `runs/archive/baseline-<run_id>.*` and copy `latest → baseline`.

```text
### C3a ratchet on regression         delta exit=1 stale_dispositions=0 → ratchet held: baseline unchanged (exit 1)
### C3b ratchet on clean delta        delta exit=0 stale_dispositions=0 → ratchet advanced: baseline <- 20261112T002258Z (old archived as 20261112T002200Z)
### C3c doctor history               5 runs listed with per-run report paths
### C3d rollback --run-id <onboarding run>   exit 0; state/reports/latest.json now has the old run_id
### C3e delta(rolled-back latest.json, regression scan)  REGRESSION, exit 1
### C3f rollback --run-id nope       "Run ID does not exist in state history." exit 4
### C3g next stateful scan           state_delta computed against the rolled-back run's file hashes
```

What history and rollback really give you:
- an append-only per-run archive of full reports (`state/reports/<run_id>/`) plus a movable `latest` alias.
- They do **not** restore code.
- Rollback silently re-bases the next scan's `state_delta`.
- `history` orders by the `completed_at` text column (see the sandbox caveat in `fieldkit.md`).

The ratchet is the stronger primitive. The doctor state is the audit trail behind it.

## C4: pycache-clean before doctor (works, no effect on doctor)

Doctor includes only `*.py` and ignores `__pycache__/*` and `*.pyc` by default, so bytecode never enters a scan.

```text
pyc files: 4 → scan exit=1 → pycache-clean --dry-run (logs "Removed directory…", deletes nothing; 4 remain)
→ pycache-clean live on /tmp copy (0 remain) → scan exit=1 → files_scanned 3 3 | identical issue sets: True
```

Use it before *harness* runs (stale bytecode can mask import errors at runtime), not before doctor. The dry-run wording ("Removed directory", "deleted 2 directories") is misleading in logs.

## C5: harness + doctor (small integration step)

Recipe: `recipes/harness_doctor_surface.py`. It splices a project surface into a scaffolded `run_test.py`, between `TEST_NAME =` and the `# Harness internals` banner. Required env: `SD_PYTHON`, `FIELDKIT`, `TEST_PYTHON`.

Steps:
1. `somnus-debug init-test-harness proj/single_test --no-contract`. Use a subdir, because of harness.md H-2.
2. `python3 recipes/harness_doctor_surface.py proj/single_test/run_test.py`
3. `cd proj && python3 single_test/run_test.py`

```text
C5a clean tree, no harness dispositions → FAIL (exit 1): the scaffolded run_test.py itself adds 9 serious findings
C5b after 4 narrow dispositions for single_test/run_test.py → PASS (exit 0) checks: project-tests-pass ✓ doctor-ran ✓ no-new-serious-findings ✓
C5c os.system regression → FAIL (exit 1) regressions: [('security_risks','risky')]; artifacts: doctor_latest.{md,json}, manifest.json, report.md, test.log
C5d SD_PYTHON unset → FAIL, 0 checks, KeyError traceback in test.log
```

Why it is "small step", not "supported now":
- The project must write `execute_test` (the template's is gp-cli specific).
- It must scaffold below the repo root.
- It must disposition the template's own findings.

## C6: custom detector (small integration step, unsupported API)

`recipes/ext_custom_detector.py` subclasses `CodeQualityVisitor` and rebinds `somnus_debug.doctor.core.CodeQualityVisitor`. Config `severity_levels: {print_calls: critical}` sets severity.

```text
X1 stock: [suspicious_short_functions] exit 0
X3 patched + crit.yaml: [suspicious_short_functions, print_calls(critical)] exit 2, score 78
X5 delta(stock, patched): REGRESSION | critical | print_calls | m.py:7 | shout | exit 1
```

## C7: src layout × dependency cycles (anti-composition, VERIFIED)

```text
import pkg.b  | root=repo, no PYTHONPATH                 | cycles=0 missing=2 (edges 'missing')
import pkg.b  | root=repo, PYTHONPATH=src (onboard runner)| cycles=0 missing=0 (edges 'third_party', no target)
import pkg.b  | root=src                                  | cycles=1 (edges local a.py<->b.py)
from pkg import b | root=src                              | cycles=0 (both edges resolve to pkg/__init__.py)
```

There are two compounding causes:
1. Modules are indexed by path from the scan root (`src.pkg.a`, `doctor/core.py:984-993`). Under `PYTHONPATH=src`, `find_spec('pkg')` succeeds, so intra-project imports are classified `third_party` (`:1003-1016`).
2. `_resolve_local` returns the exact package match first, so `from pkg import b` (and `from . import b`) target `pkg/__init__.py`, not `b.py` (`:1032-1048`).

Practical consequence: in an onboarded src-layout repo, `dependency_cycles` is effectively blind, while `missing_imports` noise is gone. Workaround (VERIFIED for the `import pkg.b` form): run a second doctor scan with `src/` as the project root to check cycles.

## How to rerun everything

```console
bash repro/s0_setup.sh            # /tmp/lane-f: 3 non-editable installs of the repo + fixture git project
bash repro/s1_selftest_onboard.sh # selftest 29/29, onboard happy path + edges
bash repro/s2_loop_delta.sh       # baseline/regress/disposition/fix loop, delta edge cases
bash repro/s3_compositions.sh     # C1, C3, C2
bash repro/s4_harness_more.sh     # harness, C5, C4, C7, self-check
bash repro/s5_extension_probes.sh # C6/extension probes, library surface, link check
bash repro/s6_doc_probes.sh       # doc-claim probes
```

The stages are sequential (each builds on `/tmp/lane-f/proj` state) and write logs to `logs/`. Nothing writes into the repo outside this lane directory. `git status` after all stages shows only `?? wiki/`.
