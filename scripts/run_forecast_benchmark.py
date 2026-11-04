"""Run or load the fixed-origin real-data benchmark; retain the spending ledger."""
from retail_pulse.config import Settings
from retail_pulse.forecast_benchmark import prepare_forecast_benchmark

report=prepare_forecast_benchmark(Settings.from_env())
print('Selected:',report['selected'])
print('Real series:',report['series'],'7-day test WAPE:',report['selected_test_wape_7d'])
print('Mean-28 baseline WAPE:',report['baseline_test_wape_7d'])
print('7-day empirical band coverage:',report['interval']['7']['empirical_test_coverage'])
