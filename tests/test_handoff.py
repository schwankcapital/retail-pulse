from dataclasses import replace
from io import BytesIO
import json
from concurrent.futures import ThreadPoolExecutor

import httpx
import pytest
from fastapi.testclient import TestClient
from PIL import Image

from retail_pulse.api import create_app
from retail_pulse.config import Settings
from retail_pulse.db import Database
from retail_pulse.ingestion import insert_records
from retail_pulse.meta_client import MetaClient
from retail_pulse.perception import analyze_media, register_media
from retail_pulse.schemas import Evidence


def png():
    stream = BytesIO()
    Image.new('RGB', (48, 32), 'white').save(stream, format='PNG')
    return stream.getvalue()


def visual_batch(sku='A'):
    return {'events': [{'sku':sku, 'zone_id':'Z1', 'start_seconds':0, 'end_seconds':1,
                        'kind':'shelf_state', 'availability':'available', 'count_min':2, 'count_max':2,
                        'confidence':0.9, 'visibility':0.95, 'note':'Mock contract input, not live detection'}],
            'limitations':['Only visible stock is measured']}


def test_api_upload_register_and_serve(db):
    with TestClient(create_app(db.settings)) as c:
        r = c.post('/api/upload-media', data={'store_id':'S1','camera_id':'CAM1','start_at':'2026-10-01T08:00:00Z'},
                   files={'file':('shelf.png',png(),'image/png')})
        assert r.status_code == 200, r.text
        eid = r.json()['evidence']['evidence_id']
        media = c.get('/api/media/' + eid)
        assert media.status_code == 200 and media.content == png()
        assert len(db.objects('observations')) == 0


@pytest.mark.parametrize('sku,success', [('A',True), ('INVENTED',False)])
def test_muse_numerical_extraction_handoff(db, monkeypatch, tmp_path, sku, success):
    settings = replace(db.settings, mode='meta', api_key='mock-contract-key', external_media=True)
    live_db = Database(settings)
    image = tmp_path/'sample.png'; image.write_bytes(png())
    evidence = register_media(live_db,image,'S1','CAM1','2026-10-01T08:00:00Z')
    requests = []
    def handler(request):
        body = json.loads(request.content); requests.append(body)
        assert body['text']['format']['type'] == 'json_schema'
        assert body['input'][0]['content'][1]['type'] == 'input_image'
        return httpx.Response(200,json={'status':'completed','usage':{'input_tokens':100,'output_tokens':100},
            'output':[{'type':'message','role':'assistant','content':[{'type':'output_text','text':json.dumps(visual_batch(sku))}]}]})
    monkeypatch.setattr('retail_pulse.perception.MetaClient',lambda s:MetaClient(s,transport=httpx.MockTransport(handler)))
    if success:
        result = analyze_media(live_db,evidence.evidence_id)
        assert result['ingestion']['inserted'] == 1
        record = live_db.objects('observations')[0]
        assert record['count_min'] == 2 and record['origin'] == 'muse'
        assert record['count_scope'] == 'visible'
        assert analyze_media(live_db,evidence.evidence_id)['content_cache_hit']
        assert len(requests) == 1
    else:
        with pytest.raises(ValueError,match='failed validation'):
            analyze_media(live_db,evidence.evidence_id)
        assert live_db.objects('observations') == []
        assert live_db.rows('SELECT COUNT(*) AS n FROM quarantine')[0]['n'] == 1


def test_api_health_agent_runs_after_validated_data_and_pipeline(db,monkeypatch):
    calls=[]
    def extraction(database,eid,sam_prompt):
        evidence=Evidence.model_validate(database.evidence(eid))
        from retail_pulse.perception import validate_extraction
        from retail_pulse.schemas import VisualBatch
        rows=validate_extraction(VisualBatch.model_validate(visual_batch()),evidence,database.objects('products'),'mock-model')
        result=insert_records(database,'observations',rows,strict=True)
        calls.append('validated_numeric_rows')
        return result
    def pipeline(settings,store_id):
        assert Database(settings).objects('observations',store_id)[0]['count_min']==2
        calls.append('pipeline')
        return {'health':{'status':'WARN'}}
    def agent(database,store_id,question,role,mode):
        assert calls==['validated_numeric_rows','pipeline']
        assert role=='health'
        calls.append('health_agent')
        return {'answer':'Mock health review'}
    monkeypatch.setattr('retail_pulse.api.analyze_media',extraction)
    monkeypatch.setattr('retail_pulse.api.run_pipeline',pipeline)
    monkeypatch.setattr('retail_pulse.api.run_agent',agent)
    with TestClient(create_app(db.settings)) as c:
        r=c.post('/api/upload-media',data={'store_id':'S1','camera_id':'CAM1','start_at':'2026-10-01T08:00:00Z','analyze':'true'},
                 files={'file':('shelf.png',png(),'image/png')})
        assert r.status_code==200,r.text
    assert calls==['validated_numeric_rows','pipeline','health_agent']


@pytest.mark.parametrize('key,value',[('budget',float('nan')),('output_price',-1),('input_price',float('inf')),
                                      ('timeout',0),('max_tokens',0),('max_media_mb',0)])
def test_invalid_configuration_rejected(tmp_path,key,value):
    with pytest.raises(ValueError):
        Settings(home=tmp_path/'run',**{key:value})


def test_evidence_identifier_cannot_escape_output_path():
    with pytest.raises(ValueError):
        Evidence(evidence_id='../../escape',path='x.png',media_type='image',store_id='S1',camera_id='CAM1',
                 start_at='2026-10-01T00:00:00Z',duration_seconds=1,sha256='example')


def test_report_identifiers_cannot_escape_path(db):
    with pytest.raises(ValueError):
        db.save_report('health','../../escape','2026-10-01T00:00:00Z',{})


def test_concurrent_report_files_are_atomic(db):
    def write(i):
        return db.save_report('health','S1',f'2026-10-01T00:00:{i:02d}Z',{'value':i})
    with ThreadPoolExecutor(max_workers=3) as executor:
        list(executor.map(write,range(6)))
    assert db.latest_report('health','S1')['value']==5
    assert json.loads((db.settings.home/'reports'/'health_S1.json').read_text())['value'] in range(6)
    assert not list((db.settings.home/'reports').glob('*.tmp'))
