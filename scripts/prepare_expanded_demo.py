"""Explicit preparation command. Reuses the configured runtime and spending ledger."""
import runpy
from retail_pulse.config import Settings
from retail_pulse.warehouse import prepare_warehouse
from retail_pulse.model_lab import run_experiments
from retail_pulse.video_transfers import prepare_and_read
from retail_pulse.flow_demo import prepare_flow

s=Settings.from_env()
prepare_warehouse(s,'data/external',reuse=True)
runpy.run_path('scripts/expand_workspaces.py',run_name='__main__')
run_experiments(s)
clips=[0,2,9,11,28,30,42,57,68,85,101,123,145,167,189,210,250,290,340,380,420,460]
prepare_and_read(s,'data/external',tuple(f'{i:06d}' for i in clips))
runpy.run_path('scripts/prepare_source_assets.py',run_name='__main__')
prepare_flow(s)
print('Expanded demo prepared; original source files and usage history retained.')
