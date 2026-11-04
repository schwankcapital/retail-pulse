import numpy as np
import pandas as pd
import pytest

from retail_pulse.db import Database
from retail_pulse.demand import metrics, RateModel
from retail_pulse.health import psi
from retail_pulse.optimization import recommend


def test_zero_denominator():
    assert metrics([0,0],[1,2])["wape"] is None


def test_empty_metrics():
    assert metrics([],[])["rows"]==0


def test_no_small_sample_drift_claim():
    assert psi([1,2],[3,4]) is None


def test_identical_psi_zero():
    assert abs(psi(np.arange(50),np.arange(50)))<1e-9


def test_chronological_splits(demo_settings):
    m=Database(demo_settings).latest_report("model","DEMO_01")
    assert m["train_range"][1]<m["validation_range"][0]
    assert m["validation_range"][1]<m["test_range"][0]
    assert m["test_range"][1]<=m["trained_through"]


def test_holdout_metrics_real(demo_settings):
    r=Database(demo_settings).latest_report("benchmark","DEMO_01")
    assert r["test_rows"]>0
    for score in r["results"].values():
        assert score["mae"]>=0
    assert "NOT live Muse" in r["notice"]


def test_decisions_respect_packs_capacity(demo_settings):
    rows=Database(demo_settings).latest_report("decisions","DEMO_01")["items"]
    for r in rows:
        assert r["target_units"]<=r["shelf_capacity"]
        assert r["suggested_units_before_review"]%r["case_pack"]==0
        assert r["approval_required"]


def test_gated_inventory(demo_settings):
    rows=Database(demo_settings).latest_report("decisions","DEMO_01")["items"]
    c=next(r for r in rows if r["sku"]=="C")
    assert c["recommended_order_units"] is None


def test_unknown_period_not_lost(demo_settings):
    d=Database(demo_settings).latest_report("demand","DEMO_01")["items"]
    f=next(r for r in d if r["sku"]=="F")
    assert f["unknown_hours"]>0
    assert f["lost_demand_estimate"]==0


def test_inventory_variance_fixture(demo_settings):
    rows=Database(demo_settings).latest_report("inventory","DEMO_01")["items"]
    by={r["sku"]:r for r in rows}
    assert by["D"]["variance_units"]==-2
    assert by["E"]["variance_units"]==3
    assert by["C"]["variance_units"]==0


def test_training_rejects_zero_exposure():
    df=pd.DataFrame(dict(sku=["A"]*4,weekday=[0]*4,date=["2026-10-01"]*4,available_hours=[0]*4,
                         contradictory_sales=[0]*4,eligible_sales=[0]*4))
    with pytest.raises(ValueError):
        RateModel().fit(df)
