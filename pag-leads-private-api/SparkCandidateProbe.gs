// Private, manually invoked RC probe. Does not change the QA sender or its triggers.
// Set CANDIDATE_DEVICE_ID only after reviewing the owner's new installation.
function pagCandidateConfig_() {
  const c = pagPushConfig_();
  const id = PropertiesService.getScriptProperties().getProperty('CANDIDATE_DEVICE_ID');
  if (!/^[a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12}$/.test(id || '') ||
      id === c.qaDevice) throw new Error('PAG_CANDIDATE_CONFIG');
  return Object.assign({}, c, {device: id});
}

// Administrative approval of this reviewed installation, never an auto-approval.
function pagApproveCandidateDevice() {
  const c = pagCandidateConfig_();
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
  console.log('PAG_CANDIDATE_DEVICE_APPROVED');
}

function pagVerifyCandidatePush() {
  const c = pagCandidateConfig_();
  if (!c.enabled) throw new Error('PAG_PUSH_NOT_READY');
  const target = pagPushTarget_(c);
  if (target.blocked) { console.log('PAG_CANDIDATE_' + target.blocked); return; }
  console.log('PAG_CANDIDATE_VALIDATE_' + pagPushSend_(c, target, 'candidate-validation', true));
}

// One attempt only; not placed in the QA retry queue (which has a different target).
// Uses the same active-owner, preferences, approval/hash and global daily cap checks.
// A generic notice creates no lead, edits no sheet and grants no data access.
function pagSendCandidateTestNotification() {
  const c = pagCandidateConfig_();
  if (!c.enabled) throw new Error('PAG_PUSH_NOT_READY');
  pagPushWithLock_(() => {
    const target = pagPushTarget_(c);
    if (target.blocked) { console.log('PAG_CANDIDATE_' + target.blocked); return; }
    const p = PropertiesService.getScriptProperties();
    const day = new Date().toISOString().slice(0, 10);
    const quota = JSON.parse(p.getProperty('PUSH_DAILY') || '{}');
    const used = quota.day === day ? quota.used || 0 : 0;
    if (used >= 500) { console.log('PAG_CANDIDATE_LIMIT'); return; }
    const eventId = pagPushHash_('CANDIDATE_TEST/' + c.device + '/' + Date.now());
    p.setProperty('PUSH_DAILY', JSON.stringify({day, used: used + 1}));
    const record = {created: Date.now(), eventId, state: 'ATTEMPTED', test: true};
    p.setProperty('CANDIDATE_TEST_LAST', JSON.stringify(record));
    try { record.state = pagPushSend_(c, target, eventId, false); }
    catch (_) { record.state = 'SERVER_UNAVAILABLE'; }
    p.setProperty('CANDIDATE_TEST_LAST', JSON.stringify(record));
    console.log('PAG_CANDIDATE_TEST_' + record.state);
  });
}

// Explicit transition only after Juan verifies RC delivery and app behavior.
// Retains the QA identifier/approval and never changes triggers or pending targets.
function pagActivateCandidateAutomaticPush() {
  pagPushWithLock_(() => {
    const c = pagCandidateConfig_();
    if (!c.enabled) throw new Error('PAG_PUSH_NOT_READY');
    const target = pagPushTarget_(c);
    if (target.blocked) throw new Error('PAG_CANDIDATE_' + target.blocked);
    if (pagPushSend_(c, target, 'candidate-route-validation', true) !== 'ACCEPTED')
      throw new Error('PAG_CANDIDATE_ROUTE_VALIDATION_FAILED');
    const p = PropertiesService.getScriptProperties();
    const previous = p.getProperty('PUSH_PRIMARY_DEVICE_ID') || c.qaDevice;
    if (previous !== c.device) p.setProperties({
      PUSH_PRIMARY_DEVICE_ID: c.device,
      PUSH_ROUTE_LAST: JSON.stringify({at: new Date().toISOString(), previous, current: c.device})
    });
    console.log('PAG_CANDIDATE_AUTOMATIC_ROUTE_READY');
  });
}
