'use strict';
/**
 * Retail Pulse Interface 2.0
 * Native JavaScript, local assets, unchanged Python API contracts.
 * All numerical displays originate from the API. No fabricated live feeds,
 * forecast improvements, agent output, or integrated external datasets.
 */
const ICONS = {
  overview: '<rect x="3" y="3" width="7" height="7" rx="1.5"/><rect x="14" y="3" width="7" height="7" rx="1.5"/><rect x="3" y="14" width="7" height="7" rx="1.5"/><rect x="14" y="14" width="7" height="7" rx="1.5"/>',
  video: '<rect x="3" y="5" width="13" height="14" rx="3"/><path d="m16 9 5-3v12l-5-3z"/>',
  box: '<path d="m12 3 9 5v9l-9 5-9-5V8zM3 8l9 5 9-5M12 13v9M7.5 5.5l9 5"/>',
  chart: '<path d="M4 3v17h17M8 15l4-5 4 2 5-7"/>',
  pulse: '<path d="M2 12h5l3-8 4 16 3-8h5"/>',
  spark: '<path d="m12 3 2.5 6.5L21 12l-6.5 2.5L12 21l-2.5-6.5L3 12l6.5-2.5zM20 2v4M18 4h4"/>',
  layers: '<path d="m12 3 10 5-10 5L2 8zM2 12l10 5 10-5M2 16l10 5 10-5"/>',
  search: '<circle cx="10.5" cy="10.5" r="6.5"/><path d="m16 16 5 5"/>',
  arrow: '<path d="M4 12h16m-6-6 6 6-6 6"/>',
  external: '<path d="M14 3h7v7M21 3 10 14M10 3H5a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-5"/>',
  shield: '<path d="m12 3 8 3v6c0 5-8 9-8 9s-8-4-8-9V6zM8.5 12l2.5 2.5 4.5-5"/>',
  key: '<circle cx="8" cy="8" r="5"/><path d="m12 12 9 9m-4-4 3-3m-6 0 3-3"/>',
  menu: '<path d="M4 6h16M4 12h16M4 18h16"/>',
  close: '<path d="m6 6 12 12M6 18 18 6"/>',
  store: '<path d="M4 9v11h16V9M3 9l2-6h14l2 6M8 20v-7h8v7M3 9c0 4 5 4 5 0 0 4 8 4 8 0 0 4 5 4 5 0"/>',
  sun: '<circle cx="12" cy="12" r="4"/><path d="M12 2v2M12 20v2M2 12h2M20 12h2M5 5l1.5 1.5M17.5 17.5 19 19M5 19l1.5-1.5M17.5 6.5 19 5"/>',
  moon: '<path d="M21 13A9 9 0 0 1 11 3a9 9 0 1 0 10 10z"/>',
  refresh: '<path d="M20 7v5h-5M4 17v-5h5M6 7a7 7 0 0 1 11-2l3 3M4 16l3 3a7 7 0 0 0 11-2"/>',
  clock: '<circle cx="12" cy="12" r="9"/><path d="M12 7v5l4 2"/>',
  eye: '<path d="M2 12s4-7 10-7 10 7 10 7-4 7-10 7S2 12 2 12z"/><circle cx="12" cy="12" r="3"/>',
  check: '<path d="m5 12 4 4L19 6"/>',
  info: '<circle cx="12" cy="12" r="9"/><path d="M12 11v6M12 7v.2"/>',
  alert: '<path d="m12 3 10 18H2zM12 9v5M12 17v.2"/>',
  target: '<circle cx="12" cy="12" r="9"/><circle cx="12" cy="12" r="5"/><circle cx="12" cy="12" r="1"/>',
  upload: '<path d="M12 16V3m-5 5 5-5 5 5M4 15v5h16v-5"/>',
  database: '<ellipse cx="12" cy="5" rx="8" ry="3"/><path d="M4 5v14c0 4 16 4 16 0V5M4 12c0 4 16 4 16 0"/>',
  scan: '<path d="M8 3H3v5M16 3h5v5M3 16v5h5M21 16v5h-5M7 7v10M11 7v10M14 7v10M17 7v10"/>',
  copy: '<rect x="8" y="8" width="13" height="13" rx="2"/><path d="M16 8V5a2 2 0 0 0-2-2H5a2 2 0 0 0-2 2v9a2 2 0 0 0 2 2h3"/>',
  download: '<path d="M12 3v13m-5-5 5 5 5-5M4 17v4h16v-4"/>',
  play: '<path d="m8 5 12 7-12 7z"/>',
  chevron: '<path d="m9 5 7 7-7 7"/>',
  link: '<path d="m10 13 4-4M7 14l-2 2a4 4 0 0 0 6 5l3-3M10 6l3-3a4 4 0 0 1 6 5l-2 2"/>',
};
const PAGES = {
  operations: ['Operations desk', 'pulse'],
  flow: ['Product journey', 'play'], library: ['Data library', 'database'], lab: ['Model experiments', 'target'],
  overview: ['Operations overview', 'overview'], timeline: ['Visual evidence', 'video'],
  inventory: ['Inventory truth', 'box'], forecast: ['Demand intelligence', 'chart'],
  health: ['ML health steward', 'pulse'], agents: ['Business insights agent', 'spark'],
  inputs: ['Sources & ingestion', 'layers'],
};
const hasPage = page => Object.prototype.hasOwnProperty.call(PAGES, page);
const $ = (q, root = document) => root.querySelector(q);
const $$ = (q, root = document) => [...root.querySelectorAll(q)];
const esc = value => String(value ?? '').replace(/[&<>"']/g, c => ({'&':'&amp;', '<':'&lt;', '>':'&gt;', '"':'&quot;', "'":'&#39;'}[c]));
const finite = value => value !== null && value !== undefined && value !== '' && Number.isFinite(Number(value));
const number = (value, digits = 1) => finite(value) ? Number(value).toLocaleString(undefined, {maximumFractionDigits: digits}) : 'Not measured';
const sum = (rows, key) => rows.reduce((total, row) => total + (finite(row[key]) ? Number(row[key]) : 0), 0);
const clamp = (value, low, high) => Math.min(high, Math.max(low, value));
const icon = name => `<svg class="icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.65" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">${ICONS[name] || ICONS.info}</svg>`;
const nice = text => String(text ?? '').replace(/_/g, ' ').replace(/\b\w/g, s => s.toUpperCase());
const badge = (label, tone = null) => `<span class="badge ${esc((tone || String(label)).toLowerCase().replace(/[^a-z0-9_]/g, ''))}">${esc(String(label).replace(/_/g, ' '))}</span>`;
const td = (value, css = '') => `<td class="${esc(css)}">${value}</td>`;
const table = (headings, rows, caption = '') => `<div class="table-wrap"><table class="data-table">${caption ? `<caption class="sr-only">${esc(caption)}</caption>` : ''}<thead><tr>${headings.map(h => `<th scope="col">${esc(h)}</th>`).join('')}</tr></thead><tbody>${rows.length ? rows.join('') : `<tr><td colspan="${headings.length}" class="muted">No matching records.</td></tr>`}</tbody></table></div>`;
const panel = (heading, description, body, tools = '', css = '') => `<section class="panel ${css}"><div class="panel-header"><div><h2>${esc(heading)}</h2>${description ? `<p>${esc(description)}</p>` : ''}</div>${tools ? `<div class="panel-tools">${tools}</div>` : ''}</div>${body}</section>`;
const callout = (text, tone = '') => `<div class="callout ${tone}">${icon('info')}<span>${esc(text)}</span></div>`;
const routeLink = (page, label, css = 'button outline') => `<a href="#${page}" data-page="${page}" class="${css}">${esc(label)}${icon('arrow')}</a>`;
const productButton = row => `<button class="product-link" data-sku="${esc(row.sku)}"><span class="sku-bubble">${esc(row.sku)}</span><span class="product-title">${esc(row.title || `SKU ${row.sku}`)}</span></button>`;
const hero = (eyebrow, heading, description, actions = '') => `<div class="hero"><div><span class="eyebrow"><span class="tiny-dot"></span>${esc(eyebrow)}</span><h2>${heading}</h2><p>${esc(description)}</p></div>${actions ? `<div class="hero-actions">${actions}</div>` : ''}</div>`;
const storage = {
  get(key, session = false) { try { return (session ? sessionStorage : localStorage).getItem(key); } catch { return null; } },
  set(key, value, session = false) { try { (session ? sessionStorage : localStorage).setItem(key, value); } catch { /* Storage can be disabled. */ } },
};
const reducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)');
const S = {
  page: hasPage(location.hash.slice(1)) ? location.hash.slice(1) : 'operations',
  store: storage.get('rp_store') || 'DEMO_01', config: null, overview: null, daily: [], evidence: [],
  chartSku: '', chartDays: 28, heatDays: 7, hiddenSeries: new Set(), inventorySearch: '', inventoryFilter: 'all',
  eventSku: '', eventKind: '', eventItems: [], eventTotal: 0, eventSequence: 0,
  selectedEvidence: '', evidenceAt: null, blob: null, mediaSequence: 0, loadSequence: 0,
  agents: new Map(), healthAnswers: new Map(), healthPending: new Set(), healthMode: 'demo',
  requests: 0, loadController: null, eventController: null, mediaController: null,
  commandItems: [], commandIndex: 0, transition: null, mobileOpen: false,
};
function agentState() {
  if (!S.agents.has(S.store)) S.agents.set(S.store, {question: '', mode: S.config?.live_ready?'meta':'demo', answer: null, busy: false, error: ''});
  return S.agents.get(S.store);
}
function hydrateIcons(root = document) { $$('[data-icon]', root).forEach(el => { el.innerHTML = icon(el.dataset.icon); }); }
function announce(text) { $('#announcer').textContent = text; }
function setError(error) { $('#global-error').textContent = error.message || String(error); $('#global-error').classList.remove('hidden'); }
function clearError() { $('#global-error').classList.add('hidden'); }
function progress(delta) { S.requests = Math.max(0, S.requests + delta); $('#request-progress').classList.toggle('active', S.requests > 0); }
function toast(message, error = false) {
  const node = document.createElement('div');
  node.className = `toast${error ? ' error' : ''}`;
  node.innerHTML = `${icon(error ? 'alert' : 'check')}<span>${esc(message)}</span><button aria-label="Dismiss notification">${icon('close')}</button>`;
  $('#toast-region').append(node);
  const dismiss = () => { node.classList.add('exiting'); setTimeout(() => node.remove(), 200); };
  $('button', node).onclick = dismiss; setTimeout(dismiss, 6500);
}
/** Safe same-origin requests. Read requests have a timeout; mutations are not retried. */
async function api(path, options = {}) {
  if (!path.startsWith('/api/')) throw new Error('Only local API routes are allowed.');
  const {signal, ...requestOptions} = options;
  const headers = new Headers(requestOptions.headers || {});
  const token = storage.get('rp_token', true);
  if (token) headers.set('Authorization', `Bearer ${token}`);
  const controller = new AbortController();
  let timedOut = false;
  const onAbort = () => controller.abort();
  if (signal?.aborted) controller.abort(); else signal?.addEventListener('abort', onAbort, {once: true});
  const timeout = requestOptions.method && requestOptions.method !== 'GET' ? null : setTimeout(() => { timedOut = true; controller.abort(); }, 30000);
  progress(1);
  try {
    const response = await fetch(path, {...requestOptions, headers, signal: controller.signal, credentials: 'same-origin', cache: 'no-store'});
    if (!response.ok) {
      let detail = response.statusText;
      try { const body = await response.json(); detail = typeof body.detail === 'string' ? body.detail : JSON.stringify(body.detail || body); } catch { /* Keep HTTP message. */ }
      const error = new Error(detail || `HTTP ${response.status}`); error.status = response.status; throw error;
    }
    return response;
  } catch (error) {
    if (timedOut) throw new Error('The local API did not respond within 30 seconds. Check the server, then refresh.');
    throw error;
  } finally { if (timeout) clearTimeout(timeout); signal?.removeEventListener('abort', onAbort); progress(-1); }
}
async function json(path, options = {}) { return (await api(path, options)).json(); }
function storeQuery() { return `store_id=${encodeURIComponent(S.store)}`; }
function formatTime(value) {
  if (!value) return 'Not recorded';
  const d = new Date(value); if (Number.isNaN(d.getTime())) return String(value);
  try { return d.toLocaleString(undefined, {timeZone: S.config?.timezone || 'UTC', month:'short', day:'numeric', hour:'2-digit', minute:'2-digit'}); }
  catch { return d.toLocaleString(); }
}
function dateLabel(value) { return String(value || '').slice(5).replace('-', '/'); }
function setTheme(theme, save = true) {
  const next = theme === 'light' ? 'light' : 'dark';
  document.documentElement.dataset.theme = next;
  $('#theme-toggle').innerHTML = icon(next === 'dark' ? 'sun' : 'moon');
  $('#theme-toggle').setAttribute('aria-label', `Switch to ${next === 'dark' ? 'light' : 'dark'} theme`);
  $('meta[name="theme-color"]').content = next === 'dark' ? '#0b1018' : '#f2f5f8';
  if (save) storage.set('rp_theme', next);
}
function disposeMedia() {
  S.mediaSequence += 1; S.mediaController?.abort();
  const player = $('#player'); if (player instanceof HTMLVideoElement) player.pause();
  if (S.blob) URL.revokeObjectURL(S.blob); S.blob = null;
}
function closeMobile() {
  S.mobileOpen = false; $('#sidebar').classList.remove('mobile-open'); $('#mobile-scrim').hidden = true;
  $('#menu-toggle').setAttribute('aria-expanded', 'false'); $('#workspace').inert = false;
  $('#sidebar').inert = window.innerWidth <= 780;
}
function toggleMobile() {
  if (S.mobileOpen) { closeMobile(); $('#menu-toggle').focus(); return; }
  S.mobileOpen = true; $('#sidebar').inert = false; $('#sidebar').classList.add('mobile-open'); $('#mobile-scrim').hidden = false;
  $('#menu-toggle').setAttribute('aria-expanded', 'true'); $('#workspace').inert = true;
  $('.nav.active')?.focus();
}
function updateNavigation() {
  $$('.nav').forEach(node => { const active = node.dataset.page === S.page; node.classList.toggle('active', active); if (active) node.setAttribute('aria-current', 'page'); else node.removeAttribute('aria-current'); });
  $('#page-title').textContent = PAGES[S.page][0];
  document.title = `${PAGES[S.page][0]} | Retail Pulse`;
  const shared=['operations','flow','library','lab'].includes(S.page);
  $('.store-control').classList.toggle('hidden',shared);$('#as-of').classList.toggle('hidden',shared);
  if(S.overview){
    $('#mode-badge').textContent=shared?(S.page==='flow'?'JOINED DEMO':'RESEARCH ARCHIVE'):(S.overview.synthetic?'SYNTHETIC DEMO':'RESEARCH DATA');
    $('#dataset-notice').innerHTML=`${icon('info')}<span class="notice-label">${shared?'RESEARCH COLLECTION':'SOURCE WORKSPACE'}</span><span class="notice-copy">${esc(shared?'Shared downloaded research sources. Dates, units and identifiers belong to their publishers. Product-journey mappings and checkout are explicitly simulated.':S.overview.notice)}</span>`;
  }
}
function navigate(page, {historyUpdate = true, focus = true} = {}) {
  if (!hasPage(page)) page = 'overview';
  const changed = page !== S.page;
  if (S.page === 'timeline' && changed) { S.eventController?.abort(); S.eventSequence += 1; disposeMedia(); }
  S.page = page; closeMobile();
  if (historyUpdate && location.hash !== `#${page}`) history.pushState(null, '', `#${page}`);
  S.transition?.skipTransition();
  const update = () => { updateNavigation(); render(); if (changed) window.scrollTo({top: 0, behavior: 'instant'}); if (focus) $('#page-title').focus({preventScroll:true}); announce(`${PAGES[S.page][0]} opened`); };
  if (changed && document.startViewTransition && !reducedMotion.matches) {
    document.documentElement.classList.add('has-transitions');
    const transition = document.startViewTransition(update); S.transition = transition;
    transition.finished.catch(() => {}).finally(() => { if (S.transition === transition) { S.transition = null; document.documentElement.classList.remove('has-transitions'); } });
  } else update();
}
function emptyPage() {
  return `<section class="panel empty">${icon('layers')}<h2>Your workspace is ready.</h2><p>No analytics report is available for this store. Initialize the included offline demonstration, or use your existing imported data.</p><pre>python -m retail_pulse demo\npython -m retail_pulse serve</pre><p>The demo uses synthetic data and no paid API calls. Do not regenerate a demo over a runtime you want to preserve.</p><div class="empty-actions"><button class="button" data-action="reload">${icon('refresh')}Retry connection</button>${routeLink('inputs', 'Open data sources', 'button outline')}</div></section>`;
}
async function load({notify = false} = {}) {
  const sequence = ++S.loadSequence;
  S.loadController?.abort(); S.loadController = new AbortController();
  S.eventController?.abort(); S.eventSequence += 1; disposeMedia();
  const signal = S.loadController.signal;
  $('#refresh').classList.add('is-spinning'); $('#content').setAttribute('aria-busy', 'true'); clearError();
  try {
    const config = await json('/api/config', {signal});
    if (sequence !== S.loadSequence) return;
    if(!S.config&&config.live_ready)S.healthMode='meta';
    S.config = config;
    if (config.stores.length && !config.stores.includes(S.store)) S.store = config.default_store || config.stores[0];
    $('#store-select').innerHTML = config.stores.length ? config.stores.map(id => `<option value="${esc(id)}" ${id === S.store ? 'selected' : ''}>${esc(id)}</option>`).join('') : '<option value="">No stores registered</option>';
    $('#store-select').disabled = !config.stores.length;
    const [overview, daily, evidence] = await Promise.all([
      json(`/api/overview?${storeQuery()}`, {signal}), json(`/api/daily?${storeQuery()}`, {signal}), json(`/api/evidence?${storeQuery()}`, {signal}),
    ]);
    if (sequence !== S.loadSequence) return;
    S.overview = overview; S.daily = daily; S.evidence = evidence;
    if(config.live_ready){
      const [business,health]=await Promise.all([json(`/api/latest-agent?${storeQuery()}&role=business`),json(`/api/latest-agent?${storeQuery()}&role=health`)]);
      if(sequence!==S.loadSequence)return;
      if(business&&!agentState().answer)agentState().answer=business;
      if(health&&!S.healthAnswers.has(S.store))S.healthAnswers.set(S.store,health);
    }
    if (!overview.inventory.some(row => row.sku === S.chartSku)) S.chartSku = overview.inventory[0]?.sku || '';
    if (!evidence.some(row => row.evidence_id === S.selectedEvidence)) S.selectedEvidence = evidence.find(row => row.camera_analysis)?.evidence_id || evidence.find(row => row.media_type === 'video')?.evidence_id || evidence.find(row => row.media_type !== 'fixture')?.evidence_id || '';
    storage.set('rp_store', S.store);
    $('#mode-badge').textContent = overview.synthetic ? 'SYNTHETIC DEMO' : 'RESEARCH DATA';
    $('#sidebar-mode').textContent = overview.synthetic ? 'Synthetic scenario workspace' : 'Registered data workspace';
    $('#connection-light').className = 'connection-light connected'; $('#connection-light').title = 'Local API connected (not a live camera indicator)';
    $('#dataset-notice').innerHTML = `${icon('info')}<span class="notice-label">${overview.synthetic ? 'DEMO DATA' : 'RESEARCH'}</span><span class="notice-copy">${esc(overview.notice)} Observations, estimates and recommendations remain separate.</span>`;
    $('#dataset-notice').classList.remove('hidden');
    $('#as-of').textContent = `Report: ${formatTime(overview.as_of)} (${config.timezone})`;
    updateNavigation(); render();
    if (notify) toast('Workspace refreshed from the local API.');
  } catch (error) {
    if (error.name === 'AbortError' || sequence !== S.loadSequence) return;
    S.overview = null; S.daily = []; S.evidence = [];
    $('#connection-light').className = 'connection-light error-state'; $('#sidebar-mode').textContent = 'Connection or report unavailable';
    $('#mode-badge').textContent = 'NOT CONNECTED'; $('#dataset-notice').classList.add('hidden');
    setError(error); updateNavigation(); render();
    if (error.status === 401) toast('Enter the local bearer token in API access.', true);
  } finally {
    if (sequence === S.loadSequence) { $('#refresh').classList.remove('is-spinning'); $('#content').setAttribute('aria-busy', 'false'); }
  }
}
function kpi(label, value, unit, sub, glyph, tone = 'mint', digits = 1) {
  return `<article class="kpi" data-tone="${tone}"><div class="kpi-top"><span class="kpi-label">${esc(label)}</span><span class="kpi-icon">${icon(glyph)}</span></div><div class="kpi-value"><span ${finite(value) ? `data-count="${Number(value)}" data-digits="${digits}"` : ''}>${number(value,digits)}</span>${unit && finite(value) ? `<span class="unit">${esc(unit)}</span>` : ''}</div><div class="kpi-sub">${esc(sub)}</div><span class="kpi-edge"></span></article>`;
}
function metricCards() {
  const demand = S.overview.demand, open = sum(demand,'open_hours');
  const coverage = open > 0 ? (1 - sum(demand,'unknown_hours') / open) * 100 : null;
  const variances = S.overview.inventory.filter(row => row.status.includes('variance')).length;
  return `<div class="kpis">${kpi('Estimated unmet demand',sum(demand,'lost_demand_estimate'),'','Units / last 7 observed days','chart')}${kpi('Observed stockout time',sum(demand,'stockout_hours'),'h','Across monitored product-hours','clock','amber')}${kpi('Observation coverage',coverage,'%','Known shelf state / open product-hours','eye','blue')}${kpi('Verified stock variances',variances,'','Physical counts versus book inventory','box','purple',0)}</div>`;
}
function heatmap() {
  const dates = [...new Set(S.daily.map(row => row.date))].sort().slice(-S.heatDays);
  if (!dates.length) return '<p class="muted">No daily observations are available.</p>';
  const lookup = new Map(S.daily.map(row => [`${row.sku}|${row.date}`, row]));
  const dense = dates.length > 7;
  let html = `<div class="signal-grid" style="--days:${dates.length}"><span class="signal-day">SKU / DAY</span>${dates.map((day,i) => `<span class="signal-day">${!dense || i % 2 === 0 ? esc(dateLabel(day)) : ''}</span>`).join('')}`;
  for (const product of S.overview.inventory) {
    html += `<button class="signal-row-label" data-sku="${esc(product.sku)}" title="${esc(product.title)}"><span class="sku-bubble">${esc(product.sku)}</span><span class="signal-name">${esc(product.title)}</span></button>`;
    for (const day of dates) {
      const row = lookup.get(`${product.sku}|${day}`);
      const open = row ? Number(row.open_hours) : 0;
      const unknown = row ? Number(row.unknown_hours) : 0;
      const unavailable = row ? Number(row.unavailable_hours) : 0;
      const type = !row || open <= 0 || unknown > 0 ? 'unknown' : unavailable / open >= .75 ? 'stockout' : unavailable > 0 ? 'partial' : 'available';
      const label = row ? `${product.sku} / ${day}: available ${number(row.available_hours,2)} h; unavailable ${number(unavailable,2)} h; unknown ${number(unknown,2)} h. Open SKU details.` : `${product.sku} / ${day}: no observation. Open SKU details.`;
      html += `<button class="signal-cell ${type}" data-sku="${esc(product.sku)}" title="${esc(label)}" aria-label="${esc(label)}"></button>`;
    }
  }
  return `${html}</div><div class="signal-footer"><div class="legend compact"><span><i></i>Available</span><span><i class="unavailable"></i>Unavailable / partial</span><span><i class="unknown"></i>Unknown</span></div><p>Daily observed shelf state</p></div>`;
}
function periodButtons(kind, value, periods) {
  return `<div class="segmented" role="group" aria-label="${kind === 'heat' ? 'Shelf availability' : 'Chart'} period">${periods.map(days => `<button data-period="${days}" data-period-kind="${kind}" class="${days === value ? 'active' : ''}" aria-pressed="${days === value}">${days}D</button>`).join('')}</div>`;
}
function priorityItems() {
  const rows = S.overview.decisions.slice(0,3);
  return `<div class="priority-list">${rows.map((row,i) => `<div class="priority-item"><span class="priority-marker">0${i+1}</span><div class="priority-copy"><strong>${esc(row.title)}</strong><p>${esc(row.actions[0] || 'Review the next verified count.')}</p>${badge(row.status)}</div><button class="priority-open" data-sku="${esc(row.sku)}" aria-label="Inspect ${esc(row.sku)}">${icon('arrow')}</button></div>`).join('')}</div>`;
}
function decisionTable() {
  return panel('Replenishment & investigation queue','Advisory plans only. No orders or inventory adjustments are executed.',table(['Product','Review cycle','Target','Order units','Review state'],S.overview.decisions.map(row => `<tr>${td(productButton(row))}${td(`${number(row.review_interval_days,0)} days`)}${td(number(row.target_units,0),'num')}${td(row.recommended_order_units === null ? '<span class="muted">Review first</span>' : number(row.recommended_order_units,0),'num')}${td(badge(row.status)+`<small>${esc(row.gates.join('; '))}</small>`)}</tr>`)),`<span class="chip">${S.overview.decisions.length} PRODUCTS</span>`);
}
function sourceSalesChart(){
  const totals=new Map();for(const r of S.daily)if(finite(r.sales))totals.set(r.date,(totals.get(r.date)||0)+r.sales);
  const points=[...totals].sort((a,b)=>a[0].localeCompare(b[0]));if(!points.length)return '<p>No source sales rows.</p>';
  const max=Math.max(1,...points.map(p=>p[1])),min=Math.min(0,...points.map(p=>p[1])),w=800,h=220;
  const firstDate=Date.parse(points[0][0]),span=Math.max(1,Date.parse(points.at(-1)[0])-firstDate);const x=i=>45+(Date.parse(points[i][0])-firstDate)*(w-65)/span,y=v=>15+(max-v)/(max-min)*(h-50);
  return `<svg class="chart" viewBox="0 0 ${w} ${h}" role="img" aria-label="Recorded source sales by date"><path class="chart-line series-available" d="${points.map((p,i)=>`${i?'L':'M'}${x(i)},${y(p[1])}`).join(' ')}"/><text x="0" y="20">${number(max,1)}</text><text x="0" y="180">${number(min,1)}</text><text x="45" y="215">${esc(points[0][0])}</text><text x="690" y="215">${esc(points.at(-1)[0])}</text></svg><p class="section-note">Original signed quantities aggregated by source date. Missing dates are not filled with invented sales. ${esc(S.overview.unit)}.</p>`;
}
function realOverview(){
  const o=S.overview;const qty=o.inventory_measured?sum(o.inventory,'ledger_units'):null;
  return `${hero('REAL DATA WORKSPACE',esc(o.source),'Historical measurements from the downloaded source; original identities and dates are retained.',routeLink('agents','Ask Muse','button'))}
  <div class="kpis">${kpi('Recorded sales',o.measured_sales_total,'',o.unit+' / loaded history','chart','mint',3)}${kpi('Reported on hand',qty,'','Latest source interval per product','box')}${kpi('Source products',o.inventory.length,'','Original publisher identifiers','layers','blue',0)}${kpi('Measured stockout hours',o.availability_measured?sum(o.demand,'stockout_hours'):null,'h','Last 7 observed days; not video-derived','clock','amber')}</div>
  ${panel('Recorded sales history',o.source,sourceSalesChart())}
  ${panel('Source inventory and catalog','Source on-hand records are not independently verified physical counts.',inventoryTable())}
  ${o.availability_measured?panel('Publisher availability history','Measured hourly stock flags; not inferred from unrelated footage.',`<div id="heatmap">${heatmap()}</div>`):callout('This source does not measure shelf availability. Stockout and hidden-demand claims are withheld.')}
  <div class="toolbar">${routeLink('timeline','Inspect real camera footage','button outline')}${routeLink('health','Review ML health with Muse','button outline')}${routeLink('forecast','Inspect demand estimates','button outline')}</div>`;
}
function overview() {
  if(S.overview.real_sources)return realOverview();
  const demand = [...S.overview.demand].sort((a,b) => b.lost_demand_estimate-a.lost_demand_estimate);
  const max = Math.max(1,...demand.map(row => Number(row.lost_demand_estimate)||0));
  const bars = demand.map(row => `<div class="bar-row"><button class="text-button" data-sku="${esc(row.sku)}">${esc(row.sku)}</button><div class="bar-track"><div class="bar-fill" style="width:${clamp(Number(row.lost_demand_estimate)/max*100,0,100)}%"></div></div><span class="bar-value">${number(row.lost_demand_estimate)}</span></div>`).join('');
  const stages = [['01','layers','Ingest','Sync existing sources','inputs'],['02','video','Perceive','SAM + Muse','timeline'],['03','box','Reconcile','Temporal inventory fusion','inventory'],['04','pulse','Understand','Demand + ML health','health'],['05','target','Recommend','Human-reviewed actions','forecast'],['06','spark','Explain','Business insights agent','agents']];
  return `${hero('IN-STORE INTELLIGENCE','Every signal. <em>One clear picture.</em>','Connect shelf observations with inventory records. Find availability gaps, inspect the evidence, and review what comes next.',routeLink('agents','Ask intelligence','button'))}${metricCards()}
    <div class="grid">${panel('Shelf availability map','What happened between scans, across observed days.',`<div id="heatmap">${heatmap()}</div>`,periodButtons('heat',S.heatDays,[7,14]))}${panel('Next best actions','Prioritized by the existing decision engine.',priorityItems(),routeLink('inventory','Inspect','text-button'))}</div>
    <div class="grid">${panel('Availability through time','Observed product-hours. Unknown footage stays unknown.',chartSection(),`<select id="chart-sku" aria-label="Chart product">${skuOptions(S.chartSku)}</select>`)}${panel('Where demand may be hidden','Estimated unfulfilled units / last 7 observed days',bars+callout('Unmet demand is an estimate, not confirmed lost sales. Unknown camera periods are excluded.'),routeLink('forecast','Explore','text-button'))}</div>
    ${panel('From observation to understanding','A single workflow. Evidence preserved at every stage.',`<div class="pipeline">${stages.map(([n,g,t,sub,p])=>`<button class="pipeline-step" data-page="${p}"><span class="step-top">${n}${icon(g)}</span><strong>${t}</strong><small>${sub}</small></button>`).join('')}</div><div class="panel-foot"><span>${esc(S.overview.health.policy)}</span>${badge(`${S.overview.health.status} / ML HEALTH`,S.overview.health.status)}</div>`)}${decisionTable()}`;
}
function skuOptions(selected) { return S.overview.inventory.map(row => `<option value="${esc(row.sku)}" ${row.sku === selected ? 'selected' : ''}>SKU ${esc(row.sku)}</option>`).join(''); }
function chartRows() { return S.daily.filter(row => row.sku === S.chartSku).sort((a,b) => a.date.localeCompare(b.date)).slice(-S.chartDays); }
function chartSection() {
  const rows = chartRows();
  if (!rows.length) return '<p class="muted">No measured daily history is available for this product.</p>';
  const w=760,h=210,pad={left:34,right:14,top:16,bottom:30};
  const max = Math.max(1,...rows.map(row => Number(row.open_hours)||0));
  const x = i => pad.left + i*(w-pad.left-pad.right)/Math.max(1,rows.length-1);
  const y = value => h-pad.bottom-Number(value)/max*(h-pad.top-pad.bottom);
  const path = key => rows.map((row,i) => `${i ? 'L' : 'M'}${x(i).toFixed(2)},${y(row[key]||0).toFixed(2)}`).join(' ');
  const ticks = [...new Set([0,Math.floor((rows.length-1)/3),Math.floor(2*(rows.length-1)/3),rows.length-1])];
  const keys = ['available_hours','unavailable_hours','unknown_hours'];
  const names = ['Available','Unavailable','Unknown'];
  const css = ['available','unavailable','unknown'];
  const svg = `<svg id="availability-chart" class="chart" viewBox="0 0 ${w} ${h}" role="img" tabindex="0" aria-label="Daily shelf availability for SKU ${esc(S.chartSku)}. Use left and right arrow keys to inspect dates.">
    ${[0,.5,1].map(frac=>`<line class="grid-line" x1="${pad.left}" x2="${w-pad.right}" y1="${y(max*frac)}" y2="${y(max*frac)}"/><text x="0" y="${y(max*frac)+3}">${number(max*frac,0)}h</text>`).join('')}
    ${S.hiddenSeries.has('available_hours') ? '' : `<path class="chart-area" d="${path('available_hours')} L${x(rows.length-1)},${y(0)} L${x(0)},${y(0)}Z"/>`}
    ${keys.filter(key=>!S.hiddenSeries.has(key)).map(key=>`<path class="chart-line series-${css[keys.indexOf(key)]}" ${key==='unknown_hours'?'stroke-dasharray="4 4"':''} d="${path(key)}"/>`).join('')}
    ${ticks.map(i=>`<text x="${x(i)}" y="${h-5}" text-anchor="${i===0?'start':i===rows.length-1?'end':'middle'}">${esc(dateLabel(rows[i].date))}</text>`).join('')}
    <line id="chart-crosshair" class="chart-hover" x1="${pad.left}" x2="${pad.left}" y1="${pad.top}" y2="${h-pad.bottom}"/>
  </svg>`;
  return `<div class="chart-summary"><div><strong>${number(sum(rows,'available_hours'))}<small> h</small></strong><small>Available</small></div><div><strong>${number(sum(rows,'unavailable_hours'))}<small> h</small></strong><small>Unavailable</small></div><div><strong>${number(sum(rows,'unknown_hours'))}<small> h</small></strong><small>Unknown</small></div></div><div class="chart-wrapper">${svg}<div id="chart-tooltip" class="chart-tooltip" aria-hidden="true"></div></div><div class="panel-foot"><div class="legend compact">${keys.map((key,i)=>`<button data-series="${key}" aria-pressed="${!S.hiddenSeries.has(key)}"><i class="${css[i]}"></i>${names[i]}</button>`).join('')}</div>${periodButtons('chart',S.chartDays,[7,14,28])}</div>`;
}
function bindChart() {
  const chart = $('#availability-chart'); if (!chart) return;
  const rows = chartRows(); let activeIndex = 0;
  const update = index => {
    activeIndex = clamp(index,0,rows.length-1); const row = rows[activeIndex]; if (!row) return;
    const left = 34 + activeIndex*(760-34-14)/Math.max(1,rows.length-1);
    const crosshair = $('#chart-crosshair'); crosshair.setAttribute('x1',left); crosshair.setAttribute('x2',left); crosshair.style.opacity='1';
    const tip=$('#chart-tooltip'); tip.innerHTML=`<strong>${esc(row.date)} / SKU ${esc(S.chartSku)}</strong><span>Available <b>${number(row.available_hours,2)} h</b></span><span>Unavailable <b>${number(row.unavailable_hours,2)} h</b></span><span>Unknown <b>${number(row.unknown_hours,2)} h</b></span>`;
    tip.style.left=`${clamp(left/760*chart.clientWidth+12,0,Math.max(0,chart.clientWidth-185))}px`;tip.classList.add('visible');
  };
  const hide=()=>{ $('#chart-tooltip')?.classList.remove('visible'); if ($('#chart-crosshair')) $('#chart-crosshair').style.opacity='0'; };
  chart.addEventListener('pointermove',e=>{ const rect=chart.getBoundingClientRect(); const pos=(e.clientX-rect.left)/rect.width*760;update(Math.round((pos-34)/(760-34-14)*(rows.length-1))); });
  chart.addEventListener('pointerleave',hide); chart.addEventListener('blur',hide); chart.addEventListener('focus',()=>update(activeIndex));
  chart.addEventListener('keydown',e=>{ if (!['ArrowLeft','ArrowRight','Home','End'].includes(e.key)) return; e.preventDefault();update(e.key==='Home'?0:e.key==='End'?rows.length-1:activeIndex+(e.key==='ArrowRight'?1:-1)); const r=rows[activeIndex]; announce(`${r.date}. Available ${number(r.available_hours,2)} hours, unavailable ${number(r.unavailable_hours,2)} hours, unknown ${number(r.unknown_hours,2)} hours.`); });
}
function inventoryRows() {
  const query = S.inventorySearch.trim().toLowerCase();
  return S.overview.inventory.filter(row => (!query || `${row.sku} ${row.title}`.toLowerCase().includes(query)) && (S.inventoryFilter==='all' || (S.inventoryFilter==='variance' ? row.status.includes('variance') : row.status===S.inventoryFilter)));
}
function inventoryTable() {
  if(S.overview.real_sources){const rows=inventoryRows();return table(['Source product','Reported on hand','Stock interval start','Stock interval end','Physical audit'],rows.map(row=>`<tr>${td(productButton(row))}${td(number(row.ledger_units,2),'num')}${td(esc(row.source_start_date||'Not supplied'))}${td(esc(row.source_end_date==='9999-12-31'?'Open-ended':row.source_end_date||'Not supplied'))}${td('Not supplied')}</tr>`));}
  const rows=inventoryRows();
  return table(['Product','Book units','Physical estimate','95% model range','Variance','Finding'],rows.map(row=>`<tr>${td(productButton(row))}${td(number(row.ledger_units,0),'num')}${td(number(row.estimated_units),'num')}${td(`${number(row.lower_units,0)} - ${number(row.upper_units,0)}`,'num')}${td(row.variance_units===null?'Unverified':number(row.variance_units),'num '+(row.variance_units<0?'negative':row.variance_units>0?'positive':''))}${td(badge(row.status)+`<small>${row.verified_recently?'Recent verified count':'Count uncertainty remains'}</small>`)}</tr>`),'Inventory reconciliation')+`<p class="section-note" id="inventory-count" aria-live="polite">${rows.length} of ${S.overview.inventory.length} products. Open a product to inspect its evidence and recommended actions.</p>`;
}
function inventory() {
  return `${hero('INVENTORY TRUTH','Separate the record <em>from the reality.</em>','Compare book inventory with physical estimates. A shelf observation is not a sale, and a negative variance is not a finding of theft.')}
    ${panel('Inventory reconciliation','Verified counts anchor physical estimates. RFID reads alone provide only a lower bound.',`<div class="toolbar"><label class="search-field">${icon('search')}<input id="inventory-search" type="search" aria-label="Search products" placeholder="Search SKU or product" value="${esc(S.inventorySearch)}"></label><select id="inventory-filter" aria-label="Inventory status"><option value="all" ${S.inventoryFilter==='all'?'selected':''}>All findings</option><option value="variance" ${S.inventoryFilter==='variance'?'selected':''}>Stock variances</option><option value="aligned" ${S.inventoryFilter==='aligned'?'selected':''}>Aligned counts</option><option value="unverified" ${S.inventoryFilter==='unverified'?'selected':''}>Unverified</option></select></div><div id="inventory-table">${inventoryTable()}</div>`)}
    <div class="inventory-insights"><article class="insight-card">${icon('box')}<h3>Negative variance</h3><p>Review receiving shortages, unrecorded disposal, timing and transaction errors. An unexplained loss is not an attribution of intent.</p></article><article class="insight-card">${icon('layers')}<h3>Positive variance</h3><p>Check missed receipts, duplicate deductions, unrecorded returns and count alignment. Never silently correct the ledger.</p></article><article class="insight-card">${icon('eye')}<h3>Stock is not availability</h3><p>Products can remain in the store while missing from their assigned shelves. Store counts and shelf availability stay separate.</p></article></div>`;
}
function forecast() {
  if(S.overview.real_sources&&!S.overview.availability_measured)return `${hero('DEMAND INTELLIGENCE','Recorded sales. <em>Unknown shelf availability.</em>','This source has no measured stockout timeline. Availability-aware forecasts are withheld.')}${panel('Original recorded sales',S.overview.unit,sourceSalesChart())}${callout('Select FRESH_0 for forecasts based on real hourly sales and stock-status sequences. No demand is inferred from unrelated camera footage.')}`;
  const overview=S.overview; const benchmark=overview.benchmark;
  const tableBody=table(['Product','Recorded sales','Stockout hours','Unknown hours','Estimated unmet units','Next 7 days'],overview.demand.map(row=>`<tr>${td(`<button class="product-link" data-sku="${esc(row.sku)}"><span class="sku-bubble">${esc(row.sku)}</span></button>`)}${td(number(row.sales,S.overview.unit==='normalized sales quantity'?3:0),'num')}${td(number(row.stockout_hours),'num')}${td(number(row.unknown_hours),'num')}${td(`${number(row.lost_demand_estimate)}<small>${number(row.lost_demand_lower,0)} - ${number(row.lost_demand_upper,0)} conditional interval</small>`,'num')}${td(`${number(row.next_7d_demand)}<small>${number(row.next_7d_lower,0)} - ${number(row.next_7d_upper,0)} conditional interval</small>`,'num')}</tr>`));
  const bench=benchmark?.results?panel('Held-out simulator benchmark','Observation labels are replayed. This does not measure Muse/SAM camera accuracy.',table(['Method','Test rows','Latent-demand MAE','WAPE'],Object.entries(benchmark.results).map(([key,value])=>`<tr>${td(esc(nice(key)))}${td(number(value.rows,0),'num')}${td(number(value.mae,3),'num')}${td(finite(value.wape)?`${number(value.wape*100)}%`:'Not measured','num')}</tr>`))+`<p class="benchmark-note">${esc(benchmark.notice)}</p>`):'';
  return `${hero('DEMAND INTELLIGENCE','The demand your sales <em>cannot show.</em>','Availability-aware estimates separate observed sales from unfulfilled demand. Forecasts are not proof that a purchase would have occurred.')}${panel('Availability through time','Daily exposure / available, unavailable and unknown shelf hours.',`<div id="chart-container">${chartSection()}</div>`,`<select id="chart-sku" aria-label="Chart product">${skuOptions(S.chartSku)}</select>`)}${panel('Availability-aware demand estimates',S.overview.real_sources?`Quantities: ${S.overview.unit}. Estimates are modeled; count-based intervals are withheld for normalized sales.`:'90% conditional Poisson predictive intervals; not full model or perception uncertainty.',tableBody)}${bench}<details><summary>Model version, chronological splits and assumptions</summary><pre>${esc(JSON.stringify(overview.model,null,2))}</pre></details>`;
}
function health() {
  const h=S.overview.health; const answer=S.healthAnswers.get(S.store); const busy=S.healthPending.has(S.store);
  const action=`<select id="health-mode" aria-label="Health agent mode"><option value="demo" ${S.healthMode==='demo'?'selected':''}>Offline review</option><option value="meta" ${!S.config.live_ready?'disabled':''} ${S.healthMode==='meta'?'selected':''}>Live Muse / credits</option></select><button id="review-health" class="button" ${busy?'disabled':''}>${busy?'<span class="spinner"></span>':icon('spark')}${busy?'Reviewing':'Review model health'}</button>`;
  return `${hero('ML HEALTH STEWARD','Intelligence, <em>with guardrails.</em>','Python computes diagnostics. Muse interprets evidence and suggests checks; it cannot change thresholds, retrain models or deploy them.',action)}
    <div class="status-card ${esc(h.status.toLowerCase())}"><div class="status-emblem">${icon(h.block_order_recommendations?'alert':'shield')}</div><div><span class="eyebrow">CURRENT POLICY STATE</span><h3>${h.block_order_recommendations?'Order recommendations are blocked':'Recommendations remain advisory'}</h3><p>${esc(h.policy)}</p></div>${badge(h.status)}</div>
    <div class="health-grid">${h.metrics.map(metric=>`<article class="health-card"><div class="panel-header"><h3>${esc(metric.label)}</h3>${badge(metric.status)}</div><div class="metric-value">${number(metric.value,4)}</div><div class="detail">${esc(metric.detail)}</div><div class="footer-note">${esc(metric.id)}</div></article>`).join('')}</div>
    <div id="health-agent-result">${busy?panel('Health-agent review','A read-only request is running.',loadingAgent()):answer?panel('Health-agent interpretation','No training or deployment action was executed.',agentResult(answer)):''}</div>
    <div class="grid equal">${panel('After authorized surveillance analysis','Validated observations first. Health review second.',`<p class="muted">Muse/SAM outputs are validated before entering the database. The analytics pipeline then computes diagnostics and asks the health agent to review those metrics.</p>`)}${panel('Explicit local monitoring','The browser does not secretly start a monitoring process.',`<pre>python -m retail_pulse watch --interval 300 --agent</pre><p class="section-note">Foreground process; stop with Ctrl+C. No automatic retraining, deployment or inventory writes.</p>`)}</div>`;
}
function loadingAgent() { return '<div class="agent-loading" role="status"><div class="thinking-dots" aria-hidden="true"><i></i><i></i><i></i></div>Retrieving evidence and preparing the response.<small>No response is displayed until the API returns a validated answer.</small></div>'; }
function agentResult(result) {
  const actions=result.suggested_actions||[];const values=result.metric_values||{};const trace=result.tool_trace||[];const ids=result.evidence_ids||[];
  return `<div class="agent-result-top">${badge(result.mode==='meta'?'LIVE MUSE':'OFFLINE WALKTHROUGH',result.mode==='meta'?'pass':'neutral')}<span>${esc(result.model)}</span></div><div class="agent-answer">${esc(result.answer)}</div>
    ${actions.length?`<h3>Suggested next actions</h3>${actions.map(action=>`<div class="action-item">${icon('arrow')}<span>${esc(action)}</span></div>`).join('')}`:''}
    ${ids.length?`<div class="detail-section"><h3>Evidence references</h3><div class="detail-tags">${ids.map(id=>`<button class="button outline small" data-evidence="${esc(id)}">${icon('play')}${esc(id)}</button>`).join('')}</div></div>`:''}
    <details><summary>Retrieved metric values (${Object.keys(values).length})</summary>${table(['Metric ID','Value'],Object.entries(values).map(([key,value])=>`<tr>${td(esc(key))}${td(esc(value??'Not measured'),'num')}</tr>`))}</details>
    <details><summary>Tool trace (${trace.length} read-only calls)</summary><pre>${esc(JSON.stringify(trace,null,2))}</pre></details>
    <p class="section-note">${(result.caveats||[]).map(esc).join(' ')}</p>`;
}
function agents() {
  const a=agentState();const usage=S.overview.usage||{};
  const spent=usage.estimated_spend_or_reserve,budget=usage.budget;
  const questions=S.overview.real_sources?['What do the real inventory and recorded sales show?','What does the real camera footage show?','Which data is measured and which conclusions are estimates?','Can we trust the forecast, and what data is missing?']:['What does the real camera footage show?','Which datasets were used and what is synthetic?','Which products have the most hidden demand?','Why is SKU C unavailable even though inventory remains?','Explain the shrink and swell discrepancies.','Which replenishment visits should we reconsider?','Can we trust the demand model right now?'];
  const empty=`<div class="agent-empty"><div class="orb-outline">${icon('spark')}</div><h3>Start with a business question.</h3><p>Follow the answer back to source observations, inventory records, forecast metrics and health diagnostics.</p><span class="chip">READ-ONLY TOOLS / EVIDENCE-LINKED</span></div>`;
  return `${hero('BUSINESS INSIGHTS AGENT','Ask naturally. <em>Understand precisely.</em>','Explore inventory, availability and demand with a read-only intelligence agent. Every returned metric remains inspectable.')}
    <div class="agent-layout"><div><section class="agent-compose"><div class="agent-identity"><span class="agent-orb">${icon('spark')}</span><div><h3>Retail Pulse Intelligence</h3><p>Store-scoped insights / ${esc(S.store)}</p></div>${badge(S.config.live_ready?'MUSE READY':'OFFLINE MODE',S.config.live_ready?'pass':'neutral')}</div>
    <label class="sr-only" for="question">Your business question</label><textarea id="question" class="prompt-box" maxlength="2000" placeholder="Where is demand going unseen, and what should we do next?">${esc(a.question)}</textarea>
    <div class="agent-toolbar"><label>MODE<select id="agent-mode"><option value="demo" ${a.mode==='demo'?'selected':''}>Offline demonstration</option><option value="meta" ${!S.config.live_ready?'disabled':''} ${a.mode==='meta'?'selected':''}>Live Muse / API credits</option></select></label><span class="keyboard-hint">Ctrl + Enter</span><button id="ask-agent" class="button" ${a.busy?'disabled':''}>${a.busy?'<span class="spinner"></span>':icon('spark')}${a.busy?'Thinking':'Get insights'}</button></div>
    <p class="section-note">${a.mode==='demo'?'Offline mode is a deterministic walkthrough, not a claim that Muse processed this data.':'Live mode spends API credits. Requests start only when you submit a question.'}</p></section>
    <section class="panel" id="agent-result">${a.busy?loadingAgent():a.error?`<div class="alert error" role="alert">${esc(a.error)}</div>`:a.answer?agentResult(a.answer):empty}</section>
    ${a.answer?`<button class="button outline small" data-action="copy-answer">${icon('copy')}Copy answer</button>`:''}</div>
    <aside>${panel('Start an investigation','Choose a question to place it in the composer.',questions.map(question=>`<button class="sample-question" data-question="${esc(question)}"><span>${esc(question)}</span>${icon('arrow')}</button>`).join(''))}
    ${panel('Controlled by design','No arbitrary SQL, code execution or ERP writes.',`<div class="budget-numbers"><span>${number(spent,4)} USD used/reserved</span></div><div class="budget-line"><span style="width:${finite(spent)&&finite(budget)&&budget>0?clamp(spent/budget*100,0,100):0}%"></span></div><div class="budget-numbers"><span>${number(budget,2)} USD guard</span>${icon('shield')}</div><p class="section-note">Local estimate only; not the provider's billing limit.</p>`)}</aside></div>`;
}
async function askBusiness() {
  const a=agentState();if(a.busy) return;
  const question=($('#question')?.value||a.question).trim();
  if(question.length<3){toast('Enter a question with at least three characters.',true);$('#question')?.focus();return;}
  a.question=question;a.mode=$('#agent-mode')?.value||a.mode;a.busy=true;a.error='';
  const store=S.store;render();
  try {
    const result=await json('/api/ask',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({question,store_id:store,role:'business',mode:a.mode})});
    a.answer=result;announce('Business insights response ready.');
    if(S.store!==store||S.page!=='agents')toast(`Business response ready for ${store}.`);
  } catch(error){a.error=`No answer was accepted. ${error.message}`;toast('The agent request could not be completed.',true);}
  finally{a.busy=false;if(S.store===store&&S.page==='agents')render();}
}
async function reviewHealth() {
  const store=S.store;if(S.healthPending.has(store))return;
  const mode=$('#health-mode')?.value||'demo';S.healthMode=mode;S.healthPending.add(store);render();
  try {
    const result=await json('/api/ask',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({store_id:store,question:'Review data quality and model health. Which recommendations need to be blocked or checked?',role:'health',mode})});
    S.healthAnswers.set(store,result);toast(`Health interpretation ready for ${store}.`);
  } catch(error){setError(error);toast('Health interpretation was not completed.',true);}
  finally{S.healthPending.delete(store);if(S.store===store&&S.page==='health')render();}
}
function timeline() {
  const playable=S.evidence.filter(row=>row.media_type!=='fixture');
  const opts=playable.map(row=>`<option value="${esc(row.evidence_id)}" ${row.evidence_id===S.selectedEvidence?'selected':''}>${esc(row.evidence_id)} / ${esc(row.camera_id)}</option>`).join('');
  const first=`<div class="toolbar"><select id="video-select" aria-label="Evidence clip" ${!playable.length?'disabled':''}>${opts||'<option>No playable media</option>'}</select><button id="analyze-camera" class="button outline small" ${!S.config.live_ready?'disabled':''}>Analyze clip with Muse</button></div><div class="camera-strip"><span>${icon('video')}REGISTERED EVIDENCE</span><span>${S.evidence.find(row=>row.evidence_id===S.selectedEvidence)?.synthetic?'SYNTHETIC REPLAY':'RECORDED MEDIA'} / NOT A LIVE FEED</span></div><div id="video-holder" class="video-wrap"><div class="video-placeholder">${icon('video')}<span>${playable.length?'Loading registered media...':'Register an authorized clip or snapshot in Sources & ingestion.'}</span></div></div><p id="video-caption" class="section-note"></p>${callout('A removal is not a sale. A missing tag is not proof of loss. Unknown or occluded intervals remain unknown.')}`;
  const filters=`<div class="toolbar"><select id="event-sku" aria-label="Filter events by SKU"><option value="">All SKUs</option>${S.overview.inventory.map(row=>`<option value="${esc(row.sku)}" ${row.sku===S.eventSku?'selected':''}>SKU ${esc(row.sku)}</option>`).join('')}</select><select id="event-kind" aria-label="Filter event type"><option value="">All event types</option>${['shelf_state','misplacement','damage','restock','removal','count'].map(kind=>`<option value="${kind}" ${kind===S.eventKind?'selected':''}>${esc(nice(kind))}</option>`).join('')}</select><button id="events-load" class="button outline small">Apply</button></div><p class="section-note" id="event-count" role="status">Loading observations...</p><div id="event-list" class="timeline-scroll"></div><button class="button outline small hidden" id="events-more">Load more observations</button>`;
  return `${hero('VISUAL EVIDENCE','See the moment. <em>Inspect the evidence.</em>','Time-stamped observations stay linked to their source. Demo media uses an explicit video-to-world time mapping, not a continuous live-camera claim.')}
    <div class="grid equal">${panel('Camera evidence','Recorded clips and snapshots.',first)}${panel('Observation timeline','Recorded clips use seconds from clip start; simulated events use workspace time.',filters)}</div>`;
}
async function loadEvents(append=false) {
  if(S.page!=='timeline'||!S.overview)return;
  if(S.evidence.find(row=>row.evidence_id===S.selectedEvidence)?.camera_analysis){await loadCameraTimeline(S.selectedEvidence);return;}
  const sequence=++S.eventSequence;S.eventController?.abort();S.eventController=new AbortController();
  const store=S.store;
  if(!append)S.eventItems=[];
  const params=new URLSearchParams({store_id:store,limit:'80',offset:String(append?S.eventItems.length:0)});
  if(S.eventSku)params.set('sku',S.eventSku);if(S.eventKind)params.set('kind',S.eventKind);
  const button=$('#events-more');if(button)button.disabled=true;
  try {
    const result=await json(`/api/events?${params}`,{signal:S.eventController.signal});
    if(sequence!==S.eventSequence||S.page!=='timeline'||S.store!==store)return;
    S.eventItems=append?[...S.eventItems,...result.items]:result.items;S.eventTotal=result.total;
    $('#event-count').textContent=`Showing ${S.eventItems.length} of ${result.total} observations. ${S.config.timezone}.`;
    $('#event-list').innerHTML=S.eventItems.map(row=>`<article class="timeline-event" data-kind="${esc(row.kind)}"><div class="timeline-head"><strong>SKU ${esc(row.sku)} / ${esc(nice(row.kind))}</strong><span class="chip">${esc(row.origin)}</span></div><time class="time" datetime="${esc(row.at)}">${esc(formatTime(row.at))}</time><p>${esc(row.kind==='shelf_state'?`${nice(row.availability)}; visibility ${number(row.visibility*100)}%`:row.note||'Inspect the source for context.')}</p><div class="timeline-actions"><button class="text-button" data-evidence="${esc(row.evidence_id)}" data-at="${esc(row.at)}">${icon('play')}Inspect source</button><button class="text-button" data-sku="${esc(row.sku)}">Product details ${icon('chevron')}</button></div></article>`).join('')||'<p class="muted">No matching observations.</p>';
    $('#events-more').classList.toggle('hidden',S.eventItems.length>=result.total);
  } catch(error){if(error.name!=='AbortError'&&S.page==='timeline'&&sequence===S.eventSequence){$('#event-count').textContent='Could not load observations.';setError(error);}}
  finally{if(sequence===S.eventSequence&&$('#events-more'))$('#events-more').disabled=false;}
}
async function loadCameraTimeline(id) {
  const sequence=++S.eventSequence;S.eventController?.abort();
  $('#events-more')?.classList.add('hidden');
  for(const key of ['event-sku','event-kind','events-load'])if($('#'+key))$('#'+key).disabled=true;
  try {
    const data=await json(`/api/camera-timeline/${encodeURIComponent(id)}?store_id=${encodeURIComponent(S.store)}`);
    if(sequence!==S.eventSequence||S.page!=='timeline'||S.selectedEvidence!==id)return;
    $('#event-count').textContent=`${data.events.length} entries: ${data.muse_event_count||0} actual Muse observations, plus separately labeled publisher annotations and pixel motion. Times are clip-relative seconds.`;
    $('#event-list').innerHTML=data.events.map(row=>`<article class="timeline-event" data-start="${row.start_seconds}" data-end="${row.end_seconds}"><div class="timeline-head"><strong>${esc(row.kind)}</strong><span class="chip">${row.origin==='muse_live'?'MUSE AI':row.origin==='publisher_annotation'?'MERL LABEL':'PIXEL MOTION'}</span></div><p>${number(row.start_seconds,1)}-${number(row.end_seconds,1)} seconds</p><p>${esc(row.item_description||'')} ${esc(row.note)}${row.origin==='muse_live'?` | Visible count: ${number(row.visible_count_min,0)} to ${number(row.visible_count_max,0)} | Confidence: ${number(row.confidence,2)}`:''}</p><button class="text-button" data-clip-seek="${row.start_seconds}">${icon('play')}Play this moment</button></article>`).join('')||'<p>No observations in this clip.</p>';
  } catch(error){if(sequence===S.eventSequence&&$('#event-count'))$('#event-count').textContent=error.message;}
}
async function playEvidence(id,at=null) {
  const source=S.evidence.find(row=>row.evidence_id===id);
  if(!source||source.media_type==='fixture'){toast('This reference is a fixture or audit record, not playable surveillance footage.');if($('#video-caption'))$('#video-caption').textContent='Selected reference is a synthetic fixture or verified audit; no video claim is made.';return;}
  if(S.page!=='timeline'){S.selectedEvidence=id;S.evidenceAt=at;navigate('timeline');return;}
  S.selectedEvidence=id;S.evidenceAt=at;
  for(const key of ['event-sku','event-kind','events-load'])if($('#'+key))$('#'+key).disabled=!!source.camera_analysis;
  loadEvents();
  const strip=$('.camera-strip');if(strip)strip.innerHTML=`<span>REGISTERED EVIDENCE</span><span>${source.synthetic?'SYNTHETIC REPLAY':'REAL RECORDED FOOTAGE'} / NOT A LIVE FEED</span>`;
  S.mediaController?.abort();S.mediaController=new AbortController();const sequence=++S.mediaSequence;
  const holder=$('#video-holder');const caption=$('#video-caption');
  if (!holder || !caption) return; // A route transition will render the selected source.
  caption.textContent='Loading registered source...';
  try {
    const response=await api(`/api/media/${encodeURIComponent(id)}`,{signal:S.mediaController.signal});
    const blob=await response.blob();
    if(sequence!==S.mediaSequence||S.page!=='timeline'||!holder.isConnected)return;
    if(S.blob)URL.revokeObjectURL(S.blob);S.blob=URL.createObjectURL(blob);
    holder.innerHTML=source.media_type==='video'?'<video id="player" controls playsinline preload="metadata" aria-label="Registered evidence video"></video>':'<img id="player" alt="Registered shelf evidence">';
    const player=$('#player');
    player.addEventListener('error',()=>{caption.textContent='This browser could not decode the registered media. Inspect the source format or try another authorized clip.';},{once:true});
    if(at&&source.media_type==='video')player.addEventListener('loadedmetadata',()=>{
      const scale=Number(source.seconds_to_world)>0?Number(source.seconds_to_world):1;
      const offset=(new Date(at)-new Date(source.start_at))/1000/scale;
      const duration=finite(player.duration)?player.duration:source.duration_seconds;
      if(Number.isFinite(offset)&&finite(duration))player.currentTime=clamp(offset,0,Math.max(0,duration-.1));
    },{once:true});
    player.addEventListener('timeupdate',()=>{
      if(!source.camera_analysis)return;
      $$('#event-list [data-start]').forEach(row=>row.classList.toggle('camera-active',player.currentTime>=Number(row.dataset.start)&&player.currentTime<Number(row.dataset.end)));
    });
    player.src=S.blob;
    caption.textContent=`${source.synthetic?'Synthetic illustration':'Registered source'} | ${source.camera_id} | source start ${formatTime(source.start_at)} (${S.config.timezone}) | time scale ${number(source.seconds_to_world,2)}x`;
    if(source.camera_analysis)caption.textContent='MERL Shopping Dataset - real overhead research footage. Clip-relative timing; original capture date unknown. Separate research footage; not proof of this source workspace\'s inventory.';
    $('#video-select').value=id;
  } catch(error){if(error.name!=='AbortError'&&sequence===S.mediaSequence&&holder.isConnected){holder.innerHTML=`<div class="video-placeholder">${icon('alert')}<span>${esc(error.message)}</span></div>`;caption.textContent='No media was loaded.';}}
}
function inputs() {
  const config=S.config||{timezone:'America/Denver',max_media_mb:25,max_video_seconds:90,live_ready:false,external_media:false};
  const allowed=config.live_ready&&config.external_media;
  const sources=[['video','Surveillance','MP4, MOV, image snapshots'],['scan','RFID & barcode','Tag reads, scans, timestamps'],['database','Inventory & POS','Sales, receipts and returns'],['layers','Planogram & catalog','Product identifiers and camera zones']];
  const media=`<form id="media-form"><label class="upload-zone">${icon('upload')}<strong>Register a clip or shelf snapshot</strong><small>Authorized media only / stored by the existing local API</small><input name="file" type="file" accept=".mp4,.mov,.png,.jpg,.jpeg" required aria-label="Surveillance media file"></label><div class="form-grid"><label>Store ID<input name="store_id" value="${esc(S.store)}" required></label><label>Mapped camera ID<input name="camera_id" value="CAM_DEMO" required></label><label>Source start timestamp<input name="start_at" type="datetime-local" required></label><label>Source timezone<input name="source_timezone" value="${esc(config.timezone)}" required></label><label>Camera clock fast by (seconds)<input name="clock_offset_seconds" type="number" step="any" value="0"></label><label>Optional SAM prompt<input name="sam_prompt" placeholder="packaged snacks"></label></div><label class="check-row"><input name="analyze" type="checkbox" value="true" ${allowed?'':'disabled'}><span>Analyze with live Muse, then run the ML health agent. This sends authorized media externally and spends API credits.</span></label><button class="button" type="submit">${icon('upload')}Upload &amp; register</button></form><p class="section-note">Maximum ${config.max_media_mb} MB and ${config.max_video_seconds} seconds. Images capture an instant, not continuous availability. Live media authorization remains controlled in .env.</p><pre id="media-result" class="hidden" aria-live="polite"></pre>`;
  const imports=`<form id="import-form"><label class="upload-zone">${icon('database')}<strong>Import normalized operational data</strong><small>CSV, JSON or JSONL / existing data contracts</small><input name="file" type="file" accept=".csv,.json,.jsonl" required aria-label="Operational data file"></label><div class="form-grid"><label>Record type<select name="table">${['products','transactions','rfid_reads','barcode_scans','evidence','observations'].map(name=>`<option value="${name}">${nice(name)}</option>`).join('')}</select></label><label>Source timezone<input name="source_timezone" value="${esc(config.timezone)}" required></label></div><p class="muted">Import the catalog before related records. Invalid rows are quarantined; repeated source IDs do not duplicate stock movements.</p><button class="button outline" type="submit">${icon('check')}Validate &amp; ingest</button></form><pre id="import-result" class="hidden" aria-live="polite"></pre>${callout('Data integration is unchanged in this interface release. No external dataset, camera, ERP or company account is automatically connected.')}`;
  return `${hero('SOURCES & INGESTION','Existing infrastructure. <em>New perspective.</em>','Keep your source data, mappings and approvals under control. This release changes presentation, not your data pipeline.',S.overview?'<button id="recompute" class="button outline">'+icon('refresh')+'Recompute analytics</button>':'')}
    <div class="source-cards">${sources.map(([glyph,heading,desc])=>`<article class="source-card">${icon(glyph)}<h3>${heading}</h3><p>${desc}</p><span class="chip">SUPPORTED INPUT</span></article>`).join('')}</div>
    <div class="grid equal">${panel('Visual evidence','Local upload; external analysis is explicitly opt-in.',media)}${panel('Operational records','Validate against the existing Python schemas.',imports)}</div>
    ${panel('Clear boundaries, preserved','The interface never changes the underlying evidence.',`<div class="step"><span class="step-no">01</span><div><h3>Observation is not a transaction</h3><p>Validated Muse observations stay separate from recorded sales, receipts, returns and verified count anchors.</p></div></div><div class="step"><span class="step-no">02</span><div><h3>Numbers stay in Python</h3><p>Reconciliation, forecasting, health gates and replenishment calculations are unchanged. Agent explanations cannot alter them.</p></div></div><div class="step"><span class="step-no">03</span><div><h3>Research claims stay scoped</h3><p>Synthetic scores do not measure real-camera performance. Live Muse and SAM still require your credentials and approved media.</p></div></div>`)}`;
}
function openProduct(sku) {
  if(!S.overview)return;const row=S.overview.inventory.find(item=>item.sku===sku);if(!row)return;
  const d=S.overview.demand.find(item=>item.sku===sku);const action=S.overview.decisions.find(item=>item.sku===sku);
  $('#inspector-content').innerHTML=`<span class="chip">SKU ${esc(row.sku)} / ${esc(S.store)}</span><h2 class="inspector-title" id="inspector-title">${esc(row.title)}</h2><p class="inspector-product">Evidence-linked product detail</p>${badge(row.status)}
    <div class="detail-stat-grid"><div class="detail-stat"><small>Book inventory</small><strong>${number(row.ledger_units,0)}</strong></div><div class="detail-stat"><small>Physical estimate</small><strong>${number(row.estimated_units)}</strong></div><div class="detail-stat"><small>Unmet demand estimate</small><strong>${number(d?.lost_demand_estimate)}</strong></div><div class="detail-stat"><small>Observed stockout time</small><strong>${number(d?.stockout_hours)} h</strong></div></div>
    <div class="detail-section"><h3>What the evidence supports</h3><p>${row.verified_recently?'A recent verified count anchors the physical estimate.':'Physical count uncertainty is unresolved.'} The model range is ${number(row.lower_units,0)} - ${number(row.upper_units,0)} units.</p><p>${esc(row.caveat||'A negative variance is not evidence of theft; shelf stock and whole-store inventory are different.')}</p>${(row.recent_event_kinds||[]).length?`<div class="detail-tags">${row.recent_event_kinds.map(kind=>`<span class="chip">${esc(nice(kind))}</span>`).join('')}</div>`:''}</div>
    ${action?`<div class="detail-section"><h3>Recommended next action</h3>${badge(action.status)}<ul>${action.actions.map(text=>`<li>${esc(text)}</li>`).join('')}</ul><p>Review cycle: ${number(action.review_interval_days,0)} days. Target: ${number(action.target_units,0)} units. Suggested order: ${action.recommended_order_units===null?'review required':number(action.recommended_order_units,0)+' units'}.</p>${action.gates.length?`<p>${esc(action.gates.join('; '))}</p>`:''}</div>`:''}
    <div class="detail-section"><h3>Evidence references</h3><div class="detail-tags">${(row.evidence_ids||[]).map(id=>`<button class="button outline small" data-evidence="${esc(id)}">${icon('play')}${esc(id)}</button>`).join('')||'<p>No source references recorded.</p>'}</div></div>
    ${callout('Unmet demand is estimated. Actions require human review. Neither a removal nor a stock variance establishes intent.')}
    <div class="toolbar" style="margin-top:20px"><button class="button" data-investigate="${esc(sku)}">${icon('spark')}Ask about this product</button></div>`;
  closeMobile();$('#command-dialog').close();const dialog=$('#inspector');if(!dialog.open)dialog.showModal();
}
function openCommands() {
  closeMobile();$('#inspector').close();const dialog=$('#command-dialog');if(!dialog.open)dialog.showModal();$('#command-search').value='';S.commandIndex=0;renderCommands();$('#command-search').focus();
}
function commandItems() {
  const pages=Object.entries(PAGES).map(([id,[label,glyph]])=>({type:'page',id,label,glyph,hint:'PAGE'}));
  const products=(S.overview?.inventory||[]).map(row=>({type:'product',id:row.sku,label:`SKU ${row.sku} / ${row.title}`,glyph:'box',hint:'PRODUCT'}));
  const actions=[{type:'action',id:'reload',label:'Refresh workspace',glyph:'refresh',hint:'ACTION'},{type:'action',id:'theme',label:'Switch interface theme',glyph:'sun',hint:'ACTION'},{type:'action',id:'access',label:'Configure local API access',glyph:'key',hint:'SETTINGS'}];
  return [...pages,...products,...actions];
}
function renderCommands() {
  const query=$('#command-search').value.trim().toLowerCase();S.commandItems=commandItems().filter(item=>`${item.label} ${item.hint}`.toLowerCase().includes(query));
  S.commandIndex=clamp(S.commandIndex,0,Math.max(0,S.commandItems.length-1));
  $('#command-results').innerHTML=S.commandItems.map((item,i)=>`<button class="command-item ${i===S.commandIndex?'selected':''}" data-command="${i}">${icon(item.glyph)}<span>${esc(item.label)}</span><small>${item.hint}</small></button>`).join('')||'<div class="empty" style="padding:25px">No matching pages or products.</div>';
}
function runCommand(index) {
  const item=S.commandItems[index];if(!item)return;$('#command-dialog').close();
  if(item.type==='page')navigate(item.id);else if(item.type==='product')openProduct(item.id);else if(item.id==='reload')load({notify:true});else if(item.id==='theme')setTheme(document.documentElement.dataset.theme==='dark'?'light':'dark');else if(item.id==='access')openAccess();
}
function openAccess() { closeMobile();$('#api-token').value=storage.get('rp_token',true)||'';$('#access-dialog').showModal(); }
function animateCounters() {
  if(['operations','lab'].includes(S.page))return;
  if(reducedMotion.matches)return;
  $$('[data-count]',$('#content')).forEach(node=>{
    const value=Number(node.dataset.count),digits=Number(node.dataset.digits||1),start=performance.now();
    const step=now=>{if(!node.isConnected)return;const t=clamp((now-start)/600,0,1);node.textContent=number(value*(1-Math.pow(1-t,3)),digits);if(t<1)requestAnimationFrame(step);};
    requestAnimationFrame(step);
  });
}
function refreshChart() {
  const current=$('#availability-chart');if(!current)return;
  const container=$('#chart-container')||$('#overview-chart');
  if(container){container.innerHTML=chartSection();bindChart();}
}
function render() {
  disposeResearchMedia();
  if ($('#player')) disposeMedia();
  const content=$('#content');
  const views={overview,timeline,inventory,forecast,health,agents,inputs,flow,library,lab,operations};
  if(!S.overview&&!(S.page==='inputs'&&S.config)){content.innerHTML=emptyPage();hydrateIcons(content);content.setAttribute('aria-busy','false');return;}
  content.innerHTML=views[S.page]();content.classList.remove('page-enter');void content.offsetWidth;content.classList.add('page-enter');content.setAttribute('aria-busy','false');
  if(S.page==='overview'){
    const chart=$('#availability-chart');
    if(chart){const panelNode=chart.closest('.panel');const header=$('.panel-header',panelNode);const wrapper=document.createElement('div');wrapper.id='overview-chart';while(header.nextSibling)wrapper.append(header.nextSibling);panelNode.append(wrapper);}
  }
  hydrateIcons(content);
  $$('.kpi, .panel, .health-card, .status-card, .source-card',content).slice(0,12).forEach((node,i)=>{node.classList.add('reveal');node.style.setProperty('--delay',`${Math.min(i*25,140)}ms`);});
  animateCounters();bindChart();
  if(S.page==='timeline'){loadEvents();if(S.selectedEvidence)playEvidence(S.selectedEvidence,S.evidenceAt);}
  if(S.page==='inputs')bindForms();
  if(['flow','library','lab'].includes(S.page))bindResearch();
  if(S.page==='operations')bindOperations();
}
function bindForms() {
  for(const [id,path,target] of [['media-form','/api/upload-media','media-result'],['import-form','/api/import','import-result']]){
    const form=$('#'+id);if(!form)continue;
    form.addEventListener('submit',async event=>{
      event.preventDefault();if(form.dataset.busy==='true')return;
      const data=new FormData(form);const file=data.get('file');
      if(!(file instanceof File)||file.size===0){toast('Choose a nonempty file.',true);return;}
      if(file.size>(S.config?.max_media_mb||25)*1024*1024){toast(`File exceeds the configured ${S.config?.max_media_mb||25} MB limit.`,true);return;}
      if(data.get('analyze')==='true'&&!window.confirm('Send this authorized media to Meta for live analysis? This spends API credits.'))return;
      const output=$('#'+target),button=$('button[type=submit]',form),label=button.innerHTML;
      form.dataset.busy='true';button.disabled=true;button.innerHTML='<span class="spinner"></span>Processing';output.classList.remove('hidden');output.textContent='Processing your explicit request. No automatic retry will be attempted.';
      try{const result=await json(path,{method:'POST',body:data});if(output.isConnected)output.textContent=JSON.stringify(result,null,2);toast('Request completed. Inspect the result; refresh or recompute when appropriate.');}
      catch(error){if(output.isConnected)output.textContent=error.message;setError(error);}
      finally{delete form.dataset.busy;if(button.isConnected){button.disabled=false;button.innerHTML=label;}}
    });
  }
}
async function recompute() {
  if(!window.confirm('Recompute analytics using the existing data and model pipeline? This is not a data integration or an automatic inventory write.'))return;
  const button=$('#recompute');if(!button||button.disabled)return;const label=button.innerHTML;button.disabled=true;button.innerHTML='<span class="spinner"></span>Computing';
  try{await json(`/api/run?${storeQuery()}`,{method:'POST'});await load({notify:true});}catch(error){setError(error);}finally{if(button.isConnected){button.disabled=false;button.innerHTML=label;}}
}
function bindShell() {
  document.addEventListener('click',event=>{
    const el=event.target.closest('button,a');if(!el)return;
    if(el.dataset.clipSeek!==undefined){const player=$('#player');if(player){player.currentTime=Number(el.dataset.clipSeek);player.play().catch(()=>{});}return;}
    if(el.dataset.page){event.preventDefault();navigate(el.dataset.page);return;}
    if(el.dataset.sku){openProduct(el.dataset.sku);return;}
    if(el.dataset.evidence){$('#inspector').close();playEvidence(el.dataset.evidence,el.dataset.at||null);return;}
    if(el.dataset.investigate){$('#inspector').close();agentState().question=`Explain SKU ${el.dataset.investigate}: inventory, hidden demand, evidence and recommended actions.`;navigate('agents');return;}
    if(el.dataset.command!==undefined){runCommand(Number(el.dataset.command));return;}
    if(el.dataset.question){agentState().question=el.dataset.question;$('#question').value=el.dataset.question;$('#question').focus();return;}
    if(el.dataset.period){const days=Number(el.dataset.period);if(el.dataset.periodKind==='heat'){S.heatDays=days;$('#heatmap').innerHTML=heatmap();}else{S.chartDays=days;refreshChart();}$$(`[data-period-kind="${el.dataset.periodKind}"]`).forEach(button=>{const active=Number(button.dataset.period)===days;button.classList.toggle('active',active);button.setAttribute('aria-pressed',String(active));});return;}
    if(el.dataset.series){const key=el.dataset.series;S.hiddenSeries.has(key)?S.hiddenSeries.delete(key):S.hiddenSeries.add(key);refreshChart();return;}
    if(el.dataset.action==='reload'){load({notify:true});return;}
    if(el.dataset.action==='copy-answer'){const answer=agentState().answer;if(answer&&navigator.clipboard)navigator.clipboard.writeText(answer.answer).then(()=>toast('Answer copied.')).catch(()=>toast('Clipboard access was blocked. Select the answer text to copy.',true));else toast('Select the answer text to copy.',true);return;}
    if(el.id==='ask-agent'){askBusiness();return;}
    if(el.id==='review-health'){reviewHealth();return;}
    if(el.id==='analyze-camera'){
      const id=S.selectedEvidence,store=S.store;el.disabled=true;el.textContent='Muse is reading the clip...';
      json(`/api/analyze-camera/${encodeURIComponent(id)}?store_id=${encodeURIComponent(store)}`,{method:'POST'}).then(()=>{if(S.store===store&&S.selectedEvidence===id)loadEvents();toast('Muse video analysis complete.');}).catch(setError).finally(()=>{if(el.isConnected){el.disabled=false;el.textContent='Analyze clip with Muse';}});return;
    }
    if(el.id==='events-load'){S.eventSku=$('#event-sku').value;S.eventKind=$('#event-kind').value;loadEvents();return;}
    if(el.id==='events-more'){loadEvents(true);return;}
    if(el.id==='recompute'){recompute();return;}
  });
  document.addEventListener('input',event=>{
    const node=event.target;if(node.id==='question')agentState().question=node.value;
    if(node.id==='inventory-search'){S.inventorySearch=node.value;$('#inventory-table').innerHTML=inventoryTable();}
    if(node.id==='command-search'){S.commandIndex=0;renderCommands();}
  });
  document.addEventListener('change',event=>{
    const node=event.target;
    if(node.id==='chart-sku'){S.chartSku=node.value;refreshChart();}
    if(node.id==='inventory-filter'){S.inventoryFilter=node.value;$('#inventory-table').innerHTML=inventoryTable();}
    if(node.id==='video-select')playEvidence(node.value);
    if(node.id==='agent-mode'){agentState().mode=node.value;const note=$('.agent-compose .section-note');if(note)note.textContent=node.value==='meta'?'Live mode spends API credits. Requests start only when you submit a question.':'Offline mode is a deterministic walkthrough, not a claim that Muse processed this data.';}
    if(node.id==='health-mode')S.healthMode=node.value;
  });
  $('#command-open').onclick=openCommands;$('#access-open').onclick=openAccess;
  $('#theme-toggle').onclick=()=>setTheme(document.documentElement.dataset.theme==='dark'?'light':'dark');
  $('#refresh').onclick=()=>load({notify:true});$('#menu-toggle').onclick=toggleMobile;$('#mobile-scrim').onclick=()=>{closeMobile();$('#menu-toggle').focus();};
  $('#store-select').onchange=event=>{S.store=event.target.value;S.overview=null;S.daily=[];S.evidence=[];S.eventSku='';S.selectedEvidence='';S.evidenceAt=null;$('#inspector').close();$('#content').innerHTML='<div class="skeleton-layout"><div class="skeleton skeleton-panel"></div></div>';load();};
  $('#access-form').onsubmit=event=>{event.preventDefault();storage.set('rp_token',$('#api-token').value.trim(),true);$('#access-dialog').close();load({notify:true});};
  window.addEventListener('hashchange',()=>navigate(location.hash.slice(1),{historyUpdate:false}));
  window.addEventListener('popstate',()=>{if(S.page!==location.hash.slice(1))navigate(location.hash.slice(1),{historyUpdate:false});});
  window.addEventListener('resize',()=>{if(window.innerWidth>780&&S.mobileOpen)closeMobile();$('#sidebar').inert=window.innerWidth<=780&&!S.mobileOpen;});
  window.addEventListener('pagehide',()=>{disposeMedia();S.loadController?.abort();S.eventController?.abort();});
  document.addEventListener('keydown',event=>{
    if((event.ctrlKey||event.metaKey)&&event.key.toLowerCase()==='k'){event.preventDefault();$('#command-dialog').open?$('#command-dialog').close():openCommands();return;}
    if((event.ctrlKey||event.metaKey)&&event.key==='Enter'&&S.page==='agents'&&event.target.id==='question'){event.preventDefault();askBusiness();return;}
    if($('#command-dialog').open&&['ArrowDown','ArrowUp','Enter'].includes(event.key)){
      if(event.key==='Enter'&&event.target.closest('.dialog-header'))return;
      event.preventDefault();if(event.key==='Enter'){runCommand(S.commandIndex);return;}
      S.commandIndex=clamp(S.commandIndex+(event.key==='ArrowDown'?1:-1),0,Math.max(0,S.commandItems.length-1));
      $$('.command-item').forEach((node,i)=>node.classList.toggle('selected',i===S.commandIndex));$('.command-item.selected')?.scrollIntoView({block:'nearest'});return;
    }
    if(S.mobileOpen&&event.key==='Escape'){closeMobile();$('#menu-toggle').focus();}
    if(S.mobileOpen&&event.key==='Tab'){
      const nodes=$$('a[href], button:not(:disabled)', $('#sidebar'));const first=nodes[0],last=nodes.at(-1);
      if(event.shiftKey&&document.activeElement===first){event.preventDefault();last.focus();}else if(!event.shiftKey&&document.activeElement===last){event.preventDefault();first.focus();}
    }
  });
  $$('dialog').forEach(dialog=>dialog.addEventListener('click',event=>{if(event.target!==dialog)return;const rect=dialog.getBoundingClientRect();if(event.clientX<rect.left||event.clientX>rect.right||event.clientY<rect.top||event.clientY>rect.bottom)dialog.close();}));
}
hydrateIcons();setTheme(storage.get('rp_theme')||'dark',false);bindShell();closeMobile();updateNavigation();load();
