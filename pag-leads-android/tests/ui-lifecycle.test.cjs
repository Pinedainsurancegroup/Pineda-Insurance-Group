const {test} = require('node:test');
const assert = require('node:assert/strict');
const vm = require('node:vm');
const fs = require('node:fs');
const path = require('node:path');
const html = fs.readFileSync(path.join(__dirname, '../app/src/main/assets/index.html'), 'utf8');

function app({cloud=false,nativeSettings={auto:true,notify:true},initialStorage={}}={}) {
  const elements = {};
  for (const [, id] of html.matchAll(/id="([^"]+)"/g)) {
    elements[id] = {textContent: '', value: id === 'sf' ? 'all' : '', checked: false,
      hidden: false, style: {}, classList: {toggle() {}, add() {}, remove() {}}, close() {}, showModal() {}};
  }
  const requests = [], storage = new Map(Object.entries(initialStorage)), timers = new Map(), syncRequests=[], watches=[], checks=[];
  let eventSequence=0;
  let active = true, timerId = 0;
  // window.status is a native string, not the element whose id is "status".
  const sandbox = {...elements, status: '', Map, Date, Intl, console,
    document: {querySelector: selector => elements[selector.slice(1)], querySelectorAll: selector => selector==='.migrateCheck'?checks:[], addEventListener() {}},
    localStorage: {getItem: key => storage.get(key), setItem: (key, value) => storage.set(key, value)},
    setTimeout: callback => {timers.set(++timerId, callback); return timerId}, clearTimeout: id => timers.delete(id), setInterval() {},
    PAGNative: {isSessionActive: () => active, hasOwnerGateway: () => active, getBuildLabel: () => 'PAG LEADS v1.8 QA',
      getSettingsJson: () => JSON.stringify(nativeSettings), requestRecruitment: (action, id) => requests.push({action, id})},
    addEventListener() {}
  };
  if(cloud)Object.assign(sandbox.PAGNative,{getSyncUid:()=> 'test-owner',newSyncId:()=> 'synthetic-event-000'+(++eventSequence),
    watchRecruitmentState: data=>watches.push(JSON.parse(data)),requestLeadSync:(data,id)=>syncRequests.push({input:JSON.parse(data),id})});
  sandbox.window = sandbox;
  const context = vm.createContext(sandbox);
  vm.runInContext(html.match(/<script>([\s\S]*?)<\/script>/)[1], context);
  const run = code => vm.runInContext(code, context);
  const result = (index, leads, ok = true) => sandbox.PAGNativeRecruitmentResult(requests[index].id, ok, JSON.stringify({ok, leads}));
  return {sandbox, run, requests, result, elements, storage, syncRequests,watches,checks,
    cloudResult: states=>sandbox.PAGCloudState({ids:Object.keys(states),states}),
    syncResult: (n,result,ok=true)=>sandbox.PAGSyncResult(syncRequests[n].id,ok,result),
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
  a.run("openLead('test-1')"); a.elements.status.value = 'Seguimiento'; a.elements.note.value = 'Prueba local';
  await a.run('saveLead()');
  assert.equal(a.requests.length, 1);
  assert.equal(a.run('st.leads[0].status'), 'Seguimiento');
  assert.equal(JSON.parse(a.storage.get('pagov'))['test-1'].note, 'Prueba local');
});


test('editing one lead updates only its badge and note; other dialogs load their own values', async () => {
  const a = app(); const first = a.resume();
  const leads = Array.from({length: 5}, (_, i) => ({...lead, id: `PAG-A-${i + 2}`, name: `Prueba ${i + 1}`}));
  a.result(0, leads); await first;
  a.run("openLead('PAG-A-3')");
  assert.equal(a.elements.status.value, 'Nuevo');
  a.elements.status.value = 'Contactado'; a.elements.note.value = 'Nota del segundo';
  await a.run('saveLead()');
  assert.equal(a.run('st.leads[1].status'), 'Contactado');
  assert.equal(a.run("st.leads.filter(x=>x.status==='Nuevo').length"), 4);
  assert.equal((a.elements.list.innerHTML.match(/>Contactado<\/span>/g) || []).length, 1);
  assert.equal((a.elements.list.innerHTML.match(/>Nuevo<\/span>/g) || []).length, 4);
  a.run("openLead('PAG-A-4')");
  assert.equal(a.elements.status.value, 'Nuevo');
  assert.equal(a.elements.note.value, '');
  a.elements.status.value = 'Seguimiento'; a.elements.note.value = 'Nota del tercero';
  await a.run('saveLead()');
  a.run("openLead('PAG-A-3')");
  assert.equal(a.elements.status.value, 'Contactado');
  assert.equal(a.elements.note.value, 'Nota del segundo');
  const refresh = a.resume(true); a.result(1, leads); await refresh;
  assert.equal(a.run('st.leads[1].status'), 'Contactado');
  assert.equal(a.run('st.leads[2].status'), 'Seguimiento');
  assert.equal(a.run("st.leads.filter(x=>x.status==='Nuevo').length"), 3);
  assert.deepEqual(Object.keys(JSON.parse(a.storage.get('pagov'))).sort(), ['PAG-A-3', 'PAG-A-4']);
  assert.equal(a.sandbox.status, '', 'never write to the native browser status property');
});

