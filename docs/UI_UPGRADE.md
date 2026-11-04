# Retail Pulse - Interface 2.0

**In-Store Retail Super Intelligence**

This is a frontend-only upgrade of the existing Python project. The source
subtitle is exactly `In-Store Retail Super Intelligence`.

## What changed

- Dark graphite surfaces, mint accents, restrained translucent header, consistent
  typography, local line icons, and a new pulse favicon. A light theme is included.
- Smooth route transitions with a direct-render fallback; small entrance and hover
  effects, loading skeletons, progress feedback, and notifications.
- Keyboard command palette (`Ctrl+K` / `Cmd+K`) for pages, products and UI actions.
- Clickable availability heatmap derived from the existing daily-exposure report.
- Interactive SVG charts: product selector, 7/14/28-day windows, series toggles,
  pointer tooltips and left/right arrow inspection.
- Product drawer: physical/book counts, demand estimates, review gates, evidence
  references and a shortcut to ask the business agent about that product.
- Searchable inventory table and status filters.
- Updated evidence player, event filters, pagination and source navigation.
- Redesigned ML Health Steward and Business Insights screens, prompt suggestions,
  in-session answer retention per store, copy answer and explicit agent-mode selection.
- Responsive mobile navigation, native modal focus behavior, keyboard controls,
  reduced-motion support and safe HTML escaping of model/API text.
- New subtitle, local assets and optional QA scripts.

## What did NOT change

All original Python modules under `src/retail_pulse/*.py` are byte-for-byte
unchanged. API routes, database schemas, data generation, forecasting, fusion,
optimization, Meta integration and health policy are unchanged. This update does
not integrate any external datasets, live camera systems or employer data.

No npm, Node build, JavaScript framework, third-party CDN, remote font or new
runtime dependency is required. Playwright is optional and only needed to rerun
browser QA. The normal application continues to run with Python/FastAPI.

Existing import and media-upload controls are retained. They perform actions only
when explicitly submitted. Live analysis still requires server-side authorization
and credentials. Health/business requests default to the offline demonstration.

## Update an existing installation (recommended)

1. Stop the running server with `Ctrl+C`.
2. Back up your existing project, especially your private `.env` and `runtime/`.
3. Extract the UI update ZIP. Run the included standard-library installer from
   Anaconda Prompt, replacing the example paths with your actual locations:

```bat
python "C:\path\retail-pulse-ui-update\scripts\apply_ui_upgrade.py" --target "C:\Users\daniel.schwank\Downloads\Retail_Pulse_Python_Project\retail-pulse"
```

The installer replaces only these assets:

```text
src/retail_pulse/web/index.html
src/retail_pulse/web/style.css
src/retail_pulse/web/app.js
src/retail_pulse/web/favicon.svg
```

It creates a dated backup beside the target project and restores changed assets
if copying fails. Add `--dry-run` to check paths without writing. Alternatively,
copy these four files manually into the same folder in your existing project.

4. Activate the same environment you already use, then start the server:

```bat
cd /d "C:\Users\daniel.schwank\Downloads\Retail_Pulse_Python_Project\retail-pulse"
conda activate retail-pulse
python -m retail_pulse serve
```

For a virtual environment instead of Conda, use `.venv\Scripts\activate`.
Open `http://127.0.0.1:8000` and hard-refresh with `Ctrl+F5`.

**Do not recreate the environment, regenerate demo data, or copy `.env.example`
over your existing `.env` just to update the interface.** Your original install
must already be working; this UI patch does not repair package-network/SSL issues.

## Clean installation from the full-project ZIP

Extract the full project to a new directory. Use the existing `START_HERE.md`
installation instructions. Keep the old project intact until you have checked
the new UI. The full ZIP does not contain your private runtime, credentials or
external source datasets.

## UI controls

| Action | Control |
|---|---|
| Jump to page, product or action | Ctrl+K / Cmd+K |
| Navigate command results | Arrow keys; Enter to open; Esc to close |
| Submit business question | Button or Ctrl+Enter / Cmd+Enter in the composer |
| Open product details | Product row, heatmap cell or action arrow |
| Switch theme | Sun/moon control in the top bar |
| Inspect chart date | Pointer hover, or focus the chart and use arrow keys |
| Inspect media | Visual evidence page; source reference buttons |
| Enter local API bearer token | API access in the sidebar |
| Refresh database reports | Refresh icon; does NOT retrain or regenerate data |
| Explicitly recompute reports | Sources & ingestion / Recompute analytics |

The local API bearer token is not your Meta API key. The Meta API key remains
server-side. Only theme/store preferences are placed in local storage; the local
bearer token uses session storage. Agent responses remain in browser memory.

## Honest data presentation

- Synthetic/demo labels remain visible. No simulated dashboard ticker is called
  a live camera stream.
- KPI counts, heatmap cells, chart lines and product details use API results.
- Observation coverage is not presented as product availability. It measures the
  fraction of monitored product-hours with a known shelf state.
- Heatmap cells with unknown hours are marked unknown; the tooltip gives exact
  available/unavailable/unknown hour totals. A cell summarizes a day, not an SKU count.
- Forecast and diagnostic ranges retain their original qualification.
- Time-window controls change the displayed availability chart or heatmap only.
  The backend's existing demand KPIs remain explicitly labeled as last 7 observed days.
- The interface does not add automatic ordering, theft attribution, retraining
  or model promotion.

## Testing and screenshots

Run Python tests:

```bat
python -m pytest -q
```

Optional browser QA (use a separate synthetic runtime, not private company data):

```bat
python -m pip install playwright
python -m playwright install chromium
python scripts\browser_smoke.py --url http://127.0.0.1:8000
```

`artifacts/ui-v2/` contains screenshots and current validation results. Earlier
files directly under `artifacts/` are retained as the original build's records,
not new live-model evaluations. See `artifacts/ui-v2/VALIDATION.md` for test scope.

## Browser implementation references

- MDN: Document.startViewTransition, including feature-detected fallback:
  https://developer.mozilla.org/en-US/docs/Web/API/Document/startViewTransition
- MDN: HTMLDialogElement.showModal, native modal behavior and background inertness:
  https://developer.mozilla.org/en-US/docs/Web/API/HTMLDialogElement/showModal
- MDN: prefers-reduced-motion:
  https://developer.mozilla.org/en-US/docs/Web/CSS/@media/prefers-reduced-motion

These document browser APIs, not endorsements or dependencies of Retail Pulse.
