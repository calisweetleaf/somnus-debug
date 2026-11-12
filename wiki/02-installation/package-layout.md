# Package layout

This page maps three trees onto each other: the repository at baseline commit `034f46e`, the installed wheel, and the PyPI 0.1.0 artifacts. It also explains the root-level duplicates that sit beside `src/`. Use it to answer "is this file what actually runs?"

## Repository tree

This section lists the repo and marks what is packaged.

```text
somnus-debug/                         (commit 034f46e = uploaded zip)
  pyproject.toml                      build + scripts            -> metadata
  README.md, LICENSE                  -> sdist (README also wheel METADATA)
  LICENSE.somnus.yaml                 provenance; not packaged
  STATE.md, PLAN.md                   operator files, present in the zip (gitignored upstream); not packaged
  .gitignore                          local-only ignore file (lists itself)
  docs/  AGENTS_APPENDIX.md CONTRACT.md MANUAL.md PUBLISHING.md Python_Doctor_QUICKSTART.md   -> sdist only
  assets/  *.svg                      README art; not packaged
  src/somnus_debug/                   -> wheel (the code that runs)
    __init__.py                       __version__ = "0.1.0"
    cli.py                            somnus-debug dispatcher
    doctor/__init__.py, core.py       doctor (2203 lines, stdlib only)
    doctor/default_config.yaml        reference copy of init-config output; read by no code
    structure/__init__.py, core.py    structure indexer
    pycache_cleaner/__init__.py, core.py   pycache cleaner (PyYAML)
    test_harness/__init__.py, scaffold.py  init-test-harness
    test_harness/templates/__init__.py, run_test.py, CONTRACT.md   package data copied by scaffold
  tests/test_cli_smoke.py             12 smoke tests; not packaged
  skills/somnus-debug-fieldkit/       agent fieldkit (SKILL.md, references/, scripts/, templates/); not packaged
  python_production_doctor.py         root duplicate of doctor/core.py (pre-packaging); not packaged
  analyze_python_structure.py         root duplicate of structure/core.py; not packaged
  pycache_cleaner.py                  root duplicate of pycache_cleaner/core.py; not packaged
  run_test.py                         root duplicate of templates/run_test.py; not packaged
  python_doctor.yaml                  old Somnus-MCP doctor config; read by nothing automatically
```

[SOURCE-CONFIRMED] repo file list; `pyproject.toml` `[tool.hatch.build.targets.wheel] packages = ["src/somnus_debug"]` and sdist `include = ["src/somnus_debug", "README.md", "LICENSE", "docs/**"]`. `docs/OPSEC.md`, linked from README and MANUAL, does not exist. [VERIFIED] lane F [doc-reconciliation.md](../_evidence/agent-findings/lane-f-ext/doc-reconciliation.md).

Every source file in the repo begins with a 32-line `# somnus:metadata:v2 ... # somnus:end` comment block. Markdown files use YAML front matter instead. Line numbers cited across this wiki are real file lines, header included. [SOURCE-CONFIRMED]

## Installed wheel

This section lists what `pip install` puts on disk.

From the installed `RECORD` (W2-02), excluding `__pycache__`:

```text
bin/somnus-debug  bin/somnus-doctor  bin/somnus-pycache-clean  bin/somnus-structure
somnus_debug/__init__.py  somnus_debug/cli.py
somnus_debug/doctor/__init__.py  somnus_debug/doctor/core.py  somnus_debug/doctor/default_config.yaml
somnus_debug/pycache_cleaner/__init__.py  somnus_debug/pycache_cleaner/core.py
somnus_debug/structure/__init__.py  somnus_debug/structure/core.py
somnus_debug/test_harness/__init__.py  somnus_debug/test_harness/scaffold.py
somnus_debug/test_harness/templates/__init__.py  somnus_debug/test_harness/templates/run_test.py
somnus_debug/test_harness/templates/CONTRACT.md
somnus_debug-0.1.0.dist-info/{INSTALLER,METADATA,RECORD,REQUESTED,WHEEL,direct_url.json,entry_points.txt,licenses/LICENSE}
```

`entry_points.txt` (lane D, identical to `pyproject.toml`):

```text
[console_scripts]
somnus-debug = somnus_debug.cli:main
somnus-doctor = somnus_debug.doctor.core:main
somnus-pycache-clean = somnus_debug.pycache_cleaner.core:main
somnus-structure = somnus_debug.structure.core:main
```

The `[tool.hatch.build] exclude` list (`.python_doctor/`, `*_report.*`, `production_doctor.log`, `__pycache__`, `*.pyc`) keeps run artifacts out of builds. No such files are in the RECORD. [VERIFIED] W2-02; lane D section 1.

