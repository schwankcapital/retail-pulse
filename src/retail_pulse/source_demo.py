"""Bounded, deterministic source profiling; no real cross-dataset identity joins."""
from __future__ import annotations
import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd
from PIL import Image

from .demo import PRODUCTS

SOURCES = ('retailaction', 'merl_shopping', 'sku110k', 'cosmetics_retail',
           'agrishelf', 'freshretailnet', 'retail_transactions_stocks', 'walmart_m5', 'favorita')


def source_files(root: Path, name: str) -> list[Path]:
    return sorted(p for p in (root/name/'raw').rglob('*') if p.is_file()
                  and '__MACOSX' not in p.parts and not p.name.startswith('.')
                  and p.suffix.lower() not in {'.zip', '.7z', '.tar', '.gz'})


def build_profile(root: Path, home: Path) -> dict:
    """Training-only prefixes are convenience samples, not population estimates."""
    import pyarrow.parquet as pq
    root = root.resolve()
    dest = home/'source_samples'
    dest.mkdir(exist_ok=True)
    profiles = {}
    all_files = {n: source_files(root, n) for n in SOURCES}
    if any(not fs for fs in all_files.values()):
        raise ValueError('All nine extracted dataset folders must be present')

    def find(name, filename):
        return next(p for p in all_files[name] if p.name == filename)

    def checksum(path):
        with path.open("rb") as stream:
            return hashlib.file_digest(stream, "sha256").hexdigest()

    def record(name, paths, stats, role):
        profiles[name] = dict(origin='REAL_SOURCE', role=role, statistics=stats, samples=[
            dict(path=str(p.relative_to(root)), sha256=checksum(p))
            for p in paths], sample_policy='Deterministic bounded convenience sample; not representative')

    # No evaluation partitions or future competition test rows enter calibration.
    p = find('freshretailnet', 'train.parquet')
    f = next(pq.ParquetFile(p).iter_batches(batch_size=4096)).to_pandas()
    sales = np.maximum(f.sale_amount.to_numpy(dtype=float), 0)
    stockout = float(np.clip(f.stock_hour6_22_cnt.mean()/16, 0, 1))
    record('freshretailnet', [p], {'sample_rows':len(f), 'stockout_fraction':stockout,
           'mean_normalized_sales':float(sales.mean())}, 'Stockout pressure scales simulated fast-seller demand')

    p = find('walmart_m5', 'sales_train_evaluation.csv')
    m5 = pd.read_csv(p, nrows=64)
    # Early historical prefix only; no overlapping validation-file concatenation.
    hist = m5[[f'd_{i}' for i in range(1,57)]].sum().to_numpy(dtype=float)
    record('walmart_m5', [p], {'sample_series':64, 'days_used':56}, 'Relative daily demand shape')

    p = find('favorita', 'train.csv')
    fav = pd.read_csv(p, nrows=20000)
    units = np.maximum(fav.unit_sales.to_numpy(dtype=float), 0)
    variability = float(np.clip(units.std()/max(units.mean(), 1e-6), 0, 5))
    record('favorita', [p], {'sample_rows':len(fav), 'nonnegative_sales_cv':variability},
           'Scales daily demand variation; returns excluded from demand calibration')

    sales_path = find('retail_transactions_stocks', 'retail_sales_ml_apl.csv')
    inv_path = find('retail_transactions_stocks', 'retail_inventory_ml_apl.csv')
    tx = pd.read_csv(sales_path, nrows=4096)
    inv = pd.read_csv(inv_path, nrows=4096)
    median_stock = float(pd.to_numeric(inv['Qty on hand'], errors='coerce').clip(lower=0).median())
    median_sale = float(pd.to_numeric(tx['Qty Sold'], errors='coerce').clip(lower=0).median())
    record('retail_transactions_stocks', [sales_path,inv_path],
           {'sales_rows':len(tx), 'inventory_rows':len(inv), 'median_on_hand':median_stock,
            'median_sale_quantity':median_sale}, 'Bounded stock scale; no inferred source-store joins')

    # Representative visual samples are references, never operational observations.
    import cv2
    for name in SOURCES[:5]:
        fs = all_files[name]
        # Keep RetailAction held-out footage out of the source sample selection.
        if name == 'retailaction': fs = [p for p in fs if 'train' in p.parts]
        candidates = [p for p in fs if p.suffix.lower() in {'.jpg','.png','.mp4','.mov'}]
        p = candidates[0]
        if p.suffix.lower() in {'.mp4','.mov'}:
            cap = cv2.VideoCapture(str(p))
            try:
                ok, frame = cap.read()
                if not ok: raise ValueError(f'Cannot decode source sample: {p}')
                height,width = frame.shape[:2]
                preview = dest/f'{name}.jpg'
                if not cv2.imwrite(str(preview),frame): raise ValueError('Cannot save preview')
                duration = float(cap.get(cv2.CAP_PROP_FRAME_COUNT)/max(cap.get(cv2.CAP_PROP_FPS),1))
            finally: cap.release()
        else:
            preview = dest/f'{name}.jpg'
            with Image.open(p) as im:
                width,height=im.size
                im.convert('RGB').save(preview)
            duration = 0.0
        record(name, [p], {'width':width,'height':height,'duration_seconds':duration},
               'Decoded reference example for agent provenance; not evidence of synthetic store events')
        profiles[name]['preview'] = str(preview.relative_to(home))

    factors = np.clip(hist/max(hist.mean(),1e-6), .5, 1.8)
    factors = np.clip(1+(factors-1)*min(1.5, .5+variability/5), .5, 2)
    stock_scale = float(np.clip(median_stock/20, .8, 1.2))
    products=[]
    for sku,upc,title,capacity,rate,pack in PRODUCTS:
        products.append([sku,upc,title,max(6,round(capacity*stock_scale)),
                         rate*(1+stockout if sku=='A' else 1),pack])
    profile = dict(version=1,store_id='DEMO_01',origin='SYNTHETIC_ASSIGNMENT',sources=profiles,
                   products=products,daily_factors=factors.tolist(),
                   limitations=['All operational records, store/SKU mappings, RFID and audit counts are simulated.',
                     'Real media is reference material only; no real events or identities are joined across sources.',
                     'Sampled statistics shape a demonstration, not a fitted or validated retail population model.',
                     'Evaluation partitions were not used for calibration.'],
                   formula='M5 relative daily shape, Favorita variation, FreshRetailNet stockout pressure, bounded inventory scale')
    (home/'source_profile.json').write_text(json.dumps(profile,indent=2,allow_nan=False),encoding='utf-8')
    return profile
