from __future__ import annotations

import csv
import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pandas as pd

from .db import Database, dumps, utcnow
from .schemas import BarcodeScan, Evidence, Observation, Product, RFIDRead, Transaction

MODELS = {
    "products": Product, "transactions": Transaction, "observations": Observation,
    "rfid_reads": RFIDRead, "barcode_scans": BarcodeScan, "evidence": Evidence,
}


def normalize_time(value: str, source_timezone: str | None = None, clock_offset_seconds: float = 0) -> str:
    """Positive offset means source clock is fast, so subtract it. DST ambiguity is rejected."""
    timestamp = pd.Timestamp(value)
    if timestamp.tzinfo is None:
        if not source_timezone:
            raise ValueError("Naive timestamp: provide source_timezone")
        timestamp = timestamp.tz_localize(source_timezone, ambiguous="raise", nonexistent="raise")
    return (timestamp.tz_convert("UTC") - pd.Timedelta(seconds=clock_offset_seconds)).isoformat()


def insert_records(db: Database, table: str, records: list[dict], source="input", strict=False) -> dict:
    if table not in MODELS:
        raise ValueError("Unknown record type")
    good, bad = [], []
    opening_keys = {}
    for row in records:
        try:
            item = MODELS[table].model_validate(row)
            if table not in {"products", "evidence"}:
                exists = db.rows("SELECT data FROM products WHERE store_id=? AND sku=?", (item.store_id, item.sku))
                if not exists:
                    raise ValueError("Unknown store/SKU; ingest catalog first")
                prod = json.loads(exists[0]["data"])
                if table == "barcode_scans" and item.upc != prod["upc"]:
                    raise ValueError("Barcode SKU/UPC mismatch")
            if table == "transactions" and item.kind == "opening":
                key = (item.store_id,item.sku)
                prior = db.rows("SELECT event_id FROM transactions WHERE store_id=? AND sku=? AND kind='opening'", key)
                if (prior and prior[0]["event_id"]!=item.event_id) or (key in opening_keys and opening_keys[key]!=item.event_id):
                    raise ValueError("Only one opening balance per store/SKU; use an explicit adjustment instead")
                opening_keys[key] = item.event_id
            if table == "observations":
                evidence = db.evidence(item.evidence_id)
                if not evidence or evidence["store_id"] != item.store_id:
                    raise ValueError("Observation needs existing, same-store evidence")
            good.append(item)
        except (ValueError, TypeError) as exc:
            bad.append((row, str(exc)))
    if strict and bad:
        raise ValueError(f"Batch rejected: {len(bad)} invalid rows; first: {bad[0][1]}")
    inserted = 0
    conflicts = 0
    with db.connect(write=True) as c:
        for row, error in bad:
            c.execute("INSERT INTO quarantine(at,source,error,data) VALUES(?,?,?,?)",
                      (utcnow(), source, error[:4000], dumps(row)))
        for item in good:
            d = item.model_dump(mode="json")
            data = dumps(d)
            if table == "products":
                # Catalog changes must be explicit; identical re-ingestion is harmless.
                cols = (item.store_id, item.sku, data)
                sql = "INSERT OR IGNORE INTO products VALUES(?,?,?)"
                key_sql, key = "SELECT data FROM products WHERE store_id=? AND sku=?", cols[:2]
            elif table == "transactions":
                cols = (item.event_id, item.store_id, item.sku, item.at.isoformat(), item.kind, item.quantity, item.delta, data)
                sql = "INSERT OR IGNORE INTO transactions VALUES(?,?,?,?,?,?,?,?)"
                key_sql, key = "SELECT data FROM transactions WHERE event_id=?", (item.event_id,)
            elif table == "observations":
                cols = (item.observation_id, item.store_id, item.sku, item.at.isoformat(), item.end_at.isoformat(), item.kind, data)
                sql = "INSERT OR IGNORE INTO observations VALUES(?,?,?,?,?,?,?)"
                key_sql, key = "SELECT data FROM observations WHERE observation_id=?", (item.observation_id,)
            elif table == "rfid_reads":
                cols = (item.read_id, item.scan_id, item.epc, item.store_id, item.sku, item.at.isoformat(), data)
                sql = "INSERT OR IGNORE INTO rfid_reads VALUES(?,?,?,?,?,?,?)"
                # Multiple antennas reading the same EPC during one scan count once.
                key_sql, key = "SELECT data FROM rfid_reads WHERE read_id=?", (item.read_id,)
            elif table == "barcode_scans":
                cols = (item.scan_id, item.store_id, item.sku, item.at.isoformat(), data)
                sql = "INSERT OR IGNORE INTO barcode_scans VALUES(?,?,?,?,?)"
                key_sql, key = "SELECT data FROM barcode_scans WHERE scan_id=?", (item.scan_id,)
            else:
                cols = (item.evidence_id, data)
                sql = "INSERT OR IGNORE INTO evidence VALUES(?,?)"
                key_sql, key = "SELECT data FROM evidence WHERE evidence_id=?", (item.evidence_id,)
            prior = c.execute(key_sql, key).fetchone()
            if prior and prior["data"] != data:
                conflicts += 1
                c.execute("INSERT INTO quarantine(at,source,error,data) VALUES(?,?,?,?)",
                          (utcnow(), source, "Conflicting existing ID; original preserved", data))
                continue
            inserted += c.execute(sql, cols).rowcount
    return {"inserted": inserted, "duplicates": len(good) - inserted - conflicts,
            "rejected": len(bad) + conflicts, "source": source}


def import_file(db: Database, table: str, path: Path, source_timezone: str | None = None,
                clock_offset_seconds: float = 0) -> dict:
    if path.suffix.lower() == ".csv":
        with path.open(newline="", encoding="utf-8-sig") as f:
            rows = list(csv.DictReader(f))  # IDs and UPCs stay strings, including leading zeroes.
        for row in rows:
            if "roi" in row:
                row["roi"] = json.loads(row["roi"])
            for key in ("count_min", "count_max"):
                if key in row and row[key] == "":
                    row[key] = None
    elif path.suffix.lower() == ".jsonl":
        rows = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
    else:
        rows = json.loads(path.read_text(encoding="utf-8"))
    for row in rows:
        for field in ("at", "end_at", "start_at"):
            if field in row:
                row[field] = normalize_time(row[field], source_timezone, clock_offset_seconds)
    return insert_records(db, table, rows, source=str(path))
