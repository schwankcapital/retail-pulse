# Retail Pulse

**In-Store Retail Super Intelligence**

## Run from a fresh clone

Python 3.11–3.13 is required. From the repository folder:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -e ".[dev,data]"
Copy-Item .env.example .env
.\.venv\Scripts\python.exe -m retail_pulse --home runtime/offline demo
.\.venv\Scripts\python.exe -m retail_pulse --home runtime/offline serve --port 8001
```

Open http://127.0.0.1:8001/#overview. This reproducible starter uses clearly
labeled synthetic fixtures and makes no paid model calls. On macOS/Linux use
`.venv/bin/python` and `cp .env.example .env`. Never overwrite an existing `.env`.

The public repository contains all application code, tests, example contracts,
preparation scripts and demo documentation. Large downloaded datasets, runtime
databases, saved provider responses, local logs and credentials are excluded.
The real-footage hackathon walkthrough requires the separately prepared data;
it is not automatically recreated by the offline command. See
[public package setup](docs/PUBLIC_PACKAGE.md) and
[the recording script](docs/HACKATHON_RECORDING_SCRIPT.md).

Run checks with `.venv/Scripts/python.exe -m pytest -q`.

## Prepared real-data workspace

The current prepared workspace includes real public datasets, saved Meta Muse
and SAM responses, and an operations desk linking evidence review, sales intake,
scenario replenishment and evaluated demand planning. Start at
http://127.0.0.1:8001/#operations and follow [Start here](START_HERE.md).
Preserve the existing `.env`, data and runtime usage ledger. The older UI-only
upgrade instructions describe an earlier release, not this integrated build.

Retail Pulse is a Python research prototype that joins existing shelf imagery/video,
RFID/barcode observations, POS transactions and inventory records. It estimates
availability gaps, reconciles physical/recorded inventory, models stockout-censored
demand and produces human-reviewed replenishment recommendations.

It includes the two requested additions:

- **ML Health Steward (step 4):** deterministic Python diagnostics plus a read-only
  Muse agent that explains data quality, model drift, holdout error and safe next steps.
- **Business Insights Agent (step 6):** Muse chooses from approved read-only tools
  to answer questions about stockouts, demand, discrepancies, evidence and decisions.

## What is ready

| Component | Implemented behavior |
|---|---|
| Data ingestion | CSV/JSON/JSONL, timezone normalization, camera clock offsets, schema validation, stable-ID deduplication, quarantine |
| Meta perception | Native Meta Responses/Files API adapter; image/video extraction with JSON Schema and local semantic validation |
| SAM integration | SAM 3.1 requests, frame/object IDs, boxes and encoded masks retained; image box overlays |
| Temporal fusion | Availability interval union, conflicts/occlusions as unknown, recorded inventory movements, discrete count posterior, RFID lower bounds, verified counts |
| Intelligence | Stockout exposure, estimated unmet demand, count discrepancies, misplacement/damage evidence, candidate review cases |
| ML | Exposure-adjusted baseline and Poisson regression; chronological train/validation/test; selection on validation only |
| ML health | Freshness, coverage, low visibility, POS/availability contradictions, quarantine, drift PSI, holdout WAPE and minimum history |
| Decisions | Enumerated review intervals and case-pack/shelf-capacity constraints; approval gates, no inventory writes |
| User interface | Redesigned seven-page browser workspace, dark/light themes, smooth navigation, command palette, evidence video, charts, product drawer and agent interfaces |
| Service | FastAPI, CLI, local SQLite WAL database, OpenAPI docs; no separate database server or Node build required |
| Reliability | Unit/integration tests, mocked Meta request contracts, budget reservations, bounded tool loops, content-addressed caching |

**This is a runnable research prototype, not a production-certified retail system.**
Live Meta calls require your own credentials and permitted media. No real Meta
inference was executed when this package was built. Provider wiring is tested with
mock HTTP responses and follows the official documentation listed in
[docs/SOURCES.md](docs/SOURCES.md).

![Retail Pulse Interface 2.0 - synthetic demo](artifacts/ui-v2/overview-viewport.png)

## 1. Start in Anaconda Prompt on Windows

Extract the ZIP, open Anaconda Prompt, and change into the extracted repository:

```bat
cd "D:\Projects\retail-pulse"
conda env create -f environment.yml
conda activate retail-pulse
copy .env.example .env
python -m retail_pulse demo
python -m retail_pulse serve
```

Open `http://127.0.0.1:8000` in your browser. API documentation is at
`http://127.0.0.1:8000/docs`.

