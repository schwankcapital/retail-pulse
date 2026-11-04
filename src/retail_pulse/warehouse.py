"""Full-source local warehouse and bounded browser summaries."""
from pathlib import Path
import json
import duckdb
from .db import Database


def connect(settings,read_only=True):
    return duckdb.connect(str(settings.home/'warehouse.duckdb'),read_only=read_only)


def prepare_warehouse(settings,root,reuse=False):
    root=Path(root).resolve();db=Database(settings);con=connect(settings,False)
    con.execute("SET memory_limit='3GB'");con.execute('SET threads=4')
    con.execute('SET max_expression_depth=10000')
    existing={r[0] for r in con.execute('SHOW TABLES').fetchall()} if reuse else set()
    def path(source,name):return str(next((root/source/'raw').rglob(name))).replace('\\','/').replace("'","''")
    def table(name,query):
        if name in existing:return
        print('Loading',name,flush=True);con.execute(f'CREATE OR REPLACE TABLE {name} AS {query}')
    table('retail_sales',f"SELECT * FROM read_csv_auto('{path('retail_transactions_stocks','retail_sales_ml_apl.csv')}',sample_size=-1)")
    table('retail_stock',f"SELECT * FROM read_csv_auto('{path('retail_transactions_stocks','retail_inventory_ml_apl.csv')}',sample_size=-1)")
    table('fresh_train',f"SELECT * FROM read_parquet('{path('freshretailnet','train.parquet')}')")
    table('fresh_eval',f"SELECT * FROM read_parquet('{path('freshretailnet','eval.parquet')}')")
    table('m5',f"SELECT * FROM read_csv_auto('{path('walmart_m5','sales_train_evaluation.csv')}')")
    table('m5_calendar',f"SELECT * FROM read_csv_auto('{path('walmart_m5','calendar.csv')}')")
    table('m5_prices',f"SELECT * FROM read_csv_auto('{path('walmart_m5','sell_prices.csv')}')")
    fav=path('favorita','train.csv')
    table('favorita',f"SELECT date,store_nbr,item_nbr,unit_sales,onpromotion FROM read_csv_auto('{fav}',sample_size=100000)")
    for name in ['items','stores','transactions','oil','holidays_events']:
        table('favorita_'+name,f"SELECT * FROM read_csv_auto('{path('favorita',name+'.csv')}')")
    stats=[]
    configs=[('retail_sales','Retail sales','"Product No"','"Store"','"Transaction Date"','"Qty Sold"'),
             ('retail_stock','Retail stock intervals','"Product No"','"Store"','"Start Date"','"Qty on hand"'),
             ('fresh_train','FreshRetailNet training','product_id','store_id','dt','sale_amount'),
             ('fresh_eval','FreshRetailNet evaluation (held out)','product_id','store_id','dt','sale_amount'),
             ('favorita','Favorita item-store sales','item_nbr','store_nbr','date','unit_sales')]
    for name,title,sku,store,date,qty in configs:
        row=con.execute(f'SELECT count(*),count(DISTINCT {sku}),count(DISTINCT {store}),min({date})::VARCHAR,max({date})::VARCHAR,sum({qty}) FROM {name}').fetchone()
        stats.append(dict(dataset=name,title=title,rows=row[0],products=row[1],stores=row[2],start=row[3],end=row[4],quantity_total=row[5],
                          unit='normalized quantity' if name.startswith('fresh') else 'source units'))
        table(name+'_store_daily',f'SELECT {store}::VARCHAR store_id,{date}::VARCHAR date,sum({qty}) quantity,count(*) source_rows FROM {name} GROUP BY 1,2')
        table(name+'_products',f'SELECT {store}::VARCHAR store_id,{sku}::VARCHAR sku,sum({qty}) quantity,count(*) source_rows FROM {name} GROUP BY 1,2')
    days=[f'd_{n}' for n in range(1,1942)]
    day_sum='list_sum(['+','.join(days)+'])'
    total=con.execute('SELECT sum('+day_sum+') FROM m5').fetchone()[0]
    stats.append(dict(dataset='m5',title='Walmart M5 full sales history',rows=con.execute('SELECT count(*) FROM m5').fetchone()[0]*1941,
      products=con.execute('SELECT count(DISTINCT item_id) FROM m5').fetchone()[0],stores=10,start='2011-01-29',end='2016-05-22',quantity_total=total,unit='source units'))
    table('m5_products','SELECT store_id,item_id sku,dept_id,cat_id,'+day_sum+' quantity FROM m5')
    table('m5_store_daily',"SELECT store_id,c.date::VARCHAR date,sum(quantity) quantity,count(*) source_rows FROM (UNPIVOT m5 ON COLUMNS('^d_[0-9]+$') INTO NAME d VALUE quantity) t JOIN m5_calendar c USING(d) GROUP BY 1,2")
    # Stable bounded real series for tuning and video crosswalk, preserving all history.
    table('m5_model_series',"SELECT t.store_id||'/'||t.item_id sku,t.item_id,t.store_id,c.date::VARCHAR date,quantity sales FROM (UNPIVOT (SELECT * FROM m5 WHERE store_id='CA_1' AND cat_id='FOODS' ORDER BY item_id LIMIT 200) ON COLUMNS('^d_[0-9]+$') INTO NAME d VALUE quantity) t JOIN m5_calendar c USING(d)")
    summary=dict(sources=stats,source_root=str(root),note='Totals are per source, not merged business quantities. Fresh evaluation is never used for training. M5 overlapping validation is not concatenated. Stock interval rows are not repeated daily snapshots.')
    db.metadata('warehouse',summary);(settings.home/'reports/warehouse.json').write_text(json.dumps(summary,indent=2),encoding='utf-8')
    con.close();return summary


