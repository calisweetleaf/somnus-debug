# Lane B: Configuration and implicit behavior

Baseline: commit 034f46e, package 0.1.0, Python 3.12.15, PyYAML 6.0.2. All experiments ran under `/tmp/lane-b/` with `PYTHONPATH=<repo>/src` and `PYTHONWARNINGS=ignore` (to suppress the pycache SyntaxWarning, see 6.4). No repo file outside this directory was written. `pycache-clean` was only ever run against `/tmp/lane-b/pc/tree`. Self-check was run against a copy of `src/` at `/tmp/lane-b/srccopy`.

Companion files:
- `configuration-registry.tsv`: 94 rows, 17 columns as briefed.
- `experiments/yaml_probe.py` + `experiments/yaml_probe.out`: 48 YAML cases, doctor parser vs PyYAML.
- `experiments/run_cfg.sh`: the config-matrix harness (C01–C26).
- `experiments/mk_tsv.py`: the generator for the TSV.

Evidence classes follow BRIEF.md. `D` = `src/somnus_debug/doctor/core.py`, `PC` = `src/somnus_debug/pycache_cleaner/core.py`, `ST` = `src/somnus_debug/structure/core.py`, `SC` = `src/somnus_debug/test_harness/scaffold.py`, `RT` = `src/somnus_debug/test_harness/templates/run_test.py`.

---

## 1. Top findings (ranked by impact)

1. **Doctor never auto-discovers a config file.** Without `-c`, `ConfigManager(None)` deep-merges `DEFAULT_CONFIG_DATA` with `{}` (D:797-799, D:2063). A `python_doctor.yaml` in the CWD or the project root is ignored. VERIFIED: in `/tmp/lane-b/proj`, a `python_doctor.yaml` holding `severity_exit_level: "none"` gave exit 1 without `-c` (E1) and exit 0 with `-c python_doctor.yaml` (E2). The README quickstart (`init-config` then `scan .`) and QUICKSTART ("Generate a starting config in your project root") both imply the file gets used. DISCREPANCY (docs vs code).
2. **Unquoted `none` breaks the `none` gate.** The parser maps `none`/`None`/`null`/`~` to null (D:625-626). So `severity_exit_level: none` becomes `None`, and `require_str` fails with exit 4. Only `"none"` (quoted) works. VERIFIED (u.yaml → exit 4; q.yaml → exit 0). The `none` and `info` gates appear in no doc at all (D:819 vs MANUAL 3.4 and QUICKSTART "Exit codes").
3. **`detect_test_gaps` is a dead key.** It is validated (D:840) and never read: grep finds only D:229/470/840/892. Setting it to false changes nothing (C22: same 9 issues as baseline). `test_gaps` severity (D:493) is also dead. VERIFIED.
4. **`ignore_functions` hides security findings.** It returns before `generic_visit` (D:1237-1238), so a function on the list loses everything inside its body as well: `security_risks` (eval), `broad_exceptions`, and `silent_failures`. VERIFIED (C23: 9→3 issues, eval at line 7 gone). `check_nested_functions: false` does the same for every nested def and its body (D:1235-1236; VERIFIED, `exec`/`eval` in nested functions dropped, exit 1→0).
5. **Default ignores prune same-named directories at any depth.** In `ignore_patterns`, an `X/*` pattern also matches any directory *named* X anywhere (D:945-946). With the defaults, a real package directory such as `myapp/env/` or `x/build/` is skipped silently. VERIFIED (`pkg/env/e.py` and `x/build/gen.py` not discovered).
6. **The MANUAL's recommended include globs drop files.** MANUAL 3.1 recommends `src/**/*.py` and `tests/**/*.py`. With fnmatch, `src/**/*.py` needs at least one subdirectory, so it does **not** match `src/c.py`. `tests/**/*.py` likewise drops top-level `tests/test_x.py`. VERIFIED (include `src/**/*.py` → only `src/a/b.py`).
7. **pycache `exclude` matches directory basenames only.** It uses case-sensitive `fnmatchcase(name, pat)` (PC:263). The MANUAL 5.1 example `"node_modules/*"` / `".git/*"` never matches, so `node_modules/__pycache__` and `.git/__pycache__` are deleted. VERIFIED (P2 dry-run: 5 dirs + 6 files incl. node_modules/.git; P3 with bare names: 3 dirs + 4 files). Contradictory doc.
8. **One unknown pycache key silences all logging.** `from_yaml` calls `logging.warning` *before* `setup_logging` (PC:179 vs PC:366). That auto-configures the root logger at WARNING, and the later `basicConfig` (PC:334, no `force`) does nothing. The result: no INFO output (Summary included), `verbose` ignored, and `log_file` created but left empty. VERIFIED (P10: only the WARNING line; `run.log` 0 lines. P11 without the unknown key: 25 lines).
9. **pycache config values are not type-checked.** They go straight in through `setattr` (PC:176-177). VERIFIED:
   - `dry_run: "false"` (quoted) is truthy, so the run is dry, yet the log prints `dry_run=false` (P8).
   - `dry_run: no` (YAML 1.1) is False, so the run is **live** (P8b: all 16 artifacts deleted).
   - `roots: tree` is iterated per character (P6).
   - `max_depth: "2"` → TypeError, exit 1 (P7).
   - `exclude: null` / `targets: null` → TypeError traceback, exit 1 (P18/P19).
   - CLI flags can only force True; there is no `--no-dry-run`.
