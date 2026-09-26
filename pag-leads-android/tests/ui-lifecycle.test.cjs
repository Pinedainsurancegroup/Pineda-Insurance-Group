const {test} = require('node:test');
const assert = require('node:assert/strict');
const vm = require('node:vm');
const fs = require('node:fs');
const path = require('node:path');
const html = fs.readFileSync(path.join(__dirname, '../app/src/main/assets/index.html'), 'utf8');

function app() {
  const elements = {};
  for (const [, id] of html.matchAll(/id="([^"]+)"/g)) {
    elements[id] = {textContent: '', value: id === 'sf' ? 'all' : '', checked: false,
      hidden: false, style: {}, classList: {toggle() {}, add() {}, remove() {}}, close() {}, showModal() {}};
  }
  const requests = [], storage = new Map(), timers = new Map();
  let active = true, timerId = 0;
  const sandbox = {...elements, Map, Date, Intl, console,
    document: {querySelector: selector => elements[selector.slice(1)], querySelectorAll: () => [], addEventListener() {}},
    localStorage: {getItem: key => storage.get(key), setItem: (key, value) => storage.set(key, value)},
    setTimeout: callback => {timers.set(++timerId, callback); return timerId}, clearTimeout: id => timers.delete(id), setInterval() {},
    PAGNative: {isSessionActive: () => active, hasOwnerGateway: () => active, getBuildLabel: () => 'PAG LEADS v1.8 QA',
      getSettingsJson: () => '{"auto":true,"notify":true}', requestRecruitment: (action, id) => requests.push({action, id})},
    addEventListener() {}
  };
  sandbox.window = sandbox;
  const context = vm.createContext(sandbox);
  vm.runInContext(html.match(/<script>([\s\S]*?)<\/script>/)[1], context);
  const run = code => vm.runInContext(code, context);
  const result = (index, leads, ok = true) => sandbox.PAGNativeRecruitmentResult(requests[index].id, ok, JSON.stringify({ok, leads}));
  return {sandbox, run, requests, result, elements, storage,
    pause: () => {active = false; sandbox.PAGSuspend()}, resume: force => {active = true; return sandbox.PAGResume(force)}};
}
const lead = {id: 'test-1', type: 'agent', name: 'Prueba QA', status: 'Nuevo', createdAt: '2026-09-25T22:37:00'};

test('first load makes one authenticated list request; repeated startup coalesces', async () => {
  const a = app();
  assert.equal(a.requests.length, 0, 'native startup waits until the permission gate resumes');
  const first = a.resume(); a.resume();
  assert.deepEqual(a.requests.map(x => x.action), ['list']);
  assert.equal(a.elements.empty.textContent, 'Cargando leads…');
  a.result(0, [lead]); await first;
  assert.equal(a.elements.s1.textContent, 1);
});

test('switching apps preserves leads, filters and detail; returning does not refetch a fresh list', async () => {
  const a = app(); const first = a.resume(); a.result(0, [lead]); await first;
  a.elements.q.value = 'Prueba'; a.run("st.type='all';st.sel=st.leads[0]");
  a.pause(); await a.resume();
  assert.equal(a.requests.length, 1);
  assert.equal(a.run('st.leads.length'), 1);
  assert.equal(a.run('st.type'), 'all');
  assert.equal(a.run('st.sel.id'), 'test-1');
  assert.equal(a.elements.q.value, 'Prueba');
});

test('pause cancels pending work and rejects late data from the previous foreground session', async () => {
  const a = app(); const old = a.resume(); a.pause(); await old;
  const current = a.resume();
  a.result(0, [lead]);
  assert.equal(a.run('st.leads.length'), 0);
  a.result(1, [{...lead, id: 'current'}]); await current;
  assert.equal(a.run('st.leads[0].id'), 'current');
});

test('failed refresh retains the last successful list and exposes stale status', async () => {
  const a = app(); const first = a.resume(); a.result(0, [lead]); await first;
  const refresh = a.resume(true); a.result(1, [], false); await refresh;
  assert.equal(a.run('st.leads.length'), 1);
  assert.match(a.elements.sync.textContent, /última carga/);
});

test('local note/status edits update immediately without another gateway round trip', async () => {
  const a = app(); const first = a.resume(); a.result(0, [lead]); await first;
  a.run('st.sel=st.leads[0]'); a.elements.status.value = 'Seguimiento'; a.elements.note.value = 'Prueba local';
  await a.run('saveLead()');
  assert.equal(a.requests.length, 1);
  assert.equal(a.run('st.leads[0].status'), 'Seguimiento');
  assert.equal(JSON.parse(a.storage.get('pagov'))['test-1'].note, 'Prueba local');
});
