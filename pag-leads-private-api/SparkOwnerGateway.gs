// Deploy as a NEW standalone Apps Script owned by Juan, never into the live
// v1.7 script. Form -> private Sheet and the existing API remain unchanged.
const PAG_FIREBASE_PROJECT = 'pag-leads-8c6ef';

function doPost(e) {
  try {
    const input = JSON.parse((e && e.postData && e.postData.contents) || '{}');
    const action = input.action;
    const idToken = input.idToken;
    if ((action !== 'ping' && action !== 'list') ||
        typeof idToken !== 'string' || idToken.length < 100 || idToken.length > 8192) {
      return pagJson_({ok: false, error: 'Acceso no autorizado'});
    }
    const props = PropertiesService.getScriptProperties();
    const ownerUid = props.getProperty('OWNER_UID');
    const sheetId = props.getProperty('SPREADSHEET_ID');
    if (!ownerUid || !sheetId || !pagOwnerAllowed_(ownerUid, idToken)) {
      return pagJson_({ok: false, error: 'Acceso no autorizado'});
    }
    if (action === 'ping') return pagJson_({ok: true, version: 'PAG Leads Owner Gateway Spark v1'});

    const name = props.getProperty('SHEET_NAME') || 'Respuestas de formulario 1';
    return pagJson_({ok: true, leads: pagRecruitmentRows_(pagSheetValues_(sheetId, name))});
  } catch (_) {
    // Never log an ID token or prospect data from an untrusted request.
    return pagJson_({ok: false, error: 'Fuente no disponible'});
  }
}

function pagSheetValues_(sheetId, name) {
  // The Sheets REST API accepts a read-only OAuth scope. SpreadsheetApp.openById
  // would request edit access to every spreadsheet in Juan's Google account.
  const range = "'" + name.replace(/'/g, "''") + "'!A:ZZ";
  const url = 'https://sheets.googleapis.com/v4/spreadsheets/' +
    encodeURIComponent(sheetId) + '/values/' + encodeURIComponent(range) +
    '?valueRenderOption=FORMATTED_VALUE';
  const result = UrlFetchApp.fetch(url, {
    method: 'get',
    headers: {Authorization: 'Bearer ' + ScriptApp.getOAuthToken()},
    muteHttpExceptions: true
  });
  if (result.getResponseCode() !== 200) throw new Error('Fuente no disponible');
  return JSON.parse(result.getContentText()).values || [];
}

function pagOwnerAllowed_(ownerUid, idToken) {
  const path = encodeURIComponent(ownerUid);
  const url = 'https://firestore.googleapis.com/v1/projects/' + PAG_FIREBASE_PROJECT +
    '/databases/(default)/documents/users/' + path;
  const result = UrlFetchApp.fetch(url, {
    method: 'get',
    headers: {Authorization: 'Bearer ' + idToken, 'Cache-Control': 'no-store'},
    muteHttpExceptions: true
  });
  if (result.getResponseCode() !== 200) return false;
  const profile = JSON.parse(result.getContentText()).fields || {};
  return profile.role && profile.role.stringValue === 'owner' &&
    profile.active && profile.active.booleanValue === true &&
    !(profile.suspended && profile.suspended.booleanValue === true);
}

function pagRecruitmentRows_(values) {
  if (!values || !values.length) return [];
  const headers = values[0], idx = {};
  headers.forEach((h, i) => idx[h] = i);
  const H = {
    ts: 'Marca temporal',
    name: 'Nombre completo / Full name',
    phone: 'Número de teléfono / Phone number',
    email: 'Correo electrónico / Email address',
    state: 'Estado o Puerto Rico donde reside / State or Puerto Rico where you reside',
    license: '¿Tiene una licencia activa de seguros de vida? / Do you have an active life insurance license?',
    experience: '¿Tiene experiencia en ventas de seguros? / Do you have insurance sales experience?',
    motivation: '¿Qué le motivó a solicitar información? / What motivated you to request information?',
    comments: 'Comentarios adicionales / Additional comments'
  };
  return values.slice(1).map((r, n) => ({
    id: 'PAG-A-' + (n + 2), // Legacy ID only; do not migrate overlays before immutable IDs exist.
    type: 'agent',
    createdAt: pagTimestamp_(r[idx[H.ts]]),
    name: r[idx[H.name]] || '',
    phone: r[idx[H.phone]] || '',
    email: r[idx[H.email]] || '',
    city: '', state: r[idx[H.state]] || '',
    license: r[idx[H.license]] || '',
    experience: r[idx[H.experience]] || '',
    motivation: r[idx[H.motivation]] || '',
    comments: r[idx[H.comments]] || '',
    source: 'Google Forms', status: 'Nuevo', note: ''
  })).filter(x => x.name || x.phone || x.email);
}

function pagTimestamp_(value) {
  if (!value) return '';
  const m = String(value).match(/^(\d{1,2})\/(\d{1,2})\/(\d{4})\s+(\d{1,2}):(\d{2})(?::(\d{2}))?$/);
  if (!m) return String(value);
  return m[3] + '-' + m[1].padStart(2, '0') + '-' + m[2].padStart(2, '0') +
    'T' + m[4].padStart(2, '0') + ':' + m[5] + ':' + (m[6] || '00');
}

function pagJson_(value) {
  return ContentService.createTextOutput(JSON.stringify(value))
    .setMimeType(ContentService.MimeType.JSON);
}
