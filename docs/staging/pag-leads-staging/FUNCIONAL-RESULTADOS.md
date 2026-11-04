# PAG Leads Staging — diagnóstico funcional específico

HEAD inicial local y remoto comprobados: 446d805. Fetch de la rama dev/pag-security-audit-20261102 dio FETCH_HEAD idéntico (0/0); no se revirtió trabajo posterior. El propietario informa que owner inicia sesión en su teléfono. Esta sesión NO tiene dispositivo ADB y no ha leído las reglas actualmente publicadas; no atribuye a red ni a identity-smoke todos los fallos.

## Cinco operaciones

| Fallo | Operación exacta y causa comprobada | Corrección preparada | Evidencia | Pendiente |
|---|---|---|---|---|
| Invitar agente | GET agentInvitations/{correo}; después transacción GET/SET invitación + CREATE audit, luego Auth sendSignInLinkToEmail. El código ocultaba la causa con el mismo mensaje para todos los errores. Código real del teléfono: NO CAPTURADO. identity-smoke lo denegaría si estuviera publicado; no se sabe si lo está. | Mostrar etapa y código SDK sin dirección, enlace ni mensaje crudo; candidata funcional exige owner y auditoría. | Código AgentWorkspace/AgentStore; compilación y prueba del clasificador. | Work debe comparar reglas publicadas; transacción real bajo candidata BLOQUEADA por emulador. No enviar invitaciones reales. |
| Agregar prospecto | Primero LIST users con role=agent para selector; después transacción GET/SET clients o recruitmentAssignments + audit; assignmentNotices solo cuando hay nueva asignación. El guardado ni siquiera se habilita si falla la consulta de usuarios. Código real: NO CAPTURADO; no asumir que falló la escritura. | Mensajes distintos para users LIST y transacción; sin sesión devuelve UNAUTHENTICATED en vez de NullPointerException. | Lectura del flujo editContact/loadAssignees; build PASS. | Reglas/índices efectivos y prueba de transacción + audit + cola inerte en emulador; BLOQUEADO. |
| Reclutamiento asignado | LIST/listener recruitmentAssignments; agente filtra assignedTo=uid, owner consulta inventario. Después recruitmentState GET y escrituras con activity audit. Código real: NO CAPTURADO. | Mostrar colección, LIST/listen y código SDK; candidata conserva scope recruitment y assignedTo. | AgentWorkspace.records y suites agents/recruitment-sync existentes. | Reproducir consulta bajo candidata y reglas publicadas; no aprobado por análisis estático. |
| Mi base original | Gateway staging vacío COMPROBADO. Antes se intentaba abrir WebView sin comprobar disponibilidad; causa del “no abre nada” exacto en teléfono NO reproducida. | Guardar navegación en workspace y mostrar «Base de pruebas no configurada» antes de crear/abrir WebView; no usar URL/token heredados. | Guardas en callback y openRecruitment; recursos APK verificados vacíos; WebView sigue con controles anteriores. | Confirmar diálogo y navegación en teléfono. Para datos: base sintética independiente aún no configurada. |
| Ingresar como agente | Auth sendSignInLink/signInWithEmailLink → users GET → si no existe perfil, transacción lee agentInvitations/users/accessRequests y escribe perfil+audit/request/claim → users GET/listen. Código real del fallo remoto: NO CAPTURADO. | Mensajes por etapa, invitación ausente diferenciada; no transformar owner. | Auth Emulator real: identidad por enlace y rechazo de reuso PASS. | Firestore aceptación completa BLOQUEADA; proveedor/dominios/Hosting App Links/reglas publicados no leídos. Prueba en teléfono pendiente. |

El nuevo APK muestra [operación · código] que puede copiarse sin datos personales. PERMISSION_DENIED no es red; UNAUTHENTICATED/tokens vencidos es sesión; provider/domain/key es configuración; NETWORK_ERROR es conectividad; UNAVAILABLE no demuestra por sí solo la causa; FAILED_PRECONDITION exige revisar requisitos/índices. CLIENT_TIMEOUT es una espera local, no un código recibido del servidor. UNKNOWN no imprime la excepción, correo, URL ni token. No se añadió registro de datos personales.

