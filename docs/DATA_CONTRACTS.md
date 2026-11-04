# Data contracts

All inputs accept JSONL or JSON arrays. CSV is convenient for normalized export
records; `roi` uses a JSON array inside a quoted CSV cell. Exact schemas are in
`examples/schemas/`. Unknown fields are rejected rather than silently ignored.

## products

One row per store/SKU: `store_id`, `sku`, `upc`, `title`, `zone_id`, `camera_id`,
`shelf_capacity`, `case_pack`, `lead_days`, `roi`.
`roi=[x1,y1,x2,y2]` is normalized to [0,1] in the registered camera image.
Store IDs contain only letters, digits, underscore or hyphen. UPC is an 8-14 digit
string. No conversion to integer. Distinguish internal SKU IDs from UPCs.

The prototype maps one assigned zone/camera per store/SKU. Multiple facings across
several cameras require an extension to an explicit location mapping table. Do not
represent an alternate display as a missing item without verifying other locations.

## transactions

`event_id`, `store_id`, `sku`, `at`, `kind`, `quantity`, optional `source` and
`business_ref`. Kinds: `opening`, `receipt`, `sale`, `return`, `disposal`,
`adjustment`. Quantity is nonnegative except for signed adjustments.

Only one opening balance is accepted per store/SKU. Sales/disposal subtract;
opening/receipt/return add; adjustment is signed. Negative sales quantities are
not returns: record a separate `return`. Internal shelf/backroom transfers do not
change store-level quantity and should be represented as observations, not receipts.

Use namespaced stable source IDs (for example `POS:store:receipt:line`). The tool
cannot know that two different IDs from separate systems are duplicates. Deduping
only on timestamps/quantity is unsafe and deliberately not done.

## rfid_reads

`read_id`, `scan_id`, `epc`, `store_id`, `sku`, `at`, optional `zone_id`.
Each distinct EPC per scan contributes at most once. Your export adapter must map
EPC to the appropriate item/SKU; this package does not guess that mapping.

Reads establish presence at a scan, not absence of unread merchandise. By default
RFID supplies a lower bound. The optional detection-probability model is justified
only for a calibrated reader/coverage experiment, not a universal 0.9 assumption.
Scan windows must be sufficiently short or otherwise reconciled for intervening
sales/movements. Do not pool unrelated visits under one scan ID.

## barcode_scans

`scan_id`, `store_id`, `sku`, `upc`, `zone_id`, `at`, optional `action`.
The SKU/UPC mapping is checked. A scan is evidence, not a stock transaction. The
subsequent successful receiving/sale/movement transaction must be ingested separately.

## evidence

Created automatically by the `media` command. Fields: `evidence_id`, `path`,
`media_type`, `store_id`, `camera_id`, `start_at`, `duration_seconds`,
`seconds_to_world`, `sha256`, `synthetic`. Paths are relative to the runtime.
The media-serving API only serves registered image/video files inside `runtime/media`.

A `fixture` is a synthetic/audit record and is not a playable clip. Media uploads
are content-addressed with their source start/camera and copied to controlled
filenames. Existing footage must be authorized before sending to Meta.

## observations

`observation_id`, `store_id`, `sku`, `zone_id`, `at`, `end_at`, `kind`,
`availability`, `count_min`, `count_max`, `count_scope`, `confidence`, `visibility`,
`evidence_id`, `origin`, optional `note`.

- Event kinds: shelf_state, removal, restock, misplacement, damage, count.
- Only shelf_state may establish available/unavailable intervals. Other events
  must use availability=unknown.
- Count bounds are both null or both nonnegative integers, with min <= max.
- Scope is visible, shelf or whole_store_verified. Muse may NEVER mark its own
  image-derived count as whole_store_verified.
- A verified count must be a separate authorized human/system audit, not merely a
  set of RFID detections or a visible front-row count.
- Origin is muse, manual or demo_replay. Synthetic fixtures use demo_replay, not muse.
- Confidence/visibility are threshold inputs, not calibrated correctness probabilities.
- End must be strictly later than start and both must carry timezones.

## Minimum history

Inventory evidence can be ingested immediately. Forecasting currently needs at
least 28 days plus enough positive-exposure observations to train and evaluate.
Insufficient history blocks forecasting/order recommendations rather than
manufacturing a model. Small sample sizes also limit drift/error interpretation.

## Timing for stockouts

Two snapshots at 08:00 and 16:00 cannot establish the exact stockout time between
them. This prototype credits only explicit observed intervals. Supply sufficiently
dense timestamped images or contiguous clip coverage. Unknown time is reported
separately. Do not hand-label an entire gap as unavailable solely because the
last frame was empty.

## Privacy and retention

No real employee/customer identifiers are required. Use product zones and events.
The code does not recognize faces, infer identity or attribute intent. Retention,
permissions and lawful access depend on your deployment; synthetic media is the
safe default for a public repository and demo.
