import json
from retail_pulse.config import Settings
from retail_pulse.db import Database
from retail_pulse.agents import run_agent
s=Settings.from_env();db=Database(s)
for store,role,q in [('STOCK_STR_1010','business','Summarize the actual product inventory and recorded sales. Cite evidence and explain which measurements are missing.'),('FRESH_0','health','Review forecast evaluation and data quality for these real normalized source records. Explain limitations and recommended checks.')]:
 r=run_agent(db,store,q,role,'meta')
 (s.home/'reports'/f'live_{role}_{store}.json').write_text(json.dumps(r,indent=2),encoding='utf-8')
 print(store,role,r['model'],r['answer'],flush=True)
