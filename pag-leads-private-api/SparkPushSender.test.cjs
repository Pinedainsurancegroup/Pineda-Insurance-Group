const {test} = require('node:test');
const assert = require('node:assert/strict');
const vm = require('node:vm');
const fs = require('node:fs');
const crypto = require('node:crypto');

function sender(options = {}) {
  const token = 'test-device-token-not-a-real-credential';
  const hash = s => crypto.createHash('sha256').update(s).digest('hex');
  const props = {FIREBASE_PROJECT_ID: 'demo-pag-leads', OWNER_UID: 'owner-test-12345678',
    SPREADSHEET_ID: 'private-sheet-test-12345678', SHEET_NAME: 'Respuestas de formulario 1',
    QA_DEVICE_ID: 'device-test-12345678', PUSH_ENABLED: 'true'};
  const properties = {getProperty: k => props[k] || null, setProperty: (k, v) => {props[k] = v},
    setProperties: values => Object.assign(props, values),
    getProperties: () => ({...props}), deleteProperty: k => delete props[k]};
  const sends = [], writes = [], logs = [], triggers = [], reads = [];
  const profile = {role: {stringValue: options.role || 'owner'}, active: {booleanValue: options.active !== false},
    suspended: {booleanValue: !!options.suspended}};
  const approved = options.unapproved ? null : {fields: {enabled: {booleanValue: options.enabled !== false},
    approvedBy: {stringValue: props.OWNER_UID}, approvedTokenSha256: {stringValue: options.changedToken ? 'old-hash' : hash(token)}}};
  const sandbox = {
    console: {log: value => logs.push(value)}, PropertiesService: {getScriptProperties: () => properties},
    LockService: {getScriptLock: () => ({waitLock() {}, releaseLock() {}})},
    Utilities: {DigestAlgorithm: {SHA_256: 'sha256'}, Charset: {UTF_8: 'utf8'}, computeDigest: (_, s) => [...crypto.createHash('sha256').update(s).digest()]},
    ScriptApp: {getOAuthToken: () => 'test-short-lived-oauth', getProjectTriggers: () => triggers,
      newTrigger: handler => {
        const obj = {getHandlerFunction: () => handler, getTriggerSourceId: () => props.SPREADSHEET_ID,
          forSpreadsheet() {return obj}, onFormSubmit() {return obj}, timeBased() {return obj}, everyMinutes() {return obj}, create() {triggers.push(obj)}};
        return obj;
      }},
    UrlFetchApp: {fetch: (url, request) => {
      reads.push(url);
      assert.equal(request.headers.Authorization, 'Bearer test-short-lived-oauth');
      const response = (code, body) => ({getResponseCode: () => code, getContentText: () => JSON.stringify(body)});
      if (url.startsWith('https://fcm.googleapis.com/')) {
        const payload = JSON.parse(request.payload); sends.push(payload);
        assert.equal(payload.message.token, token);
        assert.deepEqual(Object.keys(payload.message.data).sort(), ['eventId', 'kind', 'schema']);
        assert.equal(payload.message.android.priority, 'HIGH');
        return response(options.fcmStatus || 200, {name: 'test-message'});
      }
      assert.match(url, /^https:\/\/firestore.googleapis.com\/v1\/projects\/demo-pag-leads\//);
      if (request.method === 'patch') {writes.push({url, body: JSON.parse(request.payload)});return response(200, {});}
      if (url.endsWith('/users/' + props.OWNER_UID)) return response(200, {fields: profile});
      if (url.endsWith('/preferences/operational')) return response(200, {fields: {notifications: {booleanValue: options.notifications !== false}}});
      if (url.includes('/devices/')) return response(approved ? 200 : 404, approved);
      if (url.includes('/deviceRequests/')) return response(200, {fields: {platform: {stringValue: 'android'}, fcmToken: {stringValue: token}}});
      throw new Error('Unexpected endpoint');
    }}
  };
  vm.createContext(sandbox);
  vm.runInContext(fs.readFileSync(__dirname + '/SparkPushSender.gs', 'utf8'), sandbox);
  vm.runInContext(fs.readFileSync(__dirname + '/SparkCandidateProbe.gs', 'utf8'), sandbox);
  const event = {source: {getId: () => props.SPREADSHEET_ID}, range: {getRow: () => 6,
    getSheet: () => ({getName: () => props.SHEET_NAME, getSheetId: () => 1})},
    values: ['26/09/2026 10:00:00', 'DO-NOT-SEND-PRIVATE-NAME', '555-PII']};
  return {sandbox, props, sends, writes, logs, triggers, event, profile, reads};
}

test('one actual form event sends generic data once; duplicate event is suppressed', () => {
  const a = sender();a.sandbox.pagOnRecruitmentSubmit(a.event);a.sandbox.pagOnRecruitmentSubmit(a.event);
  assert.equal(a.sends.length, 1);
  assert.equal(a.sends[0].validate_only, false);
  assert.equal(a.writes.length, 0);
  assert.doesNotMatch(JSON.stringify([a.sends, a.props, a.logs]), /DO-NOT-SEND|555-PII/);
});

test('suspended/inactive/nonowner/unapproved/changed token/disabled device/prefs all block sends', () => {
  for (const option of [{suspended: true}, {active: false}, {role: 'agent'}, {role: 'leader'},
    {unapproved: true}, {changedToken: true}, {enabled: false}, {notifications: false}]) {
    const a = sender(option);a.sandbox.pagOnRecruitmentSubmit(a.event);assert.equal(a.sends.length, 0, JSON.stringify(option));
  }
});

test('manual or wrong-source events and disabled sender produce no sends', () => {
  const a = sender();a.sandbox.pagOnRecruitmentSubmit();
  a.sandbox.pagOnRecruitmentSubmit({...a.event, source: {getId: () => 'other-sheet'}});
  a.props.PUSH_ENABLED = 'false';a.sandbox.pagOnRecruitmentSubmit(a.event);
  assert.equal(a.sends.length, 0);
});

test('temporary FCM failure retries with same event ID and rechecks suspension', () => {
  const a = sender({fcmStatus: 503});a.sandbox.pagOnRecruitmentSubmit(a.event);
  const key = Object.keys(a.props).find(k => k.startsWith('PUSH_EVENT_'));
  let record = JSON.parse(a.props[key]);assert.equal(record.state, 'PENDING');record.next = 0;a.props[key] = JSON.stringify(record);
  a.sandbox.pagRetryPendingPush();assert.equal(a.sends.length, 2);
  assert.equal(a.sends[0].message.data.eventId, a.sends[1].message.data.eventId);
  a.profile.suspended.booleanValue = true;
  record = JSON.parse(a.props[key]);record.next = 0;a.props[key] = JSON.stringify(record);
  a.sandbox.pagRetryPendingPush();assert.equal(a.sends.length, 2);
  assert.equal(JSON.parse(a.props[key]).state, 'BLOCKED');
});

test('generic invalid response does not revoke device or delete token', () => {
  const a = sender({fcmStatus: 400});a.sandbox.pagOnRecruitmentSubmit(a.event);a.sandbox.pagRetryPendingPush();
  assert.equal(a.sends.length, 1);assert.equal(a.writes.length, 0);
});

test('daily cap blocks a new send', () => {
  const a = sender();a.props.PUSH_DAILY = JSON.stringify({day: new Date().toISOString().slice(0, 10), used: 500});
  a.sandbox.pagOnRecruitmentSubmit(a.event);assert.equal(a.sends.length, 0);
});

test('approval is explicit, conditional and never overwrites an existing device', () => {
  const a = sender({unapproved: true});a.sandbox.pagApproveQaDevice();
  assert.equal(a.writes.length, 1);assert.match(a.writes[0].url, /currentDocument.exists=false/);
  assert.ok(a.writes[0].body.fields.approvedTokenSha256);assert.equal(a.writes[0].body.fields.fcmToken, undefined);
  const b = sender();assert.throws(() => b.sandbox.pagApproveQaDevice(), /ALREADY_EXISTS/);assert.equal(b.writes.length, 0);
});

test('validation sends only validate_only and trigger setup is idempotent', () => {
  const a = sender();a.sandbox.pagVerifyPushSender();assert.equal(a.sends[0].validate_only, true);
  a.sandbox.pagInstallPushTriggers();a.sandbox.pagInstallPushTriggers();assert.equal(a.triggers.length, 2);
});

test('private phone probe uses real sending checks and daily cap without creating leads', () => {
  const a = sender();a.sandbox.pagSendQaTestNotification();
  assert.equal(a.sends.length, 1);assert.equal(a.sends[0].validate_only, false);
  assert.equal(a.writes.length, 0);
  const key = Object.keys(a.props).find(k => k.startsWith('PUSH_EVENT_'));
  assert.equal(JSON.parse(a.props[key]).test, true);
  for (const option of [{suspended: true}, {unapproved: true}, {changedToken: true}, {notifications: false}]) {
    const b = sender(option);b.sandbox.pagSendQaTestNotification();assert.equal(b.sends.length, 0);
  }
  const c = sender();c.props.PUSH_ENABLED = 'false';
  assert.throws(() => c.sandbox.pagSendQaTestNotification(), /NOT_READY/);
  const d = sender();d.props.PUSH_DAILY = JSON.stringify({day: new Date().toISOString().slice(0, 10), used: 500});
  d.sandbox.pagSendQaTestNotification();assert.equal(d.sends.length, 0);
});

test('candidate probe requires separate explicit configuration and preserves QA routing', () => {
  const a = sender();
  assert.throws(() => a.sandbox.pagSendCandidateTestNotification(), /CANDIDATE_CONFIG/);
  a.props.CANDIDATE_DEVICE_ID = '12345678-1234-1234-1234-123456789abc';
  const qa = a.props.QA_DEVICE_ID;
  a.sandbox.pagVerifyCandidatePush();
  assert.equal(a.sends[0].validate_only, true);
  a.sandbox.pagSendCandidateTestNotification();
  assert.equal(a.sends[1].validate_only, false);
  assert.equal(JSON.parse(a.props.CANDIDATE_TEST_LAST).state, 'ACCEPTED');
  assert.equal(a.props.QA_DEVICE_ID, qa);
  assert.equal(Object.keys(a.props).filter(k => k.startsWith('PUSH_EVENT_')).length, 0);
  assert.equal(a.triggers.length, 0);
  assert.equal(a.writes.length, 0);
  a.props.QA_DEVICE_ID = a.props.CANDIDATE_DEVICE_ID;
  assert.throws(() => a.sandbox.pagCandidateConfig_(), /CANDIDATE_CONFIG/);
});

test('candidate approval is conditional and scoped to candidate document', () => {
  const id = '12345678-1234-1234-1234-123456789abc';
  const a = sender({unapproved: true});a.props.CANDIDATE_DEVICE_ID = id;
  a.sandbox.pagApproveCandidateDevice();
  assert.equal(a.writes.length, 1);
  assert.ok(a.writes[0].url.endsWith('/devices/' + id + '?currentDocument.exists=false'));
  assert.equal(a.writes[0].body.fields.fcmToken, undefined);
  const b = sender();b.props.CANDIDATE_DEVICE_ID = id;
  assert.throws(() => b.sandbox.pagApproveCandidateDevice(), /ALREADY_EXISTS/);
  for (const options of [{suspended:true}, {active:false}, {role:'agent'}]) {
    const c = sender({...options, unapproved:true});c.props.CANDIDATE_DEVICE_ID=id;
    assert.throws(() => c.sandbox.pagApproveCandidateDevice(), /OWNER_INACTIVE/);
    assert.equal(c.writes.length,0);
  }
});

test('candidate probe blocks denied targets and respects global quota; retries cannot target QA', () => {
  const id = '12345678-1234-1234-1234-123456789abc';
  for (const options of [{suspended:true}, {active:false}, {role:'agent'}, {unapproved:true},
    {changedToken:true}, {enabled:false}, {notifications:false}]) {
    const a=sender(options);a.props.CANDIDATE_DEVICE_ID=id;
    a.sandbox.pagSendCandidateTestNotification();assert.equal(a.sends.length,0);
  }
  const b=sender();b.props.CANDIDATE_DEVICE_ID=id;
  b.props.PUSH_DAILY=JSON.stringify({day:new Date().toISOString().slice(0,10),used:500});
  b.sandbox.pagSendCandidateTestNotification();assert.equal(b.sends.length,0);
  b.props.PUSH_ENABLED='false';
  assert.throws(() => b.sandbox.pagSendCandidateTestNotification(), /NOT_READY/);
  const c=sender({fcmStatus:503});c.props.CANDIDATE_DEVICE_ID=id;
  c.sandbox.pagSendCandidateTestNotification();c.sandbox.pagRetryPendingPush();
  assert.equal(c.sends.length,1);
  assert.equal(JSON.parse(c.props.CANDIDATE_TEST_LAST).state,'RETRY');
});

test('activation validates approved candidate and preserves QA route, old event and trigger state', () => {
  const a=sender(), id='12345678-1234-1234-1234-123456789abc', qa=a.props.QA_DEVICE_ID;
  a.props.CANDIDATE_DEVICE_ID=id;
  a.sandbox.pagOnRecruitmentSubmit(a.event);
  const oldKey=Object.keys(a.props).find(k=>k.startsWith('PUSH_EVENT_'));
  const oldRecord=a.props[oldKey];
  a.sandbox.pagActivateCandidateAutomaticPush();
  assert.equal(a.props.PUSH_PRIMARY_DEVICE_ID,id);
  assert.equal(a.props.QA_DEVICE_ID,qa);
  assert.equal(a.props[oldKey],oldRecord);
  assert.equal(a.sends.at(-1).validate_only,true);
  assert.equal(a.triggers.length,0);
  assert.equal(a.writes.length,0);
  const routeAudit=a.props.PUSH_ROUTE_LAST;
  a.sandbox.pagActivateCandidateAutomaticPush();
  assert.equal(a.props.PUSH_ROUTE_LAST,routeAudit);
  a.sandbox.pagOnRecruitmentSubmit({...a.event, values:['new timestamp','private']});
  const latest=Object.keys(a.props).filter(k=>k.startsWith('PUSH_EVENT_')).map(k=>JSON.parse(a.props[k]));
  assert.deepEqual(latest.map(x=>x.device).sort(),[qa,id].sort());
  assert.ok(a.reads.some(u=>u.endsWith('/deviceRequests/'+id)));
  assert.doesNotThrow(()=>a.sandbox.pagCandidateConfig_());
});

test('retries keep original target after route change, including legacy QA records', () => {
  const id='12345678-1234-1234-1234-123456789abc';
  for(const legacy of [false,true]) {
    const a=sender({fcmStatus:503});a.sandbox.pagOnRecruitmentSubmit(a.event);
    const key=Object.keys(a.props).find(k=>k.startsWith('PUSH_EVENT_'));
    const record=JSON.parse(a.props[key]);record.next=0;if(legacy)delete record.device;
    a.props[key]=JSON.stringify(record);a.props.PUSH_PRIMARY_DEVICE_ID=id;a.reads.length=0;
    a.sandbox.pagRetryPendingPush();
    assert.equal(a.sends.length,2);
    assert.ok(a.reads.some(u=>u.endsWith('/deviceRequests/'+a.props.QA_DEVICE_ID)));
    assert.ok(!a.reads.some(u=>u.endsWith('/deviceRequests/'+id)));
  }
  const a=sender({fcmStatus:503});a.props.PUSH_PRIMARY_DEVICE_ID=id;
  a.sandbox.pagOnRecruitmentSubmit(a.event);
  const key=Object.keys(a.props).find(k=>k.startsWith('PUSH_EVENT_'));
  const record=JSON.parse(a.props[key]);record.next=0;a.props[key]=JSON.stringify(record);
  delete a.props.PUSH_PRIMARY_DEVICE_ID;a.reads.length=0;a.sandbox.pagRetryPendingPush();
  assert.ok(a.reads.some(u=>u.endsWith('/deviceRequests/'+id)));
});

test('failed activation changes no route; explicit QA tests remain on QA after transition', () => {
  const id='12345678-1234-1234-1234-123456789abc';
  for(const options of [{suspended:true},{unapproved:true},{changedToken:true},{notifications:false},{fcmStatus:503}]) {
    const a=sender(options);a.props.CANDIDATE_DEVICE_ID=id;
    assert.throws(()=>a.sandbox.pagActivateCandidateAutomaticPush());
    assert.equal(a.props.PUSH_PRIMARY_DEVICE_ID,undefined);
    assert.equal(a.props.PUSH_ROUTE_LAST,undefined);
  }
  const a=sender();a.props.CANDIDATE_DEVICE_ID=id;a.props.PUSH_PRIMARY_DEVICE_ID=id;
  a.sandbox.pagSendQaTestNotification();
  const key=Object.keys(a.props).find(k=>k.startsWith('PUSH_EVENT_'));
  assert.equal(JSON.parse(a.props[key]).device,a.props.QA_DEVICE_ID);
  assert.ok(a.reads.some(u=>u.endsWith('/deviceRequests/'+a.props.QA_DEVICE_ID)));
});
