# somnus-debug Wiki

This wiki is the evidence-backed knowledge base for somnus-debug 0.1.0: what the four tools and the fieldkit actually do, how to run and embed them, how they are configured, where they break, and what the existing docs get wrong. It was built on 2026-11-11 by a source-first investigation of the uploaded tree (baseline `034f46e`), with every claim tagged by evidence class.

## What somnus-debug is

This section gives the one-paragraph model a reader needs before choosing a path.

somnus-debug is a Python developer toolkit with four tools behind one dispatcher (`somnus-debug <command>`): **doctor** scans a project's AST for production-readiness problems, tracks runs in SQLite, and gates CI by severity; **structure** indexes the classes and functions of one file with line spans; **pycache-clean** removes bytecode caches by config; **init-test-harness** scaffolds a single-test runner. A separate **fieldkit** skill (not in the wheel) adds onboarding, a regression delta gate, and a 29-check behavior selftest for agents. There is no plugin API, no MCP server, and no network behavior.

## Read this first

This section lists what will surprise an operator on day one; each links to its ledger entry.

- `structure` crashes on every file carrying a somnus-metadata header, including its own source ([D-01](DISCOVERY-LEDGER.md#d-01)).
- doctor ignores `python_doctor.yaml` unless you pass `-c` ([D-02](DISCOVERY-LEDGER.md#d-02)) and writes `production_doctor.log` into whatever directory you run it from ([D-10](DISCOVERY-LEDGER.md#d-10)).
- doctor misses import cycles written `from pkg import mod` ([D-06](DISCOVERY-LEDGER.md#d-06)).
- Never give pycache-clean a scalar `roots:`; use a list ([D-14](DISCOVERY-LEDGER.md#d-14)).
- The scaffolded harness is a cargo test and writes outside the repo by default ([D-15](DISCOVERY-LEDGER.md#d-15)).

## Navigation

This section routes readers by need.

| If you want to | Go to |
|---|---|
| Get oriented by role | [START-HERE.md](START-HERE.md) |
| See every page | [INDEX.md](INDEX.md) |
| See every capability and its status | [CAPABILITY-ATLAS.md](CAPABILITY-ATLAS.md) |
| See what is new or wrong | [DISCOVERY-LEDGER.md](DISCOVERY-LEDGER.md) |
| Know what was and was not checked | [COVERAGE-REPORT.md](COVERAGE-REPORT.md) |
| Run it now | [03-getting-started/quickstart.md](03-getting-started/quickstart.md) |
| Look up a flag or key | [06-configuration/complete-option-reference.md](06-configuration/complete-option-reference.md) |
| Drive it from an agent | [10-agent-usage/agent-quickstart.md](10-agent-usage/agent-quickstart.md) |
| Audit a claim | [_evidence/README.md](_evidence/README.md) |

## Machine-readable indexes

This section lists the files other agents should parse instead of scraping Markdown.

- [`_evidence/capability-registry.jsonl`](_evidence/capability-registry.jsonl): capabilities.
- [`_evidence/configuration-registry.tsv`](_evidence/configuration-registry.tsv): configuration surfaces.
- [`_evidence/source-coverage.tsv`](_evidence/source-coverage.tsv): per-file inspection depth.
- [`_evidence/agent-findings/lane-a-arch-api/symbols.tsv`](_evidence/agent-findings/lane-a-arch-api/symbols.tsv): every symbol in `src/`.
- [`wiki-index.json`](wiki-index.json): every wiki page with title and section.

## Boundaries

This section states what the investigation changed and what it did not.

No source, test, manifest, or config file was modified; the only repository output is this `wiki/` directory. The investigated copy lives in a private workshop repository; nothing was pushed.
