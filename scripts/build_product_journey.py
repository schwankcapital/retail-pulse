"""Rebuild the joined scenario from saved observations and model results. No API call."""
from retail_pulse.config import Settings
from retail_pulse.flow_demo import prepare_flow
result=prepare_flow(Settings.from_env())
print(result['observed_clips'],'clips;',result['accepted_transfers'],'accepted transfers')