Files are copied byte for byte, metadata headers included. The installed `structure/core.py:210` therefore still carries `type_comments=True`. [VERIFIED] lane D section 1; W2-06 (installed structure crashes on stamped files under 3.10, 3.11, and 3.12).

## PyPI 0.1.0

This section compares the published artifacts with this tree.

| Aspect | PyPI 0.1.0 | This tree's `src/` |
|---|---|---|
| metadata headers | none | every file |
| code (after header strip) | identical | identical |
| `type_comments=True` in structure | yes (`structure/core.py:178`) | yes (`:210`; the 32-line offset is the header) |
| SQLite-unavailable fallback in doctor | yes | yes |
| `doctor/default_config.yaml` | old Somnus-MCP globs (`tools/*.py`, `test/*.py`, ...) | `include_patterns: ["*.py"]` plus modern ignores |
| `templates/CONTRACT.md` | no front matter | 32-line YAML front matter; body identical |
| sdist extras | README, LICENSE, `docs/*.md`, `PKG-INFO`; no tests, no skills | n/a |

[VERIFIED] lane D [install-vs-source.md](../_evidence/agent-findings/lane-d-cli-tests/install-vs-source.md) sections 2-3. The version string `0.1.0` is hard-coded in both `pyproject.toml` and `src/somnus_debug/__init__.py:57`, and nothing ties them together. [SOURCE-CONFIRMED] See [D-23](../DISCOVERY-LEDGER.md#d-23).

## Root-level duplicates vs src

This section explains why running a root script is not the same as running the package.

| Root file | Differs from its `src/` counterpart? | Practical effect |
|---|---|---|
| `python_production_doctor.py` | yes: `run_scan` lacks the `StateStoreError` fallback (`python_production_doctor.py:2066`) | an unusable state DB aborts the scan instead of degrading. See [D-28](../DISCOVERY-LEDGER.md#d-28) |
| `analyze_python_structure.py` | yes: line 210 parses **without** `type_comments` | works on stamped files ([VERIFIED] W2-15). This is the only place the "2026-11-05 fix" from STATE.md exists. See [D-01](../DISCOVERY-LEDGER.md#d-01) |
| `pycache_cleaner.py` | identical after header strip | same behavior, plus the `SyntaxWarning` on every run (never cached) |
| `run_test.py` | identical after header strip | same template; running it in place writes `forge/test-runs/` (the parent of the repo) |
| `python_doctor.yaml` | equals the **PyPI** default config (old globs) | adopted by `onboard.py` by default and scans 0 files on a normal tree (lane F OB-5) |

[VERIFIED] lane D sections 4-5, 7. `README.md:330` and `docs/MANUAL.md` section 7.5 call these "harmless, just redundant". The structure and doctor differences make that untrue. [DISCREPANCY]

## Generated at runtime (never shipped)

This section lists the paths tools create, so they are not mistaken for package content.

| Path | Created by |
|---|---|
| `<cwd>/production_doctor.log` | every doctor call |
| `<root>/production_doctor_report.{md,json}` | `doctor scan` without `-o` |
| `<root>/.python_doctor/{state.sqlite3, reports/...}` | stateful scan; also `history` on a never-scanned root |
| `<pkg>/doctor/self_check_report.*`, `<pkg>/doctor/.python_doctor/` | `doctor self-check` |
| `<target>/run_test.py`, `CONTRACT.md` | `init-test-harness` |
| `<project_root>/test-runs/<RUN_ID>/` | scaffolded `run_test.py` |
| `<repo>/.somnus-debug/` | fieldkit `onboard.py --apply` |

[VERIFIED] W2-10, W2-11, W2-19; lane D D12, D14; lane F O2. See [D-10](../DISCOVERY-LEDGER.md#d-10).

## Sources

This section lists the code and evidence this page draws on.

- `pyproject.toml`; installed `RECORD`/`entry_points.txt`
- `src/somnus_debug/__init__.py:57`; `src/somnus_debug/structure/core.py:210`; `src/somnus_debug/doctor/core.py:2061-2076`
- root `analyze_python_structure.py:210`, `python_production_doctor.py:2066`
- `README.md:330`; `docs/MANUAL.md` section 7.5; `STATE.md`
- [lane D install-vs-source.md](../_evidence/agent-findings/lane-d-cli-tests/install-vs-source.md); [lane A architecture.md](../_evidence/agent-findings/lane-a-arch-api/architecture.md) section 1; [lane F doc-reconciliation.md](../_evidence/agent-findings/lane-f-ext/doc-reconciliation.md), [fieldkit.md](../_evidence/agent-findings/lane-f-ext/fieldkit.md)
- W2 runs: [verification-results](../11-verification/verification-results.md#w2-runs)
