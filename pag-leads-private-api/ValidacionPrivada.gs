// Run manually from Juan's Apps Script editor; no web entry point or PII logging.
function pagVerificarFuente() {
  const props = PropertiesService.getScriptProperties();
  const sheetId = props.getProperty('SPREADSHEET_ID');
  const sheetName = props.getProperty('SHEET_NAME') || 'Respuestas de formulario 1';
  if (!sheetId || !props.getProperty('OWNER_UID')) throw new Error('Configuracion incompleta');
  const values = pagSheetValues_(sheetId, sheetName);
  const required = ['Marca temporal', 'Nombre completo / Full name',
    'Número de teléfono / Phone number', 'Correo electrónico / Email address'];
  const headers = values[0] || [];
  if (!required.every(h => headers.includes(h))) throw new Error('Encabezados no coinciden');
  const leads = pagRecruitmentRows_(values);
  const stable = leads.map(x => x.stableId).filter(Boolean);
  if (stable.length !== leads.length || new Set(stable).size !== leads.length)
    throw new Error('Identidad permanente incompleta o duplicada');
  console.log(JSON.stringify({ok: true, sourceReadOnly: true, recruitmentCount: leads.length,
    stableIdentityCount: stable.length}));
}
