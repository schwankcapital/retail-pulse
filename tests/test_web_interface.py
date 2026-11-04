"""Static and HTTP contract tests for the interface-only upgrade."""
from html.parser import HTMLParser
from pathlib import Path

from fastapi.testclient import TestClient
from retail_pulse.api import WEB, create_app


class Markup(HTMLParser):
    def __init__(self, text):
        super().__init__()
        self.tags = []
        self.feed(text)

    def handle_starttag(self, tag, attrs):
        self.tags.append((tag, dict(attrs)))


def test_interface_title_and_subtitle():
    html = (WEB / 'index.html').read_text()
    assert 'In-Store Retail Super Intelligence' in html
    assert 'PHYSICAL RETAIL INTELLIGENCE' not in html
    assert '<title>Retail Pulse | In-Store Retail Super Intelligence</title>' in html


def test_ui_assets_remain_local():
    markup = Markup((WEB / 'index.html').read_text())
    for tag, attrs in markup.tags:
        if tag == 'script':
            assert attrs.get('src', '').startswith('/static/')
            assert 'defer' in attrs
        if tag == 'link':
            assert attrs['href'].startswith('/static/')
    for asset in ('index.html', 'app.js', 'style.css', 'favicon.svg'):
        assert (WEB / asset).is_file()


def test_no_inline_handlers():
    markup = Markup((WEB / 'index.html').read_text())
    assert not [(tag, key) for tag, attrs in markup.tags for key in attrs if key.startswith('on')]


def test_original_pages_and_research_pages_preserved():
    markup = Markup((WEB / 'index.html').read_text())
    pages = {attrs['data-page'] for _, attrs in markup.tags if 'data-page' in attrs}
    assert pages == {'overview', 'timeline', 'inventory', 'forecast', 'health', 'agents', 'inputs','flow','library','lab','operations'}


def test_reduced_motion_and_progressive_enhancement():
    css = (WEB / 'style.css').read_text()
    js = (WEB / 'app.js').read_text()
    assert 'prefers-reduced-motion:reduce' in css
    assert 'document.startViewTransition && !reducedMotion.matches' in js
    assert 'AbortController' in js
    assert "history.pushState" in js


def test_accessibility_structure():
    markup = Markup((WEB / 'index.html').read_text())
    ids = [attrs['id'] for _, attrs in markup.tags if 'id' in attrs]
    assert len(ids) == len(set(ids))
    dialogs = [attrs for tag, attrs in markup.tags if tag == 'dialog']
    assert len(dialogs) == 3
    assert all('aria-labelledby' in attrs for attrs in dialogs)
    assert any(tag == 'main' and attrs.get('id') == 'content' for tag, attrs in markup.tags)
    assert any(attrs.get('aria-live') == 'polite' for _, attrs in markup.tags)


def test_frontend_contracts_preserved():
    js = (WEB / 'app.js').read_text()
    for route in ('/api/config', '/api/overview', '/api/daily', '/api/evidence', '/api/events',
                  '/api/media/', '/api/ask', '/api/upload-media', '/api/import', '/api/run'):
        assert route in js
    assert 'new FormData(form)' in js
    assert "role:'health'" in js and "role:'business'" in js


def test_no_executable_model_output():
    js = (WEB / 'app.js').read_text()
    assert '${esc(result.answer)}' in js
    assert 'eval(' not in js
    assert 'new Function(' not in js


def test_http_assets_and_content_policy(demo_settings):
    with TestClient(create_app(demo_settings)) as client:
        html = client.get('/')
        assert html.status_code == 200
        assert "script-src 'self'" in html.headers['content-security-policy']
        for asset in ('style.css', 'app.js', 'favicon.svg'):
            result = client.get('/static/' + asset + '?v=ui2')
            assert result.status_code == 200
            assert len(result.content) > 100
        assert client.get('/static/favicon.svg').headers['content-type'].startswith('image/svg+xml')
