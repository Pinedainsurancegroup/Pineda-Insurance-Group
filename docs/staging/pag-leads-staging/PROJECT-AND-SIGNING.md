# Proyecto existente y firma de QA

Datos proporcionados por el propietario (no se verificaron por API, cuya autenticación está bloqueada):

- Firebase Project ID: pag-leads-staging.
- Número de proyecto: 301600139735.
- Android registrado: com.pinedaagencygroup.leads.staging.
- Plan Spark; Firestore nam5; Auth correo/contraseña, enlace y Google habilitados; Firestore cerrado.

No crear otro proyecto, no registrar otra app con distinto paquete y no usar Firebase de producción. No se cambió el plan, la región, proveedores Auth ni reglas activas.

## Firma

Certificado QA actual comprobado con keytool sobre la clave debug del entorno (no se exportó clave privada):

- Alias: androiddebugkey, Android Debug.
- SHA-1: F0:9F:A0:58:20:BF:2F:B1:88:9E:FF:C2:26:30:05:1E:70:8B:7C:E7
- SHA-256: 53:8C:07:CE:2B:20:8F:D5:00:BB:4B:17:31:16:48:16:D2:C9:9C:D3:A6:56:16:03:0F:72:58:50:F4:E4:97:81

Registrar ambas huellas en Firebase Console → pag-leads-staging → Project settings → General → Your apps → com.pinedaagencygroup.leads.staging → SHA certificate fingerprints. Confirmar OAuth en el proyecto staging después de guardar; descargar google-services.json actualizado. No registrar este certificado en la app estable ni usar su clave de distribución.

La huella corresponde a la clave debug retenida actualmente en esta máquina. Si se reconstruye el entorno con otra clave, volver a comprobar y registrar la nueva; no asumir que los builds de otro PC tienen esta firma.

## Coexistencia y aislamiento

La variante staging añade applicationIdSuffix .staging y versionNameSuffix -STAGING. Es distinta de com.pinedaagencygroup.leads (estable) y .qa (QA anterior). Su manifiesto reemplaza solo la declaración de MainActivity para usar el dominio pag-leads-staging.firebaseapp.com y conserva launcher/launchMode.

El runtime staging verifica paquete, proyecto, sender y Firebase appId, incluida la instancia Firebase predeterminada que esté activa; rechaza otros proyectos/números y appId malformado. La ruta legacy de URL/token queda deshabilitada en staging y su manifiesto elimina LeadMonitorService para que no pueda iniciar polling heredado. FCM conserva su servicio independiente. Generador/importador rechazan valores productivos conocidos. No se ha demostrado aún la ausencia dinámica de tráfico productivo: falta configuración real, APK conectado y captura de red en dispositivo de pruebas. No se instaló/lanzó ninguna app.
