from retail_pulse.config import Settings
from retail_pulse.db import Database
from retail_pulse.camera_ai import analyze_camera, INSTRUCTIONS
import hashlib,json
s=Settings.from_env();db=Database(s)
# Retain already obtained real inference without another billable request.
eid='merl-1-1-60s-STOCK_STR_1010';e=db.evidence(eid);r=db.metadata('camera_timeline:'+eid)
key='muse_camera:'+hashlib.sha256((eid+e['sha256']+s.muse_model+INSTRUCTIONS).encode()).hexdigest();db.metadata(key,r)
for clip in ['merl-2-1-60s','merl-3-1-60s']:
 r=analyze_camera(db,clip+'-STOCK_STR_1010');print(clip,r['muse_event_count'],flush=True)
for clip in ['merl-1-1-60s','merl-2-1-60s','merl-3-1-60s']:
 src=clip+'-STOCK_STR_1010';dest=clip+'-FRESH_0';r=db.metadata('camera_timeline:'+src);e=db.evidence(dest)
 assert db.evidence(src)['sha256']==e['sha256']
 r.update(store_id='FRESH_0',evidence_id=dest)
 for event in r['events']:event.update(evidence_id=dest,observation_id=event['observation_id'].replace(src,dest))
 db.metadata('camera_timeline:'+dest,r)
 key='muse_camera:'+hashlib.sha256((dest+e['sha256']+s.muse_model+INSTRUCTIONS).encode()).hexdigest();db.metadata(key,r)
print('Actual Muse results available for identical footage in both workspaces')
