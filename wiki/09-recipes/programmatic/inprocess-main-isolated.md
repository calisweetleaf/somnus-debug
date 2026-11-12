# Recipe: call doctor's `main()` in-process without losing your logging

**Tier:** small integration step. **Script:** [inprocess_main.py](../_repro/inprocess_main.py).

Run the full CLI code path (config loading, reports, exit code) inside a Python host, then put the host's logging and working directory back exactly as they were.

## When to use

This section says when to prefer `main()` over `ProjectScanner`.

When you want the CLI's exact behaviour, including Markdown and JSON reports and the gate's return code, from Python. If you only need findings as objects, [embedded-scan](embedded-scan.md) is simpler and has no side effects.

`doctor.core.main(argv)` returns 0/1/2/4/5 as an int, but it calls `setup_logging()`, which runs `logging.basicConfig(force=True)` with a file handler for `production_doctor.log` in the cwd (`src/somnus_debug/doctor/core.py:2179-2186`). That removes the host's root handlers ([D-11](../../DISCOVERY-LEDGER.md#d-11)) and drops a log file wherever the host happens to be ([D-10](../../DISCOVERY-LEDGER.md#d-10)) [VERIFIED by lane A, ex3]. argparse errors and `--help` raise `SystemExit` instead of returning [VERIFIED by lane A].

## The code

This section is the isolation wrapper.

```python
import contextlib, logging, os, sys, tempfile
from pathlib import Path
from somnus_debug.doctor.core import main as doctor_main

logging.basicConfig(level=logging.INFO, format="host: %(message)s")
root_logger = logging.getLogger()

@contextlib.contextmanager
def isolated_doctor():
    """Run doctor in a temp cwd and restore the root logger's handlers and level afterwards."""
    saved_handlers, saved_level, saved_cwd = list(root_logger.handlers), root_logger.level, os.getcwd()
    with tempfile.TemporaryDirectory() as tmp:
        os.chdir(tmp)
        try:
            yield Path(tmp)
        finally:
            for handler in root_logger.handlers:
                if handler not in saved_handlers:
                    handler.close()            # release production_doctor.log before the temp dir goes
            root_logger.handlers[:] = saved_handlers
            root_logger.setLevel(saved_level)
            os.chdir(saved_cwd)

project, out = Path(sys.argv[1]).resolve(), Path(sys.argv[2]).resolve()
out.mkdir(parents=True, exist_ok=True)
with isolated_doctor():
    code = doctor_main(["scan", str(project), "--no-state", "-o", str(out / "r.md"), "--json-output", str(out / "r.json")])
```

Paths must be absolute before entering the context, because the cwd changes inside it.

## Executed result

This section shows the handlers before, during and after.

Executed: yes (output shown is from `_repro/inprocess_main.py`, which adds extra prints to this snippet; `/tmp/w4/p`, 4-file fixture; [stage 4 log](../_repro/logs/stage4_programmatic.log), section P3)

```text
$ python inprocess_main.py proj work/out
handlers before: [<StreamHandler <stderr> (NOTSET)>]
Scan complete: files=4, issues=32, critical=0, serious=13
handlers during: [<FileHandler /tmp/tmpwz2o1plz/production_doctor.log (NOTSET)>]
main() returned 1
handlers after: [<StreamHandler <stderr> (NOTSET)>]
host: host logging still works
cwd log here: False out: ['r.json', 'r.md']                                  [exit=0]
```

During the call doctor had replaced the host's stderr handler; afterwards the host handler was back and logging worked again; no log file was left in the host's cwd [VERIFIED].

## Pitfalls

This section lists what the wrapper does not handle.

- **Not thread-safe.** `os.chdir` and the root logger are process-global; do not run two of these at once, or alongside other code that logs.
- **`SystemExit` on usage errors.** Wrap the call in `try/except SystemExit` if the argv comes from users.
- **The `cli` dispatcher temporarily sets `sys.argv`** and converts `SystemExit` to an int ([lane-a API reference §5](../../_evidence/agent-findings/lane-a-arch-api/api-reference.md)), but it imports every tool, so it needs PyYAML ([D-13](../../DISCOVERY-LEDGER.md#d-13)). `doctor.core.main` alone does not.
- **Stateful scans** (no `--no-state`) create the state directory under the project root and are subject to same-second run-ID collisions ([D-08](../../DISCOVERY-LEDGER.md#d-08)).

## Sources

This section lists the files, logs and evidence this page rests on.

- [stage 4 log](../_repro/logs/stage4_programmatic.log), [inprocess_main.py](../_repro/inprocess_main.py)
- [lane-a API reference §1, §5](../../_evidence/agent-findings/lane-a-arch-api/api-reference.md), [lane-a ex3](../../_evidence/agent-findings/lane-a-arch-api/examples/ex3_side_effects.py.txt)
- `src/somnus_debug/doctor/core.py:2179-2199`
