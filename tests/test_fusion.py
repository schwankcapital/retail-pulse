from datetime import datetime, timedelta, timezone

import pytest

from retail_pulse.fusion import availability_segments, CountFilter, reconcile_inventory
from retail_pulse.ingestion import insert_records
from retail_pulse.schemas import Observation

BEGIN=datetime(2026,10,1,8,tzinfo=timezone.utc)


def obs(a=0,b=1,state="available",**kw):
    data=dict(observation_id="O1",store_id="S1",sku="A",zone_id="Z1",at=BEGIN+timedelta(hours=a),
              end_at=BEGIN+timedelta(hours=b),kind="shelf_state",availability=state,count_min=None,count_max=None,
              confidence=.95,visibility=.95,evidence_id="E1",origin="demo_replay")
    data.update(kw)
    return Observation(**data)


def test_missing_video_unknown(settings):
    rows=availability_segments([],BEGIN,BEGIN+timedelta(hours=2),settings)
    assert sum(r["hours"] for r in rows if r["state"]=="unknown")==2


def test_overlap_not_double_counted(settings):
    rows=availability_segments([obs(0,2),obs(1,3,observation_id="O2")],BEGIN,BEGIN+timedelta(hours=3),settings)
    assert sum(r["hours"] for r in rows)==3
    assert sum(r["hours"] for r in rows if r["state"]=="available")==3


def test_conflicting_views_unknown(settings):
    rows=availability_segments([obs(),obs(state="unavailable",observation_id="O2")],BEGIN,BEGIN+timedelta(hours=1),settings)
    assert rows[0]["state"]=="unknown" and rows[0]["conflict"]


def test_occlusion_not_zero(settings):
    rows=availability_segments([obs(state="unavailable",visibility=.1)],BEGIN,BEGIN+timedelta(hours=1),settings)
    assert rows[0]["state"]=="unknown"


def test_no_forward_fill(settings):
    rows=availability_segments([obs(0,1)],BEGIN,BEGIN+timedelta(hours=10),settings)
    assert sum(r["hours"] for r in rows if r["state"]=="unknown")==9


def test_verified_muse_count_forbidden():
    with pytest.raises(ValueError):
        obs(origin="muse",count_scope="whole_store_verified",count_min=4,count_max=4)


def test_reverse_interval_rejected():
    with pytest.raises(ValueError):
        obs(2,1)


def test_removal_does_not_create_availability():
    with pytest.raises(ValueError):
        obs(kind="removal")


def test_missing_tags_not_loss():
    filt=CountFilter(10)
    before=filt.result()["mean"]
    filt.rfid(7,None)
    assert filt.result()["mean"]>=before
    assert filt.result()["upper"]>=10


def test_certified_anchor():
    filt=CountFilter(100)
    filt.count(20,20,verified=True)
    assert filt.result()["lower"]==20==filt.result()["upper"]


def test_no_sale_video_double_count(db):
    insert_records(db,"transactions",[
        dict(event_id="OPEN",store_id="S1",sku="A",at=BEGIN.isoformat(),kind="opening",quantity=10),
        dict(event_id="SALE",store_id="S1",sku="A",at=(BEGIN+timedelta(hours=1)).isoformat(),kind="sale",quantity=2)])
    row=obs(1,1.01,kind="removal",state="unknown",count_min=2,count_max=2).model_dump(mode="json")
    insert_records(db,"observations",[row],strict=True)
    result=reconcile_inventory(db,"S1",BEGIN+timedelta(hours=2))
    assert result[0]["ledger_units"]==8
    assert result[0]["status"]=="unresolved"


def test_sales_never_negative_posterior():
    filt=CountFilter(2)
    filt.shift(-20)
    assert filt.result()["lower"]>=0


def test_recent_verified_variance(db):
    insert_records(db,"transactions",[dict(event_id="O",store_id="S1",sku="A",at=BEGIN.isoformat(),kind="opening",quantity=10)])
    row=obs(1,1.01,kind="count",state="unknown",count_min=8,count_max=8,count_scope="whole_store_verified",origin="manual")
    insert_records(db,"observations",[row.model_dump(mode="json")],strict=True)
    r=reconcile_inventory(db,"S1",BEGIN+timedelta(hours=2))[0]
    assert r["status"]=="negative_variance" and r["variance_units"]==-2
