"""Retail operations shadow ledger: durable events, review gates and human actions.

Research replays never mutate publisher records or submit external orders.
"""
from __future__ import annotations
import hashlib,json,math,uuid
from datetime import datetime,timezone
from typing import Literal
from pydantic import BaseModel,ConfigDict,Field
from .db import Database,dumps,utcnow
from .meta_client import usage_summary

SCHEMA='''
CREATE TABLE IF NOT EXISTS operations_cases(case_id TEXT PRIMARY KEY,revision INTEGER NOT NULL,data TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS operations_actions(action_id TEXT PRIMARY KEY,case_id TEXT NOT NULL,at TEXT NOT NULL,payload_hash TEXT NOT NULL,data TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS operations_sales(event_id TEXT PRIMARY KEY,store_id TEXT NOT NULL,sku TEXT NOT NULL,received_at TEXT NOT NULL,origin TEXT NOT NULL,payload_hash TEXT NOT NULL,data TEXT NOT NULL);
'''

class Conflict(ValueError):pass

class CaseAction(BaseModel):
    model_config=ConfigDict(extra='forbid')
    action_id:str=Field(min_length=8,max_length=100)
    expected_revision:int=Field(ge=0)
    action:Literal['approve_count','reject','match_checkout','restock','verify_shelf','restart_demo']
    quantity:int|None=Field(None,ge=0,le=100)
    note:str=Field('',max_length=500)

class PosEvent(BaseModel):
    model_config=ConfigDict(extra='forbid')
    event_id:str=Field(min_length=8,max_length=100)
    store_id:str=Field(min_length=1,max_length=64)
    sku:str=Field(min_length=1,max_length=100)
    occurred_at:datetime
    kind:Literal['sale','return','receipt']
    quantity:float=Field(gt=0,le=10000,allow_inf_nan=False)

def initialize(db):
    with db.connect() as c:c.executescript(SCHEMA)
    flow=db.metadata('video_flow') or {};ground=(db.metadata('visual_grounding') or {}).get('clips',{})
    with db.connect(write=True) as c:
        for s in flow.get('scenarios',[]):
            eid=s['scenario_id'];events=s['clip']['transfers']
            exact=[e for e in events if e['action']=='take' and e['quantity_min'] is not None and e['quantity_min']==e['quantity_max'] and e['confidence']>=.75]
            candidate=sum(e['quantity_min'] for e in exact)
            if candidate<=0:continue
            initial=s['ledger']['initial_shelf'];backroom=max(3,s['planning']['target_shelf'])
            state=dict(case_id=eid,sku=s['sku'],description=exact[0]['product_description'],revision=0,
              review='pending',review_quantity=None,checkout_units=0,restocked_units=0,verified=False,
              initial_shelf=initial,initial_backroom=backroom,shelf=initial,in_hand=0,backroom=backroom,
              store_units=initial+backroom,candidate_quantity=candidate,target_shelf=s['planning']['target_shelf'],
              forecast_daily=s['forecast_daily'],forecast_7d=s['forecast_7d'],evidence_digest=s['clip']['sha256'],
              last_action_at=None,created_at=utcnow(),note='',mode='research_scenario')
            c.execute('INSERT OR IGNORE INTO operations_cases VALUES(?,?,?)',(eid,0,dumps(state)))

def current_cases(db):
    initialize(db);ground=(db.metadata('visual_grounding') or {}).get('clips',{})
    rows=[]
    for r in db.rows('SELECT data FROM operations_cases ORDER BY case_id'):
        s=json.loads(r['data']);g=ground.get(s['case_id'],{})
        s['challenge']=g.get('comparison');s['independent_review']=g.get('review')
        s['disputed']=bool((s['challenge'] or {}).get('requires_human_review'))
        s['refill_needed']=max(0,s['target_shelf']-s['shelf']) if s['review']=='approved' else max(0,s['target_shelf']-max(0,s['initial_shelf']-s['candidate_quantity']))
        s['refill_available']=min(s['refill_needed'],s['backroom'])
        s['supplier_shortfall']=max(0,s['refill_needed']-s['backroom'])
        s['status']='REVIEW_COUNT' if s['review']=='pending' else 'REJECTED' if s['review']=='rejected' else 'VERIFIED' if s['verified'] else 'VERIFY_REFILL' if s['restocked_units'] else 'REFILL_READY'
        rows.append(s)
    return rows

