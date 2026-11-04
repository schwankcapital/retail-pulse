# Retail Pulse: hackathon positioning and proof

Research checked 2026-11-02. This is a preparation document, not a submission or
an assertion that the project will win. The final recording must match the
verified build and the accepted-participant portal's current requirements.

## The product story

**Retail Pulse turns fragmented retail evidence into a reviewable operating
decision: what changed, what should the store do next, and what should supply
chain and demand planning learn from it?**

The intended customer is a retail company. The first workflow serves a store
manager; regional operations, replenishment and demand planners consume the same
evidence and confirmed sales. The problem hypothesis is that teams must reconcile
camera observations, sales and stock records before acting. A shelf can be empty
while merchandise remains in a shopper's hand or elsewhere in the store. Sales
alone also understate demand when products were unavailable. A useful assistant
must preserve these differences instead of turning every removal into a sale.

The proposed value is a shorter path from evidence to a justified action and a
clearer handoff across store operations and planning. This prototype has not
measured customer adoption, labor savings, revenue lift or inventory accuracy in
a deployed retail business. Describe those as pilot questions, not results.

For **Build for Your World**, explain the retail problem and why the builder chose
it. Add a firsthand experience only if it is true; no personal retail history or
customer interview is established by this repository. The theme explicitly
invites practical domain problems that free time and mental space. [Meta event
page](https://dev.meta.ai/events/global-hackathon)

## What makes the implementation distinctive

1. **Video is the start of a business workflow.** Muse reads a real public retail
   clip. A validated count can move units from shelf to in-hand; a separate
   checkout event changes whole-store inventory. Uncertainty remains visible.
2. **Different models do different jobs.** Muse interprets actions and proposes
   bounded experiments; SAM supplies visual localization when it returns usable
   geometry; code maintains the ledger and calculates planning quantities.
3. **The assistant can explain its basis.** Real source records, original clip
   timestamps, saved provider responses and explicit illustrative joins make
   decisions inspectable. A response trace proves a call occurred, not that the
   model's answer is correct.
4. **Forecast proposals face evidence.** Muse chooses from a constrained tuning
   space. Chronological evaluation compares candidates with simple baselines;
   the assistant does not deploy arbitrary code or automatically promote a model.
5. **The operations desk connects departments.** Received sales, freshness
   signals, replenishment tasks and demand experiments share an auditable context.
   A replay of historical records demonstrates event handling; it does not
   establish a live connection to a retailer.

## Official judging alignment

The organizer's published final-project rubric is below. The equal weighting of
idea and skill on Meta's homepage refers to **applications**, not final projects.
[Official rules](https://cerebralvalley.ai/e/meta-ai-developer-hackathon/waiver)

| Final-project criterion | Weight | Strongest evidence to show |
|---|---:|---|
| Impact | 30% | One retail workflow with a named user, next action and handoff to replenishment/planning; honest pilot measures |
| Use of Meta AI Tooling | 25% | Actual Muse action/count reasoning and a held count disagreement; actual SAM bottle localization; structured outputs, grounded tool use and bounded model-tuning proposals |
| Technical Depth & Execution | 20% | Conservation of stock, duplicate protection, uncertainty/review gates, source provenance, chronological evaluation and durable event handling |
| Demo | 25% | One uninterrupted evidence-to-action sequence, a clear failure case, legible model results and a working replay path |

Indie is for individual builders/students and teams of up to four; one designated
representative submits and identifies teammates. The homepage characterizes the
track around originality, ambition and a working result. [Official
rules](https://cerebralvalley.ai/e/meta-ai-developer-hackathon/waiver), [Meta event
page](https://dev.meta.ai/events/global-hackathon)

## Capability and evidence register

The following capabilities are implemented in the current local build. Run the
current tests and demo checks before recording; implementation is not a claim of
production readiness or independent perception accuracy.

Current build verification: **144 automated tests passed**. Browser verification
completed clip 85 with a reviewed one-unit take, one-unit simulated checkout,
three-unit refill and three-unit shelf verification; the case reached `VERIFIED`
with conserved balances. Six real archive sales rows were received, totaling six
units and producing three shadow-stock supplier-review exceptions. The new
74-series forecast panel rendered. These are prototype checks, not measured
retailer outcomes; replay totals will change with further use. A live Muse Spark
1.3 operations brief also completed, retrieving `get_summary`, `get_operations`,
`get_visual_grounding` and `get_forecast_benchmark`. Its saved interpretation and
25 referenced numeric metrics are inspectable without another paid call.

| Capability | Current implementation and saved evidence | Limit |
|---|---|---|
| Real video understanding | Saved Muse Spark 1.3 responses for 22 paired RetailAction clips; 5 candidate takes totaling 6 inferred units; 3 MERL clips with 44 observations | Candidate totals are not a measured accuracy score. Publisher action labels do not establish count ground truth. |
| Traceable product journey and count challenge | Primary clip 420 reading says 2; a second Muse pass says 1. Operations desk holds the case for human review before movement. Five cases support shelf/in-hand/backroom/store accounting. | Repeated passes of the same model are not independent ground truth. M5 SKU and stock records come from independent datasets; no recognized UPC or matching filmed-store POS. |
| Broader visual evidence | Actual SKU110K, AgriShelf and cosmetics images with saved Muse readings | Some outputs are broad count bounds; no calibrated shelf-count benchmark is established. |
| Real sales and inventory context | RetailTransactionsStocks, FreshRetailNet, Walmart M5 and Favorita; source identity and history remain inspectable | These are separate businesses and time periods. FreshRetailNet normalized quantities are not physical item counts. |
| Muse-assisted demand experiments | Saved Muse plans and constrained evaluation; a separate rolling one-day M5 experiment across 200 series and a seven-day FreshRetailNet benchmark across 74 series | A seasonal baseline wins the FreshRetailNet selection. Muse proposes; code scores. No automatic production promotion. |
| Evidence-grounded business reasoning | Read-only tools expose source metrics, operations state, grounding, forecasts and research context; an explicit operations-brief request uses them | Citation checks do not guarantee every sentence is correct; a new brief costs API credit. No autonomous purchasing. |
| API cost control | Server-side key, persisted usage/reservations and a local $60 guard | Display the current application ledger; it is not a provider billing reconciliation. Saved result replay is separate from a new paid call. |
| SAM localization | Clip 85 has 408 frame-box records across 16 tracks; frame-aligned boxes appear in the paired player. Tested prompts on clips 42 and 420 returned no detections. | Tracks include shelf bottles, not just moved items. No localization accuracy, transfer-count validation or decoded pixel-mask claim. |
| Human action completion | Operations desk persists count review → simulated checkout → backroom refill → operator verification; action IDs, revision guards and before/after audit protect state. A time-budget what-if prioritizes tasks. | All physical actions and backroom stock are explicit scenarios; an operator click does not establish a real refill. Conditional sales-at-risk is not recovered revenue. |
| Sales reporting and supply-chain handoff | 60 archived STR-1010 sales rows; original dates and receipt times; a validated event endpoint; shadow inventory and supplier-review exceptions | Latest opening stock intervals and old sales are not a historical reconciliation. Purchase quantities are withheld when stock/lead-time evidence is missing. No merchant feed is connected. |

The indexed tabular collection contains approximately **189.9 million
heterogeneous records/daily values**, including wide M5 series expanded for this
count. This is a coverage figure, not the number of examples used in one model or
one retailer's connected inventory. Lead the demo with the useful decision, then
show the data breadth as supporting evidence.

### What the new forecasting result supports

The FreshRetailNet benchmark uses 74 series from one store, with 6,660 daily
training-source rows covering 2024-03-28 through 2024-06-25. Candidate selection
uses two fixed forecast origins, residual calibration uses two later windows,
and the separate publisher evaluation file contributes 518 rows for June 26–July
2. The seven-day forecast does not feed intermediate actual sales back into its
prediction.

The selected `seasonal7` baseline has **17.982% seven-day WAPE**, compared with
**23.588%** for the trailing-28-day mean. Nominal 80% seven-day intervals cover
**86.486%** of the 74 evaluated series. This is a measured comparison on one
held-out week; WAPE is an error metric, not "82% accuracy." Coverage is empirical
and is not guaranteed under product/time dependence. The evaluation has now been
inspected, so further tuning needs a new holdout for independent confirmation.

All FreshRetailNet amounts are publisher-normalized. They cannot become physical
supplier order quantities. The M5 experiment and its recorded-unit forecasts are
separate evidence. Camera pickups do not automatically inflate either model's
demand forecast; the observation changes shelf context and review priorities.

## Priorities before submission

1. **Rehearse the implemented operating loop.** Clip 85 → reviewed Muse count →
   explicit checkout → refill → verified scenario count → persisted audit. Show
   the held count disagreement on clip 420 as a core capability.
2. **Show the retail-company handoff.** Replay original sales records, distinguish
   source time from receipt time, and explain shadow stock and withheld supplier
   quantities. Add a live retailer connector only when one actually exists.
3. **Use the seven-day result precisely.** Show the selected baseline, separate
   evaluation period, comparison and empirical interval coverage. Preserve the
   original evaluated report and keep the older one-day M5 result distinct.
4. **Show both usable and empty visual output.** Clip 85 supplies actual SAM
   geometry; clips 42 and 420 demonstrate truthful empty output. Track totals are
   not transferred-product counts.
5. **Remove presentation friction.** Use the updated start instructions and one
   Operations desk entry point, rehearse reset/replay, and record the working
   result with the original sources, joins and saved/live distinction legible.
6. **Add a small independent perception audit when feasible.** Have a human label
   transferred counts and uncertain events in held-out clips; report sample size,
   errors and abstentions. Existing candidate-event totals are not a substitute.

## Claims the evidence does not support

- Theft detection, intent inference, or automatic accusation from an unmatched
  removal. Unresolved merchandise movement is a review case.
- A dollar saving, revenue improvement, production forecasting advantage, live
  retail deployment or customer validation that has not been measured.
- Exact package identification across unrelated datasets, continuous multi-camera
  person tracking or automatic reconstruction of the retailer's full inventory.
- "Trained on 190 million transactions," a causal lost-sales estimate, or proof
  that Muse's self-reported confidence is calibrated.
- SAM boxes as proof of the transferred count or a completed sale.

Useful pilot measures are time to resolve an evidence case, manually verified
count error and abstention rate, duplicate-sales errors, task completion time,
stockout exposure, seven-day baseline-relative forecast error, interval coverage,
and cost per reviewed case. These are proposed measures, not achieved results.

## Deadline and submission readiness

- **Submission deadline:** November 4, 2026, 9:00 PM Eastern / 7:00 PM Denver
  (MST). Judging is listed for November 4–8 and finals/winners for November 9.
  Meta states that dates can change. [Meta event
  page](https://dev.meta.ai/events/global-hackathon)
- **Submission destination:** [Cerebral Valley project
  portal](https://cerebralvalley.ai/e/meta-ai-developer-hackathon/hackathon/submit),
  linked directly in the [official
  rules](https://cerebralvalley.ai/e/meta-ai-developer-hackathon/waiver).
- The portal redirected to sign-in during this audit. Exact upload fields, video
  duration, repository visibility and deployment requirements were not verified.
  The three-minute script is a rehearsal recommendation, not an official limit.
- Prepare a working-demo recording, concise project description, reproducible
  start instructions, model/evidence table, test results, source/license inventory
  and limitations. This is a recommended preparation package, not a claim that
  every item is mandatory.
- Review distribution permissions for third-party datasets and clips before a
  public release. The submission rules require rights in submitted materials;
  public availability alone does not establish redistribution permission.
  [Official rules](https://cerebralvalley.ai/e/meta-ai-developer-hackathon/waiver)
- No agreement was accepted, account signed into, repository published or
  competition submission sent during this audit.
