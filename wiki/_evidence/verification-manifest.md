# Verification Manifest

This manifest records which checks passed, failed, or were not run, and how much of the wiki's VERIFIED labeling rests on stored records versus re-runnable inline scripts.

## Checks that ran

This section lists the executed checks with their results.

| Check | Command (cwd under /tmp) | Result | Record |
|---|---|---|---|
| Repo smoke suite, Py 3.12.15 | `pytest -q -p no:cacheprovider tests/` on a copy | 10 passed, 2 failed (exit 1); failures are D-01 | [lane D test-coverage](agent-findings/lane-d-cli-tests/test-coverage.md) |
| Repo smoke suite, Py 3.10.22 / 3.11.17 | same | 10 passed, 2 failed on each | [W2 runs](../11-verification/verification-results.md) |
| Fieldkit selftest | `selftest.py --python <venv python>` | 29/29 on 3.10, 3.11, 3.12 (one 3.11 run killed by sandbox, exit 137, then 29/29); `--python` plus `PYTHONPATH=src` gives 28/29 | [verification results](../11-verification/verification-results.md) |
| Help surfaces | 13 dispatcher surfaces, src vs installed | byte-identical after removing SyntaxWarning lines | [help-surfaces-raw.txt](agent-findings/lane-d-cli-tests/help-surfaces-raw.txt) |
| PyPI 0.1.0 diff | `pip download somnus-debug==0.1.0 --no-deps` + diff | code identical after header strip; `default_config.yaml` differs | [install-vs-source](agent-findings/lane-d-cli-tests/install-vs-source.md) |
| Reproducible probe script | 15 probes | 15/15 matched expected | [reproducible probes](../11-verification/reproducible-probes.md) |
| Recipes | 19 recipes in `09-recipes/` | all behaved as documented; logs echo `[exit=N]` | [execution log](../09-recipes/execution-log.md), `09-recipes/_repro/logs/` |
| YAML parser vs PyYAML | Y01-Y58 | 24/58 agree; every divergence classified | [w3-config-probes/probe.out](agent-findings/w3-config-probes/probe.out) |
| Doc structure gate | `somnus-doc-system/scripts/check_docs.py` over all wiki pages | 0 errors, 0 warnings after fixes | lead run, final |
| Skeptical review (H) | 27 of 34 ledger entries re-run; 15 examples run verbatim; 45 random citations; 20 registry rows; 25 capabilities | 2 high, 8 medium, 12 low corrections; all applied (see below) | [REVIEW.md](agent-findings/review-h/REVIEW.md) |

## Review corrections applied

This section records how each review correction was resolved.

H-01 to H-09 and H-11 to H-22 were applied by the lead on 2026-11-11 (exit-code pages and contracts now qualify the missing-root case per D-29; malformed-YAML behavior corrected; silent_failures wording narrowed; capability registry line ranges and the `build_index` exposure fixed; citation drift corrected; example outputs annotated). H-10 is handled by disclosure below rather than relabeling.

## Records that do not survive (H-10)

This section discloses VERIFIED claims whose raw run records were lost, so readers can weigh them.

A sandbox reset at about 00:40 UTC on 2026-11-12 wiped `/tmp`. Consequences:

- **W1 (01-system, 04-library-api, 07-internals):** example scripts under `/tmp/w1/` were recreated and re-run after the reset and their outputs matched; the scripts that matter are reproduced inline on the pages, and the outputs shown are the captured ones. No separate run table was stored. Treat these VERIFIED tags as "executed, inline-reproducible, not archived".
- **W3 (06-configuration):** the YAML probe (`probe.py`, `probe.json`, `probe.out`), the registry and page generators, and the 12 configuration recipes with their log (`recipes.sh`, `recipes.log`) are archived in [w3-config-probes/](agent-findings/w3-config-probes/). Runtime probes tagged E*, G*, M*, H*, P*, OB*, R* on the configuration pages were run but their transcripts were not archived; review-h re-ran a sample and all held.
- **Lane A:** `README.md` (reconstructed by the lead) and `undocumented-primitives.md` (coverage rebuilt by W1 from source) were lost.
- Review H re-ran 27 ledger reproductions and 15 page examples after the reset; all reproduced except the three low-severity output annotations now noted on their pages.

## Not run

This section lists checks that were not executed and why.

| Check | Reason |
|---|---|
| Live pycache-clean with scalar `roots` | Could sweep from `/`; constructor evidence only |
| Windows behavior | No Windows runner |
| Python below 3.10; 3.13 through the dispatcher with PyYAML | Not available / not attempted |
| Editable install | Would write into the repo |
| Real `pip install` from PyPI | Only `pip download` used |
| GitHub render of README (PLAN item 4) and of this wiki | Requires pushing; nothing pushed |
| Concurrent multi-process stress beyond two scans | Out of bounded scope |
| Comparison with the canonical `calisweetleaf/somnus-debug` master | Kept offline from the remote |