10. **The run_test.py default PROJECT_ROOT points outside the repo.** The default is `Path(__file__).parent.parent` (RT:748-750). `init-test-harness` copies the files *into* the target directory (default `.`), so the root resolves to the **parent of the repo**, and `test-runs/` lands outside the repo. VERIFIED (scaffold into `th/repo`, then `project_root=/tmp/lane-b/th`, `/tmp/lane-b/th/test-runs` created). CONTRACT.md says "Copy this directory into the repository". The scaffold copies the files, not a directory. DISCREPANCY.
11. **`self-check` writes into the installed package directory.** It writes `self_check_report.md/json` and `.python_doctor/` (state DB) into the directory holding `doctor/core.py` (D:2125-2126), which is site-packages when installed. VERIFIED on the /tmp copy. On a read-only package directory, it warns about state, then fails with exit 4 unless `-o` is given (VERIFIED with `chmod a-w`).
12. **`somnus-debug doctor` needs PyYAML.** `cli.py:56` imports the pycache module at import time, so `somnus-debug doctor`/`structure` fail without PyYAML. Only `somnus-doctor` is stdlib-only. VERIFIED (`sys.modules['yaml']=None`: `import somnus_debug.cli` raises, `doctor.core` imports fine). The README "doctor and structure are stdlib-only" holds only for the per-tool scripts.

---

## 2. Precedence model per tool

### 2.1 doctor (scan / history / rollback / self-check)

Layers, lowest to highest:

| Layer | Source | Notes |
|---|---|---|
| L0 in-code | `DEFAULT_CONFIG_DATA` D:451-502 | Always the base. Only this layer is read at runtime. |
| L1 file | `-c PATH` (`.yaml`/`.yml`/`.json`, case-insensitive suffix) D:796-814 | `deep_merge` D:726-734: nested dicts (only `severity_levels`) are merged; **lists and scalars replace** the default wholesale. |
| L2 CLI | `project_root`, `-o`, `--json-output`, `--no-state`, `-v` | None of these overlap a config key except output path vs `report_basename` (CLI wins). There is no CLI override for any config key, and `max_workers` has no `-j` (QUICKSTART says so). |
| env | none read by doctor | Results still depend on the interpreter's `sys.path` (see 5.6). |

