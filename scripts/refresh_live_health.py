import json
from retail_pulse.config import Settings
from retail_pulse.db import Database
from retail_pulse.agents import run_agent
s=Settings.from_env();db=Database(s)
r=run_agent(db,'FRESH_0','Review the refreshed source-native health diagnostics. Distinguish publisher stock-status inconsistencies from camera errors. Normalized quantities are not counts and count predictive intervals are withheld. Explain safe next steps.','health','meta')
(s.home/'reports/live_health_FRESH_0.json').write_text(json.dumps(r,indent=2),encoding='utf-8')
print('Refreshed live health review saved; metric citations:',len(r['metric_ids']))
