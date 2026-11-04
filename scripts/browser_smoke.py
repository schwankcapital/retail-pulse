"""Exercise Interface 2.0 against an isolated, synthetic Retail Pulse runtime.

Run the server separately, then:
  python scripts/browser_smoke.py --url http://127.0.0.1:8000

Requires Playwright (optional QA dependency):
  python -m pip install playwright
  python -m playwright install chromium

--bridge renders the exact assets through Playwright and forwards fetches to the
local HTTP API through httpx. It is for restricted render environments that
cannot navigate to localhost, not a production feature. It does not test browser
HTTP navigation, persistent localStorage, or HTTP CSP enforcement.
"""
from __future__ import annotations

import argparse
import base64
import json
import re
from pathlib import Path
from urllib.parse import urlparse

import httpx
from playwright.sync_api import sync_playwright, expect

ROOT = Path(__file__).resolve().parents[1]
WEB = ROOT / 'src' / 'retail_pulse' / 'web'
PAGES = ['overview', 'inventory', 'forecast', 'health', 'agents', 'timeline', 'inputs']

BRIDGE_SCRIPT = r'''() => {
  window.fetch = async (url, opts = {}) => {
    if (opts.signal?.aborted) throw new DOMException('Aborted', 'AbortError');
    let body = opts.body || null;
    let form = null;
    if (body instanceof FormData) {
      form = [];
      for (const [name, value] of body.entries()) {
        if (value instanceof File) {
          const bytes = new Uint8Array(await value.arrayBuffer());
          let binary = ''; for (const b of bytes) binary += String.fromCharCode(b);
          form.push({name, filename:value.name, type:value.type, base64:btoa(binary)});
        } else form.push({name, value:String(value)});
      }
      body = null;
    }
    const result = await window.__localApiBridge({url:String(url), method:opts.method || 'GET',
      headers:Object.fromEntries(new Headers(opts.headers || {})), body, form});
    if (opts.signal?.aborted) throw new DOMException('Aborted', 'AbortError');
    const bytes = Uint8Array.from(atob(result.body), c => c.charCodeAt(0));
    return new Response(bytes, {status:result.status, headers:result.headers});
  };
}'''


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--url', default='http://127.0.0.1:8000')
    parser.add_argument('--bridge', action='store_true')
    parser.add_argument('--browser-executable')
    parser.add_argument('--output', type=Path, default=ROOT / 'artifacts' / 'ui-v2')
    args = parser.parse_args()
    parsed = urlparse(args.url)
    if parsed.hostname not in {'127.0.0.1', 'localhost'}:
        parser.error('Run against a local isolated demo, not a remote company server.')
    out = args.output.resolve()
    out.mkdir(parents=True, exist_ok=True)
    checks: list[str] = []
    errors: list[str] = []
    client = httpx.Client(base_url=args.url.rstrip('/'), timeout=120)
    baseline = client.get('/api/overview').json()
    if not baseline.get('synthetic'):
        raise RuntimeError('This QA script requires an isolated synthetic runtime, not real company data.')

    def api_bridge(payload):
        url = payload['url']
        if not url.startswith('/api/') or url.startswith('//'):
            raise ValueError('QA bridge permits only relative local API requests.')
        headers = payload.get('headers', {})
        kwargs = {'headers': headers}
        if payload.get('form') is not None:
            data, files = {}, []
            for item in payload['form']:
                if 'filename' in item:
                    files.append((item['name'], (item['filename'], base64.b64decode(item['base64']), item['type'])))
                else:
                    data[item['name']] = item['value']
            headers.pop('content-type', None)
            kwargs.update(data=data, files=files)
        else:
            kwargs['content'] = payload.get('body')
        response = client.request(payload.get('method', 'GET'), url, **kwargs)
        return {'status': response.status_code, 'headers': dict(response.headers),
                'body': base64.b64encode(response.content).decode()}

    def connect(page):
        page.on('pageerror', lambda e: errors.append(str(e)))
        page.on('console', lambda m: errors.append('Console: ' + m.text) if m.type == 'error' else None)
        if args.bridge:
            page.expose_function('__localApiBridge', api_bridge)
            html = re.sub(r'<link[^>]+>', '', (WEB / 'index.html').read_text())
            html = re.sub(r'<script[^>]*>.*?</script>', '', html, flags=re.S)
            page.set_content(html)
            page.add_style_tag(content=(WEB / 'style.css').read_text())
            page.evaluate(BRIDGE_SCRIPT)
            page.add_script_tag(content=(WEB / 'app.js').read_text())
        else:
            page.goto(args.url, wait_until='networkidle')
        page.wait_for_selector('.kpi')
        page.wait_for_timeout(750)

    def go(page, name):
        print(f'GO {page.viewport_size}: {name}', flush=True)
        if page.viewport_size['width'] <= 780:
            page.locator('#menu-toggle').click()
        page.locator(f'#navigation [data-page="{name}"]').click()
        page.wait_for_function('key => document.querySelector(".nav.active")?.dataset.page === key', arg=name)
        page.wait_for_timeout(330)

    def screenshot(page, name, full=True):
        page.wait_for_timeout(750)
        page.screenshot(path=str(out / (name + '.png')), full_page=full)

    def no_overflow(page, context):
        size = page.evaluate('({width:innerWidth,scroll:document.documentElement.scrollWidth})')
        assert size['scroll'] <= size['width'] + 1, (context, size)

    with sync_playwright() as p:
        launch = {'headless': True}
        if args.browser_executable:
            launch['executable_path'] = args.browser_executable
        browser = p.chromium.launch(**launch)
        context = browser.new_context(viewport={'width':1600,'height':1100}, device_scale_factor=1)
        page = context.new_page()
        page.set_default_timeout(10000)
        connect(page)
        expect(page.locator('.brand small')).to_have_text('In-Store Retail Super Intelligence')
        expect(page.locator('#mode-badge')).to_have_text('SYNTHETIC DEMO')
        expect(page.locator('.kpi')).to_have_count(4)
        no_overflow(page, 'desktop overview')
        screenshot(page, 'overview-dark')
        screenshot(page, 'overview-viewport', full=False)
        checks.append('Exact subtitle, four API-derived KPIs, and synthetic disclosure')

        page.locator('[data-period-kind="heat"][data-period="14"]').click()
        expect(page.locator('.signal-cell')).to_have_count(len(baseline['inventory']) * 14)
        page.locator('[data-period-kind="heat"][data-period="7"]').click()
        page.locator('#chart-sku').select_option('B')
        page.locator('[data-period-kind="chart"][data-period="7"]').click()
        expect(page.locator('#availability-chart')).to_have_attribute('aria-label', re.compile('SKU B'))
        page.locator('[data-series="unknown_hours"]').click()
        expect(page.locator('[data-series="unknown_hours"]')).to_have_attribute('aria-pressed','false')
        page.locator('#availability-chart').focus()
        page.keyboard.press('ArrowRight')
        expect(page.locator('#chart-tooltip')).to_have_class(re.compile('visible'))
        checks.append('Heatmap periods, SKU selector, chart periods, legend toggles and keyboard tooltip')

        page.keyboard.press('Control+k')
        expect(page.locator('#command-dialog')).to_be_visible()
        page.locator('#command-search').fill('SKU C')
        page.keyboard.press('Enter')
        expect(page.locator('#inspector')).to_be_visible()
        expect(page.locator('#inspector-title')).to_contain_text('Misplaced')
        screenshot(page, 'product-inspector', full=False)
        page.keyboard.press('Escape')
        expect(page.locator('#inspector')).not_to_be_visible()
        checks.append('Command palette search, Enter selection, product drawer and Escape')

        go(page, 'inventory')
        page.locator('#inventory-search').fill('Misplaced')
        expect(page.locator('#inventory-table tbody tr')).to_have_count(1)
        page.locator('#inventory-search').fill('')
        page.locator('#inventory-filter').select_option('variance')
        expect(page.locator('#inventory-table tbody tr')).to_have_count(2)
        screenshot(page, 'inventory-truth')
        page.locator('#inventory-filter').select_option('all')
        checks.append('Inventory product search and variance filter')

        go(page, 'forecast')
        expect(page.locator('#chart-container')).to_be_visible()
        page.locator('#chart-sku').select_option('F')
        screenshot(page, 'demand-intelligence')
        checks.append('Demand chart, forecasts and existing benchmark display')

        go(page, 'health')
        expect(page.locator('.health-card')).to_have_count(len(baseline['health']['metrics']))
        page.locator('#health-mode').select_option('demo')
        page.locator('#review-health').click()
        expect(page.locator('#health-agent-result .agent-answer')).to_be_visible(timeout=30000)
        screenshot(page, 'ml-health-steward')
        checks.append('ML health diagnostics and actual offline health-agent API request')

        go(page, 'agents')
        screenshot(page, 'business-insights-empty')
        page.locator('.sample-question').first.click()
        expect(page.locator('#question')).not_to_be_empty()
        page.locator('#agent-mode').select_option('demo')
        page.locator('#question').focus()
        page.keyboard.press('Control+Enter')
        expect(page.locator('#agent-result .agent-answer')).to_be_visible(timeout=30000)
        expect(page.locator('#agent-result')).to_contain_text('OFFLINE WALKTHROUGH')
        screenshot(page, 'business-insights-agent')
        # Response persists for this store while navigating away and back.
        go(page, 'overview'); go(page, 'agents')
        expect(page.locator('#agent-result .agent-answer')).to_be_visible()
        checks.append('Business prompt cards, Ctrl+Enter, offline labeling and in-session answer retention')

        go(page, 'timeline')
        page.wait_for_selector('.timeline-event')
        page.wait_for_selector('#player')
        page.wait_for_function('document.querySelector("#player").readyState >= 1', timeout=15000)
        assert page.locator('#video-caption').inner_text().startswith('Synthetic illustration')
        page.locator('#event-sku').select_option('C')
        page.locator('#event-kind').select_option('misplacement')
        page.locator('#events-load').click()
        expect(page.locator('#event-list')).to_contain_text('Misplacement')
        screenshot(page, 'visual-evidence')
        checks.append('Evidence video decode, source labels and filtered observation retrieval')

        go(page, 'inputs')
        expect(page.locator('#media-form')).to_be_visible()
        assert not page.locator('#media-form').evaluate('(form) => form.checkValidity()')
        expect(page.locator('#content')).to_contain_text('Data integration is unchanged')
        # Re-import one existing demo catalog row: validates multipart handling,
        # idempotency, and the preserved import endpoint without adding records.
        product = client.get('/api/catalog').json()[0]
        page.locator('#import-form input[type=file]').set_input_files({
            'name':'existing-demo-product.json','mimeType':'application/json',
            'buffer':json.dumps([product]).encode()})
        page.locator('#import-form button[type=submit]').click()
        page.wait_for_function('document.querySelector("#import-result").textContent.trim().startsWith("{")')
        result = json.loads(page.locator('#import-result').inner_text())
        assert 'error' not in result, result
        screenshot(page, 'sources-ingestion')
        checks.append('Native required-field validation and real idempotent multipart import')

        go(page, 'overview')
        page.locator('#theme-toggle').click()
        expect(page.locator('html')).to_have_attribute('data-theme','light')
        screenshot(page, 'overview-light')
        page.locator('#theme-toggle').click()
        checks.append('Dark/light theme switch')

        page.locator('#access-open').click()
        expect(page.locator('#access-dialog')).to_be_visible()
        expect(page.locator('#access-dialog')).to_contain_text('not your Meta API key')
        page.keyboard.press('Escape')
        checks.append('Local API access dialog and token separation')

        for width in (390, 768, 1024):
            page.set_viewport_size({'width':width,'height':900})
            for name in PAGES:
                go(page,name)
                no_overflow(page, f'{width}px {name}')
            go(page,'overview')
            if width == 390:
                screenshot(page,'mobile-overview')
                page.locator('#menu-toggle').click()
                expect(page.locator('#menu-toggle')).to_have_attribute('aria-expanded','true')
                page.keyboard.press('Escape')
                expect(page.locator('#menu-toggle')).to_have_attribute('aria-expanded','false')
        checks.append('All seven pages at 390, 768 and 1024 px; mobile menu, Escape and no root overflow')

        page.set_viewport_size({'width':1600,'height':1100})
        page.evaluate('location.hash = "__proto__"')
        page.wait_for_timeout(400)
        expect(page.locator('.nav.active')).to_have_attribute('data-page','overview')
        # Rapid navigation must not render an out-of-date route or error.
        page.evaluate('''() => { for (const name of ['timeline','forecast','agents','overview']) document.querySelector(`#navigation [data-page="${name}"]`).click(); }''')
        page.wait_for_timeout(700)
        expect(page.locator('.kpi')).to_have_count(4)
        checks.append('Invalid-route fallback and rapid navigation race handling')

        reduced = browser.new_context(viewport={'width':1440,'height':1000},reduced_motion='reduce')
        rp = reduced.new_page()
        connect(rp)
        assert rp.evaluate('matchMedia("(prefers-reduced-motion: reduce)").matches')
        duration = rp.locator('.kpi').first.evaluate('(e) => getComputedStyle(e).animationDuration')
        assert float(duration.rstrip('s')) <= 0.001, duration
        go(rp,'inventory')
        checks.append('Reduced-motion preference honored')
        reduced.close()
        browser.close()

    client.close()
    report={'mode':'browser DOM + real local HTTP API bridge' if args.bridge else 'browser + local HTTP server',
            'checks_passed':len(checks),'checks':checks,'javascript_errors':errors,
            'limitations':['Live Muse/SAM not called.','Bridge mode does not validate direct browser networking, persistent storage or HTTP CSP enforcement.'] if args.bridge else ['Live Muse/SAM not called.']}
    (out/'browser-tests.json').write_text(json.dumps(report,indent=2)+'\n')
    if errors:
        raise AssertionError(errors)
    print(json.dumps(report,indent=2))
    return 0

if __name__ == '__main__':
    raise SystemExit(main())
