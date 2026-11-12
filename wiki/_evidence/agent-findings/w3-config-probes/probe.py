import warnings, json, yaml, tempfile, pathlib
warnings.simplefilter("ignore")
from somnus_debug.doctor.core import MinimalYamlParser, ConfigurationError
cases = {
 "Y01 plain scalar int": "a: 5",
 "Y02 float": "a: 5.0",
 "Y03 exponent float": "a: 1e3",
 "Y04 yes/no/on/off": "a: yes\nb: no\nc: on\nd: off",
 "Y05 True/FALSE case": "a: True\nb: FALSE",
 "Y06 null forms": "a: null\nb: ~\nc: None\nd: NULL",
 "Y07 empty value at EOF": "a:",
 "Y08 empty value then sibling": "a:\nb: 1",
 "Y09 quoted with hash": 'a: "x # y"\nb: x # comment',
 "Y10 unquoted hash no space": "a: x#y",
 "Y11 flow list": 'a: ["*.py", "src/*.py"]',
 "Y12 flow list with comma in quotes": 'a: ["a,b", "c"]',
 "Y13 flow mapping": "a: {b: 1}",
 "Y14 nested flow list": "a: [[1,2],3]",
 "Y15 block list of mappings": "a:\n  - b: 1\n    c: 2",
 "Y16 list item with nested block": "a:\n  -\n    b: 1",
 "Y17 key with colon in value": "a: http://x:80/y",
 "Y18 quoted key": '"a b": 1',
 "Y19 tabs indent": "a:\n\t- x",
 "Y20 inconsistent indent": "a:\n    - x\n  - y",
 "Y21 dash without space": "a:\n  -x",
 "Y22 block scalar |": "a: |\n  line1\n  line2",
 "Y23 anchors/alias": "a: &x 1\nb: *x",
 "Y24 document marker ---": "---\na: 1",
 "Y25 duplicate keys": "a: 1\na: 2",
 "Y26 single-quoted escape ''": "a: 'it''s'",
 "Y27 double-quoted escape \\n": 'a: "x\\ny"',
 "Y28 octal/hex": "a: 0o17\nb: 0x1F\nc: 010",
 "Y29 leading zero int": "a: 007",
 "Y30 list root": "- a\n- b",
 "Y31 empty file": "",
 "Y32 only comments": "# hi\n# there",
 "Y33 quoted number": 'a: "5"',
 "Y34 sequence at same indent as key (PyYAML compact)": "a:\n- x\n- y",
 "Y35 trailing spaces after value": "a: 5   ",
 "Y36 mismatched quotes": "a: \"x'",
 "Y37 flow list with null": "a: [null, ~, true]",
 "Y38 empty flow list item": "a: [1,,2]",
 "Y39 negative int": "a: -1",
 "Y40 dash item looks like neg number": "a:\n  - -1",
 "Y41 key-only no colon": "a",
 "Y42 windows CRLF": "a: 1\r\nb: 2\r\n",
 "Y43 BOM": "\ufeffa: 1",
 "Y44 Python-escape in double quote that YAML rejects": 'a: "\\q"',
 "Y45 quoted value with trailing comment": "a: 'x' # c",
 "Y46 inf/nan": "a: .inf\nb: .nan",
 "Y47 underscore int": "a: 1_000",
 "Y48 string 'none' lowercase": "a: none",
 "Y49 implicit concat in quotes": "a: \"x\" \"y\"",
 "Y50 empty quoted string": "a: \"\"",
 "Y51 value containing colon-space": "a: b: c",
 "Y52 flow list with spaces only": "a: [ ]",
 "Y53 dash alone": "a:\n  -",
 "Y54 quoted none": "a: \"none\"",
 "Y55 single-quoted hash": "a: 'x#y'",
 "Y56 severity flow mapping": "severity_levels: {stubs: info}",
 "Y57 key with trailing space before colon": "a : 1",
 "Y58 tab after colon": "a:\t1"
}
rows=[]
for name, text in cases.items():
    p = pathlib.Path(tempfile.mktemp(suffix=".yaml")); p.write_bytes(text.encode("utf-8"))
    try: mine = ("OK", MinimalYamlParser(p).parse())
    except ConfigurationError as e: mine = ("ConfigurationError", e.message + " " + json.dumps(e.context, default=str))
    except Exception as e: mine = (type(e).__name__, str(e))
    try: ref = ("OK", yaml.safe_load(text))
    except Exception as e: ref = (type(e).__name__, str(e).splitlines()[0])
    same = mine[0]=="OK" and ref[0]=="OK" and (mine[1]==ref[1] or (ref[1] is None and mine[1]=={}))
    rows.append((name,text,mine,ref,same))
    print(f"{name}\n   doctor: {mine[0]} {mine[1]!r}\n   pyyaml: {ref[0]} {ref[1]!r}\n   agree={same}")

import json as _j
_j.dump([[n,t,list(m),list(r),sm] for n,t,m,r,sm in rows], open("probe.json","w"), default=repr)
