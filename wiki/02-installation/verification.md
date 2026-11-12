# Verifying an installation

This page gives an ordered check that an install of somnus-debug 0.1.0 works and behaves as this wiki describes. Each step names the expected result and what a deviation means. Every step was executed in this wave. The project-wide test results live in [11-verification/verification-results](../11-verification/verification-results.md).

## Step 1: scripts and version

This section confirms the entry points exist.

Executed: yes (W2-02, all exit 0).

```bash
somnus-debug --version            # 0.1.0
somnus-doctor --help | head -1    # usage: somnus-doctor [-h] {scan,init-config,history,rollback,self-check} ...
somnus-structure --help | head -1
somnus-pycache-clean --help | head -1
```

If `somnus-debug` works but `somnus-doctor` is missing, you are on a non-pip install (for example `PYTHONPATH`-only). There is no `somnus-init-test-harness`; that is expected. [VERIFIED] W2-02.

## Step 2: PyYAML is importable

This section rules out the dispatcher's hidden hard dependency.

```bash
somnus-debug doctor --help >/dev/null && echo ok
```

Executed: yes. It exits 0 when PyYAML is present (W2-01). It exits 1 with `ModuleNotFoundError: No module named 'yaml'` when PyYAML is absent (W2-05, Python 3.13). If it fails, install `pyyaml`, or use `somnus-doctor`, which does not need it. See [D-13](../DISCOVERY-LEDGER.md#d-13).

## Step 3: a fixture scan in /tmp

This section proves doctor runs end to end without touching a real project.

Executed: yes (W2-10, exit 1).

Build the three-file fixture from [quickstart step 2](../03-getting-started/quickstart.md#2-make-a-tiny-project), then:

```bash
cd /tmp/fixture/myproj && somnus-debug doctor scan . --no-state; echo "exit=$?"
```

Expected:

```text
Scan complete: files=3, issues=7, critical=0, serious=2
...
exit=1
```

The same 7 findings, with identical `(category, file, line, symbol)` tuples, were produced on Python 3.10.22, 3.11.17, and 3.12.15 (W2-06). A different count on the same fixture points at a different version or modified source.

## Step 4: the fieldkit contract test (needs a checkout)

This section runs the repo's 29-check behavioral contract against the installed CLI.

Executed: yes (cwd `/tmp/w2/fk-run`, a copy of `skills/somnus-debug-fieldkit`; W2-04, W2-06).

```bash
env PATH=/path/to/venv/bin:/usr/bin:/bin python3 skills/somnus-debug-fieldkit/scripts/selftest.py
```

Expected last line: `29/29 passed.`, exit 0. Observed on 3.10, 3.11, and 3.12 venvs. The 3.11 run was killed once by the sandbox (exit 137) and passed 29/29 on rerun.

Limits of this check:

- With `--python <interp>` it requires an interpreter that has the package **installed**. `PYTHONPATH=src` plus `--python /usr/local/bin/python3` gave **28/29**: the src-layout check overwrites `PYTHONPATH` (W2-04).
- It does not test `structure` on metadata-stamped files, so it passes while the D-01 crash is present. See step 5.

## Step 5: check for the structure stamped-file crash

This section detects the one known defect that the shipped tests catch and selftest does not.

Executed: yes (W2-15, W2-06).

```bash
head -32 /path/to/somnus-debug/src/somnus_debug/cli.py > /tmp/stamped.py
printf 'def f() -> int:\n    """Doc."""\n    return 2\n' >> /tmp/stamped.py
somnus-debug structure /tmp/stamped.py; echo "exit=$?"
```

On 0.1.0, both from this tree and from PyPI, the result is `error: invalid syntax (stamped.py, line 9)` and `exit=2`. A future build that has the fix will print an index and exit 0. See [D-01](../DISCOVERY-LEDGER.md#d-01). Executed: yes, exactly as shown, in `/tmp/w2` (W2-26: `error: invalid syntax (stamped.py, line 9)`, exit 2). W2-15 gave the same result with the quickstart `app/core.py` as the body.

## Step 6: the repo test suite (needs a checkout)

This section runs the shipped pytest suite **on a copy** of the repo, because the suite writes into the tree it runs in.

Executed: yes (W2-03, W2-06).

```bash
mkdir /tmp/repo-copy && (cd /path/to/somnus-debug && tar --exclude=./wiki --exclude=./.git -cf - .) | tar -xf - -C /tmp/repo-copy
cd /tmp/repo-copy && PYTHONDONTWRITEBYTECODE=1 /path/to/venv/bin/python -m pytest -q -p no:cacheprovider tests/
```

Expected on 0.1.0: `2 failed, 10 passed`, exit 1. The two failures are `test_structure_tolerates_type_like_comments` and `test_structure_self_index`, both caused by D-01. The suite tests the **copy's `src/`** through `PYTHONPATH`, not the installed package. It also leaves `production_doctor.log` at the copy's root. [VERIFIED] W2-03. Details: [11-verification/test-architecture](../11-verification/test-architecture.md).

## Sources

This section lists the code and evidence this page draws on.

- `pyproject.toml` `[project.scripts]`; `src/somnus_debug/cli.py:55-58`; `src/somnus_debug/structure/core.py:210`
- `tests/test_cli_smoke.py:49-61`, `:138-165`
- `skills/somnus-debug-fieldkit/scripts/selftest.py`
- [lane D test-coverage.md](../_evidence/agent-findings/lane-d-cli-tests/test-coverage.md), [install-vs-source.md](../_evidence/agent-findings/lane-d-cli-tests/install-vs-source.md)
- W2 runs: [verification-results](../11-verification/verification-results.md#w2-runs)
