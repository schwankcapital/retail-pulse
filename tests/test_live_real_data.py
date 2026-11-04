import json
from dataclasses import replace
import pandas as pd
import pytest
from fastapi.testclient import TestClient
from retail_pulse.api import create_app
from retail_pulse.camera_ai import analyze_camera
from retail_pulse.ingestion import insert_records
from retail_pulse.real_data import blank_inventory, catalog, save_workspace


def test_source_inventory_is_not_a_physical_audit(db):
    inv=[blank_inventory('REAL-1','Original source description',2.5,source_end_date='2025-01-01')]
    catalog(db,'REAL',inv)
    daily=[dict(store_id='REAL',sku='REAL-1',date='2025-01-01',weekday=2,sales=.125,
          eligible_sales=0,contradictory_sales=0,available_hours=0,unavailable_hours=0,unknown_hours=16,open_hours=16)]
    save_workspace(db,'REAL',daily,inv,dict(source='Fixture source',unit='recorded quantity',source_url='https://example.org',
       availability_measured=False,inventory_measured=True,notice='Real source records'))
    report=db.current_overview('REAL')
    assert report['measured_sales_total']==.125
    assert report['inventory'][0]['ledger_units']==2.5
    assert report['inventory'][0]['estimated_units'] is None
    assert report['inventory'][0]['variance_units'] is None
    assert report['demand']==[] and report['decisions']==[]
    assert not report['synthetic']
    client=TestClient(create_app(db.settings))
    assert client.get('/api/daily?store_id=REAL').json()[0]['sku']=='REAL-1'
    assert client.get('/api/daily?store_id=REAL').json()[0]['sales']==.125


@pytest.mark.parametrize('end,valid',[(.5,True),(2.,False)])
def test_live_video_results_are_bounded_and_separate(db,monkeypatch,end,valid):
    p=db.settings.home/'media/real.mp4';p.write_bytes(b'test-media')
    insert_records(db,'evidence',[dict(evidence_id='REALVIDEO',path='media/real.mp4',media_type='video',store_id='S1',
       camera_id='CAM1',start_at='1970-01-01T00:00:00Z',duration_seconds=1,seconds_to_world=1,sha256='test',synthetic=False)],strict=True)
    deleted=[]
    class Client:
        def __init__(self,s):pass
        def __enter__(self):return self
        def __exit__(self,*a):pass
        def upload(self,p):return 'file-test'
        def delete_file(self,f):deleted.append(f);return True
        def create_response(self,*a):
            text=json.dumps({'events':[dict(start_seconds=.1,end_seconds=end,kind='interaction',item_description='Unidentified package',
                  visible_count_min=None,visible_count_max=None,confidence=.7,note='Occluded')],'limitations':['No SKU mapping']})
            return {'output':[{'type':'message','content':[{'type':'output_text','text':text}]}]}
    monkeypatch.setattr('retail_pulse.camera_ai.MetaClient',Client)
    if valid:
        r=analyze_camera(db,'REALVIDEO');assert r['events'][0]['origin']=='muse_live'
        assert analyze_camera(db,'REALVIDEO')['cache_hit']
    else:
        with pytest.raises(ValueError,match='out-of-bounds'):analyze_camera(db,'REALVIDEO')
        assert db.metadata('camera_timeline:REALVIDEO') is None
    assert deleted==['file-test']
    assert db.objects('observations')==[]


def test_backend_config_never_exposes_provider_secret(settings):
    client=TestClient(create_app(replace(settings,mode='meta',api_key='secret-test-value')))
    result=client.get('/api/config')
    assert result.json()['live_ready']
    assert 'secret-test-value' not in result.text
