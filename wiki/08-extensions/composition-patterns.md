# Composition patterns

somnus-debug's tools do more together than apart. Doctor produces a JSON report; the fieldkit's `delta.py` turns two reports into a regression verdict; `structure` and the report's own definition spans turn findings into the few lines worth reading. This page names each composition, classifies it, and links its executed recipe.

## Classification

This section defines the labels used below; they match the rest of the chapter.

- **Supported now:** shipped tools plus shell or short stdlib glue; no private imports; executed.
- **Small integration step:** works, but needs user-written code, a workaround for a known defect, or a non-exported import; executed.
- **Anti-composition:** two supported things that interfere.
- **Research idea:** not built.

## Pattern table

This section is the map; each row links the recipe that ran it in this wave.

| ID | Pattern | Class | Result in this wave | Recipe |
|---|---|---|---|---|
| C1 | doctor JSON → `delta.py` regression gate | Supported now | regression: exit 1; broken config: exit 3; clean: exit 0 | [ci-delta-gate](../09-recipes/automation/ci-delta-gate.md) |
| C1b | C1 as an opt-in git pre-commit hook | Supported now (hand-installed) | commit with `shell=True` call blocked (exit 1); clean commit passed | [pre-commit-gate](../09-recipes/automation/pre-commit-gate.md) |
| C2 | `structure` index → print only named definitions | Supported now | `parse_qty` lines 17-24 printed; missing name → exit 1 | [findings-to-source-slices](../09-recipes/advanced/findings-to-source-slices.md) |
| C2b | `delta --json` new findings → doctor JSON `files[].functions` spans → source slices, with a stale-report guard | Supported now | slice printed for `export_report`; tree changed after scan → exit 2 | [findings-to-source-slices](../09-recipes/advanced/findings-to-source-slices.md) |
| C3 | Quality ratchet: promote latest to baseline only on clean delta with no stale dispositions | Supported now | advanced on clean (old baseline archived); held on regression (exit 1) | [quality-ratchet](../09-recipes/advanced/quality-ratchet.md) |
| C3' | Doctor state reports (`state/reports/<run_id>/…json`, `latest.json`) as delta inputs; history and rollback as audit trail | Supported now | rollback moved `latest` alias; bad run ID exit 4 | [history-and-rollback](../09-recipes/automation/history-and-rollback.md) |
| C4 | `pycache-clean` before doctor | Works, no effect on doctor | identical issue sets with and without `.pyc` (lane F) | [pycache-dry-run](../09-recipes/beginner/pycache-dry-run.md) |
| C5 | Scaffolded harness running project tests + doctor rescan + delta as three named checks | Small integration step | FAIL on template findings; PASS after 6 narrow dispositions; FAIL on `os.system` regression | [harness-doctor-delta](../09-recipes/integrations/harness-doctor-delta.md) |
| C5b | Scaffolded harness running only the project's pytest suite | Small integration step | PASS exit 0; broken test FAIL exit 1 | [harness-pytest](../09-recipes/integrations/harness-pytest.md) |
| C6 | Custom detector (private subclass) + severity map + delta | Small integration step, unsupported API | custom `print_calls` critical → doctor exit 2, delta exit 1 | [custom-detector-probe](../09-recipes/advanced/custom-detector-probe.md) |
| C7 | Onboard's `PYTHONPATH=src` runner × `dependency_cycles` | Anti-composition | cycles 0 under the runner; 1 when `src/` is the scan root | [src-layout-cycle-check](../09-recipes/advanced/src-layout-cycle-check.md) |
| C8 | Doctor JSON as a project-wide definition index | Supported now | `files[].functions[]` carry qualname and line span; used by C2b | [embedded-scan](../09-recipes/programmatic/embedded-scan.md) |
| C9 | `ProjectScanner` in-process with no disk or logging side effects | Small integration step (non-exported class) | 4 files scanned, no new paths, root handlers `[]` | [embedded-scan](../09-recipes/programmatic/embedded-scan.md) |
| C10 | `build_index` on metadata-stamped files after blanking the header | Small integration step (works around [D-01](../DISCOVERY-LEDGER.md#d-01)) | `scaffold` indexed at lines 62-88, matching the file | [index-stamped-file](../09-recipes/programmatic/index-stamped-file.md) |
| R1 | Config-aware delta (compare `config_hash`, recompute severity) | Research idea | needed: a latest-config remap launders a regression (lane F, D3) | [experimental-extensions](experimental-extensions.md) |
| R2 | Real detector plug-in seam | Research idea | see [plugin-integration](plugin-integration.md) | [experimental-extensions](experimental-extensions.md) |
| R3 | Whole-tree structure graph merged with doctor's import graph | Research idea | the fieldkit defers it (`skills/somnus-debug-fieldkit/SKILL.md:129`) | [experimental-extensions](experimental-extensions.md) |

C1-C8 were first established by lane F [VERIFIED, [lane-f compositions](../_evidence/agent-findings/lane-f-ext/compositions.md)] and re-executed here against a different fixture (an `inventory` src-layout package) [VERIFIED, [repro logs](../09-recipes/_repro/README.md)]. C5b, C9 and C10 are new in this wave.

## The core loop: why C1 gates on delta, not on doctor

This section explains the one composition every other pattern builds on.

Doctor's exit code reflects all findings above the gate, old and new. On any real codebase it is 1 from the first scan, so it cannot tell you whether a change made things worse. `delta.py` compares two reports by finding identity `(category, file, symbol, message)` with no line number, so moved code is "persisting", and returns 1 only for new serious or critical findings not covered by a disposition (`skills/somnus-debug-fieldkit/scripts/delta.py:82-85`, `:159-191`) [SOURCE-CONFIRMED].

In this wave's loop the same tree gave doctor exit 1 and delta exit 0 [VERIFIED, [stage 2 log](../09-recipes/_repro/logs/stage2_intermediate.log)]:

```text
Scan complete: files=3, issues=2, critical=0, serious=1      [exit=1]   doctor
**CLEAN: no new serious/critical findings, coverage intact.**  [exit=0]   delta
New (open): 1 · Resolved: 0 · Persisting: 0 · Dispositioned: 1
```

That is by design, and it is why the fieldkit's automation reference says to "gate on `delta.py`'s exit code rather than the raw doctor exit" (`skills/somnus-debug-fieldkit/references/automation.md:65`) [DOCUMENTED + VERIFIED].

## Rules for composing safely

This section lists the constraints every composition above had to respect.

1. **Run doctor from a directory you own.** Every call writes `production_doctor.log` to the cwd ([D-10](../DISCOVERY-LEDGER.md#d-10)). The fieldkit runs from `.somnus-debug/`.
2. **Always pass `-o` and `--json-output`, and never point `-o` at a `.json` path** ([D-25](../DISCOVERY-LEDGER.md#d-25)).
3. **Pin one config for both sides of a delta** ([D-21](../DISCOVERY-LEDGER.md#d-21)).
4. **Separate stateful scans by at least a second.** Run IDs are per-second and history uses `INSERT OR REPLACE` ([D-08](../DISCOVERY-LEDGER.md#d-08)). In this wave two loop scans one second apart both got `20261112T004522Z`, so history kept only the second [VERIFIED, [stage 2 log](../09-recipes/_repro/logs/stage2_intermediate.log)]. The `runs/*.json` copies the fieldkit writes are unaffected.
5. **Check `files_scanned` before trusting any count.** Zero files exits 0 ([D-17](../DISCOVERY-LEDGER.md#d-17)); `delta.py` turns it into exit 2.
6. **Treat a doctor exit of 4 or 5 as "did not run".** The CI recipe maps it to exit 3 so it cannot be confused with a regression.
7. **Run the project's own tests too.** Doctor never emits `test_gaps` ([D-05](../DISCOVERY-LEDGER.md#d-05)); C5 is the pattern that puts both in one verdict.

## Sources

This section lists the files, logs and evidence this page rests on.

- [lane-f compositions](../_evidence/agent-findings/lane-f-ext/compositions.md), [lane-f fieldkit](../_evidence/agent-findings/lane-f-ext/fieldkit.md), [lane-f harness](../_evidence/agent-findings/lane-f-ext/harness.md)
- `skills/somnus-debug-fieldkit/scripts/delta.py:82-85`, `:159-191`; `skills/somnus-debug-fieldkit/references/automation.md:65`; `skills/somnus-debug-fieldkit/SKILL.md:129`
- Wave 5 runs: [repro driver and logs](../09-recipes/_repro/README.md)
