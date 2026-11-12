# Customization

Most of what you can change in somnus-debug without code is in the doctor config file and the fieldkit's `dispositions.json`. This page covers those levers from the point of view of shaping the tool to a project: what each lever does, which ones are honest, and which ones quietly hide findings. The complete key-by-key reference is in [complete-option-reference](../06-configuration/complete-option-reference.md); this page does not repeat it.

## The levers, ranked by how safe they are

This section orders the customization levers from "changes what is measured honestly" to "hides findings".

| Lever | Effect | Risk | Evidence |
|---|---|---|---|
| `include_patterns`, `ignore_patterns` | Decide which files are scanned | A wrong glob scans fewer files or zero files, and a zero-file scan exits 0 | [VERIFIED] [D-17](../DISCOVERY-LEDGER.md#d-17); [lane-b §1 items 5-6](../_evidence/agent-findings/lane-b-config/configuration-findings.md) |
| Thresholds: `min_function_lines`, `min_class_lines`, `min_docstring_length`, `max_cyclomatic_complexity` | Move the cutoffs for short-function, short-class, docstring and complexity findings | Low; the finding still exists, at a different cutoff | [SOURCE-CONFIRMED] `src/somnus_debug/doctor/core.py:823-826` |
| `require_*` docstring and hint switches | Turn docstring and type-hint findings on or off | Low | [SOURCE-CONFIRMED] `src/somnus_debug/doctor/core.py:834-838` |
| `detect_unused_imports`, `detect_security_risks`, `detect_silent_failures`, `detect_dependency_cycles` | Turn whole detectors off | Turning off security or silent-failure detection removes serious findings outright | [SOURCE-CONFIRMED] `src/somnus_debug/doctor/core.py:1222`, `:1229`, `:1572`, `:1631` |
| `detect_test_gaps` | Nothing. No code reads it | None, but it misleads | [SOURCE-CONFIRMED] [D-05](../DISCOVERY-LEDGER.md#d-05) |
| `severity_levels` | Move any category to `critical`, `serious`, `minor` or `info`; accepts category names no detector emits | Downgrading drops findings below the gate | [VERIFIED] run below; `src/somnus_debug/doctor/core.py:769-779` |
| `severity_exit_level` | Gate: `critical`, `serious`, `minor`, `info`, `none` | `minor` and `info` exit 1 even when criticals exist; unquoted `none` is null and exits 4 | [VERIFIED] run below; [D-03](../DISCOVERY-LEDGER.md#d-03), [D-18](../DISCOVERY-LEDGER.md#d-18) |
| `ignore_functions`, `ignore_classes` | Skip named functions or classes | `ignore_functions` and `check_nested_functions: false` also skip everything inside the body, security findings included | [VERIFIED] [D-16](../DISCOVERY-LEDGER.md#d-16) |
| Fieldkit `dispositions.json` | Accept specific findings in the delta gate, with a reason | Broad globs absorb future regressions | [VERIFIED] run below; [D-21](../DISCOVERY-LEDGER.md#d-21) |

What you cannot customize: score weights (`max(0, 100 - 20c - 8s - 2m - i)`, `src/somnus_debug/doctor/core.py:1772`), per-line suppression comments (none exist), and toggles for stubs, placeholder returns, incomplete methods, short classes or functions, broad exceptions, complexity, duplicates or todos. For those, the only levers are severity remap and the gate [SOURCE-CONFIRMED, [lane-f extensions](../_evidence/agent-findings/lane-f-ext/extensions.md)].

## Severity remap and gate, executed

This section shows the remap and the gate on one fixture so the interactions are visible.

Executed: yes (`/tmp/w4/b1/out`, lane-A fixture without its syntax-error and todo files, 4 files; full output in [stage 2 log](../09-recipes/_repro/logs/stage2_intermediate.log), section I3)

```console
$ diff cfg.yaml tuned.yaml
44c44
< severity_exit_level: "serious"
---
> severity_exit_level: "critical"
53c53
<   stubs: "serious"
---
>   stubs: "minor"
$ somnus-debug doctor scan ../proj_nobroken -c cfg.yaml --no-state -o d.md --json-output d.json
Scan complete: files=4, issues=32, critical=0, serious=13          [exit=1]
$ somnus-debug doctor scan ../proj_nobroken -c tuned.yaml --no-state -o t.md --json-output t.json
Scan complete: files=4, issues=32, critical=0, serious=7           [exit=0]
$ somnus-debug doctor scan ../proj_nobroken -c none_unquoted.yaml ...   # severity_exit_level: none
Doctor failure: Configuration value must be a non-empty string.    [exit=4]
$ somnus-debug doctor scan ../proj_nobroken -c none_quoted.yaml ...     # severity_exit_level: "none"
Scan complete: files=4, issues=32, critical=0, serious=13          [exit=0]
$ somnus-debug doctor scan ../proj_nobroken -c typo.yaml ...            # severity_exit_levle: "critical"
Scan complete: files=4, issues=32, critical=0, serious=13          [exit=1]
```

Read the last line carefully. The misspelled key was accepted with no warning, the gate stayed at its default `serious`, and the scan exited 1 where the author meant 0 [VERIFIED, [D-04](../DISCOVERY-LEDGER.md#d-04)]. The six stubs moved from serious to minor (13 → 7 serious) without changing the issue count, so the remap changes the gate and the score, not what is found.

The runnable version is [intermediate/severity-and-gate-tuning](../09-recipes/intermediate/severity-and-gate-tuning.md).

## Dispositions: the fieldkit's customization layer

This section explains how `dispositions.json` works and where it leaks.

`delta.py` loads a JSON list of `{category, file, symbol?, reason}` objects (`skills/somnus-debug-fieldkit/scripts/delta.py:129-144`). `category` must match exactly; `file` and `symbol` are `fnmatchcase` globs, `symbol` defaults to `*`; `reason` is required and non-empty, otherwise exit 3 [VERIFIED, [stage 6 log](../09-recipes/_repro/logs/stage6_integrations.log)]. A disposition is checked against **every** finding in the latest report, the first match wins, and any entry that matched nothing is listed as stale (`:159-191`).

Dispositions never touch doctor itself. Doctor still reports the finding and still exits 1 on it; only the delta gate ignores it. In the [baseline-delta loop recipe](../09-recipes/intermediate/baseline-delta-loop.md) the same tree gave doctor exit 1 and delta exit 0 [VERIFIED].

The leak: a broad entry is never stale while it matches something, and it matches new findings too. Executed: yes (`/tmp/w4/proj_h2`, a new `purge()` calling `os.system`; [stage 6 log](../09-recipes/_repro/logs/stage6_integrations.log), section F):

```text
narrow only: exit 1 [('security_risks', 'purge')]
plus broad:  exit 0 [] stale 0          # extra entry {"category":"security_risks","file":"src/*"}
```

The broad entry absorbed the regression and was not reported as stale, because it matched [VERIFIED]. Lane F showed the related case where a stale broad entry later mutes a new finding (L7) [VERIFIED, [lane-f fieldkit §3](../_evidence/agent-findings/lane-f-ext/fieldkit.md)]. Keep `symbol` explicit, keep `file` to one path, and review the list as code.

## Config changes can launder regressions through delta

This section records a gate hole that sits between customization and the regression gate.

`delta.py` compares severities as written in each report. It never compares `config_hash` and never recomputes severity. If the latest scan runs under a config that downgrades a category, a new finding in that category is not a regression [VERIFIED by lane F, case D3, [lane-f fieldkit §3](../_evidence/agent-findings/lane-f-ext/fieldkit.md); [D-21](../DISCOVERY-LEDGER.md#d-21)]. Pin the config path (`-c .somnus-debug/python_doctor.yaml`) for both scans and review config edits like code. Checking `baseline.config_hash == latest.config_hash` yourself before trusting delta is a one-line guard [HYPOTHESIS, not built].

## Pitfalls

This section collects the customization traps in one list.

- No config auto-discovery: an edited `python_doctor.yaml` without `-c` does nothing ([D-02](../DISCOVERY-LEDGER.md#d-02)).
- Unknown keys and misspelled category names are accepted silently ([D-04](../DISCOVERY-LEDGER.md#d-04)).
- `X/*` in `ignore_patterns` prunes every directory named `X` at any depth; `src/**/*.py` does not match `src/a.py` ([D-17](../DISCOVERY-LEDGER.md#d-17)).
- `pycache-clean` config values are not type-checked; `dry_run: no` deletes, and `targets` can name anything ([D-14](../DISCOVERY-LEDGER.md#d-14); [existing-extension-points](existing-extension-points.md#e11-in-practice-targets-turns-the-cleaner-into-a-general-deleter)).
- The fieldkit's load-bearing rule 5 forbids lowering severities or gates to go green (`skills/somnus-debug-fieldkit/SKILL.md:109`). Severity remap is for categories that are wrong for a project, recorded and reviewed, not for passing a gate.

## Sources

This section lists the files, logs and evidence this page rests on.

- [lane-b configuration findings](../_evidence/agent-findings/lane-b-config/configuration-findings.md)
- [lane-f extensions](../_evidence/agent-findings/lane-f-ext/extensions.md), [lane-f fieldkit](../_evidence/agent-findings/lane-f-ext/fieldkit.md)
- `src/somnus_debug/doctor/core.py:769-779`, `:823-849`, `:1222`, `:1229`, `:1572`, `:1631`, `:1772`
- `skills/somnus-debug-fieldkit/scripts/delta.py:129-191`, `skills/somnus-debug-fieldkit/SKILL.md:109`
- Wave 5 runs: [stage 2 log](../09-recipes/_repro/logs/stage2_intermediate.log), [stage 6 log](../09-recipes/_repro/logs/stage6_integrations.log)