There is no auto-discovery layer, no `pyproject.toml` section, and no user-level config. `history` and `rollback` take their own `-c`. They do not remember the config used at scan time, so a scan run with a custom `state_dir` plus `history` without `-c` gives a silent "No recorded runs found." and creates an empty `.python_doctor/` (VERIFIED, O10/O8).

`-c` and `-o`/`--json-output` relative paths resolve against **CWD** (D:2063, 2081). `state_dir` resolves against **project_root** (D:1923). The default markdown goes to **project_root** (D:1958). `production_doctor.log` goes to **CWD** (D:2181).

### 2.2 Three default layers: do they agree?

| Layer | Location | Used at runtime? |
|---|---|---|
| `DEFAULT_CONFIG_DATA` | D:451-502 | Yes, always |
| `ConfigManager.default_yaml()` | D:853-925 | Only as `init-config` output |
| `doctor/default_config.yaml` | packaged; lines 33-99 | **No**: read only by `tests/test_cli_smoke.py:90,117` |
| repo-root `python_doctor.yaml` | root | **No**: nothing references it |

VERIFIED: parsed `default_yaml()` == `DEFAULT_CONFIG_DATA` == parsed `default_config.yaml` (doctor parser and PyYAML both). The `default_yaml()` text is byte-identical to the body of `default_config.yaml` after its metadata header. **The winning value for every key is always `DEFAULT_CONFIG_DATA` unless `-c` is passed**, and the three layers do not currently disagree.

The root `python_doctor.yaml` differs only in `include_patterns` (`tools/*.py`, `tools/native/speech/*.py`, `test/*.py`, `test/speech/*.py`) and `ignore_patterns` (drops `.hg`, `.mypy_cache`, `.pytest_cache`, `.ruff_cache`, `.tox`, `env`, `node_modules`, `build`, `dist`; adds `potential-project-developments/*`, `reports/*`, `test/*/runs/*`). Passed with `-c` on another repo, it yields a 0-file scan with exit 0 (MANUAL 7.1 acknowledges this). The QUICKSTART claim that the generated file has "comments" is false: the output has none. DISCREPANCY.

### 2.3 pycache-clean

L0 dataclass defaults (PC:160-167) < L1 YAML via `--config` (default `config.yaml` **in CWD**, PC:340/351; the module docstring says "in the same directory", a DISCREPANCY) < L2 CLI flags, applied only when set and only toward True or toward an int (PC:357-364). Relative `roots`/`log_file` resolve against **CWD**, not the config file's directory (VERIFIED P23: `--config sub/config.yaml` with `roots: [../tree]` resolved to `/tmp/lane-b/tree`). There is no `--root` flag; `roots` must come from YAML (MANUAL 5 says so). `$VARS` are not expanded, only `~` (PC:184; VERIFIED P15), which contradicts the module docstring ("Environment variables and ~ are expanded").

### 2.4 structure, init-test-harness, cli

- **structure** (ST:290-320) and **init-test-harness** (SC:91-109) are CLI-only, with no config file or env.
- **cli** routes `argv[0]`. `-h`/`--help`/`-V`/`--version` are honored only in first position (cli.py:111-116).
- Exit codes:
  - unknown command → 2
  - `SystemExit(int)` → that int
  - a tool returning `None` → 0, so pycache success is always 0
  - other exceptions propagate (VERIFIED: structure on a latin-1 file gives a `UnicodeDecodeError` traceback, exit 1, because ST:333 catches only `OSError`/`SyntaxError`).

### 2.5 run_test.py (template)

| Variable | Precedence | Empty-string behavior |
|---|---|---|
| `PROJECT_ROOT` | env > `Path(__file__).parent.parent` | `PROJECT_ROOT=""` → `Path("")` → CWD (VERIFIED R3) |
| `SINGLE_TEST_OUTPUT_DIR` | env (non-empty) > `<project_root>/test-runs` | `""` → default (VERIFIED R3) |

