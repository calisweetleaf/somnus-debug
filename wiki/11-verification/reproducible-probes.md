# Reproducible probes

This page gives a single self-contained script that rebuilds a venv and fixtures from scratch in `/tmp`. It then re-checks the fifteen behaviors that most affect users. It prints the expected and the actual value for each one. The script was executed end to end while writing this page, and its full output is below. Use it to re-verify a new checkout or release, or to confirm that a fix landed (a fixed defect flips its `got=` value).

## Rules the script follows

This section states the safety properties, so it can be run against the real repo path.

- It only **reads** the repo: `pip install <repo>` (non-editable), `head` of one source file, and a `tar` copy for the test suite. All writes go under the work directory you pass, which should be in `/tmp`.
- `PYTHONDONTWRITEBYTECODE=1` keeps `__pycache__` out of the repo when the root `analyze_python_structure.py` is run in place.
- Every doctor call runs with cwd inside the work directory, so `production_doctor.log` never lands in the repo.
- After the run, `git status --short` in the repo showed only `?? wiki/`, the same as before. [VERIFIED] W2-28.

## The script

This section is the probe script, verbatim.

Executed: yes (`/tmp/w2/probes.sh <repo> /tmp/w2/rp`, Python 3.12.15, about 9 s; W2-28).

```bash
#!/usr/bin/env bash
# Reproducible probes for somnus-debug 0.1.0. Usage: probes.sh <repo> <workdir-under-/tmp>
set -u
REPO="$1"; W="$2"
export PYTHONDONTWRITEBYTECODE=1
rm -rf "$W" && mkdir -p "$W" && cd "$W" || exit 99
python3 -m venv venv >/dev/null && venv/bin/pip install -q pytest "$REPO" 2>/dev/null
V="$W/venv/bin"
p() { printf '%-46s expected=%-3s got=%s\n' "$1" "$2" "$3"; }

# fixture
mkdir -p fx/app run && printf '"""Pkg."""\n' > fx/app/__init__.py
printf '"""Core."""\n\n\ndef parse_count(text: str) -> int:\n    """Parse a count from text, falling back to zero."""\n    try:\n        return int(text)\n    except ValueError:\n        pass\n    return 0\n' > fx/app/core.py
mkdir -p crit && printf 'def oops(:\n' > crit/bad.py
head -32 "$REPO/src/somnus_debug/cli.py" > stamped.py && cat fx/app/core.py >> stamped.py
cd run
# P1 log in cwd even for --help
"$V/somnus-debug" doctor --help >/dev/null; p "P1 doctor --help creates ./production_doctor.log" yes "$([ -f production_doctor.log ] && echo yes || echo no)"
# P2 default gate, serious -> 1
"$V/somnus-debug" doctor scan ../fx --no-state -o "$W/run/r.md" >/dev/null; p "P2 serious finding, default gate" 1 $?
# P3 critical -> 2 ; minor gate -> 1
"$V/somnus-debug" doctor scan ../crit --no-state -o "$W/run/c.md" >/dev/null; p "P3 critical finding, default gate" 2 $?
printf 'severity_exit_level: "minor"\n' > minor.yaml
"$V/somnus-debug" doctor scan ../crit --no-state -o "$W/run/c.md" -c minor.yaml >/dev/null; p "P4 critical finding, minor gate (D-18)" 1 $?
# P5 unquoted none -> 4 ; quoted -> 0
printf 'severity_exit_level: none\n' > u.yaml; printf 'severity_exit_level: "none"\n' > q.yaml
"$V/somnus-debug" doctor scan ../fx --no-state -o "$W/run/r.md" -c u.yaml >/dev/null 2>&1; p "P5 unquoted none (D-03)" 4 $?
"$V/somnus-debug" doctor scan ../fx --no-state -o "$W/run/r.md" -c q.yaml >/dev/null; p "P6 quoted \"none\"" 0 $?
# P7 no auto-discovery
cp q.yaml ../fx/python_doctor.yaml
"$V/somnus-debug" doctor scan ../fx --no-state -o "$W/run/r.md" >/dev/null; p "P7 root python_doctor.yaml ignored (D-02)" 1 $?
rm ../fx/python_doctor.yaml
# P8 -v no effect
rm -f production_doctor.log; "$V/somnus-debug" doctor scan ../fx --no-state -o "$W/run/r.md" --verbose >/dev/null
p "P8 --verbose log bytes" 0 "$(stat -c %s production_doctor.log)"
# P9 structure stamped crash, root duplicate ok
"$V/somnus-debug" structure ../stamped.py >/dev/null 2>&1; p "P9 structure on stamped file (D-01)" 2 $?
python3 "$REPO/analyze_python_structure.py" ../stamped.py >/dev/null 2>&1; p "P10 root analyze_python_structure.py" 0 $?
# P11 same-second collision
mkdir -p ../coll && cp ../fx/app/core.py ../coll/ && cd ../coll
"$V/somnus-debug" doctor scan . >/dev/null; "$V/somnus-debug" doctor scan . >/dev/null
p "P11 runs rows after 2 same-second scans (D-08)" 1 "$(python3 -c "import sqlite3;print(sqlite3.connect('.python_doctor/state.sqlite3').execute('select count(*) from runs').fetchone()[0])")"
cd ../run
# P12 -o x.json collision
"$V/somnus-debug" doctor scan ../fx --no-state -o "$W/run/x.json" >/dev/null; p "P12 files after -o x.json (D-25)" 1 "$(ls "$W/run" | grep -c '^x\.')"
# P13 harness placement
"$V/somnus-debug" init-test-harness ../hroot >/dev/null; python3 ../hroot/run_test.py >/dev/null 2>&1; rc=$?
p "P13 root-scaffolded run_test.py verdict exit" 1 $rc
p "P14 artifacts outside the scaffold dir (D-15)" yes "$([ -d "$W/test-runs" ] && echo yes || echo no)"
# P15 repo tests on a copy
mkdir -p ../repo-copy && (cd "$REPO" && tar --exclude=./wiki --exclude=./.git -cf - .) | tar -xf - -C ../repo-copy
(cd ../repo-copy && "$V/python" -m pytest -q -p no:cacheprovider tests/ 2>&1 | tail -1)
```

