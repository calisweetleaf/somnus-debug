---
somnus:
  schema: "somnus://metadata/core/2.0.0"
  id: "urn:somnus:artifact:01a19ace-7969-70cc-8ba1-2473ba427f55"
  revision: 1
  title: "Agnostic Single-Test Surface"
  classification:
    category: "engineering"
    type: "report"
    role: "informative"
    scope: "component"
    tags: []
  lifecycle:
    status: "draft"
  authority:
    standing: "candidate"
    scopes:
      - target_ref: "urn:somnus:artifact:01a19ace-7969-70cc-8ba1-2473ba427f55"
        aspects: ["content"]
  time: {}
  names:
    slug: "agnostic-single-test-surface"
  knowledge:
    coverage: "artifact"
    subjects: ["urn:somnus:artifact:01a19ace-7969-70cc-8ba1-2473ba427f55"]
  access:
    visibility: "internal"
    allowed_uses: ["archive", "search", "reason"]
  ingestion:
    disposition: "candidate"
    body_role: "narrative"
---
# Agnostic Single-Test Surface

This directory is a portable **testing substrate**, not a repository doctrine,
agent workflow, release policy, CI system, or Accelerate installation.

Its job is deliberately narrow:

```text
one project-owned Python test
        |
        v
real package/system boundary
        |
        v
explicit project-owned acceptance
        |
        +--> manifest.json  machine-readable truth
        +--> report.md      human/model-readable report
        +--> test.log       raw execution truth
        |
        v
PASS / FAIL
```

## What is stable

The stable cross-project contract is:

1. There is one primary Python test entrypoint for the active validation.
2. The test exercises the real boundary the project means to prove.
3. The project defines its own acceptance conditions.
4. Every run receives a unique run ID and its own artifact directory.
5. Every run leaves three complementary artifacts:
   - `manifest.json`
   - `report.md`
   - `test.log`
6. The run ends in one unambiguous `PASS` or `FAIL`.
7. An exception is a failed run and still produces artifacts when possible.

## What is intentionally NOT stable

This surface does **not** decide:

- which package behavior matters;
- whether the run is unit, integration, live, replay, regression, benchmark,
  parity, compatibility, or publication validation;
- whether pytest is used;
- whether Ruff, lint, type checking, coverage, hashes, snapshots, benchmarks,
  live APIs, fixtures, or external systems are involved;
- what thresholds constitute success;
- which repository documents are authoritative;
- whether a repository is ready to publish;
- how work packets, continuity, hooks, skills, or agent state are managed.

Those belong to the project or to an orchestration method above this layer.

## Artifact semantics

### `manifest.json`

Machine-readable result.

It owns the structured run identity, verdict, acceptance checks, measurements,
evidence, environment, failure object, and artifact references.

Metrics are not automatically acceptance criteria. A number only becomes a
gate when the project-specific test explicitly makes it one.

### `test.log`

Raw execution history.

This is the diagnostic surface: detailed events, timings, package output,
warnings, exceptions, and anything else the test chooses to log.

The log is evidence. It is not itself the final verdict.

### `report.md`

Human/model-readable interpretation.

`run_test.py` writes a conservative factual report so the artifact always
exists. The executing model/operator may extend the report after consuming the
manifest and log.

A report may explain the machine result. It must not silently turn FAIL into
PASS, omit a failed acceptance check, or invent evidence that was not consumed.

## Installing into a repository

Copy `run_test.py` (and this file) into the repository, at its root or in any
subdirectory. `somnus-debug init-test-harness [DIR]` does the copy and refuses
to overwrite an existing, hand-edited copy without `--force`.

### Project root and artifact location

`run_test.py` resolves the project root as:

1. `$PROJECT_ROOT`, when set;
2. otherwise the nearest directory, starting at the directory holding
   `run_test.py` and walking up, that contains `.git`, `pyproject.toml` or
   `setup.cfg`;
3. otherwise the directory holding `run_test.py`.

Each run writes its artifacts to `<artifact root>/<run_id>/`, where the
artifact root is `$SINGLE_TEST_OUTPUT_DIR` (a relative value resolves against
the project root, not the working directory) or `<project root>/test-runs/`.

`python run_test.py --help` prints these settings and exits 0 without running
the test. The runner takes no other arguments.

### The project-specific surface

Then edit only the project-specific surface in `run_test.py`:

```python
TEST_NAME = "..."

def execute_test(ctx: TestContext) -> TestOutcome:
    ...
```

The shipped surface is a generic, runnable starting point named
`PROJECT TEST SUITE`: when the project has a pytest suite (a `tests/`
directory, `pytest.ini`, `conftest.py`, or pytest configuration in
`pyproject.toml`, `setup.cfg` or `tox.ini`) it runs `python -m pytest -q` in
the project root; otherwise it runs `python -m compileall -q` over the project
(virtualenvs, VCS and tool directories excluded, bytecode redirected to a
temporary directory). Either way it returns one named `Check` on the exit
code. Replace it with the one test that proves the project's real boundary.

`_run_command(argv, cwd=..., logger=..., expected=0, env=None)` runs a
subprocess, logs the command and its output to `test.log`, and raises on an
unexpected exit code; pass `expected=None` to receive the result and record it
as a `Check` yourself.

The test may import and exercise anything the package actually requires.

Do not bolt unrelated validation onto the run merely because a tool exists.
If a linter, test suite, benchmark, external service, replay fixture, or other
check is part of the package's real acceptance condition, invoke it
deliberately and record its result as a named `Check`.

## Relationship to Accelerate

None is required.

Accelerate, Somnus-C, a repository skill, hooks, CI, or another orchestration
system may discover and invoke this test surface. They do not define its
meaning merely by invoking it.

This directory can be archived, copied, or used independently.
