# Preparación Firebase staging (sin despliegue)

No ejecutar sobre el proyecto activo. Este directorio contiene solamente reglas bootstrap deny-all; las reglas candidatas se copian del fuente versionado por el generador. No se copiaron datos, credenciales, Functions ni módulos de envío.

Cuando el propietario haya identificado/creado su proyecto de pruebas independiente:

```sh
python3 scripts/validation/prepare_firebase_staging.py \
  --project ID_REAL_DEL_PROYECTO_STAGING \
  --output /workspace/firebase-staging-NUEVO
```

El comando solo escribe archivos locales y rechaza el proyecto activo conocido. No crea proyectos Firebase, no autentica, no llama servicios y no despliega nada. No sustituir el ID por uno inventado para presentar un entorno como configurado. El generador no puede demostrar que un proyecto desconocido sea staging: confirmar titularidad/uso en consola.

Salida:

- firebase.json: reglas bootstrap (ninguna lectura/escritura), emuladores loopback y ningún bloque functions.
- firebase.candidate.json: mismas opciones, pero reglas candidatas 1.9 copiadas sin cambiar permisos.
- firestore.indexes.json: inventario vacío; comprobar consultas reales en staging, no asumir ausencia de índices requeridos.
- .firebaserc: alias staging, sin alias default.
- apps-script/OwnerGateway.gs: copia de solo lectura con ID del proyecto staging; sin módulos de envío/triggers.
- apps-script/appsscript.json: scopes Sheets readonly/external_request.
- preparation.json: SHA256 de reglas candidatas y restricciones; ningún secreto.

Los archivos no son un despliegue aprobado. No usar comandos de README antiguos que mencionan el proyecto activo. No usar firebase deploy sin --only ni confiar en un alias/default.

## Secuencia que requiere al propietario

1. Firebase Console: crear/seleccionar proyecto de pruebas, confirmar ID, titularidad, uso exclusivo y región. No copiar bases ni usuarios reales. Mantener billing sin cambios salvo necesidad y autorización separada.
2. Crear Firestore de pruebas cerrado. Revisar reglas bootstrap en consola; mantener acceso denegado hasta disponer de pruebas y cuentas sintéticas. Crear usuarios de prueba manuales en Auth; los roles deben aprovisionarse mediante administrador autorizado solo en staging. Reglas de cliente no crean Owners.
3. Habilitar únicamente proveedores de Auth requeridos. Registrar aplicación Android `.staging`, cert SHA-1/SHA-256 del APK de pruebas y web client OAuth. Validar dominio de Auth/assetlinks para enlaces; no editar la app registrada estable.
4. Crear hoja nueva sin clientes reales y Apps Script standalone nuevo. Usar solo OwnerGateway.gs generado. Configurar OWNER_UID/SPREADSHEET_ID/SHEET_NAME desde los recursos de pruebas; no reciclar propiedades ni despliegues existentes. Gateway no envía notificaciones ni WhatsApp.
5. Revisar aislamiento OAuth: scope Sheets readonly puede abarcar otras hojas accesibles por la cuenta ejecutora; preferir identidad de pruebas con acceso únicamente a la hoja de pruebas. Habilitar Sheets API solo en el proyecto de pruebas si es necesario. No copiar scripts sender ni crear triggers automáticos.
6. Revisar y aplicar las reglas candidatas SOLO a staging cuando pruebas de emulador y autorización permitan continuar. En esta sesión no se ejecuta esa operación. Comparar SHA de preparation.json con firebase/firestore.rules y verificar en consola que el proyecto elegido no sea el activo.
7. Probar roles, scopes, invitaciones, dos agentes y perfiles suspendidos; nunca usar reglas abiertas como atajo. Leer firebase/tests para el catálogo de casos. Verificar índices para where assignedTo/role + orderBy documentId y actividad/audit por createdAt/documentId con paginación.
8. Obtener configuración pública cliente y gateway final de pruebas; generar overlay Android con prepare_staging.py. Revisar recursos y manifiesto fusionados antes de empaquetar APK conectado.

No es necesario desplegar la Function ownerRecruitment para el camino Android actual de Apps Script. Las Functions presentes en el repo son alternativa histórica; excluirlas evita heredar PAG_PRIVATE_API_URL/TOKEN o iniciar gastos/servicios no requeridos. FCM receipt no es prueba de campañas: no habilitar senders/topics/multicast.

## Pruebas de reglas (no ejecutadas aquí por falta de JAR)

La suite existente usa exclusivamente demo-pag-leads y loopback. Una vez que se haya podido instalar/verificar el JAR del emulador por la política autorizada, ejecutar `npm run test:rules` desde firebase. No cambiar ese proyecto demo por el proyecto real para hacer pasar los tests. El emulador no certifica índices desplegados ni los servicios reales.
