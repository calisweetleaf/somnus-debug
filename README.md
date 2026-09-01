<div align="center">

<svg width="460" height="200" viewBox="0 0 460 200" xmlns="http://www.w3.org/2000/svg">
  <defs>
    <linearGradient id="sdGrad" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" style="stop-color:#667eea;stop-opacity:1" />
      <stop offset="50%" style="stop-color:#764ba2;stop-opacity:1" />
      <stop offset="100%" style="stop-color:#c9a0dc;stop-opacity:1" />
    </linearGradient>
    <filter id="sdGlow">
      <feGaussianBlur stdDeviation="3" result="b"/>
      <feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge>
    </filter>
  </defs>
  <rect width="460" height="200" fill="#0d1117" rx="14"/>
  <rect x="1" y="1" width="458" height="198" fill="none" stroke="#1e2430" stroke-width="1" rx="14"/>
  <text x="230" y="92" font-family="'Courier New', monospace" font-size="42" fill="url(#sdGrad)" text-anchor="middle" filter="url(#sdGlow)" font-weight="bold" letter-spacing="2">somnus-debug</text>
  <text x="230" y="120" font-family="'Courier New', monospace" font-size="13" fill="#8b949e" text-anchor="middle" letter-spacing="1">Python Developer Toolkit</text>
  <text x="230" y="144" font-family="'Courier New', monospace" font-size="11" fill="#484f58" text-anchor="middle">4 Tools  |  Zero-Dep Core  |  One CLI  |  pip Installable</text>
  <line x1="130" y1="160" x2="330" y2="160" stroke="#21262d" stroke-width="1"/>
  <text x="230" y="180" font-family="'Courier New', monospace" font-size="9" fill="#2d333b" text-anchor="middle" letter-spacing="5">SOMNUS SOVEREIGN SYSTEMS</text>
</svg>

</div>

<p align="center"><em>What used to be four scripts copied by hand between projects, now one package with one CLI.</em></p>

<p align="center">
  <img src="https://img.shields.io/badge/License-MIT-6bcf7f?style=flat-square" alt="License: MIT"/>
  <img src="https://img.shields.io/badge/Python-3.10%20%7C%203.11%20%7C%203.12-667eea?style=flat-square" alt="Python 3.10-3.12"/>
  <img src="https://img.shields.io/badge/PyPI-not%20yet%20published-febc2e?style=flat-square" alt="Not yet on PyPI"/>
  <img src="https://img.shields.io/badge/Status-Alpha-febc2e?style=flat-square" alt="Status: Alpha"/>
  <img src="https://img.shields.io/badge/Tests-9%2F9%20passing%20(manual)-28c840?style=flat-square" alt="9/9 tests passing"/>
</p>

---

<!-- ============================================================ -->
<!-- GLOBAL STYLES — Somnus Documentation Design System v3        -->
<!-- ============================================================ -->

