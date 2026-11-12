# Recipe: first doctor scan with a config, reports where you want them

**Tier:** supported now. **Tools:** `doctor init-config`, `doctor scan`.

Run doctor once on a project without leaving files in it, then read the result from JSON instead of eyeballing the Markdown.

## When to use

This section says when this recipe is the right starting point.

Use it the first time you point doctor at a codebase, or whenever you need a one-off scan without the fieldkit profile. For a repo you will work in repeatedly, use [onboard-a-repo](../intermediate/onboard-a-repo.md) instead.

## Steps

This section gives the commands in order. `sd` stands for the runner used in this wave, `/tmp/w4/venv/bin/python -m somnus_debug.cli`, which is equivalent to the `somnus-debug` console script.

```console
mkdir out && cd out                       # a directory you own: doctor writes production_doctor.log to the cwd
sd doctor init-config -o cfg.yaml          # write the built-in defaults to a file you can edit
sd doctor scan ../proj -c cfg.yaml --no-state -o report.md --json-output report.json
python3 -c "import json; from collections import Counter; r=json.load(open('report.json')); print(r['summary']); print(Counter((i['severity'],i['category']) for i in r['issues']).most_common())"
```

Why each flag matters:

- `-c cfg.yaml`: doctor never finds a config by itself; without `-c` the built-in defaults apply even if a `python_doctor.yaml` is sitting in the project ([D-02](../../DISCOVERY-LEDGER.md#d-02)) [VERIFIED].
- `--no-state`: skips the SQLite history, so no `.python_doctor/` directory appears in the project [SOURCE-CONFIRMED, `src/somnus_debug/doctor/core.py:2061`].
- `-o` and `--json-output`: without them both reports land in the project root ([D-10](../../DISCOVERY-LEDGER.md#d-10)). Do not pass a `.json` path to `-o`; it overwrites the Markdown with JSON ([D-25](../../DISCOVERY-LEDGER.md#d-25)).

## Executed result

This section shows what the run produced.

Executed: yes (`/tmp/w4/b1/out`, the lane-A fixture: 6 files including one syntax error, stubs, a cycle attempt, a `Protocol`, an overload, a property setter; [stage 1 log](../_repro/logs/stage1_beginner.log), section B1)

```text
$ sd doctor init-config -o cfg.yaml
Wrote default configuration: /tmp/w4/b1/out/cfg.yaml                         [exit=0]
$ sd doctor scan ../proj -c cfg.yaml --no-state -o report.md --json-output report.json
Scan complete: files=6, issues=37, critical=2, serious=13
Markdown report: /tmp/w4/b1/out/report.md
JSON report: /tmp/w4/b1/out/report.json                                       [exit=2]
$ ls; ls ../proj
cfg.yaml  production_doctor.log  report.json  report.md
pkg  tests                                                                    # nothing written into the project
{'critical_issues': 2, 'files_scanned': 6, 'minor_issues': 22, 'production_score': 0, 'serious_issues': 13, 'total_issues': 37, ...}
[(('minor', 'suspicious_short_functions'), 11), (('serious', 'stubs'), 6), ... (('critical', 'syntax_errors'), 1), (('critical', 'tokenization_errors'), 1)]
```

Exit 2 means at least one critical finding under the default `serious` gate. The two criticals are the deliberate syntax error, reported twice (`syntax_errors` and `tokenization_errors`) [VERIFIED].

Each issue object carries a fix hint. The first stub, as read from the JSON:

```text
{'category': 'stubs', 'severity': 'serious', 'file_path': 'pkg/b.py', 'line_number': 19, 'symbol': 'stub_func',
 'message': 'Function stub_func has a stub implementation.',
 'remediation': 'Replace pass, ellipsis, or NotImplementedError with a real diagnostic path or domain exception.'}
```

## Reading the result

This section says what to check before believing any number.

1. **`files_scanned` first.** A zero-file scan exits 0 ([D-17](../../DISCOVERY-LEDGER.md#d-17)).
2. **Exit code second:** 0 gate passed, 1 serious, 2 critical, 4 config or doctor error, 5 runtime failure ([exit codes](../../05-cli-and-tools/exit-codes.md)).
3. **Then the findings,** knowing the known false positives: stubs on `@abstractmethod`, `Protocol` and `@overload` bodies, duplicates on property setters, `return 1` as a placeholder ([D-07](../../DISCOVERY-LEDGER.md#d-07)). Several of the 6 stubs here are exactly those cases.
4. **The score is blunt:** `max(0, 100 - 20c - 8s - 2m - i)` reached 0 on six small files (`src/somnus_debug/doctor/core.py:1772`) [SOURCE-CONFIRMED].

## Sources

This section lists the files, logs and evidence this page rests on.

- [stage 1 log](../_repro/logs/stage1_beginner.log); fixture source: [lane-a fixture](../../_evidence/agent-findings/lane-a-arch-api/fixture/proj/pkg/b.py.txt)
- [lane-d command reference](../../_evidence/agent-findings/lane-d-cli-tests/command-reference.md), [lane-d exit codes](../../_evidence/agent-findings/lane-d-cli-tests/exit-codes.md)
- `src/somnus_debug/doctor/core.py:1772`, `:2061`
