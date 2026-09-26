// Add this file only to the existing private Push Sender Spark project.
// Uses its already approved scopes and helpers; does not change its FCM handlers.
const PAG_ID_HEADER = 'PAG_LEAD_ID';
function pagIdentityPlan_(values) {
  const headers = values[0] || [];
  if (headers.filter(x => x === PAG_ID_HEADER).length > 1) throw new Error('PAG_ID_DUPLICATE_HEADER');
  const col = headers.indexOf(PAG_ID_HEADER), seen = new Set(), rows = [];
  const name = headers.indexOf('Nombre completo / Full name');
  const phone = headers.indexOf('Número de teléfono / Phone number');
  const email = headers.indexOf('Correo electrónico / Email address');
  if (name < 0 || phone < 0 || email < 0 || headers[0] !== 'Marca temporal') throw new Error('PAG_ID_SOURCE_HEADERS');
  values.slice(1).forEach((r, n) => {
    if (!r[name] && !r[phone] && !r[email]) return;
    const id = col < 0 ? '' : String(r[col] || '');
    if (id && (!/^r_[a-f0-9-]{36}$/.test(id) || seen.has(id))) throw new Error('PAG_ID_INVALID_OR_DUPLICATE');
    if (id) seen.add(id);
    rows.push({row: n + 2, id});
  });
  if (rows.length > 5000) throw new Error('PAG_ID_REVIEW_CAPACITY');
  return {column: (col < 0 ? headers.length : col) + 1, newColumn: col < 0, rows};
}
function pagIdentityContext_() {
  const c = pagPushConfig_();
  if (!pagPushOwner_(c)) throw new Error('PAG_ID_OWNER_INACTIVE');
  const sheet = SpreadsheetApp.openById(c.sheet).getSheetByName(c.tab);
  if (!sheet) throw new Error('PAG_ID_SOURCE_MISSING');
  return {c, sheet};
}
// Read-only preflight: no names, answers or tokens in the execution log.
function pagInspectRecruitmentIdentity() {
  const {sheet} = pagIdentityContext_(), p = pagIdentityPlan_(sheet.getDataRange().getDisplayValues());
  console.log(JSON.stringify({check: 'PAG_ID_PREFLIGHT', leads: p.rows.length,
    missing: p.rows.filter(r => !r.id).length, column: p.column, addHeader: p.newColumn}));
}
function pagRegisterSource_(c, id) {
  const path = 'recruitmentSources/' + id, existing = pagPushFirestore_(c, path);
  const sourceHash = pagPushHash_(c.sheet + '/' + c.tab);
  if (existing) {
    const f = existing.fields || {};
    if (!f.enabled || f.enabled.booleanValue !== true || !f.sourceKeyHash ||
        f.sourceKeyHash.stringValue !== sourceHash) throw new Error('PAG_ID_REGISTRY_REVIEW');
    return;
  }
  pagPushFirestore_(c, path, 'patch', {fields: {enabled: {booleanValue: true},
    sourceKeyHash: {stringValue: sourceHash}, createdAt: {timestampValue: new Date().toISOString()}}},
    '?currentDocument.exists=false');
}
// Only fills blank identifiers in an appended column; never rewrites source answers.
// Existing IDs are validated before any mutation and never regenerated.
function pagPrepareRecruitmentIdentity() { pagApplyRecruitmentIdentity_(null); }
function pagApplyRecruitmentIdentity_(onlyRow) {
  pagPushWithLock_(() => {
    const {c, sheet} = pagIdentityContext_(), p = pagIdentityPlan_(sheet.getDataRange().getDisplayValues());
    if (p.column > sheet.getMaxColumns()) throw new Error('PAG_ID_NO_FREE_COLUMN');
    if (p.newColumn) sheet.getRange(1, p.column).setValue(PAG_ID_HEADER);
    let created = 0; const allocated = new Set(p.rows.map(r => r.id).filter(Boolean));
    p.rows.filter(r => onlyRow === null || r.row === onlyRow).forEach(r => {
      let id = r.id;
      if (!id) {
        const cell = sheet.getRange(r.row, p.column);
        if (cell.getValue()) throw new Error('PAG_ID_CONCURRENT_EDIT');
        id = 'r_' + Utilities.getUuid().toLowerCase();
        if (allocated.has(id)) throw new Error('PAG_ID_COLLISION');
        allocated.add(id);
        cell.setValue(id); created++;
      }
      pagRegisterSource_(c, id);
    });
    console.log(JSON.stringify({check: 'PAG_ID_READY', leads: p.rows.length, created}));
  });
}
// An independent trigger. Failures cannot prevent the existing notification handler.
function pagAssignRecruitmentIdentity(e) {
  const c = pagPushConfig_();
  if (!e || !e.range || !e.source || e.source.getId() !== c.sheet ||
      e.range.getSheet().getName() !== c.tab || e.range.getRow() < 2) return;
  pagApplyRecruitmentIdentity_(e.range.getRow());
}
function pagInstallIdentityTrigger() {
  const c = pagPushConfig_();
  if (!pagPushOwner_(c)) throw new Error('PAG_ID_OWNER_INACTIVE');
  if (!ScriptApp.getProjectTriggers().some(t => t.getHandlerFunction() === 'pagAssignRecruitmentIdentity' &&
      t.getTriggerSourceId() === c.sheet))
    ScriptApp.newTrigger('pagAssignRecruitmentIdentity').forSpreadsheet(c.sheet).onFormSubmit().create();
  console.log('PAG_ID_TRIGGER_READY');
}
