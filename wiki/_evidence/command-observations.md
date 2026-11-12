# Command Observations

This page indexes observed CLI behavior per command; full transcripts are in lane D's experiment log and raw JSONL.

## Observed exit codes

This section summarizes exit codes observed across lanes A, B, D, and F, each from at least one executed run.

| Command | 0 | 1 | 2 | 3 | 4 | 5 |
|---|---|---|---|---|---|---|
| `doctor scan` | below gate | serious gate tripped; also any gate `minor`/`info` | critical gate tripped; argparse error | n/a | config error; missing root only with `--no-state` or an uncreatable path (D-29); unwritable report path; a broken state DB makes scan fall back to stateless (D-28) | classified runtime error (e.g. RecursionError) |
| `doctor init-config` | written | | argparse | | exists without `--force` | |
| `doctor history` | listed | | argparse | | state unavailable | |
| `doctor rollback` | alias moved | | argparse / missing `--run-id` | | unknown run id | |
| `doctor self-check` | clean | findings (observed 1) | | | read-only package dir without `-o` | |
| `structure` | indexed | latin-1 file traceback (lane B) | every handled error incl. argparse and stamped-file SyntaxError | | | |
| `pycache-clean` | done, incl. missing root | config error, bad YAML traceback | argparse | | | |
| `init-test-harness` | scaffolded | refuses overwrite | argparse | | | |
| dispatcher `somnus-debug` | help / version | missing PyYAML (import error) | unknown command | | | |
| fieldkit `delta.py` | clean | regression; malformed report traceback | coverage drop / zero files; argparse | bad input | | |
| fieldkit `onboard.py` | ok | not a directory; bad config traceback | verification failed / zero files | no somnus-debug runner | | |
| scaffolded `run_test.py` | PASS | FAIL | | | | |

## Where the transcripts are

This section points to the raw records.

- [lane D experiment-log.md](agent-findings/lane-d-cli-tests/experiment-log.md) and [experiments.jsonl](agent-findings/lane-d-cli-tests/experiments.jsonl): every command with cwd, exit, stdout/stderr.
- [lane D help-surfaces-raw.txt](agent-findings/lane-d-cli-tests/help-surfaces-raw.txt): verbatim `--help` for every surface.
- [lane B configuration-findings.md](agent-findings/lane-b-config/configuration-findings.md): 26-run config matrix.
- [lane F logs/](agent-findings/lane-f-ext/logs/): fieldkit, delta, compositions, harness runs.
- [lane A api-reference.md](agent-findings/lane-a-arch-api/api-reference.md): CLI run table and in-process `cli.main` runs.
