# Functions

This page documents the module-level functions, grouped by job. For each it gives the real signature, whether it is pure, and what it raises. Exported functions (`main`, `build_index`, `scaffold`) are covered in depth in [public-api](public-api.md); the CLI command functions (`run_*`) are in [call-chains](../07-internals/call-chains.md).

All rows below are `src/somnus_debug/doctor/core.py` unless another file is named. A pure function reads only its arguments and has no side effects. [SOURCE-CONFIRMED] for every signature (copied from source, cross-checked against [symbols.tsv](../_evidence/agent-findings/lane-a-arch-api/symbols.tsv)).

## Gate, scoring and rendering

This section covers the functions a caller most often needs after a scan.

| Function | Line | Pure | Notes |
|---|---:|---|---|
| `exit_code_for_summary(summary: SummaryCounts, gate: str) -> int` | 2046 | yes | `none` → 0. `critical` → 2 if any critical. `serious` → 2 if any critical, else 1 if any serious. `minor` → 1 if any critical, serious, or minor. `info` → 1 if any issue. Any unknown gate string → 1. The `minor` and `info` gates return 1, never 2, even when critical findings exist ([D-18](../DISCOVERY-LEDGER.md#d-18)) |
| `dumps_json(value: object, *, indent: int = 2) -> str` | 578 | yes | `json.dumps(to_json_value(value), sort_keys=True)` |
| `to_json_value(value: object) -> JsonValue` | 559 | yes | `Enum` → `.value`; `Path` → `str`; `datetime` → ISO with `Z`; dataclass → dict; mapping → dict; list, tuple, or set → list; else `str()` |
| `render_history(records: Sequence[RunRecord]) -> str` | 2034 | yes | `"No recorded runs found."` when empty |
| `table_escape(value: object) -> str` | 591 | yes | replaces newline with a space and `\|` with `\\\|`, then strips |
| `mermaid_escape(value: str) -> str` | 1690 | yes | `"` → `'`, `[` → `(`, `]` → `)` |

[VERIFIED] `/tmp/w1/ex_api.py`: `exit serious 2 critical 2 minor 1 none 0 bogus 1` on a summary with 2 critical and 13 serious findings.

## Configuration helpers

This section covers the functions behind `ConfigManager`.

| Function | Line | Pure | Raises |
|---|---:|---|---|
| `deep_merge(base: JsonObject, override: JsonObject) -> JsonObject` | 726 | yes (does not mutate) | none. Dicts merge recursively; lists and scalars replace |
| `parse_yaml_scalar(value: str, line_number: int) -> JsonValue` | 619 | yes | `ConfigurationError` on a bad quoted scalar. `none`, `null`, and `~` (any case) → `None` |
| `strip_yaml_comment(line: str) -> str` | 596 | yes | none. A `#` outside quotes starts a comment even without a preceding space |
| `require_bool(data, key) -> bool` | 737 | yes | `ConfigurationError` |
| `require_int(data, key, minimum: int) -> int` | 745 | yes | `ConfigurationError`; rejects bools |
| `require_str(data, key) -> str` | 753 | yes | `ConfigurationError`; returns the stripped value |
| `require_str_tuple(data, key) -> tuple[str, ...]` | 761 | yes | `ConfigurationError`; an empty list is valid |
| `parse_severities(raw: JsonValue) -> Mapping[str, Severity]` | 769 | yes | `ConfigurationError`. Accepts any category name; values must be lowercase |

## AST predicates

This section lists the small pure functions the detectors are built from. They are useful on their own for custom analysis.

| Function | Line | Returns |
|---|---:|---|
| `cyclomatic_complexity(node: ast.AST) -> int` | 1423 | starts at 1. Adds 1 per `If`, `For`, `AsyncFor`, `While`, `Try`, `ExceptHandler`, `IfExp`, or `Match`. Adds `len(values)-1` per `BoolOp`, and `1 + len(ifs)` per comprehension generator. Walks nested functions too |
| `body_is_stub(body: Sequence[ast.stmt]) -> bool` | 1436 | True for a single `pass`, `...`, or `raise NotImplementedError[(...)]`. Ignores decorators ([D-07](../DISCOVERY-LEDGER.md#d-07)) |
| `placeholder_return_kind(body) -> str` | 1451 | `""` or a label: `"implicit None"`, `repr` of None/False/True/0/-1/`""`, or `"empty list/dict/tuple/set"`. Note `True == 1`, so `return 1` matches ([D-07](../DISCOVERY-LEDGER.md#d-07)) |
| `handler_is_silent(node: ast.ExceptHandler) -> bool` | 1471 | True when the body is empty, a lone `pass`, a placeholder return, or a lone `print`/`logging.debug`/`logging.info` call; or when the body has no `raise` and no call named `logging.error`, `logging.exception`, `logger.error`, or `logger.exception` |
| `dotted_name(node: ast.AST \| None) -> str` | 1490 | `a.b.c` for Name/Attribute chains; follows `Call.func`; otherwise `ast.unparse` |
| `missing_type_hints(node, config: DoctorConfig) -> tuple[str, ...]` | 1407 | labels `return`, `param:x`, `vararg:x`, `kwarg:x`; skips `self` and `cls` |
| `executable_line_count(body) -> int` | 1386 | unique line numbers spanned by the statements, docstring excluded |
| `body_without_docstring(body) -> tuple[ast.stmt, ...]` | 1379 | body minus a leading string `Expr` |
| `function_argument_count(node) -> int` | 1397 | posonly + args + kwonly + vararg + kwarg |
| `meaningful_doc(node, min_length: int) -> bool` | 1374 | stripped docstring length ≥ `min_length` |
| `is_private_function(name: str) -> bool` | 1402 | starts with `_` and is not a dunder |
| `canonical_cycle(cycle: Sequence[str]) -> tuple[str, ...]` | 1682 | the lexicographically smallest rotation |
| `dedupe_issues(issues: Iterable[DiagnosticIssue]) -> list[DiagnosticIssue]` | 1361 | dedupes by `identity()`, then sorts by (file, line, severity string, category, symbol) |

```python
import ast
from somnus_debug.doctor.core import cyclomatic_complexity, body_is_stub, placeholder_return_kind, handler_is_silent
fn = ast.parse("def f(x):\n    if x and x > 1:\n        return [i for i in x if i]\n    return 1\n").body[0]
print(cyclomatic_complexity(fn), placeholder_return_kind(fn.body[1:]), body_is_stub([ast.parse("...").body[0]]))
h = ast.parse("try:\n    pass\nexcept E:\n    self.log.error('x')\n").body[0].handlers[0]
print(handler_is_silent(h))
```

Executed: yes (`/tmp/w1/ex_pred.py`, `PYTHONPATH=src`, exit 0). Output: `5 1 True` and then `True`. The score of 5 is 1 base, +1 `If`, +1 `BoolOp`, +2 for the comprehension (one generator with one `if`). `return 1` is reported as the placeholder `1`. `self.log.error` is not a recognized logging call, so the handler counts as silent ([D-07](../DISCOVERY-LEDGER.md#d-07)).

## Utilities

This section covers time, hashing and path helpers.

| Function | Line | Pure | Notes |
|---|---:|---|---|
| `utc_now() -> dt.datetime` | 525 | no (clock) | timezone-aware UTC |
| `utc_now_text() -> str` | 530 | no (clock) | `%Y%m%dT%H%M%SZ`; this is the `run_id` |
| `isoformat_utc(value: dt.datetime) -> str` | 535 | yes | treats a naive datetime as UTC; uses a `Z` suffix |
| `stable_hash_text(text: str) -> str` | 542 | yes | sha256 hex of UTF-8 |
| `stable_hash_file(path: Path) -> str` | 547 | reads file | sha256 in 1 MiB chunks; raises `FileReadError` |
| `safe_relpath(path: Path, root: Path) -> str` | 583 | reads fs (resolve) | POSIX relative path, or the absolute path when outside root |
| `write_text_atomic(path: Path, text: str) -> None` | 2012 | writes | `mkdir -p` parent, write `.<name>.tmp`, `replace`; raises `ReportGenerationError` |
| `copy_file_atomic(source: Path, destination: Path) -> None` | 2023 | writes | `shutil.copy2` to temp, then `replace`; raises `StateStoreError` |

## CLI plumbing (doctor)

This section lists the functions that exist for the command line. You can call them, but they act on `argparse.Namespace` objects.

| Function | Line | Notes |
|---|---:|---|
| `main(argv: Sequence[str] \| None = None) -> int` | 2184 | see [public-api](public-api.md#cli-entry-points-as-functions) |
| `build_parser() -> argparse.ArgumentParser` | 2130 | subcommands `scan`, `init-config`, `history`, `rollback`, `self-check` |
| `normalize_argv(argv: Sequence[str]) -> list[str]` | 2165 | `[]` → `["scan","."]`; first arg starting with `-` (not `-h`/`--help`) → `["scan",".",*argv]`; first arg not a command → `["scan",*argv]` |
| `setup_logging(verbose: bool = False) -> None` | 2179 | `basicConfig(FileHandler("production_doctor.log"), force=True)` |
| `run_scan(args)`, `run_init_config(args)`, `run_history(args)`, `run_rollback(args)`, `run_self_check(args)` | 2061-2127 | the command bodies; each returns an int exit code and raises `DoctorError` subclasses |

[VERIFIED] `/tmp/w1/ex_api.py`: `normalize ['scan', '.'] ['scan', 'proj'] ['scan', '.', '-v'] ['history']`.

## Other modules

This section lists functions outside the doctor.

| Function | Location | Notes |
|---|---|---|
| `build_index(...) -> str` | `src/somnus_debug/structure/core.py:202` | [public-api](public-api.md#structurebuild_index) |
| `structure.core.main(argv=None) -> int` | `src/somnus_debug/structure/core.py:323` | |
| `_signature`, `_doc_summary`, `_render_class`, `_iter_classes`, `_count_indexed_definitions`, … | `src/somnus_debug/structure/core.py:58-199` | private renderers. `_count_indexed_definitions` counts the scoped-nested class twice ([D-24](../DISCOVERY-LEDGER.md#d-24)) |
| `setup_logging(cfg: CleanerConfig) -> None` | `src/somnus_debug/pycache_cleaner/core.py:324` | `basicConfig` without `force`; stdout plus an optional append file |
| `parse_args() -> argparse.Namespace` | `src/somnus_debug/pycache_cleaner/core.py:337` | reads `sys.argv` |
| `pycache_cleaner.core.main() -> None` | `src/somnus_debug/pycache_cleaner/core.py:349` | |
| `scaffold(target_dir, *, force=False, with_contract=True) -> list[Path]` | `src/somnus_debug/test_harness/scaffold.py:62` | [public-api](public-api.md#scaffold) |
| `_template_text(name: str) -> str` | `src/somnus_debug/test_harness/scaffold.py:58` | `importlib.resources` read |
| `cli.main(argv=None) -> int`, `_run_subcommand(name, argv) -> int` | `src/somnus_debug/cli.py:85-125` | dispatcher |

## Sources

This section lists the code, evidence files, and probes this page rests on.

- `src/somnus_debug/doctor/core.py:525-2199` (lines per row)
- `src/somnus_debug/structure/core.py`, `src/somnus_debug/pycache_cleaner/core.py`, `src/somnus_debug/test_harness/scaffold.py`, `src/somnus_debug/cli.py`
- [lane-a symbols.tsv](../_evidence/agent-findings/lane-a-arch-api/symbols.tsv), [lane-a api-reference.md](../_evidence/agent-findings/lane-a-arch-api/api-reference.md)
- Executed probes: `/tmp/w1/ex_api.py`, `/tmp/w1/ex_pred.py`
