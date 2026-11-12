# State and persistence

This page documents everything the toolkit writes and keeps: the doctor's SQLite state store and report tree, the log file, and the files the other tools produce. The schema below was read from source and confirmed against a live database.

## What persists, and who owns it

This section lists every persistent artifact and the directory it is relative to, which is the source of most surprises.

| Artifact | Tool | Directory it is relative to | Lifetime |
|---|---|---|---|
| `production_doctor.log` | doctor | **cwd** of the process | appended forever |
| `<report_basename>.md` / `.json` | doctor scan | `-o` / `--json-output` (relative to cwd), else the **scanned project root** | overwritten each scan |
| `<state_dir>/state.sqlite3` (+ `-wal`, `-shm`) | doctor scan, history, rollback | scanned project root | grows, never pruned |
| `<state_dir>/<reports_dir>/<run_id>/<basename>.{md,json}` | doctor scan | project root | one directory per distinct second |
| `<state_dir>/<reports_dir>/latest.{md,json}` | doctor scan, rollback | project root | overwritten |
| `python_doctor.yaml` | doctor init-config | cwd or `-o` | one-time |
| `self_check_report.{md,json}` (+ state) | doctor self-check | the installed `somnus_debug/doctor/` directory | overwritten |
| index Markdown | structure | `-o` / `--update-doc` | overwritten |
| `log_file` | pycache-clean | config value resolved against cwd | appended |
| `run_test.py`, `CONTRACT.md` | init-test-harness | target dir | one-time |

Defaults: `state_dir=".python_doctor"`, `reports_dir="reports"`, `report_basename="production_doctor_report"` (`src/somnus_debug/doctor/core.py:474-476`). Path roots: `src/somnus_debug/doctor/core.py:1919-1925`, `:1955-1962`, `:2181`, `:2123-2127`. [VERIFIED] [lane-a architecture §3.7](../_evidence/agent-findings/lane-a-arch-api/architecture.md), [lane-b configuration-findings §2.1](../_evidence/agent-findings/lane-b-config/configuration-findings.md).

`state_dir`, `reports_dir`, and `report_basename` are not confined. Absolute paths or `..` segments are accepted, so state can land outside the project. [VERIFIED] [lane-b configuration-findings §4](../_evidence/agent-findings/lane-b-config/configuration-findings.md) (S1-S3).

Nothing is global or per-user. The scanned project owns its state, and the cwd owns only the log.

## SQLite schema

This section gives the exact schema, created by `StateStore.initialize()` on every state access.

```sql
PRAGMA journal_mode=WAL;

CREATE TABLE IF NOT EXISTS runs (
  run_id          TEXT PRIMARY KEY,      -- UTC "%Y%m%dT%H%M%SZ", one-second resolution
  project_root    TEXT NOT NULL,         -- stored, never filtered on
  config_hash     TEXT NOT NULL,         -- sha256 of the merged config JSON; never compared
  started_at      TEXT NOT NULL,
  completed_at    TEXT NOT NULL,         -- history orders by this column
  status          TEXT NOT NULL,         -- always "complete"
  files_scanned   INTEGER NOT NULL,
  total_issues    INTEGER NOT NULL,
  critical_issues INTEGER NOT NULL,
  serious_issues  INTEGER NOT NULL,
  minor_issues    INTEGER NOT NULL,
  info_issues     INTEGER NOT NULL,
  report_md       TEXT NOT NULL,         -- absolute path of the per-run state copy
  report_json     TEXT NOT NULL,
  report_hash     TEXT NOT NULL          -- sha256(markdown + json_text)
);

CREATE TABLE IF NOT EXISTS file_snapshots (
  run_id        TEXT NOT NULL,
  relative_path TEXT NOT NULL,
  file_hash     TEXT NOT NULL,           -- sha256 of file bytes; "" for unreadable files
  size_bytes    INTEGER NOT NULL,
  modified_time TEXT NOT NULL,           -- ISO UTC with Z, or "unavailable"
  PRIMARY KEY (run_id, relative_path),
  FOREIGN KEY (run_id) REFERENCES runs(run_id)
);

CREATE TABLE IF NOT EXISTS report_aliases (
  alias       TEXT PRIMARY KEY,          -- only 'latest' is ever written
  run_id      TEXT NOT NULL,
  report_md   TEXT NOT NULL,
  report_json TEXT NOT NULL,
  updated_at  TEXT NOT NULL,
  FOREIGN KEY (run_id) REFERENCES runs(run_id)
);
```

The column comments are this page's annotations; the DDL is otherwise verbatim. [SOURCE-CONFIRMED] `src/somnus_debug/doctor/core.py:1927-1940` (DDL), `:1964-1979` (insert values). [VERIFIED] `/tmp/w1/ex_state.py` (exit 0) read `sqlite_master` from a live database and printed exactly these three `CREATE TABLE` statements, with `PRAGMA journal_mode` = `wal`.

Foreign keys are declared but not enforced: SQLite enforces them only with `PRAGMA foreign_keys=ON`, which the code never sets. [SOURCE-CONFIRMED] no such pragma in the file. This has no observable effect today, because nothing deletes rows.

## Write path

This section shows the order of writes in a stateful scan, which determines what survives a failure.