## Resultados ejecutados

- Auth Emulator, proyecto demo-pag-leads, loopback9099: PASS de signInWithEmailLink con identidad sintética verificada y rechazo de reutilización del código. Cero correos externos. NO prueba apertura Android/Hosting ni acceso Firestore.
- Firestore/Auth bajo candidata: BLOQUEADO antes de ejecutar casos, por descarga fallida de cloud-firestore-emulator-v1.22.0.jar desde storage.googleapis.com. No existe candidate-validation.json PASS.
- 51 pruebas Node locales y 14 Python: PASS. Son pruebas de código, no sustituyen reglas.
- Java OperationMessagesTest, AccessCheckTest y StagingPolicyTest con assertions: PASS.
- assembleStaging, assembleStagingAndroidTest y lintStaging: PASS, 0 errores y 40 advertencias sin supresiones nuevas.
- adb devices: ningún teléfono conectado. Ninguna de las cinco acciones fue ejecutada por este agente en el teléfono ni en servicios remotos.

## Reglas y Work

Paquete firebase/staging/work-functional: candidata copiada exactamente de firebase/firestore.rules, SHA256 77af6e6fdecf7b3fde0015e09ec067e12a2505c8de5636b3e5d984f7aeb317ee. Sin cambios publicados ni alteración del owner. El runner carga explícitamente esa candidata en cada suite existente y añade un flujo Auth+Firestore con transacciones reales; solo genera prueba PASS tras éxito total. La copia está pendiente de validación; NO está aprobada para aplicar.

WORK-HANDOFF.md exige lectura/respaldo de release/ruleset actualmente publicados, comparación sin perder avances, revisión de índices/consumidores de assignmentNotices, validación completa, verificación del hash y reversión al ruleset anterior. No deploy genérico ni Functions. Reglas y configuración aplicada desde esta tarea: NINGUNA.

## APK y actualización

Se generó porque hay cambios Android. Versión 1.9-INVITATIONS-QA3-STAGING-FUNCTIONAL1, versionCode19, paquete com.pinedaagencygroup.leads.staging. Misma firma QA que el APK18: SHA-1 F0:9F:A0:58:20:BF:2F:B1:88:9E:FF:C2:26:30:05:1E:70:8B:7C:E7; SHA-256 53:8C:07:CE:2B:20:8F:D5:00:BB:4B:17:31:16:48:16:D2:C9:9C:D3:A6:56:16:03:0F:72:58:50:F4:E4:97:81. Registro remoto SHA-256 sigue sin confirmarse por API/consola.

Recursos coinciden con overlay auténtico ya importado, proyecto pag-leads-staging / 301600139735, flag staging, enlace staging y gateway vacío. Ningún valor Firebase de main/qa aparece en los recursos/manifiesto. No se reimportó JSON, no se publicó configuración ni credenciales. Prueba dinámica de ausencia de tráfico productivo: PENDIENTE.

Instalar este APK como actualización de la instalación STAGING existente, verificando antes paquete, firma y checksum. No desinstalar, borrar datos ni tocar com.pinedaagencygroup.leads estable. Android debe ofrecer actualizar PAG Leads STAGING; si presenta incompatibilidad de firma o paquete, detenerse. No forzar downgrade. Si Work resuelve solo configuración, mantener instalación actual; este APK añade diagnóstico/navegación, NO abre Firestore por sí mismo.

Artefactos y evidencias locales: /workspace/pag-staging-functional-evidence/artifacts y logs sanitizados correspondientes. Logs Auth crudos quedan fuera de la entrega porque contienen enlaces sintéticos. La revisión de datos y pruebas funcionales remotas requerirá intervención externa; no está listo para producción.
