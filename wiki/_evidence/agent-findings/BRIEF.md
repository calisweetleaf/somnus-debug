# Lane brief: Somnus Debug capability archaeology

REPO (read-only except wiki/_evidence/agent-findings/<your-lane>/):
/workspace/projects/69c23182-5d69-4d5c-ae10-5cdad587b9d3/forge/somnus-debug
Git baseline commit 034f46e = the uploaded zip (somnus-debug.zip, 2026-11-11). Package somnus-debug 0.1.0 (pyproject), Python 3.12.15 sandbox, PyYAML 6.0.2 present system-wide, pytest NOT installed system-wide.

## Hard rules
- Never modify anything in the repo outside your own findings dir. No cleanup, no deletes, no refactors, no fixes.
- Experiments run in /tmp/<lane>/ only: copy fixtures there, run tools with cwd inside /tmp so log files (production_doctor.log, reports, .python_doctor/ state) land there, not in the repo. Doctor writes production_doctor.log to CWD on every call, even --help.
- Run the source via `PYTHONPATH=<repo>/src python3 -m somnus_debug.cli ...` or `python3 -c "import somnus_debug..."`. An isolated venv in /tmp (python3 -m venv) with `pip install pytest` and `pip install <repo>` (non-editable) is allowed; never install into the system interpreter. `pip download somnus-debug==0.1.0 --no-deps -d /tmp/<lane>/pypi` to compare against PyPI is allowed.
- Never run pycache-clean against the repo or any real tree except a /tmp copy.
- Evidence classes: VERIFIED (you executed it; record command, cwd, exit code, key output), SOURCE-CONFIRMED (file:line), DOCUMENTED-ONLY, CONDITIONAL, DISCREPANCY, UNVERIFIED, HYPOTHESIS. Never invent a result. Cite repo-relative file:line.
- If something blocks you twice, stop that thread and record the cause.

## Known leads (verify, do not trust)
- STATE.md claims structure's `ast.parse(..., type_comments=True)` crash on metadata-stamped files was fixed 2026-11-05. In this zip, src/somnus_debug/structure/core.py:210 still has type_comments=True; root analyze_python_structure.py does not. Root duplicates differ from src/ in other places too (doctor main around line 2066).
- STATE/PLAN claims: test_gaps configured but never emitted; silent_failures name-sensitive; stubs flags abstractmethod/Protocol/overload; duplicate_definitions flags property setters; doctor exit codes 0/1/2/4/5; root python_doctor.yaml read by nothing; default_config.yaml reference-only.
- Every file carries a `# somnus:metadata:v2` header block.

## Deliverable format
Write Markdown into wiki/_evidence/agent-findings/<lane>/ (one or several files) plus any TSV/JSONL the lane asks for. Final reply to the lead: a tight summary of the top findings, files written, commands run with exit codes, and what remains unverified.
