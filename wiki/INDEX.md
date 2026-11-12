# Index

This index lists every wiki page by section, then routes by intent, interface, and problem. The same list is machine-readable in [wiki-index.json](wiki-index.json).

## By intent

This section maps common goals to the page that answers them.

| I want to | Page |
|---|---|
| run a first scan | [quickstart](03-getting-started/quickstart.md) |
| gate CI on regressions | [ci-delta-gate recipe](09-recipes/automation/ci-delta-gate.md), [automation contracts](10-agent-usage/automation-contracts.md) |
| embed doctor in Python | [programmatic invocation](10-agent-usage/programmatic-invocation.md), [embedded-scan recipe](09-recipes/programmatic/embedded-scan.md) |
| change what doctor flags | [configuration atlas](06-configuration/configuration-atlas.md), [severity and gate tuning](09-recipes/intermediate/severity-and-gate-tuning.md) |
| index one file for an agent | [index-one-file recipe](09-recipes/beginner/index-one-file.md), [index-stamped-file](09-recipes/programmatic/index-stamped-file.md) |
| clean caches safely | [pycache dry run](09-recipes/beginner/pycache-dry-run.md), [D-14](DISCOVERY-LEDGER.md#d-14) |
| add a custom check | [customization](08-extensions/customization.md), [custom-detector-probe](09-recipes/advanced/custom-detector-probe.md) |
| onboard a repo for agents | [onboard-a-repo](09-recipes/intermediate/onboard-a-repo.md), [agent quickstart](10-agent-usage/agent-quickstart.md) |

## By interface

This section routes by how you call the toolkit.

| Interface | Pages |
|---|---|
| CLI | [command reference](05-cli-and-tools/command-reference.md), [options and flags](05-cli-and-tools/options-and-flags.md), [exit codes](05-cli-and-tools/exit-codes.md) |
| Python | [public API](04-library-api/public-api.md), [internal interfaces](04-library-api/internal-interfaces.md), [api index](04-library-api/api-index.md) |
| Fieldkit scripts | [agent quickstart](10-agent-usage/agent-quickstart.md), [automation contracts](10-agent-usage/automation-contracts.md) |
| MCP / plugins / hooks | none exist: [plugin integration](08-extensions/plugin-integration.md), [hooks and events](08-extensions/hooks-and-events.md) |

## By problem

This section routes from a symptom to its explanation.

| Symptom | Page |
|---|---|
| structure says `invalid syntax` on a valid file | [D-01](DISCOVERY-LEDGER.md#d-01) |
| my config is ignored | [D-02](DISCOVERY-LEDGER.md#d-02), [precedence](06-configuration/precedence.md) |
| exit 4 on a config that looks right | [D-03](DISCOVERY-LEDGER.md#d-03), [D-04](DISCOVERY-LEDGER.md#d-04) |
| a known cycle is not reported | [D-06](DISCOVERY-LEDGER.md#d-06), [D-22](DISCOVERY-LEDGER.md#d-22) |
| history lost a run | [D-08](DISCOVERY-LEDGER.md#d-08), [D-32](DISCOVERY-LEDGER.md#d-32) |
| a log file appeared in my directory | [D-10](DISCOVERY-LEDGER.md#d-10) |
| first-run trouble generally | [troubleshooting first run](03-getting-started/troubleshooting-first-run.md), [failure recovery](10-agent-usage/failure-recovery.md) |

## All pages

This section lists every page, grouped by section.

### top

- [Capability Atlas](CAPABILITY-ATLAS.md)
- [Coverage Report](COVERAGE-REPORT.md)
- [Discovery Ledger](DISCOVERY-LEDGER.md)
- [Glossary](GLOSSARY.md)
- [Index](INDEX.md)
- [somnus-debug Wiki](README.md)
- [Start Here](START-HERE.md)

### 01-system

- [Architecture](01-system/architecture.md)
- [Dependency map](01-system/dependency-map.md)
- [Design invariants](01-system/design-invariants.md)
- [Execution model](01-system/execution-model.md)
- [Lifecycle](01-system/lifecycle.md)
- [Module map](01-system/module-map.md)
- [System overview](01-system/overview.md)
- [State and persistence](01-system/state-and-persistence.md)

### 02-installation

- [Compatibility](02-installation/compatibility.md)
- [Environment detection](02-installation/environment-detection.md)
- [Installation](02-installation/installation.md)
- [Package layout](02-installation/package-layout.md)
- [Requirements](02-installation/requirements.md)
- [Verifying an installation](02-installation/verification.md)

### 03-getting-started

- [Common workflows](03-getting-started/common-workflows.md)
- [First project: a full doctor loop on a src-layout package](03-getting-started/first-project.md)
- [Minimal examples](03-getting-started/minimal-examples.md)
- [Quickstart](03-getting-started/quickstart.md)
- [Troubleshooting the first run](03-getting-started/troubleshooting-first-run.md)

### 04-library-api

- [API index](04-library-api/api-index.md)
- [Async and concurrency](04-library-api/async-and-concurrency.md)
- [Classes](04-library-api/classes.md)
- [Exceptions](04-library-api/exceptions.md)
- [Functions](04-library-api/functions.md)
- [Internal interfaces](04-library-api/internal-interfaces.md)
- [Library API overview](04-library-api/overview.md)
- [Public API](04-library-api/public-api.md)
- [Types and schemas](04-library-api/types-and-schemas.md)

### 05-cli-and-tools

- [Automation examples](05-cli-and-tools/automation-examples.md)
- [Command reference](05-cli-and-tools/command-reference.md)
- [Exit codes](05-cli-and-tools/exit-codes.md)
- [Input and output contracts](05-cli-and-tools/input-output-contracts.md)
- [Options and flags](05-cli-and-tools/options-and-flags.md)
- [Tooling integration](05-cli-and-tools/tooling-integration.md)

### 06-configuration

- [Complete option reference](06-configuration/complete-option-reference.md)
- [Configuration atlas](06-configuration/configuration-atlas.md)
- [Configuration pitfalls](06-configuration/configuration-pitfalls.md)
- [Configuration recipes](06-configuration/configuration-recipes.md)
- [Defaults](06-configuration/defaults.md)
- [Environment variables](06-configuration/environment-variables.md)
- [File-based configuration](06-configuration/file-based-configuration.md)
- [Hidden and conditional options](06-configuration/hidden-and-conditional-options.md)
- [Implicit configuration](06-configuration/implicit-configuration.md)
- [Precedence](06-configuration/precedence.md)
- [Runtime configuration](06-configuration/runtime-configuration.md)

### 07-internals

- [Caching and performance](07-internals/caching-and-performance.md)
- [Call chains](07-internals/call-chains.md)
- [Error handling](07-internals/error-handling.md)
- [Fallbacks](07-internals/fallbacks.md)
- [Implementation notes](07-internals/implementation-notes.md)
- [Initialization](07-internals/initialization.md)
- [Registries and discovery](07-internals/registries-and-discovery.md)
- [State transitions](07-internals/state-transitions.md)

### 08-extensions

- [Composition patterns](08-extensions/composition-patterns.md)
- [Customization](08-extensions/customization.md)
- [Existing extension points](08-extensions/existing-extension-points.md)
- [Experimental extensions](08-extensions/experimental-extensions.md)
- [Extension overview](08-extensions/extension-overview.md)
- [Hooks and events](08-extensions/hooks-and-events.md)
- [Plugin integration](08-extensions/plugin-integration.md)

### 09-recipes

- [Recipes](09-recipes/README.md)
- [Recipe: prototype a custom detector (private-API probe)](09-recipes/advanced/custom-detector-probe.md)
- [Recipe: turn new findings into the exact source lines to read](09-recipes/advanced/findings-to-source-slices.md)
- [Recipe: quality ratchet (promote the baseline only when clean)](09-recipes/advanced/quality-ratchet.md)
- [Recipe: check import cycles in a src-layout project](09-recipes/advanced/src-layout-cycle-check.md)
- [Recipe: CI regression gate (doctor JSON → `delta.py`)](09-recipes/automation/ci-delta-gate.md)
- [Recipe: audit runs with `doctor history`, and what `rollback` really does](09-recipes/automation/history-and-rollback.md)
- [Recipe: opt-in git pre-commit gate](09-recipes/automation/pre-commit-gate.md)
- [Recipe: first doctor scan with a config, reports where you want them](09-recipes/beginner/first-scan.md)
- [Recipe: index one Python file with `structure`](09-recipes/beginner/index-one-file.md)
- [Recipe: preview a bytecode cleanup with `pycache-clean`](09-recipes/beginner/pycache-dry-run.md)
- [Recipe execution log](09-recipes/execution-log.md)
- [Recipe: prove the installed CLI still matches the fieldkit (`selftest.py`)](09-recipes/integrations/fieldkit-selftest.md)
- [Recipe: one harness run = project tests + doctor rescan + delta gate](09-recipes/integrations/harness-doctor-delta.md)
- [Recipe: wire a project's pytest suite into the single-test harness](09-recipes/integrations/harness-pytest.md)
- [Recipe: baseline, change, rescan, delta, triage](09-recipes/intermediate/baseline-delta-loop.md)
- [Recipe: onboard a repository with the fieldkit](09-recipes/intermediate/onboard-a-repo.md)
- [Recipe: remap a category's severity and choose the exit gate](09-recipes/intermediate/severity-and-gate-tuning.md)
- [Recipe: scan in-process with `ProjectScanner` (no files, no logging changes)](09-recipes/programmatic/embedded-scan.md)
- [Recipe: index a metadata-stamped file with `build_index`](09-recipes/programmatic/index-stamped-file.md)
- [Recipe: call doctor's `main()` in-process without losing your logging](09-recipes/programmatic/inprocess-main-isolated.md)

### 10-agent-usage

- [Agent quickstart](10-agent-usage/agent-quickstart.md)
- [Agent workflows](10-agent-usage/agent-workflows.md)
- [Automation contracts](10-agent-usage/automation-contracts.md)
- [Failure recovery](10-agent-usage/failure-recovery.md)
- [Programmatic invocation](10-agent-usage/programmatic-invocation.md)
- [Subagent patterns](10-agent-usage/subagent-patterns.md)
- [Tool selection](10-agent-usage/tool-selection.md)

### 11-verification

- [Environment matrix](11-verification/environment-matrix.md)
- [Known limitations](11-verification/known-limitations.md)
- [Reproducible probes](11-verification/reproducible-probes.md)
- [Test architecture](11-verification/test-architecture.md)
- [Tested behaviors](11-verification/tested-behaviors.md)
- [Untested behaviors](11-verification/untested-behaviors.md)
- [Verification results](11-verification/verification-results.md)

### 12-discoveries

- [Implementation Discrepancies](12-discoveries/implementation-discrepancies.md)
- [Implicit Behaviors](12-discoveries/implicit-behaviors.md)
- [Latent Interfaces](12-discoveries/latent-interfaces.md)
- [Research Opportunities](12-discoveries/research-opportunities.md)
- [Surprising Defaults](12-discoveries/surprising-defaults.md)
- [Undocumented Capabilities](12-discoveries/undocumented-capabilities.md)
- [Unexpected Compositions](12-discoveries/unexpected-compositions.md)
- [Unresolved Questions](12-discoveries/unresolved-questions.md)

### 13-reference

- [Configuration index](13-reference/configuration-index.md)
- [Entrypoint index](13-reference/entrypoint-index.md)
- [File index](13-reference/file-index.md)
- [Module index](13-reference/module-index.md)
- [Symbol index](13-reference/symbol-index.md)
- [Terminology](13-reference/terminology.md)

### _evidence

- [Evidence Tree](_evidence/README.md)
- [Command Observations](_evidence/command-observations.md)
- [Experiment Log](_evidence/experiment-log.md)
- [Source Inventory](_evidence/source-inventory.md)
- [Verification Manifest](_evidence/verification-manifest.md)
