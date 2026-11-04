"""Source-native reports: original measurements, no fabricated cross-source joins."""
from pathlib import Path
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
import json
import numpy as np
import pandas as pd
import pyarrow.parquet as pq

from .db import Database
from .ingestion import insert_records
from .demand import train_and_evaluate, demand_summary
from .health import assess_health


def blank_inventory(sku,title,units=None,**source):
    return dict(sku=sku,title=title,ledger_units=units,estimated_units=None,lower_units=None,
        upper_units=None,verified_recently=False,variance_units=None,status='unresolved',notes=[],
        recent_event_kinds=[],evidence_ids=[],caveat='Source on-hand records are not independent physical audits.',**source)


def catalog(db,store,inventory):
    rows=[dict(store_id=store,sku=r['sku'],upc='00000000',title=r['title'][:160],zone_id='UNMAPPED',
               camera_id='UNMAPPED',shelf_capacity=1,case_pack=1,lead_days=0,roi=[0,0,1,1]) for r in inventory]
    insert_records(db,'products',rows,'source_catalog',strict=True)


def prepare_real_data(settings,root):
    db=Database(settings)
    if db.objects('products'):raise ValueError('Real data preparation requires a new empty runtime')
    root=Path(root).resolve()
    # Six complete original series, preserving encoded IDs and normalized hourly quantities.
    f=next(pq.ParquetFile(root/'freshretailnet/raw/train.parquet').iter_batches(batch_size=8192)).to_pandas()
    counts=f.groupby(['store_id','product_id']).size()
    eligible=counts[counts==90].index
    f=f.set_index(['store_id','product_id']).loc[eligible].reset_index()
    source_store=int(f.store_id.iloc[0]);f=f[f.store_id==source_store]
    ids=f.groupby('product_id').stock_hour6_22_cnt.sum().sort_values(ascending=False).head(6).index
    f=f[f.product_id.isin(ids)].copy();store=f'FRESH_{source_store}'
    inventory=[blank_inventory(str(int(pid)),f'FreshRetailNet product {int(pid)}',source_product_id=int(pid)) for pid in sorted(ids)]
    catalog(db,store,inventory)
    daily=[]
    for r in f.itertuples():
        flags=np.asarray(r.hours_stock_status)[6:22];sales=np.asarray(r.hours_sale,dtype=float)[6:22]
        known=np.isin(flags,[0,1]);available=(flags==0);unavailable=(flags==1)
        daily.append(dict(store_id=store,sku=str(r.product_id),date=r.dt,weekday=pd.Timestamp(r.dt).weekday(),
          sales=float(sales.sum()),eligible_sales=float(sales[available].sum()),
          contradictory_sales=float(sales[unavailable].sum()),available_hours=int(available.sum()),
          unavailable_hours=int(unavailable.sum()),unknown_hours=int((~known).sum()),open_hours=16,
          source='FreshRetailNet train.parquet',source_product_id=r.product_id,source_store_id=r.store_id))
    f.to_parquet(settings.home/'raw/freshretailnet_selected.parquet',index=False)
    save_workspace(db,store,daily,inventory,dict(source='FreshRetailNet-50K',unit='normalized sales quantity',
        source_url='https://huggingface.co/datasets/Dingdong-Inc/FreshRetailNet-50K',
        availability_measured=True,inventory_measured=False,
        notice='Real FreshRetailNet sales and stock-status sequences, 06:00-22:00. Quantities are globally normalized, not original unit counts. Product IDs are publisher-encoded; no product names or on-hand counts are supplied. Video is a separate research source.'))
    # Original retailer product descriptions and stock interval records, no fictional inventory adjustments.
    raw=root/'retail_transactions_stocks/raw'
    sales=pd.read_csv(raw/'retail_sales_ml_apl.csv',dtype={'Product No':str,'Store':str})
    stock=pd.read_csv(raw/'retail_inventory_ml_apl.csv',dtype={'Product No':str,'Store':str})
    source_store=stock.groupby('Store')['Product No'].nunique().idxmax()
    inv=stock[stock.Store==source_store];tx=sales[sales.Store==source_store]
    ids=tx[tx['Product No'].isin(inv['Product No'])].groupby('Product No')['Qty Sold'].sum().nlargest(6).index
    inv=inv[inv['Product No'].isin(ids)];tx=tx[tx['Product No'].isin(ids)]
    store='STOCK_'+source_store.replace('-','_');inventory=[]
    for sku in sorted(ids):
        g=inv[inv['Product No']==sku];latest=g['End Date'].max();g=g[g['End Date']==latest]
        inventory.append(blank_inventory(sku,str(g.iloc[0]['Product Description']),float(g['Qty on hand'].sum()),
           source_start_date=str(g['Start Date'].min()),source_end_date=str(latest),source_store_id=source_store))
    catalog(db,store,inventory)
    tx.to_csv(settings.home/'raw/retail_sales_selected.csv',index=False);inv.to_csv(settings.home/'raw/retail_inventory_selected.csv',index=False)
    grouped=tx.groupby(['Product No','Transaction Date'])['Qty Sold'].sum()
    daily=[dict(store_id=store,sku=sku,date=date,weekday=pd.Timestamp(date).weekday(),sales=float(qty),
        eligible_sales=0.,contradictory_sales=0.,available_hours=0,unavailable_hours=0,unknown_hours=16,open_hours=16,
        source='Retail Transactions and Stocks',source_store_id=source_store) for (sku,date),qty in grouped.items()]
    save_workspace(db,store,daily,inventory,dict(source='Retail Transactions and Stocks',unit='recorded units',
        source_url='https://data.mendeley.com/datasets/27x8mjm8k4/1',availability_measured=False,inventory_measured=True,
        notice='Real source product IDs/descriptions, recorded sales and latest reported stock intervals. Stock dates vary by item. No physical audits, shelf availability, RFID or verified variances are supplied. Missing sales dates are not assumed zero. Video is a separate research source.'))
    db.metadata('default_store',store)
    return {'stores':[r['store_id'] for r in db.rows("SELECT DISTINCT store_id FROM products")],'default_store':store}


