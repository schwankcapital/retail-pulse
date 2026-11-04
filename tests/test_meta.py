from dataclasses import replace
import json

import httpx
import pytest

from retail_pulse.config import Settings
from retail_pulse.db import Database
from retail_pulse.meta_client import MetaClient, MetaError, BudgetExceeded, output_text, usage_summary
from retail_pulse.sam import parse_sam_output
from retail_pulse.perception import validate_extraction
from retail_pulse.schemas import Evidence, VisualBatch


def response(text="READY",**kw):
    return dict(id="resp_1",status="completed",output=[{"type":"message","role":"assistant","content":[{"type":"output_text","text":text}]}],
                usage={"input_tokens":100,"output_tokens":50},**kw)


def live(settings,**kw):
    return replace(settings,mode="meta",api_key="unit-test-not-a-real-key",**kw)


def test_no_paid_call_in_demo(settings):
    with pytest.raises(MetaError):
        MetaClient(settings)


def test_key_missing(settings):
    with pytest.raises(MetaError):
        MetaClient(replace(settings,mode="meta"))


def test_native_meta_request(settings):
    def handler(request):
        assert str(request.url)=="https://api.meta.ai/v1/responses"
        body=json.loads(request.content)
        assert body["store"] is False
        assert request.headers["authorization"]=="Bearer unit-test-not-a-real-key"
        return httpx.Response(200,json=response())
    with MetaClient(live(settings),transport=httpx.MockTransport(handler)) as c:
        r=c.create_response({"model":settings.muse_model,"input":"test"},"unit")
    assert output_text(r)=="READY"
    assert usage_summary(Database(settings))["estimated_spend_or_reserve"]>0


def test_response_cache_no_second_charge(settings):
    calls=[]
    def handler(request):
        calls.append(request)
        return httpx.Response(200,json=response())
    with MetaClient(live(settings),transport=httpx.MockTransport(handler)) as c:
        payload={"model":settings.muse_model,"input":"cache test"}
        c.create_response(payload,"cache")
        r=c.create_response(payload,"cache")
    assert len(calls)==1 and r["_retail_pulse_cache_hit"]


def test_budget_guard_no_request(settings):
    def forbidden(request):
        raise AssertionError("Request must not be made")
    with MetaClient(live(settings,budget=.1),transport=httpx.MockTransport(forbidden)) as c:
        with pytest.raises(BudgetExceeded):
            c.create_response({"model":settings.muse_model,"input":"test"},"unit")


def test_401_not_retried(settings):
    calls=[]
    def handler(request):
        calls.append(request)
        return httpx.Response(401,json={"error":"unauthorized"})
    with MetaClient(live(settings),transport=httpx.MockTransport(handler)) as c:
        with pytest.raises(MetaError):
            c.create_response({"model":settings.muse_model,"input":"401"},"unit")
    assert len(calls)==1
    assert usage_summary(Database(settings))["estimated_spend_or_reserve"]==0


def test_429_bounded_retry(settings,monkeypatch):
    calls=[]
    monkeypatch.setattr("retail_pulse.meta_client.time.sleep",lambda _:None)
    def handler(request):
        calls.append(request)
        return httpx.Response(429,json={"error":"limited"}) if len(calls)<3 else httpx.Response(200,json=response())
    with MetaClient(live(settings),transport=httpx.MockTransport(handler)) as c:
        c.create_response({"model":settings.muse_model,"input":"429"},"unit")
    assert len(calls)==3


def test_timeout_reserves_budget(settings):
    def handler(request):
        raise httpx.ReadTimeout("timeout",request=request)
    with MetaClient(live(settings),transport=httpx.MockTransport(handler)) as c:
        with pytest.raises(MetaError):
            c.create_response({"model":settings.muse_model,"input":"timeout"},"unit")
    summary=usage_summary(Database(settings))
    assert summary["estimated_spend_or_reserve"]==max(settings.reservation,(1_048_576*settings.input_price+settings.max_tokens*settings.output_price)/1e6)
    assert summary["requests"]==1


def test_upload_consent(settings,tmp_path):
    p=tmp_path/"clip.mp4"; p.write_bytes(b"fake")
    with MetaClient(live(settings)) as c:
        with pytest.raises(MetaError):
            c.upload(p)


def test_sam_empty():
    assert parse_sam_output("")==[]


def test_sam_sparse_tracking():
    text="<4f>7<|box;x1=1;y1=2;x2=6;y2=7;w=10;h=10;c=0.95|><|mask;x=0;y=0;c=0.95;data=6,6,!abc|>\n<9f>7<|box;x1=2;y1=2;x2=7;y2=7;w=10;h=10|><|mask;x=0;y=0;data=6,6,!def|>"
    r=parse_sam_output(text)
    assert [x["frame_index"] for x in r]==[4,9]
    assert r[0]["object_id"]==r[1]["object_id"]==7
    assert r[0]["confidence"]==.95


def test_sam_malformed():
    with pytest.raises(ValueError):
        parse_sam_output("Not SAM output")


def test_sam_out_of_bounds():
    with pytest.raises(ValueError):
        parse_sam_output("<0f>1<|box;x1=1;y1=2;x2=20;y2=7;w=10;h=10|><|mask;x=0;y=0;data=6,6,!abc|>")


def test_visual_time_bounds(db):
    e=Evidence.model_validate(db.evidence("E1"))
    e.duration_seconds=10
    row=dict(sku="A",zone_id="Z1",start_seconds=0,end_seconds=20,kind="shelf_state",availability="available",
             count_min=1,count_max=1,confidence=.9,visibility=.9,note="test")
    with pytest.raises(ValueError):
        validate_extraction(VisualBatch(events=[row],limitations=[]),e,db.objects("products"),"test")


def test_visual_idempotent_ids(db):
    e=Evidence.model_validate(db.evidence("E1"))
    row=dict(sku="A",zone_id="Z1",start_seconds=0,end_seconds=1,kind="shelf_state",availability="available",
             count_min=1,count_max=1,confidence=.9,visibility=.9,note="test")
    batch=VisualBatch(events=[row],limitations=[])
    a=validate_extraction(batch,e,db.objects("products"),"test")
    b=validate_extraction(batch,e,db.objects("products"),"test")
    assert a[0]["observation_id"]==b[0]["observation_id"]


def test_visual_unknown_sku(db):
    e=Evidence.model_validate(db.evidence("E1"))
    row=dict(sku="NOT_IN_CATALOG",zone_id="Z1",start_seconds=0,end_seconds=1,kind="shelf_state",availability="unknown",
             count_min=None,count_max=None,confidence=.9,visibility=.9,note="test")
    with pytest.raises(ValueError):
        validate_extraction(VisualBatch(events=[row],limitations=[]),e,db.objects("products"),"test")


def test_contributor_requires_consent(settings):
    with pytest.raises(ValueError):
        replace(settings,muse_model="muse-spark-1.3-contributor")


def test_endpoint_allowlist(settings):
    with pytest.raises(ValueError):
        replace(settings,base_url="https://attacker.invalid/v1")
