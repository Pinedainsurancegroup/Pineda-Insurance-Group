# Reglas, gateway y evidencia de la continuación

## Preparación realizada sin cloud writes

Se generó /workspace/pag-leads-staging-preparation con prepare_firebase_staging.py usando el proyecto real existente. Incluye bootstrap deny-all, reglas candidatas 1.9 exactas (SHA256 77af6e6fdecf7b3fde0015e09ec067e12a2505c8de5636b3e5d984f7aeb317ee), alias staging sin default y Apps Script standalone de solo lectura parametrizado a pag-leads-staging. No contiene Functions, módulos sender ni triggers. No se desplegó ni creó otro proyecto. Spark no requiere añadir Functions/Blaze para el camino Apps Script actual.

Gateway todavía necesita un Apps Script nuevo en cuenta de pruebas, hoja separada, OWNER_UID de cuenta sintética aprobada, SPREADSHEET_ID y SHEET_NAME de pruebas y URL final de ese gateway. Esos recursos no se hallaron. No usar las URLs/hojas del recurso Android main o qa. No modificar los scripts activos. El bundle es preparación de fuente, no servicio activo.

## Reglas mínimas propuestas (NO aplicadas)

firebase/staging/firestore.identity-smoke.rules deniega todo salvo GET del perfil propio de un usuario autenticado/verificado, previamente aprobado por admin en stagingTestUsers/{uid}, enabled=true y environment=pag-leads-staging. Los clientes no pueden autoaprobarse, listar, editar roles ni escribir prospectos. Sirve solo para pruebas mínimas de identidad, NO para sincronización completa. Bootstrap deny-all sigue siendo el default del bundle y las reglas cloud no se cambiaron.

La suite nueva firebase/tests/staging-identity.test.cjs define 12 verificaciones de aprobación, aislamiento, email_verified y rechazo de todas las escrituras. Ejecutar `npm run test:staging-identity` desde firebase; usa exclusivamente demo-pag-leads/loopback. Se intentó ejecutar: el emulador se detuvo descargando el JAR desde storage.googleapis.com. **Cero aserciones de esta suite ejecutadas**, por bloqueo de red. No se certifican reglas por revisión estática.

Después de aprobación de reglas y cuentas staging, la suite funcional del runbook puede comprobar Google/correo, perfiles, dos agentes, edición concurrente, notificaciones sintéticas al dispositivo dedicado y recuperación. Ninguna notificación se envió. SMS, WhatsApp, campañas, topics y senders permanecen fuera de la preparación. Las reglas mínimas no habilitan esos canales.

## Resultados ejecutados

- Android compileDebugJavaWithJavac: BUILD SUCCESSFUL (17 tareas), comprueba las barreras Java/resource nuevas; no produce/ejecuta APK conectado.
- StagingPolicyTest con -ea: pasa, comprueba proyecto/número admitidos y rechazo de IDs productivos, diferentes y malformados. Los strings de parser no son credenciales utilizadas.
- Python preparación/importación: 14/14 pasan, sin llamadas a servicios.
- Suites Node PAG + contratos: 51/51 pasan; no son pruebas funcionales de Firebase real.
- Sintaxis de la nueva suite de reglas: pasa; ejecución de reglas BLOQUEADA, no aprobada.
- ADB: no dispositivos conectados.

No hay nuevo APK staging conectado entregable: falta el archivo real Android/autorización de lectura. Los APK offline de la entrega anterior no se presentan como conectados. No se crearon claves ficticias ni se reutilizó configuración productiva para generar un APK.

## Intervenciones exactas pendientes

1. Registrar las huellas públicas en la app EXISTENTE staging y obtener el google-services.json actualizado o habilitar lectura CLI autorizada del mismo proyecto. No hace falta volver a proporcionar ID/número/plan/región.
2. Aplicar la política de red del entorno de desarrollo para Firebase API, GitHub API y descarga del emulador. La autenticación Firebase CLI sigue siendo un requisito separado.
3. Proporcionar gateway/hoja de pruebas y cuentas sintéticas cuando se vaya a validar datos; no bloquean la preparación auth-only.
4. Conectar Android dedicado/autorizado; el PC del usuario puede ejecutar el procedimiento ya preparado si no hay ruta ADB a cloud.
5. GitHub PR: red API aún bloqueada; procedimiento manual existente. Sin PR remoto creado/fusión ni despliegues.

Ninguna aplicación está certificada para producción. La ausencia de comunicación productiva en una ejecución real sigue sin verificarse porque aún no hay APK staging configurado ni dispositivo; la presente entrega establece barreras de código y evidencia estática/local.
