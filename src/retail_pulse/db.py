from __future__ import annotations

import json
import re
import uuid
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path

from .config import Settings

SCHEMA = """
CREATE TABLE IF NOT EXISTS products (
 store_id TEXT NOT NULL, sku TEXT NOT NULL, data TEXT NOT NULL,
 PRIMARY KEY (store_id,sku));
CREATE TABLE IF NOT EXISTS transactions (
 event_id TEXT PRIMARY KEY, store_id TEXT NOT NULL, sku TEXT NOT NULL,
 at TEXT NOT NULL, kind TEXT NOT NULL, quantity INTEGER NOT NULL, delta INTEGER NOT NULL, data TEXT NOT NULL,
 FOREIGN KEY(store_id,sku) REFERENCES products(store_id,sku));
CREATE INDEX IF NOT EXISTS txn_lookup ON transactions(store_id,sku,at);
CREATE TABLE IF NOT EXISTS observations (
 observation_id TEXT PRIMARY KEY, store_id TEXT NOT NULL, sku TEXT NOT NULL,
 at TEXT NOT NULL, end_at TEXT NOT NULL, kind TEXT NOT NULL, data TEXT NOT NULL,
 FOREIGN KEY(store_id,sku) REFERENCES products(store_id,sku));
CREATE INDEX IF NOT EXISTS obs_lookup ON observations(store_id,sku,at);
CREATE TABLE IF NOT EXISTS rfid_reads (
 read_id TEXT PRIMARY KEY, scan_id TEXT NOT NULL, epc TEXT NOT NULL,
 store_id TEXT NOT NULL, sku TEXT NOT NULL, at TEXT NOT NULL, data TEXT NOT NULL,
 UNIQUE(scan_id,epc), FOREIGN KEY(store_id,sku) REFERENCES products(store_id,sku));
CREATE TABLE IF NOT EXISTS barcode_scans (
 scan_id TEXT PRIMARY KEY, store_id TEXT NOT NULL, sku TEXT NOT NULL, at TEXT NOT NULL, data TEXT NOT NULL,
 FOREIGN KEY(store_id,sku) REFERENCES products(store_id,sku));
CREATE TABLE IF NOT EXISTS evidence (evidence_id TEXT PRIMARY KEY, data TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS reports (
 report_id TEXT PRIMARY KEY, kind TEXT NOT NULL, store_id TEXT NOT NULL, at TEXT NOT NULL, data TEXT NOT NULL);
CREATE INDEX IF NOT EXISTS report_lookup ON reports(kind,store_id,at);
CREATE TABLE IF NOT EXISTS quarantine (id INTEGER PRIMARY KEY, at TEXT NOT NULL, source TEXT, error TEXT, data TEXT);
CREATE TABLE IF NOT EXISTS usage (
 id TEXT PRIMARY KEY, at TEXT NOT NULL, purpose TEXT NOT NULL, model TEXT NOT NULL,
 reserved REAL NOT NULL, actual REAL, status TEXT NOT NULL, data TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS agent_runs (
 run_id TEXT PRIMARY KEY, at TEXT NOT NULL, role TEXT NOT NULL, store_id TEXT NOT NULL, data TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS metadata (key TEXT PRIMARY KEY,value TEXT NOT NULL);
"""


def utcnow() -> str:
    return datetime.now(timezone.utc).isoformat()


def dumps(value) -> str:
    return json.dumps(value, ensure_ascii=True, allow_nan=False, default=str)


