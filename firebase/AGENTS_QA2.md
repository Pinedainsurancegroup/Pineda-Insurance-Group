# PAG Leads 1.9 — Agentes QA2

Fecha: 13 de octubre de 2026, California. Estado: desarrollo implementado y pruebas automáticas aprobadas; **sin despliegue de reglas ni habilitación de agentes reales**.

## Decisión de Juan

Juan aprueba desarrollar primero el sistema para varios agentes. Cada agente solicita acceso con su propio correo verificado; Juan aprueba o rechaza y selecciona Clientes Final Expense, Reclutamiento o ambas. Todos los prospectos proceden de Juan. El agente ve únicamente los asignados. Juan puede suspender, retirar o reasignar sin borrar historial. Esto sustituye para los prospectos asignados el criterio anterior de reclutamiento exclusivo del Owner. Líderes/equipos no se habilitan en esta entrega.

## Implementación

- Android nativo: registro con contraseña propia, acceso por correo o Google, comprobación de correo, solicitud pendiente, cierre de sesión. La contraseña nunca se pasa al WebView ni se persiste por PAG.
- Owner: solicitudes por correo, nombre, acceso aprobado/suspendido, permisos por módulo. Aprobar un agente nunca permite crear otro Owner.
- Clientes FE: ingreso manual de contacto, clasificación Lead/B Lead, asignación, retiro/reasignación, estados, notas e historial. No incluye importación masiva CSV.
- Reclutamiento: contacto manual o selección individual desde la base original. La selección copia únicamente nombre, teléfono, correo y región a `recruitmentAssignments/{stableId}`; no copia la hoja completa ni sus respuestas. Comparte `recruitmentState/{stableId}` y su historial con la app estable del Owner. Los datos del contacto asignado son una instantánea; cambios posteriores del formulario no se propagan automáticamente.
- Agente: secciones autorizadas, lista limitada por `assignedTo`, llamada/WhatsApp mediante apertura explícita de las apps del teléfono, edición de estado/nota e historial. No puede editar contacto, clasificar, reasignar ni cambiar permisos.
- Listas de 50 registros y páginas siguientes; historial de 30 eventos por página. Los agentes elegibles se cargan por páginas de 100.
- Reglas: vinculación UID/correo verificado, autorización actual, denegación de privilegios, revisión incremental y auditoría atómica bidireccional. Historial inmutable. Las transacciones rechazan versiones obsoletas.
- Suspensión/permisos/asignaciones: los listeners cierran datos revocados y las reglas bloquean nuevas consultas incluso desde una sesión antigua. Sin caché persistente Firestore para prospectos. Se vacía la pantalla al pasar a segundo plano. Los borradores del espacio nativo no se conservan al salir: guardar antes de cambiar de pantalla/app. No se promete borrado remoto de información ya vista/copias externas.

## Colecciones y compatibilidad

`accessRequests/{uid}` es una solicitud inmutable con nombre, correo verificado y hora. `users/{uid}` conserva el Owner existente y permite a ese Owner crear/editar únicamente agentes con `scopes.clients` y `scopes.recruitment` y auditoría. Un agente puede leer su perfil aun suspendido para ver su estado, pero no prospectos ni preferencias.

`clients/{id}` almacena contactos FE y seguimiento, con `audit/{eventId}`. `recruitmentAssignments/{stableId}` almacena contacto y asignación, con auditoría separada. `recruitmentState/{stableId}/activity` sigue guardando estados/notas, compatibles con v1.8. Los agentes solo crean eventos de edición, nunca importaciones/respaldos del Owner.

La API de la hoja y el Gateway siguen siendo exclusivos del Owner. No se cambian Google Forms/Sheets, la web, HighLevel, PAG CRM ni PAG Leads STABLE. No se crean usuarios, prospectos ni asignaciones reales. Spark se conserva: no se requieren Cloud Functions ni Blaze.

Los avisos automáticos existentes del Owner no se redirigen. **Avisos de asignación implementados en código, no activados:** cada asignación genera una cola atómica; el emisor Spark privado revisa Owner/rol/módulo/asignación/preferencia/aprobación y hash del token en cada intento. Juan aprueba o suspende teléfonos desde la ficha del agente. Un cambio de token requiere nueva aprobación. Aviso genérico sin PII, máximo 100 intentos/día, 25 eventos/ejecución y hasta 20 dispositivos por agente, con registro de aceptación por dispositivo y reintentos ante fallo. FCM aceptado no demuestra recepción. Si en el momento del procesamiento no hay dispositivo aprobado o el acceso/preferencia impide enviar, el aviso se omite; no se envía retrospectivamente tras aprobar. Las ambigüedades de red pueden causar un duplicado, mitigado por ID estable en Android. Requiere desplegar `SparkAgentAssignments.gs` en el emisor privado existente, actualizar `SparkPushSender.gs`, establecer `AGENT_ASSIGNMENT_PUSH_ENABLED=true` y ejecutar una vez `pagInstallAgentAssignmentTrigger`. El módulo no activa nada al cargarlo y no modifica la ruta de avisos del Owner.

