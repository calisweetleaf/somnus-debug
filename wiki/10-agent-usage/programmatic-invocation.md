# Programmatic invocation

This page shows the three ways an agent's code can drive somnus-debug: as subprocesses (the default), through the library classes in-process, and through the fieldkit scripts. Each pattern was executed in this wave; the full scripts are in the recipes.

## Choose the mode

This section compares the modes on what matters to an agent.

| Mode | Isolation | Output | Side effects | When |
|---|---|---|---|---|
| Subprocess: `<venv>/bin/python -m somnus_debug.cli …` | Separate process, project interpreter | Exit code, stdout lines, JSON report files | Log file in cwd, reports, state | Default; what the fieldkit does |
| In-process library: `ProjectScanner(root, ConfigManager(cfg)).scan({})` | Same process | Python objects; `dumps_json` gives the CLI's JSON | None on disk, no logging changes | Python hosts that need objects |
| In-process `doctor.core.main(argv)` | Same process | Exit code as int, report files | Replaces root logging handlers; log in cwd | Only when the exact CLI path is needed, inside an isolation wrapper |

[VERIFIED: [embedded-scan](../09-recipes/programmatic/embedded-scan.md), [inprocess-main-isolated](../09-recipes/programmatic/inprocess-main-isolated.md), and every CLI recipe]

## Subprocess pattern

This section is the reference implementation an agent tool should follow.

```python
import json, os, subprocess, tempfile
from pathlib import Path

def doctor_scan(repo: Path, python: Path, config: Path, out_dir: Path, src_layout: bool) -> dict:
    """Run one doctor scan with explicit config and outputs; return a summary the caller can branch on."""
    # Make paths absolute first: doctor runs in a temp cwd, so relative paths would resolve against it.
    # Use absolute(), not resolve(), for the interpreter: resolve() follows venv/bin/python to the base
    # interpreter and loses the venv (the same trap as onboard.py --python, D-20).
    repo, python, config, out_dir = (Path(p).absolute() for p in (repo, python, config, out_dir))
    env = dict(os.environ, PYTHONPATH=str(repo / "src")) if src_layout else None
    md, js = out_dir / "latest.md", out_dir / "latest.json"
    with tempfile.TemporaryDirectory() as cwd:          # keeps production_doctor.log out of the repo
        proc = subprocess.run([str(python), "-m", "somnus_debug.cli", "doctor", "scan", str(repo),
                               "-c", str(config), "--no-state", "-o", str(md), "--json-output", str(js)],
                              cwd=cwd, env=env, text=True, capture_output=True, check=False)
    if proc.returncode >= 4 or not js.exists():      # no report means no result, whatever the exit code
        return {"ran": False, "exit": proc.returncode, "stderr": [line for line in proc.stderr.strip().splitlines() if line.strip()][:1]}
    report = json.loads(js.read_text(encoding="utf-8"))
    return {"ran": True, "exit": proc.returncode, "files": report["summary"]["files_scanned"],
            "serious": report["summary"]["serious_issues"], "report": str(js)}
```

Executed: yes ([doctor_scan_subprocess.py](../09-recipes/_repro/doctor_scan_subprocess.py) run against the onboarded fixture; [stage 6c log](../09-recipes/_repro/logs/stage6c_subprocess_pattern.log))

```text
$ python3 doctor_scan_subprocess.py /tmp/w4/proj /tmp/w4/proj/.venv/bin/python /tmp/w4/proj/.somnus-debug/python_doctor.yaml out
{'ran': True, 'exit': 1, 'files': 4, 'serious': 1, 'report': '/tmp/w4/s6c/out/latest.json'}
$ python3 doctor_scan_subprocess.py /tmp/w4/proj /tmp/w4/proj/.venv/bin/python bad.yaml out2      # severity_exit_level: "bogus"
{'ran': False, 'exit': 4, 'stderr': ['Doctor failure: Invalid severity_exit_level.']}
$ git -C /tmp/w4/proj status --short
                                                                     # nothing written into the repo
```

Two earlier drafts of this wrapper failed, and both failures are worth knowing [VERIFIED, logs kept]:

