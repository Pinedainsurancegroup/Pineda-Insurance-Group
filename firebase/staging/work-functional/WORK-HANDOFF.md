# PAG Leads STAGING — paquete para Work

ESTADO: BLOQUEADO PARA APLICAR. La política candidata NO ha pasado las pruebas de Firestore: esta sesión no puede descargar cloud-firestore-emulator-v1.22.0.jar. No confundir pruebas Auth/compilación/mocks con validación de reglas. No aplicar hasta obtener PASS de TODAS las suites bajo esta candidata.

## Alcance y contenido

Único destino eventual: pag-leads-staging / 301600139735 / Firestore (default), región indicada por propietario nam5. App com.pinedaagencygroup.leads.staging. Spark, sin activar facturación. No producción, Functions, SMS, WhatsApp, campañas ni importaciones reales.

firestore.candidate.rules es una copia exacta de firebase/firestore.rules de la rama de desarrollo. Su hash está en SHA256SUMS; identity-smoke NO es esta política funcional. Las reglas mantienen owner activo, sin modificar el documento owner, prohíben promocionarse a owner, restringen agentes a assignedTo y scopes, exigen auditoría atómica/revisiones e impiden editar/eliminar historial. Una cuenta suspendida conserva únicamente acceso de diagnóstico a su propio perfil/solicitud; no a prospectos. Las invitaciones solo las escribe owner; el agente reclama su correo verificado en transacción con users, accessRequests y auditoría. No hay reglas abiertas.

assignmentNotices conserva la cola de asignaciones requerida por AgentStore.save. Escribir pending NO equivale a enviar, pero cualquier consumidor existente podría reaccionar: Work debe comprobar que no hay triggers, Functions, Eventarc, Jobs, webhooks o procesos externos que consuman esa cola en staging. No crear ni habilitar consumidores. Si alguno está activo, DETENER antes de fixtures/mutaciones, informar y preparar otra candidata sin cola con el cambio Android correspondiente; no desactivar servicios sin autorización.

## Puerta de validación en un entorno autorizado

1. Usar copia completa de firebase (package.json/package-lock.json/tests/staging/work-functional). Instalar dependencias fijadas con npm ci. Node compatible con firebase-tools y Java requerido por su versión; conservar TLS y proxy del entorno. Descargar el emulador oficial desde storage.googleapis.com en un entorno cuya política lo permita. No sustituir la prueba por análisis estático.
2. Desde raíz del repositorio/paquete: bash firebase/staging/work-functional/test-candidate.sh. Solo loopback Auth9099/Firestore8085 y proyecto demo-pag-leads. Nunca cambiar ese ID por staging en pruebas destructivas.
3. El runner verifica SHA256SUMS, configura PAG_RULES_FILE absoluto y carga esas reglas explícitamente con initializeTestEnvironment en cada suite. No cae silenciosamente a otro archivo. Ejecuta rules, recruitment-sync, owner-password, agents, invitations, auth-links y staging-functional. La última usa identidades reales de Auth Emulator y transacciones como Android, con auditorías, asignación y cola inerte; ninguna llamada a proveedor externo.
4. Solo tras éxito completo se genera candidate-validation.json con hash de reglas, hashes de tests y hora. Su ausencia o cualquier suite fallida = BLOQUEADO. Si se corrige una regla o prueba, actualizar hash, revisar diff y repetir todo. No distribuir logs Auth crudos: contienen enlaces sintéticos de un solo uso.

## Primero leer y respaldar lo publicado (Work; no ejecutado aquí)

