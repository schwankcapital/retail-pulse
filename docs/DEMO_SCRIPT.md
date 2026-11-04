# Retail Pulse demonstration

Suggested length: approximately three minutes. This is a presentation suggestion,
not a verified competition video-duration requirement.

## Preparation

Run the default demo in a clean runtime. Start the dashboard. Check the video,
then rehearse the same dataset without changing the random seed. To use actual
Muse reasoning, configure the backend key and select Live Muse. The included
screenshots and canned offline answers are clearly labeled demonstrations.

Never describe the generated video's observation labels as Muse/SAM output.
For the final competition recording, separately show a permitted real or staged
clip being extracted by the live model, with its validated database rows.

## Sequence

| Time | Screen | Point to show |
|---|---|---|
| 0:00-0:20 | Overview | Two SKUs can sell the same weekly quantity but have very different stockout exposure. |
| 0:20-0:55 | Visual evidence | Filter SKU C / misplacement; jump to the cited clip. Explain that moved merchandise is not a sale. |
| 0:55-1:20 | Inventory truth | Show verified negative/positive count variance for D/E, without attributing intent. |
| 1:20-1:45 | Demand intelligence | Show available/unavailable/unknown time, forecasts and conditional lost-demand estimates. |
| 1:45-2:10 | ML health steward | Run the review; show diagnostics, tool trace and that the agent cannot change gates or deploy a model. |
| 2:10-2:35 | Business insights | Ask why SKU C can be unavailable despite inventory, then inspect source IDs and numerical tool results. |
| 2:35-3:00 | Decisions and limits | Show quantity/capacity/review-cycle constraints, measured benchmark scope and human approval. |

## Useful prompts

```text
Which products have the most hidden demand, and which evidence supports that?
Why is SKU C unavailable even though inventory remains?
Explain the shrink and swell discrepancies without assuming theft.
Which replenishment visits should we reconsider?
Can we trust the demand model, and which diagnostics need attention?
```

Offline mode supports predefined walkthroughs; arbitrary natural-language
reasoning requires Live Muse. A live provider failure is shown as a failure and is
not silently replaced with an offline answer.

## Show an honest failure case

Use an occluded interval or a source clip without enough product detail. The
system should preserve unknown availability or reject invalid extraction. Then
show that an absent RFID read does not become a finding of loss.

## Submission package to prepare separately

Record the real working workflow, link the repository after reviewing its contents,
and include the data/evaluation limitations. Consult the accepted-participant
portal for actual upload fields, permitted data, duration limits and deadlines.
No competition submission or repository publishing is performed by this package.