1. **Relative paths.** Passing `out` and `bad.yaml` relative while doctor ran in a temp cwd made doctor write the reports into the temp directory and look for the config there; the wrapper then crashed reading a JSON that was never written ([first attempt log](../09-recipes/_repro/logs/stage6c_first_attempt_relative_paths.log)).
2. **`Path.resolve()` on the interpreter.** Resolving `/tmp/w4/proj/.venv/bin/python` followed the symlink to `/usr/local/bin/python3.12`, which cannot import `somnus_debug` (the same interpreter onboard reports as `cannot import somnus_debug`), so no report was written ([second attempt log](../09-recipes/_repro/logs/stage6c_second_attempt_resolved_interpreter.log)). This is the same mistake as `onboard.py --python` ([D-20](../DISCOVERY-LEDGER.md#d-20)). Use `absolute()`, and treat "no report file" as "did not run" whatever the exit code.

The fieldkit's `onboard.py` uses the same overall shape (`skills/somnus-debug-fieldkit/scripts/onboard.py:397-412`).

Rules the pattern encodes:

1. Absolute paths, and `absolute()` rather than `resolve()` for a venv interpreter.
2. Argv lists, never a shell string (the fieldkit's stated convention, `SKILL.md:101`).
3. A cwd the agent owns, so the log does not land in the repo ([D-10](../DISCOVERY-LEDGER.md#d-10)).
4. Explicit `-c`; doctor finds no config by itself ([D-02](../DISCOVERY-LEDGER.md#d-02)).
5. Both output paths; never `-o something.json` ([D-25](../DISCOVERY-LEDGER.md#d-25)).
6. `--no-state` unless history is wanted; if it is, at least one second between scans ([D-08](../DISCOVERY-LEDGER.md#d-08)).
7. Exit ≥ 4 means no result; exit 2 needs stderr to tell critical findings from argparse errors ([D-18](../DISCOVERY-LEDGER.md#d-18)).
8. `files_scanned == 0` is a failure regardless of exit code ([D-17](../DISCOVERY-LEDGER.md#d-17)).

## Delta from code

This section shows how to consume the gate.

```console
python3 <fieldkit>/scripts/delta.py runs/baseline.json runs/latest.json --dispositions dispositions.json --json
```

Parse stdout as JSON only when the exit code is 0, 1 or 2 **and** stdout starts with `{`: an argparse error also exits 2 with usage text on stderr, and a malformed issue crashes with exit 1 and a traceback ([failure-recovery](failure-recovery.md)). The lane-F harness surface does exactly this check (`json.loads(delta.stdout) if delta.stdout.strip().startswith("{") else {}`, [harness_doctor_surface.py](../_evidence/agent-findings/lane-f-ext/recipes/harness_doctor_surface.py)) [VERIFIED in [harness-doctor-delta](../09-recipes/integrations/harness-doctor-delta.md)]. Object shape: [automation-contracts](automation-contracts.md#deltapy---json).

`delta.py` is a script, not an importable module of the package. Importing it with `runpy` or `importlib` from the fieldkit path would work in principle (its `main(argv)` returns an int, `delta.py:235-255`) [HYPOTHESIS, not executed]; the subprocess form is what the fieldkit and this wiki use.

## In-process library

This section summarizes the two in-process recipes.

- **No side effects:** `ProjectScanner(Path(root), ConfigManager(None or Path(cfg))).scan({})` returned 4 files / 32 issues with no new paths and root handlers `[]`; `dumps_json(result)` matched the CLI's report in every key except `run_id`, `started_at`, `finished_at` [VERIFIED, [embedded-scan](../09-recipes/programmatic/embedded-scan.md)].
- **Indexing:** `from somnus_debug.structure import build_index` is exported; blank the metadata header first on stamped files [VERIFIED, [index-stamped-file](../09-recipes/programmatic/index-stamped-file.md)].
- **`main()`:** wrap it to restore root handlers and cwd [VERIFIED, [inprocess-main-isolated](../09-recipes/programmatic/inprocess-main-isolated.md)].
- **Scaffold:** `from somnus_debug.test_harness.scaffold import scaffold` → `scaffold(target, force=False, with_contract=True) -> list[Path]`, raising `FileExistsError` before writing anything [VERIFIED by lane A, ex7].

Nothing outside `__version__`, the `main` functions and `build_index` is exported; `ProjectScanner`, `ConfigManager` and the rest live in `somnus_debug.doctor.core` and are not marked stable [VERIFIED, [lane-a API reference §0](../_evidence/agent-findings/lane-a-arch-api/api-reference.md)]. Full API: [public-api](../04-library-api/public-api.md).

## Sources

This section lists the files, logs and evidence this page rests on.

- [embedded-scan](../09-recipes/programmatic/embedded-scan.md), [index-stamped-file](../09-recipes/programmatic/index-stamped-file.md), [inprocess-main-isolated](../09-recipes/programmatic/inprocess-main-isolated.md), [ci-delta-gate](../09-recipes/automation/ci-delta-gate.md)
- [lane-a API reference](../_evidence/agent-findings/lane-a-arch-api/api-reference.md), [lane-f harness_doctor_surface.py](../_evidence/agent-findings/lane-f-ext/recipes/harness_doctor_surface.py)
- `skills/somnus-debug-fieldkit/scripts/onboard.py:397-412`, `skills/somnus-debug-fieldkit/scripts/delta.py:235-255`, `skills/somnus-debug-fieldkit/SKILL.md:101`
