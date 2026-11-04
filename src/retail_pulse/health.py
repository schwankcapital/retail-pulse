from __future__ import annotations

from datetime import datetime, timedelta

import numpy as np
import pandas as pd

from .db import Database
from .fusion import parse_time


def psi(reference, current) -> float | None:
    """Diagnostic, not a hypothesis test. Requires minimum 20 observations per window."""
    a=np.asarray(reference,dtype=float)
    b=np.asarray(current,dtype=float)
    a=a[np.isfinite(a)]; b=b[np.isfinite(b)]
    if len(a)<20 or len(b)<20:
        return None
    edges=np.unique(np.quantile(a,np.linspace(0,1,6)))
    if len(edges)<3:
        return 0.0 if np.allclose(np.mean(a),np.mean(b)) else None
    edges[0]=-np.inf; edges[-1]=np.inf
    pa=(np.histogram(a,edges)[0]+.5)/(len(a)+.5*(len(edges)-1))
    pb=(np.histogram(b,edges)[0]+.5)/(len(b)+.5*(len(edges)-1))
    return float(np.sum((pb-pa)*np.log(pb/pa)))


def assess_health(db: Database, store_id: str, daily: pd.DataFrame, model: dict, as_of: datetime) -> dict:
    observations=db.objects("observations",store_id)
    recent=[o for o in observations if as_of-timedelta(days=7)<=parse_time(o["at"])<=as_of]
    dates=sorted(daily.date.unique())
    r=daily[daily.date.isin(dates[-7:])]
    coverage=float((r.available_hours+r.unavailable_hours).sum()/r.open_hours.sum()) if r.open_hours.sum() else 0
    # Use visual shelf data, not a manual inventory count, to measure camera freshness.
    shelf=[o for o in observations if o["kind"]=="shelf_state" and parse_time(o["at"])<=as_of]
    freshness=(as_of-max(min(as_of,parse_time(o["end_at"])) for o in shelf)).total_seconds()/3600 if shelf else None
    usable=daily[(daily.available_hours>.1)&(daily.contradictory_sales==0)]
    reference=usable[usable.date.isin(dates[:-14])]
    current=usable[usable.date.isin(dates[-14:])]
    # Normalize by product baseline before pooling; avoids comparing entirely different SKU rates.
    rates=reference.groupby("sku").eligible_sales.sum()/reference.groupby("sku").available_hours.sum()
    def normalized(df):
        denom=df.sku.map(rates).clip(lower=.05)
        return (df.eligible_sales/df.available_hours)/denom
    drift=psi(normalized(reference),normalized(current))
    quarantined=db.rows("SELECT COUNT(*) AS n FROM quarantine")[0]["n"]
    metrics=[]
    def add(mid,label,value,status,detail):
        metrics.append(dict(id=mid,label=label,value=value,status=status,detail=detail))
    add("health.coverage","Known shelf availability coverage",round(coverage,4),
        "FAIL" if coverage<.4 else "WARN" if coverage<.8 else "PASS",
        "Unknown intervals are excluded from lost-demand estimates, not imputed as empty shelves.")
    add("health.freshness_hours","Latest camera-observation age in hours",round(freshness,2) if freshness is not None else None,
        "FAIL" if freshness is None or freshness>48 else "WARN" if freshness>24 else "PASS",
        "Measured against report as_of, not wall-clock time for synthetic replay.")
    low=sum(o["visibility"]<db.settings.min_visibility or o["confidence"]<db.settings.min_confidence for o in recent)
    fraction=low/len(recent) if recent else 1
    add("health.low_quality_fraction","Low-visibility / low-confidence observations",round(fraction,4),
        "WARN" if fraction>.15 else "PASS","Scores from Muse are uncalibrated; thresholds are engineering controls.")
    contradictions=int(r.contradictory_sales.sum())
    add("health.sales_conflicts","POS units during visually unavailable intervals",contradictions,
        "FAIL" if contradictions>20 else "WARN" if contradictions else "PASS",
        "May indicate clock drift, alternate displays, transaction delay or a perception error.")
    add("health.quarantined_rows","Rejected or conflicting ingestion rows",quarantined,
        "WARN" if quarantined else "PASS","All local sources; inspect quarantine before using new data.")
    add("health.drift_psi","Product-normalized demand-rate PSI",round(drift,4) if drift is not None else None,
        "NOT_EVALUATED" if drift is None else "WARN" if drift>.25 else "PASS",
        "Heuristic drift flag; does not prove model degradation. Seasonality may contribute.")
    chosen=model.get("model")
    score=model.get("test",{}).get(chosen,{})
    wape=score.get("wape")
    add("health.test_wape","Held-out observed-sales WAPE",round(wape,4) if wape is not None else None,
        "NOT_EVALUATED" if wape is None else "WARN" if wape>.6 else "PASS",
        f"Only fully available test days ({score.get('rows',0)} rows); does not validate latent demand.")
    add("health.training_days","Measured history in calendar days",model.get("training_days",0),
        "FAIL" if model.get("training_days",0)<28 else "PASS","Minimum history is a configurable policy in code, not a statistical guarantee.")
    status="FAIL" if any(m["status"]=="FAIL" for m in metrics) else "WARN" if any(m["status"] in {"WARN","NOT_EVALUATED"} for m in metrics) else "PASS"
    return dict(store_id=store_id,as_of=as_of.isoformat(),status=status,
                block_order_recommendations=status=="FAIL",metrics=metrics,
                policy="Deterministic gates. Muse may explain or recommend; it cannot change thresholds or promote models.",
                recommended_review=[m["detail"] for m in metrics if m["status"] not in {"PASS"}])