class Database:
    def __init__(self, settings: Settings):
        self.settings = settings
        self.path = settings.db_path
        with self.connect() as conn:
            conn.executescript(SCHEMA)

    @contextmanager
    def connect(self, write: bool = False):
        conn = sqlite3.connect(self.path, timeout=30)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys=ON")
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA busy_timeout=30000")
        try:
            if write:
                conn.execute("BEGIN IMMEDIATE")
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    def rows(self, sql: str, params=()) -> list[dict]:
        """Internal parameterized queries only. Never exposed as an agent tool."""
        with self.connect() as conn:
            return [dict(r) for r in conn.execute(sql, params).fetchall()]

    def objects(self, table: str, store_id: str | None = None) -> list[dict]:
        allowed = {"products", "transactions", "observations", "rfid_reads", "barcode_scans", "evidence"}
        if table not in allowed:
            raise ValueError("Table not allowed")
        sql = f"SELECT data FROM {table}"
        params = ()
        if store_id and table != "evidence":
            sql += " WHERE store_id=?"
            params = (store_id,)
        values = [json.loads(row["data"]) for row in self.rows(sql, params)]
        return [v for v in values if store_id is None or v.get("store_id") == store_id]

    def metadata(self, key: str, value=None):
        if value is not None:
            with self.connect(write=True) as c:
                c.execute("INSERT OR REPLACE INTO metadata VALUES (?,?)", (key, dumps(value)))
            return value
        rows = self.rows("SELECT value FROM metadata WHERE key=?", (key,))
        return json.loads(rows[0]["value"]) if rows else None

    def save_report(self, kind: str, store_id: str, at: str, data: dict) -> str:
        import hashlib
        if not re.fullmatch(r"[A-Za-z0-9_-]{1,64}", store_id) or not re.fullmatch(r"[A-Za-z0-9_-]{1,64}", kind):
            raise ValueError("Report store/kind identifiers must be safe filenames")
        rid = hashlib.sha256(f"{kind}:{store_id}:{at}".encode()).hexdigest()[:20]
        data = dict(data, report_id=rid)
        with self.connect(write=True) as c:
            c.execute("INSERT OR REPLACE INTO reports VALUES (?,?,?,?,?)", (rid, kind, store_id, at, dumps(data)))
        path = self.settings.home / "reports" / f"{kind}_{store_id}.json"
        # Unique temporary names allow concurrent health/report writers. API reads the DB copy.
        tmp = path.with_name(path.name + "." + uuid.uuid4().hex + ".tmp")
        try:
            tmp.write_text(json.dumps(data, indent=2, allow_nan=False, default=str), encoding="utf-8")
            tmp.replace(path)
        finally:
            tmp.unlink(missing_ok=True)
        return rid

    def latest_report(self, kind: str, store_id: str) -> dict:
        rows = self.rows("SELECT data FROM reports WHERE kind=? AND store_id=? ORDER BY at DESC LIMIT 1",
                         (kind, store_id))
        return json.loads(rows[0]["data"]) if rows else {}

    def evidence(self, evidence_id: str) -> dict | None:
        rows = self.rows("SELECT data FROM evidence WHERE evidence_id=?", (evidence_id,))
        return json.loads(rows[0]["data"]) if rows else None

    def safe_media_path(self, evidence_id: str) -> Path:
        evidence = self.evidence(evidence_id)
        if not evidence:
            raise FileNotFoundError("Unknown evidence")
        path = (self.settings.home / evidence["path"]).resolve()
        media_root = (self.settings.home / "media").resolve()
        if not path.is_relative_to(media_root) or path.suffix.lower() not in {".mp4", ".mov", ".png", ".jpg", ".jpeg"}:
            raise ValueError("Evidence path is outside the media allowlist")
        if not path.is_file():
            raise FileNotFoundError("Evidence file not present")
        return path

    @contextmanager
    def lease(self, name: str, ttl_seconds: int = 1800):
        """Cross-process single-writer lease for bounded local pipeline jobs."""
        import time
        import uuid
        owner=uuid.uuid4().hex
        key=f"lease:{name}"
        now=time.time()
        with self.connect(write=True) as c:
            row=c.execute("SELECT value FROM metadata WHERE key=?",(key,)).fetchone()
            if row and json.loads(row["value"])["expires"]>now:
                raise RuntimeError("A pipeline for this store is already running")
            c.execute("INSERT OR REPLACE INTO metadata VALUES(?,?)",(key,dumps({"owner":owner,"expires":now+ttl_seconds})))
        try:
            yield
        finally:
            with self.connect(write=True) as c:
                row=c.execute("SELECT value FROM metadata WHERE key=?",(key,)).fetchone()
                if row and json.loads(row["value"])["owner"]==owner:
                    c.execute("DELETE FROM metadata WHERE key=?",(key,))

    def current_overview(self, store_id: str) -> dict:
        result=self.latest_report("overview",store_id)
        if not result:
            return result
        health=self.latest_report("health",store_id)
        if health:
            result["health"]=health
            if health.get("block_order_recommendations"):
                for row in result.get("decisions",[]):
                    row["recommended_order_units"]=None
                    row["status"]="REVIEW_REQUIRED"
                    row["gates"]=list(dict.fromkeys(row["gates"]+["Latest monitoring health gate blocks this recommendation"]))
        return result
