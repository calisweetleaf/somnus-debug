# Lane F: Extensions & Composition (index)

| File | Contents |
|---|---|
| `extensions.md` | Extension points in `src/somnus_debug/`. Verdict: none supported; monkeypatch probe; severity, gate and toggle customization. |
| `fieldkit.md` | `onboard.py` / `delta.py` / `selftest.py`: CLI, algorithm, exit codes, files written, JSON formats, verified runs, references-vs-code table |
| `harness.md` | `init-test-harness`, the scaffolded `run_test.py`, the manifest schema, CONTRACT.md reconciliation, agent recipe |
| `doc-reconciliation.md` | Claim-by-claim table for README, MANUAL, QUICKSTART, PUBLISHING, AGENTS_APPENDIX (+ CONTRACT cross-refs); dead links |
| `compositions.md` | C1–C8 and R1–R3, classified, with recipes and run excerpts |
| `recipes/` | `ci_delta_gate.sh`, `ratchet_promote.sh`, `structure_slice.py`, `findings_to_slices.py`, `harness_doctor_surface.py`, `ext_custom_detector.py` |
| `repro/` | `env.sh` and stages `s0`–`s6`, which rebuild `/tmp/lane-f` and rerun every experiment |
| `logs/` | Raw logs of the final full run (s0→s6), plus copies of the generated PROFILE.md and configs (`*.txt`) |

Note: `/tmp` was wiped once mid-investigation (container reset), so every experiment was re-executed from scratch through `repro/`. The logs here come from that clean rerun.
