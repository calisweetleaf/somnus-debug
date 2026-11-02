---
name: somnus-debug-fieldkit
description: >
  Set up and operate the somnus-debug CLI (pip install somnus-debug) in any
  Python codebase. Use when entering a new, early, or not-yet-onboarded repo
  (no .somnus-debug/PROFILE.md); when asked to set up, onboard, configure, or
  run somnus-debug; and for all later use: doctor diagnostics and the
  baseline-fix-rescan loop, triaging doctor findings, structure indexing,
  pycache cleanup, single-test harness scaffolding, the AGENTS.md block, or
  attaching evidence to Somnus Accelerate or another harness. Ships tested
  scripts: onboard.py (survey + verified project profile), delta.py (baseline
  vs latest regression gate), selftest.py (29-check skill-vs-CLI contract).
  For using somnus-debug, not developing the package. Graphify is deferred.
---

# somnus-debug fieldkit

somnus-debug is four Python tools behind one CLI: `doctor` (static production-readiness diagnostics), `structure` (one-file AST index), `pycache-clean` (bytecode cache removal), and `init-test-harness` (single-test contract scaffold). This skill turns them into a repeatable loop: **onboard once, then baseline → change → rescan → delta → triage, until the delta is clean.**

## Start here (every session)

1. **Authority.** Read the repo's `AGENTS.md`, tests, CI, and task packet. They own acceptance; doctor is evidence.
2. **CLI.** Run `somnus-debug --version`, or `<venv>/bin/python -m somnus_debug.cli --version`. If it's missing, read [install](references/install.md). The install is `pip install somnus-debug`, ideally into the project's own venv. Don't install silently.
3. **Profile.** Look for `.somnus-debug/PROFILE.md`.
   - **Present:** read it. It has this repo's runner, config, coverage, and exact commands. Go to the [loop](references/doctor-loop.md).
   - **Absent:** onboard. Run plan mode, read the output, then apply:

     ```console
     python3 <skill-dir>/scripts/onboard.py <repo>                      # survey + coverage proof; writes nothing
     python3 <skill-dir>/scripts/onboard.py <repo> --apply --baseline   # .somnus-debug/ profile + baseline
     ```

     Then append [the AGENTS block](templates/AGENTS_APPENDIX.md) to the repo's instructions. Details and failure handling: [onboarding](references/onboarding.md).
4. **Route** with the table below. Load only the reference the task needs.

## The loop, in commands

From `.somnus-debug/`, using the runner printed in `PROFILE.md` (shown here as `sd`):

```console
sd doctor scan .. -c python_doctor.yaml -o runs/baseline.md --json-output runs/baseline.json   # once, before edits
# ...make the real change, run the project's own tests...
sd doctor scan .. -c python_doctor.yaml -o runs/latest.md --json-output runs/latest.json
python3 <skill-dir>/scripts/delta.py runs/baseline.json runs/latest.json --dispositions dispositions.json
```

`delta.py` exits 0 when clean, 1 on a new serious or critical finding, 2 on a coverage regression, and 3 on bad input. For every new or persisting in-scope finding, use [findings](references/findings.md) to decide one of four outcomes: fix, out of scope, disposition (with a reason in `dispositions.json`), or unverified. Repeat after each repair batch.

## Router

| Need | Open | First action |
|---|---|---|
| Not onboarded, new or early repo, "set up somnus-debug" | [onboarding](references/onboarding.md) | `onboard.py <repo>`, then `--apply --baseline` |
| CLI missing, which env to install into, `missing_imports` noise | [install](references/install.md) | `pip install somnus-debug` into the project venv; run `selftest.py` |
| Changing Python, or a production-readiness claim | [doctor loop](references/doctor-loop.md) | Baseline, change, rescan, `delta.py` |
| "What does this finding mean / is it a false positive?" | [findings](references/findings.md) | Find the category; fix or disposition with a reason |
| Exact flags, outputs, file side effects | [commands](references/commands.md) | Confirm with `--help`; `selftest.py` checks them all |
| What each tool is and isn't | [topology](references/topology.md) | Read the anti-concepts |
| Somnus Accelerate packet | [Accelerate integration](references/accelerate-integration.md) | Put scan + delta + native gate in the packet's evidence |
| Hook, CI, watcher decision | [automation](references/automation.md) | Use the lightest existing seam; no watcher by default |
| Docs disagree with behavior, after an upgrade | [provenance](references/provenance.md) | Run `selftest.py`; the CLI wins |

