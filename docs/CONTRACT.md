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

Copy this directory into the repository.

Then edit only the project-specific surface in `run_test.py`:

```python
TEST_NAME = "..."

def execute_test(ctx: TestContext) -> TestOutcome:
    ...
```

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
