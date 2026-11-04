# Public source package

The repository contains the complete Python application, browser interface,
tests, preparation scripts, synthetic example contracts and hackathon guides.
The repository's MIT license applies to project code, not independently sourced
datasets or video. Publisher access conditions continue to apply to those sources.

## First run

Follow the fresh-clone instructions at the top of README.md. The offline demo
requires no API key. It is separate from the real-source research demonstration.
Never regenerate a demo in an occupied runtime or reset the API usage database.

## Real research demonstration

Original source downloads are deliberately not included in Git. Obtain them
from their publishers, using these source names and directories under
`data/external/<name>/raw/` (archives belong under `archives/`):

| Directory | Publisher |
|---|---|
| retailaction | https://huggingface.co/datasets/standard-cognition/RetailAction |
| merl_shopping | https://www.merl.com/research/downloads/MERL_Shopping_Dataset |
| sku110k | https://github.com/eg4000/SKU110K_CVPR19 |
| cosmetics_retail | https://huggingface.co/datasets/Innovatiana/innv-cosmetics-dataset-for-retail |
| agrishelf | https://data.mendeley.com/datasets/s3vc2552sf/3 |
| freshretailnet | https://huggingface.co/datasets/Dingdong-Inc/FreshRetailNet-50K |
| retail_transactions_stocks | https://data.mendeley.com/datasets/27x8mjm8k4/1 |
| walmart_m5 | https://www.kaggle.com/competitions/m5-forecasting-accuracy/data |
| favorita | https://www.kaggle.com/competitions/favorita-grocery-sales-forecasting/data |

Some downloads require a publisher account or acceptance of dataset conditions.
The preparation scripts document the expected extracted filenames. Install
the `data` extras for DuckDB and Parquet support. Data preparation is not part
of the automatic offline starter and can require substantial disk space.

The prepared workspace uses `RETAIL_PULSE_HOME=runtime/real-data`. Source
dashboards are built with `python -m retail_pulse prepare-real --datasets data/external`.
`scripts/prepare_expanded_demo.py` indexes the warehouse and prepares M5 tuning,
counted-video research scenarios and source imagery. It can make paid Meta calls.
`scripts/prepare_visual_grounding.py` prepares SAM geometry and the Muse count
challenge. Rebuild the flow afterward with `scripts/build_product_journey.py`.
`scripts/run_forecast_benchmark.py` prepares the separate weekly evaluation.
After the warehouse and flow exist, `retail_pulse.operations.prepare_sales_replay`
prepares historical POS rows; the operations API initializes scenario cases.

Real video analysis needs a privately configured `MODEL_API_KEY`, Meta mode,
and authorization for external media. Consult docs/META_INTEGRATION.md before
running paid preparation. Keep a single persisted usage ledger for the agreed
budget; the hard maximum in code is $60, and configuration may set a lower limit.

## What is excluded

- `.env` and credentials; `.env.example` contains blank credential placeholders.
- `data/`, `runtime/`, virtual environments, model binaries and databases.
- Local screenshots, validation logs, build outputs and source archives.

`artifacts/demo-verification.json` records a previous validation snapshot of
the prepared local demo. Its results are not a guarantee for a new installation.
The complete public-code package can be downloaded from GitHub's Code → Download ZIP.
