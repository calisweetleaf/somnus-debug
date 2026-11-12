# Fallbacks

This page lists every place where the code substitutes a default or degraded behavior instead of failing. For each one it gives the trigger and the substitute behavior, and says whether the user is told. Fallbacks that happen silently are the most important to know about.

## Doctor fallbacks

This section lists the doctor's degraded paths, ordered from most to least consequential.

| Fallback | Trigger | Substitute behavior | User told? | Evidence |
|---|---|---|---|---|
| Stateless scan | `StateStoreError` while opening state (unwritable dir, a file named `.python_doctor`, corrupt DB) | skip history; write only the two reports; exit by gate | yes: one stderr warning line | [VERIFIED] [D-28](../DISCOVERY-LEDGER.md#d-28); `src/somnus_debug/doctor/core.py:2068-2077` |
| Missing root created | state enabled, root path missing but writable | `mkdir(parents=True)` creates it; a 0-file scan passes the gate | **no** | [VERIFIED] `/tmp/w1` `scan ghost/root` exit 0; see [initialization](initialization.md#doctor-startup-sequence) |
| Per-file error issue | read or decode failure | `analysis_read_errors` issue; the file is excluded from the delta | yes, as a critical finding | [SOURCE-CONFIRMED] `:1524-1525`, `:1583-1586` |
| Partial file result | `SyntaxError`/`ValueError` from `ast.parse` | token-level findings plus `syntax_errors`; no AST, import, or graph data | yes, as a critical finding | [VERIFIED] `/tmp/w1/ex_api.py` (`broken.py`) |
| Worker error issue | exception in a thread worker | `analysis_read_errors` with symbol `<analysis>` | yes, as a critical finding | [VERIFIED] `/tmp/w1/ex_serial.py` (threaded case) |
| Default config | no `-c` | `DEFAULT_CONFIG_DATA`, even if `python_doctor.yaml` exists | **no** | [VERIFIED] [D-02](../DISCOVERY-LEDGER.md#d-02) |
| Key-by-key defaults | a key is absent or misspelled in the config file | the default value for that key | **no** | [VERIFIED] [D-04](../DISCOVERY-LEDGER.md#d-04) |
| Severity default | category not in `severity_levels` | `Severity.MINOR` | **no** | [SOURCE-CONFIRMED] `:792-794`; [VERIFIED] `cm.severity("unknown_cat")` gives `Severity.MINOR` in `/tmp/w1/ex_api.py` |
| Unknown gate | `exit_code_for_summary` called with an unrecognized gate | returns 1 | n/a (the CLI validates the gate first) | [VERIFIED] `bogus` gives 1 in `/tmp/w1/ex_api.py` |
| Missing import | `find_spec` raises | classified `missing` | as a finding, without the cause | [SOURCE-CONFIRMED] `:1050-1055` |
| Absolute "relative" path | file resolves outside the root (symlink) | `safe_relpath` returns the absolute POSIX path | **no** | [SOURCE-CONFIRMED] `:583-588` |
| `<module>` symbol | issue inside a skipped private function at module level, or at module scope | symbol `<module>` or the enclosing class | **no** | [VERIFIED] [lane-f extensions](../_evidence/agent-findings/lane-f-ext/extensions.md) |
| Empty evidence | issue with line ≤ 0, or an empty file | `evidence = ""`; Markdown prints "No source evidence available." | n/a | [SOURCE-CONFIRMED] `:1083-1090`, `:1899` |
| `dotted_name` | unparseable node | `""` | n/a | [SOURCE-CONFIRMED] `:1501-1504` |

## Root-duplicate parity

This section records that one doctor fallback exists in `src/` but not in the older root script. This was reconciled in the lead's brief.

`python_production_doctor.py` at the repository root lacks the stateless fallback. When state cannot open, it raises, and the scan exits 4 instead of degrading. The packaged doctor in `src/` and the PyPI 0.1.0 code both have the fallback. [VERIFIED] [lane-a architecture §7](../_evidence/agent-findings/lane-a-arch-api/architecture.md), [lane-d install-vs-source §4](../_evidence/agent-findings/lane-d-cli-tests/install-vs-source.md), [D-28](../DISCOVERY-LEDGER.md#d-28). The fallback covers `scan` only. `history` and `rollback` still exit 4. The smoke test `test_doctor_scan_degrades_when_sqlite_state_is_unavailable` (`tests/test_cli_smoke.py:88`) covers the scan case and passes. [VERIFIED] lead's reconciled test result: 10 of 12 pass, and both failures are the structure type-comment tests.

## structure fallbacks

This section covers the indexer's two small fallbacks.

- `_unparse` falls back to `ast.dump` on `AttributeError`, which only happens on Python versions older than 3.9. [SOURCE-CONFIRMED] `src/somnus_debug/structure/core.py:75-80`.
- A class with no docstring renders as `_No class docstring._`, a class with no methods as `- _No methods._`, and an empty module as `_No classes found._`. [VERIFIED] `/tmp/w1/ex_misc.py`.

There is no fallback for the type-comment failure. The root `analyze_python_structure.py` parses without `type_comments`, and that is the only working variant ([D-01](../DISCOVERY-LEDGER.md#d-01)).

## pycache-clean fallbacks

This section lists the cleaner's substitutions, several of which hide failures.

| Fallback | Trigger | Behavior | User told? |
|---|---|---|---|
| Skip root | root missing or not a directory | logged ERROR, continue, exit 0 | ERROR line only |
| Skip directory | `PermissionError` on scandir | WARNING | yes |
| Size 0 | size computation fails | counts 0 bytes | no |
| No file logging | `log_file` cannot be opened | stderr note, console logging only | yes |
| Logging silenced | an unknown config key triggers a pre-setup `logging.warning` | root configured at WARNING; INFO summary lost | **no** ([D-14](../DISCOVERY-LEDGER.md#d-14)) |
| `{}` config | YAML file empty or `null` | all dataclass defaults (then `ValueError` for missing roots) | via the error |

[SOURCE-CONFIRMED] `src/somnus_debug/pycache_cleaner/core.py:173`, `:211-213`, `:226-231`, `:276-279`, `:329-333`. [VERIFIED] logging silenced: [lane-b §1 item 8](../_evidence/agent-findings/lane-b-config/configuration-findings.md).

## Template fallbacks (scaffolded run_test.py)

This section covers the environment-variable defaults in the harness template.

`PROJECT_ROOT` falls back to `Path(__file__).resolve().parent.parent`, and an empty value means the cwd. `SINGLE_TEST_OUTPUT_DIR` falls back to `<project_root>/test-runs`, and an empty value means that same default. [VERIFIED] [lane-b §2.5](../_evidence/agent-findings/lane-b-config/configuration-findings.md); [SOURCE-CONFIRMED] `src/somnus_debug/test_harness/templates/run_test.py:747-750`, `:589-593`.

## Sources

This section lists the code, evidence files, and probes this page rests on.

- `src/somnus_debug/doctor/core.py:583-588`, `:792-794`, `:1050-1055`, `:1083-1090`, `:1501-1504`, `:1520-1586`, `:1726-1738`, `:1899`, `:2046-2058`, `:2068-2077`
- `src/somnus_debug/structure/core.py:75-80`, `src/somnus_debug/pycache_cleaner/core.py:170-334`, `src/somnus_debug/test_harness/templates/run_test.py:589-593`, `:747-750`; `tests/test_cli_smoke.py:88`
- [lane-a architecture.md](../_evidence/agent-findings/lane-a-arch-api/architecture.md), [lane-b configuration-findings.md](../_evidence/agent-findings/lane-b-config/configuration-findings.md), [lane-d install-vs-source.md](../_evidence/agent-findings/lane-d-cli-tests/install-vs-source.md), [lane-f extensions.md](../_evidence/agent-findings/lane-f-ext/extensions.md)
- Executed probes: `/tmp/w1/ex_api.py`, `/tmp/w1/ex_serial.py`, `/tmp/w1/ex_misc.py`, `/tmp/w1` `scan ghost/root`
