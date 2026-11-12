# Common workflows

This page describes the recurring jobs people actually do with somnus-debug. For each job it gives the command sequence, what to read in the output, and the trap specific to that job. Each workflow is built from steps executed in this wave or by the evidence lanes, and the evidence is cited per step.

## 1. Triage an unfamiliar codebase

This section is for a first look at a repo you did not write.

1. Run from a scratch directory, without state, with the reports outside the repo:

   ```bash
   somnus-debug doctor scan /repo --no-state -o /tmp/triage/d.md --json-output /tmp/triage/d.json
   ```

   [VERIFIED] W2-21 pattern.
2. Check `summary.files_scanned` first. If it is 0 or suspiciously low:
   - your config's globs do not match the layout, or
   - a default ignore such as `env/*` or `build/*` pruned a real package directory.

   See [D-17](../DISCOVERY-LEDGER.md#d-17).
3. Rank findings by category:

   ```bash
   python3 -c "import json,collections;d=json.load(open('/tmp/triage/d.json'));print(collections.Counter((i['severity'],i['category']) for i in d['issues']).most_common(10))"
   ```

   Executed: yes, same expression form as W2-19's per-file count.
4. Discount the known false-positive families before acting on them:
   - `return 1` flagged as a placeholder
   - stubs on `@abstractmethod`/`Protocol`/`@overload`
   - duplicates on property setters
   - short-class findings on frozen dataclasses
   - name-sensitive `silent_failures`

   See [D-07](../DISCOVERY-LEDGER.md#d-07).
5. For a src layout, rerun with `PYTHONPATH=/repo/src`. Otherwise every own-package import is a serious `missing_imports`. [VERIFIED] W2-14.

Trap: the interpreter running doctor decides which third-party imports count as missing ([D-26](../DISCOVERY-LEDGER.md#d-26)).

## 2. Keep a project from getting worse (baseline loop)

This section is for repos with existing findings you cannot fix today.

1. Record a baseline: a stateful scan with `-c`, then copy the JSON.
2. On each change, scan again and run `delta.py baseline.json latest.json [--dispositions dispositions.json]`.
3. Fix or disposition anything `delta.py` calls new. Dispositions must be narrow (`category` + `file` glob + `symbol` glob + `reason`).
4. Promote the baseline only when delta exits 0 and no dispositions are stale (the ratchet).

[VERIFIED] W2-14/W2-17 (delta exit 1 on the regression, 0 after the fix); lane F C1-C3. The full walk-through is in [first-project](first-project.md).

Traps:

- A stale but broad disposition silently mutes future findings.
- A looser `-c` on the latest scan launders regressions, because `config_hash` is not compared.

See [D-21](../DISCOVERY-LEDGER.md#d-21).

## 3. Gate a pull request in CI

This section is for a pass/fail signal in a pipeline.

Use the tested script in [automation-examples](../05-cli-and-tools/automation-examples.md#example-1-ci-gate-on-the-raw-doctor-result) (raw gate) or lane F's `ci_delta_gate.sh` (regression gate). In both cases:

- Pass `-c`.
- Quote the gate value.
- Use `--no-state`.
- Assert `files_scanned > 0`.
- Map doctor exit codes 4 and 5 to "the tool failed", not to "the code failed".

[VERIFIED] W2-21; lane F C1.

## 4. Read a large file efficiently

This section is for agents or reviewers who need the shape of a file before reading it.

1. `somnus-debug structure big.py` gives the class/method map with line spans. [VERIFIED] W2-15.
2. Read only the spans you need, or join doctor findings to spans. Lane F's recipes do this: `findings_to_slices.py` and `structure_slice.py`. The latter refuses a stale report (exit 2) when the file changed since the scan. [VERIFIED] lane F C2a-C2c ([compositions.md](../_evidence/agent-findings/lane-f-ext/compositions.md)).

Trap: any file carrying a `# somnus:metadata:v2` header (all of this repo) crashes `structure` with exit 2. Use the repo-root `analyze_python_structure.py` for those files. [VERIFIED] W2-15. See [D-01](../DISCOVERY-LEDGER.md#d-01).

## 5. Clean bytecode before packaging or archiving

This section is for removing `__pycache__` and stray `.pyc`/`.pyo` files.

1. Write a config with **absolute** `roots` as a YAML list and **bare-name** `exclude` entries.
2. Run `--dry-run --verbose` and read the `Removed ...` lines as "would remove".
3. Run for real. Grep the output for `[ERROR] Root path does not exist`, because the exit code stays 0 when a root is missing.

[VERIFIED] W2-18. Hazards: [D-14](../DISCOVERY-LEDGER.md#d-14).

Running pycache-clean first has no effect on later doctor results. [VERIFIED] lane F C4.

## 6. Onboard a repo with the fieldkit (agents)

This section is for setting up a per-repo profile in one step.

```bash
python3 <fieldkit>/scripts/onboard.py /repo                      # plan mode: survey + verification scan
python3 <fieldkit>/scripts/onboard.py /repo --apply --baseline   # write .somnus-debug/ and record runs/baseline.*
```

This writes `.somnus-debug/{python_doctor.yaml, pycache.yaml, dispositions.json, .gitignore, PROFILE.md}`, plus `state/` and `runs/baseline.{md,json}`. It never overwrites existing files. [VERIFIED] lane F O2/O3; lane D O01-O03.

Traps:

- A root `python_doctor.yaml` is adopted by default. This repo's own root config scans 0 files on a normal tree; pass `--new-config` to avoid that.
- `--apply` writes `PROFILE.md` even when verification fails.
- A doctor config error crashes onboard with exit 1 instead of the documented 2.

See [D-20](../DISCOVERY-LEDGER.md#d-20).

## 7. Undo a bad "latest" after a misconfigured scan

This section is for when the latest report should not be the comparison point.

Run `somnus-debug doctor history <root>` to find a good run ID, then `somnus-debug doctor rollback <root> --run-id <id>`. The rollback repoints `.python_doctor/reports/latest.*` and the hash index that the next scan's `state_delta` uses. It leaves the root `production_doctor_report.*` alone. [VERIFIED] W2-16; lane F C3d/C3g. See [D-09](../DISCOVERY-LEDGER.md#d-09).

## Sources

This section lists the code and evidence this page draws on.

- `src/somnus_debug/doctor/core.py:1916-2010`, `:2061-2120`
- `src/somnus_debug/pycache_cleaner/core.py:255-290`
- [lane F compositions.md](../_evidence/agent-findings/lane-f-ext/compositions.md), [fieldkit.md](../_evidence/agent-findings/lane-f-ext/fieldkit.md), [recipes/](../_evidence/agent-findings/lane-f-ext/recipes/findings_to_slices.py)
- [lane D experiment-log.md](../_evidence/agent-findings/lane-d-cli-tests/experiment-log.md)
- W2 runs: [verification-results](../11-verification/verification-results.md#w2-runs)
