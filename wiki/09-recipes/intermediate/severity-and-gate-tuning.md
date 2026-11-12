# Recipe: remap a category's severity and choose the exit gate

**Tier:** supported now. **Tool:** `doctor` config (`severity_levels`, `severity_exit_level`).

Make doctor's exit code mean what your project needs, for example "fail only on criticals" or "treat stubs as minor in this prototype", and avoid the three config mistakes that silently change the gate.

## When to use

This section says when tuning is legitimate.

When a category's default severity is wrong for the project and the decision is recorded and reviewed. Not to make a red scan green: the fieldkit forbids lowering severities or gates to pass (`skills/somnus-debug-fieldkit/SKILL.md:109`), and in a delta workflow a remap in the latest scan can hide a regression ([D-21](../../DISCOVERY-LEDGER.md#d-21)).

## Steps

This section gives the edit and the scan. `sd` is `/tmp/w4/venv/bin/python -m somnus_debug.cli`.

```console
sd doctor init-config -o cfg.yaml
sed -e 's/^  stubs: "serious"/  stubs: "minor"/' \
    -e 's/^severity_exit_level: "serious"/severity_exit_level: "critical"/' cfg.yaml > tuned.yaml
sd doctor scan <project> -c tuned.yaml --no-state -o t.md --json-output t.json
```

Valid gates are `critical`, `serious`, `minor`, `info`, `none` (`src/somnus_debug/doctor/core.py:2046-2058`) [SOURCE-CONFIRMED]. Severity values are `critical`, `serious`, `minor`, `info`; any category name is accepted, and an unmapped category is `minor` (`:769-779`, `:792-794`) [SOURCE-CONFIRMED].

## Executed result

This section shows the gate moving, and the three traps.

Executed: yes (`/tmp/w4/b1/out`; `proj_nobroken` is the lane-A fixture minus its syntax-error and todo files, 4 files; `proj` is the full 6-file fixture; [stage 2 log](../_repro/logs/stage2_intermediate.log), section I3)

| Config | Change from default | Target | Result | Exit |
|---|---|---|---|---|
| `cfg.yaml` | none | proj_nobroken | `issues=32, critical=0, serious=13` | 1 |
| `tuned.yaml` | `stubs: "minor"`, gate `"critical"` | proj_nobroken | `issues=32, critical=0, serious=7` | 0 |
| `tuned.yaml` | same | proj (has a syntax error) | `issues=37, critical=2, serious=7` | 2 |
| `none_unquoted.yaml` | `severity_exit_level: none` | proj_nobroken | `Doctor failure: Configuration value must be a non-empty string.` | 4 |
| `none_quoted.yaml` | `severity_exit_level: "none"` | proj_nobroken | `issues=32, critical=0, serious=13` | 0 |
| `typo.yaml` | `severity_exit_levle: "critical"` (misspelled key) | proj_nobroken | `issues=32, critical=0, serious=13` | 1 |

What the table shows [VERIFIED]:

1. The remap moved six stubs out of serious without changing the issue count. Severity changes the gate and the score, not detection.
2. The `critical` gate still fails on a real critical (the syntax error), exit 2.
3. **Trap: unquoted `none`.** Doctor's YAML subset maps `none`, `null` and `~` to null, so the gate becomes `None` and validation fails with exit 4. Quote it ([D-03](../../DISCOVERY-LEDGER.md#d-03)).
4. **Trap: typos are silent.** The misspelled key was ignored, the default `serious` gate applied, and the scan exited 1 when the author expected 0 ([D-04](../../DISCOVERY-LEDGER.md#d-04)).

## The third trap: `minor` and `info` gates

This section records a gate behaviour not exercised above but verified by other lanes.

With gate `minor` or `info`, any finding at or above that level returns 1, **including criticals**; the 2 for criticals is only produced by the `serious` and `critical` gates. A wrapper that maps "2 = critical" breaks under those gates ([D-18](../../DISCOVERY-LEDGER.md#d-18)) [VERIFIED by lane D, D26_minor and D26_info; `src/somnus_debug/doctor/core.py:2046-2058`].

## Pitfalls

This section lists the remaining caveats.

- The config is used only with `-c`; editing a `python_doctor.yaml` that is not passed does nothing ([D-02](../../DISCOVERY-LEDGER.md#d-02)).
- A misspelled category (`stubz: minor`) is also accepted silently [VERIFIED by lane F, X6].
- In a fieldkit repo, change `.somnus-debug/python_doctor.yaml` deliberately and re-baseline in the same slice; otherwise delta compares reports produced under different severities ([D-21](../../DISCOVERY-LEDGER.md#d-21)).
- More context: [customization](../../08-extensions/customization.md), [configuration pitfalls](../../06-configuration/configuration-pitfalls.md).

## Sources

This section lists the files, logs and evidence this page rests on.

- [stage 2 log](../_repro/logs/stage2_intermediate.log)
- [lane-b configuration findings](../../_evidence/agent-findings/lane-b-config/configuration-findings.md), [lane-d exit codes](../../_evidence/agent-findings/lane-d-cli-tests/exit-codes.md), [lane-f extensions](../../_evidence/agent-findings/lane-f-ext/extensions.md)
- `src/somnus_debug/doctor/core.py:769-794`, `:2046-2058`; `skills/somnus-debug-fieldkit/SKILL.md:109`
