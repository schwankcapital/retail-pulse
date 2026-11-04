# Meta integration notes

Documentation checked on 2026-10-26. Source links: [SOURCES.md](SOURCES.md).

## Interfaces

- Base URL: `https://api.meta.ai/v1`.
- Text/multimodal model default: `muse-spark-1.3`.
- Segmentation default: `sam-3.1` (the API ID, not a guessed marketing slug).
- Authorization: `Bearer MODEL_API_KEY`, held only in backend environment variables.
- Calls: `POST /responses`; video upload: `POST /files` with `purpose=user_data`.
- Images: input_image data URLs. Videos: input_video with uploaded file ID.
- Structured extraction/answers: Responses `text.format` with a JSON Schema.
  Do not send Chat Completions' `response_format` to this adapter.
- Agent calls: function tools and function_call_output items. Bounded stateless
  history replay retains encrypted reasoning when supplied by the provider.

The project uses `httpx` directly rather than requiring an OpenAI SDK. This is
Meta inference, not OpenAI inference with a renamed model.

## Three Muse roles

1. **Vision:** derives bounded observations from approved media and known catalog.
2. **ML health:** interprets computed health/error/drift metrics after numerical
   extraction reaches the database. May suggest, but cannot execute, retraining.
3. **Business insights:** retrieves operational evidence with allowlisted tools.

Raw responses stay in the private runtime. The dashboard displays the final
answer and tool evidence, not private chain-of-thought. Encrypted reasoning is
only used as opaque replay state for tool loops.

## SAM behavior

One concise object noun phrase per request. Responses contain explicit frame
indices and object IDs with box/mask records. The parser retains frame indices
and IDs rather than assuming dense frames or matching array positions. A response
with no matches is valid. The raw encoded mask is saved; exact mask raster decoding
is not implemented. Source boxes support image overlays and geometry context.

The perception workflow can run Muse without SAM; provide `--sam-prompt` to invoke
SAM first. Segmentation does not identify UPCs or prove hidden counts. Track IDs
must not be used as permanent RFID item identities.

## Budget and retries

Default standard-mode rates are configurable snapshots, not guaranteed future
prices. Cache hits are handled separately from input tokens. SAM estimates use
source frame/image counts. Local SQLite reservations serialize concurrent budget
checks. A minimum request reserve prevents many simultaneous calls from bypassing
the guard; costs settle when usage is returned.

Only 429 responses are automatically retried, at most twice. Authentication and
schema failures fail visibly. Read timeouts may have been billed: reservations
remain until an operator reconciles them. The project never pretends a timeout
cost zero or silently switches a failed live call to a fake successful demo.

This is an approximate local guard, not enforcement by Meta. Media tokenization,
pricing changes and other API clients can change actual spending. Check the
provider dashboard and keep an independent reserve for the final demo.

Identical text requests are content-cached. Perception also uses an evidence/model/
prompt-version cache before uploading again. Clear relevant private cache records
only deliberately when testing a changed model/prompt.

## Before using real data

Default is standard mode with no contributor suffix. Contributor mode requires a
separate opt-in because content-use terms differ. Uploading media additionally
requires `ALLOW_EXTERNAL_MEDIA=true`. Native video files are removed after use
when possible, with a 24-hour expiry requested as backup. This does not establish
that no provider-side records remain; review your organization's requirements.

## Live smoke checklist

1. Configure the key locally and run `python -m retail_pulse smoke-meta`.
2. Run a live business question against synthetic numerical data.
3. Register one permitted image with the correct camera/zone mapping.
4. Analyze it with Muse and inspect the raw JSON plus accepted observations.
5. Add a single SAM noun-phrase prompt and verify geometry on known objects.
6. Test a short H.264 MP4 with known timestamps and an occlusion.
7. Confirm ambiguous events remain unknown, then run the pipeline and health agent.
8. Inspect actual Meta usage and set a conservative budget for evaluation.

Successful mock tests do not replace this live credential/media check.