Both variables are documented only in a comment inside the template (RT:188-192), not in MANUAL. The shipped `execute_test` runs `cargo metadata` for a gp-cli project, so the template is FAIL (exit 1) out of the box (VERIFIED R1/R2).

---

## 3. The doctor YAML mini-parser contract (D:596-723)

**Accepted subset:**
- Block mappings with `key: value`, where the key is everything before the first `:` (D:704).
- Block sequences, `- scalar` only.
- Inline lists `[a, b]` split on `,` with no quote awareness (D:641-645).
- Scalars:
  - `true`/`false` (case-insensitive)
  - `null`/`none`/`~` (case-insensitive)
  - quoted strings via `ast.literal_eval`
  - ints matching `[-+]?\d+`
  - floats matching `[-+]?\d+\.\d+`
  - anything else is a plain string
- `#` comments outside quotes.
- Blank lines.
- Indentation by spaces, with strict equal-indent siblings.

**Errors it raises (ConfigurationError → exit 4):**
- an empty value at end of file or before a sibling (`a:` → "Expected an indented child block")
- a block list of mappings (`- b: 1\n  c: 2`)
- `-` items with a nested block
- `---` document markers
- block scalars `|`/`>`
- tab indentation
- PyYAML's compact form (`a:\n- x`, a sequence at the key's indent)
- a list root
- `-x` without a space
- inconsistent indentation

**Silent mis-parses (no error, wrong value). VERIFIED in `experiments/yaml_probe.out`:**

| Case | Input | doctor | YAML (PyYAML) |
|---|---|---|---|
| Y04 | `yes/no/on/off` | strings | bools → bool keys then fail validation (exit 4), not silent for bool keys |
| Y06/Y48 | `none`, `None` | `None` | `'none'`/`'None'` strings → **breaks `severity_exit_level: none`** |
| Y10 | `x#y` | `'x'` (truncated at `#` with no space) | `'x#y'` |
| Y12 | `["a,b", "c"]` | `['"a', 'b"', 'c']` | `['a,b','c']` (a glob with a comma is corrupted) |
| Y13 | `{b: 1}` | string `'{b: 1}'` | mapping → `severity_levels: {}` fails ("must be a mapping") |
| Y14 | `[[1,2],3]` | `['[1','2]',3]` | nested list |
| Y18 | `"a b": 1` | key `'"a b"'` (quotes kept) | `'a b'` (a quoted key never matches a real key, so it is silently ignored) |
| Y23 | `&x 1` / `*x` | literal strings | anchors resolved |
| Y26 | `'it''s'` | `'its'` (Python implicit concatenation) | `"it's"` |
| Y28 | `010`, `0x1F` | `10`, `'0x1F'` | `8`, `31` |
| Y29 | `007` | `7` | `7` |
| Y36 | `"x'` | string `"x'` | ScannerError |
| Y38 | `[1,,2]` | `[1,2]` | ParserError |
| Y43 | UTF-8 BOM | key `'\ufeffa'` (first key silently unknown) | `'a'` |
| Y44 | `"\q"` | `'\\q'` | ScannerError |
| Y46/Y47 | `.inf`, `1_000` | strings | float / 1000 |
| Y25 | duplicate keys | last wins, no warning | same |

Validation layer (D:737-782): bools must be real bools; ints must be ints ≥ minimum (bools rejected); strings must be non-empty after strip; lists must be lists of non-empty strings (an **empty list is valid**). `severity_levels` values must be lowercase `critical|serious|minor|info`. **Unknown top-level keys and unknown severity categories are accepted silently** (VERIFIED C10: the typo `detect_silent_failure: false` had no effect; C18). `schema_version` is any non-empty string, never compared (C20 `"99.9"` accepted; C21 int `3` → exit 4). JSON configs share the same merge and validation (VERIFIED: object OK; list root → exit 4; `null` value → exit 4).

---

