const VERSION = 'PAG Leads Private API v1.0';

function doPost(e) {
  try {
    const body = JSON.parse((e && e.postData && e.postData.contents) || '{}');
    const props = PropertiesService.getScriptProperties();
    const expectedToken = props.getProperty('API_TOKEN');
    const spreadsheetId = props.getProperty('SPREADSHEET_ID');
    const sheetName = props.getProperty('SHEET_NAME') || 'Respuestas de formulario 1';

    if (!expectedToken || !spreadsheetId) {
      return json_({ ok: false, error: 'Configuración incompleta' });
    }
    if (!body.token || body.token !== expectedToken) {
      return json_({ ok: false, error: 'Acceso no autorizado' });
    }

    if (body.action === 'ping') {
      return json_({ ok: true, version: VERSION });
    }
    if (body.action !== 'list') {
      return json_({ ok: false, error: 'Acción no válida' });
    }

    const ss = SpreadsheetApp.openById(spreadsheetId);
    const sh = ss.getSheetByName(sheetName);
    if (!sh) return json_({ ok: false, error: 'Pestaña no encontrada' });

    const values = sh.getDataRange().getDisplayValues();
    if (!values.length) return json_({ ok: true, leads: [] });

    const headers = values[0];
    const rows = values.slice(1);
    const idx = {};
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

    const leads = rows.map((r, n) => ({
      id: 'PAG-A-' + (n + 2),
      type: 'agent',
      createdAt: parseTimestamp_(r[idx[H.ts]]),
      name: r[idx[H.name]] || '',
      phone: r[idx[H.phone]] || '',
      email: r[idx[H.email]] || '',
      city: '',
      state: r[idx[H.state]] || '',
      license: r[idx[H.license]] || '',
      experience: r[idx[H.experience]] || '',
      motivation: r[idx[H.motivation]] || '',
      comments: r[idx[H.comments]] || '',
      source: 'Google Forms',
      status: 'Nuevo',
      note: ''
    })).filter(x => x.name || x.phone || x.email);

    return json_({ ok: true, leads: leads });
  } catch (err) {
    return json_({ ok: false, error: 'Error interno de PAG Leads' });
  }
}

function parseTimestamp_(s) {
  if (!s) return '';
  const m = String(s).match(/^(\d{1,2})\/(\d{1,2})\/(\d{4})\s+(\d{1,2}):(\d{2})(?::(\d{2}))?$/);
  if (!m) return String(s);
  const d = new Date(Number(m[3]), Number(m[2]) - 1, Number(m[1]), Number(m[4]), Number(m[5]), Number(m[6] || 0));
  return d.toISOString();
}

function json_(obj) {
  return ContentService
    .createTextOutput(JSON.stringify(obj))
    .setMimeType(ContentService.MimeType.JSON);
}
