const api = async (path) => {
  const r = await fetch(path);
  if (!r.ok) throw new Error(`API ${path} failed`);
  return r.json();
};
const $ = (id) => document.getElementById(id);
const fmt = (v, d = 2) => (v === undefined || v === null || v === '-' ? '-' : Number(v).toLocaleString(undefined, { maximumFractionDigits: d }));
const ts = (ms) => (ms ? new Date(Number(ms)).toLocaleTimeString() : '-');

const state = {
  events: [],
  wsConnected: false,
  apiConnected: false,
  lastWsAt: 0,
  counts: { submitted: 0, filled: 0, canceled: 0 },
};

const charts = {
  equity: echarts.init($("chartEquity")),
  pnl: echarts.init($("chartPnl")),
  price: echarts.init($("chartPrice")),
  spread: echarts.init($("chartSpread")),
  position: echarts.init($("chartPosition")),
  activity: echarts.init($("chartOrderActivity")),
};

function baseChart(title, series) {
  return { backgroundColor: 'transparent', tooltip: { trigger: 'axis' }, grid: { left: 40, right: 20, top: 20, bottom: 30 }, xAxis: { type: 'time' }, yAxis: { type: 'value' }, series };
}

function renderKPIs(summary) {
  const a = summary.account || {}, m = summary.market || {}, d = summary.decision || {}, p = summary.position || {};
  const spread = (m.best_ask && m.best_bid && m.best_ask !== '-' && m.best_bid !== '-') ? Number(m.best_ask) - Number(m.best_bid) : null;
  const kpis = [
    ["Equity", a.equity], ["Balance", a.balance], ["Unrealized PnL", a.unrealized_pnl], ["Realized PnL", a.realized_pnl],
    ["Free Margin", a.free_margin], ["Free Margin %", a.free_margin_pct], ["Net Position Qty", p.qty], ["Net Position Notional", p.notional],
    ["Best Bid", m.best_bid, 'bid'], ["Best Ask", m.best_ask, 'ask'], ["Mid", m.mid], ["Spread (USDT)", spread],
    ["Spread bps", m.spread_bps], ["Net Edge bps", d.net_edge_bps], ["Decision Reason", d.reason, ''],
  ];
  $("kpiGrid").innerHTML = kpis.map(([label, value, cls]) => `<div class="kpi"><div class="label">${label}</div><div class="value ${cls || (Number(value)>0?'pos':Number(value)<0?'neg':'')}">${typeof value==='string'&&isNaN(Number(value))?value:fmt(value)}</div></div>`).join('');
}

function setBadge(id, text, mode) {
  const el = $(id); el.textContent = text; el.className = `badge ${mode}`;
}

function renderTables(summary, orders, fills) {
  $("openOrdersTable").innerHTML = '<tr><th>time</th><th>order id</th><th>side</th><th>price</th><th>qty</th><th>status</th><th>role</th></tr>' +
    (orders.length ? orders.map(o => `<tr><td>${ts(o.created_at_ms)}</td><td>${o.order_id||'-'}</td><td>${o.side||'-'}</td><td>${fmt(o.price,4)}</td><td>${fmt(o.qty,6)}</td><td>${o.status||'-'}</td><td>${o.order_role||'-'}</td></tr>`).join('') : '<tr><td colspan="7">No open orders</td></tr>');
  $("fillsTable").innerHTML = '<tr><th>time</th><th>side</th><th>price</th><th>qty</th><th>fee</th><th>pnl</th></tr>' +
    (fills.length ? fills.map(f => `<tr><td>${ts(f.ts_ms)}</td><td>${f.side||'-'}</td><td>${fmt(f.price,4)}</td><td>${fmt(f.qty,6)}</td><td>${fmt(f.fee,6)}</td><td>${fmt(f.realized_pnl,6)}</td></tr>`).join('') : '<tr><td colspan="6">No fills</td></tr>');
  const p = summary.position || {};
  const a = summary.account || {};
  const m = summary.market || {};
  $("positionSummaryTable").innerHTML = [
    ['current qty', p.qty], ['avg entry', p.avg_entry || '-'], ['mark', m.mark_price || '-'], ['unrealized pnl', a.unrealized_pnl || '-'], ['leverage', a.leverage || '-']
  ].map(([k,v])=>`<tr><th>${k}</th><td>${v}</td></tr>`).join('');
}

function renderEvents() {
  const f = $("eventFilter").value;
  const filtered = f === 'all' ? state.events : state.events.filter(e => e.event_type === f || e.type === f);
  $("eventLog").innerHTML = filtered.slice(0,200).map(e => `<div class="log-${(e.level||'info')}">[${ts(e.ts_ms)}] ${(e.event_type||e.type)} ${e.payload?JSON.stringify(e.payload):e.payload||''}</div>`).join('') || 'No events yet. Waiting for engine events...';
  const types = Array.from(new Set(state.events.map(e => e.event_type || e.type).filter(Boolean)));
  const cur = $("eventFilter").value;
  $("eventFilter").innerHTML = '<option value="all">All</option>' + types.map(t => `<option value="${t}">${t}</option>`).join('');
  $("eventFilter").value = types.includes(cur) ? cur : 'all';
}