- Autenticar mediante el canal seguro ya autorizado, sin pedir claves en chat. Verificar ID y número del proyecto; registrar identidad y permisos efectivos. No activar APIs/plan automáticamente.
- Leer Firebase Rules release projects/pag-leads-staging/releases/cloud.firestore mediante Firebase Rules API. Registrar el rulesetName exacto y release/updateTime. Obtener ese ruleset y guardar íntegro ruleset.source.files, nombres de archivo y hashes en almacenamiento privado. No asumir que Git representa lo publicado.
- Leer en modo solo lectura users/<UID owner autorizado> y respaldar el perfil de manera privada. Confirmar role=owner, active=true, suspended=false y UID de la sesión existente. No escribirlo, cambiar correo/rol ni convertirlo en agente. No incluir UID/correo en informes compartidos.
- Comparar backup publicado con la candidata validada; revisar cambios de colecciones, consultas, privilegios, self-get, auditoría y cola. Si lo publicado contiene avances adicionales, integrarlos de forma explícita en candidata y repetir emuladores; no sobreescribirlos.
- Revisar índices publicados y configuraciones de Auth solo lectura. Si existe índice faltante, registrar FAILED_PRECONDITION; no abrir reglas para encubrirlo.
- Obtener autorización de aplicación en el flujo de Work y seguir solo si candidato/hash/tests coinciden. Esta tarea NO autoriza a este agente a publicar reglas ni acredita su publicación.

## Aplicación eventual y reversión (solo Work después de validar)

Guardar un nuevo ruleset con las fuentes EXACTAS validadas y actualizar únicamente la release cloud.firestore de pag-leads-staging. No ejecutar firebase deploy genérico, no incluir Functions/Hosting ni cambiar datos. Inmediatamente antes, releer la release y abortar si cambió desde el backup (evitar sobrescribir cambios concurrentes). Tras aplicar, leer de nuevo release/ruleset y comparar hash. Conservar la instalación del teléfono si solo cambia configuración.

Verificar que el owner existente sigue leyendo su perfil; no invitar personas reales. Una validación funcional remota requerirá autorización para crear fixtures sintéticos separados y comprobar que no hay consumidores/envíos activos. Los emails por enlace se prueban primero y por ahora solo en Auth Emulator.

Reversión: conservar rulesetName anterior y release snapshot; si el cambio provoca regresión, Work debe restablecer exclusivamente la release cloud.firestore al ruleset respaldado y verificar hash/owner. No borrar colecciones, perfiles ni datos para revertir reglas. No usar reglas abiertas como emergencia. Si no se puede leer/respaldar o no hay permisos para restaurar, no aplicar.

## Configuración Auth y enlaces que Work debe comprobar (no confirmada por este agente)

Proveedor email/password y emailLink habilitados; Google habilitado. Authorized domains incluye pag-leads-staging.firebaseapp.com. Android está registrado como com.pinedaagencygroup.leads.staging, con SHA-1 QA conocido y SHA-256 QA confirmado en consola (el JSON solo acredita el SHA-1 OAuth). No crear otra app/proyecto.

Android ActionCodeSettings usa handleCodeInApp=true, package staging e installApp=false, continue URL https://pag-leads-staging.firebaseapp.com/__/auth/handler. La apertura declarada en manifiesto es https://pag-leads-staging.firebaseapp.com/__/auth/links. Revisar Hosting App Links/assetlinks y path del enlace real en canal privado; la dependencia usa Auth moderno, no Dynamic Links legado. No publicar enlaces, oobCode, email ni tokens. El fallback «Tengo el enlace» valida scheme https, host staging e isSignInWithEmailLink. Auth Emulator prueba la identidad y consumo del código, pero NO prueba resolución Android/Hosting.

Ruta funcional: Auth signInWithEmailLink → users GET servidor → si falta perfil, redeem lee invitation/users/accessRequests → transacción atómica crea perfil agent con scopes exactos aprobados y auditoría, registra request y reclama invitation → users GET/listen. Usuario sin invitación/credencial verificada no recibe acceso. Perfil owner ya existente nunca se convierte en agent.

## Base separada de reclutamiento

El APK mantiene gateway vacío y muestra «Base de pruebas no configurada» antes de abrir WebView. No requiere gateway para clients/recruitmentAssignments en Firestore. Para ensayar base heredada: crear en otro paso autorizado una hoja exclusivamente sintética y un Apps Script de staging, con ID propio, verificación de ID token de pag-leads-staging y owner activo; no copiar hojas/tokens reales. Contrato de lectura list y rutas HTTPS existentes; ningún sender/trigger. Probar identidad incorrecta/expirada y respuesta acotada. No configurar URL hasta validar ese servicio; después importar un nuevo overlay con URL aprobada requiere nueva compilación, sin reemplazar configuración existente a mano.
