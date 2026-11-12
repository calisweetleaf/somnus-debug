"""Call doctor's main() in-process without losing the host's logging or littering the cwd."""
import contextlib
import logging
import os
import sys
import tempfile
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
                    handler.close()
            root_logger.handlers[:] = saved_handlers
            root_logger.setLevel(saved_level)
            os.chdir(saved_cwd)


project, out = Path(sys.argv[1]).resolve(), Path(sys.argv[2]).resolve()
out.mkdir(parents=True, exist_ok=True)
print("handlers before:", root_logger.handlers)
with isolated_doctor():
    code = doctor_main(["scan", str(project), "--no-state", "-o", str(out / "r.md"), "--json-output", str(out / "r.json")])
    print("handlers during:", root_logger.handlers)
print("main() returned", code)
print("handlers after:", root_logger.handlers)
logging.info("host logging still works")
print("cwd log here:", Path("production_doctor.log").exists(), "out:", sorted(p.name for p in out.iterdir()))
