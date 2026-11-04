from __future__ import annotations

import math
from scipy.stats import poisson


def recommend(products: list[dict], demand: list[dict], inventory: list[dict], health: dict,
              open_hours: int, target_service: float=.95) -> list[dict]:
    """Enumerate feasible review intervals; not a multi-store routing or global cost optimizer."""
    ds={r["sku"]:r for r in demand}; inv={r["sku"]:r for r in inventory}
    rows=[]
    for p in products:
        d=ds[p["sku"]]; i=inv[p["sku"]]
        rate=d["hourly_rate"]*open_hours
        cap=p["shelf_capacity"]
        feasible=[v for v in [1,2,3,7] if poisson.ppf(target_service,rate*(v+p["lead_days"]))<=cap]
        interval=max(feasible) if feasible else 1
        protection_demand=rate*(interval+p["lead_days"])
        unconstrained=int(poisson.ppf(target_service,protection_demand)) if protection_demand else 0
        target=min(cap,unconstrained)
        known=i["verified_recently"]
        position=i["estimated_units"] if known else i["ledger_units"]
        need=max(0,target-position)
        requested=math.ceil(need/p["case_pack"])*p["case_pack"]
        room=max(0,cap-max(0,position))
        fits=math.floor(room/p["case_pack"])*p["case_pack"]
        proposed=max(0,min(requested,fits))
        reasons=[]
        if d.get("history_exposure_hours",0)<6:
            reasons.append("Insufficient measured in-stock exposure for this SKU")
        if d["coverage"]<.5:
            reasons.append("More than half of recent availability time is unknown")
        if health["block_order_recommendations"]:
            reasons.append("Model/data health gate failed; inspect diagnostics first")
        if not known:
            reasons.append("No recent verified whole-store count; check inventory position")
        if {"misplacement","damage"}&set(i["recent_event_kinds"]):
            reasons.append("Resolve misplaced or non-sellable units before ordering")
        actions=[]
        if "misplacement" in i["recent_event_kinds"]:
            actions.append("Inspect alternate locations and return sellable units to the assigned shelf")
        if "damage" in i["recent_event_kinds"]:
            actions.append("Verify damaged-unit disposition and update sellable inventory")
        if i["status"] in {"negative_variance","positive_variance"}:
            actions.append("Review receiving, sales, returns and count evidence; no attribution of intent")
        if not feasible:
            actions.append("Shelf capacity cannot support the service target even with daily review; test extra capacity or shorter lead time")
        if requested>proposed:
            actions.append("Case-pack rounding constrained by shelf capacity; partial service target may remain unmet")
        if interval<7:
            actions.append(f"Evaluate {interval}-day service instead of weekly service")
        priority=d["stockout_hours"]+abs(i["variance_units"] or 0)*3+(10 if reasons else 0)
        rows.append(dict(sku=p["sku"],title=p["title"],review_interval_days=interval,
                         lead_days=p["lead_days"],shelf_capacity=cap,case_pack=p["case_pack"],
                         target_units=target,unconstrained_target=unconstrained,
                         suggested_units_before_review=proposed,recommended_order_units=None if reasons else proposed,
                         status="REVIEW_REQUIRED" if reasons else "ADVISORY_READY",gates=reasons,
                         actions=actions,priority=round(priority,2),evidence_ids=i["evidence_ids"],
                         approval_required=True,
                         caveat="Advisory only. No ERP write, purchase order, visit reschedule, or inventory correction occurs."))
    return sorted(rows,key=lambda r:r["priority"],reverse=True)
