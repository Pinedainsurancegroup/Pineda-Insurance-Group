# Auditoría técnica PAG — 2026-11-02

## Alcance y evidencia
Trabajo en `dev/pag-security-audit-20261102`, base PAG Leads 1.9 `be70a838662d92ad8673329136fb4a8745451200`. Ningún despliegue, envío, escritura de base real o consulta de leads. El informe suministrado es referencia, no prueba de producción. No se ha establecido correspondencia entre APK instalado, configuración remota y commits.

`branch-inventory.json` registra los SHA de todas las ramas remotas encontradas, sus manifiestos y pruebas. Se inspeccionaron árboles de main, 1.8, 1.9, CRM bridge, PIMFLEX Android/iOS y Taty Nails. Las ramas auxiliares quedaron inventariadas; no constituyen una revisión exhaustiva línea a línea de todos sus commits.

## Hallazgos y tratamiento

| Prioridad | Evidencia | Tratamiento / límite |
|---|---|---|
| Alta | MainActivity 1.9: origen file, acceso universal, puente JavaScript | Origen HTTPS local WebViewAssetLoader, acceso file/content deshabilitado, CSP sin frames/conexiones remotas y bloqueo de recursos externos. Migración de notas y borradores desde documento inerte sin puente. Requiere prueba real de actualización antes de merge. |
| Alta | Token heredado en pag_native y pagset12 | AES-GCM con Android Keystore, migración sin fallback a escritura plana, eliminación de token de respuestas del puente y persistencia web. Transporte heredado nativo restringido a Apps Script HTTPS. |
| Alta | allowBackup=true; captura de pantalla | Backup y transferencia de datos excluidos; FLAG_SECURE. Esto deshabilita capturas deliberadamente. |
| Media | Callback de asignación puede resolver tras cambio de cuenta | Comprobación adicional del UID vigente y existencia de perfil. Mantiene gates y reglas existentes; no cambia roles remotos. |
| Alta | Monitor heredado acepta URL arbitraria y redirecciones automáticas | Restringido a Apps Script HTTPS; redirecciones limitadas a Google y respuesta acotada a 2 MB. Confirmar contratos de endpoints instalados antes de publicar. |
| Alta | PIMFLEX Android permite cleartext y URLs con credenciales | Pendiente: contrato TLS/proveedor y pruebas de login/stream con fixtures. No cambiar producción ni asumir que HTTPS funciona en cada proveedor. |
| Media | Taty Nails usa fragmentos base64 y overlays en workflow | Archivo base reconstruido en memoria y CRC ZIP validado; inventario en tatynails-artifact.txt. Esto no demuestra autenticidad ni valida overlays. |
| Media | Firebase Functions usa rangos y no hay lockfile en Firebase | Dependencias no reproducibles. Generar locks revisados y auditoría de transitivas en siguiente PR. No actualización masiva sin regresión. |
| Alta pendiente | Firebase rules / roles, invitaciones y asignaciones | Existen reglas deny-by-default, auditoría atómica, propietario activo, scopes y asignación. Pruebas de emulador bloqueadas por descarga; no se certifica aislamiento por revisión estática. |
| Media | Functions limita cuerpo después de response.text() | El límite no acota memoria antes de leer; implementar streaming limitado y política explícita de redirecciones en PR backend. |

El escaneo limitado de 507 blobs del historial disponible no encontró firmas de claves privadas, AWS access-key IDs o tokens GitHub. No demuestra ausencia de secretos/PII, cadenas genéricas ni secretos codificados; ver secret-scan-summary.json. No se imprimieron valores de credenciales.

## Pruebas y límites

- PAG Leads 1.9: suites Node de UI/lifecycle, gateway, identidad, envíos simulados y asignaciones. Se agregó regresión que verifica exclusión de credenciales persistidas y conservación de notas.
- PAG Leads 1.8: cinco archivos de suite Node ejecutados satisfactoriamente.
- CRM bridge: cinco archivos de suite ejecutados satisfactoriamente (incluyen controles, idempotencia y preview). No habilitado ni conectado a CRM/WhatsApp.
- Instrumentación Android ampliada para migración de token, cifrado, IV distinto y corrupción; pendiente ejecución en dispositivo/emulador. No existe /dev/kvm ni emulador instalado.
- Firestore: `npm run test:rules`, proyecto exclusivamente `demo-pag-leads`; descarga de JAR desde storage.googleapis.com devuelve 403. No se ejecutaron las aserciones de reglas.
- Primer build con Gradle 8.9 falló por requisito 8.13; segundo con Java del sistema falló por falta de JAVA_COMPILER. Se instaló JDK 17 completo y Gradle 8.13 con hashes oficiales verificados. Resultado final en RESULTS.md.
- iOS requiere macOS/Xcode; no compilado aquí. PIMFLEX y Taty Nails no se certifican por compilar PAG Leads.

## Bloqueos de entrega y criterios de merge

Git fetch funciona con el proxy inyectado. La API `api.github.com` responde Forbidden; `gh auth status` no demuestra que falte autenticación Git. PR remoto pendiente si no se restablece acceso API. No introducir tokens en chat.

Antes de merge: ejecutar emuladores de reglas, instrumentación de migración v1.7/v1.9 con datos sintéticos, comprobar notas/borradores/credenciales tras reinicio y cambio de cuenta, denegación de permisos de notificación, enlace de invitación, suspensión, rotación/revocación, navegación maliciosa y subframes. La migración de origen y el vault son cambios sensibles: este PR debe permanecer borrador hasta esas verificaciones.

No se ha auditado producción ni se ha confirmado la procedencia de sus binarios. Faltan fuentes completos de PAG AI, PAG CRM v22 y WhatsApp Receiver v23: el bridge no reemplaza sus servicios. Se requieren repositorios/exports autorizados, commit desplegado, manifiestos, contratos y datos de prueba anonimizados, sin compartir secretos.
