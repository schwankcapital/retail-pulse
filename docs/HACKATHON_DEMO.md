# Retail Pulse: three-minute retail operations demo

For the detailed recording plan, exact click sequence and timed voiceover, use
[the three-minute recording script](HACKATHON_RECORDING_SCRIPT.md).

**One-line pitch:** Retail Pulse connects what a camera observes, what a retailer
actually sold and what the team should do next, with evidence at every handoff.

Three minutes is a rehearsal recommendation. The official submission portal's
video limit was not accessible without sign-in; verify it before exporting.
[Submission portal](https://cerebralvalley.ai/e/meta-ai-developer-hackathon/hackathon/submit)

## Rehearsal setup

- Follow [Start here](../START_HERE.md) and open
  `http://127.0.0.1:8001/#operations`. Start with `retailaction-000085`, which has
  actual SAM detections. Clip 420 is the deliberate count-disagreement example.
- Run the demo checks on the current build before recording. Confirm clip
  playback, overlay alignment, case actions, persistence, sales replay, forecast
  values and current usage. No provider request is required for these checks.
- Use **Restart this scenario** to prepare a repeatable case; the audit history
  remains. Restarting a case does not erase sales replay. The prepared replay has
  60 rows and will stop when exhausted rather than manufacture new sales.
- Keep the source/join disclosure visible: footage, source sales and stock are
  real; product mapping, backroom stock, checkout and physical refill are scenario
  assumptions/actions. Replaying saved actual model output is not a new inference.
- Preserve the $60 local guard and existing ledger. A new Muse operations brief
  consumes API credit; reuse a saved real response if available and label it.

## Narration and screen sequence

| Time | Screen/action | Suggested narration |
|---|---|---|
| 0:00–0:20 | Operations desk | “Retail teams see sales in one place, stock in another, and camera evidence somewhere else. Retail Pulse connects them so a store manager can act and supply-chain and demand teams can understand why. Here's one decision, from real footage to an auditable action.” |
| 0:20–0:45 | Play clip 85 with actual SAM boxes and the Muse reading | “Muse reads this public retail clip and proposes a one-unit take. SAM localizes bottles so we can inspect the visual evidence. These are saved real model results. The boxes include objects still on the shelf: they are not sales counts.” |
| 0:45–1:05 | Switch to clip 420; show first count 2, second count 1, pending review | “This second example is more revealing. Two passes of the same Muse model disagree about the count. The system holds the proposal for a person to review; no inventory movement is applied. The disagreement is evidence of uncertainty, not something to hide.” |
| 1:05–1:40 | Return to clip 85; record reviewed count, match simulated checkout, refill, verify; show audit | “Here I record a reviewed count for the scenario. A pickup moves units from shelf to in-hand; only the explicitly simulated checkout reduces total store stock. I then report and verify a refill. Each action preserves the balances and leaves a persistent history. The product mapping and backroom stock are disclosed demo assumptions.” |
| 1:40–2:00 | Replay 5 real sales; show dates, received times, shadow stock and supplier review | “These incoming events replay actual historical sales rows. Original dates and receipt times remain visible. They update shadow inventory and surface supplier reviews. When verified stock or lead times are missing, purchase quantities are withheld. This proves the event workflow, not a connected live merchant feed.” |
| 2:00–2:35 | Model experiments: seven-day comparison, split and interval coverage | “Muse proposes bounded experiments; measured results choose the model. On 74 real FreshRetailNet series, a seasonal baseline wins the selection. Its seven-day evaluation WAPE is 17.98%, compared with 23.59% for a trailing-mean baseline. The evaluation file was separate from selection and calibration. These normalized quantities support research comparison, not physical purchase orders.” |
| 2:35–3:00 | Work-plan what-if and saved/live Muse brief; expose evidence tools | “The manager can compare priorities under a time limit, then ask Muse to explain the evidence, sales exceptions and forecast limits together. Retail Pulse turns scattered signals into a reviewable operating loop. The next proof is a retailer pilot measuring verified counts, decision time and replenishment outcomes.” |

For the refill segment, use the quantities shown by the case. Enter a review note
that states the demo scope; after reporting a refill, verify the resulting shelf
count rather than the transferred quantity. Never imply that clicking a button
proves a physical refill occurred. If time is tight, show the existing audit
instead of rushing through every action.

The verified clip 85 run used a one-unit reviewed count, one-unit checkout,
three-unit refill and final shelf count of three. Restart the scenario before a
new recording and confirm the displayed balances; the existing verified audit is
also usable as saved demonstration evidence.

## Evidence to have ready after the main story

| Capability | Concrete evidence | Boundary to state |
|---|---|---|
| Muse action/count reasoning | Actual primary responses across 22 RetailAction clips; 5 candidate take cases totaling 6 inferred units | Candidate totals are not perception accuracy; current Operations actions require review. |
| Count challenge | Clip 420 primary count 2 versus second-pass count 1; hold for human review | A second pass of the same model is not independent ground truth. |
| SAM localization | Clip 85: 408 frame-box records, 16 tracks; tested clips 42 and 420: no detections | Tracks include shelf bottles and do not establish transferred quantities, identity or payment. |
| Durable operating loop | Five cases; reviewed counts, checkout, refill, verification, before/after audit, duplicate and revision guards | A local research scenario, with no original source-inventory write. |
| Sales reporting | 60 prepared real STR-1010 source rows; event IDs, original source dates and receipt times | Latest opening stock intervals and historical sales are not aligned for historical reconciliation. Noon UTC is a placeholder for day-only source timestamps. |
| Seven-day evaluation | 74 series × 90 training days = 6,660 rows; separate 518-row publisher evaluation; 17.982% versus 23.588% WAPE | One store and one final week; normalized quantities; no universal accuracy claim. |
| Forecast uncertainty | Nominal 80% seven-day bands covered 86.486% of the 74 evaluation series | Empirical coverage under temporal/product dependence is not a future guarantee. |
| Muse-assisted M5 tuning | Separate constrained experiment using 200 M5 series and real recorded-unit history | Its rolling one-day results are separate from the FreshRetailNet seven-day benchmark. |

Open Data library (`#library`) for broader source history. The warehouse's full
size is not the tuning sample size, and separate source businesses are not one
connected retailer. Product journey (`#flow`) retains the original walkthrough;
use Operations desk for current review gates and persisted human actions.

Useful brief prompt:

> Explain the highest-priority store action. Separate the camera observation,
> reviewed count, confirmed or simulated sale, stock assumption and forecast.
> Cite the evidence, identify what still needs review, and describe the planning
> handoff without inventing an order quantity.

## Failure case and fallback

The clip 420 disagreement is the primary failure case. Also show that SAM's
zero-detection results remain empty rather than being replaced with invented
geometry. Neither uncertainty nor an unmatched movement is a theft finding.

If a new provider request fails, display the failure and explicitly switch to a
saved real-response walkthrough. Existing evidence, sales replay, case actions
and benchmark reports remain usable without a new inference. A benchmark can
select a simple baseline; do not relabel that result as a Muse-trained model win.

Do not claim customer validation, theft detection, measured savings, live retail
deployment or a competition win. The [strategy](HACKATHON_STRATEGY.md) records
official criteria and submission unknowns; [POS integration](POS_INTEGRATION.md)
describes the actual event contract and its limits.
