import json
from pathlib import Path

import pytest

from retail_pulse.ingestion import insert_records, normalize_time, import_file
from retail_pulse.schemas import Observation, Product


def txn(**kw):
    return dict(event_id="T1",store_id="S1",sku="A",at="2026-10-01T10:00:00Z",kind="opening",quantity=10,**kw)


def test_utc_offset():
    assert normalize_time("2026-10-01T08:00:00-06:00").startswith("2026-10-01T14:00:00")


def test_naive_requires_timezone():
    with pytest.raises(ValueError):
        normalize_time("2026-10-01T08:00:00")


def test_dst_ambiguity_rejected():
    with pytest.raises(Exception):
        normalize_time("2026-11-01T01:30:00","America/Denver")


def test_clock_offset():
    assert normalize_time("2026-10-01T08:00:30Z",clock_offset_seconds=30).startswith("2026-10-01T08:00:00")


def test_idempotent(db):
    assert insert_records(db,"transactions",[txn()])["inserted"]==1
    assert insert_records(db,"transactions",[txn()])["duplicates"]==1
    assert len(db.objects("transactions"))==1


def test_conflicting_id_quarantined(db):
    insert_records(db,"transactions",[txn()])
    row=txn(); row["quantity"]=50
    assert insert_records(db,"transactions",[row])["rejected"]==1
    assert db.objects("transactions")[0]["quantity"]==10


def test_second_opening_rejected(db):
    insert_records(db,"transactions",[txn()])
    row=txn(); row["event_id"]="T2"
    assert insert_records(db,"transactions",[row])["rejected"]==1


def test_two_openings_in_batch(db):
    a=txn(); b=txn(); b["event_id"]="T2"
    result=insert_records(db,"transactions",[a,b])
    assert result["inserted"]==1 and result["rejected"]==1


def test_upc_preserved(db,tmp_path):
    path=tmp_path/"scans.csv"
    path.write_text('scan_id,store_id,sku,upc,zone_id,at\nB1,S1,A,000000000001,Z1,2026-10-01T10:00:00Z\n')
    assert import_file(db,"barcode_scans",path)["inserted"]==1
    assert db.objects("barcode_scans")[0]["upc"]=="000000000001"


def test_barcode_mismatch(db):
    row=dict(scan_id="B1",store_id="S1",sku="A",upc="111111111111",zone_id="Z1",at="2026-10-01T10:00:00Z")
    assert insert_records(db,"barcode_scans",[row])["rejected"]==1


def test_unknown_sku(db):
    row=txn(); row["sku"]="UNKNOWN"
    assert insert_records(db,"transactions",[row])["rejected"]==1


def test_strict_batch_atomic(db):
    good=txn(); bad=txn(); bad["event_id"]="T2"; bad["quantity"]=-1
    with pytest.raises(ValueError):
        insert_records(db,"transactions",[good,bad],strict=True)
    assert not db.objects("transactions")


def test_rfid_duplicates(db):
    a=dict(read_id="R1",scan_id="SCAN",epc="EPC1",store_id="S1",sku="A",at="2026-10-01T10:00:00Z")
    b=dict(a,read_id="R2")
    result=insert_records(db,"rfid_reads",[a,b])
    assert result["inserted"]==1


def test_table_allowlist(db):
    with pytest.raises(ValueError):
        db.objects("products; DROP TABLE products")


def test_path_scope(db):
    with pytest.raises(FileNotFoundError):
        db.safe_media_path("../../.env")


def test_store_path_characters_rejected():
    with pytest.raises(ValueError):
        Product(store_id="../secret",sku="A",upc="000000000001",title="A",zone_id="Z",camera_id="C",shelf_capacity=10,case_pack=1,lead_days=1,roi=[0,0,1,1])
