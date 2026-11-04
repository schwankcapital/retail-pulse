from __future__ import annotations

import hashlib
import math
import uuid
from datetime import datetime, timedelta

import joblib
import numpy as np
import pandas as pd
from scipy.stats import poisson
from sklearn.compose import ColumnTransformer
from sklearn.linear_model import PoissonRegressor
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

from .db import Database


class RateModel:
    """Availability-exposure model. No imputed lost demand is ever used as a training label.

    Poisson regression on count/exposure with exposure weights has the same relevant
    coefficient objective as Poisson counts with a log(exposure) offset. Assumes
    approximately constant arrival intensity within a SKU/day, no substitution model.
    """
    def __init__(self, kind: str = "exposure_baseline"):
        self.kind = kind
        self.rates = {}
        self.weekday_rates = {}
        self.global_rate = 0.1
        self.pipeline = None
        self.exposure_hours = {}

    @staticmethod
    def features(df):
        out=df[["sku","weekday"]].copy()
        out["trend"]=(pd.to_datetime(df["date"])-pd.Timestamp("2020-01-01")).dt.days/365.25
        return out

    def fit(self, frame: pd.DataFrame):
        df=frame[(frame.available_hours>=.1)&(frame.contradictory_sales==0)].copy()
        if len(df)<3 or df.eligible_sales.sum()<=0:
            raise ValueError("Need at least 3 usable positive-exposure rows and positive recorded sales")
        self.global_rate=float(df.eligible_sales.sum()/df.available_hours.sum())
        self.exposure_hours={str(k):float(v) for k,v in df.groupby("sku").available_hours.sum().items()}
        for sku,g in df.groupby("sku"):
            self.rates[sku]=float((g.eligible_sales.sum()+self.global_rate*12)/(g.available_hours.sum()+12))
        for (sku,dow),g in df.groupby(["sku","weekday"]):
            self.weekday_rates[(sku,int(dow))]=float((g.eligible_sales.sum()+self.rates[sku]*12)/(g.available_hours.sum()+12))
        if self.kind=="poisson_ml":
            transforms=ColumnTransformer([
                ("categories",OneHotEncoder(handle_unknown="ignore",sparse_output=False),["sku","weekday"]),
                ("trend",StandardScaler(),["trend"]),
            ])
            self.pipeline=Pipeline([("features",transforms),("model",PoissonRegressor(alpha=.05,max_iter=2000))])
            self.pipeline.fit(self.features(df),df.eligible_sales/df.available_hours,
                              model__sample_weight=df.available_hours.to_numpy())
        return self

    def predict_rate(self, df):
        if self.pipeline is not None:
            out=self.pipeline.predict(self.features(df))
        else:
            out=np.array([self.weekday_rates.get((r.sku,int(r.weekday)),self.rates.get(r.sku,self.global_rate))
                          for r in df.itertuples()])
        if not np.isfinite(out).all():
            raise ValueError("Non-finite model output")
        return np.clip(out,0,10000)


def metrics(actual, predicted) -> dict:
    y=np.asarray(actual,dtype=float)
    p=np.asarray(predicted,dtype=float)
    if len(y)==0:
        return {"rows":0,"mae":None,"wape":None,"bias":None}
    denom=y.sum()
    return dict(rows=int(len(y)),mae=float(np.abs(p-y).mean()),
                wape=float(np.abs(p-y).sum()/denom) if denom else None,
                bias=float((p-y).sum()/denom) if denom else None)


def uncensored(df):
    return df[(df.available_hours>=.98*df.open_hours)&(df.unknown_hours<=.02*df.open_hours)&(df.contradictory_sales==0)]