## 4. Absent / None / empty / false / 0 / invalid matrix (doctor, VERIFIED)

| Input | Result |
|---|---|
| key absent | default from L0 (merge) |
| `key:` (empty) | parse error, exit 4 |
| `key: null`/`none`/`~` | None → validation error, exit 4 (even for string keys) |
| `include_patterns: []` | 0 files scanned, **exit 0** (C11), so a silent pass in CI |
| `ignore_patterns: []` | all defaults gone (VCS/venv/node_modules scanned); SOURCE-CONFIRMED by merge semantics |
| `max_workers: 0`, `"4"` | exit 4 (C13/C14) |
| `min_*: 0` | exit 4 (min 1) |
| `state_dir: ""` / `report_basename: "  "` | exit 4 (C24/C26) |
| `state_dir: /abs` or `../x` | accepted; state written outside the project (S1/S2) |
| `reports_dir: ../../R2`, `report_basename: deep/dir/name` | accepted; subdirectories created, reports written outside the state root (S3) |
| `severity_exit_level: CRITICAL` / `off` | exit 4 (C06/C07) |
| `severity_levels: {stubs: SERIOUS}` | exit 4 (C19) |
| config path missing / `.toml` / no extension | exit 4 (L3/L4) |

---

## 5. Implicit behaviors

1. **`production_doctor.log` on every doctor call, `--help` included**, in CWD, append mode (D:2179-2181, D:2186). VERIFIED (L1). On success it stays empty: doctor logs only on error (D:2192, 2196).
2. **`-v`/`--verbose` do nothing.** `setup_logging` checks for the literal string `"--verbose"` in argv (D:2186), so `-v` never even sets DEBUG. And no DEBUG records exist. VERIFIED (both give a 0-line log). `history --verbose` → argparse exit 2.
3. **Reports land in the scanned project by default:** `<root>/production_doctor_report.{md,json}` plus `<root>/.python_doctor/{state.sqlite3,reports/<run_id>/…,reports/latest.*}` (VERIFIED O4). The JSON is always written, which contradicts QUICKSTART's "if requested".
4. **`-o report.json` collision.** The md path and the JSON path become the same file, and the JSON overwrites the markdown (D:1958-1959; VERIFIED O1). `-o rep` (no suffix) → `rep` + `rep.json`.
5. **Read-only commands write.** `history`/`rollback` call `initialize()`, which creates the state dir and DB (D:1983, 1993; VERIFIED O8).
6. **Environment-dependent `missing_imports`.** Imports resolve via `sys.stdlib_module_names` plus `importlib.util.find_spec` in the *running* interpreter (D:1001, D:1050-1055). `python -m somnus_debug.cli` puts CWD on `sys.path`, while a console script or `python -P` does not. VERIFIED: the same project gave 0 issues under `python -m` with `zzlocalonly.py` in CWD, and `missing_imports` (exit 1) under `python -P`. `PYTHONPATH` and the active venv change results the same way.
7. **Legacy argv normalization** (D:2165-2176):
   - no args → `scan .`
   - a leading flag → `scan . <flags>`
   - a bare path → `scan <path>`
   - `doctor --version` → `scan . --version` → exit 2

   A directory named after a subcommand (`history`, etc.) can't be scanned in bare form.
8. **Exit-code overlap.** Gate breaches give 1 or 2. Argparse usage errors also give 2 (VERIFIED L5). DoctorError → 4, unclassified → 5. MANUAL says "0 / non-zero". With the `critical` gate, a CI job can't tell a critical finding from a typo'd flag.
9. **Discovery semantics:**
   - `include_patterns` are tested against both the relative path and the basename (D:952).
   - `*` crosses `/`.
   - Matching is case-sensitive on POSIX (`Build/k.py` was not ignored by `build/*`; VERIFIED). `fnmatch.fnmatch` uses `normcase`, so on Windows it becomes case-insensitive. SOURCE-CONFIRMED, platform behavior not tested.
   - Directory pruning uses `should_ignore` only (D:974).
