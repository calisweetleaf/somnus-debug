# Findings playbook

What each doctor category actually detects in 0.1.0, how to fix it for real, and the false positives that will show up. Triggers are read from `src/somnus_debug/doctor/core.py`; rows marked **(selftest)** are re-proven on every `scripts/selftest.py` run.

## Triage rule

For every finding in scope, decide one of four outcomes:

1. **Fix it.** It's a real defect in code you're touching.
2. **Out of scope.** It's real, but outside this task. Leave it in the backlog.
3. **Disposition it.** It's a false positive, or an accepted design choice. Add an entry to `.somnus-debug/dispositions.json` with a reason a reviewer would accept.
4. **Unverified.** Proving it needs runtime or input you don't have. Say so.

Never make a finding go away by renaming, re-importing, lowering severities, or excluding the file. The evasions below are listed so you recognize them in review, not so you use them.

## Severity, gate, and score

| Severity | Categories (defaults) |
|---|---|
| critical | `analysis_read_errors`, `syntax_errors`, `tokenization_errors` |
| serious | `missing_imports`, `dependency_cycles`, `stubs`, `placeholder_returns`, `incomplete_methods`, `suspicious_short_classes`, `silent_failures`, `broad_exceptions`, `security_risks`, `test_gaps` |
| minor | `todos`, `missing_docstrings`, `suspicious_short_functions`, `type_hint_gaps`, `complexity`, `unused_imports`, `duplicate_definitions` |

The `serious` gate exits 1 on any serious finding and 2 on any critical one. The production score is `max(0, 100 - 20*critical - 8*serious - 2*minor - info)`. It is a trend number, not a quality verdict.

## Scope rules that change what gets checked

- **Private functions** (`_name`, not dunder) are skipped unless `check_private_functions: true`. Their bodies are still visited, so nested definitions and calls inside them are checked.
- **Dunder methods** such as `__init__` *are* checked: docstring, hints, and shortness. The defaults only ignore `__repr__` and `__str__` (`ignore_functions`).
- **Nested functions** are checked (`check_nested_functions: true`).
- **Line counts** use unique executable lines, excluding the docstring. A one-line body counts as 1.

## Categories

### `syntax_errors`, `tokenization_errors`, `analysis_read_errors` (critical)
A file failed `ast.parse` or `tokenize`, or couldn't be read or decoded. Every other check is skipped for that file. **Fix:** make the file parse under the interpreter running doctor. A newer syntax feature run under an older Python counts here. **Don't:** exclude the file to turn the gate green.

### `missing_imports` (serious) — (selftest)
**Trigger:** an import that isn't found among the scanned files, the stdlib, or `importlib.util.find_spec` **in the interpreter running doctor**.
**False-positive sources, most common first:**
1. **Doctor runs outside the project's environment.** Every third-party dependency is then reported missing. Fix: `pip install somnus-debug` into the project's venv and run `<venv>/bin/python -m somnus_debug.cli doctor ...`. `onboard.py` picks that runner automatically.
2. **`src/` layout.** Files are indexed as `src.pkg.mod`, so `import pkg.mod` doesn't resolve locally. Fix: run with `PYTHONPATH=src` (the onboard profile does this), or install the project editable (`pip install -e .`).
3. **Optional or conditional imports** inside `try/except ImportError`. Disposition them with the reason, or install the extra.
**Real defects:** a typo, a dependency missing from `pyproject.toml`, or a relative import that climbs above the package (`unresolved_relative`).

### `dependency_cycles` (serious)
**Trigger:** a cycle among *local* import edges between scanned files. **Fix:** move the shared contract into a lower module, or defer an import to the function that needs it. Lazy imports inside functions are still collected by the AST walk, so moving an import into a function does not hide the cycle from doctor. Restructure instead.

### `stubs` (serious) — (selftest)
**Trigger:** a function or class body, after the docstring, that is exactly one `pass`, `...`, or `raise NotImplementedError[(...)]`.
**False positives:** `@abstractmethod` bodies, `typing.Protocol` methods, `@overload` signatures, and marker exception classes whose body is just `pass`. Decorators are not consulted. Disposition them with symbol-level entries. An abstract method can instead carry a meaningful body, for example raising a domain error that names the subclass contract.
**Real defects:** anything that callers actually reach.

### `placeholder_returns` (serious)
**Trigger:** the whole body is one `return` of `None`, `True`, `False`, `0`, `-1`, `""`, `[]`, `{}`, `()`, or `set()`.
**False positives:** intentional constant hooks (`def is_enabled(self) -> bool: return True` in a base class) and default strategy objects. Disposition them. Better: give the hook a docstring that states the contract and a body that computes something.

### `incomplete_methods` (serious)
**Trigger:** a class inherits from a **same-file** class that declares `@abstractmethod`/`abc.abstractmethod`, but doesn't define every one of those names. Cross-file bases are not checked. **Fix:** implement the methods, or mark the subclass abstract.

### `suspicious_short_classes` (serious)
**Trigger:** a non-dataclass, non-Enum, non-exception class whose body is empty, or that has fewer than `min_class_lines` (6) executable lines and either no methods or no public methods and no attributes. **False positives:** marker or tag classes, `TypedDict`/`NamedTuple` subclasses (not exempted), and small mixins. Disposition them, or convert to `@dataclass` or `Enum` when that is the real intent.

