# Evidence Tree

This directory holds the raw and machine-readable evidence behind every claim in the wiki, so a later agent can re-run the investigation against a new version without rebuilding it.

## Contents

This section says what each file is and who produced it.

| File | Format | Contents |
|---|---|---|
| [source-inventory.md](source-inventory.md) | Markdown | Identity, versions, source-of-truth map, every file with hash |
| [source-files.tsv](source-files.tsv) | TSV | path, bytes, lines, sha256 prefix, kind |
| [source-coverage.tsv](source-coverage.tsv) | TSV | per-file inspection lanes and depth (listed, read, diffed, executed) |
| [capability-registry.jsonl](capability-registry.jsonl) | JSONL | one capability per line (id, sources, exposure, invocation, side effects, tests, verification, wiki page, discoveries) |
| [configuration-registry.tsv](configuration-registry.tsv) | TSV | every configuration surface with defaults, precedence, effect, verification |
| [command-observations.md](command-observations.md) | Markdown | index of observed CLI behaviors with exit codes |
| [experiment-log.md](experiment-log.md) | Markdown | index of every experiment set and where its raw log lives |
| [verification-manifest.md](verification-manifest.md) | Markdown | which checks passed, failed, or were not run |
| [agent-findings/](agent-findings/) | mixed | lane reports, scripts, fixtures, logs (see below) |

## Lanes

This section records which research lanes actually ran; no other delegation occurred.

| Lane | Roles from the mission | Directory |
|---|---|---|
| A | Architectural Archaeologist + Programmatic API | [lane-a-arch-api](agent-findings/lane-a-arch-api/README.md) |
| B | Configuration & Implicit Behavior | [lane-b-config](agent-findings/lane-b-config/configuration-findings.md) |
| D | CLI/Tools/Integration + Tests/Runtime/Failure Modes | [lane-d-cli-tests](agent-findings/lane-d-cli-tests/README.md) |
| F | Extensions & Composition (incl. fieldkit, harness, doc reconciliation) | [lane-f-ext](agent-findings/lane-f-ext/README.md) |
| W1-W4 | Wave 5 page writers (Documentation Architect role shared with the lead) | canonical pages only |
| H | Independent Skeptical Reviewer | [review](agent-findings/review-h/) |
| Lead | coordination, reconciliation, ledger, atlas, indexes | top-level pages |

Lane briefs: [BRIEF.md](agent-findings/BRIEF.md), [WRITING-BRIEF.md](agent-findings/WRITING-BRIEF.md).

## Repeating the investigation

This section says how to re-run against a later version.

1. Unpack the new tree, commit a baseline, regenerate `source-files.tsv` and diff its hash column against this one to find changed files.
2. Re-run the lane D experiment set (`agent-findings/lane-d-cli-tests/experiments.jsonl` holds every command) and lane F's staged repro scripts (`agent-findings/lane-f-ext/repro/s0`-`s6`) in /tmp.
3. For every ledger entry, re-run its "Reproduce" step; mark the entry resolved with the version that fixed it instead of deleting it.