`StateStore.persist(result, markdown, json_text, paths)` (`src/somnus_debug/doctor/core.py:1964-1979`):

1. `initialize()`: `mkdir -p` of the reports root, then the DDL above.
2. Six calls to `write_text_atomic`: the project-root md and json, the `reports/<run_id>/` md and json, and `reports/latest.{md,json}`.
3. One connection: `INSERT OR REPLACE INTO runs`, `executemany INSERT OR REPLACE INTO file_snapshots`, and `INSERT OR REPLACE INTO report_aliases ('latest', …)`. Committed by the connection context manager.

`write_text_atomic` writes `.<name>.tmp` in the target directory, then calls `Path.replace`, so each file is replaced atomically on POSIX (`:2012-2020`). The temp name is fixed rather than unique, so two concurrent doctor processes writing the same report can collide on it. [HYPOTHESIS] from source; not exercised. The six files and the database rows are not one transaction. A database failure at step 3 raises `StateStoreError` (exit 4) after the reports already exist on disk.

## Read paths

This section lists what reads the state and with which query.

| Reader | Query | Notes |
|---|---|---|
| `previous_file_index()` (`:1942-1953`) | `SELECT run_id FROM report_aliases WHERE alias='latest'`, then `SELECT relative_path, file_hash FROM file_snapshots WHERE run_id=?` | feeds `StateDelta`; after a rollback, the delta is computed against the rolled-back run |
| `history(limit)` (`:1981-1989`) | `SELECT … FROM runs ORDER BY completed_at DESC LIMIT ?` | creates the store if absent |
| `rollback(run_id)` (`:1991-2009`) | `SELECT … FROM runs WHERE run_id=?`, copy the stored md and json over `latest.*`, `INSERT OR REPLACE` the alias | fails with `StateStoreError` if the run or its files are missing |

No reader filters by `project_root` or compares `config_hash`. A state directory shared by two projects (through an absolute `state_dir`) mixes their histories. [SOURCE-CONFIRMED] queries above; [HYPOTHESIS] for the shared-directory consequence.

## Known persistence defects

This section collects the verified ways the state can mislead, each with its discovery entry.

- **Same-second overwrite.** One-second `run_id` plus `INSERT OR REPLACE` means a second scan in the same second replaces the first. [VERIFIED] `/tmp/w1/cli`: two scans, one row. [D-08](../DISCOVERY-LEDGER.md#d-08).
- **Rollback is partial.** It moves `reports/latest.*` and the alias, not the project-root report. [VERIFIED] [D-09](../DISCOVERY-LEDGER.md#d-09).
- **Read commands create state.** `history` on a fresh tree creates `.python_doctor/`. [VERIFIED] [D-10](../DISCOVERY-LEDGER.md#d-10).
- **History needs the scan's config.** `history` and `rollback` take their own `-c`. With a custom `state_dir` and no `-c`, they look in `.python_doctor/` and report "No recorded runs found." [VERIFIED] [lane-b configuration-findings §2.1](../_evidence/agent-findings/lane-b-config/configuration-findings.md).
- **Degradation is scan-only.** If the database cannot be opened, `scan` warns and runs stateless. `history` and `rollback` exit 4. The root duplicate `python_production_doctor.py` lacks the scan fallback. [VERIFIED] [D-28](../DISCOVERY-LEDGER.md#d-28).

## Executed example

This section shows a complete stateful cycle through the library API.

```python
# /tmp/w1/ex_state.py (abridged)
from pathlib import Path
from somnus_debug.doctor import core as d
cm = d.ConfigManager(None)
root = Path("st/proj").resolve()
store = d.StateStore(root, cm.config)
prev = store.previous_file_index()                 # creates .python_doctor/
res = d.ProjectScanner(root, cm).scan(prev)
md, js = d.MarkdownReportWriter(cm.config).render(res), d.dumps_json(res)
store.persist(res, md, js, store.report_paths(res.run_id, None, None))
print([r.run_id for r in store.history(10)])
store.rollback(store.history(10)[-1].run_id)
```

Executed: yes (`/tmp/w1`, PYTHONPATH=src, exit 0). Output with two runs separated by `sleep(1.1)`:

```
run 0 20261112T003555Z delta new/unchanged 6 0
run 1 20261112T003556Z delta new/unchanged 0 6
journal ('wal',)
runs (2,) snapshots (12,) aliases [('latest', '20261112T003556Z')]
history ['20261112T003556Z', '20261112T003555Z']
rollback -> 20261112T003555Z alias now ('20261112T003555Z',)
StateStoreError: Run ID does not exist in state history.
```

## Sources

This section lists the code, evidence files, and probes this page rests on.

- `src/somnus_debug/doctor/core.py:474-476`, `:1916-2031`, `:2061-2127`, `:2179-2181`
- [lane-a architecture.md §3.4, §3.7](../_evidence/agent-findings/lane-a-arch-api/architecture.md)
- [lane-b configuration-findings.md §2.1, §4](../_evidence/agent-findings/lane-b-config/configuration-findings.md)
- [lane-d experiment-log.md](../_evidence/agent-findings/lane-d-cli-tests/experiment-log.md) (D38, D39)
- Executed probes: `/tmp/w1/ex_state.py`, `/tmp/w1/cli`
