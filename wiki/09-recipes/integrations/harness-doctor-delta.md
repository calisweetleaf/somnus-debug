# Recipe: one harness run = project tests + doctor rescan + delta gate

**Tier:** small integration step. **Script:** lane F's [harness_doctor_surface.py](../../_evidence/agent-findings/lane-f-ext/recipes/harness_doctor_surface.py). **Needs:** an onboarded repo ([onboard-a-repo](../intermediate/onboard-a-repo.md)).

Produce a single PASS/FAIL verdict, with artifacts, that requires the project's tests to pass, doctor to have actually scanned files, and no new serious findings against the baseline.

## When to use

This section says why combine them.

Doctor alone says nothing about tests (it never emits `test_gaps`, [D-05](../../DISCOVERY-LEDGER.md#d-05)); tests alone say nothing about stubs, silent failures or risky calls. This recipe makes both one named-check verdict an orchestrator can read from `manifest.json`. It is the composition the harness contract allows: "an orchestrator may discover and invoke its single-test surface" (`skills/somnus-debug-fieldkit/references/accelerate-integration.md`, integration pattern item 5).

## Steps

This section gives the scaffold, the splice, the dispositions, and the run.

```console
cd <repo>
.venv/bin/python -m somnus_debug.cli init-test-harness single_test --no-contract
python3 harness_doctor_surface.py single_test/run_test.py          # splice the 3-check execute_test()
export SD_PYTHON=<repo>/.venv/bin/python FIELDKIT=<fieldkit> TEST_PYTHON=<repo>/.venv/bin/python
python3 single_test/run_test.py                                    # first run FAILs on the template's own findings
# add narrow dispositions for single_test/run_test.py (below), then rerun
```

The spliced `execute_test()` runs three subprocesses and returns three checks (full source in the linked script):

| Check | Passes when |
|---|---|
| `project-tests-pass` | `TEST_PYTHON -m pytest -q tests` exits 0 |
| `doctor-ran` | doctor scan (from `.somnus-debug/`, `-c python_doctor.yaml`, reports into the artifact dir) exits below 4 and scanned more than 0 files |
| `no-new-serious-findings` | `delta.py baseline.json <artifact>/doctor_latest.json --dispositions dispositions.json --json` exits 0 |

## Executed result

This section shows the four outcomes.

Executed: yes (`/tmp/w4/proj_h2`, copy of the onboarded fixture; [stage 6 log](../_repro/logs/stage6_integrations.log), section N2)

```text
# 1. fresh harness, no harness dispositions
FAIL                                                                            [exit=1]
[('project-tests-pass', True), ('doctor-ran', True), ('no-new-serious-findings', False)]
[('broad_exceptions', '<module>'), ('broad_exceptions', 'main'), ('security_risks', '<module>'),
 ('security_risks', 'execute_test') x3, ('silent_failures', '<module>'),
 ('suspicious_short_classes', 'Check'), ('suspicious_short_classes', 'TestContext')]
# 2. after 6 narrow dispositions for single_test/run_test.py (7 entries in total)
PASS                                                                            [exit=0]
[('project-tests-pass', True), ('doctor-ran', True), ('no-new-serious-findings', True)] {'doctor_exit_raw': 1, 'production_score': 0, 'total_issues': 20}
['doctor_latest.json', 'doctor_latest.md', 'manifest.json', 'report.md', 'test.log']
# 3. purge() calling os.system added to src/inventory/store.py
FAIL                                                                            [exit=1]
[('security_risks', 'purge')]
# 4. SD_PYTHON unset
FAIL                                                                            [exit=1]
KeyError: 'SD_PYTHON'                                                           # in test.log; manifest still written
```

Note `doctor_exit_raw: 1` in the PASS run: doctor itself is red on the accepted findings, the delta gate is green [VERIFIED].

## The dispositions used

This section shows the entries, kept per symbol so they cannot absorb new findings elsewhere.

```json
{"category": "security_risks", "file": "single_test/run_test.py", "symbol": "execute_test", "reason": "Harness runs fixed argv lists (pytest, doctor, delta.py) with no shell."},
{"category": "security_risks", "file": "single_test/run_test.py", "symbol": "<module>", "reason": "Template _run_command (private, so attributed to <module>) runs argv lists with no shell."},
{"category": "broad_exceptions", "file": "single_test/run_test.py", "symbol": "*", "reason": "Template contract: any Exception in execute_test becomes a FAIL verdict with artifacts."},
{"category": "silent_failures", "file": "single_test/run_test.py", "symbol": "<module>", "reason": "Template _setup_logger handler cleanup; attributed to <module> because the function is private."},
{"category": "suspicious_short_classes", "file": "single_test/run_test.py", "symbol": "Check", "reason": "Frozen dataclass; doctor exempts only plain @dataclass."},
{"category": "suspicious_short_classes", "file": "single_test/run_test.py", "symbol": "TestContext", "reason": "Frozen dataclass; doctor exempts only plain @dataclass."}
```

Judgment call: the `security_risks` entry for `execute_test` covers all three subprocess calls in that function, and any future one. That is acceptable only because the harness function exists to run subprocesses; review it when the function changes. The frozen-dataclass entries exist because doctor's dataclass exemption tests `name.endswith("dataclass")` on the decorator text, which `dataclass(frozen=True)` fails (`src/somnus_debug/doctor/core.py:1192`; [D-07](../../DISCOVERY-LEDGER.md#d-07)) [VERIFIED by lane F, X9].

## Pitfalls

This section lists what makes this a small integration step rather than supported-now.

- You must write `execute_test()` (the template's is project-specific), scaffold below the repo root, and disposition the template's own findings ([D-15](../../DISCOVERY-LEDGER.md#d-15)).
- Findings in the template's private helpers (`_run_command`, `_setup_logger`) are attributed to `<module>`, so a `<module>` disposition also covers any future module-level code in that file.
- The doctor scan inside the harness is stateful; its run IDs share the per-second clock with any other scan ([D-08](../../DISCOVERY-LEDGER.md#d-08)).
- Missing env vars produce a FAIL with 0 checks and a `KeyError` in `test.log`, not a usage message.

## Sources

This section lists the files, logs and evidence this page rests on.

- [stage 6 log](../_repro/logs/stage6_integrations.log)
- [lane-f harness](../../_evidence/agent-findings/lane-f-ext/harness.md), [lane-f compositions C5](../../_evidence/agent-findings/lane-f-ext/compositions.md), [lane-f s4 C5 log](../../_evidence/agent-findings/lane-f-ext/logs/s4_C5.log)
- `src/somnus_debug/doctor/core.py:1192`, `src/somnus_debug/test_harness/templates/run_test.py:747-855`
