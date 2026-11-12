# Compatibility

This page records which Python versions, platforms, dependency versions, and distribution variants somnus-debug 0.1.0 has actually been run on, and how they differ. Claims beyond what was run are marked.

## Python versions

This section is the tested interpreter matrix.

| Python | How obtained | Install | Repo smoke tests | doctor fixture scan | structure (plain / stamped) | fieldkit selftest | Evidence |
|---|---|---|---|---|---|---|---|
| 3.10.22 | `uv python install 3.10` (into `/tmp/w2/uvpy`) | venv + `pip install <repo>`, exit 0 | 10 passed, 2 failed | 7 issues, exit 1 | 0 / 2 | 29/29 | [VERIFIED] W2-06 |
| 3.11.17 | `uv python install 3.11` | exit 0 | 10 passed, 2 failed | 7 issues, exit 1 | 0 / 2 | 29/29 (on rerun; first run killed by the sandbox, exit 137) | [VERIFIED] W2-06 |
| 3.12.15 | system `/usr/local/bin/python3` | exit 0 | 10 passed, 2 failed | 7 issues, exit 1 | 0 / 2 | 29/29 | [VERIFIED] W2-03, W2-04, W2-06 |
| 3.13.5 | `/usr/bin/python3`, **no PyYAML** | not installed (`PYTHONPATH=src`) | not run | via `-m somnus_debug.doctor.core`: 7 issues, exit 1 | `-m somnus_debug.structure.core`: exit 0 on a plain file | not run (the dispatcher fails without PyYAML) | [VERIFIED] W2-05 |
| < 3.10 | not available | n/a | n/a | n/a | n/a | n/a | [UNVERIFIED] Declared unsupported (`requires-python >=3.10`) |

On the doctor fixture (the quickstart project), the issue tuples `(category, file_path, line_number, symbol)` were identical on 3.10, 3.11, and 3.12 (W2-06). The 3.13 run matched on counts.

Notes:

- `pyproject.toml` classifiers stop at 3.12. 3.13 works for doctor and structure. Under 3.13 the dispatcher was only tested without PyYAML (it fails). The dispatcher with PyYAML on 3.13 is [UNVERIFIED].
- Import classification uses the running interpreter's stdlib list, so results on code that imports version-specific stdlib modules can differ by version. [HYPOTHESIS] See [environment-detection](environment-detection.md).

## Platforms

This section states the platform coverage honestly.

| Platform | Status |
|---|---|
| Linux aarch64, Debian 13 (this sandbox) | [VERIFIED] all W2 and lane runs |
| Linux x86_64 | [UNVERIFIED] (no platform-specific code exists, so expected to behave the same; [HYPOTHESIS]) |
| macOS | [UNVERIFIED] |
| Windows | [UNVERIFIED]. pycache-clean's promised long-path support is not implemented ([SOURCE-CONFIRMED] `src/somnus_debug/pycache_cleaner/core.py:64`, no `os.name` branch). Doctor's `production_doctor.log` handler and path handling use `pathlib`, which should be portable ([HYPOTHESIS]) |

## Dependency versions

This section lists the PyYAML and pytest versions seen.

| Dependency | Versions exercised | Notes |
|---|---|---|
| PyYAML | 6.0.3 (fresh venvs, W2-02/W2-06), 6.0.2 (system Python, lanes B/D) | unpinned in `pyproject.toml`; only pycache-clean and the dispatcher import it |
| pytest | 9.2.0 (W2 venvs) | only for `tests/`; declared `pytest>=7` in the `dev` extra |
| sqlite3 | the stdlib module of each interpreter | required for doctor state; scan degrades without a usable DB |

## Distribution variants

This section compares the code you might actually be running.

| Variant | Same code as this tree's `src/`? | Behavioral differences |
|---|---|---|
| PyPI 0.1.0 wheel/sdist | yes, after header strip | `default_config.yaml` has old globs (reference-only, no runtime effect). Its files have no metadata headers, so `structure` indexes its own source but still crashes on stamped files |
| wheel built from this tree | byte-identical to `src/` | none |
| `PYTHONPATH=src` source run | identical | `SyntaxWarning` from pycache on uncached imports |
| root duplicate scripts | **no** | structure handles stamped files; doctor lacks the SQLite fallback |

[VERIFIED] lane D [install-vs-source.md](../_evidence/agent-findings/lane-d-cli-tests/install-vs-source.md) sections 2-5; W2-01 (source help identical to installed). Layout details: [package-layout](package-layout.md).

## Backward compatibility of invocations

This section lists the legacy forms that still work.

- `somnus-doctor <path>` and `somnus-doctor --no-state ...` (the old standalone forms) are normalized to `scan`. [VERIFIED] lane D D35-D37.
- The root scripts accept the same flags as the packaged tools. [VERIFIED] lane D section 7.
- No deprecation warnings are emitted anywhere. [SOURCE-CONFIRMED]

## Sources

This section lists the code and evidence this page draws on.

- `pyproject.toml`; `src/somnus_debug/doctor/core.py:72`, `:79`, `:1001`, `:2165-2176`; `src/somnus_debug/pycache_cleaner/core.py:64`
- [lane D install-vs-source.md](../_evidence/agent-findings/lane-d-cli-tests/install-vs-source.md), [experiment-log.md](../_evidence/agent-findings/lane-d-cli-tests/experiment-log.md)
- W2 runs: [verification-results](../11-verification/verification-results.md#w2-runs)
