# Entrypoint index

This page is the complete index of every way to start somnus-debug code: console scripts, `python -m` targets, `main()` functions, library entry points, repo-only scripts, and root duplicates. Each entry gives its backend location and how argv reaches it. Full behavior is in [05-cli-and-tools/command-reference](../05-cli-and-tools/command-reference.md).

## Console scripts (installed)

This section lists the four scripts `pip install` creates.

| Script | Target (`pyproject.toml` `[project.scripts]`) | argv handling | Return | Evidence |
|---|---|---|---|---|
| `somnus-debug` | `somnus_debug.cli:main` (`src/somnus_debug/cli.py:107`) | `sys.argv[1:]`; routes to a tool | int | [VERIFIED] W2-02 |
| `somnus-doctor` | `somnus_debug.doctor.core:main` (`src/somnus_debug/doctor/core.py:2184`) | `sys.argv[1:]`, legacy-normalized | int (0/1/2/4/5) | [VERIFIED] W2-02 |
| `somnus-structure` | `somnus_debug.structure.core:main` (`src/somnus_debug/structure/core.py:323`) | `sys.argv[1:]` | int (0/2) | [VERIFIED] W2-02 |
| `somnus-pycache-clean` | `somnus_debug.pycache_cleaner.core:main` (`src/somnus_debug/pycache_cleaner/core.py:349`) | `argparse` reads `sys.argv` (no argv parameter) | `None`; exits via `sys.exit(1)` on error | [VERIFIED] W2-02 |

There is no `somnus-init-test-harness`. [VERIFIED] W2-02.

## Dispatcher subcommands

This section lists the routes inside `somnus-debug`.

| Subcommand | Function called | Call form | Evidence |
|---|---|---|---|
| `doctor` | `doctor.core.main` | `main(list(rest))` | [SOURCE-CONFIRMED] `src/somnus_debug/cli.py:60-65`, `:100` |
| `structure` | `structure.core.main` | `main(list(rest))` | same |
| `pycache-clean` | `pycache_cleaner.core.main` | `main()`, with `sys.argv` swapped | same |
| `init-test-harness` | `test_harness.scaffold.main` | `main(list(rest))` | same |

The doctor subcommands (`scan`, `init-config`, `history`, `rollback`, `self-check`) map to `run_scan`, `run_init_config`, `run_history`, `run_rollback`, and `run_self_check` (`src/somnus_debug/doctor/core.py:2061`, `:2096`, `:2106`, `:2113`, `:2123`) through `build_parser` (`:2130`).

## python -m targets

This section lists which modules can be executed with `-m`.

| Target | Works? | Notes | Evidence |
|---|---|---|---|
| `somnus_debug.cli` | yes | equivalent to `somnus-debug`; puts the cwd on `sys.path` | [VERIFIED] W2-01, W2-25 |
| `somnus_debug.doctor.core` | yes | runpy `RuntimeWarning`; `prog` is `core.py`; works without PyYAML | [VERIFIED] W2-05 |
| `somnus_debug.structure.core` | yes | runpy `RuntimeWarning` | [VERIFIED] W2-05; lane D C06 |
| `somnus_debug.pycache_cleaner.core` | expected yes (has a `__main__` guard) | not run | [SOURCE-CONFIRMED] `src/somnus_debug/pycache_cleaner/core.py:375-376` |
| `somnus_debug.test_harness.scaffold` | yes | `prog` hard-coded `somnus-debug init-test-harness` | [VERIFIED] W2-02 |
| `somnus_debug` | **no** (no `__main__.py`), exit 1 | | [VERIFIED] lane D C04 |
| `somnus_debug.doctor` (and the other subpackages) | **no**, exit 1 | | [VERIFIED] lane D C05 |

## Library entry points

This section lists the functions and classes callers use without argv. Full signatures are in [04-library-api/public-api](../04-library-api/public-api.md).

