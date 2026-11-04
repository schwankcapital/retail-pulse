from retail_pulse.config import Settings
from retail_pulse.warehouse import prepare_warehouse
print(prepare_warehouse(Settings.from_env(),'data/external'))
