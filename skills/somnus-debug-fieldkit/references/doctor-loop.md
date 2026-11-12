---
somnus:
  schema: "somnus://metadata/core/2.0.0"
  id: "urn:somnus:artifact:01a19ace-75ef-74ca-b8f3-2e7572b9ccf6"
  revision: 1
  title: "Doctor loop: baseline, change, rescan, delta, triage"
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
      - target_ref: "urn:somnus:artifact:01a19ace-75ef-74ca-b8f3-2e7572b9ccf6"
        aspects: ["content"]
  time: {}
  names:
    slug: "doctor-loop-baseline-change-rescan-delta-triage"
  knowledge:
    coverage: "artifact"
    subjects: ["urn:somnus:artifact:01a19ace-75ef-74ca-b8f3-2e7572b9ccf6"]
  access:
    visibility: "internal"
    allowed_uses: ["archive", "search", "reason"]
  ingestion:
    disposition: "candidate"
    body_role: "narrative"
---
# Doctor loop: baseline, change, rescan, delta, triage

This is the operating protocol for any Python change in an onboarded repo. Commands come from `.somnus-debug/PROFILE.md`. `sd` below means that profile's runner, for example `/repo/.venv/bin/python -m somnus_debug.cli`. Run everything from `.somnus-debug/`.

## 0. Preconditions

Check these before the baseline.

- `PROFILE.md` exists. If not, onboard first ([onboarding](onboarding.md)).
- The runner still works: `sd --version`. After an install or upgrade, run `scripts/selftest.py` once.
- If the tree changed shape since onboarding (new package, vendored drop), run `onboard.py <repo>` in plan mode. It rescans and writes nothing.

## 1. Baseline before the first edit

Record the state of the code before you change it.

```console
sd doctor scan .. -c python_doctor.yaml -o runs/baseline.md --json-output runs/baseline.json
```

Check that `files=` matches what you expect, and that the files you're about to touch are in the report. Keep this baseline for the whole work slice; don't overwrite it mid-task. The baseline is what separates pre-existing findings from findings you introduced.

## 2. Orient on the code you'll touch

Run `sd structure ../path/to/file.py` on unfamiliar or dense files. Read the source and its tests. The index gives you definitions and line spans, not behavior. Look up the baseline's findings for those files in [findings](findings.md). Some are fixable in passing; others are false positives to disposition.

## 3. Make the real change and run the real gate

Implement the task. Run the project's own tests, build, and acceptance commands. Doctor never substitutes for them.

## 4. Rescan and delta

Rescan with the same config and compare against the baseline.

```console
sd doctor scan .. -c python_doctor.yaml -o runs/latest.md --json-output runs/latest.json
python3 <skill-dir>/scripts/delta.py runs/baseline.json runs/latest.json --dispositions dispositions.json
```

| delta exit | Meaning | Next move |
|---|---|---|
| 0 | No new serious or critical findings; coverage intact | Review new minor findings in touched files; continue or close |
| 1 | New serious or critical finding | Triage each one (step 5) and repeat steps 3–4 |
| 2 | Coverage regression: zero files, or a baseline file dropped while still on disk | Fix `python_doctor.yaml` coverage first. The other numbers are meaningless until then |
| 3 | Bad input: a usage error, a missing or malformed report, or a `config_hash` that differs between the two reports | Rerun the scan and check paths. For a config change, rescan the baseline with the current config; pass `--allow-config-change` only to compare deliberately |

Findings match on category + file + symbol + message, so code that only moved isn't "new". Resolved findings are listed too: report them as progress.

## 5. Triage

For each new finding, and each persisting one in code you touched:

- **Fix it**, if it's real and in scope. See [findings](findings.md) for the real fix and the evasions to avoid.
- **Disposition it**, if it's a false positive or an accepted design choice. Add `{category, file, symbol, reason}` to `dispositions.json`, as narrow as the evidence allows. Only an exact entry (file and symbol, no glob characters) excuses a new finding; `delta.py` lists new findings a broad entry would have matched and keeps them open.
- **Out of scope**, if it's real but outside this task. Leave it out of the change and mention it in the handoff.
- **Unverified**, if it needs runtime or input you don't have. Say so.

Never lower severities or gates, exclude source, or rename around a check to get exit 0.

## 6. Loop condition

Repeat steps 3–5 after every repair batch while any of these hold: `delta.py` exits nonzero; a new in-scope finding is untriaged; an edited file is missing from the latest report; or the project's gate fails.

## 7. Close

The slice is done when every item holds.

- Native gate passes.
- `delta.py` exits 0 (or each remaining new serious finding is explained in the handoff).
- `dispositions.json` has no stale entries (`delta.py` lists them).
- `sd doctor history .. -c python_doctor.yaml --limit 5` shows the run trend when state is enabled.
- The handoff states: CLI version and runner, baseline and latest file and finding counts, the delta verdict, dispositions added (with reasons), and anything unverified.

## Long sessions

Treat each work slice as one loop: a fresh baseline at the start of the slice, the same config throughout. If coverage must change mid-slice, record why, rescan the baseline with the new config, then continue; `delta.py` refuses reports with different `config_hash` values. Don't trust an earlier scan from memory; reopen the report for the active slice.
