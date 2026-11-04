"""Expand source-native workspaces without resetting API usage or original data."""
from retail_pulse.config import Settings
from retail_pulse.db import Database
from retail_pulse.warehouse import connect
from retail_pulse.real_data import blank_inventory,catalog,save_workspace
import numpy as np
import pandas as pd

s=Settings.from_env();db=Database(s)
with connect(s,False) as c:
    c.execute('CREATE OR REPLACE TABLE retail_stock_latest AS SELECT "Store" store_id,"Product No" sku,"Product Description" title,"Qty on hand" quantity,"Start Date"::VARCHAR source_start,"End Date"::VARCHAR source_end FROM retail_stock QUALIFY row_number() OVER(PARTITION BY "Store","Product No" ORDER BY "End Date" DESC,"Start Date" DESC)=1')
    c.execute('CREATE OR REPLACE TABLE retail_stock_products AS SELECT * FROM retail_stock_latest')
    c.execute('CREATE OR REPLACE TABLE retail_sales_products AS SELECT "Store" store_id,"Product No" sku,max("Product Description") title,sum("Qty Sold") quantity,count(*) source_rows FROM retail_sales GROUP BY 1,2')
    inv=c.execute("SELECT * FROM retail_stock_latest WHERE store_id='STR-1010' ORDER BY sku").df()
    tx=c.execute("SELECT \"Product No\" sku,\"Transaction Date\"::VARCHAR date,sum(\"Qty Sold\") sales FROM retail_sales WHERE \"Store\"='STR-1010' GROUP BY 1,2").df()
    fresh=c.execute('SELECT * FROM fresh_train WHERE store_id=0 ORDER BY product_id,dt').df()
stock_inventory=[blank_inventory(r.sku,r.title,float(r.quantity),source_start_date=r.source_start,source_end_date=r.source_end,source_store_id='STR-1010') for r in inv.itertuples()]
store='STOCK_STR_1010';catalog(db,store,stock_inventory)
daily=[dict(store_id=store,sku=r.sku,date=r.date,weekday=pd.Timestamp(r.date).weekday(),sales=float(r.sales),eligible_sales=0.,contradictory_sales=0.,available_hours=0,unavailable_hours=0,unknown_hours=16,open_hours=16,source='Retail Transactions and Stocks',source_store_id='STR-1010') for r in tx.itertuples()]
meta=db.metadata('source_workspace:'+store)
save_workspace(db,store,daily,stock_inventory,{k:meta[k] for k in ('source','unit','source_url','availability_measured','inventory_measured','notice')})
store='FRESH_0';ids=sorted(fresh.product_id.unique());inventory=[blank_inventory(str(int(pid)),f'FreshRetailNet product {int(pid)}',source_product_id=int(pid)) for pid in ids]
catalog(db,store,inventory);daily=[]
for r in fresh.itertuples():
    flags=np.asarray(r.hours_stock_status)[6:22];sales=np.asarray(r.hours_sale,dtype=float)[6:22]
    daily.append(dict(store_id=store,sku=str(r.product_id),date=r.dt,weekday=pd.Timestamp(r.dt).weekday(),sales=float(sales.sum()),eligible_sales=float(sales[flags==0].sum()),contradictory_sales=float(sales[flags==1].sum()),available_hours=int((flags==0).sum()),unavailable_hours=int((flags==1).sum()),unknown_hours=int((~np.isin(flags,[0,1])).sum()),open_hours=16,source='FreshRetailNet train.parquet',source_product_id=r.product_id,source_store_id=0))
meta=db.metadata('source_workspace:'+store)
save_workspace(db,store,daily,inventory,{k:meta[k] for k in ('source','unit','source_url','availability_measured','inventory_measured','notice')})
print('Expanded source workspaces:',len(stock_inventory),'retail products;',len(inventory),'FreshRetailNet series')
