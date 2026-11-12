# Lane D: exit codes per command

Every entry below is VERIFIED from at least one run (experiment ID in brackets; details in `experiment-log.md`) unless marked SOURCE-CONFIRMED. All runs used the installed 0.1.0 venv in `/tmp/lane-d`.

## Dispatcher `somnus-debug`

| Condition | Exit | Evidence |
|---|---|---|
| no args / `-h` / `--help` / `-V` / `--version` | 0 | help capture |
| unknown command | 2 (help printed on stderr) | C01 |
| subcommand result | passed through. `SystemExit(int)` → that int, `SystemExit(non-int)` → 1 (`cli.py:100-101`) | all |
| uncaught exception in a subcommand (e.g. pycache-clean bad YAML) | 1 (Python traceback, not caught by the dispatcher) | P06, P07 |
| PyYAML missing in the interpreter (any subcommand, incl. doctor) | 1 (ImportError traceback) | F02b |

## `doctor` (`doctor/core.py:main`, `:2184-2199`)

| Condition | Exit | Evidence |
|---|---|---|
| scan passes gate (incl. **zero files scanned**) | 0 | D05a, D17, D38 |
| gate `serious` (default): serious, no critical | 1 | D03, D14 |
| gate `serious`: any critical | 2 | D01, D02 |
| gate `critical`: critical present | 2; serious-only → 0 | D26_critical, SOURCE `:2050-2051` |
| gate `none` | 0 always | D26_none, D28, D31 |
| gate `minor` / `info` with findings | **1, even when critical findings exist** | D26_minor, D26_info |
| argparse error (unknown flag, bad `--limit`, missing `--run-id`, `doctor --version`) | 2 | D11, D19, D20, D42, C02 |
| DoctorError: missing / non-dir project root, missing config, malformed JSON config, non-bool value, bad `severity_exit_level`, init-config target exists, unknown run-id, unopenable state DB for history/rollback, unwritable output | 4 | D10, D16, D18, D21, D23, D26_bogus, D33, D34, D40, D41, D43 |
| unclassified runtime (`OSError/RuntimeError/TypeError/ValueError/sqlite3.Error`), e.g. RecursionError on a pathological file aborting the whole scan | 5 | D44 |
| scan with unopenable state DB | gate result (degrades with a stderr warning, not 4) | D39 |
| malformed YAML config | **not detected**: proceeds with defaults → gate result | D30 |
| `history` / `rollback` / `init-config` success | 0 | D07–D09, D22, D24, D25 |
| `self-check` (on the installed doctor dir) | 1 (17 serious on itself) | D14, D15 |

Note: 3 is unused by doctor. MANUAL §3.4 says only "0 / non-zero". The fieldkit `references/commands.md:78` documents 0/1/2/4/5 accurately, apart from the minor/info nuance it already mentions.

## `structure` (`structure/core.py:main`, `:323-347`)

| Condition | Exit | Evidence |
|---|---|---|
| success (stdout or `-o` / `--update-doc`) | 0 | S04, S09–S12 |
| missing file, directory as source, syntax error, **stamped metadata header (type_comments crash)** | 2 (`error: …` on stderr) | S01–S03, S05, S07, S14, S15, S17 |
| output write OSError | 2 | SOURCE `:343-346` |
| argparse error (missing source, `-o` with `--update-doc`, unknown flag) | 2 | S13, S16, C03 |

Runtime errors and usage errors share code 2, so callers cannot tell them apart.

## `pycache-clean` (`pycache_cleaner/core.py:main`, `:349-372`)

| Condition | Exit | Evidence |
|---|---|---|
| success, dry-run or real | 0 | P01–P03, P09 |
| configured root missing (logged ERROR) | **0** | P01, P03 |
| config file not found | 1 | P04 |
| `roots: []` / any exception inside `PycacheCleaner` | 1 (traceback logged to stdout) | P05 |
| malformed YAML / top-level non-mapping | 1 (uncaught traceback on stderr) | P06, P07 |
| argparse error (`--max-depth x`, unknown flag) | 2 | P08, P10 |

## `init-test-harness` (`test_harness/scaffold.py:main`, `:112-125`)

| Condition | Exit | Evidence |
|---|---|---|
| files written | 0 | H01, H03, H04 |
| destination exists without `--force`; target path is an existing file | 1 | H02, H05, H07 |
| argparse error | 2 | H06 |

## Scaffolded `run_test.py`

| Condition | Exit | Evidence |
|---|---|---|
| verdict PASS | 0 | H10 |
| verdict FAIL (incl. the default cargo test without cargo; `--help` is ignored) | 1 | H08, H09 |

## Fieldkit scripts

| Script | 0 | 1 | 2 | 3 |
|---|---|---|---|---|
| `selftest.py` | all pass (F01) | any fail (F02, F02c) | — | CLI unavailable (F03) |
| `onboard.py` | ok (O01–O03) | usage / bad repo path (O06) | coverage failure, e.g. zero files (O04, O08) | CLI unavailable (O05, O07) |
| `delta.py` | clean (T01, T03) | new serious/critical (T02) | coverage regression (T04, T05) | input error (T06–T08) |
