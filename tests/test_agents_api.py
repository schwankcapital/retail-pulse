from dataclasses import replace
import json

import httpx
import pytest
from fastapi.testclient import TestClient

from retail_pulse.agents import ReadOnlyTools, run_agent, validate_answer
from retail_pulse.api import create_app
from retail_pulse.db import Database
from retail_pulse.meta_client import MetaClient
from retail_pulse.schemas import AgentAnswer


def test_tools_reject_sql(demo_settings):
    tools=ReadOnlyTools(Database(demo_settings),"DEMO_01")
    with pytest.raises(ValueError):
        tools.call("execute_sql",{"sql":"DELETE FROM transactions"})


def test_tools_scope(demo_settings):
    tools=ReadOnlyTools(Database(demo_settings),"DEMO_01")
    with pytest.raises(ValueError):
        tools.call("get_summary",{"store_id":"OTHER"})


def test_tool_limit(demo_settings):
    tools=ReadOnlyTools(Database(demo_settings),"DEMO_01")
    with pytest.raises(ValueError):
        tools.call("get_events",{"sku":None,"limit":100000})


def test_bad_citations_rejected(demo_settings):
    tools=ReadOnlyTools(Database(demo_settings),"DEMO_01")
    tools.call("get_summary",{})
    a=AgentAnswer(answer="x",evidence_ids=["invented"],metric_ids=[],caveats=[],suggested_actions=[])
    with pytest.raises(ValueError):
        validate_answer(a,tools)


def test_demo_is_labeled(demo_settings):
    r=run_agent(Database(demo_settings),"DEMO_01","Which products have hidden demand?")
    assert r["mode"]=="demo" and r["model"].startswith("none")
    assert r["metric_values"]
    assert "not a Muse" in " ".join(r["caveats"])


def test_demo_health_agent(demo_settings):
    r=run_agent(Database(demo_settings),"DEMO_01","Can we trust the model?",role="health")
    assert "health.coverage" in r["metric_values"]


def test_live_function_loop_mock(demo_settings,monkeypatch):
    settings=replace(demo_settings,mode="meta",api_key="unit-test-key")
    seen=[]
    def handler(request):
        body=json.loads(request.content); seen.append(body)
        if len(seen)==1:
            return httpx.Response(200,json={"id":"r1","status":"completed","usage":{"input_tokens":100,"output_tokens":100},
                "output":[{"type":"function_call","name":"get_product","arguments":"{\"sku\":\"A\"}","call_id":"call_1"}]})
        assert any(x.get("type")=="function_call_output" and x["call_id"]=="call_1" for x in body["input"])
        answer=dict(answer="See observed unavailable time [demand.A.stockout_hours].",metric_ids=["demand.A.stockout_hours"],
                    evidence_ids=[],caveats=["Estimate limitations apply"],suggested_actions=["Review replenishment"])
        return httpx.Response(200,json={"id":"r2","status":"completed","usage":{"input_tokens":100,"output_tokens":100},
                "output":[{"type":"message","role":"assistant","content":[{"type":"output_text","text":json.dumps(answer)}]}]})
    monkeypatch.setattr("retail_pulse.agents.MetaClient",lambda s:MetaClient(s,transport=httpx.MockTransport(handler)))
    r=run_agent(Database(settings),"DEMO_01","Unit-test unique live function loop",mode="meta")
    assert len(seen)==2
    assert r["mode"]=="meta" and r["metric_values"]["demand.A.stockout_hours"]>0


def test_api_home(demo_settings):
    with TestClient(create_app(demo_settings)) as c:
        assert c.get("/").status_code==200
        assert c.get("/static/app.js").status_code==200
        assert c.get("/healthz").json()["status"]=="ok"


def test_api_overview(demo_settings):
    with TestClient(create_app(demo_settings)) as c:
        r=c.get("/api/overview")
        assert r.status_code==200 and r.json()["synthetic"]


def test_api_rejects_unknown_store(demo_settings):
    with TestClient(create_app(demo_settings)) as c:
        assert c.get("/api/overview",params={"store_id":"other"}).status_code==404
        assert c.get("/api/daily",params={"store_id":"../../.env"}).status_code==404


def test_api_key_gate(demo_settings):
    with TestClient(create_app(replace(demo_settings,api_token="local-test-token"))) as c:
        assert c.get("/api/config").status_code==401
        assert c.get("/api/config",headers={"Authorization":"Bearer local-test-token"}).status_code==200


def test_api_rejects_cross_origin(demo_settings):
    with TestClient(create_app(demo_settings)) as c:
        assert c.post("/api/run",headers={"Origin":"https://evil.invalid"}).status_code==403


def test_api_events_pagination(demo_settings):
    with TestClient(create_app(demo_settings)) as c:
        r=c.get("/api/events",params={"limit":3,"sku":"A"}).json()
        assert len(r["items"])==3 and r["total"]>3


def test_api_demo_insights(demo_settings):
    with TestClient(create_app(demo_settings)) as c:
        r=c.post("/api/ask",json={"question":"Explain shrink and swell","mode":"demo"})
        assert r.status_code==200 and "theft" in r.json()["answer"]


def test_api_live_requires_configuration(demo_settings):
    with TestClient(create_app(demo_settings)) as c:
        r=c.post("/api/ask",json={"question":"Explain stockouts","mode":"meta"})
        assert r.status_code==502


def test_api_config_no_secrets(demo_settings):
    with TestClient(create_app(replace(demo_settings,api_key="never-expose-this-key"))) as c:
        assert "never-expose" not in c.get("/api/config").text


def test_pipeline_lease(db):
    with db.lease("test"):
        with pytest.raises(RuntimeError):
            with db.lease("test"):
                pass
    with db.lease("test"):
        pass
