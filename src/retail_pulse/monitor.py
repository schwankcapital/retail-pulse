from __future__ import annotations

import time
from datetime import datetime, timezone

from .agents import run_agent
from .config import Settings
from .db import Database
from .fusion import daily_exposure, parse_time
from .health import assess_health


def monitor_once(settings:Settings,store_id:str,agent:bool=False,as_of:str|None=None) -> dict:
    db=Database(settings)
    if db.metadata("source_workspace:"+store_id):
        import pandas as pd
        from .real_data import source_health
        meta=db.metadata("source_workspace:"+store_id)
        daily=pd.read_csv(settings.home/"reports"/f"daily_exposure_{store_id}.csv",dtype={"sku":str})
        overview=db.current_overview(store_id)
        health=source_health(db,store_id,daily,overview["model"],parse_time(meta["as_of"]))
        db.save_report("health",store_id,meta["as_of"],health)
        result={"health":health}
        if agent:
            result["agent"]=run_agent(db,store_id,"Review source data quality, forecast errors and limitations.","health",settings.mode)
        return result
    demo=db.metadata("demo")
    at=parse_time(as_of or (demo["as_of"] if demo else datetime.now(timezone.utc).isoformat()))
    overview=db.latest_report("overview",store_id)
    if not overview:
        raise ValueError("Run the pipeline once before starting health monitoring")
    daily=daily_exposure(db,store_id,at)
    if daily.empty:
        raise ValueError("No measured data available")
    health=assess_health(db,store_id,daily,overview["model"],at)
    model_age=(at-parse_time(overview["as_of"])).total_seconds()/3600
    health["metrics"].append({"id":"health.report_age_hours","label":"Inventory/demand report age in hours",
                              "value":round(model_age,2),"status":"FAIL" if model_age>48 else "WARN" if model_age>24 else "PASS",
                              "detail":"Monitoring does not retrain or regenerate operational reports. Run the pipeline when input data changes."})
    if model_age>48:
        health["status"]="FAIL"; health["block_order_recommendations"]=True
    elif model_age>24 and health["status"]=="PASS":
        health["status"]="WARN"
    db.save_report("health",store_id,at.isoformat(),health)
    result={"health":health}
    if agent:
        result["agent"]=run_agent(db,store_id,"Review ML health, data quality and safe next steps.","health",settings.mode)
    return result


def watch(settings:Settings,store_id:str,interval_seconds:int=300,agent:bool=False):
    """Explicit local foreground process. Ctrl+C stops it; the assistant schedules nothing."""
    if interval_seconds<30:
        raise ValueError("Monitoring interval must be at least 30 seconds")
    db=Database(settings)
    previous=None
    while True:
        report=monitor_once(settings,store_id,agent=False)
        h=report["health"]
        signature=(h["status"],tuple((m["id"],m["status"]) for m in h["metrics"]))
        # Paid interpretation only on changed health category, not on every unchanged poll.
        if agent and signature!=previous:
            report["agent"]=run_agent(db,store_id,"Review changed ML/data health and recommend checks.","health",settings.mode)
        print(f"{h['as_of']} health={h['status']} agent={'agent' in report}",flush=True)
        previous=signature
        time.sleep(interval_seconds)
