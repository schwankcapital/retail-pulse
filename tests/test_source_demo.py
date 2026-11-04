from retail_pulse.agents import ReadOnlyTools, run_agent
from retail_pulse.db import Database
from retail_pulse.source_demo import build_profile
import pytest


def test_missing_dataset_fails_before_simulation(tmp_path):
    with pytest.raises(ValueError, match='All nine'):
        build_profile(tmp_path, tmp_path)


def test_agent_source_scope_and_no_ground_truth(demo_settings):
    db = Database(demo_settings)
    db.metadata('source_profile', {'store_id':'DEMO_01', 'origin':'SYNTHETIC_ASSIGNMENT',
        'sources':{'example':{'role':'Reference only', 'statistics':{'sample_rows':12}}},
        'limitations':['Not operational evidence'], 'products':[['private simulation config']],
        'daily_factors':[1.1]})
    result=ReadOnlyTools(db,'DEMO_01').call('get_data_sources',{})
    assert result['metrics']['sources.example.sample_rows']==12
    assert result['evidence_ids']==[]
    assert 'daily_factors' not in result['data']
    answer=run_agent(db,'DEMO_01','Which datasets were used?',mode='demo')
    assert 'source mappings are synthetic' in answer['answer']
    assert 'sources.example.sample_rows' in answer['metric_ids']
    assert 'error' in ReadOnlyTools(db,'OTHER_STORE').call('get_data_sources',{})
    db.metadata('source_profile', {})
