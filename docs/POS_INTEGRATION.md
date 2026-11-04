# Sales events and the operations shadow ledger

The Operations desk accepts local sales events through a validated HTTP contract
and demonstrates them with real historical source records. It connects reporting,
shadow inventory, supplier-review exceptions and the Muse operations brief.
**No live merchant/POS connector is configured.** This document describes the
implemented contract and the remaining work for a retailer integration.

## Start and inspect

Start the prepared environment as described in [Start here](../START_HERE.md),
then open `http://127.0.0.1:8001/#operations`.

| Endpoint | Purpose |
|---|---|
| `GET /api/catalog?store_id=STOCK_STR_1010` | Inspect registered source products before choosing a SKU |
| `POST /api/pos-events` | Receive one sale, return or receipt |
| `GET /api/operations` | Read cases, sales, shadow inventory, supplier reviews, plan and action audit |
| `POST /api/operations/replay-sale` | Receive the next prepared archive record; no provider inference |
| `GET /api/operations/brief` | Read the latest saved operations brief, if present |
| `POST /api/operations/brief` | Request a new tool-grounded Muse brief; consumes API credit in Meta mode |

The local service defaults to `127.0.0.1`. If `RETAIL_PULSE_API_TOKEN` is configured,
protected endpoints require `Authorization: Bearer <local API token>`. This local
token is distinct from the Meta model credential; never send the model key in a
POS event. The current shared-token/local-host protections are not enterprise
authentication or a production deployment design.

## Event contract

Send `Content-Type: application/json`. Every field below is required; additional
fields are rejected.

| Field | Accepted value | Meaning |
|---|---|---|
| `event_id` | String, 8–100 characters | Stable source event/line identifier, unique across this runtime |
| `store_id` | String, 1–64 characters | Registered store key |
| `sku` | String, 1–100 characters | Product registered for that store |
| `occurred_at` | ISO timestamp with UTC offset | Original event time; timezone-naive values are rejected |
| `kind` | `sale`, `return` or `receipt` | Sale subtracts stock; return and receipt add stock |
| `quantity` | Finite number, greater than 0 and at most 10,000 | Source quantity; sign is determined by `kind` |

Example request body only; replace `REGISTERED_SKU` with a catalog SKU before
using it. This example has not been sent to the running application.

```json
{
  "event_id": "merchant-store1010-ticket42-line1",
  "store_id": "STOCK_STR_1010",
  "sku": "REGISTERED_SKU",
  "occurred_at": "2026-11-02T14:30:00-07:00",
  "kind": "sale",
  "quantity": 2
}
```

The receiver adds `received_at`, `origin: "connector_event"`, `source: null` and
`duplicate`. The origin describes which intake path was used; it does not prove
that an authenticated commercial merchant generated the event. Identifiers
should include provider/store/transaction/line scope so unrelated events cannot
collide. Reserve `archive-retail-...` identifiers for the built-in replay.

### Retry and error behavior

- A new valid event returns HTTP 200 with `duplicate: false` and is stored once.
- Repeating the same `event_id` and unchanged normalized content returns the
  original event with `duplicate: true`; its original receipt time is preserved.
- Reusing an identifier with different content returns **409 Conflict**. It does
  not overwrite the first event. Retry an uncertain delivery with the same ID and
  unchanged body, rather than inventing a fresh ID.
- An unknown store/product or timezone-naive timestamp returns **400**. Field
  validation failures, such as invalid kinds, extra fields, nonpositive/oversized
  quantities or nonfinite numbers, return **422**.
- Missing/incorrect configured bearer credentials return **401**. Host/origin
  restrictions can reject requests with **403**.

The event endpoint does not implement transaction voids, correction links,
currency/revenue, prices, tenders, customer identity, stock adjustments or
commercial order submission. A return is a new business event, not an instruction
to rewrite an earlier sale. Vendor-specific correction semantics require a
separate, explicit mapping.

## Historical replay semantics

The prepared demo selects 60 positive sales rows for source store `STR-1010`
from Retail Transactions and Stocks, joined to products with a positive latest
stock interval. It maps the source store to the registered local key
`STOCK_STR_1010`. The UI receives five rows per **Replay 5 real sales** click.

- `origin` is `archive_replay`, and the original source row/date/product/quantity
  remain in the saved source metadata.
- The source provides a calendar date, not a checkout timestamp. Replay uses
  **12:00 UTC as an explicit placeholder**; it does not claim midday sales or
  convert the archive into current events.
- Records are prepared from the newest source dates first. This is a reporting
  demonstration, not a chronological re-creation of the store's trading day.
- Receipt time records when this application accepted the row. The UI polls for
  state updates approximately every five seconds; no production latency or
  streaming throughput guarantee has been measured.
- The opening stock is from a separate latest interval. Applying historical
  sales to it creates a **shadow scenario**, not a verified historical balance.
- Stable source-row event IDs prevent duplicate deductions. After all prepared
  rows are received, replay reports completion and adds no fabricated rows.

## What downstream components do

**Reporting:** the desk displays received event count, recorded sale quantity,
original source date, receipt time, source product and replay/connector origin.
The sales-quantity total includes sales; return and receipt totals are retained
separately in shadow inventory.

**Shadow inventory:** per store/SKU, the desk computes opening stock minus sales
plus returns and receipts. If no opening balance is available, projected stock
remains unknown. Negative projections remain visible as discrepancies; they do
not establish theft or a real physical shortage. This ledger is separate from
the original transaction data and from the five video review scenarios.

**Supply chain:** projected stock at or below one unit triggers a supplier-review
exception. One unit is an explicit demo threshold. `order_units` stays null
because verified current counts and lead times are missing. No purchase order,
supplier message or warehouse transfer is sent.

**Agents and planning:** the Muse brief can retrieve operations, visual grounding
and forecast-benchmark context to explain priorities and limits. Event receipt
does not automatically retrain a demand model or raise demand because a pickup
occurred. The saved seven-day FreshRetailNet benchmark is a separate evaluation
on normalized quantities, which cannot be converted to physical order units.
The M5 experiment uses recorded-unit history and remains distinct.

## Human action contract

`POST /api/operations/cases/{case_id}` records local scenario actions. It requires
an `action_id`, current `expected_revision`, an allowed `action`, optional integer
`quantity` (0–100), and an optional `note` (at most 500 characters). Actions are
`approve_count`, `reject`, `match_checkout`, `restock`, `verify_shelf` and
`restart_demo`; each has its own state and quantity checks.

Disputed/corrected counts require a review note. Checkout cannot exceed reviewed
items still in hand; refill cannot exceed backroom stock or the scenario shelf
target; verification must match the projected shelf count. Shelf + backroom +
in-hand must equal whole-store stock after every action. Reused action IDs are
idempotent for unchanged content; conflicting IDs and stale revisions return
409. Before/after snapshots persist, and a scenario restart keeps the audit.
These records are operator reports within a demo, not new camera proof that a
physical action happened.

## Requirements for a retailer pilot

A real integration still needs a vendor connector and store/SKU/unit mapping,
authenticated signed delivery, retailer-authorized source access, aligned opening
counts, timestamp/timezone quality checks, returns/voids/corrections semantics,
retry/dead-letter handling, tenant separation and monitoring. Demand planning
also needs current supplier lead times and physical-unit mapping before creating
order quantities. Validate these on a retailer's permitted data before describing
the system as a live control tower.

Keep the $60 model-usage guard and its existing ledger. Receiving sales and
replaying archive records make no Meta calls; requesting a new brief or new media
analysis does. Source files and provider credentials remain local unless a
separately authorized integration sends them elsewhere.
