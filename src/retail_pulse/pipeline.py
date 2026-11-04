from __future__ import annotations

from datetime import datetime, timezone

from .config import Settings
from .db import Database
from .demand import demand_summary, train_and_evaluate
from .fusion import daily_exposure, parse_time, reconcile_inventory
from .health import assess_health
from .optimization import recommend


def _run_pipeline(settings: Settings, store_id: str="DEMO_01", as_of: str | None=None) -> dict:
    db=Database(settings)
    if db.metadata("source_workspace:"+store_id):
        from .real_data import rebuild_real_report
        return rebuild_real_report(db,store_id)
    demo=db.metadata("demo")
    at=parse_time(as_of or (demo["as_of"] if demo else datetime.now(timezone.utc).isoformat()))
    daily=daily_exposure(db,store_id,at)
    if daily.empty:
        raise ValueError("No inventory/catalog data. Run demo or ingest your sources first.")
    daily.to_csv(settings.home/"reports"/f"daily_exposure_{store_id}.csv",index=False)
    inventory=reconcile_inventory(db,store_id,at)
    try:
        model,model_report=train_and_evaluate(db,store_id,daily,at)
        demand=demand_summary(daily,model,at,settings)
        health=assess_health(db,store_id,daily,model_report,at)
        decisions=recommend(db.objects("products",store_id),demand,inventory,health,settings.close_hour-settings.open_hour)
    except ValueError as exc:
        # New installations have inventory intelligence before they have enough forecasting history.
        model_report={"status":"INSUFFICIENT_DATA","reason":str(exc),"training_days":len(daily.date.unique())}
        demand=[]
        health=assess_health(db,store_id,daily,model_report,at)
        health["status"]="FAIL"; health["block_order_recommendations"]=True
        health["recommended_review"].append(str(exc))
        decisions=[]
    for kind,data in [("inventory",{"items":inventory}),("demand",{"items":demand}),
                      ("health",health),("decisions",{"items":decisions})]:
        db.save_report(kind,store_id,at.isoformat(),dict(data,as_of=at.isoformat(),store_id=store_id))
    result=dict(store_id=store_id,as_of=at.isoformat(),synthetic=bool(demo),
                inventory=inventory,demand=demand,health=health,decisions=decisions,model=model_report,
                notice=("Dataset-informed synthetic demo. All operations and source mappings are simulated; reference footage is not event evidence." if db.metadata("source_profile") else "Synthetic observation replay; not a perception benchmark.") if demo else "Research prototype; verify operational actions.")
    db.save_report("overview",store_id,at.isoformat(),result)
    return result


def run_pipeline(settings: Settings, store_id: str="DEMO_01", as_of: str | None=None) -> dict:
    db=Database(settings)
    with db.lease(f"pipeline:{store_id}"):
        return _run_pipeline(settings,store_id,as_of)
