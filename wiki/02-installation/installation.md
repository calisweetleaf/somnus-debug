# Installation

This page gives each supported way to get somnus-debug 0.1.0 onto a machine: PyPI, a local checkout, running from source without installing, and per-project venvs. It says which ones were executed in this wave and what each leaves behind.

## Option A: from PyPI

This section installs the published release.

```bash
python3 -m venv .venv && . .venv/bin/activate
pip install somnus-debug==0.1.0
somnus-debug --version          # 0.1.0
```

Executed: not as an install in this wave. Lane D downloaded the PyPI 0.1.0 wheel and sdist (`pip download somnus-debug==0.1.0 --no-deps`, exit 0) and ran them via `PYTHONPATH`. The SHA-256 hashes are:

- wheel: `1e6913e1...4139`
- sdist: `4dd3fd5a...15d4`

[VERIFIED] lane D [install-vs-source.md](../_evidence/agent-findings/lane-d-cli-tests/install-vs-source.md) section 2.

The PyPI code is identical to this tree's `src/` once the `# somnus:metadata:v2` headers are stripped. The only real difference is `doctor/default_config.yaml`, which still has the old Somnus-MCP globs on PyPI. That file is read by no code, so it has no runtime effect. [VERIFIED] lane D section 3. See [D-23](../DISCOVERY-LEDGER.md#d-23).

## Option B: from a checkout (non-editable)

This section installs from this repository, which is how every W2 run was set up.

Executed: yes (`/tmp/w2`, exit 0; W2-02). The same was repeated for Python 3.10 and 3.11 venvs (W2-06).

```bash
python3 -m venv /tmp/w2/venv
/tmp/w2/venv/bin/pip install /path/to/somnus-debug          # add pytest for the test suite
ls /tmp/w2/venv/bin | grep somnus
```

```text
somnus-debug
somnus-doctor
somnus-pycache-clean
somnus-structure
```

PyYAML is pulled in automatically (6.0.3 in this run). The non-editable install left no build artifacts in the repo: `git status` still showed only `?? wiki/`. [VERIFIED] W2-02.

## Option C: editable install

This section covers the developer install the README recommends.

```bash
pip install -e .            # or: pip install -e ".[dev]" for pytest
```

Executed: no. It was not run, to keep the repo read-only. `docs/MANUAL.md` section 7.3 notes that it needs network access to fetch `hatchling`, or `--no-build-isolation` with hatchling already present. [DOCUMENTED-ONLY]

## Option D: run from source without installing

This section is for one-off use and for agents that must not install anything.

Executed: yes (W2-01, W2-05; lane B ran all its experiments this way).

```bash
PYTHONPATH=/path/to/somnus-debug/src python3 -m somnus_debug.cli doctor scan /some/project --no-state
PYTHONPATH=/path/to/somnus-debug/src python3 -m somnus_debug.doctor.core scan /some/project   # no PyYAML needed
```

Costs of this form:

- The interpreter must have PyYAML for the `.cli` form.
- Expect the pycache `SyntaxWarning` on stderr if bytecode is not cached.
- Add `PYTHONDONTWRITEBYTECODE=1`, or `__pycache__/` directories appear inside `src/`. The repo's `.gitignore` covers them, but they still alter the tree.

## Option E: inside the project's own venv

This section explains why the install location changes results.

Doctor marks a third-party import "resolved" only if its **own** interpreter can find the module (`importlib.util.find_spec`). Installing somnus-debug into the project's venv therefore gives the fewest false `missing_imports`. [VERIFIED] lane D D05a/D05b. See [D-26](../DISCOVERY-LEDGER.md#d-26).

The fieldkit's `onboard.py` looks for project venvs (`.venv`, `venv`, `env`, then any directory holding `pyvenv.cfg`) that can `import somnus_debug`, before falling back to PATH. [VERIFIED] lane F [fieldkit.md](../_evidence/agent-findings/lane-f-ext/fieldkit.md) section 2.

## What is installed, and what is not

This section lists the installed payload so you know which repo files you still need from a checkout.

The installed `RECORD` (W2-02) lists:

- 4 console scripts
- 12 `.py` modules under `somnus_debug/` (including the template `run_test.py`)
- `doctor/default_config.yaml`
- `test_harness/templates/CONTRACT.md`
- the `dist-info` files

There is no `somnus-init-test-harness` script. Not in the wheel, and only available from a checkout:

- `skills/somnus-debug-fieldkit/` (selftest, onboard, delta)
- `tests/`
- `docs/`
- the root duplicate scripts

The sdist adds `docs/` and `README.md`. [VERIFIED] lane D section 2. The full layout is in [package-layout](package-layout.md).

## Uninstall and cleanup

This section lists what removal does and does not cover.

`pip uninstall somnus-debug` removes the package and scripts. It does **not** remove:

- `production_doctor.log` files left in whatever directories you ran doctor from
- `production_doctor_report.*` and `.python_doctor/` in scanned projects
- `self_check_report.*` and `.python_doctor/` that `self-check` wrote into the package directory. pip does not know about these files, so they can be left behind in site-packages. [HYPOTHESIS] based on lane D D14 and pip's RECORD-based uninstall; not executed.
- `test-runs/` from the harness

[VERIFIED] (the artifacts themselves) W2-10, W2-11, W2-19.

## Sources

This section lists the code and evidence this page draws on.

- `pyproject.toml`; installed `somnus_debug-0.1.0.dist-info/RECORD`, `METADATA`
- `README.md:179-193`; `docs/MANUAL.md` sections 1, 7.3
- `src/somnus_debug/doctor/core.py:1050-1055`
- [lane D install-vs-source.md](../_evidence/agent-findings/lane-d-cli-tests/install-vs-source.md), [experiment-log.md](../_evidence/agent-findings/lane-d-cli-tests/experiment-log.md)
- [lane F fieldkit.md](../_evidence/agent-findings/lane-f-ext/fieldkit.md)
- W2 runs: [verification-results](../11-verification/verification-results.md#w2-runs)
