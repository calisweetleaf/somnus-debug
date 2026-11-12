# Implementation notes

This page collects implementation details that do not belong to a single chain or state machine but explain observed behavior. It also records the places where the evidence lanes disagreed, and how each disagreement was settled against the source.

## Lane disagreements resolved

This section records each conflict between evidence lanes, the decision, and the check that settled it.

| Topic | Lane claims | Resolution | How decided |
|---|---|---|---|
| Line of the `is_dataclass` test | lane A: `core.py:1186`; lane F: `:1192` | **`src/somnus_debug/doctor/core.py:1192`** | `grep -n "is_dataclass=any"` [VERIFIED] |
| Malformed YAML config | lane A: malformed input raises `ConfigurationError` (exit 4); lane D, D30: `schema_version: [` "silently accepted, defaults used" | Both are partly right. `[` with no closing `]` is not a list token, so `parse_yaml_scalar` returns the **string `'['`**. That passes `require_str`, and `schema_version` is never compared. So this one input is accepted with a garbage value, not with the default. Structural malformations (bad indentation, a missing child block, mixed containers) do raise | [VERIFIED] `/tmp/w1/ex_misc.py`: `schema_version parsed as '['`; source `:619-643` |
| RecursionError "aborts the whole scan" | lane D, D44 | **Only on the serial path.** D44's project had one file. With a second file, the same input becomes one `analysis_read_errors` finding and the scan exits 2 | [VERIFIED] `/tmp/w1/rec1` (exit 5) vs `/tmp/w1/rec2` (exit 2) |
| `doctor scan <missing path>` exits 4 | lane A (`/nonexistent`) | **Only when the path cannot be created, or with `--no-state`.** A writable missing path is created by state initialization and scanned as empty, exit 0 | [VERIFIED] `/tmp/w1` `scan ghost/root` exit 0; `--no-state` exit 4 |
| `-v` vs `--verbose` | lanes A and B | lead reconciliation adopted: `-v` is ignored; `--verbose` sets DEBUG with no visible effect | [SOURCE-CONFIRMED] `:2186`, `:2140`; [VERIFIED] [lane-a §3.0](../_evidence/agent-findings/lane-a-arch-api/architecture.md) |
| Smoke-test outcome for structure | lane A inferred failure; lead measured | **2 of 12 fail** (`test_structure_tolerates_type_like_comments`, `test_structure_self_index`) | lead result in `WRITING-BRIEF.md`; source `src/somnus_debug/structure/core.py:210` |

## Doctor quirks that explain output

This section lists small implementation choices that produce surprising results.

