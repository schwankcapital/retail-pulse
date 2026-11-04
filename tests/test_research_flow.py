from dataclasses import replace
import numpy as np
import pandas as pd
import pytest
import httpx
from retail_pulse.flow_demo import replay_transfers
from retail_pulse.model_lab import features,FEATURES
from retail_pulse.meta_client import MetaClient,BudgetExceeded
from retail_pulse.warehouse import browse

def event(action='take',qty=1,start=1,end=2,track='a',confidence=.9):
    return dict(action=action,quantity_min=qty,quantity_max=qty,start_seconds=start,end_seconds=end,track_id=track,confidence=confidence)

def test_pickup_moves_shelf_but_not_store_stock():
    result=replay_transfers([event()],1)
    assert (result['shelf_after'],result['in_hand_after'],result['store_units_after'])==(0,1,1)
    assert result['checkout_matched']['store_units_after']==0
    assert result['checkout_unmatched']['store_units_after']==1
    assert 'no theft conclusion' in result['checkout_unmatched']['review']

def test_replay_deduplicates_overlap_and_balances_return():
    result=replay_transfers([event(),event(start=1.2,end=2.1),event('put',start=3,end=4)],2)
    assert (result['shelf_after'],result['in_hand_after'])==(2,0)
    assert sum(r['applied'] for r in result['events'])==2

def test_uncertain_count_or_confidence_never_changes_stock():
    uncertain=dict(event(),quantity_max=2)
    result=replay_transfers([uncertain,event(confidence=.7),event('touch')],1)
    assert result['shelf_after']==1 and all(not e['applied'] for e in result['events'])

def test_impossible_balance_goes_to_review():
    result=replay_transfers([event(qty=3)],2)
    assert result['shelf_after']==2 and not result['events'][0]['applied']

def test_independent_count_disagreement_overrides_primary_confidence():
    result=replay_transfers([dict(event(qty=2,confidence=.99),hold_for_review=True)],2)
    assert result['shelf_after']==2 and result['in_hand_after']==0
    assert not result['events'][0]['applied']

def test_features_do_not_read_current_or_future_sales():
    f=pd.DataFrame({'sku':['A']*60,'date':pd.date_range('2020-01-01',periods=60),'sales':np.arange(60.)})
    original=features(f);f.loc[40:,'sales']=100000;changed=features(f)
    pd.testing.assert_frame_equal(original.loc[:40,FEATURES],changed.loc[:40,FEATURES])
    assert changed.loc[41,'lag1']==100000

def test_total_cap_cannot_be_raised_through_config(settings):
    settings=replace(settings,mode='meta',api_key='fake-test-only',budget=1000)
    with MetaClient(settings,transport=httpx.MockTransport(lambda request:pytest.fail('No HTTP request allowed'))) as c:
        c.reserve('previous','muse-spark-1.3',59)
        with pytest.raises(BudgetExceeded):c.create_response({'model':settings.muse_model,'input':'test'},'over_cap')

def test_library_rejects_sql_identifier_injection(settings):
    with pytest.raises(ValueError):browse(settings,'m5; DROP TABLE m5')
