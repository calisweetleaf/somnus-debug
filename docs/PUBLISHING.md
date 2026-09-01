# Publishing somnus-debug

**Status as of 2026-09-01: not published anywhere.** `pip install somnus-debug`
does not work yet — today it's `git clone` + `pip install -e .`. `somnus-debug`
*is* confirmed unclaimed on PyPI (checked 2026-09-01), and the package is
license/metadata-ready for a public release (MIT, see `LICENSE`). This
document is the checklist for when you actually pull the trigger — nothing
in it has been run against the real index yet.

## Before the first real publish

- [ ] Decide on and create the real public repository (GitHub or wherever) and
      fill in `[project.urls]` in `pyproject.toml` (Homepage, Repository,
      Issues) — currently omitted because there is no real URL to point at.
- [ ] Get `git` actually initialized and committed (see `docs/MANUAL.md` §7.4
      for the stale-lock issue from the initial packaging pass, if it's still
      unresolved).
- [ ] Decide the real author contact (`authors` in `pyproject.toml` has a name
      only, no email — PyPI doesn't require one, but you may want it).
- [ ] Delete or archive the old root-level duplicate scripts
      (`python_production_doctor.py`, `analyze_python_structure.py`,
      `pycache_cleaner.py`, `run_test.py`, `python_doctor.yaml`) so the repo
      doesn't ship confusing dead weight — they're excluded from the actual
      package build already (only `src/`, `README.md`, `LICENSE`, `docs/**`
      are included per `[tool.hatch.build.targets.sdist]`), but they
      shouldn't linger in the repo either.
- [ ] Run the full check below and get a clean bill of health.

## Build and check locally

```bash
pip install --upgrade build twine
python -m build                      # produces dist/*.whl and dist/*.tar.gz
twine check dist/*                   # validates metadata, README rendering, etc.
```

Install the built wheel into a throwaway venv and smoke-test it before
uploading anything:

```bash
python -m venv /tmp/sd-verify && /tmp/sd-verify/bin/pip install dist/somnus_debug-*.whl
/tmp/sd-verify/bin/somnus-debug --help
/tmp/sd-verify/bin/pytest tests/  # if you copy tests/ + dev deps in too
```

## Publish to TestPyPI first

Always. Never skip straight to real PyPI, even for a "trivial" version bump.

```bash
twine upload --repository testpypi dist/*
pip install --index-url https://test.pypi.org/simple/ --no-deps somnus-debug
```

You'll need a TestPyPI account and an API token (`~/.pypirc` or
`TWINE_USERNAME=__token__` / `TWINE_PASSWORD=<token>` env vars). Never commit
a token to the repo.

## Publish to real PyPI

Only after the TestPyPI install actually works end to end:

```bash
twine upload dist/*
```

From that point on, `pip install somnus-debug` works for anyone, anywhere.
There is no unpublish — a version can be yanked (hidden from fresh installs,
but not deleted) but never truly removed. Treat every upload as permanent.

## Version bumps

`pyproject.toml`'s `version = "0.1.0"` is the single source of truth (no
dynamic versioning configured). Bump it before every publish — PyPI rejects
re-uploading an existing version number outright, even if the file contents
changed.

Suggested scheme while this is young: `0.1.x` for fixes/doc changes to the
current tool set, `0.x.0` for real feature additions (the planned `doctor`
report expansion, `structure --both`), `1.0.0` once you're willing to call
the CLI surface stable enough that you'd be annoyed if it broke someone's
script.

## What's already ready

- `pyproject.toml` has real PEP 621 metadata: MIT license (`license = "MIT"`
  + `license-files = ["LICENSE"]`), classifiers, keywords, Python version
  support (3.10-3.12), console-script entry points.
- `LICENSE` (MIT) is in place at the repo root.
- Build hygiene: `[tool.hatch.build] exclude` keeps runtime-generated
  artifacts (`.python_doctor/` state, `*_report.md`/`.json`,
  `production_doctor.log`, `__pycache__/`) out of the sdist/wheel even if
  they exist in the working tree from testing.
- Zero packaging surprises: build + editable install + wheel install +
  `twine check` were all verified working end-to-end (see project memory
  `packaging.md` for the record) — the only unverified step is the actual
  upload.
- `pyyaml` is correctly declared as the one real runtime dependency
  (`pycache-clean` needs it; `doctor` and `structure` don't).

## One honest caveat

`README.md` uses Daeron's Somnus Documentation Design System v3 (terminal-
window frames, inline `<style>`, gradient/glow SVG banners). That renders
richly in editors/previewers that execute embedded HTML+CSS (VS Code's
Markdown preview, for instance). **GitHub's README sanitizer strips
`<style>` blocks and most SVG filter/gradient elements**, and PyPI's
description renderer (readme_renderer) is similarly restrictive — so on
either of those two surfaces, the styled sections will likely degrade to
plain unstyled text/boxes rather than the intended terminal-chrome look.
`twine check` only validates that the README parses as valid
Markdown/reST, not that it renders as designed — it passed, but that's not
the same as "will look right on the PyPI project page." Worth checking
directly once this actually gets pushed/published, rather than assuming.
