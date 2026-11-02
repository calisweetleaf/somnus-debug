# Install and runner choice

somnus-debug is on PyPI as `somnus-debug` (0.1.0, Python 3.10+, one runtime dependency: PyYAML).

```console
pip install somnus-debug
```

That's the whole install. The only decision is **which environment** it goes into. That choice changes doctor's results.

## Install into the project's environment

Doctor resolves third-party imports with `importlib.util.find_spec` in the interpreter that runs it. If somnus-debug lives in a different environment than the project, every project dependency shows up as a serious `missing_imports` finding. So, when the project has a virtualenv:

```console
<project>/.venv/bin/python -m pip install somnus-debug
<project>/.venv/bin/python -m somnus_debug.cli --version
```

Then run doctor through that interpreter: `<project>/.venv/bin/python -m somnus_debug.cli doctor ...`. `scripts/onboard.py` detects `.venv`, `venv`, `env`, or any directory containing `pyvenv.cfg`, checks whether it can `import somnus_debug`, and writes the matching runner into `PROFILE.md`. Installing into a project environment changes that environment, so follow the operator's install policy and ask first if it's not yours.

For a `src/` layout, the project's own packages resolve only if they're importable. Use `PYTHONPATH=src` (which onboard sets automatically), or install the project editable: `pip install -e .`.

## Standalone install

A global or user-level `pip install somnus-debug` (or any isolated-tool installer) gives a `somnus-debug` command on PATH. That's fine for `structure`, `pycache-clean`, `init-test-harness`, and doctor runs on code with no third-party imports. For doctor on a real project, expect `missing_imports` noise unless the project's dependencies are also importable from that interpreter.

## Entry points

| Command | Same as |
|---|---|
| `somnus-debug <cmd>` | `python -m somnus_debug.cli <cmd>` |
| `somnus-doctor` | `somnus-debug doctor` |
| `somnus-structure` | `somnus-debug structure` |
| `somnus-pycache-clean` | `somnus-debug pycache-clean` |

`python -m somnus_debug.cli` works even when the scripts directory isn't on PATH. It's the most reliable form inside a specific venv.

## Verify

```console
somnus-debug --version                                   # or <python> -m somnus_debug.cli --version
python3 <fieldkit>/scripts/selftest.py [--python <python>]
```

`selftest.py` runs 29 checks against throwaway fixtures: flags, defaults, exit codes, file side effects, and finding triggers. All must pass before you trust the references for that install. A failing check names the reference to update.

## Upgrade and source installs

- Upgrade: `pip install -U somnus-debug`, then rerun `selftest.py`.
- From a checkout (developing somnus-debug itself): `pip install -e /path/to/somnus-debug`.
- Never install silently into an environment you don't own. If the CLI is missing and policy is unclear, report it and stop at that boundary.
