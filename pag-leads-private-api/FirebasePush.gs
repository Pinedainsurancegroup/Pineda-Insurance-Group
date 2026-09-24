/**
 * PAG Leads Firebase Push extension
 * No contiene secretos. Requiere Script Properties:
 * - FCM_SERVICE_ACCOUNT_JSON = JSON completo de una cuenta de servicio del proyecto Firebase
 * - (opcional) FCM_PROJECT_ID, si se desea sobrescribir service_account.project_id
 *
 * El API_TOKEN, SPREADSHEET_ID y SHEET_NAME existentes permanecen sin cambios.
 */

function registerFcmDevice_(body) {
  const deviceToken = String(body.deviceToken || '').trim();
  if (!deviceToken) return { ok: false, error: 'deviceToken requerido' };

  const props = PropertiesService.getScriptProperties();
  let tokens = [];
  try { tokens = JSON.parse(props.getProperty('FCM_DEVICE_TOKENS') || '[]'); } catch (e) {}
  if (!Array.isArray(tokens)) tokens = [];

  tokens = tokens.filter(t => t && t !== deviceToken);
  tokens.unshift(deviceToken);
  tokens = tokens.slice(0, 20);
  props.setProperty('FCM_DEVICE_TOKENS', JSON.stringify(tokens));
  return { ok: true, registered: true, devices: tokens.length };
}

function setupFirebasePushTriggerOnce() {
  const props = PropertiesService.getScriptProperties();
  const spreadsheetId = props.getProperty('SPREADSHEET_ID');
  if (!spreadsheetId) throw new Error('Falta SPREADSHEET_ID');

  ScriptApp.getProjectTriggers().forEach(t => {
    if (t.getHandlerFunction() === 'onPagLeadFormSubmit') ScriptApp.deleteTrigger(t);
  });

  ScriptApp.newTrigger('onPagLeadFormSubmit')
    .forSpreadsheet(spreadsheetId)
    .onFormSubmit()
    .create();

  return 'PAG FCM trigger creado';
}

function onPagLeadFormSubmit(e) {
  // No incluir teléfono, email ni otra PII en el push.
  sendPagFcm_({
    title: 'PAG Leads — Nuevo agente',
    body: 'Nuevo lead recibido. Toca para abrir PAG Leads.',
    type: 'agent'
  });
}

function testPagFcmPush() {
  return sendPagFcm_({
    title: 'PAG Leads — Prueba Firebase',
    body: 'La notificación push de Firebase funciona correctamente.',
    type: 'test'
  });
}

function sendPagFcm_(data) {
  const props = PropertiesService.getScriptProperties();
  let tokens = [];
  try { tokens = JSON.parse(props.getProperty('FCM_DEVICE_TOKENS') || '[]'); } catch (e) {}
  if (!Array.isArray(tokens) || !tokens.length) return { ok: true, sent: 0 };

  const serviceAccount = getFirebaseServiceAccount_();
  const projectId = props.getProperty('FCM_PROJECT_ID') || serviceAccount.project_id;
  if (!projectId) throw new Error('Falta project_id de Firebase');

  const accessToken = getFcmAccessToken_(serviceAccount);
  let sent = 0;
  const valid = [];

  tokens.forEach(deviceToken => {
    const payload = {
      message: {
        token: deviceToken,
        data: {
          title: String(data.title || 'PAG Leads'),
          body: String(data.body || 'Nuevo lead recibido.'),
          type: String(data.type || 'agent')
        },
        android: {
          priority: 'high'
        }
      }
    };

    const resp = UrlFetchApp.fetch(
      'https://fcm.googleapis.com/v1/projects/' + encodeURIComponent(projectId) + '/messages:send',
      {
        method: 'post',
        contentType: 'application/json',
        headers: { Authorization: 'Bearer ' + accessToken },
        payload: JSON.stringify(payload),
        muteHttpExceptions: true
      }
    );

    const code = resp.getResponseCode();
    if (code >= 200 && code < 300) {
      sent++;
      valid.push(deviceToken);
    } else if (code !== 404 && code !== 400) {
      // Conservar token ante errores temporales de red/permisos.
      valid.push(deviceToken);
    }
  });

  props.setProperty('FCM_DEVICE_TOKENS', JSON.stringify(valid.slice(0, 20)));
  return { ok: true, sent: sent, devices: valid.length };
}

function getFirebaseServiceAccount_() {
  const raw = PropertiesService.getScriptProperties().getProperty('FCM_SERVICE_ACCOUNT_JSON');
  if (!raw) throw new Error('Falta FCM_SERVICE_ACCOUNT_JSON');
  const svc = JSON.parse(raw);
  if (!svc.client_email || !svc.private_key) throw new Error('Cuenta de servicio Firebase incompleta');
  return svc;
}

function getFcmAccessToken_(svc) {
  const cache = CacheService.getScriptCache();
  const cached = cache.get('PAG_FCM_ACCESS_TOKEN');
  if (cached) return cached;

  const now = Math.floor(Date.now() / 1000);
  const header = base64Url_(JSON.stringify({ alg: 'RS256', typ: 'JWT' }));
  const claim = base64Url_(JSON.stringify({
    iss: svc.client_email,
    scope: 'https://www.googleapis.com/auth/firebase.messaging',
    aud: 'https://oauth2.googleapis.com/token',
    iat: now,
    exp: now + 3600
  }));

  const unsigned = header + '.' + claim;
  const sig = Utilities.computeRsaSha256Signature(unsigned, svc.private_key);
  const jwt = unsigned + '.' + Utilities.base64EncodeWebSafe(sig).replace(/=+$/g, '');

  const resp = UrlFetchApp.fetch('https://oauth2.googleapis.com/token', {
    method: 'post',
    payload: {
      grant_type: 'urn:ietf:params:oauth:grant-type:jwt-bearer',
      assertion: jwt
    },
    muteHttpExceptions: true
  });

  if (resp.getResponseCode() < 200 || resp.getResponseCode() >= 300) {
    throw new Error('No se pudo obtener token OAuth para FCM');
  }

  const obj = JSON.parse(resp.getContentText());
  if (!obj.access_token) throw new Error('OAuth FCM sin access_token');
  cache.put('PAG_FCM_ACCESS_TOKEN', obj.access_token, 3000);
  return obj.access_token;
}

function base64Url_(s) {
  return Utilities.base64EncodeWebSafe(s, Utilities.Charset.UTF_8).replace(/=+$/g, '');
}