## Scripts

| Script | Does | Exit codes |
|---|---|---|
| `scripts/onboard.py <repo> [--apply] [--baseline] [--new-config] [--python PY]` | Surveys the tree, picks the runner (project venv → PATH), proves coverage, writes `.somnus-debug/` without overwriting | 0 ok · 1 usage · 2 coverage failure · 3 no CLI |
| `scripts/delta.py BASE.json LATEST.json [--dispositions F] [--json]` | Line-independent finding diff, coverage check, stale-disposition report | 0 clean · 1 regression · 2 coverage · 3 input |
| `scripts/selftest.py [--python PY]` | 29 fixture checks proving every behavioral claim in this skill | 0 pass · 1 drift · 3 no CLI |

All three are stdlib-only, invoke subprocesses with argv lists (never a shell), and never write outside their stated targets.

## Load-bearing rules

1. **Python change ⇒ the loop.** Don't close a Python change without a post-change scan and a `delta.py` result, or a plainly stated blocker.
2. **A doctor result is evidence, not a verdict.** It is static analysis only. The project's tests and gates decide acceptance. 0.1.0 never emits `test_gaps`, so doctor tells you nothing about test coverage.
3. **Coverage first.** Check `files=` on every scan. A zero-file scan exits 0. `onboard.py` and `delta.py` both fail loudly on it.
4. **Run doctor in the project's environment.** Otherwise third-party and `src/` imports become `missing_imports` noise. The profile runner handles this.
5. **Disposition, don't mute.** Never lower severities or gates, exclude source trees, rename to dodge a check, or pad code to satisfy a heuristic. Record accepted findings in `dispositions.json` with reasons.
6. **Respect mutating tools.** `pycache-clean` deletes files: dry-run first, and the profile config is dry-run locked. `init-test-harness` writes files and refuses overwrite: never pass `--force` without authority. Don't install CI, hooks, or watchers by default.
7. **Keep it local.** The skill is global. Configs, state, reports, and dispositions live in the target repo's `.somnus-debug/`. Its existing `AGENTS.md`, tests, and CI stay authoritative.

## Sharp edges (0.1.0, all re-proven by `selftest.py`)

- Every `doctor` call, even `--help`, writes `production_doctor.log` to the **current directory**. Run from `.somnus-debug/` or a temp dir.
- `doctor scan` without `-o` writes `production_doctor_report.md` and `.json` into the **project root**. Always pass `-o` and `--json-output`.
- There is no config auto-discovery. Without `-c`, built-in defaults apply, even if a `python_doctor.yaml` sits at the root.
- Doctor exit codes: 0 pass, 1 serious, 2 critical, 4 config or doctor error, 5 runtime failure.
- `silent_failures` only accepts `raise` or calls spelled exactly `logging.error|exception` or `logger.error|exception`. `log.error(...)` counts as silent.
- `pycache-clean` excludes match directory names only (`node_modules`, not `node_modules/*`). Relative `roots` resolve against cwd. The default `--config` is `./config.yaml`.
- Older copied configs with Somnus-style `tools/*.py` and `test/*.py` globs scan zero files in most repos. The current `init-config` default is `*.py`.

## Done means

The requested change is complete. Native tests and gates pass. The final scan covers every edited file. `delta.py` exits 0, or every remaining new serious finding is explained. `dispositions.json` has no stale entries. The handoff states the CLI version, the runner, the delta verdict, the dispositions added, and any proof that wasn't available.

## Boundaries

Graphify is deferred: never present `structure` indexes or doctor's import cycles as a full semantic graph. For exact behavior, the installed CLI's `--help` and `selftest.py` outrank these references. When they disagree, update the reference.