The demo creates a local `runtime/` folder. It does not require an API key and makes
**zero paid API requests**. The server stays in the terminal; stop it with Ctrl+C.

For an existing Python 3.11-3.13 environment:

```bat
python -m pip install -e ".[dev]"
copy .env.example .env
python -m retail_pulse demo
python -m retail_pulse serve
```

On macOS/Linux use `cp .env.example .env` instead of `copy`. The code and browser
are platform-neutral. Windows/Conda commands are provided as a convenience;
build-time execution was on Linux with Python 3.13, not on Windows.

### Demo scenes

The reproducible 56-day simulator has six products:

| SKU | Controlled scenario |
|---|---|
| A | Sells out early; a weekly count understates latent demand |
| B | Slow-moving comparison with sustained availability |
| C | Merchandise is moved to another location and later returned |
| D | Unexplained removal and a verified negative count variance |
| E | Unrecorded receiving and a verified positive count variance |
| F | Visible damage plus recurring camera occlusion |

A 28-second H.264 time-lapse illustrates the final week. An explicit time scale
maps video seconds to scenario time. Its numerical observations are generated
**fixture labels, not model-extracted observations**. The demo does not measure
Muse or SAM accuracy. Ground-truth demand is stored separately for evaluation and
is not exposed to agents or forecasting training.

Run `demo` only in an empty runtime. To create a separate simulation without
removing anything:

```bat
python -m retail_pulse --home runtime_seed_99 demo --seed 99
python -m retail_pulse --home runtime_seed_99 serve --port 8001
```

## 2. Enable live Muse and SAM

Edit `.env` locally; never put the API key in GitHub:

```dotenv
RETAIL_PULSE_MODE=meta
MODEL_API_KEY=YOUR_META_API_KEY
MUSE_MODEL=muse-spark-1.3
SAM_MODEL=sam-3.1
ALLOW_EXTERNAL_MEDIA=false
API_BUDGET_USD=20
```

First make a small explicit connectivity test:

```bat
python -m retail_pulse smoke-meta
```

Then try live text/tool reasoning over the synthetic numerical records:

```bat
python -m retail_pulse ask "Which products have hidden demand, and why?" --mode meta
python -m retail_pulse health --agent
```

Restart the server after editing `.env`. The Business Insights page lets you
choose **Live Muse** when the backend is configured. The health review button uses
live Muse when configured; otherwise it uses a clearly labeled deterministic demo.

To send approved footage, set `ALLOW_EXTERNAL_MEDIA=true`. Standard mode is the
default. Contributor-mode model IDs are blocked unless you explicitly enable
`ALLOW_CONTRIBUTOR_MODE=true`; review the provider's content-use terms first.

**Your $150 credit is not automatically spent or discovered by this program.**
The default local guard is $20. Change it deliberately. Costs are local estimates
based on reported tokens/configured frame prices; this is not a provider billing
cap. Ambiguous timeouts retain their reserved budget rather than assuming zero
cost. See [docs/META_INTEGRATION.md](docs/META_INTEGRATION.md).

## 3. Import your existing records

No employer connection, credentials, SQL table names or schema were invented.
The boundary is normalized exports. Keep real data in a different runtime from
the synthetic demo.

```bat
python -m retail_pulse --home runtime_real import --table products --file examples\products.csv
python -m retail_pulse --home runtime_real import --table transactions --file examples\transactions.csv
python -m retail_pulse --home runtime_real import --table rfid_reads --file examples\rfid_reads.csv
python -m retail_pulse --home runtime_real import --table barcode_scans --file examples\barcode_scans.csv
```

The examples are small schema examples, not enough history to train a forecast.
The package rejects naive timestamps unless `--timezone America/Denver` (or your
actual source timezone) is supplied. DST ambiguity is rejected, not guessed.
A positive `--clock-offset 30` means the source clock is 30 seconds fast.
UPCs and EPCs are strings; leading zeros are preserved.

See [docs/DATA_CONTRACTS.md](docs/DATA_CONTRACTS.md) for all required fields,
verified-count requirements, scan deduplication and observation semantics.
Machine-readable JSON Schemas are in `examples/schemas/`.

### Analyze authorized video or an image

The product catalog must first map the camera and zones. Example using the
sample catalog (`STORE_01`, camera `CAM_01`):

