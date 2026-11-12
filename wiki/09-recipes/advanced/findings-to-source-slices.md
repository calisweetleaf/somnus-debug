# Recipe: turn new findings into the exact source lines to read

**Tier:** supported now (stdlib glue over shipped outputs). **Scripts:** lane F's [findings_to_slices.py](../../_evidence/agent-findings/lane-f-ext/recipes/findings_to_slices.py) and [structure_slice.py](../../_evidence/agent-findings/lane-f-ext/recipes/structure_slice.py).

Print only the enclosing function or class for each new finding, instead of opening whole files. Useful for agents with limited context and for reviewers.

## When to use

This section says which of the two variants to pick.

- **From a delta** (`findings_to_slices.py`): after a [baseline-delta loop](../intermediate/baseline-delta-loop.md) rescan, to read only what regressed. It uses doctor's JSON report, whose `files[].functions[]` and `files[].classes[]` carry `qualname`, `line_number` and `end_line_number`, so no extra tool call is needed.
- **By name** (`structure_slice.py`): when you know which definitions you want in one file. It runs `structure` and parses its `(lines A-B)` spans.

## Steps

This section gives the commands. Run from `.somnus-debug/` in an onboarded repo.

```console
python3 <fieldkit>/scripts/delta.py runs/baseline.json runs/latest.json --dispositions dispositions.json --json > runs/delta.json
python3 findings_to_slices.py runs/latest.json runs/delta.json            # serious and critical only
python3 findings_to_slices.py runs/latest.json runs/delta.json --all      # include minor
python3 structure_slice.py <python-with-somnus-debug> ../src/inventory/store.py parse_qty
```

`findings_to_slices.py` first re-hashes every scanned file and compares it with the report's `file_hash` (sha256). If anything changed since the scan it refuses with exit 2, because line spans from a stale report point at the wrong code.

## Executed result

This section shows both scripts, including the guard and the missing-name case.

Executed: yes (`/tmp/w4/proj/.somnus-debug` with `export_report()` calling `os.system` added; [stage 3 log](../_repro/logs/stage3_advanced.log), section A2)

```text
$ python3 findings_to_slices.py runs/latest.json runs/delta.json
### serious security_risks src/inventory/store.py:47 export_report: High-risk call detected: os.system.
   44  def export_report(path: str) -> int:
   45      """Export the stock report by shelling out to a helper."""
   46      import os
   47      status = os.system("report-tool " + path)
   48      code = int(status)
   49      return code                                                        [exit=0]
$ echo '# touched after scan' >> ../src/inventory/store.py
$ python3 findings_to_slices.py runs/latest.json runs/delta.json
STALE REPORT: files changed since the scan: ['src/inventory/store.py']. Rescan first.   [exit=2]
$ python3 structure_slice.py /tmp/w4/proj/.venv/bin/python ../src/inventory/store.py parse_qty nope
not in index: ['nope']
--- ../src/inventory/store.py:17-24 (parse_qty)
   17  def parse_qty(raw: str) -> int:
   ...
   24      return value                                                       [exit=1]
```

`structure_slice.py` printed the span it found and exited 1 because one requested name was missing [VERIFIED].

## Pitfalls

This section lists the limits of both variants.

- **`<module>` findings have no span.** Module-level code, and anything inside a private function (private functions are visited but not put on the scope stack, `src/somnus_debug/doctor/core.py:1239-1241`), is attributed to `<module>`. The script prints "no definition span for this symbol; read around the line" [SOURCE-CONFIRMED in the script].
- **`structure_slice.py` crashes with any metadata-stamped file**, because `structure` does ([D-01](../../DISCOVERY-LEDGER.md#d-01)). The delta variant does not use `structure` and is unaffected. For stamped files, see [programmatic/index-stamped-file](../programmatic/index-stamped-file.md).
- **Bare names in `structure_slice.py`.** It matches the bare def or class name, so two methods named `run` in different classes both print [SOURCE-CONFIRMED, regex in the script].
- **Neither is a semantic graph.** The fieldkit forbids presenting indexes or doctor's import cycles as one (`skills/somnus-debug-fieldkit/SKILL.md:129`).

## Sources

This section lists the files, logs and evidence this page rests on.

- [stage 3 log](../_repro/logs/stage3_advanced.log)
- [lane-f compositions C2, C2b, C8](../../_evidence/agent-findings/lane-f-ext/compositions.md), [doctor JSON shape](../../_evidence/agent-findings/lane-f-ext/logs/s1_doctor_json_shape.txt)
- `src/somnus_debug/doctor/core.py:1239-1241`, `skills/somnus-debug-fieldkit/SKILL.md:129`
