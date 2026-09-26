// NEW PRIVATE standalone Apps Script. No doGet/doPost, web deployment or private key.
// Do not paste into the live v1.7 API or the read-only Owner Gateway.
// OAuth runs as Juan; administrative Firestore reads use IAM, not client Rules.
// Therefore every attempt explicitly checks the active owner and approved token.
function pagPushConfig_() {
  const p = PropertiesService.getScriptProperties();
  const c = {project: p.getProperty('FIREBASE_PROJECT_ID'), owner: p.getProperty('OWNER_UID'),
    sheet: p.getProperty('SPREADSHEET_ID'), tab: p.getProperty('SHEET_NAME'),
    device: p.getProperty('QA_DEVICE_ID'), enabled: p.getProperty('PUSH_ENABLED') === 'true'};
  if (!/^[a-z][a-z0-9-]{4,62}$/.test(c.project || '') ||
      !/^[A-Za-z0-9_-]{16,128}$/.test(c.owner || '') ||
      !/^[A-Za-z0-9_-]{20,128}$/.test(c.sheet || '') || !c.tab ||
      !/^[A-Za-z0-9-]{16,80}$/.test(c.device || '')) throw new Error('PAG_PUSH_CONFIG');
  return c;
}

function pagPushHash_(text) {
  return Utilities.computeDigest(Utilities.DigestAlgorithm.SHA_256, text, Utilities.Charset.UTF_8)
    .map(b => ((b + 256) % 256).toString(16).padStart(2, '0')).join('');
}

function pagPushFirestore_(c, path, method, body, suffix) {
  const response = UrlFetchApp.fetch('https://firestore.googleapis.com/v1/projects/' + c.project +
    '/databases/(default)/documents/' + path + (suffix || ''), {
    method: method || 'get', headers: {Authorization: 'Bearer ' + ScriptApp.getOAuthToken()},
    contentType: 'application/json', ...(body ? {payload: JSON.stringify(body)} : {}), muteHttpExceptions: true
  });
  const status = response.getResponseCode();
  if (status === 404 && !method) return null;
  if (status !== 200) throw new Error('PAG_PUSH_FIRESTORE');
  return JSON.parse(response.getContentText());
}

function pagPushOwner_(c) {
  const doc = pagPushFirestore_(c, 'users/' + c.owner);
  const f = doc && doc.fields || {};
  return f.role && f.role.stringValue === 'owner' && f.active && f.active.booleanValue === true &&
    !(f.suspended && f.suspended.booleanValue === true);
}

function pagPushTarget_(c) {
  if (!pagPushOwner_(c)) return {blocked: 'OWNER_INACTIVE'};
  const pref = pagPushFirestore_(c, 'users/' + c.owner + '/preferences/operational');
  if (pref && pref.fields && pref.fields.notifications && pref.fields.notifications.booleanValue === false)
    return {blocked: 'NOTIFICATIONS_OFF'};
  const approved = pagPushFirestore_(c, 'users/' + c.owner + '/devices/' + c.device);
  const f = approved && approved.fields || {};
  if (!f.enabled || f.enabled.booleanValue !== true || !f.approvedTokenSha256 ||
      !f.approvedBy || f.approvedBy.stringValue !== c.owner) return {blocked: 'DEVICE_NOT_APPROVED'};
  const request = pagPushFirestore_(c, 'users/' + c.owner + '/deviceRequests/' + c.device);
  const r = request && request.fields || {};
  const token = r.fcmToken && r.fcmToken.stringValue;
  if (!r.platform || r.platform.stringValue !== 'android' || typeof token !== 'string' ||
      token.length < 20 || token.length > 4096 || pagPushHash_(token) !== f.approvedTokenSha256.stringValue)
    return {blocked: 'TOKEN_REQUIRES_APPROVAL'};
  return {token};
}

// Run once ONLY after Juan approves the specific QA device and OAuth permissions.
// A client deviceRequest alone never grants permission. No existing approval is overwritten.
function pagApproveQaDevice() {
  const c = pagPushConfig_();
  if (!pagPushOwner_(c)) throw new Error('PAG_PUSH_OWNER_INACTIVE');
  const path = 'users/' + c.owner + '/devices/' + c.device;
  if (pagPushFirestore_(c, path)) throw new Error('PAG_PUSH_APPROVAL_ALREADY_EXISTS');
  const request = pagPushFirestore_(c, 'users/' + c.owner + '/deviceRequests/' + c.device);
  const r = request && request.fields || {};
  const token = r.fcmToken && r.fcmToken.stringValue;
  if (!r.platform || r.platform.stringValue !== 'android' || typeof token !== 'string' ||
      token.length < 20 || token.length > 4096) throw new Error('PAG_PUSH_DEVICE_INVALID');
  pagPushFirestore_(c, path, 'patch', {fields: {
    enabled: {booleanValue: true}, platform: {stringValue: 'android'},
    approvedTokenSha256: {stringValue: pagPushHash_(token)}, approvedBy: {stringValue: c.owner},
    approvedAt: {timestampValue: new Date().toISOString()}
  }}, '?currentDocument.exists=false');
  console.log('PAG_PUSH_QA_DEVICE_APPROVED');
}