def act(db,case_id,request:CaseAction):
    initialize(db);payload=request.model_dump();digest=hashlib.sha256(dumps(payload).encode()).hexdigest()
    disputed=next((s['disputed'] for s in current_cases(db) if s['case_id']==case_id),False)
    with db.connect(write=True) as c:
        old=c.execute('SELECT case_id,payload_hash,data FROM operations_actions WHERE action_id=?',(request.action_id,)).fetchone()
        if old:
            if old['case_id']!=case_id or old['payload_hash']!=digest:raise Conflict('Action identifier already used for different content')
            return dict(json.loads(old['data'])['after'],duplicate=True)
        row=c.execute('SELECT * FROM operations_cases WHERE case_id=?',(case_id,)).fetchone()
        if not row:raise ValueError('Unknown operations case')
        if row['revision']!=request.expected_revision:raise Conflict('This case changed. Refresh it before applying the action.')
        s=json.loads(row['data']);before=dict(s);q=request.quantity;a=request.action
        if a=='restart_demo':
            s.update(review='pending',review_quantity=None,checkout_units=0,restocked_units=0,verified=False,
              shelf=s['initial_shelf'],in_hand=0,backroom=s['initial_backroom'],store_units=s['initial_shelf']+s['initial_backroom'])
        elif a=='reject':
            if s['review']!='pending':raise ValueError('Only an unreviewed proposal can be rejected')
            if len(request.note.strip())<3:raise ValueError('Record why the evidence is rejected')
            s['review']='rejected'
        elif a=='approve_count':
            if s['review']!='pending':raise ValueError('Count was already reviewed')
            if q is None or not 1<=q<=s['shelf']:raise ValueError('Reviewed count must fit the scenario opening shelf balance')
            if (disputed or q!=s['candidate_quantity']) and len(request.note.strip())<8:raise ValueError('A disputed or corrected count requires a human review note')
            s.update(review='approved',review_quantity=q,shelf=s['shelf']-q,in_hand=q)
        elif a=='match_checkout':
            if s['review']!='approved' or q is None or not 1<=q<=s['in_hand']:raise ValueError('Checkout must match reviewed items still in hand')
            s['in_hand']-=q;s['checkout_units']+=q;s['store_units']-=q
        elif a=='restock':
            if s['review']!='approved' or q is None or not 1<=q<=s['backroom']:raise ValueError('Restock requires a reviewed case and sufficient scenario backroom stock')
            if q>max(0,s['target_shelf']-s['shelf']):raise ValueError('Quantity exceeds the approved scenario shelf target')
            s['shelf']+=q;s['backroom']-=q;s['restocked_units']+=q;s['verified']=False
        elif a=='verify_shelf':
            if s['restocked_units']<=0:raise ValueError('Report the refill before verifying it')
            if q!=s['shelf']:raise ValueError('Count differs from the projected shelf balance; investigate instead of silently adjusting stock')
            if len(request.note.strip())<3:raise ValueError('Record the operator confirmation and its demo scope')
            s['verified']=True
        if min(s['shelf'],s['backroom'],s['in_hand'],s['store_units'])<0 or s['shelf']+s['backroom']+s['in_hand']!=s['store_units']:
            raise ValueError('Inventory conservation check failed')
        s.update(revision=s['revision']+1,last_action_at=utcnow(),note=request.note)
        record=dict(action=payload,before=before,after=s,scope='Explicit research scenario; no source inventory or external purchase-order write')
        c.execute('UPDATE operations_cases SET revision=?,data=? WHERE case_id=?',(s['revision'],dumps(s),case_id))
        c.execute('INSERT INTO operations_actions VALUES(?,?,?,?,?)',(request.action_id,case_id,utcnow(),digest,dumps(record)))
    return s