```bat
python -m retail_pulse --home runtime_real media --file "D:\ApprovedClips\shelf.mp4" --store STORE_01 --camera CAM_01 --start "2026-10-26T08:00:00-06:00" --sam-prompt "packaged products" --analyze
```

This command performs the entire requested handoff:

```text
Register source clip and timestamp
  -> SAM geometry (when a prompt is supplied)
  -> Muse structured numeric observations
  -> Schema + SKU/zone/time/bounds validation
  -> Separate observations table / raw response retained
  -> Reconciliation + demand + deterministic health + recommendations
  -> Muse ML Health Steward review
```

`--analyze` is explicit. Without it, `media` only registers the source.
Images are accepted via the same command. A snapshot supplies at most a one-second
observation; it does not establish availability for the rest of the week. Ordinary
clips have `--time-scale 1`; only use another value for a genuine timestamped
time-lapse with known timing.

Native video uploads are deleted after analysis when possible; requested expiry
is 24 hours if cleanup fails. Deletion is not a claim about all provider retention.
Do not send unapproved employee/customer media. Crop to approved shelf regions
before uploading; configure planogram ROIs for the cropped view.

## 4. Run the intelligence and agents

```bat
python -m retail_pulse run --store DEMO_01
python -m retail_pulse health --agent
python -m retail_pulse ask "Explain the shrink and swell discrepancies." --mode demo
python -m retail_pulse ask "Why was SKU C unavailable?" --mode meta
python -m retail_pulse evaluate
```

The `run` command explicitly evaluates/refits the forecasting architecture.
Neither agent can call that command, run arbitrary code/SQL, promote a model,
change thresholds, make purchases or update inventory.

For periodic health checks, start a local foreground monitor:

```bat
python -m retail_pulse watch --interval 300 --agent
```

It recomputes health every five minutes and requests a Muse interpretation only
when health categories change. It does not automatically retrain. The process
must remain running; stop with Ctrl+C. Use `--home runtime_real` before `watch`
for real data. Demo monitoring uses the simulator's `as_of` time intentionally.

## 5. Dashboard sections

1. **Operations overview:** known-availability coverage, stockout hours, estimated
   unmet units and prioritized recommendations.
2. **Visual evidence:** registered clips/images, timed observation log and source
   navigation. Verified synthetic audits are labeled as fixtures, not video proof.
3. **Inventory truth:** ledger quantities, physical estimate/range, verified
   discrepancies and unresolved counts.
4. **Demand intelligence:** daily availability, exposure-aware forecasts,
   chronological metrics and a separate synthetic latent-demand benchmark.
5. **ML health steward:** deterministic checks, blocking policy and agent review.
6. **Business insights agent:** read-only question answering with approved tools,
   retrieved metric values, evidence IDs and tool traces.
7. **Sources & ingestion:** uploads, normalized imports and explicit recomputation.

## 6. Architecture and repository

```text
src/retail_pulse/
  config.py         environment settings and explicit opt-ins
  schemas.py        data contracts and model-response validation
  db.py             SQLite WAL store, reports and job leases
  ingestion.py      normalized exports, timezone handling, quarantine
  demo.py           synthetic dataset and illustrative H.264 video
  meta_client.py    native Meta API, cost guard, retries and cache
  sam.py            SAM boxes/tracks; encoded masks retained
  perception.py     Muse extraction and validated observation persistence
  fusion.py         availability intervals and inventory count posterior
  demand.py         exposure model, Poisson ML, chronological evaluation
  health.py         deterministic ML/data quality diagnostics
  optimization.py   constrained advisory review/replenishment rules
  agents.py         ML Health Steward and Business Insights tool loops
  monitor.py        foreground periodic health checks
  pipeline.py       explicit analytics orchestration
  evaluation.py     isolated simulator evaluation
  api.py            FastAPI and local dashboard service
  cli.py            command-line entry points
  web/              browser UI; no external JS libraries or build step
```

More detail: [architecture](docs/ARCHITECTURE.md),
[Meta wiring](docs/META_INTEGRATION.md), [data contracts](docs/DATA_CONTRACTS.md),
[evaluation](docs/EVALUATION.md), [security](SECURITY.md),
[demo script](docs/DEMO_SCRIPT.md).

## 7. Tests and GitHub

```bat
python -m pytest -q
python -m compileall src
```

