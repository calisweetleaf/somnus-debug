# Automation contracts

This page is the machine-facing reference for every artifact an agent or script reads or writes when it drives somnus-debug: exit codes, stdout lines, the doctor JSON report, the fieldkit baseline, `dispositions.json`, `delta.py --json`, the onboarding profile, and the harness manifest. None of these formats carries a version number except the harness manifest; treat the key sets below as observed for 0.1.0.

## Exit codes

This section is the one table to branch on. Full detail: [exit codes](../05-cli-and-tools/exit-codes.md).

| Program | 0 | 1 | 2 | 3 | 4 | 5 |
|---|---|---|---|---|---|---|
| `doctor scan` (gate `serious`, the default) | gate passed, **including zero files** | serious, no critical | any critical; **also argparse errors** | unused | config or doctor error | unclassified runtime error |
| `doctor scan` (gate `minor` or `info`) | no findings at or above the gate | **any** finding at or above the gate, criticals included | argparse errors | unused | as above | as above |
| `structure` | ok | uncaught exception, e.g. non-UTF-8 source (`UnicodeDecodeError`) | parse error, missing file, **or** argparse error | — | — | — |
| `pycache-clean` | ok, **including a missing root** | config missing, bad YAML, no roots | argparse error | — | — | — |
| `init-test-harness` | written | refused (exists) | argparse error | — | — | — |
| `run_test.py` (scaffolded) | PASS | FAIL | — | — | — | — |
| `onboard.py` | ok | usage, bad path, **or doctor config error (traceback)** | coverage failure | no usable somnus-debug | — | — |
| `delta.py` | clean | new serious/critical; **or malformed issue (traceback)** | coverage regression; **or argparse error** | bad input | — | — |
| `selftest.py` | all pass | any fail | — | no CLI | — | — |