def plan_work(cases,minutes=10,delay_hours=3):
    """Exact small knapsack, conditional units rather than invented dollar savings."""
    candidates=[]
    for s in cases:
        if s['review']=='rejected' or s['verified']:continue
        duration=3+math.ceil(s['refill_available']*.5)
        hypothetical_empty=(s['shelf']==0) if s['review']=='approved' else s['candidate_quantity']>=s['initial_shelf']
        risk=s['forecast_daily']/16*delay_hours if hypothetical_empty else 0
        candidates.append(dict(case_id=s['case_id'],sku=s['sku'],minutes=duration,conditional_units_at_risk=round(risk,4),
          task='Resolve conflicting evidence first' if s['disputed'] and s['review']=='pending' else 'Review count, then refill' if s['review']=='pending' else 'Verify refill' if s['restocked_units'] else 'Refill shelf',
          proposed_units=s['refill_available'],requires_review=s['review']=='pending'))
    # Bound work even if a future intake has a large queue.
    candidates=sorted(candidates,key=lambda r:r['conditional_units_at_risk'],reverse=True)[:20]
    dp={0:(0.,[])}
    for i,t in enumerate(candidates):
        for used,(benefit,ids) in sorted(list(dp.items()),reverse=True):
            nxt=used+t['minutes'];score=benefit+t['conditional_units_at_risk']
            if nxt<=minutes and (nxt not in dp or dp[nxt][0]<score):dp[nxt]=(score,ids+[i])
    used,(benefit,ids)=max(dp.items(),key=lambda r:(r[1][0],-r[0]));selected=[candidates[i] for i in ids]
    return dict(time_budget_minutes=minutes,proposed_minutes=used,delay_hours=delay_hours,tasks=selected,
      conditional_units_at_risk=round(benefit,4),unselected_cases=len(candidates)-len(ids),
      assumptions='Scenario: 16 trading hours/day, selected delay window, 3-minute visit plus 30 seconds/unit. Historical M5 forecasts are uncertain. Risk is conditional, not measured recovered sales. Disputed counts still require review.')

def prepare_sales_replay(settings):
    from .warehouse import connect
    db=Database(settings);initialize(db)
    with connect(settings) as c:
        records=c.execute('''SELECT t.rowid row_id,t."Transaction Date"::VARCHAR original_date,t."Product No" sku,t."Product Description" title,t."Qty Sold" quantity,t."Store" source_store,s.quantity opening_units,s.source_start,s.source_end
          FROM retail_sales t JOIN retail_stock_latest s ON t."Store"=s.store_id AND t."Product No"=s.sku
          WHERE t."Store"='STR-1010' AND t."Qty Sold">0 AND s.quantity>0
          ORDER BY t."Transaction Date" DESC,t."Product No",t.rowid LIMIT 60''').df().to_dict('records')
    result=dict(records=records,origin='archive_replay',source='Retail Transactions and Stocks',
      notice='Actual source sales rows and quantities replayed on receipt. Original day-level dates are retained. Opening inventory comes from separate latest intervals; this is a simulated projection, not a historical reconciliation or a live merchant connection.')
    db.metadata('operations_replay',result);return result

def ingest_sale(db,event:PosEvent,origin='connector_event',source=None):
    initialize(db)
    if event.occurred_at.utcoffset() is None:raise ValueError('POS timestamps require a timezone')
    if not db.rows('SELECT sku FROM products WHERE store_id=? AND sku=?',(event.store_id,event.sku)):raise ValueError('Register the source store and product before ingesting events')
    data=event.model_dump(mode='json');data.update(origin=origin,source=source)
    digest=hashlib.sha256(dumps(data).encode()).hexdigest()
    with db.connect(write=True) as c:
        row=c.execute('SELECT payload_hash,data FROM operations_sales WHERE event_id=?',(event.event_id,)).fetchone()
        if row:
            if row['payload_hash']!=digest:raise Conflict('Event identifier reused with different content')
            return dict(json.loads(row['data']),duplicate=True)
        data['received_at']=utcnow()
        c.execute('INSERT INTO operations_sales VALUES(?,?,?,?,?,?,?)',(event.event_id,event.store_id,event.sku,data['received_at'],origin,digest,dumps(data)))
    return dict(data,duplicate=False)

