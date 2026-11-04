import cv2
import numpy as np
from retail_pulse.camera_demo import motion_intervals
from retail_pulse.api import create_app
from retail_pulse.db import Database
from retail_pulse.agents import ReadOnlyTools
from fastapi.testclient import TestClient


def test_motion_measures_pixels_and_bounds(tmp_path):
    p=tmp_path/'motion.mp4'
    w=cv2.VideoWriter(str(p),cv2.VideoWriter_fourcc(*'mp4v'),10,(64,64))
    for i in range(30):w.write(np.full((64,64,3),255 if 10<=i<20 else 0,dtype=np.uint8))
    w.release()
    events,params=motion_intervals(p)
    assert len(events)==2
    assert all(0<=r['start_seconds']<r['end_seconds']<=3 for r in events)
    assert params['decoded_frames']==30


def test_camera_scope_and_evidence_separation(db):
    db.metadata('camera_timeline:E1',{'evidence_id':'E1','store_id':'S1','events':[]})
    client=TestClient(create_app(db.settings))
    assert client.get('/api/camera-timeline/E1?store_id=S1').status_code==200
    assert client.get('/api/camera-timeline/E1?store_id=OTHER').status_code==404
    assert client.get('/api/evidence?store_id=S1').json()[0]['camera_analysis']
    assert db.objects('observations')==[]