The included GitHub Actions workflow is configured to run tests on Windows and Ubuntu with Python 3.11; it has not been run on your repository. No live Meta requests or
secrets are required. Provider tests use explicit mock transports; they do not
establish real API performance. The build environment's test summary is in
`artifacts/VALIDATION.md`.

To publish after reviewing the files:

```bat
git init
git add .
git status
git commit -m "Initial Retail Pulse research prototype"
```

`runtime/`, `.env`, uploaded video, SQLite files and model binaries are ignored.
Review `git status` before committing. Do not use `git add -f` on private files.
The supplied license covers this repository's code, not Meta models or third-party
media/data. Source and sample data are synthetic; replace the example IDs locally.

## Explicit limits

- Existing cameras need sufficient coverage and resolution. Hidden units, UPC
  identity, payment status and intent are not established by segmentation alone.
- SAM masks are saved in the provider's encoding; this release overlays boxes and
  tracks, not decoded pixel masks. No exact mask-occupancy claim is made.
- No cross-camera person re-identification or theft-accusation feature is included.
- No live CCTV/NVR, Oracle, POS or RFID-vendor connector is claimed. Export ingestion
  is implemented; adapters should be added against your actual authorized systems.
- Weekly RFID supplies sparse anchors, not continuous item tracking. A barcode
  scan does not automatically change stock. An RFID absence never proves loss.
- The discrete count posterior has explicit simplifying assumptions. It is not a
  calibrated production warehouse digital twin. Recent verified audits are needed
  to classify count variances in this release.
- Forecasting is a defensible initial exposure model, not a claim of a novel
  forecasting algorithm. Substitution, price elasticity, seasonality beyond
  weekday/trend and exact foot traffic are not modeled.
- Conditional Poisson intervals omit perception and parameter uncertainty. Do not
  present them as fully calibrated uncertainty bounds.
- Replenishment enumerates fixed review periods for one store. It is not a global
  multi-store vehicle-routing or purchase optimization solver.
- Citation IDs are checked; this cannot guarantee every free-text LLM statement is
  correct. Numeric tool outputs and source evidence remain the review authority.
- The local shared-token gate is not production identity management. Use proper
  authentication, role-based access, encryption, retention and audit controls before
  deploying with real business/customer data.

## Demo informed by collected datasets

Install `python -m pip install -e ".[dev,data]"`, then run:

```powershell
python -m retail_pulse demo --datasets data/external
python -m retail_pulse serve
python -m retail_pulse ask "Which datasets were used and what is synthetic?"
```

Generation requires an empty runtime. To keep an existing demo, supply
`--home runtime/another-demo` before both the `demo` and `serve` subcommands.
The prepared default `runtime/` contains the generated dataset-informed demo.

All nine sources are profiled using bounded deterministic samples. FreshRetailNet
stockout frequency shapes fast-seller pressure; M5 supplies a relative daily shape;
Favorita scales its variation; transactions/stocks supplies a bounded inventory
scale. Source evaluation partitions are excluded from calibration. The five visual
sources supply decoded reference previews and measured media properties for agent
provenance, not operational observations. This does not train a perception model.

The six scenario SKUs share one simulated store, consistent identifiers, receipts,
sales, stock movements, RFID reads, audit counts and shelf intervals. Cross-source
relationships are artificial. All operational observations remain `demo_replay`;
latent demand is saved separately for synthetic evaluation and is not an agent tool.

`runtime/source_profile.json` records sampling, formulas, file hashes and limitations.
`runtime/source_samples/` contains real reference previews for local inspection.
`runtime/demo_inputs/` contains normalized synthetic inputs. Reports and model files
are in `runtime/reports/` and `runtime/models/`. The read-only `get_data_sources`
agent tool exposes profiles without granting file-system access. Offline answers
remain deterministic; live Muse inference has not been run or validated here.

## Real recorded camera demo

Run `python -m retail_pulse camera-demo --datasets data/external` after generating
the store demo. This prepares three 60-second H.264 excerpts from the public MERL
Shopping Dataset and a separate camera timeline. Open Visual evidence; real clips
are selected by default. Click Play this moment to seek; current events highlight.
The updated launcher serves at http://127.0.0.1:8001 to avoid the existing server.

VIDEO ANALYSIS entries are computed locally from decoded video frames using
full-frame differences at 5 samples/second (320x180 grayscale, Gaussian blur,
pixel change >20 and changed area >=1.5%). This is a simple motion detector,
not a trained action classifier. MERL LABEL entries come from the publisher's
MATLAB annotations, mapped from original 30 fps frame indices. Source and
method are shown for each event. Reports are saved as runtime/reports/camera_*.json.