## Observed output

This section is the real output of the run above.

```text
P1 doctor --help creates ./production_doctor.log expected=yes got=yes
P2 serious finding, default gate               expected=1   got=1
P3 critical finding, default gate              expected=2   got=2
P4 critical finding, minor gate (D-18)         expected=1   got=1
P5 unquoted none (D-03)                        expected=4   got=4
P6 quoted "none"                               expected=0   got=0
P7 root python_doctor.yaml ignored (D-02)      expected=1   got=1
P8 --verbose log bytes                         expected=0   got=0
P9 structure on stamped file (D-01)            expected=2   got=2
P10 root analyze_python_structure.py           expected=0   got=0
P11 runs rows after 2 same-second scans (D-08) expected=1   got=1
P12 files after -o x.json (D-25)               expected=1   got=1
P13 root-scaffolded run_test.py verdict exit   expected=1   got=1
P14 artifacts outside the scaffold dir (D-15)  expected=yes got=yes
2 failed, 10 passed in 1.35s
```

All 15 probes matched. P15 is the last line: the repo suite on 0.1.0.

## Reading the results after a change

This section says what a different `got=` means for each probe.

| Probe | A fix would show | Note |
|---|---|---|
| P1 | `no` if logging becomes opt-in | [D-10](../DISCOVERY-LEDGER.md#d-10) |
| P4 | `2` if `minor`/`info` start honoring critical | [D-18](../DISCOVERY-LEDGER.md#d-18) |
| P5 | `0` if bare `none` is treated as the string | [D-03](../DISCOVERY-LEDGER.md#d-03) |
| P7 | `0` if auto-discovery is added | [D-02](../DISCOVERY-LEDGER.md#d-02) |
| P9 | `0` once `type_comments=True` is removed from `src/` | [D-01](../DISCOVERY-LEDGER.md#d-01); P15 then reads `12 passed` |
| P11 | `2` if run IDs gain sub-second resolution or uniqueness | [D-08](../DISCOVERY-LEDGER.md#d-08). Can read `2` today if the two scans straddle a second boundary, so rerun before concluding |
| P12 | `2` if the JSON stops overwriting the Markdown | [D-25](../DISCOVERY-LEDGER.md#d-25) |
| P13 | `1` stays: the shipped test is cargo-specific | |
| P14 | `no` if the template's default root changes | [D-15](../DISCOVERY-LEDGER.md#d-15) |

## Other probe collections

This section points at the lane-level probe scripts, which cover more ground.

- Lane F: `repro/s0_setup.sh` to `repro/s6_doc_probes.sh` (onboard, delta, compositions, harness, extension probes), with logs in `logs/`. See [lane F README](../_evidence/agent-findings/lane-f-ext/README.md) and [repro/env.sh](../_evidence/agent-findings/lane-f-ext/repro/env.sh).
- Lane B: `experiments/run_cfg.sh` (config matrix C01-C26) and `experiments/yaml_probe.py` (48 YAML cases, doctor parser vs PyYAML). See [run_cfg.sh](../_evidence/agent-findings/lane-b-config/experiments/run_cfg.sh).
- Lane D: every run's command, cwd, exit code, stdout/stderr, and file delta in [experiments.jsonl](../_evidence/agent-findings/lane-d-cli-tests/experiments.jsonl). Its runner script was lost with `/tmp`, but each row is enough to replay a run.

## Sources

This section lists the code and evidence this page draws on.

- `src/somnus_debug/doctor/core.py:82`, `:625-626`, `:796-799`, `:1953-1960`, `:1975`, `:2046-2058`, `:2179-2186`
- `src/somnus_debug/structure/core.py:210`; `analyze_python_structure.py:210`
- `src/somnus_debug/test_harness/templates/run_test.py:749`
- `tests/test_cli_smoke.py`
- W2 runs: [verification-results](verification-results.md#w2-runs)
