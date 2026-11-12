# Recipe: index a metadata-stamped file with `build_index`

**Tier:** small integration step (a workaround for [D-01](../../DISCOVERY-LEDGER.md#d-01)). **Script:** [index_any.py](../_repro/index_any.py).

Get a `structure` index for files that start with a `# somnus:metadata:v2` header, which the shipped `structure` command and `build_index()` both refuse to parse.

## When to use

This section explains the defect the recipe routes around.

`structure` and `somnus_debug.structure.build_index` call `ast.parse(source, type_comments=True)` (`src/somnus_debug/structure/core.py:210`). A header line like `#     type: "source-code"` is then read as a type comment and raises `SyntaxError`. Every file in this repo carries such a header, as do files stamped by the same tooling elsewhere [VERIFIED, [lane-a API reference §2](../../_evidence/agent-findings/lane-a-arch-api/api-reference.md)]. The fix exists only in the repo-root duplicate `analyze_python_structure.py`. Until the package is fixed, blank the header before indexing.

## The code

This section is the full script. Replacing each header line with an empty line keeps every line number unchanged, so the spans in the index still point at the real file.

```python
import sys
from pathlib import Path

from somnus_debug.structure import build_index   # exported: structure.__all__ == ["build_index", "main"]

path = Path(sys.argv[1])
lines = path.read_text(encoding="utf-8").splitlines(keepends=True)
try:
    build_index("".join(lines), source_name=path.name)
    print("plain build_index: ok")
except SyntaxError as error:
    print(f"plain build_index: SyntaxError: {error}")
if lines and lines[0].startswith("# somnus:metadata"):
    end = next(i for i, line in enumerate(lines) if line.startswith("# somnus:end"))
    lines[: end + 1] = ["\n"] * (end + 1)
print("\n".join(build_index("".join(lines), source_name=path.name).splitlines()[:14]))
```

## Executed result

This section shows the crash, the workaround, and a line-number check against the real file.

Executed: yes (`/tmp/w4/p`, a copy of `src/somnus_debug/test_harness/scaffold.py`; [stage 4 log](../_repro/logs/stage4_programmatic.log), section P2)

```text
$ python index_any.py stamped_scaffold.py
plain build_index: SyntaxError: invalid syntax (stamped_scaffold.py, line 9)
# Class Index for `stamped_scaffold.py`
- Class declarations: 0 (0 top-level, 0 nested)
- Definitions emitted (module-level functions and class methods): 4
## Module-level functions
- `def _template_text(name: str) -> str:` (lines 58-59)
- `def scaffold(target_dir: Path, *, force: bool=False, with_contract: bool=True) -> list[Path]:` (lines 62-88)
  - Copy the test-harness template into ``target_dir``.                     [exit=0]
$ grep -n '^def scaffold' stamped_scaffold.py
62:def scaffold(target_dir: Path, *, force: bool = False, with_contract: bool = True) -> list[Path]:
```

The index places `scaffold` at line 62, where the file has it [VERIFIED].

## Pitfalls

This section lists the limits.

- Only the metadata block is neutralized. A real `# type:` comment that is not PEP 484 syntax elsewhere in the file (for example `x = [  # type: List[int]` split across lines) still fails [VERIFIED by lane A, ex4].
- The script assumes the header starts on line 1 and ends with `# somnus:end`, which is how the stamped files in this repo look (`src/somnus_debug/__init__.py:1-32`) [SOURCE-CONFIRMED].
- The CLI `structure` command cannot take this path; use `build_index` or pre-process the file into a temp copy.

## Sources

This section lists the files, logs and evidence this page rests on.

- [stage 4 log](../_repro/logs/stage4_programmatic.log), [index_any.py](../_repro/index_any.py)
- [lane-a API reference §2](../../_evidence/agent-findings/lane-a-arch-api/api-reference.md), [lane-d README item 1](../../_evidence/agent-findings/lane-d-cli-tests/README.md)
- `src/somnus_debug/structure/core.py:202-210`