<style>
.t {
  background: #141414;
  border-radius: 10px;
  box-shadow: 0 12px 40px rgba(0,0,0,0.55), 0 0 0 1px #2a2a2a;
  margin: 22px 0;
  font-family: 'Menlo', 'Monaco', 'Cascadia Code', 'Courier New', monospace;
  overflow: hidden;
}
.t-hdr {
  background: #252525;
  padding: 11px 16px;
  display: flex;
  align-items: center;
  border-bottom: 1px solid #1e1e1e;
  user-select: none;
}
.t-btn { width: 13px; height: 13px; border-radius: 50%; margin-right: 8px; flex-shrink: 0; }
.t-btn.r { background: #ff5f57; box-shadow: 0 0 4px #ff5f5780; }
.t-btn.y { background: #febc2e; box-shadow: 0 0 4px #febc2e80; }
.t-btn.g { background: #28c840; box-shadow: 0 0 4px #28c84080; }
.t-title { color: #888; font-size: 12.5px; margin-left: 10px; letter-spacing: 0.4px; }
.t-tag {
  margin-left: auto;
  background: #1e1e1e;
  border: 1px solid #333;
  color: #555;
  font-size: 10px;
  padding: 2px 8px;
  border-radius: 3px;
  letter-spacing: 1px;
  text-transform: uppercase;
}
.t-body { padding: 18px 20px; font-size: 13px; line-height: 1.65; color: #d4d4d4; overflow-x: auto; }
.prompt { color: #28c840; }
.dim    { color: #555; }
.info   { color: #667eea; }
.ok     { color: #28c840; }
.warn   { color: #febc2e; }
.err    { color: #ff5f57; }
.accent { color: #c9a0dc; }
.cmd    { margin-bottom: 2px; }
.out    { margin-bottom: 3px; }
.cur {
  display: inline-block;
  width: 8px; height: 14px;
  background: #d4d4d4;
  vertical-align: text-bottom;
  animation: blink 1.1s step-end infinite;
}
@keyframes blink { 0%,100%{opacity:1} 50%{opacity:0} }
.t-code {
  white-space: pre;
  font-size: 12.5px;
  line-height: 1.6;
  overflow-x: auto;
  padding: 18px 20px;
  margin: 0;
  color: #d4d4d4;
  font-family: 'Menlo', 'Monaco', 'Cascadia Code', 'Courier New', monospace;
}
.cmt { color: #5c6370; }
.t-sep { height: 1px; background: #1e1e1e; margin: 8px 0; }
.mon-row {
  display: grid;
  grid-template-columns: 170px 1fr 96px;
  align-items: center;
  margin-bottom: 5px;
  font-size: 12.5px;
}
.mon-label { color: #888; }
.mon-bar { background: #1e1e1e; height: 9px; border-radius: 2px; overflow: hidden; position: relative; }
.mon-fill { height: 100%; border-radius: 2px; }
.mon-val { color: #c9d1d9; text-align: right; font-size: 11px; }
</style>

## What this is

Somnus's project-agnostic Python dev tooling — production-readiness
diagnostics, an AST class/definition indexer, bytecode-cache cleanup, and a
portable single-test harness scaffold — packaged as one real `pip`-installable
CLI instead of loose scripts.

**Zero runtime dependencies beyond `pyyaml`**, and that's only for
`pycache-clean` — `doctor` and `structure` are stdlib-only.

## Install

```bash
git clone <this repo>
cd somnus-agnostic-test
pip install -e .
```

`pip install somnus-debug` isn't live yet — the package is publish-ready
(MIT-licensed, real PEP 621 metadata, verified build) but hasn't actually
been uploaded anywhere. See `docs/PUBLISHING.md` for what that takes and
what's still open before it happens.

## The tools

| Command | What it does |
|---|---|
| `somnus-debug doctor ...` | AST-based production-readiness diagnostics: stubs, placeholder returns, silent exception handling, dependency cycles, docstring/type-hint coverage, security-risk patterns, TODOs. |
| `somnus-debug structure <file.py>` | Class-by-class, definition-by-definition AST index of a single Python file, with source line spans. Never imports or executes the target. |
| `somnus-debug pycache-clean ...` | Configurable removal of `__pycache__` dirs and `*.pyc`/`*.pyo` files across one or more directory trees. Dry-run by default via `--dry-run`. |
| `somnus-debug init-test-harness [dir]` | Copies the CONTRACT.md-governed single-test harness (`run_test.py`) into a target repository. |

Every tool is also installed as its own script for muscle memory:
`somnus-doctor`, `somnus-structure`, `somnus-pycache-clean`.

<div class="t">
  <div class="t-hdr">
    <div class="t-btn r"></div><div class="t-btn y"></div><div class="t-btn g"></div>
    <span class="t-title">somnus-debug · quickstart</span>
    <span class="t-tag">SESSION</span>
  </div>
  <div class="t-body">
    <div class="cmd"><span class="prompt">daeron@somnus:~$</span> pip install -e .</div>
    <div class="out dim">Successfully installed somnus-debug-0.1.0</div>
    <div class="t-sep"></div>
    <div class="cmd"><span class="prompt">daeron@somnus:~$</span> somnus-debug doctor init-config -o python_doctor.yaml</div>
    <div class="out dim">Wrote default configuration: python_doctor.yaml</div>
    <div class="t-sep"></div>
    <div class="cmd"><span class="prompt">daeron@somnus:~$</span> somnus-debug doctor scan . -o report.md</div>
    <div class="out ok">Scan complete: files=42, issues=118, critical=0, serious=9</div>
    <div class="t-sep"></div>
    <div class="cmd"><span class="prompt">daeron@somnus:~$</span> somnus-debug structure src/core.py -o CORE_INDEX.md</div>
    <div class="out dim">Class Index for `core.py` written to CORE_INDEX.md</div>
    <div class="t-sep"></div>
    <div class="cmd"><span class="prompt">daeron@somnus:~$</span> somnus-debug pycache-clean --config config.yaml --dry-run</div>
    <div class="out dim">Summary: deleted 6 directories, 0 files; freed 2.10 MiB <span class="cmt"># dry run — nothing actually removed</span></div>
    <div class="cmd" style="margin-top:8px;"><span class="prompt">daeron@somnus:~$</span> <span class="cur"></span></div>
  </div>
</div>

Full flag reference and worked examples for every command:
**[`docs/MANUAL.md`](docs/MANUAL.md)**.

## Build status

Honest, not aspirational — this reflects what's actually been verified,
not what's planned.

<div class="t">
  <div class="t-hdr">
    <div class="t-btn r"></div><div class="t-btn y"></div><div class="t-btn g"></div>
    <span class="t-title">somnus-debug · build status — 2026-09-01</span>
    <span class="t-tag">STATUS</span>
  </div>
  <div class="t-body">
    <div class="mon-row">
      <span class="mon-label">Package skeleton</span>
      <span class="mon-bar"><span class="mon-fill" style="width:100%;background:linear-gradient(90deg,#28c840,#667eea);"></span></span>
      <span class="mon-val ok">verified</span>
    </div>
    <div class="mon-row">
      <span class="mon-label">doctor / structure / pycache-clean</span>
      <span class="mon-bar"><span class="mon-fill" style="width:100%;background:linear-gradient(90deg,#28c840,#667eea);"></span></span>
      <span class="mon-val ok">verified</span>
    </div>
    <div class="mon-row">
      <span class="mon-label">init-test-harness</span>
      <span class="mon-bar"><span class="mon-fill" style="width:100%;background:linear-gradient(90deg,#28c840,#667eea);"></span></span>
      <span class="mon-val ok">verified</span>
    </div>
    <div class="mon-row">
      <span class="mon-label">Wheel build + install</span>
      <span class="mon-bar"><span class="mon-fill" style="width:100%;background:linear-gradient(90deg,#28c840,#667eea);"></span></span>
      <span class="mon-val ok">verified</span>
    </div>
    <div class="mon-row">
      <span class="mon-label">git version control</span>
      <span class="mon-bar"><span class="mon-fill" style="width:40%;background:linear-gradient(90deg,#ff5f57,#febc2e);"></span></span>
      <span class="mon-val warn">blocked</span>
    </div>
    <div class="mon-row">
      <span class="mon-label">PyPI publish</span>
      <span class="mon-bar"><span class="mon-fill" style="width:0%;"></span></span>
      <span class="mon-val err">not started</span>
    </div>
    <div class="mon-row">
      <span class="mon-label">doctor / structure feature expansion</span>
      <span class="mon-bar"><span class="mon-fill" style="width:0%;"></span></span>
      <span class="mon-val err">not started</span>
    </div>
  </div>
</div>

> **Open items.** `.git` got stuck on a stale `index.lock` during the initial
> packaging pass (a sandboxed shell couldn't clean up after itself) — see
> `docs/MANUAL.md` §7.4 for the one-command fix. `pip install somnus-debug`
> means an actual PyPI upload, which hasn't happened — see
> `docs/PUBLISHING.md`. The old root-level scripts
> (`python_production_doctor.py`, `analyze_python_structure.py`,
> `pycache_cleaner.py`, `run_test.py`, `python_doctor.yaml`) are still sitting
> next to `src/somnus_debug/` pending cleanup — harmless, just redundant.

## Using it as a library

```python
from somnus_debug.structure.core import build_index
from somnus_debug.doctor.core import ProjectScanner, ConfigManager
from somnus_debug.pycache_cleaner.core import PycacheCleaner, CleanerConfig
```

Each `core.py` is the original single-file implementation, moved into the
package rather than rewritten — anything importable from the standalone
script is importable from `somnus_debug.<tool>.core` too.

## Repository layout

```
pyproject.toml              package metadata, deps, entry points
LICENSE                      MIT
README.md                    this file
src/somnus_debug/
    cli.py                    `somnus-debug <command>` dispatcher
    doctor/core.py             = old python_production_doctor.py
    doctor/default_config.yaml = old python_doctor.yaml
    structure/core.py          = old analyze_python_structure.py
    pycache_cleaner/core.py    = old pycache_cleaner.py
    test_harness/scaffold.py + templates/{run_test.py, CONTRACT.md}
tests/test_cli_smoke.py      9 passing smoke tests
docs/
    MANUAL.md                  full command reference (start here for usage)
    PUBLISHING.md               the real-PyPI-release checklist
    CONTRACT.md                 governs run_test.py's artifact contract
    OPSEC.md                    Somnus agent operational security protocol
    Python_Doctor_QUICKSTART.md  deep config-field reference for `doctor`
```

## Documentation index

- **[docs/MANUAL.md](docs/MANUAL.md)** — day-to-day command reference, every
  flag, worked examples, troubleshooting.
- **[docs/PUBLISHING.md](docs/PUBLISHING.md)** — the checklist for actually
  shipping this to PyPI.
- **[docs/Python_Doctor_QUICKSTART.md](docs/Python_Doctor_QUICKSTART.md)** —
  full `python_doctor.yaml` field reference.
- **[docs/CONTRACT.md](docs/CONTRACT.md)** — what `run_test.py` does and
  does not own.
- **[docs/OPSEC.md](docs/OPSEC.md)** — SUPREME-authority agent security
  posture for this codebase.

---

<div align="center">

<svg width="400" height="48" viewBox="0 0 400 48" xmlns="http://www.w3.org/2000/svg">
  <rect width="400" height="48" fill="#0d1117" rx="6"/>
  <line x1="60" y1="24" x2="170" y2="24" stroke="#21262d" stroke-width="1"/>
  <line x1="230" y1="24" x2="340" y2="24" stroke="#21262d" stroke-width="1"/>
  <text x="200" y="28" font-family="'Courier New', monospace" font-size="10" fill="#484f58" text-anchor="middle" letter-spacing="3">SOMNUS SOVEREIGN SYSTEMS</text>
</svg>

</div>
