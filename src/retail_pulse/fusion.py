from __future__ import annotations

from collections import defaultdict
from datetime import datetime, time, timedelta, timezone
from zoneinfo import ZoneInfo

import numpy as np
import pandas as pd
from scipy.stats import binom

from .config import Settings
from .db import Database
from .schemas import Observation, RFIDRead, Transaction


def parse_time(value: str | datetime) -> datetime:
    result = datetime.fromisoformat(value.replace("Z", "+00:00")) if isinstance(value, str) else value
    if result.tzinfo is None:
        raise ValueError("Timezone-aware time required")
    return result.astimezone(timezone.utc)


def availability_segments(observations: list[Observation], begin: datetime, end: datetime,
                          settings: Settings) -> list[dict]:
    """Interval union; contradictions and low-visibility intervals remain unknown.

    No carrying a snapshot through a camera outage. An image certifies at most its
    explicit observation interval. Overlapping views never add duplicate exposure.
    """
    relevant = [o for o in observations if o.kind == "shelf_state" and o.end_at > begin and o.at < end]
    points = sorted({begin, end, *[max(begin,o.at) for o in relevant], *[min(end,o.end_at) for o in relevant]})
    segments = []
    for a,b in zip(points,points[1:]):
        active = [o for o in relevant if o.at < b and o.end_at > a]
        good = [o for o in active if o.confidence >= settings.min_confidence and o.visibility >= settings.min_visibility
                and o.availability != "unknown"]
        states = {o.availability for o in good}
        state = next(iter(states)) if len(states) == 1 else "unknown"
        segments.append({"start":a,"end":b,"state":state,"hours":(b-a).total_seconds()/3600,
                         "evidence_ids":sorted({o.evidence_id for o in good}),
                         "conflict":len(states)>1})
    return segments


def daily_exposure(db: Database, store_id: str, as_of: datetime) -> pd.DataFrame:
    settings = db.settings
    products = db.objects("products", store_id)
    tx = [Transaction.model_validate(t) for t in db.objects("transactions",store_id) if parse_time(t["at"]) < as_of]
    obs = [Observation.model_validate(o) for o in db.objects("observations",store_id) if parse_time(o["at"]) < as_of]
    if not products or not tx:
        return pd.DataFrame()
    tz = ZoneInfo(settings.timezone)
    first = min(t.at for t in tx).astimezone(tz).date()
    last = as_of.astimezone(tz).date()
    by_sku = defaultdict(list)
    by_sale = defaultdict(list)
    for o in obs:
        by_sku[o.sku].append(o)
    for t in tx:
        if t.kind == "sale":
            by_sale[t.sku].append(t)
    rows=[]
    for p in products:
        for day in pd.date_range(first,last,freq="D"):
            local = datetime.combine(day.date(),time(settings.open_hour),tz)
            close = datetime.combine(day.date(),time(0),tz)+timedelta(hours=settings.close_hour)
            begin, end = local.astimezone(timezone.utc), min(close.astimezone(timezone.utc),as_of)
            if end <= begin:
                continue
            segments = availability_segments(by_sku[p["sku"]],begin,end,settings)
            totals = {s:sum(x["hours"] for x in segments if x["state"]==s) for s in ("available","unavailable","unknown")}
            sales=[t for t in by_sale[p["sku"]] if begin<=t.at<end]
            eligible_sales=sum(t.quantity for t in sales if any(s["state"]=="available" and s["start"]<=t.at<s["end"] for s in segments))
            contradict=sum(t.quantity for t in sales if any(s["state"]=="unavailable" and s["start"]<=t.at<s["end"] for s in segments))
            rows.append(dict(store_id=store_id,sku=p["sku"],date=str(day.date()),weekday=day.dayofweek,
                             available_hours=totals["available"],unavailable_hours=totals["unavailable"],
                             unknown_hours=totals["unknown"],open_hours=(end-begin).total_seconds()/3600,
                             sales=sum(t.quantity for t in sales),eligible_sales=eligible_sales,
                             contradictory_sales=contradict,
                             conflict_hours=sum(s["hours"] for s in segments if s["conflict"])))
    return pd.DataFrame(rows)