function pagPushSend_(c, target, eventId, validateOnly) {
  const response = UrlFetchApp.fetch('https://fcm.googleapis.com/v1/projects/' + c.project + '/messages:send', {
    method: 'post', contentType: 'application/json', muteHttpExceptions: true,
    headers: {Authorization: 'Bearer ' + ScriptApp.getOAuthToken()},
    payload: JSON.stringify({validate_only: !!validateOnly, message: {token: target.token,
      data: {kind: 'recruitment', eventId, schema: '1'}, android: {priority: 'HIGH', ttl: '3600s'}}})
  });
  const status = response.getResponseCode();
  if (status === 200) return 'ACCEPTED'; // FCM acceptance is not handset delivery evidence.
  if (status === 429 || status >= 500) return 'RETRY';
  return 'REJECTED'; // Never delete tokens on a generic 400/404.
}

// Only validates FCM; no notification is sent.
function pagVerifyPushSender() {
  const c = pagPushConfig_(), target = pagPushTarget_(c);
  if (target.blocked) { console.log('PAG_PUSH_' + target.blocked); return; }
  console.log('PAG_PUSH_VALIDATE_' + pagPushSend_(c, target, 'validation', true));
}

// Install only in this new project. Existing triggers and old scripts remain untouched.
function pagInstallPushTriggers() {
  const c = pagPushConfig_();
  if (!c.enabled || pagPushTarget_(c).blocked) throw new Error('PAG_PUSH_NOT_READY');
  const triggers = ScriptApp.getProjectTriggers();
  if (!triggers.some(t => t.getHandlerFunction() === 'pagOnRecruitmentSubmit' && t.getTriggerSourceId() === c.sheet))
    ScriptApp.newTrigger('pagOnRecruitmentSubmit').forSpreadsheet(c.sheet).onFormSubmit().create();
  if (!triggers.some(t => t.getHandlerFunction() === 'pagRetryPendingPush'))
    ScriptApp.newTrigger('pagRetryPendingPush').timeBased().everyMinutes(5).create();
  console.log('PAG_PUSH_TRIGGERS_READY');
}

function pagOnRecruitmentSubmit(e) {
  const c = pagPushConfig_();
  if (!c.enabled || !e || !e.range || !e.source || e.source.getId() !== c.sheet ||
      e.range.getSheet().getName() !== c.tab || e.range.getRow() < 2 || !e.values || !e.values[0]) return;
  // Only hash event coordinates/timestamp. Never store or send the prospect's answers.
  const eventId = pagPushHash_(c.sheet + '/' + e.range.getSheet().getSheetId() + '/' +
    e.range.getRow() + '/' + String(e.values[0]));
  pagPushWithLock_(() => {
    const p = PropertiesService.getScriptProperties(), key = 'PUSH_EVENT_' + eventId;
    pagPrunePushEvents_(p);
    if (p.getProperty(key)) return;
    if (Object.keys(p.getProperties()).filter(k => k.startsWith('PUSH_EVENT_')).length >= 100)
      throw new Error('PAG_PUSH_QUEUE_FULL');
    const record = {created: Date.now(), attempts: 0, state: 'PENDING', next: 0};
    p.setProperty(key, JSON.stringify(record));
    pagProcessPushEvent_(c, p, key, record);
  });
}

function pagPushWithLock_(fn) {
  const lock = LockService.getScriptLock();
  lock.waitLock(15000);
  try { fn(); } finally { lock.releaseLock(); }
}

function pagPrunePushEvents_(p) {
  const all = p.getProperties();
  Object.keys(all).filter(k => k.startsWith('PUSH_EVENT_')).forEach(k => {
    const record = JSON.parse(all[k]);
    if (Date.now() - record.created > 7 * 86400000) p.deleteProperty(k);
  });
}

function pagProcessPushEvent_(c, p, key, record) {
  if (!c.enabled || record.state !== 'PENDING' || record.next > Date.now()) return;
  if (Date.now() - record.created > 86400000 || record.attempts >= 3) {
    record.state = 'EXPIRED'; p.setProperty(key, JSON.stringify(record)); return;
  }
  try {
    const target = pagPushTarget_(c);
    if (target.blocked) {
      record.state = 'BLOCKED'; record.reason = target.blocked;
    } else {
      // Hard cap is an operational safeguard, not a billing budget. Spark stays in place.
      const day = new Date().toISOString().slice(0, 10);
      const quota = JSON.parse(p.getProperty('PUSH_DAILY') || '{}');
      const used = quota.day === day ? quota.used || 0 : 0;
      if (used >= 500) { record.state = 'LIMIT'; }
      else {
        p.setProperty('PUSH_DAILY', JSON.stringify({day, used: used + 1}));
        record.attempts++;
        record.next = Date.now() + 300000;
        p.setProperty(key, JSON.stringify(record));
        const outcome = pagPushSend_(c, target, key.slice('PUSH_EVENT_'.length), false);
        record.state = outcome === 'RETRY' ? 'PENDING' : outcome;
      }
    }
  } catch (_) {
    // Sanitized state only; never log HTTP bodies, OAuth/FCM tokens or event values.
    record.next = Date.now() + 300000;
    record.reason = 'SERVER_UNAVAILABLE';
  }
  p.setProperty(key, JSON.stringify(record));
  console.log('PAG_PUSH_' + record.state);
}

function pagRetryPendingPush() {
  const c = pagPushConfig_();
  if (!c.enabled) return;
  pagPushWithLock_(() => {
    const p = PropertiesService.getScriptProperties();
    pagPrunePushEvents_(p);
    const all = p.getProperties();
    Object.keys(all).filter(k => k.startsWith('PUSH_EVENT_') && JSON.parse(all[k]).state === 'PENDING')
      .slice(0, 5).forEach(k => pagProcessPushEvent_(c, p, k, JSON.parse(all[k])));
  });
}