def browse(settings,dataset,store=None,query='',offset=0,limit=50,sku=None):
    allowed={'retail_sales','retail_stock','fresh_train','fresh_eval','favorita','m5'}
    if dataset not in allowed:raise ValueError('Unknown source')
    with connect(settings) as c:
        where='WHERE (? IS NULL OR store_id=?) AND sku ILIKE ?'
        params=[store,store,'%'+query+'%']
        total=c.execute(f'SELECT count(*) FROM {dataset}_products {where}',params).fetchone()[0]
        selection=f'SELECT * FROM {dataset}_products'
        if dataset=='favorita':selection='SELECT p.*,i.family title,i.perishable FROM favorita_products p LEFT JOIN favorita_items i ON p.sku=i.item_nbr::VARCHAR'
        frame=c.execute(f'{selection} {where} ORDER BY quantity DESC,store_id,sku LIMIT ? OFFSET ?',params+[limit,offset]).df()
        daily=c.execute(f'SELECT date,sum(quantity) quantity FROM {dataset}_store_daily WHERE (? IS NULL OR store_id=?) GROUP BY date ORDER BY date',[store,store]).df()
        if sku:
            if dataset=='m5':
                daily=c.execute("SELECT cal.date::VARCHAR date,sum(quantity) quantity FROM (UNPIVOT (SELECT * FROM m5 WHERE item_id=? AND (? IS NULL OR store_id=?)) ON COLUMNS('^d_[0-9]+$') INTO NAME d VALUE quantity) t JOIN m5_calendar cal USING(d) GROUP BY 1 ORDER BY 1",[sku,store,store]).df()
            else:
                fields={'retail_sales':('"Transaction Date"','"Qty Sold"','"Product No"','"Store"'),
                  'retail_stock':('"Start Date"','"Qty on hand"','"Product No"','"Store"'),
                  'fresh_train':('dt','sale_amount','product_id','store_id'),'fresh_eval':('dt','sale_amount','product_id','store_id'),
                  'favorita':('date','unit_sales','item_nbr','store_nbr')}
                date,qty,item,branch=fields[dataset]
                daily=c.execute(f'SELECT {date}::VARCHAR date,sum({qty}) quantity FROM {dataset} WHERE {item}::VARCHAR=? AND (? IS NULL OR {branch}::VARCHAR=?) GROUP BY 1 ORDER BY 1',[sku,store,store]).df()
        return dict(total=total,items=frame.to_dict('records'),daily=daily.to_dict('records'),stores=[r[0] for r in c.execute(f'SELECT DISTINCT store_id FROM {dataset}_products ORDER BY 1').fetchall()])
