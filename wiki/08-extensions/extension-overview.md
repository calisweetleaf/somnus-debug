# Extension overview

somnus-debug 0.1.0 has no plugin system. It does have three real surfaces you can build on: the configuration file, the JSON report contract, and the fieldkit scripts that consume that contract. This page maps what you can extend today, what takes a small amount of glue, and what would need new code.

## Verdict

This section gives the one-paragraph answer before the detail.

There is no supported way to add a detector, a report format, or a command without editing `src/somnus_debug/`. No registry, no entry-point group, no hook or callback exists [VERIFIED, [lane-f-ext/extensions.md](../_evidence/agent-findings/lane-f-ext/extensions.md); search scope restated in [hooks-and-events](hooks-and-events.md)]. The tools are built to be composed from the outside instead: doctor writes a JSON report (unversioned, but its shape is fixed in code), the fieldkit `delta.py` reads it, and agents and CI chain the two. That outside-in composition is where all of the supported extension value is [VERIFIED, [lane-f-ext/compositions.md](../_evidence/agent-findings/lane-f-ext/compositions.md)].

## Three tiers

This section sorts every extension idea into one of three tiers, and the rest of this chapter keeps the same labels.

| Tier | Meaning | Examples |
|---|---|---|
| **Supported now** | Works with the shipped tools and shell glue. No code changes, no private imports. Executed. | Config thresholds, toggles, globs, severity remaps, exit gate ([customization](customization.md)); doctor JSON → `delta.py` gate; ratchet; findings → source slices; opt-in git hook ([composition-patterns](composition-patterns.md)) |
| **Small integration step** | Works, but needs user-written glue, a workaround for a known defect, or an import of non-exported classes. Executed. | Harness `execute_test()` running tests + doctor + delta; embedding `ProjectScanner`; indexing metadata-stamped files through `build_index` after blanking the header |
| **Research idea** | Not built. Would need new code in the package or the fieldkit. | Detector plug-in seam, config-aware `delta.py`, whole-tree structure graph, an MCP server ([experimental-extensions](experimental-extensions.md)) |

A custom detector made by subclassing `CodeQualityVisitor` sits between the second and third tiers. It runs and its output flows through the whole pipeline, but it rebinds a private module global. Treat it as a probe, not an API [VERIFIED + HYPOTHESIS for stability, [lane-f-ext/extensions.md](../_evidence/agent-findings/lane-f-ext/extensions.md); [D-19](../DISCOVERY-LEDGER.md#d-19)].

## Where each tool can be shaped

This section lists, per tool, the levers that exist and points to the page that covers each.

| Tool | Levers that exist | Levers that do not exist |
|---|---|---|
| `doctor` | `-c` config (thresholds, 5 detector toggles, include and ignore globs, `ignore_functions`, `ignore_classes`, per-category severity, exit gate, `state_dir`), `-o`, `--json-output`, `--no-state` | Score weights, new detectors, suppression comments, output formats beyond Markdown and JSON, config auto-discovery |
| `structure` | `--no-line-numbers`, `--no-module-functions`, `--source-label`, `-o`, `--update-doc`; `build_index()` keyword flags | Multi-file or tree mode, JSON output |
| `pycache-clean` | YAML `roots`, `exclude`, `targets`, `dry_run`, `max_depth`, `follow_symlinks`, `log_file`; `--dry-run`, `--max-depth`, `--follow-symlinks`, `--verbose` | Type checking of config values, path-style excludes |
| `init-test-harness` | Target directory, `--force`, `--no-contract`; the scaffolded `TEST_NAME` and `execute_test()` | Template choice, CLI flags on the scaffolded `run_test.py` |
| fieldkit | `dispositions.json`, `delta.py --json`, `--root`; `onboard.py --new-config`, `--python` | Config-hash checking, severity recomputation |

Sources for the table: `src/somnus_debug/doctor/core.py:829-849` (parsed config fields), `src/somnus_debug/pycache_cleaner/core.py:158-180` (cleaner fields and loader), `skills/somnus-debug-fieldkit/scripts/delta.py:235-243` (delta CLI), help output captured in [lane-d-cli-tests/help-surfaces-raw.txt](../_evidence/agent-findings/lane-d-cli-tests/help-surfaces-raw.txt) [SOURCE-CONFIRMED, VERIFIED].

## How to read the rest of this chapter

This section routes you to the page that answers each question.

- What exists, file by file: [existing-extension-points](existing-extension-points.md).
- Whether you can subscribe to anything: [hooks-and-events](hooks-and-events.md). Short answer: no.
- Plugins, entry points, MCP: [plugin-integration](plugin-integration.md). Short answer: none present.
- Config-only tuning and its traps: [customization](customization.md).
- Chaining tools into workflows: [composition-patterns](composition-patterns.md), with runnable versions in [the recipes index](../09-recipes/README.md).
- Monkeypatching and unbuilt seams: [experimental-extensions](experimental-extensions.md).
- Agents driving all of this: [agent quickstart](../10-agent-usage/agent-quickstart.md).

## Sources

This section lists the files, logs and evidence this page rests on.

- [lane-f-ext/extensions.md](../_evidence/agent-findings/lane-f-ext/extensions.md)
- [lane-f-ext/compositions.md](../_evidence/agent-findings/lane-f-ext/compositions.md)
- [lane-a-arch-api/api-reference.md](../_evidence/agent-findings/lane-a-arch-api/api-reference.md)
- [lane-d-cli-tests/help-surfaces-raw.txt](../_evidence/agent-findings/lane-d-cli-tests/help-surfaces-raw.txt)
- `src/somnus_debug/doctor/core.py:829-849`, `src/somnus_debug/pycache_cleaner/core.py:158-180`
- `skills/somnus-debug-fieldkit/scripts/delta.py:235-243`
