from retail_pulse.config import Settings
from retail_pulse.video_transfers import prepare_and_read
prepare_and_read(Settings.from_env(),'data/external')