10. **Severity fallback.** A category missing from `severity_levels` gets MINOR (D:794). Remapping a category to `info` takes it out of every gate except `info` (VERIFIED C16: 4→2 serious).
11. **The pycache scan is iterative.** It calls `scandir` before the depth check (PC:226-234), so directories one level past `max_depth` are still listed. VERIFIED: P4 `--max-depth 0` deleted only `tree/z.pyo` (root-level files). `--max-depth 1` deleted 2 dirs + 3 files. A negative value processes nothing (P5).
12. **pycache symlinks.** With `follow_symlinks` false, symlinked dirs and files are neither traversed nor deleted (PC:240, 252-255). SOURCE-CONFIRMED.
13. **init-test-harness:**
    - creates missing target parents (SC:83)
    - a target that is a file → misleading "File exists" error, exit 1 (VERIFIED H4)
    - `--no-contract` skips the existence check for `CONTRACT.md` (SC:71-73; VERIFIED H3)
    - there is no standalone console script for it (pyproject `[project.scripts]`)

---

## 6. Hidden or undocumented options and constants

1. **Undocumented config keys.** None of these appear in any doc: `max_report_evidence_lines`, `markdown_include_css`, `state_dir`, `reports_dir`, `report_basename`, `check_private_functions`, `check_nested_functions`. Nor do the gate values `info`/`none`.
2. **Categories with no toggle.** These can only be re-severitied, never disabled: `broad_exceptions`, `missing_imports`, `todos`, `stubs`, `placeholder_returns`, `duplicate_definitions`, `complexity`, `suspicious_short_*`, `incomplete_methods`, `syntax_errors`, `tokenization_errors`.
3. **Hard-coded vocabularies:**
   - `TODO_PATTERNS` (D:504-511): TODO, FIXME, HACK, XXX, TEMP, WIP, case-insensitive word match in comments only.
   - `PLACEHOLDER_CONSTANTS` (D:513).
   - `SECURITY_CALLS` (D:514): eval, exec, compile, pickle.load(s), subprocess.call/run/Popen, os.system, os.popen, yaml.load, marshal.load(s). Matched by dotted name, so `from subprocess import run; run()` is not caught. SOURCE-CONFIRMED by name matching, not tested.
4. **Cycle search limits.** It stops after 100 cycles, with DFS path depth < 30 (D:1642, 1653), and truncates silently.
5. **Score.** `100 − 20·crit − 8·serious − 2·minor − info`, floored at 0 (D:1772).
6. **Run ID.** `%Y%m%dT%H%M%SZ`, one-second resolution (D:82). Two state-enabled scans of the same root in one second share a run_id, and `INSERT OR REPLACE` overwrites the earlier one. SOURCE-CONFIRMED, not reproduced.
7. **structure.**
   - `--update-doc` behaves exactly like `-o`: it doesn't require an existing file and creates parent dirs (VERIFIED T1). It is mutually exclusive with `-o` (T2, exit 2).
   - `--source-label` also becomes the SyntaxError filename; the heading shows the basename only (T3).
   - `type_comments=True` is hard-coded in src (ST:210) but absent in the root duplicate. VERIFIED: a file with a misplaced `# type: str` comment gives exit 2 in src and exit 0 in the root `analyze_python_structure.py`. That contradicts STATE.md's "fixed 2026-11-05".
8. **pycache module docstring.** It has an invalid escape (PC:64) that emits a `SyntaxWarning` on first compile under py3.12 (seen on the first run in this lane).

---

## 7. Configuration combinations with materially different outcomes

