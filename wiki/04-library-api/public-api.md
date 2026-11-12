# Public API

This page documents the exported names and the six classes and functions that README and MANUAL §8 name as library entry points. For each one it gives the real signature from source, the return structure, side effects, failure modes, and an executed example. Everything else is internal; see [internal-interfaces](internal-interfaces.md).

## Doctor scan without side effects

This section covers the recommended way to run the doctor from Python: `ConfigManager` plus `ProjectScanner`, with no CLI.

```python
class ConfigManager:
    def __init__(self, config_path: Path | None) -> None
    config: DoctorConfig
    raw_config: dict          # merged JSON-safe mapping
    config_hash: str          # sha256 hex of dumps_json(raw_config)
    config_path: Path | None
    def severity(self, category: str) -> Severity        # unknown category -> Severity.MINOR
    @staticmethod
    def default_yaml() -> str

class ProjectScanner:
    def __init__(self, project_root: Path, config_manager: ConfigManager) -> None
    def scan(self, previous_index: Mapping[str, str]) -> ProjectAnalysisResult
```

[SOURCE-CONFIRMED] `src/somnus_debug/doctor/core.py:782-855`, `:1695-1714`.

**Behavior.**

- `ConfigManager(None)` means built-in defaults. It does no file discovery ([D-02](../DISCOVERY-LEDGER.md#d-02)).
- A path must exist and end in `.yaml`, `.yml`, or `.json` (case-insensitive). Anything else raises `ConfigurationError`.
- A relative path resolves against the cwd at `exists()` time. The CLI calls `.resolve()` first; do the same.
- `ProjectScanner.__init__` walks the tree immediately through `ProjectFileIndex`. It raises `AnalysisExecutionError` if the root is missing or not a directory.
- `scan(previous_index)` takes a `{relative_path: sha256}` mapping and uses it only for `state_delta`. Pass `{}` when you keep no state.

**Side effects.** None: no writes, no logging configuration, no prints. [VERIFIED] `/tmp/w1/ex_api.py` showed no new files in the cwd and `root handlers []` after a full scan; same in [lane-a Example A](../_evidence/agent-findings/lane-a-arch-api/api-reference.md). [D-12](../DISCOVERY-LEDGER.md#d-12).

**Return.** A frozen `ProjectAnalysisResult` with these fields: `run_id`, `project_root`, `started_at`, `finished_at`, `config_hash`, `summary: SummaryCounts`, `files: tuple[FileAnalysisResult, ...]`, `issues: tuple[DiagnosticIssue, ...]`, `dependency_graph: DependencyGraphResult`, and `state_delta: StateDelta`. Full field lists are in [types-and-schemas](types-and-schemas.md).

**Failure modes.**

- `ConfigurationError` comes from the constructor; `AnalysisExecutionError` from the scanner constructor.
- During `scan`, per-file problems become issues rather than exceptions, with one exception: on the serial path (`max_workers == 1` or a single-file project), an analyzer exception escapes. [VERIFIED] `/tmp/w1/ex_serial.py`; see [async-and-concurrency](async-and-concurrency.md).

```python
from pathlib import Path
from somnus_debug.doctor import core as d
cm = d.ConfigManager(None)
res = d.ProjectScanner(Path("proj"), cm).scan({})
print(res.summary)
print(d.exit_code_for_summary(res.summary, "serious"), d.exit_code_for_summary(res.summary, "none"))
md = d.MarkdownReportWriter(cm.config).render(res)
js = d.dumps_json(res)
```

Executed: yes (`/tmp/w1/ex_api.py`, lane-a fixture, exit 0). Key output:

```
hash ff1bdc11340bc602 gate serious workers 4
files 6 issues 37 crit 2 serious 13 minor 22 score 0
exit serious 2 critical 2 minor 1 none 0 bogus 1
json keys ['config_hash', 'dependency_graph', 'files', 'finished_at', 'issues', 'project_root', 'run_id', 'started_at', 'state_delta', 'summary']
md starts style True
new files in cwd [] root handlers []
```

## DoctorConfig

This section covers the typed configuration object you read, but do not usually build yourself.

`DoctorConfig` is a frozen dataclass with 29 fields (`src/somnus_debug/doctor/core.py:207-240`). Build it through `ConfigManager`, which validates every field. Constructing it directly skips validation. To change one value programmatically, write a YAML or JSON file and pass its path. Alternatively, call `dataclasses.replace(cm.config, ...)` on a validated instance and assign the result back to `cm.config`, because `ProjectScanner` and `DiagnosticIssueFactory` read `config_manager.config`. [SOURCE-CONFIRMED] `src/somnus_debug/doctor/core.py:1702`, `:1079-1090`, `:792-794`. [VERIFIED] `/tmp/w1/ex_perf.py` sets `cm.config = dataclasses.replace(base.config, max_workers=w)` and scans with each value. When you do this, `cm.config_hash` and `cm.raw_config` still describe the original config, so the hash recorded in reports no longer matches the config that ran. Field list and defaults: [types-and-schemas](types-and-schemas.md#doctorconfig); semantics of each key: [06-configuration/complete-option-reference](../06-configuration/complete-option-reference.md).

## `structure.build_index`

This section documents the only exported library function that does real work.

```python
def build_index(source: str, *, source_name: str, include_lines: bool = True,
                include_module_functions: bool = True) -> str
```

[SOURCE-CONFIRMED] `src/somnus_debug/structure/core.py:202-285`.

- **Input.** Source text, not a path. `source_name` is used as the `ast.parse` filename and, through `Path(source_name).name`, in the heading.
- **Return.** Markdown text that starts with `# Class Index for \`<name>\``, followed by:
  - the class count and the definition count;
  - one `##` block per top-level class, with nested classes as `###`;
  - "Classes nested in functions or other scopes";
  - "Module-level functions".
- **Side effects.** None. The target code is not imported or executed.
- **Raises.** `SyntaxError`, including on valid files whose comments look like PEP 484 type comments, because of `type_comments=True` at `:210`. That covers every metadata-stamped file in this repository. [VERIFIED] [D-01](../DISCOVERY-LEDGER.md#d-01). It can also raise `ValueError` for source containing null bytes. [HYPOTHESIS] based on `ast.parse` behavior; not run.
- **Known defect.** A class nested in a class that is itself inside a function is rendered twice and counted twice. [VERIFIED] [D-24](../DISCOVERY-LEDGER.md#d-24).

```python
from somnus_debug.structure import build_index
src = 'class A:\n    """Doc para."""\n    def m(self, x: int) -> int:\n        return x\n\ndef f():\n    class L:\n        class LI:\n            pass\n    return L\n'
print(build_index(src, source_name="demo.py"))
build_index('x = [  # type: List[int]\n 1]\n', source_name="t.py")   # raises
```

Executed: yes (`/tmp/w1/ex_misc.py`, exit 0). Output, abridged:

```
# Class Index for `demo.py`
...
- Class declarations: 3 (1 top-level, 2 nested)
- Definitions emitted (module-level functions and class methods): 2

## class `A` (lines 1-4)
**Doc**: Doc para.

- `def m(self, x: int) -> int:` (lines 3-4)

## Classes nested in functions or other scopes

### class `L` (lines 7-9)
...
### class `LI` (lines 8-9)      <- rendered once under L
...
### class `LI` (lines 8-9)      <- and again (D-24)
...
## Module-level functions

- `def f():` (lines 6-10)

SyntaxError: invalid syntax line 1
```

## Pycache cleaner

This section documents `CleanerConfig` and `PycacheCleaner`, the cleaner's library surface.

```python
@dataclass
class CleanerConfig:
    roots: List[str] = []
    exclude: List[str] = []
    targets: List[str] = ["__pycache__", "*.pyc", "*.pyo"]
    dry_run: bool = False
    verbose: bool = False
    max_depth: Optional[int] = None
    follow_symlinks: bool = False
    log_file: Optional[str] = None
    @staticmethod
    def from_yaml(path: Path) -> "CleanerConfig"
    def normalize(self) -> None

class PycacheCleaner:
    def __init__(self, config: CleanerConfig) -> None
    def run(self) -> None
    deleted_dirs: int; deleted_files: int; deleted_bytes: int
```

[SOURCE-CONFIRMED] `src/somnus_debug/pycache_cleaner/core.py:157-321`.

**Behavior.**

- `PycacheCleaner.__init__` calls `config.normalize()`, which **mutates the caller's object**: roots and `log_file` are resolved against the cwd, and `~` is expanded. It then raises `ValueError("No roots specified in configuration.")` when `roots` is empty.
- Targets without `*` or `?` are directory names, deleted wholesale. The rest are case-sensitive file globs.
- `exclude` matches directory basenames only.
- `run()` returns `None`. Results are available only as the three counters. Missing roots are logged and skipped.
- No type validation. A string `roots` is iterated character by character, and can produce `/` as a root. [VERIFIED] [D-14](../DISCOVERY-LEDGER.md#d-14).

**Side effects.**

- Deletes files unless `dry_run`.
- Logs through the root logger with module-level `logging.info/debug/error`. If the host has not configured logging, the first such call installs a `StreamHandler(stderr)` on the root logger, because the stdlib `logging.info` auto-configures. [VERIFIED] `/tmp/w1`: root handlers `[]` before `run()`, `[<StreamHandler <stderr>>]` after, root level still 30.

```python
from pathlib import Path
from somnus_debug.pycache_cleaner.core import CleanerConfig, PycacheCleaner
cfg = CleanerConfig(roots=["pc/tree"], dry_run=True)
c = PycacheCleaner(cfg); c.run()
print(c.deleted_dirs, c.deleted_files, c.deleted_bytes, cfg.roots)
```

Executed: yes (`/tmp/w1/ex_tools.py`, a temp tree with `a/__pycache__/m.cpython-312.pyc` (10 B), `b/s.pyc` (5 B), `b/KEEP.PYC`; exit 0):

```
run() -> None dirs 1 files 1 bytes 15
cfg.roots mutated to absolute: True
still present after dry run: True
live dirs 1 files 1 left ['b/KEEP.PYC']
ValueError: No roots specified in configuration.
```

Dry runs count "deleted" items, and `KEEP.PYC` survives because matching is case-sensitive.

## scaffold

This section documents the test-harness copier.

```python
def scaffold(target_dir: Path, *, force: bool = False, with_contract: bool = True) -> list[Path]
```

[SOURCE-CONFIRMED] `src/somnus_debug/test_harness/scaffold.py:62-88`.

- **Behavior.** Resolves `target_dir`. If `force` is false and any destination exists, it raises `FileExistsError` before writing anything. Otherwise it runs `mkdir -p`, writes `run_test.py` (and `CONTRACT.md` when `with_contract`) from package resources, and returns the absolute paths it wrote.
- **Caveat.** The template is project-specific (cargo `gp-cli`) and must be edited. Placed at a repository root, it writes `test-runs/` to the repository's parent. [VERIFIED] [D-15](../DISCOVERY-LEDGER.md#d-15).

```python
from pathlib import Path
from somnus_debug.test_harness.scaffold import scaffold
print(scaffold(Path("sc/repo/single_test")))
scaffold(Path("sc/repo/single_test"))                      # FileExistsError
scaffold(Path("sc/repo/single_test"), force=True, with_contract=False)
```

Executed: yes (`/tmp/w1/ex_tools.py`, exit 0):

```
scaffold -> [PosixPath('<abs>/sc/repo/single_test/run_test.py'), PosixPath('<abs>/sc/repo/single_test/CONTRACT.md')]
FileExistsError: refusing to overwrite existing file(s) without --force
forced -> 1
```

## CLI entry points as functions

This section covers the exported `main` functions. They are callable, but they carry CLI side effects.

| Function | Signature | Returns | Raises | Side effects |
|---|---|---|---|---|
| `somnus_debug.doctor.main` | `main(argv: Sequence[str] \| None = None) -> int` | 0/1/2 gate, 4 `DoctorError`, 5 classified runtime | `SystemExit` on `--help` (0) and usage errors (2); unlisted exception types propagate | creates `./production_doctor.log`; `basicConfig(force=True)` replaces root handlers; prints; writes reports and state |
| `somnus_debug.structure.main` | `main(argv: Optional[Sequence[str]] = None) -> int` | 0, or 2 on `OSError`/`SyntaxError` | `SystemExit(2)` on usage errors; `UnicodeDecodeError` propagates | stdout or output file |
| `somnus_debug.pycache_cleaner.main` | `main() -> None` (reads `sys.argv`) | `None` | `SystemExit(1)` on a missing config or any cleaner exception; YAML errors propagate | deletes files, configures logging |
| `somnus_debug.cli.main` | `main(argv: Sequence[str] \| None = None) -> int` | the tool's code; 2 for an unknown command | exceptions other than `SystemExit` propagate | swaps `sys.argv` during the call |
| `test_harness.scaffold.main` | `main(argv: Sequence[str] \| None = None) -> int` | 0, or 1 on refusal | `SystemExit(2)` on usage errors | writes files, prints |

[SOURCE-CONFIRMED] `src/somnus_debug/doctor/core.py:2184-2199`, `src/somnus_debug/structure/core.py:323-347`, `src/somnus_debug/pycache_cleaner/core.py:349-372`, `src/somnus_debug/cli.py:85-125`, `src/somnus_debug/test_harness/scaffold.py:112-125`. [VERIFIED] doctor in-process handler replacement in [lane-a Example B](../_evidence/agent-findings/lane-a-arch-api/api-reference.md); exit codes in [lane-d exit-codes](../_evidence/agent-findings/lane-d-cli-tests/exit-codes.md).

`doctor.main([])` scans the cwd: `normalize_argv([])` returns `["scan", "."]`. The `--verbose` check, however, reads the host's `sys.argv[1:]`, because `[]` is falsy in `argv or sys.argv[1:]` (`:2186`). [SOURCE-CONFIRMED]

## `__version__`

This section covers the one exported constant.

`somnus_debug.__version__ == "0.1.0"`. It is hard-coded and duplicated in `pyproject.toml`. [VERIFIED] `/tmp/w1/ex_api.py` printed `version 0.1.0`. [D-23](../DISCOVERY-LEDGER.md#d-23).

## Sources

This section lists the code, evidence files, and probes this page rests on.

- `src/somnus_debug/doctor/core.py:207-240`, `:782-855`, `:1695-1714`, `:2184-2199`
- `src/somnus_debug/structure/core.py:202-347`, `src/somnus_debug/pycache_cleaner/core.py:157-372`, `src/somnus_debug/test_harness/scaffold.py:62-125`, `src/somnus_debug/cli.py:85-125`
- [lane-a api-reference.md](../_evidence/agent-findings/lane-a-arch-api/api-reference.md), [lane-d exit-codes.md](../_evidence/agent-findings/lane-d-cli-tests/exit-codes.md)
- Executed probes: `/tmp/w1/ex_api.py`, `/tmp/w1/ex_misc.py`, `/tmp/w1/ex_tools.py`, `/tmp/w1/ex_serial.py`