const stableOne='r_11111111-1111-4111-8111-111111111111',stableTwo='r_22222222-2222-4222-8222-222222222222';
const cloudLeads=[{...lead,id:'PAG-A-2',stableId:stableOne},{...lead,id:'PAG-A-3',stableId:stableTwo,name:'Segundo'}];
async function cloudApp(){const a=app({cloud:true});const p=a.resume();a.result(0,cloudLeads);await p;return a}
test('cloud save waits for server, keeps a draft, changes only one lead and survives refresh',async()=>{
 const a=await cloudApp();a.run("openLead('PAG-A-2')");a.elements.status.value='Cita';a.elements.note.value='Mi nota';
 await a.run('saveLead()');assert.equal(a.syncRequests.length,0);
 a.cloudResult({[stableOne]:null,[stableTwo]:null});
 const saving=a.run('saveLead()');assert.equal(a.run('st.leads[0].status'),'Nuevo');
 assert.ok(a.storage.get('pagcloud:test-owner:drafts').includes('Mi nota'));
 a.syncResult(0,{outcome:'saved',state:{status:'Cita',note:'Mi nota',revision:1},kind:'edit'});await saving;
 assert.equal(a.run('st.leads[0].status'),'Cita');assert.equal(a.run('st.leads[1].status'),'Nuevo');
 assert.equal(a.storage.get('pagcloud:test-owner:drafts'),'{}');
 const refresh=a.resume(true);a.result(1,cloudLeads);await refresh;assert.equal(a.run('st.leads[0].note'),'Mi nota');
});
test('remote update does not erase an open draft; conflict requires another explicit save',async()=>{
 const a=await cloudApp();a.cloudResult({[stableOne]:{status:'Nuevo',note:'Old',revision:1},[stableTwo]:null});
 a.run("openLead('PAG-A-2')");a.elements.note.value='My edit';a.elements.status.value='Contactado';
 a.cloudResult({[stableOne]:{status:'Seguimiento',note:'Other phone',revision:2}});
 assert.equal(a.elements.note.value,'My edit');assert.equal(a.run('st.baseRevision'),1);
 const saving=a.run('saveLead()');a.syncResult(0,{outcome:'conflict',state:{status:'Seguimiento',note:'Other phone',revision:2}});await saving;
 assert.equal(a.elements.note.value,'My edit');assert.equal(a.run('st.baseRevision'),2);assert.equal(a.syncRequests.length,1);
 const retry=a.run('saveLead()');assert.equal(a.syncRequests[1].input.baseRevision,2);
 assert.notEqual(a.syncRequests[0].input.eventId,a.syncRequests[1].input.eventId);
 a.syncResult(1,{outcome:'saved',state:{status:'Contactado',note:'My edit',revision:3}});await retry;
});
test('migration requires a checked review, freezes source ID and preserves the old local copy',async()=>{
 const a=await cloudApp();const old=JSON.stringify({'PAG-A-2':{status:'Cita',note:'Legacy note',updatedAt:'2026-09-26'}});a.storage.set('pagov',old);
 a.cloudResult({[stableOne]:{status:'Seguimiento',note:'Newer cloud note',revision:2},[stableTwo]:null});
 a.elements.reviewLocal.onclick();await a.elements.importLocal.onclick();assert.equal(a.syncRequests.length,0);
 a.checks.push({checked:true,dataset:{index:'0'}});const importing=a.elements.importLocal.onclick();
 assert.equal(a.syncRequests[0].input.importing,true);assert.equal(a.syncRequests[0].input.leadId,stableOne);
 assert.equal(JSON.parse(a.storage.get('pagcloud:test-owner:bindings'))['PAG-A-2'],stableOne);
 a.syncResult(0,{outcome:'saved',kind:'backup',state:{status:'Seguimiento',note:'Newer cloud note',revision:2}});await importing;
 assert.equal(a.storage.get('pagov'),old);assert.equal(a.run('localCandidates().length'),0);
 assert.equal(a.run('st.leads[0].note'),'Newer cloud note');
});
test('paused cloud results cannot change visible data; pending draft survives an uncertain save',async()=>{
 const a=await cloudApp();a.cloudResult({[stableOne]:null,[stableTwo]:null});a.run("openLead('PAG-A-2')");a.elements.note.value='Pending';
 const saving=a.run('saveLead()');a.pause();await saving;
 a.syncResult(0,{outcome:'saved',state:{status:'Cita',note:'late',revision:1}});
 a.cloudResult({[stableOne]:{status:'Cita',note:'late',revision:1}});assert.notEqual(a.run('st.leads[0].note'),'late');
 assert.ok(a.storage.get('pagcloud:test-owner:drafts').includes('Pending'));
 await a.resume();assert.equal(a.run('cloudReady.size'),0);
});

test('upgrade keeps legacy configuration and notes while using the authenticated gateway and account state',async()=>{
 const old=JSON.stringify({'PAG-A-2':{status:'Seguimiento',note:'Nota local v1.7',updatedAt:'2026-09-25T22:37:00Z'}});
 const settings={url:'https://example.invalid/legacy',tok:'synthetic-upgrade-only',auto:false,notify:true};
 const a=app({cloud:true,nativeSettings:settings,initialStorage:{pagov:old,pagset12:JSON.stringify(settings)}});
 const first=a.resume();assert.deepEqual(a.requests.map(x=>x.action),['list']);a.result(0,cloudLeads);await first;
 assert.deepEqual(JSON.parse(a.storage.get('pagset12')),settings);
 assert.equal(a.storage.get('pagov'),old);
 a.cloudResult({[stableOne]:{status:'Completado',note:'Nota actual de la cuenta',revision:4},[stableTwo]:null});
 assert.equal(a.run('st.leads[0].note'),'Nota actual de la cuenta');
 assert.equal(a.run('st.leads[0].status'),'Completado');
 assert.equal(a.run('localCandidates().length'),1);
 assert.equal(a.storage.get('pagov'),old,'old local note must stay available for reviewed backup');
 a.elements.reviewLocal.onclick();assert.equal(a.syncRequests.length,0,'opening review must not import automatically');
});