def train_and_evaluate(db: Database, store_id: str, daily: pd.DataFrame, as_of: datetime) -> tuple[RateModel,dict]:
    dates=sorted(daily.date.unique())
    if len(dates)<28:
        raise ValueError("Need at least 28 calendar days for chronological train/validation/test")
    holdout=max(7,min(14,len(dates)//4))
    train_dates=dates[:-2*holdout]
    valid_dates=dates[-2*holdout:-holdout]
    test_dates=dates[-holdout:]
    train=daily[daily.date.isin(train_dates)]
    valid=uncensored(daily[daily.date.isin(valid_dates)])
    test=uncensored(daily[daily.date.isin(test_dates)])
    candidates={kind:RateModel(kind).fit(train) for kind in ("exposure_baseline","poisson_ml")}
    validation={kind:metrics(valid.sales,model.predict_rate(valid)*valid.open_hours)
                if len(valid) else metrics([],[]) for kind,model in candidates.items()}
    base_score=validation["exposure_baseline"]["wape"]
    ml_score=validation["poisson_ml"]["wape"]
    chosen="poisson_ml" if len(valid)>=10 and ml_score is not None and base_score is not None and ml_score<base_score*.98 else "exposure_baseline"
    trainvalid=daily[daily.date.isin(train_dates+valid_dates)]
    test_metrics={}
    test_predictions=daily[daily.date.isin(test_dates)].copy()
    for kind in candidates:
        candidate=RateModel(kind).fit(trainvalid)
        test_metrics[kind]=metrics(test.sales,candidate.predict_rate(test)*test.open_hours) if len(test) else metrics([],[])
        test_predictions[f"{kind}_rate"]=candidate.predict_rate(test_predictions)
    # Inventory-only reference sees recorded sales, NOT vision availability or hidden labels.
    naive=(trainvalid.groupby("sku").sales.sum()/trainvalid.groupby("sku").open_hours.sum()).to_dict()
    test_predictions["inventory_only_rate"]=test_predictions.sku.map(naive).fillna(0)
    prediction_path=db.settings.home/"reports"/f"test_predictions_{store_id}.csv"
    test_predictions.to_csv(prediction_path,index=False)
    # Freeze evaluation before refitting chosen architecture on all available measured history.
    deployed=RateModel(chosen).fit(daily)
    version=uuid.uuid4().hex[:12]
    model_dir=db.settings.home/"models"
    model_path=model_dir/f"{store_id}_{version}.joblib"
    joblib.dump(deployed,model_path)
    report=dict(version=version,model=chosen,store_id=store_id,as_of=as_of.isoformat(),
                trained_through=dates[-1],training_days=len(dates),train_range=[train_dates[0],train_dates[-1]],
                validation_range=[valid_dates[0],valid_dates[-1]],test_range=[test_dates[0],test_dates[-1]],
                validation=validation,test=test_metrics,
                evaluation_scope="Held-out fully available days only; no lost-demand pseudo-labels.",
                deployment_refit="Chosen architecture refitted through as_of AFTER holding out the test evaluation.",
                artifact=str(model_path.relative_to(db.settings.home)),
                sha256=hashlib.sha256(model_path.read_bytes()).hexdigest(),
                assumptions=["Demand intensity approximately constant within each product/day",
                             "Observed in-stock periods are representative conditional on product and weekday",
                             "No calibrated substitution, promotion or foot-traffic model",
                             "Conditional Poisson intervals omit parameter/model and perception uncertainty"])
    db.save_report("model",store_id,as_of.isoformat(),report)
    return deployed,report


def demand_summary(daily: pd.DataFrame, model: RateModel, as_of: datetime, settings) -> list[dict]:
    dates=sorted(daily.date.unique())[-7:]
    recent=daily[daily.date.isin(dates)].copy()
    recent["estimated_rate"]=model.predict_rate(recent)
    result=[]
    for sku,g in recent.groupby("sku"):
        lost=float((g.estimated_rate*g.unavailable_hours).sum())
        future=pd.DataFrame([dict(sku=sku,date=(as_of+timedelta(days=i)).date().isoformat(),
                                  weekday=(as_of+timedelta(days=i)).weekday()) for i in range(7)])
        future_rate=model.predict_rate(future)
        expected=float(future_rate.sum()*(settings.close_hour-settings.open_hour))
        upper=lambda mu:int(poisson.ppf(.95,mu)) if mu>0 else 0
        lower=lambda mu:int(poisson.ppf(.05,mu)) if mu>0 else 0
        result.append(dict(sku=sku,period="last_7_observed_days",sales=int(g.sales.sum()),
                           available_hours=round(float(g.available_hours.sum()),2),
                           stockout_hours=round(float(g.unavailable_hours.sum()),2),
                           unknown_hours=round(float(g.unknown_hours.sum()),2),
                           open_hours=float(g.open_hours.sum()),
                           coverage=round(float((g.available_hours+g.unavailable_hours).sum()/g.open_hours.sum()),4),
                           lost_demand_estimate=round(lost,2),lost_demand_lower=lower(lost),lost_demand_upper=upper(lost),
                           next_7d_demand=round(expected,2),next_7d_lower=lower(expected),next_7d_upper=upper(expected),
                           hourly_rate=round(float(future_rate.mean()),4),
                           history_exposure_hours=round(model.exposure_hours.get(sku,0),2),
                           interval_label="90% conditional Poisson predictive interval; NOT full uncertainty",
                           caveat="Estimated unfulfilled product demand, not confirmed lost sales; unknown camera periods excluded."))
    return result
