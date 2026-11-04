# Retail Pulse — three-minute hackathon recording script

Prepared November 3, 2026 for the Indie track / Build for Your World theme.
The recording follows the verified local build. Three minutes is the requested
editorial target; the submission portal's official video-duration requirement
has not been verified. No new paid inference is needed to read or rehearse this script.

**Video title:** Retail Pulse: From Shelf Evidence to Retail Decisions

**Core message:** Help retail companies connect what happened on the shelf,
what was sold, and what operations and planning should do next.

**Opening visual:** The working Operations desk, with a small title overlay:
“Retail Pulse · Built with Meta Muse Spark 1.3 + SAM 3.1”. Show the product within
the first second. Avoid spending opening time on an animated logo or architecture slide.

**Recording setup**

1. Open http://127.0.0.1:8001/#operations. If necessary, start the existing server
   with `Start_Dataset_Demo.cmd`. Preserve the current runtime and API usage ledger.
2. Record at 1920 × 1080, 30 fps, with browser zoom chosen so the evidence video,
   balances and action controls are readable. Hide bookmarks and unrelated tabs.
   Keep the app's source disclosures visible. Record a clean microphone track.
3. Select the card `FOODS_1_011`, described as “single small chilled beverage
   container”. Confirm the evidence identifier is `retailaction-000085`.
   Click **Restart this scenario (keeps audit history)** before recording the
   action take. Expect shelf 1, backroom 3, in-hand 0, whole-store balance 4.
4. Keep clip `retailaction-000420` unreviewed. Its card is `FOODS_1_022`, the small
   red packets with **COUNT DISAGREEMENT**. Do not approve it merely to simplify a demo.
5. Prepare these notes in a local scratchpad for pasting:
   - Count: “Demo review: one visible container inferred from the paired clip; product identity is an illustrative mapping.”
   - Verification: “Demo operator confirmation: three scenario shelf units; no new camera evidence or real store audit.”
6. Inspect the sales replay counter. There are 60 prepared rows total. Each click
   receives up to five unused rows; navigation or rerender can stop the batch.
   Stay on the page until it finishes. Rehearse without exhausting the replay.
7. Capture a full successful action-and-sales take first. Then, if the saved Muse
   brief no longer matches that take, request **one** fresh operations brief using
   the existing guarded button and capture the completed result as a pickup shot.
   New briefs spend credit; playback, actions and sales replay do not. Do not
   repeatedly call the API to hide waiting time. Label the displayed answer
   “Saved actual Muse response”, including when edited into the final recording.
8. Capture the forecasting page in separate takes: the lower M5 experiment, then
   the upper FreshRetailNet weekly benchmark. This avoids hurried scrolling in
   the final video. Preserve the distinction between those two experiments.
9. Use the narration below as a separate voice track. Record slightly slower on
   quantities and model results. Target roughly 130–140 spoken words per minute,
   leaving short pauses for state changes. Rehearse against the exact time windows.

**Timed shot list and word-for-word narration**

| Time | Screen direction and editing cue | Narration |
|---|---|---|
| 0:00–0:15 | Start on Operations desk. Briefly frame “See the shelf. Act on the signal.” and the Observe → Review → Reconcile → Replenish → Plan strip. Small overlay: “For store operations, supply chain and demand planning”. | “A shelf can be empty while the inventory system still reports stock. For retail teams, that means a decision: refill, investigate, or reorder? I built Retail Pulse to connect camera evidence, sales, and planning.” |
| 0:15–0:38 | Select FOODS_1_011 / clip 85. Click **Replay evidence** with **Show actual SAM boxes** checked. Let the full five-second clip run at normal speed. Then frame the Muse reading, including the 1.8–4.2 second transfer interval. Lower third: “Public RetailAction footage · Saved actual model results”. | “This is real public retail footage. Muse Spark interprets the interaction and proposes a one-item shelf-to-hand transfer. SAM localizes bottles across the video, so the manager can inspect the evidence. These are saved results from actual Meta API calls. The boxes include shelf objects; they are not purchase counts.” |
| 0:38–0:55 | Select FOODS_1_022 / clip 420. Frame the challenge panel showing first-pass 2 and second-pass 1, plus REVIEW COUNT and unchanged opening balance. Lower third: “Two Muse passes disagree → human review”. | “Now watch what happens when the evidence is ambiguous. Two passes of Muse disagree: two packets or one? Retail Pulse holds the proposal for human review. An uncertain observation cannot silently become an inventory adjustment.” |
| 0:55–1:30 | Return to FOODS_1_011 / clip 85. Follow the exact action sequence below. Hold each changed balance on screen briefly. Finish on VERIFIED and the action audit. Persistent lower third for this segment: “Demo joins and operator actions · Source records preserved”. | “For the clearer case, I record a reviewed count. One item moves from shelf to in-hand; total store stock stays unchanged. Only the simulated checkout reduces that total. I then report a three-unit refill and verify the resulting shelf count. Every step leaves an audit trail. Product identities and stock mappings are explicit demo joins.” |
| 1:30–1:52 | Click **Replay 5 real sales** and wait for completion. Cut to the received-sales table, then Supply-chain exceptions. Highlight “Source day” and “Received” together. Lower third: “Historical source replay · No live merchant feed connected”. | “Next, actual historical sales records arrive through the event workflow. Original sale dates and receipt times remain separate. Sales update a shadow inventory and surface supplier-review exceptions. Missing verified stock or lead times keeps order quantities on hold. This demonstrates the workflow for a future live retailer connection.” |
| 1:52–2:26 | Open **Model experiments**. First show the lower M5 candidate table for about seven seconds. Then cut to the upper FreshRetailNet table and four KPI cards. Highlight 17.98%, 23.59%, and 74 series. Lower third: “Separate weekly evaluation · Normalized quantities”. | “Muse also plans bounded forecasting experiments. Here, it chose regression settings tested against real M5 sales. In a separate weekly test on seventy-four FreshRetailNet product histories, validation selected the seasonal baseline. Seven-day error was seventeen point nine eight percent, versus twenty-three point five nine for the trailing mean. Selection happened before final evaluation. These are normalized quantities, so the system withholds physical order amounts.” |
| 2:26–2:46 | Return to Operations desk. Show the completed Muse brief and its three suggested actions. Expand **Read the complete reasoning, source metrics and tool trace**, then briefly show the four-tool trace. Cut to Work plan under a time limit; compare 5 minutes and 10 minutes if the captured case state is unchanged. | “Muse retrieves operational state, video reviews, and forecast metrics through tools. Its brief explains what needs attention and why. The manager can inspect the evidence behind each recommendation and choose work that fits the available time.” |
| 2:46–3:00 | Return to the Operations desk hero, or use a simple end card with a small product screenshot. Text: “Retail Pulse — Evidence → Action → Planning”. Small supporting line: “144 automated tests passed at validation”. Hold the final frame for the last two seconds. | “For Build for Your World, this is my focus: helping retail teams turn scattered signals into clear decisions. Retail Pulse connects the shelf to the next operational action.” |