### `silent_failures` (serious) — (selftest)
**Trigger:** an `except` body that is empty, or a lone `pass`, a lone placeholder `return`, or a lone `print(...)`/`logging.debug|info(...)`. Also any handler containing no `raise` and no call spelled exactly `logging.error`, `logging.exception`, `logger.error`, or `logger.exception`.
**Name-sensitive:** `log.error(...)`, `self.logger.error(...)`, `LOG.exception(...)`, and `logger.warning(...)` all count as **silent**. Real fix, in order of preference: re-raise a domain error with context; or call `logger.exception(...)` on a module-level `logger = logging.getLogger(__name__)`; or return a structured failure the caller must inspect (and disposition it).
**Don't:** rename your logger to `logger` only to satisfy the check while still swallowing the error.

### `broad_exceptions` (serious)
**Trigger:** a bare `except:`, or `except Exception` / `except BaseException`. This fires even when the handler logs and re-raises. **Accepted uses:** top-level CLI or worker boundaries that convert any error into an exit code or a structured failure. Disposition those by symbol with that reason. Everywhere else, catch the specific exceptions.

### `security_risks` (serious)
**Trigger:** a call whose dotted name is exactly one of `eval`, `exec`, `compile`, `pickle.load(s)`, `marshal.load(s)`, `yaml.load`, `os.system`, `os.popen`, `subprocess.call`, `subprocess.run`, `subprocess.Popen`.
**Fix:** `yaml.safe_load`, `ast.literal_eval`, `json`, or typed APIs. For subprocess, an argv list, no `shell=True`, a fixed executable, and validated arguments is the safe form. It is still flagged, so **disposition it** with exactly that reason.
**Evasion to reject in review:** `from subprocess import run; run(...)` or `sp = subprocess; sp.run(...)` escape the dotted-name match. That hides risk; it does not remove it.

### `test_gaps` (serious, configured) — (selftest)
**0.1.0 never emits this category.** `detect_test_gaps` and its severity exist in the config, but no code produces the finding. A clean doctor run says nothing about test coverage. Use the project's real test runner and coverage tool. If a future version starts emitting it, `selftest.py` fails on its sentinel check; update this section then.

### `todos` (minor) — (selftest)
**Trigger:** a comment matching `TODO`, `FIXME`, `HACK`, `XXX`, `TEMP`, or `WIP` as a word, **case-insensitive**. Plain prose like "# write to a temp dir" or "# wip branch" therefore triggers. **Fix:** resolve the debt, or move it to a tracked issue. Reword prose comments that only collide by accident.

### `missing_docstrings` (minor)
**Trigger:** a module, class, or function docstring shorter than `min_docstring_length` (18 characters, stripped), honoring the `require_*_docstring` switches. **Fix:** state purpose and contract. Padding a docstring to 18 characters satisfies the check and helps nobody.

### `type_hint_gaps` (minor)
**Trigger:** a missing return annotation, or any unannotated parameter (including `*args` and `**kwargs`) except `self`/`cls`. `__init__` needs `-> None`. Test functions are included, so `def test_x() -> None:`.

### `suspicious_short_functions` (minor)
**Trigger:** fewer than `min_function_lines` (5) executable lines. Many correct functions are short: properties, adapters, delegations. This is the noisiest category. Leave it at minor, review it only in code you're touching, and don't pad functions.

### `complexity` (minor)
**Trigger:** cyclomatic complexity above 12. It counts `if`/`for`/`while`/`try`/`except`/ternary/`match`, each extra boolean operand, and each comprehension loop plus its filters. **Fix:** extract named validation, collection, and rendering steps.

### `unused_imports` (minor)
**Trigger:** an imported name that's never loaded as a plain `Name`. Names starting with `_` and star imports are skipped.
**False positives:** `from __future__ import annotations`; re-exports in `__init__.py` (listing a name in `__all__` does not count, because strings are not loads); names used only inside quoted (string) annotations; side-effect imports. Unquoted annotations are AST names and do count as uses. Disposition the re-exports and the `__future__` import, or prefix intentional side-effect imports with `_`.

### `duplicate_definitions` (minor) — (selftest)
**Trigger:** the same name defined more than once in one scope. **False positives:** `@property` + `@x.setter`/`@x.deleter` pairs, `@typing.overload` families, and `@singledispatch` `.register` functions named `_`. Disposition them by symbol. Real defects: a copy-pasted function that silently shadows the first definition.

## Writing dispositions

`dispositions.json` is a JSON list. `file` and `symbol` are fnmatch globs; `symbol` defaults to `*`. Keep each entry as narrow as the evidence allows:

```json
[
  {"category": "security_risks", "file": "scripts/release.py", "symbol": "publish", "reason": "argv list, no shell, fixed twine executable"},
  {"category": "duplicate_definitions", "file": "src/pkg/box.py", "symbol": "Box.value", "reason": "property getter/setter pair"},
  {"category": "missing_imports", "file": "src/pkg/compat.py", "symbol": "tomli", "reason": "py<3.11 fallback inside try/except ImportError"}
]
```

`delta.py` lists every entry that no longer matches anything as stale. Delete stale entries, so the file stays a true record and doesn't turn into a blanket mute.
