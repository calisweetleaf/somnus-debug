# Tooling integration

This page explains how somnus-debug fits next to the tools a project already uses: CI runners, git, virtual environments, src layouts, pytest, the fieldkit agent loop, and in-process Python embedding. It records what integration the package ships (very little) and what has been verified to work.

## What ships and what does not

This section sets expectations before any wiring.

| Integration | Shipped? | Evidence |
|---|---|---|
| console scripts (`somnus-debug`, `somnus-doctor`, `somnus-structure`, `somnus-pycache-clean`) | yes | `pyproject.toml` `[project.scripts]`; [VERIFIED] W2-02 |
| GitHub Actions / CI workflow files | no (no `.github/` in the repo) | [SOURCE-CONFIRMED] repo file list |
| pre-commit hook definition (`.pre-commit-hooks.yaml`) | no | [SOURCE-CONFIRMED] repo file list |
| `pyproject.toml` `[tool.somnus-debug]` config section | no; doctor reads config only from `-c` | [SOURCE-CONFIRMED] `src/somnus_debug/doctor/core.py:796-814` |
| pytest plugin | no | [SOURCE-CONFIRMED] no entry points besides console scripts |
| regression gate (baseline vs latest) | yes, outside the wheel: `skills/somnus-debug-fieldkit/scripts/delta.py` | [VERIFIED] W2-14, W2-17 |
| onboarding (per-repo profile) | yes, outside the wheel: `skills/somnus-debug-fieldkit/scripts/onboard.py` | [VERIFIED] lane F [fieldkit.md](../_evidence/agent-findings/lane-f-ext/fieldkit.md) section 2 |

The fieldkit ships in the repo and the sdist omits it (lane D [install-vs-source.md](../_evidence/agent-findings/lane-d-cli-tests/install-vs-source.md) section 2). Using it means having a checkout or copy of `skills/somnus-debug-fieldkit/`.

## CI runners

This section gives the rules for running doctor in CI. A tested script is in [automation-examples](automation-examples.md).

