from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

from .db import Database
from .demand import metrics


def evaluate_synthetic(db:Database,store_id:str="DEMO_01") -> dict:
    """Evaluation-only access to withheld simulator demand; never supplied to inference/agents."""
    path=db.settings.home/"ground_truth.json"
    if not path.exists() or not db.metadata("demo"):
        raise ValueError("Synthetic ground truth unavailable; do not manufacture a real-world latent-demand score")
    truth=pd.DataFrame(json.loads(path.read_text(encoding="utf-8")))
    truth=truth[truth.store_id==store_id]
    # Dates in the simulator's original store timezone, preserved in ISO strings.
    truth["date"]=truth["at"].str[:10]
    grouped=truth.groupby(["sku","date"],as_index=False).agg(actual_demand=("demand","sum"),actual_lost=("lost","sum"))
    predictions=pd.read_csv(db.settings.home/"reports"/f"test_predictions_{store_id}.csv",dtype={"sku":str})
    joined=predictions.merge(grouped,on=["sku","date"],validate="one_to_one")
    scores={}
    for name in ["inventory_only","exposure_baseline","poisson_ml"]:
        estimated=joined[f"{name}_rate"]*joined.open_hours
        scores[name]=metrics(joined.actual_demand,estimated)
    report={"dataset":"Synthetic controlled retail simulation","store_id":store_id,"test_rows":len(joined),
            "results":scores,"notice":"Models fitted before test window. Perception uses replayed fixture labels, NOT live Muse or SAM.",
            "limits":["One seeded simulation; not proof of real-store generalization",
                      "Cannot estimate latent-demand error from ordinary real stockout records without ground truth",
                      "Run multiple seeds and held-out real/staged camera scenes before making performance claims"]}
    db.save_report("benchmark",store_id,db.metadata("demo")["as_of"],report)
    return report
