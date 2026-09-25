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
    UrlFetchApp: {fetch: (url, request) => {
      authChecks++;
      assert.match(url, /\/users\/owner-uid$/);
      assert.equal(request.headers.Authorization, 'Bearer ' + TEST_TOKEN);
      return {getResponseCode: () => profileResponse.code,
        getContentText: () => JSON.stringify(profileResponse.data || {})};
    }},
    SpreadsheetApp: {openById: () => {
      sheetReads++;
      return {getSheetByName: () => ({getDataRange: () => ({getDisplayValues: () => [
        ['Marca temporal', 'Nombre completo / Full name'], ['1/2/2026 12:00', 'Ana']
      ]})})};
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
  assert.deepEqual(g.counts(), [1, 1]);
});