These real clips do not depict the synthetic business ledger. No shelf quantity,
stockout, SKU identity, sale, theft or payment conclusion is generated from motion.
Camera observations stay out of operational inventory fusion and demand training.
Original capture dates are unknown; the UI uses clip-relative seconds. The epoch
timestamp in the evidence record is solely a seek anchor. The read-only agent
can retrieve the real camera timelines with get_camera_observations. Ask
"What does the real camera footage show?".

Source: https://www.merl.com/research/downloads/MERL_Shopping_Dataset
Copyright Mitsubishi Electric Research Laboratories, 2016; research and educational
use per the included README. Cite Singh et al., CVPR 2016. Retain original data
and documentation. This workflow performs no external uploads or paid inference.

## Live Muse and real source workspaces

The local `.env` now selects `runtime/real-data`, Meta mode, `muse-spark-1.3`,
and explicitly authorized media uploads. The credential stays in ignored `.env`;
never copy it into frontend code, screenshots, reports or `.env.example`.
The existing $20 local API budget guard remains enabled. It is an estimate,
not an authoritative provider billing limit. Muse is Meta inference, not OpenAI inference.

Launch `Start_Dataset_Demo.cmd` and open http://127.0.0.1:8001.
The source selector provides:

- `STOCK_STR_1010`: six original product IDs/descriptions from Retail Transactions
  and Stocks, original signed sales quantities, and latest reported stock intervals.
  Dates and open-ended intervals are shown. Different interval dates are not a
  synchronized physical census. Missing sales dates are not imputed as zero.
- `FRESH_0`: six complete 90-day series from FreshRetailNet's training file.
  Charts use original 06:00-22:00 hourly quantities and stock-status flags.
  Quantities are globally normalized, not raw unit counts. Original product IDs
  are retained; product names and on-hand inventory are not supplied.

No factual product or store joins are made between these sources. Real MERL clips
are attached as separate research footage; they do not verify these inventories.
No invented physical audits, RFID readings, stockouts or sales are introduced.
A model forecast or inferred demand is labeled as an estimate, not source data.
Count-based predictive intervals are withheld for normalized quantities.

All three real clips have actual Muse readings. `MUSE AI` timeline entries contain
model-produced timestamps, item descriptions, visible-count bounds when supportable,
confidence and limitations. `MERL LABEL` and `PIXEL MOTION` retain their distinct
provenance. Analyze clip with Muse uses the configured backend key, validates the
returned timeline, caches identical analysis, and requests uploaded-file deletion.
It does not add a grocery-camera count to a footwear stock ledger.

Business insights and ML Health Steward default to live Muse. Saved real responses
load on opening the page; new requests remain explicit. Monitoring recomputes source
health and can ask Muse to interpret it, without promoting models or writing orders.

For a new empty runtime, reproduce measurements with:
`python -m retail_pulse --home runtime/new-real prepare-real --datasets data/external`.
Raw selected records and source reports are preserved under the chosen runtime.
The earlier fully synthetic runtime remains in `runtime/` for regression demos.

## Expanded research demo (October 28)

Historical release notes below: the November count challenge supersedes the
original clip 420 acceptance. Its primary two-item reading conflicts with a
second one-item reading, so the current journey holds it for human review.
Four transfers remain accepted by the playback gates; all five operations
candidate cases require explicit review before a scenario action.

Open http://127.0.0.1:8001/#flow after launching `Start_Dataset_Demo.cmd`.