**Exact action choreography for 0:55–1:30**

| Approximate time | Input and button | Expected result for the prepared clip 85 scenario |
|---|---|---|
| 0:55–1:02 | Quantity **1**; paste the count note; click **Record reviewed count**. | Shelf **0**, in-hand **1**, backroom **3**, whole-store **4**. |
| 1:02–1:08 | Set Quantity back to **1**; click **Match simulated checkout**. The form can change its default quantity after each action, so explicitly set it. | Shelf **0**, in-hand **0**, backroom **3**, whole-store **3**. |
| 1:08–1:15 | Set Quantity **3**; click **Report scenario refill**. | Shelf **3**, in-hand **0**, backroom **0**, whole-store **3**. |
| 1:15–1:23 | Quantity **3**; paste the verification note; click **Verify scenario shelf count**. | Status **VERIFIED**. Verification is an operator demo report. |
| 1:23–1:30 | Show **Action audit**, with the four new entries. | Approve Count → Match Checkout → Restock → Verify Shelf, displayed newest first. |

Pause recording between takes if needed. The final edit can cut typing and long
scrolls while preserving the visible before/after values. Do not splice together
incompatible case revisions or imply edited waiting time is measured model latency.

**Make the result easy to judge**

- Give each shot one job: establish the problem, show perception, show a failure
  gate, complete an action, receive sales, evaluate forecasting, explain decisions.
- Use large, accurate captions. Keep them to one or two lines and away from
  the quantity inputs, video controls and source notices. Spell out WAPE once
  in an overlay as “Weighted absolute percentage error — lower is better”.
- Show the complete five-second evidence clip once at its real speed. If using
  an enlarged inset later, keep both views available and label it as a replay.
- Use only quiet background music, if any. Clear narration and legible numbers
  matter more than transitions. Straight cuts are sufficient.
- Crop the app into the relevant panel rather than shrinking an entire desktop.
  Preserve enough UI context that judges can see the feature is working software.
- Keep a small, readable source footer for footage and benchmark shots. Suggested
  footer text: “RetailAction public research footage” and “FreshRetailNet-50K,
  store 0; eval 2024-06-26–2024-07-02”.
- Use 17.98% as **weekly WAPE**, not classification accuracy or a measured sales
  improvement. The seasonal baseline won the weekly selection. M5 regression
  tuning is a different experiment with rolling one-day evaluation.
- Do not describe a pickup as confirmed payment or theft. The photographed item
  is illustratively mapped to the displayed product identifier. The retail sales
  replay is separate from the filmed store's checkout records.
- Let the opening communicate the intended benefit without fabricated customer
  quotes, revenue gains or claims of deployment. Add a personal motivation only
  if you can truthfully support it, replacing rather than extending the opening.

**Backup shots to record outside the three-minute cut**

- Data library: original product identifiers, quantities, dates and filters.
- The 74-series forecast's separate publisher evaluation dates and interval
  coverage, with the one-store/one-week scope visible.
- M5 candidate parameters and chronological train/validation/test partitions.
- Action audit and a screenshot of the completed scenario.
- The empty SAM result on clip 420: zero detections are not evidence of no product.

If a fresh provider request is slow or fails, use a labeled saved real response.
Do not regenerate the forecast or upload more video merely to record the demo.
If replay has exhausted its 60 rows, use the recorded intake take or show the
existing event ledger, explaining that it is a saved replay. Do not reset the
usage ledger or invent additional events.

**Export and submission**

As an editorial recommendation, export a 16:9 1080p MP4 with clear narration and
captions, and inspect the exported file from start to finish. The final timeline
should end at 3:00, including its end card. Confirm the portal's accepted format,
length and link permissions before submitting; those requirements are not
established by this script.

Meta's event page currently lists November 4, 2026, 9 PM Eastern / 7 PM Denver
as the submission deadline, with dates subject to change. Its Indie description
emphasizes creativity, technical ambition and a working result; Build for Your
World emphasizes practical domain problems. This sequence presents working
evidence for those aims. [Official event page](https://dev.meta.ai/events/global-hackathon)

The signed-in portal's duration limit was not accessible during preparation.
[Submission portal](https://cerebralvalley.ai/e/meta-ai-developer-hackathon/hackathon/submit)

Supporting files: [demo strategy](HACKATHON_STRATEGY.md),
[POS contract](POS_INTEGRATION.md), and
[verification snapshot](../artifacts/demo-verification.json).
