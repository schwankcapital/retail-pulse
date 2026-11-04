from retail_pulse.config import Settings
from retail_pulse.model_lab import run_experiments
run_experiments(Settings.from_env())
