# Experimental extensions

This page holds everything beyond the supported surface: one executed probe that patches private internals, and the research ideas that would need new code. Nothing here is an API. Read [extension-overview](extension-overview.md) first for what is supported.

## Probe: a custom detector by subclassing `CodeQualityVisitor`

This section documents the only way to add a doctor detector without editing the package, and why it is not an extension API.

**Status:** small integration step against private internals. [VERIFIED for 0.1.0; HYPOTHESIS for any other version]. Recorded as [D-19](../DISCOVERY-LEDGER.md#d-19).

**How it works.** `FileAnalyzer.analyze()` creates its visitor with `CodeQualityVisitor(self.config_manager, factory)`, looking the class up by module-global name at call time (`src/somnus_debug/doctor/core.py:1542`). Rebinding `somnus_debug.doctor.core.CodeQualityVisitor` to a subclass before the scan makes every file use the subclass. The subclass calls `self.issue_factory.create(...)` and `self._current_symbol()`, both private, and appends to `self.issues` [SOURCE-CONFIRMED, `src/somnus_debug/doctor/core.py:1143-1358`].

The probe script is lane F's [ext_custom_detector.py](../_evidence/agent-findings/lane-f-ext/recipes/ext_custom_detector.py). Its core:

```python
from somnus_debug.doctor import core

class PrintCallVisitor(core.CodeQualityVisitor):
    def visit_Call(self, node):
        if core.dotted_name(node.func) == "print":
            self.issues.append(self.issue_factory.create(
                "print_calls", node.lineno, node.col_offset, self._current_symbol(),
                "print() call in library code.", "Use the module logger.", {"call": "print"}))
        super().visit_Call(node)

core.CodeQualityVisitor = PrintCallVisitor   # the whole "extension point"
```

Executed: yes (`/tmp/w4/a3/out`, one-file fixture `m.py` whose `shout()` calls `print`; config adds `print_calls: "critical"`; [stage 3 log](../09-recipes/_repro/logs/stage3_advanced.log), section A3)

```text
$ somnus-debug doctor scan ../m -c crit.yaml --no-state -o stock.md --json-output stock.json
Scan complete: files=1, issues=1, critical=0, serious=0                 [exit=0]
$ python ext_custom_detector.py ../m crit.yaml patched
Scan complete: files=1, issues=2, critical=1, serious=0                 [exit=2]
[('suspicious_short_functions', 'minor', 'shout', 4), ('print_calls', 'critical', 'shout', 7)] 78
$ python3 delta.py stock.json patched.json
| critical | `print_calls` | `m.py:7` | `shout` | print() call in library code. |   [exit=1]
```

The custom category reached the JSON, the Markdown, the summary, the score (98 → 78, the −20 critical weight), the exit gate, and `delta.py` with no other change [VERIFIED].

**Why it is not an API.**

- It rebinds a module global; two tools doing it in one process would fight, and the last rebind wins [HYPOTHESIS].
- It depends on four private names: `CodeQualityVisitor`, `issue_factory`, `_current_symbol`, `issues`. None is exported (`somnus_debug.doctor.__all__ == ["main"]`) [VERIFIED, [lane-a API reference](../_evidence/agent-findings/lane-a-arch-api/api-reference.md)].
- Findings inside private functions are attributed to the enclosing scope (`<module>` at top level), because private functions are visited but not pushed on the scope stack (`src/somnus_debug/doctor/core.py:1239-1241`). A custom detector inherits that attribution [VERIFIED by lane F].
- Without a `severity_levels` entry the new category defaults to `minor` (`:792-794`) [VERIFIED by lane F, X2].

Use it to prototype a detector and measure its false-positive rate on a real tree. Do not ship it in CI.

## Probe: patching rule data

This section notes a lighter probe that was not executed in this wave.

`TODO_PATTERNS`, `PLACEHOLDER_CONSTANTS` and `SECURITY_CALLS` are module-level tuples and frozensets (`src/somnus_debug/doctor/core.py:504-514`). Replacing `core.SECURITY_CALLS` with a larger frozenset before a scan would extend the security detector, since `visit_Call` reads the global at call time (`:1229`) [HYPOTHESIS, not executed]. `PLACEHOLDER_CONSTANTS` containing `True` is why `return 1` is flagged ([D-07](../DISCOVERY-LEDGER.md#d-07)); patching it would be a local workaround with the same private-API caveats.

## Research ideas

This section lists extensions that do not exist and would need new code. Each names the gap that motivates it. [HYPOTHESIS for every design here]

| ID | Idea | Motivation (verified gap) | Smallest change |
|---|---|---|---|
| R1 | Config-aware `delta.py` | `delta.py` never compares `config_hash` or recomputes severity, so a latest-scan severity remap launders a regression ([D-21](../DISCOVERY-LEDGER.md#d-21)) | Refuse (exit 3) when `baseline.config_hash != latest.config_hash` unless `--allow-config-change`; optionally recompute severity from one config |
| R1b | Disposition expiry | A broad disposition absorbs new findings and is not reported stale while it matches ([customization](customization.md#dispositions-the-fieldkits-customization-layer)) | Require `symbol` to be non-wildcard, or record the matched finding count per entry and fail when it grows |
| R2 | Detector plug-in seam | No registry or entry points ([plugin-integration](plugin-integration.md)) | Read extra visitor classes from a `somnus_debug.detectors` entry-point group in `FileAnalyzer.analyze()`; severity and delta already generalize |
| R3 | Whole-tree structure graph ("Graphify") | `structure` is one file at a time; doctor's import graph misses `from pkg import mod` edges ([D-06](../DISCOVERY-LEDGER.md#d-06)) | The fieldkit defers it and forbids presenting either as a semantic graph (`skills/somnus-debug-fieldkit/SKILL.md:129`) |
| R4 | Hook adapter | `references/automation.md:59-71` specifies an adapter contract; none ships ([hooks-and-events](hooks-and-events.md)) | A thin wrapper around the [CI gate](../09-recipes/automation/ci-delta-gate.md) that takes changed paths and a lock on the state DB |
| R5 | MCP server | Not present; may be built later by the project owner | Wrap scan, structure and delta as tools over the [automation contracts](../10-agent-usage/automation-contracts.md); force `-o`, `--json-output` and a temp cwd |
| R6 | Neutral harness template | The shipped `execute_test()` is a cargo/gp-cli test ([D-15](../DISCOVERY-LEDGER.md#d-15)) | Ship a placeholder like the [pytest surface](../09-recipes/integrations/harness-pytest.md) used in this wave |

## Sources

This section lists the files, logs and evidence this page rests on.

- [lane-f extensions](../_evidence/agent-findings/lane-f-ext/extensions.md), [lane-f compositions](../_evidence/agent-findings/lane-f-ext/compositions.md), [ext_custom_detector.py](../_evidence/agent-findings/lane-f-ext/recipes/ext_custom_detector.py)
- [lane-a API reference](../_evidence/agent-findings/lane-a-arch-api/api-reference.md)
- `src/somnus_debug/doctor/core.py:504-514`, `:792-794`, `:1143-1358`, `:1229`, `:1239-1241`, `:1542`
- `skills/somnus-debug-fieldkit/SKILL.md:129`, `skills/somnus-debug-fieldkit/references/automation.md:59-71`
- Wave 5 run: [stage 3 log](../09-recipes/_repro/logs/stage3_advanced.log)
