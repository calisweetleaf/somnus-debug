# Wave 5 writing brief: canonical wiki pages

Repo: /workspace/projects/69c23182-5d69-4d5c-ae10-5cdad587b9d3/forge/somnus-debug (baseline commit 034f46e, somnus-debug 0.1.0). Read BRIEF.md first; its rules still hold (repo read-only except your owned pages; experiments in /tmp/<you> with PYTHONDONTWRITEBYTECODE=1 and cwd in /tmp).

## Evidence you build on
wiki/_evidence/agent-findings/
- lane-a-arch-api/: architecture.md, api-reference.md, symbols.tsv (256 symbols), undocumented-primitives.md, examples/
- lane-b-config/: configuration-registry.tsv (94 rows), configuration-findings.md, experiments/
- lane-d-cli-tests/: command-reference.md, exit-codes.md, experiment-log.md, experiments.jsonl, test-coverage.md, install-vs-source.md, help-surfaces-raw.txt
- lane-f-ext/: extensions.md, fieldkit.md, harness.md, doc-reconciliation.md, compositions.md, recipes/, repro/, logs/
Do not concatenate lane reports. Reconcile them into one account. Where lanes disagree, read the source and decide; say which. Lead reconciliations already made:
- `-v` is accepted by argparse but ignored; setup_logging() checks for the literal string `--verbose` in argv before parsing (doctor/core.py:2179-2186). `--verbose` sets the log file to DEBUG, but doctor/core.py contains zero logger.debug calls, so it has no observable effect.
- Source tests: 10 passed, 2 failed (both structure type_comments). Fieldkit selftest 29/29 (its structure probe uses an unstamped file, so it misses the crash).
- PyPI 0.1.0 code == src/ after stripping metadata headers; only default_config.yaml differs (old MCP globs). Root duplicates differ from src/ (structure type_comments line; doctor SQLite fallback near line 2066).
- STATE.md and PLAN.md exist in the zip (operator files, gitignored upstream); docs/OPSEC.md does not exist.

