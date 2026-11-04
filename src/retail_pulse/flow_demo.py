"""Replay observed movements against explicitly joined demonstration stock."""
import json,math
from .db import Database
from .warehouse import connect

def replay_transfers(transfers,initial_shelf,initial_hand=0,threshold=.75):
    shelf=initial_shelf;hand=initial_hand;whole=shelf+hand;events=[];seen=[]
    for index,t in sorted(enumerate(transfers),key=lambda p:p[1]['start_seconds']):
        row=dict(t,event_id=str(index),shelf_before=shelf,in_hand_before=hand,store_units_before=whole)
        qty=t.get('quantity_min');reason=None
        if t.get('hold_for_review'):reason='Independent Muse reading disagrees; human count review required'
        elif t['action'] not in {'take','put'}:reason='No confirmed transfer'
        elif qty is None or qty!=t.get('quantity_max') or qty<=0:reason='Exact quantity is not established'
        elif t['confidence']<threshold:reason='Below the review threshold'
        elif any(t['track_id']==p['track_id'] and t['action']==p['action'] and t['start_seconds']<p['end_seconds'] and p['start_seconds']<t['end_seconds'] for p in seen):reason='Overlapping observation of the same transfer'
        elif t['action']=='take' and shelf<qty:reason='Count exceeds scenario shelf balance'
        elif t['action']=='put' and hand<qty:reason='Return has no accounted in-hand balance'
        if reason is None:
            sign=1 if t['action']=='put' else -1;shelf+=sign*qty;hand-=sign*qty;seen.append(t)
        row.update(applied=reason is None,review_reason=reason,shelf_after=shelf,in_hand_after=hand,store_units_after=whole)
        events.append(row)
    return dict(initial_shelf=initial_shelf,initial_in_hand=initial_hand,initial_store_units=whole,events=events,
                shelf_after=shelf,in_hand_after=hand,store_units_after=whole,
                checkout_matched=dict(simulated=True,paid_units=hand,store_units_after=whole-hand,in_hand_after=0),
                checkout_unmatched=dict(simulated=True,paid_units=0,store_units_after=whole,in_hand_after=hand,review='No checkout match supplied; investigate, no theft conclusion'))

def prepare_flow(settings):
    db=Database(settings);model=db.metadata('model_lab')
    if not model:raise ValueError('Prepare real-data model experiment first')
    clips=[json.loads(r['value']) for r in db.rows("SELECT value FROM metadata WHERE key LIKE 'transfers:%' ORDER BY key")]
    ground=(db.metadata('visual_grounding') or {}).get('clips',{})
    with connect(settings) as c:
        products=c.execute("SELECT sku FROM m5_products WHERE store_id='CA_1' AND cat_id='FOODS' ORDER BY sku LIMIT 30").fetchall()
        stocks=c.execute('SELECT "Store" store_id,"Product No" sku,"Product Description" title,"Qty on hand" units,"Start Date"::VARCHAR start,"End Date"::VARCHAR finish FROM retail_stock WHERE "Qty on hand" BETWEEN 1 AND 5 ORDER BY "End Date" DESC,"Start Date" DESC,"Product No" LIMIT 500').df().to_dict('records')
        scenarios=[]
        for i,clip in enumerate(clips):
            exact=[t for t in clip['transfers'] if t['action'] in ('take','put') and t['quantity_min'] is not None and t['quantity_min']==t['quantity_max'] and t['quantity_min']>0 and t['confidence']>=.75]
            # Opening quantity copied from an actual stock record, with a disclosed cross-source identity join.
            needed=max(1,sum(t['quantity_min'] for t in exact if t['action']=='take'))
            stock=next((s for s in stocks if s['units']>=needed),stocks[0])
            exactstock=next((s for s in stocks if s['units']==needed),stock);stock=exactstock
            initial_hand=sum(t['quantity_min'] for t in exact if t['action']=='put')
            challenge=ground.get(clip['evidence_id'],{}).get('comparison')
            held=bool(challenge and challenge['requires_human_review'])
            ledger=replay_transfers([dict(t,hold_for_review=held) for t in clip['transfers']],stock['units'],initial_hand)
            item=products[i%len(products)][0];sku='CA_1/'+item
            future=[r for r in model['forecasts'] if r['sku']==sku];forecast=sum(r['forecast_units'] for r in future)
            history=c.execute('SELECT date,sales quantity FROM m5_model_series WHERE sku=? ORDER BY date',[sku]).df().to_dict('records')
            target=math.ceil(forecast/7*2+1)
            scenarios.append(dict(scenario_id=clip['evidence_id'],clip=clip,sku=item,store='CA_1',stock_anchor=stock,evidence_review=challenge,
              join_notice='Illustrative join: the filmed package is assigned to this real M5 identifier and a separate real retailer stock record. Neither identity nor opening shelf stock was recognized from video.',
              ledger=ledger,forecast_7d=forecast,forecast_daily=forecast/7,forecast=future,history=history,
              planning=dict(lead_days=2,safety_units=1,open_hours=16,assumed_empty_hours=3,target_shelf=target,
                refill_before=max(0,target-ledger['initial_shelf']),refill_after=max(0,target-ledger['shelf_after']),
                conditional_units_at_risk=forecast/7/16*3 if ledger['shelf_after']==0 else 0,
                explanation='Two-day lead, one safety unit, 16-hour day and three-hour empty-shelf scenario are demo assumptions. At-risk sales are conditional model estimates, not observed lost purchases. Video movements never inflate historical sales or forecast labels.'),
              initial_hand_notice='Demo assumes the returning units were already in hand before this clip.' if initial_hand else None))
    scenarios.sort(key=lambda s:(-sum(e['applied'] and e['action']=='take' for e in s['ledger']['events']),s['scenario_id']))
    report=dict(scenarios=scenarios,threshold=.75,model_selected=model['selected'],
      observed_clips=len(clips),accepted_transfers=sum(e['applied'] for s in scenarios for e in s['ledger']['events']),
      notice='Real video and live Muse observations; explicitly simulated catalog mapping, shelf allocation and checkout. Replays do not write to source inventories or training labels. No person is identified or accused.')
    db.metadata('video_flow',report);(settings.home/'reports/video_flow.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
    return report
