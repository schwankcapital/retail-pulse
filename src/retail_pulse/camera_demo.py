"""Real MERL camera clips with local pixel-motion analysis and source annotations."""
from datetime import datetime, timedelta, timezone
from pathlib import Path
import hashlib
import json
import subprocess

import cv2
import imageio_ffmpeg
import numpy as np
from scipy.io import loadmat

from .db import Database
from .ingestion import insert_records

ACTIONS = ('Reach to shelf', 'Retract from shelf', 'Hand in shelf', 'Inspect product', 'Inspect shelf')


def motion_intervals(path: Path, sample_hz=5, threshold=.015):
    """Measure full-frame pixel changes; makes no object/action identity claims."""
    cap = cv2.VideoCapture(str(path))
    try:
        fps = cap.get(cv2.CAP_PROP_FPS)
        if fps <= 0: raise ValueError('Invalid video FPS')
        step = max(1, round(fps/sample_hz))
        duration = cap.get(cv2.CAP_PROP_FRAME_COUNT)/fps
        previous=None; scores=[]; index=0
        while True:
            ok,frame=cap.read()
            if not ok: break
            if index % step == 0:
                gray=cv2.GaussianBlur(cv2.cvtColor(cv2.resize(frame,(320,180)),cv2.COLOR_BGR2GRAY),(5,5),0)
                if previous is not None:
                    score=float(np.mean(cv2.absdiff(gray,previous)>20))
                    scores.append((index/fps,score))
                previous=gray
            index+=1
        if not scores: raise ValueError('No decodable motion samples')
        rows=[]; active=None
        for at,score in scores:
            if score>=threshold:
                if active is None: active={'start_seconds':max(0,at-step/fps),'end_seconds':at,'peak_changed_fraction':score}
                active['end_seconds']=min(duration,at+step/fps)
                active['peak_changed_fraction']=max(active['peak_changed_fraction'],score)
            elif active is not None:
                rows.append(active);active=None
        if active is not None: rows.append(active)
        return rows,dict(sample_hz=fps/step,threshold=threshold,pixel_delta_threshold=20,
                         decoded_frames=index,duration_seconds=duration)
    finally: cap.release()


def prepare_camera_demo(settings, root:Path, store_id='DEMO_01'):
    db=Database(settings)
    if not db.objects('products',store_id): raise ValueError('Generate the store demo first')
    raw=root/'merl_shopping'/'raw'
    outputs=[]
    for clip in ('1_1','2_1','3_1'):
        source=next(raw.rglob(clip+'_crop.mp4'))
        label=next(raw.rglob(clip+'_label.mat'))
        eid='merl-'+clip.replace('_','-')+'-60s'
        target=settings.home/'media'/f'{eid}.mp4'
        subprocess.run([imageio_ffmpeg.get_ffmpeg_exe(),'-y','-loglevel','error','-i',str(source),
                        '-t','60','-an','-c:v','libx264','-pix_fmt','yuv420p','-movflags','+faststart',str(target)],
                       check=True,capture_output=True,timeout=120)
        motion,parameters=motion_intervals(target)
        duration=parameters['duration_seconds']
        # No original capture date is supplied. Epoch is an explicitly arbitrary seek anchor.
        anchor=datetime(1970,1,1,tzinfo=timezone.utc)
        events=[]
        for row in motion:
            events.append(dict(row,kind='Frame motion',origin='local_frame_analysis',
                note='Measured pixel change across the frame; not a classified action, sale or stockout.'))
        for action,intervals in zip(ACTIONS,loadmat(label)['tlabs'].ravel()):
            for first,last in intervals:
                start=max(0,(int(first)-1)/30);end=min(duration,int(last)/30)
                if start>=end:continue
                events.append(dict(start_seconds=start,end_seconds=end,kind=action,origin='publisher_annotation',
                    note='MERL supplied action label, aligned using original 30 fps frame indices; not newly inferred.'))
        events.sort(key=lambda row:(row['start_seconds'],row['origin']))
        for i,row in enumerate(events):
            row.update(observation_id=f'{eid}-{i}',evidence_id=eid,
                       at=(anchor+timedelta(seconds=row['start_seconds'])).isoformat())
        digest=hashlib.sha256(target.read_bytes()).hexdigest()
        record=dict(evidence_id=eid,path=str(target.relative_to(settings.home)),media_type='video',
                    store_id=store_id,camera_id='MERL_OVERHEAD',start_at=anchor.isoformat(),
                    duration_seconds=duration,seconds_to_world=1,sha256=digest,synthetic=False)
        insert_records(db,'evidence',[record],'merl_camera_demo',strict=True)
        result=dict(evidence_id=eid,store_id=store_id,title=f'MERL overhead clip {clip} / first 60 seconds',
                    source_url='https://www.merl.com/research/downloads/MERL_Shopping_Dataset',
                    source_filename=source.name,annotation_filename=label.name,
                    capture_time='Unknown; timeline uses clip-relative seconds',parameters=parameters,events=events,
                    limitations=['Research/educational dataset; retain MERL attribution.',
                      'This clip is attached to the demo workspace; it does not depict its simulated inventory.',
                      'Motion is computed from pixels. Named actions are supplied publisher annotations.',
                      'No SKU identity, stock quantity, payment, theft or stockout is inferred.'])
        db.metadata('camera_timeline:'+eid,result)
        (settings.home/'reports'/f'camera_{eid}.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
        outputs.append(dict(evidence_id=eid,events=len(events),motion_intervals=len(motion)))
    return outputs
