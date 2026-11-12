# File-based configuration

This page documents every configuration file the toolkit reads or writes: the doctor YAML/JSON config and the exact contract of doctor's own YAML parser, the pycache-clean YAML config, the fieldkit's generated files and `dispositions.json`, and the reference files that look like configuration but are never read.

## Files at a glance

This section lists each file, who reads it, and how.

| File | Read by | Parser | Located by | Evidence |
|---|---|---|---|---|
| any `*.yaml` / `*.yml` passed with `doctor ... -c` | doctor scan, history, rollback, self-check | `MinimalYamlParser` (stdlib, own subset) | `-c` only, relative to CWD | [VERIFIED W3 E1, E5; `src/somnus_debug/doctor/core.py:812-813`] |
| any `*.json` passed with `-c` | same | `json.loads`; root must be an object | `-c` only | [VERIFIED W3 E6a/E6b; `core.py:802-811`] |
| `python_doctor.yaml` written by `init-config` | nobody, until passed with `-c` | n/a | default `-o` name | [VERIFIED W3 E1, E8] |
| `src/somnus_debug/doctor/default_config.yaml` | `tests/test_cli_smoke.py` only | PyYAML in the test | n/a | [SOURCE-CONFIRMED `tests/test_cli_smoke.py:90,117`] |
| repo-root `python_doctor.yaml` | nothing at runtime; fieldkit onboard adopts a root config of this name | n/a | n/a | [VERIFIED W3 E8f; lane F OB-5] |
| pycache `config.yaml` (or `--config PATH`) | pycache-clean | PyYAML `safe_load`, values applied with `setattr` | `--config`, default `./config.yaml` | [VERIFIED W3 P1-P19; `pycache_cleaner/core.py:170-180,351`] |
| `.somnus-debug/python_doctor.yaml` | doctor via `-c` (onboard's commands pass it) | doctor parser | written by `onboard.py --apply` | [VERIFIED W3 OB3] |
| `.somnus-debug/pycache.yaml` | pycache-clean via `--config` | PyYAML | written by `onboard.py --apply` | [VERIFIED W3 OB3] |
| `dispositions.json` | `delta.py --dispositions` | `json.loads`; root must be a list | flag only | [VERIFIED W3 DL2/DL3; `delta.py:128-144`] |
| `run_test.py` (`TEST_NAME`, `execute_test()`) | the harness itself | Python source you edit | scaffolded by `init-test-harness` | [SOURCE-CONFIRMED `run_test.py:195-198`] |

## doctor config files

This section explains how a doctor config file is loaded, merged, and validated.

### Loading

1. The path from `-c` is resolved against CWD; a missing file is `ConfigurationError` (exit 4) [VERIFIED W3 E5b].
2. Suffix decides the parser, case-insensitively: `.json` -> `json.loads`; `.yaml`/`.yml` -> `MinimalYamlParser`; anything else, exit 4 [VERIFIED W3 E6c/E6d; `core.py:802-814`].
3. The parsed mapping is merged over `DEFAULT_CONFIG_DATA` (see [precedence.md](precedence.md)).
4. `_validate` builds the frozen `DoctorConfig` [SOURCE-CONFIRMED `core.py:816-851`].
5. `config_hash` = hash of the merged raw mapping, unknown keys included [SOURCE-CONFIRMED `core.py:790`].

PyYAML is never used for doctor configs, which is why `somnus-doctor` can stay stdlib-only [SOURCE-CONFIRMED `core.py:596-723`; VERIFIED W3 NOYAML1]. The flip side: doctor does not accept everything PyYAML accepts, and accepts a few things PyYAML rejects.

### Validation rules

| Kind | Keys | Accepted | Rejected (exit 4) | Evidence |
|---|---|---|---|---|
| bool | `check_*`, `require_*`, `detect_*`, `markdown_include_css` | `true`/`false` in any case | `yes`, `no`, `on`, `off`, `1`, `"true"`, null | [VERIFIED W3 E7d; `core.py:737-742`] |
| int with minimum 1 | `min_*`, `max_cyclomatic_complexity`, `max_report_evidence_lines`, `max_workers` | ints >= 1 | `0`, negatives, `"4"`, bools, `1_000` | [VERIFIED W3 M5/M6; `core.py:745-750`] |
| non-empty string | `schema_version`, `state_dir`, `reports_dir`, `report_basename`, `severity_exit_level` | any string with a non-space character (stripped) | `""`, `"  "`, null, numbers | [VERIFIED lane B C20/C21/C24/C26; `core.py:753-758`] |
| gate | `severity_exit_level` | `critical`, `serious`, `minor`, `info`, `none` (exact, lowercase, after strip) | `CRITICAL`, `off`, unquoted `none` | [VERIFIED W3 E2/E3; lane B C06/C07; `core.py:818-820`] |
| list of strings | `include_patterns`, `ignore_patterns`, `ignore_functions`, `ignore_classes` | lists of non-empty strings; `[]` | a bare string, null, list containing non-strings or empties | [SOURCE-CONFIRMED `core.py:761-766`] |
| severity map | `severity_levels` | mapping of any string category to `critical`/`serious`/`minor`/`info` | non-mapping, upper-case values | [VERIFIED lane B C19; `core.py:769-779`] |
| anything else | unknown top-level keys and unknown categories | silently accepted, no effect | never | [VERIFIED W3 E7a; lane B C18] |

### The mini-YAML parser contract

This subsection states precisely what `MinimalYamlParser` (`src/somnus_debug/doctor/core.py:596-723`) accepts and how it reads it.

**Line preparation** (`core.py:670-679`): each line has comments stripped by `strip_yaml_comment` (a `#` outside single or double quotes ends the line, with or without a preceding space; backslash escapes are honored only inside double quotes), trailing whitespace removed, blank lines dropped. Indentation is the count of leading spaces; tabs are not indentation. Lines are read as UTF-8; a BOM is not removed.

**Structure** (`core.py:681-723`):

- A block is either a mapping or a sequence; mixing `key:` lines and `- ` items at one indent is an error.
- A mapping line is split at the **first** `:`; the key is stripped but quotes in it are kept.
- An empty value after `key:` requires an indented child block on the next line; otherwise "Expected an indented child block".
- A sequence item must start with `- ` (dash and space). `- value` is a scalar; `-` with a nested block, `- key: value` lists of mappings, and `-x` are errors or mis-reads.
- Sibling lines must share exactly one indent; deeper or shallower lines than expected raise "Unexpected indentation" or end the block.
- The root must be a mapping; an empty or comment-only file parses as `{}`.

**Scalars** (`parse_yaml_scalar`, `core.py:619-643`), tested in this order:

| Order | Rule | Result |
|---|---|---|
| 1 | empty text | `""` |
| 2 | `true` / `false`, any case | bool |
| 3 | `null` / `none` / `~`, any case | `None` (note: YAML 1.1 treats `None`/`none` as strings) |
| 4 | starts and ends with the same quote | `ast.literal_eval` (Python string rules); syntax error -> exit 4 |
| 5 | starts with `[` and ends with `]` | split on every `,` (not quote-aware), each part parsed recursively, empty parts dropped |
| 6 | matches `[-+]?\d+` | int (leading zeros allowed, decimal) |
| 7 | matches `[-+]?\d+\.\d+` | float |
| 8 | anything else | the text as a string (flow mappings, anchors, `.inf`, `0x1F`, `1_000`, `1e3` included) |

**Errors** are `ConfigurationError` with the path and line number; the CLI prints the context and exits 4 [VERIFIED W3 E2 output shows `"key"`/`"value"` context].

### Doctor parser versus PyYAML: 58 inputs

Each input was written to a temporary `.yaml` file and parsed by `MinimalYamlParser(path).parse()` and by `yaml.safe_load(text)`. Y01-Y48 are lane B's cases (re-run by W3 with byte-identical output); Y49-Y58 were added by W3. 24 of 58 agree. "SILENT" marks inputs where doctor returns a wrong value without any error, the cases that matter most; "loud" marks inputs doctor rejects with exit 4.

Executed: yes (`/tmp/w3/probe.py`, Python 3.12.15, PyYAML 6.0.2; lane B original: [`yaml_probe.py`](../_evidence/agent-findings/lane-b-config/experiments/yaml_probe.py), [`yaml_probe.out`](../_evidence/agent-findings/lane-b-config/experiments/yaml_probe.out)). Temporary paths in error contexts are elided. In the input column `\n` is a line break, `\t` a tab, `\r` a carriage return, and `<BOM>` a U+FEFF byte-order mark; Y27 and Y44 contain literal backslashes.

| ID | Input (file text) | Doctor `MinimalYamlParser` | PyYAML `safe_load` | Agree | Consequence for a doctor config |
|---|---|---|---|---|---|
| Y01 | `a: 5` | `{'a': 5}` | `{'a': 5}` | yes | - |
| Y02 | `a: 5.0` | `{'a': 5.0}` | `{'a': 5.0}` | yes | - |
| Y03 | `a: 1e3` | `{'a': '1e3'}` | `{'a': '1e3'}` | yes | - |
| Y04 | `a: yes\nb: no\nc: on\nd: off` | `{'a': 'yes', 'b': 'no', 'c': 'on', 'd': 'off'}` | `{'a': True, 'b': False, 'c': True, 'd': False}` | no | bool keys then fail validation (exit 4): loud, not silent |
| Y05 | `a: True\nb: FALSE` | `{'a': True, 'b': False}` | `{'a': True, 'b': False}` | yes | - |
| Y06 | `a: null\nb: ~\nc: None\nd: NULL` | `{'a': None, 'b': None, 'c': None, 'd': None}` | `{'a': None, 'b': None, 'c': 'None', 'd': None}` | no | `None`: doctor null, PyYAML string |
| Y07 | `a:` | `ConfigurationError: Expected an indented child block. {"line": 1}` | `{'a': None}` | no | loud: empty value is an error |
| Y08 | `a:\nb: 1` | `ConfigurationError: Expected an indented child block. {"line": 1}` | `{'a': None, 'b': 1}` | no | loud |
| Y09 | `a: "x # y"\nb: x # comment` | `{'a': 'x # y', 'b': 'x'}` | `{'a': 'x # y', 'b': 'x'}` | yes | - |
| Y10 | `a: x#y` | `{'a': 'x'}` | `{'a': 'x#y'}` | no | SILENT: value truncated at `#` even without a preceding space |
| Y11 | `a: ["*.py", "src/*.py"]` | `{'a': ['*.py', 'src/*.py']}` | `{'a': ['*.py', 'src/*.py']}` | yes | - |
| Y12 | `a: ["a,b", "c"]` | `{'a': ['"a', 'b"', 'c']}` | `{'a': ['a,b', 'c']}` | no | SILENT: a glob containing a comma is split and keeps its quote characters |
| Y13 | `a: {b: 1}` | `{'a': '{b: 1}'}` | `{'a': {'b': 1}}` | no | flow mapping kept as a string; for `severity_levels` it fails validation (exit 4) |
| Y14 | `a: [[1,2],3]` | `{'a': ['[1', '2]', 3]}` | `{'a': [[1, 2], 3]}` | no | SILENT: nested list flattened into strings |
| Y15 | `a:\n  - b: 1\n    c: 2` | `ConfigurationError: Unexpected indentation. {"line": 3, "indent": 4, "expected": 2}` | `{'a': [{'b': 1, 'c': 2}]}` | no | loud: lists of mappings unsupported |
| Y16 | `a:\n  -\n    b: 1` | `ConfigurationError: Expected key followed by colon. {"line": 2, "content": "-"}` | `{'a': [{'b': 1}]}` | no | loud |
| Y17 | `a: http://x:80/y` | `{'a': 'http://x:80/y'}` | `{'a': 'http://x:80/y'}` | yes | - |
| Y18 | `"a b": 1` | `{'"a b"': 1}` | `{'a b': 1}` | no | SILENT: quoted key keeps its quotes, so it never matches a real key and is ignored |
| Y19 | `a:\n\t- x` | `ConfigurationError: Expected an indented child block. {"line": 1}` | `ScannerError: while scanning for the next token` | no | loud: tabs not indentation |
| Y20 | `a:\n    - x\n  - y` | `ConfigurationError: Unexpected indentation. {"line": 3, "indent": 2, "expected": 0}` | `ParserError: while parsing a block mapping` | no | - |
| Y21 | `a:\n  -x` | `ConfigurationError: Expected key followed by colon. {"line": 2, "content": "-x"}` | `{'a': '-x'}` | no | loud |
| Y22 | `a: \|\n  line1\n  line2` | `ConfigurationError: Unexpected indentation. {"line": 2, "indent": 2, "expected": 0}` | `{'a': 'line1\nline2'}` | no | loud: block scalars unsupported |
| Y23 | `a: &x 1\nb: *x` | `{'a': '&x 1', 'b': '*x'}` | `{'a': 1, 'b': 1}` | no | SILENT: anchors and aliases are literal strings |
| Y24 | `---\na: 1` | `ConfigurationError: Expected key followed by colon. {"line": 1, "content": "---"}` | `{'a': 1}` | no | loud: `---` rejected |
| Y25 | `a: 1\na: 2` | `{'a': 2}` | `{'a': 2}` | yes | last wins, no warning (both parsers) |
| Y26 | `a: 'it''s'` | `{'a': 'its'}` | `{'a': "it's"}` | no | SILENT: YAML `''` escape becomes Python implicit concatenation |
| Y27 | `a: "x\ny"` (backslash and n, not a line break) | `{'a': 'x\ny'}` | `{'a': 'x\ny'}` | yes | - |
| Y28 | `a: 0o17\nb: 0x1F\nc: 010` | `{'a': '0o17', 'b': '0x1F', 'c': 10}` | `{'a': '0o17', 'b': 31, 'c': 8}` | no | SILENT: `010` is decimal 10 (PyYAML: octal 8); `0x1F` stays a string |
| Y29 | `a: 007` | `{'a': 7}` | `{'a': 7}` | yes | - |
| Y30 | `- a\n- b` | `ConfigurationError: Configuration root must be a mapping. {"root_type": "list"}` | `['a', 'b']` | no | loud: root must be a mapping |
| Y31 | `` | `{}` | `None` | yes | - |
| Y32 | `# hi\n# there` | `{}` | `None` | yes | - |
| Y33 | `a: "5"` | `{'a': '5'}` | `{'a': '5'}` | yes | - |
| Y34 | `a:\n- x\n- y` | `ConfigurationError: Expected an indented child block. {"line": 1}` | `{'a': ['x', 'y']}` | no | loud: PyYAML's compact sequence style rejected |
| Y35 | `a: 5   ` | `{'a': 5}` | `{'a': 5}` | yes | - |
| Y36 | `a: "x'` | `{'a': '"x\''}` | `ScannerError: while scanning a quoted scalar` | no | SILENT: mismatched quotes accepted as a string |
| Y37 | `a: [null, ~, true]` | `{'a': [None, None, True]}` | `{'a': [None, None, True]}` | yes | - |
| Y38 | `a: [1,,2]` | `{'a': [1, 2]}` | `ParserError: while parsing a flow node` | no | SILENT: empty item dropped (PyYAML errors) |
| Y39 | `a: -1` | `{'a': -1}` | `{'a': -1}` | yes | - |
| Y40 | `a:\n  - -1` | `{'a': [-1]}` | `{'a': [-1]}` | yes | - |
| Y41 | `a` | `ConfigurationError: Expected key followed by colon. {"line": 1, "content": "a"}` | `a` | no | loud |
| Y42 | `a: 1\r\nb: 2\r\n` | `{'a': 1, 'b': 2}` | `{'a': 1, 'b': 2}` | yes | - |
| Y43 | `<BOM>a: 1` | `{'\ufeffa': 1}` | `{'a': 1}` | no | SILENT: BOM becomes part of the first key, which is then unknown |
| Y44 | `a: "\q"` | `{'a': '\\q'}` | `ScannerError: while scanning a double-quoted scalar` | no | SILENT: Python escape rules, not YAML's |
| Y45 | `a: 'x' # c` | `{'a': 'x'}` | `{'a': 'x'}` | yes | - |
| Y46 | `a: .inf\nb: .nan` | `{'a': '.inf', 'b': '.nan'}` | `{'a': inf, 'b': nan}` | no | strings, not floats |
| Y47 | `a: 1_000` | `{'a': '1_000'}` | `{'a': 1000}` | no | string, not int: an int key would fail validation (exit 4) |
| Y48 | `a: none` | `{'a': None}` | `{'a': 'none'}` | no | SILENT for the gate: `severity_exit_level: none` becomes null, exit 4 |
| Y49 | `a: "x" "y"` | `{'a': 'xy'}` | `ParserError: while parsing a block mapping` | no | SILENT: `ast.literal_eval` concatenates adjacent quoted strings |
| Y50 | `a: ""` | `{'a': ''}` | `{'a': ''}` | yes | empty string; any string key then fails `require_str` (exit 4) |
| Y51 | `a: b: c` | `{'a': 'b: c'}` | `ScannerError: mapping values are not allowed here` | no | SILENT: first `:` splits; PyYAML errors |
| Y52 | `a: [ ]` | `{'a': []}` | `{'a': []}` | yes | - |
| Y53 | `a:\n  -` | `ConfigurationError: Expected key followed by colon. {"line": 2, "content": "-"}` | `{'a': [None]}` | no | loud |
| Y54 | `a: "none"` | `{'a': 'none'}` | `{'a': 'none'}` | yes | - |
| Y55 | `a: 'x#y'` | `{'a': 'x#y'}` | `{'a': 'x#y'}` | yes | - |
| Y56 | `severity_levels: {stubs: info}` | `{'severity_levels': '{stubs: info}'}` | `{'severity_levels': {'stubs': 'info'}}` | no | string, then `severity_levels must be a mapping` (exit 4) |
| Y57 | `a : 1` | `{'a': 1}` | `{'a': 1}` | yes | - |
| Y58 | `a:\t1` | `{'a': 1}` | `ScannerError: while scanning for the next token` | no | accepted (PyYAML rejects the tab) |

What the table means in practice [VERIFIED by the rows cited]:

- Write every string value in double quotes, as `init-config` does. That avoids Y06/Y48 (`none`), Y10 (`#`), Y23, Y28, Y46-Y47.
- Use block lists (`- "glob"` per line) for patterns. Flow lists break on commas inside quotes (Y12).
- Never quote keys (Y18) and save files without a BOM (Y43): both produce an unknown key that is silently ignored.
- Use `true`/`false`, never `yes`/`no` (Y04).
- Do not use `---`, anchors, block scalars, flow mappings, or lists of mappings; doctor's config schema never needs them.
- A file that PyYAML loads is not guaranteed to load in doctor, and vice versa (Y34, Y51, Y58).

[D-04](../DISCOVERY-LEDGER.md#d-04), [D-03](../DISCOVERY-LEDGER.md#d-03)

### JSON configs

JSON configs share merge and validation with YAML. Differences: real JSON types (so `null` is null, `"none"` is a string), standard JSON escapes, and errors reported with line and column [VERIFIED W3 E6a: `{"severity_exit_level": "none", "severity_levels": {"todos": "info"}}` -> exit 0; E6b: `[1]` -> "JSON configuration root must be an object", exit 4; `core.py:802-811`]. JSON is the only way to write a doctor config whose values contain commas inside list items safely.

### What `init-config` writes

`doctor init-config [-o PATH] [--force]` writes `ConfigManager.default_yaml()` verbatim: every key, all strings double-quoted, block lists, no comments [VERIFIED W3 E8a-E8e]. Without `--force` an existing file is an error (exit 4) [VERIFIED W3 E8b]. The output suffix is not checked; `-o x.toml` succeeds but `-c x.toml` is then rejected [VERIFIED lane B]. The file is used only when you pass it with `-c` [VERIFIED W3 E1, recipe R1].

## pycache-clean config file

This section documents the cleaner's YAML file.

- Loaded with `yaml.safe_load` (full YAML 1.1: `yes`/`no`/`on`/`off` are bools, anchors work). An empty file becomes `{}` and then fails "No roots specified" (exit 1); a list root fails with `AttributeError` (exit 1) [VERIFIED W3 P16/P17; `pycache_cleaner/core.py:172-175`].
- Each known key is assigned with `setattr`, with no type check; unknown keys trigger `logging.warning` before logging is configured [SOURCE-CONFIRMED `pycache_cleaner/core.py:175-179`].

| Key | Default | Expected | What a wrong type does | Evidence |
|---|---|---|---|---|
| `roots` | `[]` | list of paths; absolute recommended | a string is iterated per character | [VERIFIED W3 P13: roots `t`, `r`, `e`, `e`] |
| `exclude` | `[]` | directory **names** (fnmatchcase on the basename) | `node_modules/*` never matches; `null` -> TypeError, exit 1 | [VERIFIED W3 P3/P4/P18] |
| `targets` | `__pycache__`, `*.pyc`, `*.pyo` | entries without `*`/`?` are directory names, with them file patterns | replaces the defaults entirely | [SOURCE-CONFIRMED `pycache_cleaner/core.py:198-199`] |
| `dry_run` | `false` | YAML bool | `no`/`off` are false (live run); `"false"` is truthy (dry run while logging `dry_run=false`) | [VERIFIED W3 P7/P8] |
| `verbose` | `false` | bool | ignored when an unknown key is present | [VERIFIED W3 P9] |
| `max_depth` | `null` | int or null | `"2"` -> TypeError traceback, exit 1 | [VERIFIED W3 P14] |
| `follow_symlinks` | `false` | bool | n/a | [SOURCE-CONFIRMED `pycache_cleaner/core.py:237,248,253`] |
| `log_file` | `null` | path, appended to | left empty when an unknown key is present | [VERIFIED W3 P9: `run.log` 0 lines] |

`roots`, `log_file`, and `--config` are resolved against CWD, never the config file's directory [VERIFIED W3 P10/P11]. [D-14](../DISCOVERY-LEDGER.md#d-14)

## Fieldkit files

This section documents the files onboard.py writes and delta.py reads.

- `.somnus-debug/python_doctor.yaml`: init-config output with `include_patterns: ["*.py"]`, `ignore_patterns` = `BASE_IGNORES` plus discovered venvs, `*.egg-info`, and git-ignored Python directories, and `state_dir: ".somnus-debug/state"`, behind a 4-line header comment. If the init-config layout ever changes, onboard raises instead of writing a half-edited file [SOURCE-CONFIRMED `onboard.py:276-297`; VERIFIED lane F `logs/s1_profile_python_doctor.yaml.txt`].
- `.somnus-debug/pycache.yaml`: absolute repo root, name-only excludes, `dry_run: true` [SOURCE-CONFIRMED `onboard.py:300-321`].
- `.somnus-debug/dispositions.json`: starts as `[]`. Each entry needs non-empty string `category`, `file`, and `reason`; `symbol` is optional (default `*`); `file` and `symbol` are case-sensitive fnmatch globs [VERIFIED W3 DL2 and recipe R12; `delta.py:128-144`]. A missing file is a stderr note, not an error [VERIFIED W3 DL3]. A malformed file is exit 3 [VERIFIED lane F D6].
- `.somnus-debug/.gitignore`: `state/`, `runs/`, `*.log` [SOURCE-CONFIRMED `onboard.py:501`].
- onboard never overwrites any of these [VERIFIED lane F O3].

## Sources

This section lists the evidence behind this page.

- [`../_evidence/configuration-registry.tsv`](../_evidence/configuration-registry.tsv)
- [`../_evidence/agent-findings/lane-b-config/configuration-findings.md`](../_evidence/agent-findings/lane-b-config/configuration-findings.md) sections 3-4, [`experiments/yaml_probe.py`](../_evidence/agent-findings/lane-b-config/experiments/yaml_probe.py), [`experiments/yaml_probe.out`](../_evidence/agent-findings/lane-b-config/experiments/yaml_probe.out)
- [`../_evidence/agent-findings/lane-f-ext/fieldkit.md`](../_evidence/agent-findings/lane-f-ext/fieldkit.md)
- `src/somnus_debug/doctor/core.py:596-923`, `src/somnus_debug/pycache_cleaner/core.py:157-186`, `skills/somnus-debug-fieldkit/scripts/onboard.py:276-321,495-501`, `skills/somnus-debug-fieldkit/scripts/delta.py:128-144`
- W3 probes Y01-Y58 (`/tmp/w3/probe.py`), E1-E8, M5/M6, P1-P18, OB3, DL2/DL3
