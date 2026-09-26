const test = require('node:test');
const assert = require('node:assert/strict');
const vm = require('node:vm');
const fs = require('node:fs');
const TEST_TOKEN = 'test-token-' + 'x'.repeat(120);

function build(profileResponse) {
  let sheetReads = 0, authChecks = 0;
  const context = vm.createContext({
    ContentService: {MimeType: {JSON: 'json'}, createTextOutput: text => ({
      text, setMimeType() { return this; }
    })},
    PropertiesService: {getScriptProperties: () => ({getProperty: key => ({
      OWNER_UID: 'owner-uid', SPREADSHEET_ID: 'sheet-id', SHEET_NAME: 'Answers'
    })[key]})},
    ScriptApp: {getOAuthToken: () => 'read-only-oauth-token'},
    UrlFetchApp: {fetch: (url, request) => {
      if (url.includes('firestore.googleapis.com')) {
        authChecks++;
        assert.match(url, /\/users\/owner-uid$/);
        assert.equal(request.headers.Authorization, 'Bearer ' + TEST_TOKEN);
        return {getResponseCode: () => profileResponse.code,
          getContentText: () => JSON.stringify(profileResponse.data || {})};
      }
      sheetReads++;
      assert.match(url, /sheets.googleapis.com\/v4\/spreadsheets\/sheet-id\/values\//);
      assert.equal(request.headers.Authorization, 'Bearer read-only-oauth-token');
      return {getResponseCode: () => 200, getContentText: () => JSON.stringify({values: [
        ['Marca temporal', 'Nombre completo / Full name'], ['21/09/2026 19:30:09', 'Ana']
      ]})};
    }}
  });
  vm.runInContext(fs.readFileSync(__dirname + '/SparkOwnerGateway.gs', 'utf8'), context);
  return {call: (action, idToken = TEST_TOKEN) => JSON.parse(context.doPost({postData: {
    contents: JSON.stringify({action, idToken})
  }}).text), counts: () => [authChecks, sheetReads]};
}

test('denies missing ID token before reading the private Sheet', () => {
  const g = build({code: 200});
  assert.equal(g.call('list', '').ok, false);
  assert.deepEqual(g.counts(), [0, 0]);
});

test('denies suspended, agent and rejected Firebase sessions before reading the Sheet', () => {
  for (const p of [
    {code: 403},
    {code: 200, data: {fields: {role: {stringValue: 'agent'}, active: {booleanValue: true}}}},
    {code: 200, data: {fields: {role: {stringValue: 'owner'}, active: {booleanValue: true}, suspended: {booleanValue: true}}}}
  ]) {
    const g = build(p);
    assert.equal(g.call('list').ok, false);
    assert.deepEqual(g.counts(), [1, 0]);
  }
});

test('active owner gets only recruitment records after Firebase rule check', () => {
  const g = build({code: 200, data: {fields: {role: {stringValue: 'owner'}, active: {booleanValue: true}}}});
  const output = g.call('list');
  assert.equal(output.ok, true);
  assert.equal(output.leads.length, 1);
  assert.equal(output.leads[0].type, 'agent');
  assert.equal(output.leads[0].createdAt, '2026-09-21T19:30:09');
  assert.deepEqual(g.counts(), [1, 1]);
});

test('permanent IDs survive reordering; duplicate or missing IDs disable sync only', () => {
  const c = vm.createContext({});
  vm.runInContext(fs.readFileSync(__dirname + '/SparkOwnerGateway.gs', 'utf8'), c);
  const h = ['Marca temporal','Nombre completo / Full name','PAG_LEAD_ID'];
  const a = ['26/09/2026 00:00:00','Synthetic A','r_11111111-1111-4111-8111-111111111111'];
  const b = ['26/09/2026 00:01:00','Synthetic B','r_22222222-2222-4222-8222-222222222222'];
  const first = c.pagRecruitmentRows_([h,a,b]), reversed = c.pagRecruitmentRows_([h,b,a]);
  assert.equal(first[0].stableId, reversed[1].stableId);
  assert.equal(first[0].id, 'PAG-A-2');
  assert.equal(reversed[1].id, 'PAG-A-3');
  const bad = c.pagRecruitmentRows_([h,a,[...b.slice(0,2),a[2]],['','Synthetic C','']]);
  assert.equal(bad.length, 3);
  assert.ok(bad.every(x => x.stableId === ''));
});