def replay_next(db):
    replay=db.metadata('operations_replay')
    if not replay:raise ValueError('Prepare real sales replay first')
    with db.lease('operations-sales-replay',60):
        used={r['event_id'] for r in db.rows("SELECT event_id FROM operations_sales WHERE origin='archive_replay'")}
        row=next((r for r in replay['records'] if 'archive-retail-'+str(r['row_id']) not in used),None)
        if not row:return dict(complete=True,notice='All prepared source records have been replayed; no duplicates or fabricated new sales were added.')
        e=PosEvent(event_id='archive-retail-'+str(row['row_id']),store_id='STOCK_STR_1010',sku=row['sku'],
          occurred_at=row['original_date']+'T12:00:00+00:00',kind='sale',quantity=row['quantity'])
        return ingest_sale(db,e,'archive_replay',dict(row,timestamp_note='Source supplies a date only; noon UTC is a replay placeholder, not a measured checkout time.'))

def sales_state(db):
    initialize(db);events=[json.loads(r['data']) for r in db.rows('SELECT data FROM operations_sales ORDER BY received_at,event_id')]
    base={(p['store_id'],p['sku']):p for p in db.objects('products')};totals={};replay=db.metadata('operations_replay') or {}
    for e in events:
        key=(e['store_id'],e['sku']);source=e.get('source') or {};meta=db.metadata('source_workspace:'+e['store_id']) or {}
        if key not in totals:
            inv=next((x for x in meta.get('inventory',[]) if x['sku']==e['sku']),{})
            opening=source.get('opening_units',inv.get('ledger_units'))
            totals[key]=dict(store_id=e['store_id'],sku=e['sku'],title=source.get('title',base[key]['title']),opening_units=opening,
              projected_units=opening,sales=0.,returns=0.,receipts=0.,origin=e['origin'],events=0)
        t=totals[key];delta=-e['quantity'] if e['kind']=='sale' else e['quantity']
        if t['projected_units'] is not None:t['projected_units']+=delta
        t[{'sale':'sales','return':'returns','receipt':'receipts'}[e['kind']]]+=e['quantity'];t['events']+=1
    alerts=[dict(t,action='Verify stock and prepare supplier review',order_units=None,
      reason='Projected shadow stock <= 1 unit. One unit is a demo threshold; lead times and verified counts are missing, so purchase quantity is withheld.') for t in totals.values() if t['projected_units'] is not None and t['projected_units']<=1]
    return dict(events=events[-30:][::-1],event_count=len(events),sales_quantity=sum(e['quantity'] for e in events if e['kind']=='sale'),
      inventory=list(totals.values()),supplier_reviews=alerts,last_received_at=events[-1]['received_at'] if events else None,
      replay_total=len(replay.get('records',[])),replay_count=sum(e['origin']=='archive_replay' for e in events),notice=replay.get('notice'),
      live_connector_events=sum(e['origin']=='connector_event' for e in events))

def desk(db,minutes=10,delay_hours=3):
    cases=current_cases(db);sales=sales_state(db)
    audit=[dict(json.loads(r['data']),action_id=r['action_id'],case_id=r['case_id'],at=r['at']) for r in db.rows('SELECT * FROM operations_actions ORDER BY at DESC LIMIT 30')]
    return dict(cases=cases,sales=sales,audit=audit,plan=plan_work(cases,minutes,delay_hours),usage=usage_summary(db),
      generated_at=utcnow(),summary=dict(cases=len(cases),review_required=sum(s['review']=='pending' for s in cases),
      disputed=sum(s['disputed'] for s in cases),verified=sum(s['verified'] for s in cases),supplier_reviews=len(sales['supplier_reviews'])),
      notice='Research control tower. Video counts are model inferences; product joins, backroom stock, checkout and operator actions are explicit simulations. POS replay uses real historical rows. No external orders or original source inventory writes.')