Bold cells are overloads an agent must disambiguate by reading stderr ([D-18](../DISCOVERY-LEDGER.md#d-18), [D-20](../DISCOVERY-LEDGER.md#d-20), [D-21](../DISCOVERY-LEDGER.md#d-21)). Sources: [lane-d exit codes](../_evidence/agent-findings/lane-d-cli-tests/exit-codes.md) [VERIFIED]; overloads for `delta.py` re-run in this wave [VERIFIED, [stage 6 log](../09-recipes/_repro/logs/stage6_integrations.log)].

## stdout lines worth parsing

This section lists the stable-looking lines tools print.

| Line | Printed by | Notes |
|---|---|---|
| `Scan complete: files=N, issues=N, critical=N, serious=N` | every completed doctor scan | `onboard.py` parses it with `files=(\d+), issues=(\d+), critical=(\d+), serious=(\d+)` and raises if it is missing (`skills/somnus-debug-fieldkit/scripts/onboard.py:88`, `:403-405`) |
| `Markdown report: <path>` / `JSON report: <path>` | doctor scan | absolute paths |
| `Run ID: <YYYYmmddTHHMMSSZ>` | stateful scans only | per-second, not unique ([D-08](../DISCOVERY-LEDGER.md#d-08)) |
| `Doctor failure: <message>` + `Remediation:` + `Context:` JSON | doctor, on stderr, exit 4 | the `Remediation` line can be the class default rather than the specific hint ([lane-a API reference, Errors](../_evidence/agent-findings/lane-a-arch-api/api-reference.md)) |
| Final JSON object `{run_id, test_name, verdict, elapsed_s, artifacts{manifest,report,log}}` | `run_test.py`, on stdout | progress goes to stderr |

[VERIFIED, [stage logs](../09-recipes/_repro/README.md)]

## Doctor JSON report

This section is the report written by `--json-output` (and by `dumps_json` in-process, which produced an identical report in this wave apart from run ID and timestamps).

Key sets observed in this wave [VERIFIED, [stage 6b log](../09-recipes/_repro/logs/stage6b_contract_keys.log)]:

```text
top-level   config_hash, dependency_graph, files, finished_at, issues, project_root, run_id, started_at, state_delta, summary
summary     critical_issues, dependency_cycles, files_scanned, info_issues, minor_issues, missing_imports, production_score,
            serious_issues, suspicious_short_classes, suspicious_short_functions, syntax_error_files, total_issues
issues[]    category, column_offset, details, evidence, file_path, line_number, message, remediation, severity, symbol
files[]     classes, code_map, file_hash (sha256), file_path, functions, import_edges, imports, issues, metrics,
            modified_time, relative_path, size_bytes, syntax_valid
  functions[]  argument_count, cyclomatic_complexity, decorators, end_line_number, executable_line_count, has_docstring,
               kind, line_number, missing_type_hints, qualname, return_count, statement_count
  classes[]    bases, decorators, end_line_number, executable_line_count, has_docstring, is_dataclass, is_enum,
               is_exception, line_number, method_count, public_method_count, qualname
  metrics      blank_lines, code_lines, comment_lines, documented_symbols, fully_type_hinted_functions, import_count,
               local_dependency_count, max_cyclomatic_complexity, missing_import_count, total_classes, total_functions,
               total_lines, total_methods
  code_map     classes, docstring_present, functions, imports, module
dependency_graph  cycles, edges, mermaid, missing_imports, nodes
  edges[]      classification (local|standard_library|third_party|missing|unresolved_relative), confidence, imported_module,
               line_number, raw, source_file, status, target_file
state_delta  new_files, modified_files, deleted_files, unchanged_files
```

Semantics an agent needs:

- `issues[].file_path` and `files[].relative_path` are POSIX paths relative to `project_root`.
- `issues[].symbol` is the enclosing qualname, or `<module>` for module-level code and anything inside a private function ([experimental-extensions](../08-extensions/experimental-extensions.md)).
- `files[].functions[]` and `classes[]` give a project-wide definition index with line spans; no `structure` call is needed ([findings-to-source-slices](../09-recipes/advanced/findings-to-source-slices.md)).
- `state_delta` is against the previous **stateful** run's file hashes, which a rollback changes ([history-and-rollback](../09-recipes/automation/history-and-rollback.md)).
- `started_at`/`finished_at` were localized strings in this sandbox, not ISO-8601 [CONDITIONAL, [lane-f fieldkit, sandbox caveat](../_evidence/agent-findings/lane-f-ext/fieldkit.md)]. Do not parse them; use `run_id`.

## Fieldkit baseline

This section defines "baseline" precisely.

A baseline is a doctor JSON report kept at `.somnus-debug/runs/baseline.json` (plus its `.md`). There is no separate baseline format [SOURCE-CONFIRMED, `skills/somnus-debug-fieldkit/scripts/onboard.py:518-520`]. Any doctor JSON report works as a baseline, including doctor's own `state/reports/<run_id>/production_doctor_report.json` and `state/reports/latest.json` [VERIFIED, [stage 5b log](../09-recipes/_repro/logs/stage5b_state_reports.log)]. `delta.py` needs only `issues[].{category, file_path, symbol?, message?, severity?, line_number?}`, `summary`, `files[].relative_path`, and optionally `project_root` and `run_id` (`skills/somnus-debug-fieldkit/scripts/delta.py:110-126`) [SOURCE-CONFIRMED].

## `dispositions.json`

This section is the input format for accepted findings.

```json
[
  {"category": "silent_failures", "file": "src/inventory/store.py", "symbol": "safe_level",
   "reason": "Missing SKU means zero stock by design; KeyError is the expected path, not a failure."}
]
```

| Field | Required | Match |
|---|---|---|
| `category` | yes, non-empty string | exact |
| `file` | yes, non-empty string | `fnmatchcase` against `issues[].file_path` |
| `symbol` | no (default `*`) | `fnmatchcase` against `issues[].symbol` |
| `reason` | yes, non-empty string | not matched; for humans |

A non-list file, or any entry missing a required field, is exit 3. A missing file is a stderr note and the run continues without dispositions. Each entry is checked against every latest finding; first match wins; entries that matched nothing are returned as `stale_dispositions` (`skills/somnus-debug-fieldkit/scripts/delta.py:88-103`, `:129-144`, `:159-191`) [SOURCE-CONFIRMED; exit 3 and missing-file note VERIFIED in this wave].

## `delta.py --json`

This section is the verdict object.

```text
{ baseline: <summary>, latest: <summary>, baseline_run: str, latest_run: str,
  persisting: int, dispositioned: int,
  new: [{severity, category, file, line, symbol, message}],          # new and not dispositioned, any severity
  resolved: [...same shape...],
  regressions: [...same shape...],                                    # subset of new with severity critical|serious
  stale_dispositions: [{category, file, symbol, reason}],
  uncovered_files: [path], deleted_files: [path], added_files: [path],
  coverage_failure: bool, exit: 0|1|2 }
```

Identity is `(category, file, symbol, message)`, no line number; `new` and `resolved` are multiset differences, so duplicates count (`:82-85`, `:147-156`). `exit` in the object equals the process exit code. `coverage_failure` is true when latest scanned 0 files or a baseline file is missing from latest while it still exists on disk under `--root` (default: latest `project_root`) [SOURCE-CONFIRMED; key set VERIFIED, [stage 6b log](../09-recipes/_repro/logs/stage6b_contract_keys.log)].

What the object does **not** contain: either report's `config_hash`, and any statement that both scans used the same config ([D-21](../DISCOVERY-LEDGER.md#d-21)). Compare `config_hash` yourself from the two reports if it matters.

## Onboarding profile (`.somnus-debug/`)

This section lists the files `onboard.py --apply --baseline` creates and who may change them.

| File | Tracked in git | Written by | Agent may edit? |
|---|---|---|---|
| `python_doctor.yaml` | yes | onboard (generated from `init-config`), never overwritten | Only with a recorded reason; coverage edits then rerun plan mode |
| `dispositions.json` | yes | onboard (`[]`) | Yes, narrow entries with reasons |
| `pycache.yaml` | yes | onboard (absolute root, name excludes, `dry_run: true`) | No live run without authorization |
| `PROFILE.md` | yes | onboard | Regenerate by deleting and re-running onboard |
| `.gitignore` | yes | onboard (`state/`, `runs/`, `*.log`) | No |
| `runs/baseline.{md,json}`, `runs/latest.*` | no | scans with `-o` | Baseline only through a ratchet |
| `state/` (SQLite + per-run reports) | no | stateful scans | No |
| `production_doctor.log` | no | every doctor call from this cwd | No |

[VERIFIED, [onboard-a-repo](../09-recipes/intermediate/onboard-a-repo.md); policy column from `skills/somnus-debug-fieldkit/references/onboarding.md` and `SKILL.md:103-111`]

## Harness `manifest.json` (schema 1.0)

This section is the only versioned format in the toolchain.

```text
{ schema_version: "1.0", run_id, test_name, verdict: "PASS"|"FAIL", started_at_utc, finished_at_utc, elapsed_s,
  environment: {cwd, platform, project_root, python, python_executable, runner},
  acceptance: {total_checks, passed_checks, failed_checks, checks: [{name, passed, detail, expected, observed}]},
  result: {summary, metrics, evidence, notes},
  error: null | {type, message, traceback},
  artifacts: {manifest: "manifest.json", report: "report.md", log: "test.log"} }
```

`verdict` is PASS only if `checks` is non-empty and every check passed; process exit is 0 for PASS, 1 for FAIL (`src/somnus_debug/test_harness/templates/run_test.py:596-645`, `:855`) [VERIFIED, key sets in [stage 6b log](../09-recipes/_repro/logs/stage6b_contract_keys.log)].

## Sources

This section lists the files, logs and evidence this page rests on.

- [stage 6b log](../09-recipes/_repro/logs/stage6b_contract_keys.log), [stage 5b log](../09-recipes/_repro/logs/stage5b_state_reports.log), [stage 6 log](../09-recipes/_repro/logs/stage6_integrations.log)
- [lane-f fieldkit §3](../_evidence/agent-findings/lane-f-ext/fieldkit.md), [lane-f harness §2](../_evidence/agent-findings/lane-f-ext/harness.md), [lane-d exit codes](../_evidence/agent-findings/lane-d-cli-tests/exit-codes.md), [lane-a API reference](../_evidence/agent-findings/lane-a-arch-api/api-reference.md)
- `skills/somnus-debug-fieldkit/scripts/delta.py`, `skills/somnus-debug-fieldkit/scripts/onboard.py:88`, `:403-405`, `:518-520`
- `src/somnus_debug/test_harness/templates/run_test.py:596-645`, `:855`