1. **Always pass `-c`.** A committed `python_doctor.yaml` is not read otherwise. [VERIFIED] lane D D27. See [D-02](../DISCOVERY-LEDGER.md#d-02).
2. **Quote the gate.** `severity_exit_level: "none"` works, but unquoted `none` exits 4. [VERIFIED] W2-08. See [D-03](../DISCOVERY-LEDGER.md#d-03).
3. **Run from a scratch cwd** so `production_doctor.log` does not land in the checkout. [VERIFIED] W2-21: the project root was untouched and the log landed in the output directory.
4. **Use `--no-state`** for ephemeral runners. State is only useful when the directory persists between runs. Same-second runs also collide ([D-08](../DISCOVERY-LEDGER.md#d-08)).
5. **Send reports out of the tree** with `-o` and `--json-output`. Give both, because `-o x.json` alone is overwritten by the JSON ([D-25](../DISCOVERY-LEDGER.md#d-25)).
6. **Assert `files_scanned > 0`.** A zero-file scan passes every gate ([D-17](../DISCOVERY-LEDGER.md#d-17)).
7. **Gate on new findings rather than the raw exit** for legacy code. Doctor exits 1 on any pre-existing serious finding, while `delta.py` exits 1 only on new, undispositioned serious or critical ones. [VERIFIED] lane F C1 and L6 ([compositions.md](../_evidence/agent-findings/lane-f-ext/compositions.md)); W2-14 and W2-17.
8. **Pin the interpreter.** `missing_imports` depends on what the interpreter running doctor can import. [VERIFIED] lane D D05a/b. See [D-26](../DISCOVERY-LEDGER.md#d-26).

## Git

This section covers how the tools interact with a repository's working tree.

- Default report files (`production_doctor_report.{md,json}`) and `.python_doctor/` are written into the scanned root. This repo's own `.gitignore` lists `*_report.md`, `*_report.json`, `.python_doctor/`, and `*.log`. Copy those lines into the target project's ignore file, or redirect the outputs. [SOURCE-CONFIRMED] `.gitignore`.
- The fieldkit profile lives in `.somnus-debug/`. `onboard.py --apply` writes a `.somnus-debug/.gitignore` covering `state/`, `runs/`, and `*.log`. [VERIFIED] lane F fieldkit O2.
- Doctor never reads git. It does not know about `.gitignore`. Its own `ignore_patterns` (defaults: VCS dirs, caches, venvs, `node_modules`, `build`, `dist`) decide what is scanned. [SOURCE-CONFIRMED] `src/somnus_debug/doctor/core.py:458-459`, `:937-947`.
- `onboard.py` plan mode can refresh `.git/index` (a git stat refresh) despite "writes nothing". [VERIFIED] lane D O04.

## Virtual environments and src layouts

This section explains the two environment couplings that change results.

- **Which interpreter runs doctor matters.** Third-party imports are "resolved" only if `importlib.util.find_spec` finds them in doctor's own environment (`src/somnus_debug/doctor/core.py:1050-1055`). Install somnus-debug into the project's venv, or accept `missing_imports` for packages only that venv has.
- **src layout.** Without `PYTHONPATH=<repo>/src`, a test's `from calc.ops import add` is a serious `missing_imports` finding. With it, the import resolves. [VERIFIED] W2-14:

  ```text
  without: serious missing_imports tests/test_ops.py 3 Import could not be resolved: calc.ops.   (exit 1)
  with PYTHONPATH=src: files=3, issues=4, critical=0, serious=0                                (exit 0)
  ```

  The cost: under `PYTHONPATH=src`, the edge is classified `third_party`, not `local`. That means cycles through those imports are invisible. [VERIFIED] W2-14 (`tests/test_ops.py calc.ops third_party resolved`); lane F C7. See [D-22](../DISCOVERY-LEDGER.md#d-22).
- `onboard.py` picks a runner automatically, in this order: `--python`, then a project venv that can `import somnus_debug`, then `somnus-debug` on PATH. It adds `PYTHONPATH=<repo>/src` for src layouts. `--python` with a normal symlinked venv interpreter is rejected. [VERIFIED] lane F OB-1. See [D-20](../DISCOVERY-LEDGER.md#d-20).

## pytest and the single-test harness

This section covers the relationship to a project's test runner.

- Doctor does not run tests. `detect_test_gaps` is configured and validated but never emits anything ([D-05](../DISCOVERY-LEDGER.md#d-05)).
- `init-test-harness` gives a project one artifact-producing test entrypoint. A tested way to make it wrap pytest is the splice in [first-project](../03-getting-started/first-project.md#step-6-add-the-single-test-harness-optional). [VERIFIED] W2-19: PASS, exit 0.
- Once scaffolded inside the scanned tree, `run_test.py` is scanned too. W2-19 counted 9 new serious findings from the template itself (`broad_exceptions` 2, `security_risks` 2, `silent_failures` 1, `suspicious_short_classes` 2 on frozen dataclasses), plus 8 minor. [VERIFIED] W2-19; lane F H-3. Either disposition them narrowly or add the harness directory to `ignore_patterns`.

## Agents (fieldkit loop)

This section points agents at the integration path built for them.

The fieldkit's loop is: onboard once (profile plus baseline), scan to `runs/latest.json`, gate with `delta.py`, disposition reviewed findings, and ratchet the baseline when clean. Recipes live in `wiki/_evidence/agent-findings/lane-f-ext/recipes/` (`ci_delta_gate.sh`, `ratchet_promote.sh`, `findings_to_slices.py`, `structure_slice.py`). [VERIFIED] lane F C1-C3. Agent-oriented guidance is in [10-agent-usage/agent-workflows](../10-agent-usage/agent-workflows.md).

`templates/AGENTS_APPENDIX.md` must be pasted into a repo's `AGENTS.md` by hand. No script appends it. [SOURCE-CONFIRMED] lane F fieldkit section 4.

## In-process embedding

This section covers calling the tools from Python instead of a subprocess.

- `somnus_debug.cli.main([...])` returns the exit code as an int and restores `sys.argv`. [VERIFIED] W2-20.
- It is **not** side-effect free. Doctor's `main` replaces the host's root logging handlers with a `FileHandler` on `production_doctor.log` in cwd. [VERIFIED] W2-20:

  ```text
  root handlers before: ['StreamHandler'] after: ['FileHandler']
  ```

  See [D-11](../DISCOVERY-LEDGER.md#d-11).
- The clean path is the library: `ProjectScanner(Path(root), ConfigManager(None)).scan({})` returns a result object without touching logging or disk. [VERIFIED] W2-20 (`library scan: 2 1`). See [D-12](../DISCOVERY-LEDGER.md#d-12). Library details: [04-library-api/overview](../04-library-api/overview.md).
- The dispatcher swaps the process-global `sys.argv`. Do not call `cli.main` from several threads at once. [HYPOTHESIS] (see [execution-model](../01-system/execution-model.md)).

## Sources

This section lists the code and evidence this page draws on.

- `pyproject.toml`; `.gitignore`
- `src/somnus_debug/cli.py:85-104`
- `src/somnus_debug/doctor/core.py:458-459`, `:796-814`, `:937-947`, `:1050-1055`, `:2179-2186`
- [lane F fieldkit.md](../_evidence/agent-findings/lane-f-ext/fieldkit.md), [compositions.md](../_evidence/agent-findings/lane-f-ext/compositions.md), [harness.md](../_evidence/agent-findings/lane-f-ext/harness.md), [recipes/](../_evidence/agent-findings/lane-f-ext/recipes/ci_delta_gate.sh)
- [lane D experiment-log.md](../_evidence/agent-findings/lane-d-cli-tests/experiment-log.md), [install-vs-source.md](../_evidence/agent-findings/lane-d-cli-tests/install-vs-source.md)
- W2 runs: [verification-results](../11-verification/verification-results.md#w2-runs)
