# Start Retail Pulse

Retail Pulse connects camera evidence, recorded sales, inventory review and
demand planning for retail operations teams. This workspace contains prepared
real datasets, saved Meta model responses and an interactive research demo.

## Open the prepared demo

Double-click **`Start_Dataset_Demo.cmd`**, or run this from the project folder in
PowerShell:

```powershell
.\.venv\Scripts\python.exe -m retail_pulse serve --port 8001
```

Open **http://127.0.0.1:8001/#operations**. If the server is already running, open
the page directly. Stop a server you started with Ctrl+C.

Keep the existing `.env`, `runtime/real-data/`, `data/` and `.venv/`. The prepared
workspace's environment selects the real-data runtime and keeps the API key on
the server. Do not replace it with `.env.example` or regenerate the older
synthetic demo to start this version. The synthetic `demo` command remains a
separate research fixture; it is not the current hackathon walkthrough.

## Follow one operating decision

1. **Operations desk:** play the real footage for `retailaction-000085`. Its SAM
   overlay contains actual bottle detections; the Muse reading proposes a
   one-unit take. Boxes include shelf objects and are not purchase counts.
2. **Resolve uncertainty:** open `retailaction-000420`. Two Muse passes report
   different counts, so the proposal stays in human review with no applied
   inventory movement. The second pass uses the same model, not ground truth.
3. **Complete a scenario:** return to clip 85, review its count, match a simulated
   checkout, report a scenario refill and verify the displayed shelf count with a
   note. The balances and action history persist. Restarting the scenario keeps
   its audit history.
4. **Replay sales:** choose **Replay 5 real sales**. The desk receives historical
   source rows, updates a shadow inventory and shows supplier-review exceptions.
   Original dates and receipt times remain separate. No live merchant feed is
   connected and no purchase order is sent.
5. **Model experiments:** inspect the seven-day FreshRetailNet evaluation. The
   selected seasonal baseline has 17.98% WAPE versus 23.59% for the trailing-28-day
   mean on 74 series. Quantities are normalized, so these forecasts cannot become
   physical-unit orders. The separate M5 experiment shows bounded Muse-assisted
   tuning on recorded unit sales.

The Data library and Product journey pages retain deeper source history, original
video timestamps and mapping disclosures. The Operations desk's work planner
compares priorities under a time budget; its sales-at-risk calculation is a
conditional scenario, not measured recovered sales.

## Real evidence, explicit scenario joins

Videos, source sales, product records and stock records are real. The link from a
video product to an M5 SKU and an independent stock record is illustrative; it is
not recognized UPC identity or the filmed store's own POS. Opening backroom
stock, checkout and operator confirmations are explicit demo actions. Publisher
records remain unchanged.

SAM returned no detections for clips 42 and 420 with the tested prompts. Clip 85
has 408 frame-box records across 16 tracks. Neither track totals nor repeated
Muse agreement establish an independently verified transferred count.

## API usage and the $60 guard

Browsing pages, playing clips, replaying historical sales and using saved model
results do not request new Meta inference. **Ask Muse for an operations brief**,
other live agent actions and new media analysis make paid requests. They use the
existing server-side credential and persisted local usage/reservation ledger.

Keep `API_BUDGET_USD=60` for this user's authorized total limit, and preserve the
runtime ledger when restarting. Read the current usage display rather than a
hardcoded balance. This guard tracks the application's estimates; it does not
reconcile provider billing or other applications using the credential.

## Read next

- [Three-minute demo](docs/HACKATHON_DEMO.md): a complete evidence-to-action story.
- [Hackathon strategy](docs/HACKATHON_STRATEGY.md): official criteria, deadline,
  evidence register and remaining validation needs.
- [POS integration](docs/POS_INTEGRATION.md): accepted event contract, duplicate
  protection, replay semantics and production gaps.
- [Architecture](docs/ARCHITECTURE.md) and [data contracts](docs/DATA_CONTRACTS.md):
  model, ledger and source boundaries.
- [Meta integration](docs/META_INTEGRATION.md): provider configuration and media
  controls. Never publish `.env` or the API key.

Before recording, run the current demo checks: video playback and boxes on clip
85, held review on clip 420, a saved action sequence, sales replay, the forecast
report and the current cost display. This is a local research prototype, with no
production POS/NVR connector or independently measured retail business outcome.
