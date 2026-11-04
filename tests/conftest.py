from datetime import datetime, timezone
from pathlib import Path

import pytest

from retail_pulse.config import Settings
from retail_pulse.db import Database
from retail_pulse.ingestion import insert_records


@pytest.fixture
def settings(tmp_path):
    return Settings(home=tmp_path/"runtime")


@pytest.fixture
def db(settings):
    db=Database(settings)
    p=dict(store_id="S1",sku="A",upc="000000000001",title="Test item",zone_id="Z1",camera_id="CAM1",
           shelf_capacity=20,case_pack=2,lead_days=1,roi=[0,0,1,1])
    insert_records(db,"products",[p],strict=True)
    e=dict(evidence_id="E1",path="",media_type="fixture",store_id="S1",camera_id="CAM1",
           start_at="2026-10-01T00:00:00Z",duration_seconds=86400,seconds_to_world=1,
           sha256="fixture",synthetic=True)
    insert_records(db,"evidence",[e],strict=True)
    return db


@pytest.fixture(scope="session")
def demo_settings(tmp_path_factory):
    from retail_pulse.demo import make_demo
    from retail_pulse.pipeline import run_pipeline
    from retail_pulse.evaluation import evaluate_synthetic
    s=Settings(home=tmp_path_factory.mktemp("demo"))
    make_demo(s)
    run_pipeline(s)
    evaluate_synthetic(Database(s))
    return s