function updateCharts(eq, pnl, price, spread, summary) {
  charts.equity.setOption(baseChart('Equity', [{ name: 'equity', type: 'line', smooth: true, data: eq.map(x => [x.ts_ms, Number(x.equity || 0)]) }]));
  charts.pnl.setOption(baseChart('PnL', [
    { name: 'realized', type: 'line', data: pnl.map(x => [x.ts_ms, Number(x.realized_pnl || 0)]) },
    { name: 'unrealized', type: 'line', data: pnl.map(x => [x.ts_ms, Number(x.unrealized_pnl || 0)]) },
  ]));
  charts.price.setOption(baseChart('Price', [
    { name: 'mid', type: 'line', data: price.map(x => [x.ts_ms, Number(x.mid || 0)]) },
    { name: 'mark', type: 'line', data: price.map(x => [x.ts_ms, Number(x.mark_price || 0)]) },
  ]));
  charts.spread.setOption(baseChart('Spread', [
    { name: 'spread_bps', type: 'line', data: spread.map(x => [x.ts_ms, Number(x.spread_bps || 0)]) },
  ]));
  const pos = Number(summary.position?.qty || 0);
  charts.position.setOption(baseChart('Position', [{ type:'line', data:[[Date.now(), pos]] }]));
  charts.activity.setOption({ xAxis:{type:'category', data:['submitted','filled','canceled']}, yAxis:{type:'value'}, series:[{type:'bar', data:[state.counts.submitted,state.counts.filled,state.counts.canceled]}] });
}

function handleRealtimeEvent(e) {
  const t = e.type || e.event_type;
  state.events.unshift(e);
  state.lastWsAt = Date.now();
  if (t === 'place_order_intent' || t === 'order_intent') state.counts.submitted += 1;
  if (t === 'order_filled' || t === 'place_order_success') state.counts.filled += 1;
  if (t === 'order_canceled') state.counts.canceled += 1;
  renderEvents();
}

async function refresh() {
  try {
    const [summary, orders, fills, events, eq, pnl, price, spread] = await Promise.all([
      api('/api/summary'), api('/api/open-orders'), api('/api/fills'), api('/api/events?limit=200'), api('/api/equity-curve'), api('/api/pnl-curve'), api('/api/price-curve'), api('/api/spread-curve')
    ]);
    state.apiConnected = true;
    const engine = summary.engine || {};
    $("symbol").textContent = engine.symbol || '-';
    $("lastHeartbeat").textContent = ts(engine.last_heartbeat_ts);
    $("lastUpdate").textContent = new Date().toLocaleTimeString();
    setBadge('engineStatusBadge', engine.status || 'WAITING', engine.status === 'RUNNING' ? 'ok' : engine.status === 'ERROR' ? 'err' : 'neutral');
    setBadge('modeBadge', (engine.mode || 'dry-run').toUpperCase(), (engine.mode || '').includes('live') ? 'err' : 'ok');
    setBadge('apiBadge', 'API OK', 'ok');
    const riskScenario = summary.risk?.scenario || 'UNKNOWN';
    setBadge('riskBadge', riskScenario, riskScenario === 'NORMAL_QUOTING' ? 'ok' : 'warn');
    renderKPIs(summary);
    renderTables(summary, orders, fills);
    state.events = events;
    renderEvents();
    updateCharts(eq.reverse(), pnl.reverse(), price.reverse(), spread.reverse(), summary);
  } catch (err) {
    state.apiConnected = false;
    setBadge('apiBadge', 'API ERROR', 'err');
  }
  const stale = (Date.now() - state.lastWsAt) > 8000;
  $("staleBanner").classList.toggle('hidden', !stale);
}

function connectWs() {
  const wsUrl = `ws://${location.host}/ws/dashboard`;
  const ws = new WebSocket(wsUrl);
  ws.onopen = () => { state.wsConnected = true; state.lastWsAt = Date.now(); setBadge('wsBadge', 'WS CONNECTED', 'ok'); };
  ws.onmessage = (evt) => { try { handleRealtimeEvent(JSON.parse(evt.data)); } catch {} };
  ws.onclose = () => { state.wsConnected = false; setBadge('wsBadge', 'WS RECONNECTING', 'warn'); setTimeout(connectWs, 1500); };
  ws.onerror = () => { setBadge('wsBadge', 'WS ERROR', 'err'); };
}

$('eventFilter').addEventListener('change', renderEvents);
connectWs();
refresh();
setInterval(refresh, 2000);
window.addEventListener('resize', () => Object.values(charts).forEach(c => c.resize()));
