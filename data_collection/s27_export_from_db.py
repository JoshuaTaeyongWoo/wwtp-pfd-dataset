"""
s27_export_from_db.py — read Label Studio's SQLite database directly: progress, JSON export, backup.

Why: the pilot server runs on the adjudicator's laptop and is often off; the JSON export otherwise needs the
server up plus an API token. The database is a single file, so the three things we need (how far the
annotators are, the per-project JSON that s17/s19/s22 read, and a backup copy) can all be done from the file.

Sandbox note (2026-11-24): inside the Claude desktop app, %LOCALAPPDATA% is virtualised, so
C:\\Users\\<u>\\AppData\\Local\\label-studio\\... shows an empty copy from 2026-11-17, not the real database.
The loopback admin share \\\\localhost\\C$\\Users\\<u>\\AppData\\Local\\... bypasses the virtualisation and is the
default --db here. From a normal PowerShell both paths are the same file.

The database is always copied to a temp file before reading (safe while the server is running).

Usage:
  python s27_export_from_db.py --status                                   # tasks / annotations per project
  python s27_export_from_db.py --export pilot_A,pilot_B --out data/pilot/exports   # -> pilot_A.json, pilot_B.json
  python s27_export_from_db.py --backup                                   # -> data/pilot/ls_backup/label_studio_YYYYMMDD_HHMM.sqlite3
  python s27_export_from_db.py --db path/to/label_studio.sqlite3 --status  # any copy of the database
"""
from __future__ import annotations

import argparse
import json
import os
import shutil
import sqlite3
import sys
import tempfile
from datetime import datetime
from pathlib import Path

from common import DATA

USER = Path(os.environ.get("USERPROFILE", Path.home()))
REAL_DB = Path("//localhost/" + USER.drive.rstrip(":") + "$") / USER.relative_to(USER.anchor) / "AppData/Local/label-studio/label-studio/label_studio.sqlite3"
BACKUP_DIR = DATA / "pilot" / "ls_backup"


def snapshot(db: Path) -> Path:
    """Copy the database to a temp file and return that path (read the copy, never the live file)."""
    if not db.exists():
        sys.exit(f"database not found: {db}")
    tmp = Path(tempfile.mkdtemp(prefix="ls_db_")) / "label_studio.sqlite3"
    shutil.copy2(db, tmp)
    return tmp


def connect(path: Path) -> sqlite3.Connection:
    con = sqlite3.connect(f"file:{path.as_posix()}?mode=ro", uri=True)
    con.row_factory = sqlite3.Row
    return con


def projects(con: sqlite3.Connection) -> list[sqlite3.Row]:
    return con.execute("select id, title, created_at, updated_at, label_config from project order by id").fetchall()


def status(con: sqlite3.Connection) -> list[dict]:
    rows = []
    for p in projects(con):
        n_tasks = con.execute("select count(*) from task where project_id=?", (p["id"],)).fetchone()[0]
        n_labeled = con.execute("select count(*) from task where project_id=? and is_labeled=1", (p["id"],)).fetchone()[0]
        anns = con.execute(
            """select count(*) n, sum(a.was_cancelled) skipped, max(a.updated_at) last, sum(a.lead_time) secs
               from task_completion a join task t on t.id=a.task_id where t.project_id=?""", (p["id"],)).fetchone()
        rows.append({"id": p["id"], "title": p["title"], "tasks": n_tasks, "labeled": n_labeled,
                     "annotations": anns["n"] or 0, "skipped": anns["skipped"] or 0, "last": (anns["last"] or "")[:16],
                     "hours": round((anns["secs"] or 0) / 3600, 2)})
    return rows


def export_project(con: sqlite3.Connection, title: str) -> list[dict]:
    """Label Studio 'JSON' export shape, enough for s17 / s19 / s22: tasks with data + annotations[result]."""
    p = con.execute("select id from project where title=?", (title,)).fetchone()
    if p is None:
        sys.exit(f"no project named {title!r}; have {[r['title'] for r in projects(con)]}")
    tasks = []
    for t in con.execute("select * from task where project_id=? order by inner_id, id", (p["id"],)):
        anns = []
        for a in con.execute("select * from task_completion where task_id=? order by was_cancelled, id", (t["id"],)):
            anns.append({"id": a["id"], "completed_by": a["completed_by_id"], "result": json.loads(a["result"] or "[]"),
                         "was_cancelled": bool(a["was_cancelled"]), "ground_truth": bool(a["ground_truth"]),
                         "created_at": a["created_at"], "updated_at": a["updated_at"], "lead_time": a["lead_time"],
                         "task": t["id"], "project": p["id"]})
        tasks.append({"id": t["id"], "inner_id": t["inner_id"], "project": p["id"], "data": json.loads(t["data"]),
                      "meta": json.loads(t["meta"] or "{}"), "created_at": t["created_at"], "updated_at": t["updated_at"],
                      "is_labeled": bool(t["is_labeled"]), "total_annotations": t["total_annotations"],
                      "cancelled_annotations": t["cancelled_annotations"], "annotations": anns, "predictions": [], "drafts": []})
    return tasks


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--db", default=str(REAL_DB), help=f"database file (default: real server DB via loopback share: {REAL_DB})")
    ap.add_argument("--status", action="store_true", help="print tasks / annotations per project")
    ap.add_argument("--export", default="", help="comma-separated project titles to export as <title>.json")
    ap.add_argument("--out", default=str(DATA / "pilot" / "exports"))
    ap.add_argument("--backup", action="store_true", help=f"copy the database to {BACKUP_DIR}/label_studio_YYYYMMDD_HHMM.sqlite3")
    a = ap.parse_args()
    if not (a.status or a.export or a.backup):
        a.status = True

    db = Path(a.db)
    snap = snapshot(db)
    print(f"database: {db} ({db.stat().st_size:,} bytes, modified {datetime.fromtimestamp(db.stat().st_mtime):%Y-%m-%d %H:%M})")
    con = connect(snap)

    if a.status:
        rows = status(con)
        print(f"{'id':>3} {'project':<12} {'tasks':>5} {'labeled':>7} {'annots':>6} {'skipped':>7} {'hours':>6}  last annotation")
        for r in rows:
            print(f"{r['id']:>3} {r['title']:<12} {r['tasks']:>5} {r['labeled']:>7} {r['annotations']:>6} {r['skipped']:>7} {r['hours']:>6}  {r['last']}")

    if a.export:
        out = Path(a.out); out.mkdir(parents=True, exist_ok=True)
        for title in [s.strip() for s in a.export.split(",") if s.strip()]:
            tasks = export_project(con, title)
            dest = out / f"{title}.json"
            dest.write_text(json.dumps(tasks, ensure_ascii=False, indent=1), encoding="utf-8")
            n_ann = sum(1 for t in tasks for x in t["annotations"] if not x["was_cancelled"])
            print(f"{title}: {len(tasks)} tasks, {n_ann} annotations -> {dest}")

    if a.backup:
        BACKUP_DIR.mkdir(parents=True, exist_ok=True)
        dest = BACKUP_DIR / f"label_studio_{datetime.now():%Y%m%d_%H%M}.sqlite3"
        shutil.copy2(snap, dest)
        print(f"backup -> {dest} ({dest.stat().st_size:,} bytes)")

    con.close()
    shutil.rmtree(snap.parent, ignore_errors=True)


if __name__ == "__main__":
    main()