| Combination | Outcome | Evidence |
|---|---|---|
| `init-config` then `scan .` (no `-c`) | config ignored; the defaults happen to equal it, so the mistake is invisible until the user edits the file | VERIFIED E1/E2 |
| edited `python_doctor.yaml` + `scan .` | edits silently ignored | VERIFIED E1 |
| `severity_exit_level: none` vs `"none"` | exit 4 vs exit 0 | VERIFIED |
| `include_patterns: []` or Somnus root yaml on another repo + CI | 0 files, exit 0, so a false green | VERIFIED C11 |
| `ignore_functions: [f]` | suppresses f's security/exception findings | VERIFIED C23 |
| `check_nested_functions: false` | suppresses everything inside nested defs | VERIFIED |
| custom `state_dir` + `history` without `-c` | empty history + stray `.python_doctor/` | VERIFIED O10 |
| `-o X.json` | markdown lost | VERIFIED O1 |
| `self-check` installed read-only | exit 4 unless `-o` | VERIFIED |
| `python -m` vs console script | different `missing_imports` | VERIFIED |
| pycache: unknown key + `log_file`/`verbose` | no log output at all | VERIFIED P10 |
| pycache: `dry_run: no` | live deletion | VERIFIED P8b |
| pycache: `dry_run: "false"` | dry run despite the log saying false | VERIFIED P8 |
| pycache: MANUAL exclude globs | excluded trees cleaned anyway | VERIFIED P2 |
| scaffold at repo root + run_test default | artifacts written to the repo's parent | VERIFIED R1 |

---

## 8. Root duplicate differences relevant to configuration

The `diff` of repo-root scripts against `src/` (VERIFIED) shows:

- **doctor** (`python_production_doctor.py:2066-2079`): no SQLite fallback. `previous_file_index()` errors propagate (StateStoreError → exit 4) instead of warning and going stateless. Otherwise identical apart from the metadata ids.
- **structure** (`analyze_python_structure.py:210`): no `type_comments=True`.
- **pycache_cleaner.py** and **run_test.py**: identical apart from metadata ids.
- **docs/CONTRACT.md** vs the templates copy: metadata ids only.

---

## 9. Doc-status summary vs README.md, docs/MANUAL.md, docs/Python_Doctor_QUICKSTART.md

**Contradictory:**
- `--json-output` "if requested"
- QUICKSTART's "generated file … with comments"
- the pycache module docstring on config location and env expansion
- the MANUAL 5.1 `exclude` example
- README "Dry-run by default via `--dry-run`": a dry run happens only when `--dry-run` or `dry_run: true` is set
- README's "stdlib-only doctor" (via the dispatcher)
- STATE.md's type_comments fix
- the run_test PROJECT_ROOT default vs scaffold placement
- `detect_test_gaps` documented as a working toggle
- MANUAL include-glob advice (`src/**/*.py`)
- the README quickstart line `structure … -o` prints "Class Index … written to CORE_INDEX.md": structure prints nothing on `-o` (VERIFIED T1)

**Partial:**
- exit codes (only 0 / non-zero documented)
- the `-v` effect
- legacy argv forms
- `severity_levels` semantics
- unknown-key handling

**Missing:**
- no auto-discovery
- the `none`/`info` gates
- 7 config keys
- env-dependent import resolution
- self-check write location
- history/rollback side effects
- `PROJECT_ROOT`/`SINGLE_TEST_OUTPUT_DIR` (template comment only)

---

## 10. Not verified / limits

- Windows behavior: `fnmatch` case-folding, and drive letters. The pycache docstring's Windows `\\?\` long-path normalization claim (PC:64) has no implementing code; the only matches for "long path" are docstring lines PC:42 and PC:64. SOURCE-CONFIRMED absence; DISCREPANCY.
- PyPI 0.1.0 sdist/wheel comparison: not done in this lane.
- Run-ID collision within one second: not reproduced.
- `follow_symlinks: true` loops: not tested.
- Installed console scripts (`somnus-doctor` etc.) were not exercised in a venv. Behavior was inferred from entry points plus `python -P`, which reproduces the no-CWD-on-sys.path condition.
