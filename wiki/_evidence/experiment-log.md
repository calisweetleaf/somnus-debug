# Experiment Log

This page is the index of every experiment set run during the investigation, with environment and location of the raw record.

## Environment

This section fixes the conditions all experiments shared.

- Sandbox Linux, Python 3.12.15, PyYAML 6.0.2; experiments ran with cwd under `/tmp/<lane>/`, sources via `PYTHONPATH=<repo>/src` or a /tmp venv with a non-editable `pip install <repo>`; one `--no-deps` venv for the PyYAML-absent case.
- Fixtures were synthetic projects created in /tmp (deliberate bare/silent excepts, stubs, duplicate defs, property setters, abstract/Protocol/overload, src-layout cycles, unresolved imports, a syntax-error file, a metadata-stamped file). Copies of lane A's fixture are kept as `.txt` under `agent-findings/lane-a-arch-api/fixture/` so a doctor scan of the repo does not ingest the broken file.
- `/tmp` was reset by the container once during lanes D and F; lane F rebuilt everything as rerunnable stages and all its logs come from one clean full rerun.

## Experiment sets

This section lists the sets, their size, and their outcome.

| Set | Lane | Runs | Outcome summary | Raw record |
|---|---|---|---|---|
| Doctor CLI exit-code matrix | A | ~20 | codes 0/1/2/4/5 mapped; D-08, D-09, D-28 | [api-reference.md](agent-findings/lane-a-arch-api/api-reference.md) |
| Library examples ex1-ex7 | A | 7 | 6 exit 0; scaffolded run_test FAIL as expected | [examples/](agent-findings/lane-a-arch-api/examples/) |
| Config precedence matrix | B | 26 | D-02, D-03, D-16, D-17 | [configuration-findings.md](agent-findings/lane-b-config/configuration-findings.md) |
| YAML parser vs PyYAML | B | 48 inputs | D-04 | [yaml_probe.out](agent-findings/lane-b-config/experiments/yaml_probe.out) |
| pycache config probes | B | ~10 | D-14 (constructor only for scalar roots) | [configuration-findings.md](agent-findings/lane-b-config/configuration-findings.md) |
| Help capture + command sweep | D | all surfaces | verbatim help; exit table | [experiment-log.md](agent-findings/lane-d-cli-tests/experiment-log.md) |
| Smoke suite on /tmp copy | D | 12 tests | 10 passed, 2 failed (D-01) | [test-coverage.md](agent-findings/lane-d-cli-tests/test-coverage.md) |
| PyPI 0.1.0 diff | D | 1 | code identical; default_config differs (D-23) | [install-vs-source.md](agent-findings/lane-d-cli-tests/install-vs-source.md) |
| Fieldkit selftest | D, F | 2 | 29/29 both | [s1_selftest.md](agent-findings/lane-f-ext/logs/s1_selftest.md) |
| onboard edge cases | F | 8 | D-20 | [s1_onboard_edges.log](agent-findings/lane-f-ext/logs/s1_onboard_edges.log) |
| delta loop + edges | F | 14 | D-21 | [s2_loop.log](agent-findings/lane-f-ext/logs/s2_loop.log), [s2_delta_edges.log](agent-findings/lane-f-ext/logs/s2_delta_edges.log) |
| Compositions C1-C5 | F | 5 | D-27 | [compositions.md](agent-findings/lane-f-ext/compositions.md) |
| Harness | A, B, D, F | ~8 | D-15 | [harness.md](agent-findings/lane-f-ext/harness.md) |
| Custom detector | F | 1 | works via private subclass (D-19) | [s5_ext.log](agent-findings/lane-f-ext/logs/s5_ext.log) |

## Not executed on purpose

This section lists experiments withheld for safety.

- A live `pycache-clean` run with a scalar `roots:` value (could sweep from `/`).
- Any tool run against the real repo tree with write effects (pycache-clean, init-test-harness, doctor with state).
- Network actions beyond `pip install` into /tmp venvs and `pip download` of PyPI 0.1.0.