class CountFilter:
    """Small discrete posterior over store-level on-hand units; model assumptions are explicit."""
    def __init__(self, ledger: int, upper: int = 500):
        self.support=np.arange(max(upper,max(ledger,0)+100)+1)
        sigma=max(2.0,np.sqrt(max(ledger,1)))
        self.p=np.exp(-.5*((self.support-max(ledger,0))/sigma)**2)
        self.p/=self.p.sum()
        self.conflicts=[]

    def update(self, likelihood: np.ndarray, reason: str):
        new=self.p*likelihood
        if new.sum() < 1e-200:
            self.conflicts.append(reason)
            return
        self.p=new/new.sum()

    def shift(self, delta: int):
        target=self.support+delta
        valid=(target>=0)&(target<len(self.p))
        new=np.zeros_like(self.p)
        np.add.at(new,target[valid],self.p[valid])
        if not new.sum():
            self.conflicts.append("Recorded movement incompatible with physical state support")
            return
        self.p=new/new.sum()

    def count(self, lo: int, hi: int, verified=False):
        if verified:
            # A certified count starts a new physical anchor even if prior ledger was wrong.
            self.p=((self.support>=lo)&(self.support<=hi)).astype(float)
            if not self.p.sum():
                raise ValueError("Verified count exceeds filter support")
            self.p/=self.p.sum()
        else:
            self.update((self.support>=lo).astype(float),"Visible lower bound conflicts with prior")

    def rfid(self, count: int, detection_probability: float | None):
        if detection_probability is None:
            self.update((self.support>=count).astype(float),"RFID lower bound conflicts with prior")
        else:
            self.update(binom.pmf(count,self.support,detection_probability),"RFID likelihood conflicts with prior")

    def result(self):
        c=np.cumsum(self.p)
        return {"mean":float(self.support@self.p),"lower":int(np.searchsorted(c,.025)),
                "upper":int(np.searchsorted(c,.975)),"conflicts":self.conflicts}


def reconcile_inventory(db: Database, store_id: str, as_of: datetime) -> list[dict]:
    products=db.objects("products",store_id)
    tx=[Transaction.model_validate(t) for t in db.objects("transactions",store_id) if parse_time(t["at"])<=as_of]
    obs=[Observation.model_validate(o) for o in db.objects("observations",store_id) if parse_time(o["at"])<=as_of]
    rfid=[RFIDRead.model_validate(r) for r in db.objects("rfid_reads",store_id) if parse_time(r["at"])<=as_of]
    result=[]
    for p in products:
        t=sorted([x for x in tx if x.sku==p["sku"]],key=lambda x:x.at)
        ledger=sum(x.delta for x in t)
        initial=t[0].delta if t and t[0].kind=="opening" else 0
        count_bounds=[o.count_max for o in obs if o.sku==p["sku"] and o.count_max is not None]
        support_max=max([500, max(ledger,0)+100, initial+100, *[n+100 for n in count_bounds]])
        filt=CountFilter(initial,support_max)
        updates=[]
        for x in t[1:] if t and t[0].kind=="opening" else t:
            updates.append((x.at,0,"delta",x.delta))
        last_verified=None
        for o in obs:
            if o.sku!=p["sku"] or o.count_min is None or o.confidence<db.settings.min_confidence:
                continue
            if o.count_scope=="whole_store_verified":
                updates.append((o.at,2,"verified",o))
            elif o.kind=="shelf_state" and o.visibility>=db.settings.min_visibility and o.count_min>0:
                updates.append((o.at,1,"visible_bound",o))
            # Visible counts constrain a lower bound; they are NEVER added/subtracted as transactions.
        scans=defaultdict(list)
        for r in rfid:
            if r.sku==p["sku"]:
                scans[r.scan_id].append(r)
        for records in scans.values():
            updates.append((max(r.at for r in records),1,"rfid",len({r.epc for r in records})))
        for at,_,kind,value in sorted(updates,key=lambda v:(v[0],v[1])):
            if kind=="delta":
                filt.shift(value)
            elif kind=="verified":
                filt.count(value.count_min,value.count_max,verified=True)
                last_verified=value
            elif kind=="visible_bound":
                filt.count(value.count_min,value.count_max,verified=False)
            else:
                filt.rfid(value,db.settings.rfid_detection_probability)
        estimate=filt.result()
        # Only a recent certified audit supports a confirmed count variance in this release.
        verified=bool(last_verified and (as_of-last_verified.at).total_seconds()<=86400)
        variance=estimate["mean"]-ledger if verified else None
        status="unresolved"
        if verified:
            status="negative_variance" if estimate["upper"]<ledger else "positive_variance" if estimate["lower"]>ledger else "aligned"
        recent_events=[o for o in obs if o.sku==p["sku"] and o.kind!="shelf_state" and (as_of-o.at).days<7]
        result.append(dict(store_id=store_id,sku=p["sku"],title=p["title"],ledger_units=ledger,
                           estimated_units=round(estimate["mean"],2),lower_units=estimate["lower"],upper_units=estimate["upper"],
                           verified_recently=verified,variance_units=round(variance,2) if variance is not None else None,
                           status=status,notes=estimate["conflicts"],
                           recent_event_kinds=sorted({o.kind for o in recent_events}),
                           evidence_ids=sorted({o.evidence_id for o in recent_events}),
                           caveat="A negative variance is not evidence of theft; shelf quantity is not whole-store quantity."))
    return result