| Entry point | Location | Side effects | Evidence |
|---|---|---|---|
| `somnus_debug.cli.main(argv)` | `src/somnus_debug/cli.py:107` | everything the routed tool does, plus doctor's logging hijack | [VERIFIED] W2-20 |
| `somnus_debug.doctor.core.main(argv)` | `:2184` | log in cwd, `basicConfig(force=True)` | [VERIFIED] W2-20 |
| `ProjectScanner(root, ConfigManager(path or None)).scan(previous)` | `:1695`, `:782` | none (no disk, no logging) | [VERIFIED] W2-20; lane A. See [D-12](../DISCOVERY-LEDGER.md#d-12) |
| `MarkdownReportWriter(config).render(result)`, `dumps_json(result)` | `:1776`, `:578` | none | [SOURCE-CONFIRMED] used by `run_scan`, `:2077-2078` |
| `StateStore(root, config)` methods (`persist`, `history`, `rollback`) | `:1916` | state writes under `<root>/<state_dir>` | [SOURCE-CONFIRMED] |
| `somnus_debug.structure.build_index(source, *, source_name, include_lines=True, include_module_functions=True)` | `src/somnus_debug/structure/core.py:202` | none; raises `SyntaxError` on stamped headers | [VERIFIED] minimal-examples run |
| `somnus_debug.test_harness.scaffold.scaffold(target_dir, *, force=False, with_contract=True)` | `src/somnus_debug/test_harness/scaffold.py:62` | writes files; raises `FileExistsError` | [VERIFIED] minimal-examples run |
| `somnus_debug.__version__` | `src/somnus_debug/__init__.py:57` | none | [SOURCE-CONFIRMED] |

## Scaffolded program

This section lists the entry point that `init-test-harness` writes.

| Entry | Location | argv | Configuration | Evidence |
|---|---|---|---|---|
| `python run_test.py` | `src/somnus_debug/test_harness/templates/run_test.py:747` (`main`) | ignored | `PROJECT_ROOT`, `SINGLE_TEST_OUTPUT_DIR` | [VERIFIED] W2-19 |
| `execute_test(ctx) -> TestOutcome` | template `:198` | n/a | the one function a project edits, along with `TEST_NAME` (`:195`) | [SOURCE-CONFIRMED] |

## Repo-only scripts (not installed)

This section lists entry points that exist only in a checkout.

| Script | argv | Exit codes | Evidence |
|---|---|---|---|
| `skills/somnus-debug-fieldkit/scripts/selftest.py [--python PY]` | argparse | 0 / 1 / 3 | [VERIFIED] W2-04, W2-24 |
| `skills/somnus-debug-fieldkit/scripts/onboard.py [repo] [--apply] [--baseline] [--new-config] [--python PY]` | argparse | 0 / 1 / 2 / 3 | [VERIFIED] W2-24; lane D O01-O08 |
| `skills/somnus-debug-fieldkit/scripts/delta.py BASELINE LATEST [--dispositions F] [--root DIR] [--json]` | argparse | 0 / 1 / 2 / 3 | [VERIFIED] W2-14, W2-17, W2-24 |
| `tests/test_cli_smoke.py` | via pytest | pytest's | [VERIFIED] W2-03 |

## Root duplicates (pre-packaging)

This section lists the loose scripts at the repo root. Each one runs its own copy of the code, which can differ from `src/`.

| Script | Packaged counterpart | Behavioral difference | Evidence |
|---|---|---|---|
| `python_production_doctor.py` | `doctor/core.py` | no SQLite-unavailable fallback (`:2066`) | [VERIFIED] lane D section 4 |
| `analyze_python_structure.py` | `structure/core.py` | no `type_comments`, so it works on stamped files | [VERIFIED] W2-15 |
| `pycache_cleaner.py` | `pycache_cleaner/core.py` | none (after header strip) | [VERIFIED] lane D section 4 |
| `run_test.py` | `templates/run_test.py` | none; running it in place writes `../test-runs/` (the `forge/` directory) | [VERIFIED] lane D section 7 |

## Sources

This section lists the code and evidence this page draws on.

- `pyproject.toml` `[project.scripts]`
- `src/somnus_debug/cli.py:54-125`; `src/somnus_debug/doctor/core.py:578`, `:782`, `:1695`, `:1776`, `:1916`, `:2061-2184`; `src/somnus_debug/structure/core.py:202`, `:323`; `src/somnus_debug/pycache_cleaner/core.py:349`, `:375-376`; `src/somnus_debug/test_harness/scaffold.py:62`, `:112`; `src/somnus_debug/test_harness/templates/run_test.py:195-198`, `:747`
- [lane D command-reference.md](../_evidence/agent-findings/lane-d-cli-tests/command-reference.md), [install-vs-source.md](../_evidence/agent-findings/lane-d-cli-tests/install-vs-source.md); [lane A api-reference.md](../_evidence/agent-findings/lane-a-arch-api/api-reference.md)
- W2 runs: [verification-results](../11-verification/verification-results.md#w2-runs)
