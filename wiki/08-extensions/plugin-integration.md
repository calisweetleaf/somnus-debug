# Plugin integration

somnus-debug 0.1.0 has no plugin system and no MCP server. This page states what was searched, what integration surfaces do exist, and what a plugin seam would need if one were built.

## Finding

This section gives the result and its evidence class.

| Question | Answer | Class |
|---|---|---|
| Plugin discovery (entry points, `pkg_resources`, `importlib.metadata`) | None. The distribution declares only 4 `console_scripts` | [VERIFIED] |
| Plugin registry or `register()` call | None | [VERIFIED] |
| Config-listed extra detectors or visitor classes | None. `DoctorConfig` has no such field (`src/somnus_debug/doctor/core.py:208-240`, built at `:821-849`) | [SOURCE-CONFIRMED] |
| MCP (Model Context Protocol) server or tool definitions | Not present. No MCP code, manifest, or dependency in the package, the fieldkit, or `pyproject.toml` | [VERIFIED by search] |
| Editor, LSP, or IDE integration | None | [VERIFIED by search] |
| CI templates (GitHub Actions, pre-commit config) | None shipped. The fieldkit says not to install them by default | [SOURCE-CONFIRMED] |

## Search scope

This section records how the negatives were established.

- Package source: `grep -rniE 'entry_points|pkg_resources|importlib\.metadata|plugin|hook|callback|register|__subclasses__|import_module\('` over `src/somnus_debug/**/*.py` returned no code matches [VERIFIED, this wave and [lane F](../_evidence/agent-findings/lane-f-ext/extensions.md)].
- Installed metadata: an `importlib.metadata` scan of all entry-point groups found only the 4 scripts [VERIFIED, [lane-f s5 log](../_evidence/agent-findings/lane-f-ext/logs/s5_library_and_links.log)].
- `pyproject.toml`: `[project.scripts]` lists `somnus-debug`, `somnus-doctor`, `somnus-structure`, `somnus-pycache-clean`; there is no `[project.entry-points.*]` table [SOURCE-CONFIRMED].
- MCP: `grep -rniE '\bmcp\b'` over `*.py`, `*.toml`, `*.yaml`, `*.md` in the repo (excluding `wiki/`) matched only `STATE.md:30` and `skills/somnus-debug-fieldkit/references/provenance.md:44`. Both refer to the "Somnus-MCP" project layout that the old `tools/*.py` / `test/*.py` default globs came from, not to an MCP server [VERIFIED]. That history is [D-23](../DISCOVERY-LEDGER.md#d-23).

An MCP server for somnus-debug may be built later by the project owner. Nothing in 0.1.0 anticipates one, and this wiki does not describe one as existing.

## Integration surfaces that do exist

This section lists what an outside tool can integrate with today, all of it process-level.

| Surface | Contract | Page |
|---|---|---|
| CLI subprocess | Argv, exit codes, stdout summary line, `-o` / `--json-output` paths | [programmatic-invocation](../10-agent-usage/programmatic-invocation.md) |
| Doctor JSON report | Fixed key set: `config_hash, dependency_graph, files, finished_at, issues, project_root, run_id, started_at, state_delta, summary` | [automation-contracts](../10-agent-usage/automation-contracts.md) |
| Fieldkit `delta.py --json` | Verdict object with `exit`, `new`, `regressions`, `stale_dispositions`, coverage fields | [automation-contracts](../10-agent-usage/automation-contracts.md) |
| Python import of internals | `ProjectScanner`, `ConfigManager`, `build_index`, `scaffold`; none marked stable | [programmatic recipes](../09-recipes/README.md#programmatic) |
| Harness `run_test.py` | Stdout JSON summary, `manifest.json` schema 1.0, exit 0/1 | [integrations recipes](../09-recipes/README.md#integrations) |

A host that wants "plugin-like" behaviour today wraps these. The fieldkit is itself such a wrapper: it adds onboarding, a regression gate, and dispositions without touching the package [VERIFIED, [lane-f fieldkit](../_evidence/agent-findings/lane-f-ext/fieldkit.md)].

## What a plugin seam would need

This section is design guidance only. Nothing here exists. [HYPOTHESIS]

1. **Detector discovery.** `FileAnalyzer.analyze()` instantiates `CodeQualityVisitor` by its module-global name (`src/somnus_debug/doctor/core.py:1542`). The smallest change is to read extra visitor classes from config or from a `somnus_debug.detectors` entry-point group and run them in the same pass.
2. **Severity.** Already generic: `parse_severities` accepts any category name and unknown categories default to `minor` (`:769-779`, `:792-794`) [VERIFIED].
3. **Downstream.** Already generic: the Markdown writer, summary counts, score, exit gate and `delta.py` all handled a custom `print_calls` category without change [VERIFIED, [custom-detector probe](../09-recipes/advanced/custom-detector-probe.md)].
4. **MCP.** A server would wrap the same process-level surfaces above: scan (with mandatory `-o`, `--json-output`, and a temp cwd so the log does not land in the repo), structure, delta. It should expose coverage (`files_scanned`) prominently, since a zero-file scan exits 0.

See [experimental-extensions](experimental-extensions.md) for the monkeypatch probe that demonstrates point 1 against private internals.

## Sources

This section lists the files, logs and evidence this page rests on.

- [lane-f extensions](../_evidence/agent-findings/lane-f-ext/extensions.md), [lane-f s5 log](../_evidence/agent-findings/lane-f-ext/logs/s5_library_and_links.log), [lane-f fieldkit](../_evidence/agent-findings/lane-f-ext/fieldkit.md)
- `pyproject.toml`; `src/somnus_debug/doctor/core.py:208-240`, `:769-794`, `:821-849`, `:1542`
- `STATE.md:30`, `skills/somnus-debug-fieldkit/references/provenance.md:44`
- [stage 3 log](../09-recipes/_repro/logs/stage3_advanced.log) (custom category flowing through delta)
