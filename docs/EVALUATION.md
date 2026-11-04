# Evaluation and evidence limits

## Reproduce the included result

```text
python -m retail_pulse demo --seed 71 --days 56
python -m retail_pulse evaluate
python -m pytest -q
```

Use a new `--home` before the subcommand to avoid overwriting an existing dataset.
The package's build-time results are in `artifacts/`. They are actual outputs of
this implementation, not proposed results or a forecast of real-store performance.

## Keep three evaluations separate

1. **Engineering correctness:** schema validation, idempotency, clock conversion,
   interval arithmetic, conservative count fusion, tool permissions, API contract
   tests and bounded spending. Tests use synthetic inputs and mock provider calls.
2. **Forecast evaluation:** chronological validation and test splits using sales
   only in fully available periods, where the simulator's sales equal demand.
3. **Latent-demand evaluation:** an isolated evaluator reads withheld simulator
   demand after predictions have been saved. The forecasting models, perception
   adapter and agents do not receive that ground truth.

No test in this release establishes real Muse/SAM perception accuracy. The
synthetic video's availability labels are supplied by the simulator. They are
explicitly marked `demo_replay`, rather than represented as model detections.

## Default dataset and split

Six SKUs and 56 calendar days, random seed 71. The generated scenario contains
676 recorded transactions, 257 RFID observations, 42 barcode scans and 4,095
visual/count observations. These are generated records, not business/customer data.

| Stage | Dates | Role |
|---|---|---|
| Train | August 31 - September 27, 2026 | Initial parameter fit |
| Validation | September 28 - October 11, 2026 | Select exposure baseline or Poisson regression |
| Test | October 12 - October 25, 2026 | Evaluate after training on train + validation |
| Deployment refit | Through October 25, 2026 | Refit selected architecture only after evaluation |

The simpler exposure baseline won validation in this run. The system does not
force the more complex machine-learning candidate to win.

### Ordinary holdout metrics

These use **54 fully available SKU-days** from the test period. Censored/unknown
periods are not relabeled with model predictions and then used as ground truth.

| Model | MAE, units per SKU-day | WAPE | Bias |
|---|---:|---:|---:|
| Exposure baseline | 1.2500 | 58.70% | +11.92% |
| Poisson regression | 1.3900 | 65.27% | +24.79% |

These errors are not evidence of high forecast accuracy. A passing health gate
only means the configured checks pass; it is not a certification of the model.
Low-volume counts, short history, censoring and a small holdout require caution.

### Separate synthetic latent-demand benchmark

This uses **84 SKU-days** including stockout periods, against withheld simulator
demand. All three methods use the same train/test dates. The inventory-only
baseline ignores availability; the other two use availability exposure.

| Model | MAE, units per SKU-day | WAPE | Bias |
|---|---:|---:|---:|
| Inventory-only baseline | 4.6236 | 81.08% | -61.24% |
| Exposure baseline | 2.1987 | 38.56% | -15.43% |
| Poisson regression | 4.2952 | 75.32% | -48.45% |

This shows the value of availability information **in this controlled scenario**.
It does not measure Meta model superiority, prove causal demand recovery in real
stores, or establish business savings. It is not a randomized field experiment.

## Statistical assumptions

The exposure baseline estimates a product/weekday demand intensity from observed
in-stock time, with smoothing for sparse data. The Poisson candidate uses product,
weekday and time-trend features, with available hours as observation weight.
The initial model assumes roughly stable within-day intensity conditional on
these features. Censoring correlated with hour-of-day demand can violate this.

The displayed 90% bounds are conditional Poisson predictive intervals. They omit
parameter uncertainty, visibility errors, product matching errors, substitution
and unknown camera time. Unknown camera periods do not become confirmed stockouts.
Do not sum intervals across dependent products and call them a portfolio interval.

## Before a hackathon performance claim

Use a second dataset with independently annotated, unseen camera footage. Include
normal purchases, misplaced returns, restocking, occlusion, incomplete RFID scans,
clock offsets and a case that cannot be resolved. Split by recording session/store,
not neighboring frames from the same clip.

Measure:

- Shelf-state precision/recall, stockout interval timing error and unknown coverage.
- SKU identity/quantity error, invalid extraction rate and calibrated confidence.
- Count-error/variance classification accuracy against independent physical audits.
- Demand error only where independently identifiable; report simulator-only scores separately.
- Agent unsupported-claim rate, citation validity, tool cost and useful abstention.
- Recommendation feasibility and intervention results under a controlled replay.

Compare inventory-only, inventory plus availability, and the full system. To
isolate the Muse contribution, compare manually annotated availability with
Muse-derived availability on the same held-out scenes. Repeat seeds and report
variation. Do not select a good seed after inspecting its test performance.

## Numerical definitions

`WAPE = sum(abs(predicted - actual)) / sum(actual)`; a zero denominator returns
an undefined value rather than a misleading percentage. `Bias` uses the same
denominator and signed errors. Metrics are not reported as 'accuracy = 1 - WAPE'.