- **Product journey** plays actual paired RetailAction clips. Twenty-two clips were read by Muse Spark 1.3; five events pass the exact-count and 0.75 confidence gates, totaling six observed transfers of units. Clip `retailaction-000420` is a two-item example. Occluded, uncertain, partial-bound and touch observations remain visible but cannot alter the scenario count. Confidence is model-reported, not calibrated accuracy.
- Each filmed object is illustratively joined to a real M5 item identifier and an independent real retailer stock quantity. These are disclosed demo assignments, not recognized UPCs or measurements of the filmed store. Playback changes the scenario shelf/in-hand balance at the event timestamp. Whole-store stock changes only with the explicitly simulated checkout. Unmatched checkout means review, never a theft conclusion. Original source inventories and model labels stay unchanged.
- Refill advice uses the real-history forecast with disclosed two-day lead and one-unit safety assumptions. The three-hour empty-shelf estimate is conditional sales at risk. Video does not inflate the sales forecast or prove lost purchases.
- **Data library** indexes 125,497,040 Favorita sales rows, 59,181,090 M5 daily sales values, 4,500,000 FreshRetailNet training rows, 350,000 separate evaluation rows, 125,751 retailer sales rows and 284,755 retailer stock intervals. Dataset/store/product filtering and pagination expose original quantities and dates. M5 overlapping validation files are not duplicated. Normalized FreshRetailNet quantities are never labeled physical unit counts. Stock interval sums are not daily on-hand inventory.
- Main source workspaces include 2,010 retailer products and all 74 available FreshRetailNet series for store 0. All stores remain searchable in the library. Retail stock uses the latest source interval per store/product. Different items' stock dates can differ; source counts are not verified physical audits.
- All five visual collections are inventoried in the library. Real SKU110K, AgriShelf and cosmetics sample images have actual saved Muse shelf readings. RetailAction and MERL clips remain playable. Duplicate views/encodings are not independent customer events.
- **Model experiments** uses 200 original M5 CA_1 food series (388,200 daily values). Muse chose three bounded Poisson regularization candidates. Python trained on 73,000 rows, chose the winner on 5,600 validation rows, then evaluated 5,600 held-out test rows. The selected alpha 0.01 candidate had test WAPE 80.31%, versus 82.86% for the 28-day mean and 105.09% for seasonal naive. These errors remain high; no production promotion or universal improvement claim is made. Seven-day forecasts are recursive and are not evaluated by the one-day test metric. The locally available regression library is used; the operating system blocked loading the optional boosted-tree extension.
- Business insights can retrieve the shared journey, full source coverage and tuning experiment through bounded read-only tools. Its saved live explanation distinguishes source measurements, observed transfers and simulated mappings.

The key stays in ignored `.env`. The existing `runtime/real-data` usage ledger is retained. `API_BUDGET_USD=60` is also clamped to $60 in code; the configured $2 reservation covers the documented Spark context and output limits before each call. Unknown charges keep their reservations; repeated playback and data browsing do not make paid calls. Prices and usage are local estimates; the provider dashboard is authoritative. Never reset the usage database to bypass the guard. [Meta model specification and pricing](https://dev.meta.ai/models/muse-spark).

Install data dependencies with `.venv\Scripts\python.exe -m pip install -e ".[data]"` if needed. To reproduce the expansion explicitly, run `.venv\Scripts\python.exe scripts\prepare_expanded_demo.py`. This command can call Muse for missing analyses; saved analyses and the usage ledger are reused. To rebuild only the inventory scenario without calling Muse, run `.venv\Scripts\python.exe scripts\build_product_journey.py`.

## Retail operations expansion (November 3)

- **Operations desk:** durable count review, simulated checkout, backroom refill,
  operator verification and before/after audit. Revision and event identifiers
  prevent stale changes and duplicate deductions. Source inventories stay intact.
- **Real sales intake:** 60 prepared historical STR-1010 records use the same
  validated intake as the POS event contract. Shadow stock creates supplier
  reviews while missing verified balances and lead times withhold order amounts.
  No commercial merchant feed is connected. See [POS integration](docs/POS_INTEGRATION.md).
- **Perception challenge:** real SAM bottle geometry for clip 85 overlays the
  right camera view. Its 408 frame-box records and 16 tracks include shelf bottles,
  not 16 purchases. Clips 42 and 420 returned zero detections for the tested prompts.
- **Weekly planning benchmark:** Muse proposed bounded candidates on 74 real
  FreshRetailNet series. Frozen seven-day seasonal forecasts scored 17.98% WAPE
  against 23.59% for mean28 on a separate 518-row publisher evaluation. The
  nominal 80% bands covered 86.49% of series in that week. These normalized
  quantities cannot become physical orders; one store/week is not a generalization
  guarantee. The older M5 one-day experiment remains separately available.
- **Muse operations brief:** an actual saved Spark 1.3 response retrieves summary,
  operations, independent video review and the weekly benchmark, with inspectable
  evidence and numeric metrics. New briefs are explicit paid actions; replay is free.

Rehearse with [the three-minute demo guide](docs/HACKATHON_DEMO.md). The
[hackathon strategy](docs/HACKATHON_STRATEGY.md) maps demonstrated behavior to
the official criteria without claiming measured customer impact.
