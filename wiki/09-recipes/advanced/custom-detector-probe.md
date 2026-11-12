# Recipe: prototype a custom detector (private-API probe)

**Tier:** small integration step against **private** internals. This is not a public API and must not be presented as one. **Script:** lane F's [ext_custom_detector.py](../../_evidence/agent-findings/lane-f-ext/recipes/ext_custom_detector.py).

Prototype a new doctor finding category, here `print_calls`, to measure how often it fires on a real tree before proposing it upstream.

## When to use

This section draws the line between prototyping and shipping.

Use it to answer "would this detector be useful, and how noisy is it?" on your own machine. Do not put it in CI, a pre-commit hook, or anything another person relies on. somnus-debug 0.1.0 has no detector registry, plugin discovery or hook ([plugin-integration](../../08-extensions/plugin-integration.md)), and this probe works only by rebinding a private module global ([D-19](../../DISCOVERY-LEDGER.md#d-19)).

## Steps

This section gives the config edit and the two scans to compare. `sd` is `/tmp/w4/venv/bin/python -m somnus_debug.cli`.

```console
sd doctor init-config -o base.yaml
# give the new category a severity; unmapped categories default to minor
sed 's/^  duplicate_definitions: "minor"/  duplicate_definitions: "minor"\n  print_calls: "critical"/' base.yaml > crit.yaml
sd doctor scan ../m -c crit.yaml --no-state -o stock.md --json-output stock.json          # stock doctor
python ext_custom_detector.py ../m crit.yaml patched                                     # patched doctor, same config
python3 <fieldkit>/scripts/delta.py stock.json patched.json                              # what the detector adds
```

The probe's mechanism, in full:

```python
from somnus_debug.doctor import core

class PrintCallVisitor(core.CodeQualityVisitor):        # private class
    def visit_Call(self, node):
        if core.dotted_name(node.func) == "print":
            self.issues.append(self.issue_factory.create(  # private attributes
                "print_calls", node.lineno, node.col_offset, self._current_symbol(),
                "print() call in library code.", "Use the module logger.", {"call": "print"}))
        super().visit_Call(node)

core.CodeQualityVisitor = PrintCallVisitor   # FileAnalyzer.analyze() looks the name up at call time (core.py:1542)
raise SystemExit(core.main(["scan", root, "-c", config, "--no-state", "-o", f"{out}.md", "--json-output", f"{out}.json"]))
```

## Executed result

This section shows the category flowing through doctor and delta.

Executed: yes (`/tmp/w4/a3/out`, fixture `m.py` whose `shout()` calls `print`; [stage 3 log](../_repro/logs/stage3_advanced.log), section A3)

```text
$ grep -n print_calls crit.yaml
68:  print_calls: "critical"
$ sd doctor scan ../m -c crit.yaml --no-state -o stock.md --json-output stock.json
Scan complete: files=1, issues=1, critical=0, serious=0                 [exit=0]
$ python ext_custom_detector.py ../m crit.yaml patched
Scan complete: files=1, issues=2, critical=1, serious=0                 [exit=2]
[('suspicious_short_functions', 'minor', 'shout', 4), ('print_calls', 'critical', 'shout', 7)] 78
$ python3 delta.py stock.json patched.json
| production score | 98 | 78 | -20 |
**REGRESSION: new serious/critical findings.**
| critical | `print_calls` | `m.py:7` | `shout` | print() call in library code. |   [exit=1]
```

The new category reached the JSON, the score, the exit gate (2 on a critical) and `delta.py`, which is category-agnostic [VERIFIED].

## Pitfalls

This section lists why the probe is fragile.

- **Private names.** `CodeQualityVisitor`, `issue_factory`, `_current_symbol` and `issues` are not exported (`somnus_debug.doctor.__all__ == ["main"]`). Any refactor can break the probe [HYPOTHESIS for future versions].
- **Process-global.** The rebind affects every scan in the process; run it in its own interpreter, as the script does.
- **Attribution.** Calls inside private functions are reported under the enclosing scope, `<module>` at top level (`src/somnus_debug/doctor/core.py:1239-1241`).
- **Severity defaults to `minor`** if you forget the `severity_levels` entry [VERIFIED by lane F, X2].
- **`main()` side effects still apply:** the log file in the cwd and the replaced root logging handlers ([D-10](../../DISCOVERY-LEDGER.md#d-10), [D-11](../../DISCOVERY-LEDGER.md#d-11)).
- **What a supported version would need** is in [experimental-extensions](../../08-extensions/experimental-extensions.md).

## Sources

This section lists the files, logs and evidence this page rests on.

- [stage 3 log](../_repro/logs/stage3_advanced.log)
- [lane-f extensions](../../_evidence/agent-findings/lane-f-ext/extensions.md), [lane-f s5 log](../../_evidence/agent-findings/lane-f-ext/logs/s5_ext.log)
- `src/somnus_debug/doctor/core.py:769-794`, `:1143`, `:1239-1241`, `:1542`
