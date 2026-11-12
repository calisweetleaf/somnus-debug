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
| Y27 | `a: "x\\ny"` | `{'a': 'x\ny'}` | `{'a': 'x\ny'}` | yes | - |
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
| Y44 | `a: "\\q"` | `{'a': '\\q'}` | `ScannerError: while scanning a double-quoted scalar` | no | SILENT: Python escape rules, not YAML's |
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