- **Scope attribution.** When `check_private_functions` is false, a private function is visited for its body but not pushed onto `scope_stack`. Findings inside it are attributed to the enclosing class or to `<module>`. [SOURCE-CONFIRMED] `src/somnus_debug/doctor/core.py:1239-1241`; [VERIFIED] [lane-a §3.3](../_evidence/agent-findings/lane-a-arch-api/architecture.md).
- **Nested-function check heuristic.** `_inside_function` is true only when the most recently recorded function's qualname equals the current scope. Private functions are never recorded and never pushed onto the scope stack, so a function nested inside a private function is not seen as nested. `check_nested_functions: false` therefore does not skip it, and its symbol loses the parent prefix. [SOURCE-CONFIRMED] `:1356-1358`, `:1233-1241`. [VERIFIED] `/tmp/w1/ex_nest.py`, using a module with `outer()` containing `first()` and `second()`, and `_private()` containing `inner()`, each calling `eval`:

  | Config | `security_risks` reported at |
  |---|---|
  | defaults | 7 (`outer.first`), 9 (`outer.second`), 17 (`inner`) |
  | `check_nested_functions: false` | 17 (`inner`) only |

  So the switch hides nested functions under public parents but not under private ones. Both behaviors are surprising: one hides findings ([D-16](../DISCOVERY-LEDGER.md#d-16)), and the other silently ignores the setting.
- **Executable lines include nested definitions.** `executable_line_count` counts every line spanned by top-level statements in the body, so a short function that contains a long nested function is not "short". [SOURCE-CONFIRMED] `:1386-1394`.
- **`return 1` is a placeholder.** `value.value in PLACEHOLDER_CONSTANTS` uses `==`, and `True == 1`. [VERIFIED] `/tmp/w1/ex_pred.py` (`placeholder_return_kind` returns `1`); [D-07](../DISCOVERY-LEDGER.md#d-07).
- **Within-file sort uses the severity string.** On one line the order is critical, info, minor, serious. [SOURCE-CONFIRMED] `:1371`.
- **Issues appear twice in JSON.** They are listed top-level and per file. [SOURCE-CONFIRMED] `:1712-1714`.
- **Duplicate checks run per scope, twice.** `_check_duplicates` runs at the end of every class and function visit, and again at module end through `analyze`. It clears the scope after reporting, so nothing is double-counted. [SOURCE-CONFIRMED] `:1315-1322`, `:1163`.
- **`is_exception` heuristic.** A base whose name ends with `Error` or `Exception`, or a class name ending in `Error`, exempts the class from the short-class check. [SOURCE-CONFIRMED] `:1193`.
- **`incomplete_methods` matching.** A base is matched to a same-file abstract class by its last dotted component, so classes with the same name in different scopes can collide. [SOURCE-CONFIRMED] `:1324-1336`.
- **Markdown contains HTML and CSS.** `SOMNUS_MARKDOWN_STYLE` and a `<div class="t">` terminal block are emitted unless `markdown_include_css: false`, but the terminal block is emitted regardless (`:1804-1820`). GitHub strips `<style>`, so the block renders as plain text there. [SOURCE-CONFIRMED]; GitHub behavior [HYPOTHESIS].
- **Self-check scope.** It scans only `Path(__file__).parent`, which is `doctor/` with 2 files, not the whole package. [SOURCE-CONFIRMED] `:2125`; [VERIFIED] [lane-a §3.6](../_evidence/agent-findings/lane-a-arch-api/architecture.md).

## structure notes

This section records the indexer's implementation details.

- **Type comments.** `type_comments=True` (`src/somnus_debug/structure/core.py:210`) is the only difference from the root script. The flag makes `ast.parse` validate any comment matching `# type:` in positions where type comments are allowed. Header lines such as `#     type: "source-code"` are then rejected as invalid syntax. [VERIFIED] `/tmp/w1/ex_misc.py`: `'#     type: "source-code"\nx = 1\n'` raises SyntaxError at line 1. [D-01](../DISCOVERY-LEDGER.md#d-01).
- **Signatures are rebuilt from AST fields, not sliced from text.** This keeps annotations such as `Dict[str, Any]` intact. [SOURCE-CONFIRMED] `:83-91` (comment at `:85-87`).
- **Duplicate class names get occurrence labels.** For example, `(occurrence 1/2)`. [SOURCE-CONFIRMED] `:218-225`.

## pycache-clean notes

This section records where the cleaner's docstring and its code disagree.

| Docstring claim | Code | Evidence |
|---|---|---|
| "Windows long path support: paths are normalized to the `\\?\` namespace" | no such code | [SOURCE-CONFIRMED] grep; [lane-a §5](../_evidence/agent-findings/lane-a-arch-api/architecture.md) |
| "Environment variables and `~` are expanded" | only `~` (`expanduser`) | [VERIFIED] [lane-b §2.3](../_evidence/agent-findings/lane-b-config/configuration-findings.md) |
| "default config.yaml in the same directory" | `config.yaml` in the cwd | [SOURCE-CONFIRMED] `src/somnus_debug/pycache_cleaner/core.py:340`, `:351` |
| exclude "glob patterns" for directories | basename-only `fnmatchcase` | [VERIFIED] [D-14](../DISCOVERY-LEDGER.md#d-14) |

The docstring's `\\?\`` sequence also triggers the `SyntaxWarning: invalid escape sequence '\`'` at compile time (`:64`). [VERIFIED] seen in `/tmp/w1` runs from source.

## Packaging notes

This section records implementation facts about how the code is laid out and shipped.

- **Metadata header in every source file.** Every `.py` file starts with a `# somnus:metadata:v2 … # somnus:end` comment block, so line numbers in `src/` are offset by about 30 to 50 lines compared with the PyPI build, which differs only in headers. [VERIFIED] [lane-d install-vs-source](../_evidence/agent-findings/lane-d-cli-tests/install-vs-source.md). Cite `src/` lines only against this baseline.
- **Version hard-coded twice.** `src/somnus_debug/__init__.py:57` and `pyproject.toml` both say `0.1.0` and are not linked. [SOURCE-CONFIRMED] [D-23](../DISCOVERY-LEDGER.md#d-23).
- **`test_harness/__init__.py` is header-only.** `scaffold` must be imported from its module. [VERIFIED] [lane-a api-reference §0](../_evidence/agent-findings/lane-a-arch-api/api-reference.md).
- **Root duplicates.** These pre-packaging scripts are not imported by anything. See [architecture](../01-system/architecture.md#root-level-duplicates).

## Sources

This section lists the code, evidence files, and probes this page rests on.

- `src/somnus_debug/doctor/core.py:619-643`, `:1163`, `:1192-1193`, `:1233-1241`, `:1315-1358`, `:1371`, `:1386-1394`, `:1712-1714`, `:1804-1820`, `:2125`, `:2140`, `:2186`
- `src/somnus_debug/structure/core.py:83-91`, `:210`, `:218-225`; `src/somnus_debug/pycache_cleaner/core.py:34-138`, `:340-351`
- [lane-a architecture.md](../_evidence/agent-findings/lane-a-arch-api/architecture.md), [lane-b configuration-findings.md](../_evidence/agent-findings/lane-b-config/configuration-findings.md), [lane-d experiment-log.md](../_evidence/agent-findings/lane-d-cli-tests/experiment-log.md), [lane-d install-vs-source.md](../_evidence/agent-findings/lane-d-cli-tests/install-vs-source.md), [lane-f extensions.md](../_evidence/agent-findings/lane-f-ext/extensions.md)
- Executed probes: `/tmp/w1/ex_misc.py`, `/tmp/w1/ex_pred.py`, `/tmp/w1/ex_nest.py`, `/tmp/w1/rec1`, `/tmp/w1/rec2`, `/tmp/w1` `scan ghost/root`
