# Start Here

This page gives four reading paths through the wiki, one per kind of reader, each ordered so every page builds on the previous one.

## New to this codebase

This path takes a developer from zero to a first useful scan.

1. [01-system/overview.md](01-system/overview.md): the four tools and how they relate.
2. [02-installation/installation.md](02-installation/installation.md) and [02-installation/verification.md](02-installation/verification.md).
3. [03-getting-started/quickstart.md](03-getting-started/quickstart.md), then [03-getting-started/first-project.md](03-getting-started/first-project.md).
4. [03-getting-started/troubleshooting-first-run.md](03-getting-started/troubleshooting-first-run.md).
5. [DISCOVERY-LEDGER.md](DISCOVERY-LEDGER.md) executive summary.

## Experienced developer

This path covers configuration, CI, and limits.

1. [05-cli-and-tools/command-reference.md](05-cli-and-tools/command-reference.md) and [05-cli-and-tools/exit-codes.md](05-cli-and-tools/exit-codes.md).
2. [06-configuration/configuration-atlas.md](06-configuration/configuration-atlas.md), [06-configuration/precedence.md](06-configuration/precedence.md), [06-configuration/configuration-pitfalls.md](06-configuration/configuration-pitfalls.md).
3. [08-extensions/composition-patterns.md](08-extensions/composition-patterns.md) for the delta-gate ratchet.
4. [11-verification/known-limitations.md](11-verification/known-limitations.md).

## Autonomous agent

This path gives an agent the invocation contracts and recovery rules it needs.

1. [10-agent-usage/agent-quickstart.md](10-agent-usage/agent-quickstart.md).
2. [10-agent-usage/tool-selection.md](10-agent-usage/tool-selection.md) and [10-agent-usage/automation-contracts.md](10-agent-usage/automation-contracts.md).
3. [10-agent-usage/failure-recovery.md](10-agent-usage/failure-recovery.md).
4. Parse [_evidence/capability-registry.jsonl](_evidence/capability-registry.jsonl) and [_evidence/configuration-registry.tsv](_evidence/configuration-registry.tsv) rather than prose.

## Library consumer

This path covers embedding the tools in Python programs.

1. [04-library-api/overview.md](04-library-api/overview.md) and [04-library-api/public-api.md](04-library-api/public-api.md).
2. [10-agent-usage/programmatic-invocation.md](10-agent-usage/programmatic-invocation.md) for the side-effect-free doctor path ([D-12](DISCOVERY-LEDGER.md#d-12)).
3. [04-library-api/internal-interfaces.md](04-library-api/internal-interfaces.md) and [07-internals/call-chains.md](07-internals/call-chains.md).
4. [08-extensions/customization.md](08-extensions/customization.md).
