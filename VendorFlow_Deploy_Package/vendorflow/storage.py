"""SQLite persistence for submissions, uploaded files, and active demo vendors."""

from __future__ import annotations

import json
import os
import sqlite3
import uuid
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from vendorflow.samples import SEEDED_VENDORS


def database_path() -> Path:
    override = os.environ.get("VENDORFLOW_DB")
    if override:
        return Path(override).expanduser().resolve()
    data_dir = Path(os.environ.get("VENDORFLOW_DATA_DIR", Path(__file__).resolve().parent.parent / "data"))
    data_dir.mkdir(parents=True, exist_ok=True)
    return data_dir / "vendorflow.sqlite3"


@contextmanager
def connect(db_path: str | Path | None = None):
    path = Path(db_path) if db_path else database_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(path, timeout=10)
    try:
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def initialize(db_path: str | Path | None = None) -> None:
    with connect(db_path) as conn:
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS runs (
                run_id TEXT PRIMARY KEY,
                submitted_at TEXT NOT NULL,
                decision TEXT NOT NULL,
                legal_name TEXT NOT NULL,
                contact_email TEXT,
                source TEXT NOT NULL,
                vendor_json TEXT NOT NULL,
                result_json TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS documents (
                document_id INTEGER PRIMARY KEY AUTOINCREMENT,
                run_id TEXT NOT NULL REFERENCES runs(run_id) ON DELETE CASCADE,
                doc_type TEXT NOT NULL,
                filename TEXT NOT NULL,
                mime_type TEXT,
                size_bytes INTEGER NOT NULL,
                sha256 TEXT NOT NULL,
                content BLOB NOT NULL,
                source TEXT NOT NULL DEFAULT 'upload'
            );
            CREATE TABLE IF NOT EXISTS vendor_master (
                record_id TEXT PRIMARY KEY,
                legal_name TEXT NOT NULL,
                pan TEXT NOT NULL,
                gstin TEXT NOT NULL DEFAULT '',
                status TEXT NOT NULL DEFAULT 'active',
                source TEXT NOT NULL,
                created_at TEXT NOT NULL
            );
            CREATE INDEX IF NOT EXISTS idx_runs_submitted_at ON runs(submitted_at DESC);
            CREATE INDEX IF NOT EXISTS idx_documents_run_id ON documents(run_id);
        """)
        count = conn.execute("SELECT COUNT(*) FROM vendor_master").fetchone()[0]
        if count == 0:
            seed_vendor_master(conn)


def seed_vendor_master(conn: sqlite3.Connection) -> None:
    now = datetime.now(timezone.utc).isoformat(timespec="seconds")
    for vendor in SEEDED_VENDORS:
        conn.execute("""INSERT OR IGNORE INTO vendor_master
            (record_id, legal_name, pan, gstin, status, source, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (vendor["record_id"], vendor["legal_name"], vendor["pan"], vendor["gstin"],
             vendor["status"], vendor["source"], now))


def vendor_master(db_path: str | Path | None = None) -> list[dict[str, Any]]:
    initialize(db_path)
    with connect(db_path) as conn:
        return [dict(row) for row in conn.execute("SELECT * FROM vendor_master WHERE status='active' ORDER BY record_id")]


def save_run(vendor: dict[str, Any], result: dict[str, Any], documents: list[dict[str, Any]],
             source: str = "manual", db_path: str | Path | None = None) -> str:
    run_id = "VF-" + uuid.uuid4().hex[:10].upper()
    submitted_at = datetime.now(timezone.utc).isoformat(timespec="seconds")
    stored_result = dict(result)
    stored_result["run_id"] = run_id
    stored_result["submitted_at"] = submitted_at
    clean_vendor = dict(result.get("vendor", vendor))
    with connect(db_path) as conn:
        conn.execute("""INSERT INTO runs
            (run_id, submitted_at, decision, legal_name, contact_email, source, vendor_json, result_json)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (run_id, submitted_at, result["decision"], clean_vendor.get("legal_name", "(missing)"),
             clean_vendor.get("contact_email", ""), source, json.dumps(clean_vendor), json.dumps(stored_result)))
        for doc in documents:
            conn.execute("""INSERT INTO documents
                (run_id, doc_type, filename, mime_type, size_bytes, sha256, content, source)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                (run_id, doc["doc_type"], doc["filename"], doc.get("mime_type", "application/octet-stream"),
                 len(doc.get("content", b"")), doc["sha256"], sqlite3.Binary(doc.get("content", b"")), doc.get("source", "upload")))
        if result["decision"] == "APPROVED":
            conn.execute("""INSERT OR IGNORE INTO vendor_master
                (record_id, legal_name, pan, gstin, status, source, created_at)
                VALUES (?, ?, ?, ?, 'active', ?, ?)""",
                (run_id, clean_vendor.get("legal_name", ""), clean_vendor.get("pan", ""), clean_vendor.get("gstin", ""),
                 "approved submission", submitted_at))
    return run_id


def list_runs(db_path: str | Path | None = None, limit: int = 200) -> list[dict[str, Any]]:
    initialize(db_path)
    with connect(db_path) as conn:
        rows = conn.execute("SELECT run_id, submitted_at, decision, legal_name, contact_email, source FROM runs ORDER BY submitted_at DESC LIMIT ?", (limit,))
        return [dict(row) for row in rows]


def get_run(run_id: str, db_path: str | Path | None = None) -> dict[str, Any] | None:
    initialize(db_path)
    with connect(db_path) as conn:
        row = conn.execute("SELECT * FROM runs WHERE run_id=?", (run_id,)).fetchone()
        if not row:
            return None
        result = json.loads(row["result_json"])
        result["run_id"] = row["run_id"]
        result["submitted_at"] = row["submitted_at"]
        result["source"] = row["source"]
        result["documents"] = [dict(d) for d in conn.execute(
            "SELECT document_id, doc_type, filename, mime_type, size_bytes, sha256, source FROM documents WHERE run_id=? ORDER BY document_id",
            (run_id,))]
        return result


def get_document(document_id: int, db_path: str | Path | None = None) -> dict[str, Any] | None:
    initialize(db_path)
    with connect(db_path) as conn:
        row = conn.execute("SELECT filename, mime_type, content FROM documents WHERE document_id=?", (document_id,)).fetchone()
        return dict(row) if row else None


def metrics(db_path: str | Path | None = None) -> dict[str, int]:
    initialize(db_path)
    with connect(db_path) as conn:
        return {"total": conn.execute("SELECT COUNT(*) FROM runs").fetchone()[0],
                "approved": conn.execute("SELECT COUNT(*) FROM runs WHERE decision='APPROVED'").fetchone()[0],
                "pending": conn.execute("SELECT COUNT(*) FROM runs WHERE decision='PENDING'").fetchone()[0],
                "rejected": conn.execute("SELECT COUNT(*) FROM runs WHERE decision='REJECTED'").fetchone()[0]}


def reset_demo(db_path: str | Path | None = None) -> None:
    """Clear demo run history and restore the small seeded active-vendor master."""
    initialize(db_path)
    with connect(db_path) as conn:
        conn.execute("DELETE FROM documents")
        conn.execute("DELETE FROM runs")
        conn.execute("DELETE FROM vendor_master")
        seed_vendor_master(conn)