def save_workspace(db,store,daily,inventory,meta):
    frame=pd.DataFrame(daily).sort_values(['date','sku']);frame.to_csv(db.settings.home/'reports'/f'daily_exposure_{store}.csv',index=False)
    meta.update(store_id=store,inventory=inventory,as_of=(pd.Timestamp(frame.date.max())+pd.Timedelta(days=1)).tz_localize(db.settings.timezone).isoformat(),
      limitations=['No cross-source product/store identity joins.','UPC, shelf capacity and zone fields in the internal catalog are unmapped placeholders, not source facts.','Historical archive, not current live store data.'])
    db.metadata('source_workspace:'+store,meta)
    rebuild_real_report(db,store)


def rebuild_real_report(db,store):
    meta=db.metadata('source_workspace:'+store)
    daily=pd.read_csv(db.settings.home/'reports'/f'daily_exposure_{store}.csv',dtype={'sku':str})
    at=datetime.fromisoformat(meta['as_of']);model={'status':'INSUFFICIENT_DATA','training_days':0,'reason':'Source has no measured availability; exposure forecasting is withheld.'};demand=[]
    if meta['availability_measured']:
        fitted,model=train_and_evaluate(db,store,daily,at)
        model['assumptions'].append('Normalized non-integer quantities: quasi-Poisson rate approximation, not calibrated unit-count probabilities. Predictive count intervals are withheld.')
        db.save_report('model',store,at.isoformat(),model)
        demand=demand_summary(daily,fitted,at,db.settings)
        for row in demand:
            row.update(sales=float(daily[(daily.sku==row['sku']) & daily.date.isin(sorted(daily.date.unique())[-7:])].sales.sum()),
                       lost_demand_lower=None,lost_demand_upper=None,next_7d_lower=None,next_7d_upper=None,
                       interval_label='Count-based intervals withheld for normalized quantities',
                       caveat='Normalized source quantities; model estimate, not original units or measured lost sales.')
    health=source_health(db,store,daily,model,at)
    result=dict(store_id=store,as_of=at.isoformat(),synthetic=False,real_sources=True,source=meta['source'],unit=meta['unit'],
      inventory=meta['inventory'],demand=demand,health=health,decisions=[],model=model,notice=meta['notice'],
      measured_sales_total=float(daily.sales.sum()),source_url=meta['source_url'],availability_measured=meta['availability_measured'],
      inventory_measured=meta['inventory_measured'])
    for kind,data in [('health',health),('overview',result)]:db.save_report(kind,store,at.isoformat(),data)
    return result


def source_health(db,store,daily,model,at):
    health=assess_health(db,store,daily,model,at)
    for metric in health['metrics']:
        if metric['id'] in {'health.freshness_hours','health.low_quality_fraction'}:
            metric.update(value=None,status='NOT_EVALUATED',detail='Archival source records; camera quality/freshness is not established for these products.')
        if metric['id']=='health.sales_conflicts':
            recent=daily[daily.date.isin(sorted(daily.date.unique())[-7:])]
            metric.update(value=float(recent.contradictory_sales.sum()),label='Recorded quantity during publisher out-of-stock flags',detail='Source flag/sales inconsistency; not a measured camera/POS conflict.')
        if metric['id']=='health.coverage':metric.update(label='Publisher stock-status coverage',detail='Publisher flags, not inferred from unrelated camera footage.')
    health['status']='FAIL' if any(m['status']=='FAIL' for m in health['metrics']) else 'WARN'
    health['block_order_recommendations']=True
    health['recommended_review']=[m['detail'] for m in health['metrics'] if m['status']!='PASS']
    health['recommended_review'].append('Source inventory is not reconciled to the camera; no automated orders recommended.')
    return health
