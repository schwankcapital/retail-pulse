from retail_pulse.config import Settings
from retail_pulse.db import Database
from retail_pulse.camera_ai import analyze_camera
s=Settings.from_env();db=Database(s)
r=analyze_camera(db,'merl-1-1-60s-STOCK_STR_1010')
print({'model':r['muse_model'],'actual_muse_events':r['muse_event_count'],'limitations':r['muse_limitations']})
