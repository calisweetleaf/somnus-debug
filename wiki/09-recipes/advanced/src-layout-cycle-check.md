# Recipe: check import cycles in a src-layout project

**Tier:** supported now (a second scan). Works around the anti-composition recorded as [D-22](../../DISCOVERY-LEDGER.md#d-22).

Get a real `dependency_cycles` result for a `src/` layout package, where the fieldkit's normal runner reports zero cycles regardless of the code.

## When to use

This section explains why the normal scan is blind here.

In any src-layout repo onboarded with the fieldkit. Onboard runs doctor with `PYTHONPATH=src` so the project's own imports resolve (`skills/somnus-debug-fieldkit/scripts/onboard.py:236-238`). Doctor indexes modules by path from the scan root, so `src/pkg/a.py` is `src.pkg.a`, while `import pkg.b` is resolved through `importlib.util.find_spec` in doctor's interpreter. With `src` on the path, `find_spec("pkg")` succeeds and the import is classified `third_party`, so no local edge exists and no cycle can be found (`src/somnus_debug/doctor/core.py:984-1016`) [SOURCE-CONFIRMED; VERIFIED below].

## Steps

This section gives the extra scan. `sd` is `/tmp/w4/venv/bin/python -m somnus_debug.cli`.

```console
sd doctor scan <repo>/src --no-state -o cycles.md --json-output cycles.json      # src/ as the project root
python3 -c "import json; r=json.load(open('cycles.json')); print(r['summary']['dependency_cycles'], r['dependency_graph']['cycles'])"
```

Use the same `-c` config as the main scan if you have one (its ignore patterns are relative to the scan root, so check `files_scanned`).

## Executed result

This section compares the three ways of scanning the same two-module cycle.

Executed: yes (`/tmp/w4/a4`, `repo/src/pkg/a.py` does `import pkg.b`, `repo/src/pkg/b.py` does `import pkg.a`; [stage 3 log](../_repro/logs/stage3_advanced.log), section A4)

| Scan | Exit | `dependency_cycles` | `missing_imports` | `pkg.*` edges |
|---|---|---|---|---|
| root `repo/`, no `PYTHONPATH` | 1 | 0 | 2 | `pkg.b` and `pkg.a` → `missing` |
| root `repo/`, `PYTHONPATH=repo/src` (the onboard runner) | 0 | 0 | 0 | `pkg.b` and `pkg.a` → `third_party`, no target |
| root `repo/src` | 1 | **1** | 0 | `pkg.b` → `local` `pkg/b.py`; `pkg.a` → `local` `pkg/a.py`; cycle `['pkg/a.py', 'pkg/b.py']` |

The onboard runner removed the `missing_imports` noise and the cycle with it; the `src/`-rooted scan found the cycle [VERIFIED].

## Pitfalls

This section lists what the workaround does not fix.

- **`from pkg import b` still hides the cycle**, even with `src/` as root: both `from pkg import b` and `from . import b` resolve to `pkg/__init__.py` ([D-06](../../DISCOVERY-LEDGER.md#d-06)) [VERIFIED by lane F, C7 last row]. The workaround covers the `import pkg.b` form only.
- **Tests are outside `src/`.** The second scan sees only the package; keep the main scan for coverage and findings.
- **Don't fold this into the delta baseline.** Its `project_root` and file paths differ from the main scan, so `delta.py` would report every file as dropped (exit 2) [HYPOTHESIS from `delta.py:176-181`, not run].
- **Cycles are import edges, not a semantic graph** (`skills/somnus-debug-fieldkit/SKILL.md:129`).

## Sources

This section lists the files, logs and evidence this page rests on.

- [stage 3 log](../_repro/logs/stage3_advanced.log)
- [lane-f compositions C7](../../_evidence/agent-findings/lane-f-ext/compositions.md), [lane-f s4 C7 log](../../_evidence/agent-findings/lane-f-ext/logs/s4_C7.log)
- `src/somnus_debug/doctor/core.py:984-1048`, `skills/somnus-debug-fieldkit/scripts/onboard.py:236-238`, `skills/somnus-debug-fieldkit/scripts/delta.py:176-181`