## Writing rules
- Plain GitHub Markdown. No emoji. Every H2 opens with one sentence stating the section's job.
- Every technical claim carries an evidence class in brackets: [VERIFIED], [SOURCE-CONFIRMED], [DOCUMENTED-ONLY], [CONDITIONAL], [DISCREPANCY], [UNVERIFIED], [HYPOTHESIS], and a source: repo-relative `path:line` and/or a link to the lane evidence file (relative link, e.g. `../_evidence/agent-findings/lane-b-config/configuration-findings.md`).
- Code examples: mark each `Executed: yes (where/result)` or `Executed: no`. Never invent import paths, flags, keys, or outputs. If you add a new example, run it in /tmp first.
- Depth over volume: concept, operation, programmatic use, internals, pitfalls where they apply. Do not pad. If a planned page truly has nothing to say, write a short page stating why and what was searched (do not skip the file; the lead's coverage report links to it).
- Cross-link with relative links ONLY to pages in the planned tree below (they will exist). Link discoveries as `../12-discoveries/<page>.md` or `../DISCOVERY-LEDGER.md#d-NN` only for IDs in the list at the bottom.
- Write only the pages you own. End each page with a "Sources" list.

## Planned tree (all pages will exist)
wiki/README.md INDEX.md START-HERE.md CAPABILITY-ATLAS.md DISCOVERY-LEDGER.md COVERAGE-REPORT.md GLOSSARY.md
01-system/: overview architecture module-map execution-model lifecycle state-and-persistence dependency-map design-invariants
02-installation/: requirements installation environment-detection package-layout verification compatibility
03-getting-started/: quickstart first-project minimal-examples common-workflows troubleshooting-first-run
04-library-api/: overview public-api classes functions types-and-schemas exceptions async-and-concurrency internal-interfaces api-index
05-cli-and-tools/: command-reference options-and-flags input-output-contracts exit-codes tooling-integration automation-examples
06-configuration/: configuration-atlas complete-option-reference defaults precedence environment-variables file-based-configuration runtime-configuration implicit-configuration hidden-and-conditional-options configuration-recipes configuration-pitfalls
07-internals/: initialization call-chains state-transitions registries-and-discovery caching-and-performance error-handling fallbacks implementation-notes
08-extensions/: extension-overview existing-extension-points hooks-and-events plugin-integration customization composition-patterns experimental-extensions
09-recipes/: README.md, beginner/, intermediate/, advanced/, programmatic/, automation/, integrations/ (recipe file names chosen by owner; list them in 09-recipes/README.md)
10-agent-usage/: agent-quickstart tool-selection programmatic-invocation agent-workflows subagent-patterns automation-contracts failure-recovery
11-verification/: test-architecture tested-behaviors untested-behaviors reproducible-probes known-limitations environment-matrix verification-results
12-discoveries/: undocumented-capabilities implicit-behaviors surprising-defaults latent-interfaces unexpected-compositions implementation-discrepancies unresolved-questions research-opportunities
13-reference/: symbol-index configuration-index entrypoint-index module-index file-index terminology
_evidence/: README source-inventory source-coverage.tsv capability-registry.jsonl configuration-registry.tsv command-observations experiment-log verification-manifest

## Discovery IDs (lead owns DISCOVERY-LEDGER.md; link only these)
D-01 structure type_comments crash still in src/ and PyPI; fix only in root duplicate; 2 smoke tests fail
D-02 doctor never auto-loads python_doctor.yaml; only -c
D-03 unquoted `severity_exit_level: none` parsed as null -> exit 4; `none`/`info` gates undocumented
D-04 doctor mini-YAML parser silent mis-parses; unknown keys accepted silently
D-05 test_gaps / detect_test_gaps configured, validated, never emitted
D-06 import resolution: `from pkg import mod` resolves to pkg/__init__.py; cycles and missing siblings missed
D-07 detector false positives: silent_failures name-sensitive, stubs on abstract/Protocol/overload, duplicates on property setters/overloads, frozen dataclass short-class, __future__/__all__ unused imports, placeholder_returns on `return 1`
D-08 run IDs per-second + INSERT OR REPLACE -> same-second scans overwrite history
D-09 rollback only moves latest alias; project-root reports not rolled back
D-10 cwd/package writes: production_doctor.log in cwd every call; self-check writes into installed package dir; history/rollback create state dirs
D-11 logging.basicConfig(force=True) replaces host program logging handlers
D-12 clean embedding path: ProjectScanner(root, ConfigManager(None)).scan({}) has no disk/logging side effects
D-13 PyYAML hard requirement for every dispatcher subcommand (cli.py imports all tools)
D-14 pycache-clean config hazards: scalar roots iterated per char (can include /), exclude bare names only, no type checks (`dry_run: no` deletes), unknown key silences logging, roots relative to cwd, no $VAR expansion, no Windows long-path code, dry-run says "Removed", missing root exits 0
D-15 init-test-harness template is project-specific (cargo gp-cli) and default placement writes test-runs/ outside repo; template ignores --help; adds 9 doctor findings
D-16 ignore_functions / check_nested_functions hide security findings in skipped bodies
D-17 default ignore patterns skip dirs named env/build/venv at any depth; empty include_patterns scans 0 files and exits 0
D-18 exit code 2 overloaded (critical gate vs argparse error); minor/info gate returns 1 even with criticals; uncaught exception types escape as tracebacks; RecursionError aborts scan exit 5
D-19 no extension API; custom detector works only by subclassing CodeQualityVisitor (private)
D-20 onboard.py bugs: --python venv symlink rejected; bad config traceback exit 1; PROFILE written on zero-file failure
D-21 delta.py holes: stale broad disposition absorbs regressions; config_hash never compared; usage error exit 2 == coverage regression; malformed report traceback
D-22 src-layout composition conflict: PYTHONPATH=src makes own imports third-party, dependency_cycles 0
D-23 PyPI 0.1.0 default_config.yaml ships old MCP globs (reference-only, no runtime effect); version hard-coded in __init__.py and pyproject
D-24 structure double-renders/counts nested class in class in function
D-25 -o report.json overwrites markdown report; JSON always written
D-26 missing_imports depends on the running interpreter and cwd on sys.path
D-27 verified compositions: doctor JSON->delta gate, structure slices, findings->slices, ratchet, state reports as baselines
D-28 SQLite-unavailable fallback works for scan, not history; root duplicate lacks it
