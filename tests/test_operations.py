import copy
from dataclasses import replace
import uuid
import pytest
from fastapi.testclient import TestClient
from retail_pulse.api import create_app
from retail_pulse.operations import CaseAction,PosEvent,Conflict,act,current_cases,ingest_sale,plan_work,sales_state

@pytest.fixture
def ops(db):
    transfer=dict(action='take',quantity_min=1,quantity_max=1,confidence=.9,product_description='Bottle')
    db.metadata('video_flow',dict(scenarios=[dict(scenario_id='clip-1',sku='A',clip=dict(transfers=[transfer],sha256='source-hash'),
        ledger=dict(initial_shelf=1),planning=dict(target_shelf=3),forecast_daily=8,forecast_7d=56)]))
    db.metadata('source_workspace:S1',dict(inventory=[dict(sku='A',ledger_units=5)]))
    current_cases(db)
    return db

def action(db,kind,quantity=None,note='',revision=None,action_id=None):
    s=current_cases(db)[0]
    return act(db,'clip-1',CaseAction(action_id=action_id or str(uuid.uuid4()),expected_revision=s['revision'] if revision is None else revision,action=kind,quantity=quantity,note=note))

def test_complete_loop_conserves_inventory_and_preserves_sources(ops):
    products=copy.deepcopy(ops.objects('products'));source=copy.deepcopy(ops.metadata('source_workspace:S1'))
    assert action(ops,'approve_count',1)['store_units']==4
    s=current_cases(ops)[0];assert (s['shelf'],s['in_hand'],s['backroom'])==(0,1,3)
    assert action(ops,'match_checkout',1)['store_units']==3
    s=action(ops,'restock',3);assert (s['shelf'],s['in_hand'],s['backroom'],s['store_units'])==(3,0,0,3)
    assert action(ops,'verify_shelf',3,'Simulated operator confirmation')['verified']
    assert ops.objects('products')==products and ops.metadata('source_workspace:S1')==source
    assert len(ops.rows('SELECT * FROM operations_actions'))==4
    action(ops,'restart_demo');assert len(ops.rows('SELECT * FROM operations_actions'))==5
    assert current_cases(ops)[0]['shelf']==1

def test_duplicate_and_stale_actions_are_safe(ops):
    first=action(ops,'approve_count',1,revision=0,action_id='action-0001')
    assert action(ops,'approve_count',1,revision=0,action_id='action-0001')['duplicate']
    assert len(ops.rows('SELECT * FROM operations_actions'))==1
    with pytest.raises(Conflict):action(ops,'approve_count',0,revision=0,action_id='action-0001')
    with pytest.raises(Conflict):action(ops,'restock',1,revision=0)
    assert current_cases(ops)[0]['revision']==first['revision']

def test_disputed_count_requires_review_note(ops):
    ops.metadata('visual_grounding',dict(clips={'clip-1':dict(comparison=dict(requires_human_review=True))}))
    with pytest.raises(ValueError,match='review note'):action(ops,'approve_count',1)
    assert current_cases(ops)[0]['shelf']==1
    assert action(ops,'approve_count',1,'Scenario review: one visible bottle')['shelf']==0

@pytest.mark.parametrize('kind,quantity',[('match_checkout',1),('restock',1),('verify_shelf',1),('approve_count',2)])
def test_invalid_actions_leave_state_unchanged(ops,kind,quantity):
    with pytest.raises(ValueError):action(ops,kind,quantity)
    assert current_cases(ops)[0]['revision']==0
    assert not ops.rows('SELECT * FROM operations_actions')

def test_verification_discrepancy_is_not_silently_adjusted(ops):
    action(ops,'approve_count',1);action(ops,'restock',2)
    with pytest.raises(ValueError,match='differs'):action(ops,'verify_shelf',3,'Demo discrepancy')
    assert current_cases(ops)[0]['shelf']==2
    assert not current_cases(ops)[0]['verified']

def event(**kwargs):
    return PosEvent(**dict(dict(event_id='sale-0001',store_id='S1',sku='A',occurred_at='2026-10-01T12:00:00Z',kind='sale',quantity=4),**kwargs))

def test_sales_idempotency_projection_and_supplier_gate(ops):
    assert not ingest_sale(ops,event())['duplicate']
    assert ingest_sale(ops,event())['duplicate']
    with pytest.raises(Conflict):ingest_sale(ops,event(quantity=3))
    s=sales_state(ops);assert s['event_count']==1 and s['inventory'][0]['projected_units']==1
    assert s['supplier_reviews'][0]['order_units'] is None
    ingest_sale(ops,event(event_id='return-001',kind='return',quantity=1))
    assert sales_state(ops)['inventory'][0]['projected_units']==2
    assert not sales_state(ops)['supplier_reviews']

def test_sales_reject_unknown_products_and_naive_timestamps(ops):
    with pytest.raises(ValueError,match='timezone'):ingest_sale(ops,event(occurred_at='2026-10-01T12:00:00'))
    with pytest.raises(ValueError,match='Register'):ingest_sale(ops,event(sku='unknown'))
    assert sales_state(ops)['event_count']==0

def test_planner_respects_time_budget_and_review_gate(ops):
    cases=current_cases(ops)
    assert not plan_work(cases,3)['tasks']
    plan=plan_work(cases,5);assert plan['proposed_minutes']<=5
    assert plan['tasks'][0]['requires_review']
    assert plan['conditional_units_at_risk']==1.5

def test_api_conflicts_validation_and_auth(ops):
    with TestClient(create_app(ops.settings)) as c:
        payload=event().model_dump(mode='json')
        assert c.post('/api/pos-events',json=payload).status_code==200
        assert c.post('/api/pos-events',json=dict(payload,quantity=5)).status_code==409
        assert c.post('/api/pos-events',json=dict(payload,quantity=-1)).status_code==422
        assert c.get('/api/operations?minutes=0').status_code==422
    with TestClient(create_app(replace(ops.settings,api_token='test-token'))) as c:
        assert c.post('/api/pos-events',json=payload).status_code==401
        assert c.get('/api/operations').status_code==401