## Evidencia automatizada

- 38 pruebas locales de WebView/Gateway/emisores/identidad (incluyen cinco escenarios del emisor de agentes y las 11 pruebas del WebView): carga, regreso/pausa, notas, migración, conflictos y conservación de datos.
- Reglas existentes: aislamiento, dispositivos, suspensión y sincronización del Owner, más autenticación por contraseña.
- 17 grupos nuevos de escenarios de seguridad: solicitud verificada, correo/UID falsos, aprobación con auditoría, exclusión de Owner, asignación, consultas restringidas, edición limitada, conflicto, historial inmutable, reasignación, separación FE/reclutamiento, estado compartido, retirada de permisos, suspensión, cambio de identidad y retorno a inventario.
- Primera compilación/reglas: GitHub Actions 38431446479 y 38431446329. QA2 incorpora avisos; commit de producto `240718a823d4041c227b230ebbdadfea70841e65`, build 38433646293 y reglas 38433646393. La verificación JSON de entrega contiene los resultados finales de cada gate.
- APK QA con paquete `com.pinedaagencygroup.leads.qa`, código 17; firma PAG existente SHA-256 `b470f6fcf469ac928852283418dd6c1a7f681815cf8d1cc826751ce60fd7a374`. HTML empaquetado igual al fuente, ZIP y alineación comprobados.

La APK se instala junto a STABLE y actualiza una instalación QA anterior si existe. No distribuir a agentes antes de activar reglas y probar con datos ficticios. No etiquetar STABLE.

## Activación y prueba pendientes

1. Restablecer acceso administrativo de Firebase. `firebase login:list` devolvió ausencia de cuentas autorizadas en este entorno. No extraer sesiones del navegador ni introducir credenciales en el repositorio.
2. Leer y respaldar las reglas publicadas actuales; comparar con la base v1.8 para conservar cambios de otros chats. Publicar únicamente las nuevas reglas probadas, sin cambiar datos, región, facturación ni proveedores.
3. Instalar QA en el teléfono de Juan sin desinstalar STABLE. Probar acceso Owner y base original. Con una cuenta de prueba distinta y correo verificado: solicitud pendiente → aprobación solo FE → ambas secciones → suspensión → reactivación. Usar contactos ficticios.
4. Probar notas/estado con Owner y agente, conflicto de edición, retiro/reasignación y bloqueo inmediato de datos ajenos. Confirmar conservación de notas/historial en v1.8.
5. Desplegar y activar el emisor de asignaciones preparado, aprobar dispositivos y probar recepción física. Después preparar candidata de distribución, conservando firma y respaldos.

## Recuperación

Código en rama `pag-leads-v1.9-agents`; la base `pag-leads-v1.8-fcm` no se modifica. Antes de desplegar, guardar el ruleset real vigente. Una reversión de reglas retira acceso nuevo pero no borra documentos ni historial. Nunca restaurar un snapshot viejo sobre datos nuevos. Conservar las colecciones nuevas hasta decidir su tratamiento; no hay operación de borrado masivo.

La carpeta de Drive de esta entrega contiene código de desarrollo, APK QA, verificación, guía y documentos vigentes. Es un respaldo del desarrollo, no una exportación actualizada de producción. La firma y contraseñas permanecen separadas en el respaldo privado previo.

## Límite de activación

La habilitación real queda bloqueada por falta de sesión administrativa. Los 17 escenarios de reglas y 38 pruebas locales aprobaron con datos sintéticos. Las pruebas de CI y la firma se consultan en el JSON de verificación; no se crean agentes reales ni se envían avisos durante el desarrollo. QA2 sustituye QA1 como candidata de prueba; conservar QA1 únicamente como hito histórico.

### Herramientas Android

AGP 8.13.2 y Gradle 8.13 (JDK 17), compatibles con los metadatos Kotlin 2.3 de Firebase Auth. Referencia oficial: https://developer.android.com/build/releases/agp-8-13-0-release-notes . No cambia el SDK objetivo ni la identidad de firma.
