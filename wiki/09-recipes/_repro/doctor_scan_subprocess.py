"""Reference subprocess wrapper for agents: one doctor scan with explicit config and outputs."""
import json
import os
import subprocess
import sys
import tempfile
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


if __name__ == "__main__":
    repo, python, config, out = (Path(a) for a in sys.argv[1:5])
    out.mkdir(parents=True, exist_ok=True)
    print(doctor_scan(repo, python, config, out, src_layout=(repo / "src").is_dir()))
