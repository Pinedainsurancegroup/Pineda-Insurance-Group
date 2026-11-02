# PAG Leads 1.9 — pruebas funcionales staging

Estado: preparación, no prueba funcional aprobada. Base ada5e1c. No se repiten builds offline ni se generan APK conectados con identificadores inventados.

## Prerrequisitos que faltan

1. Android de pruebas autorizado y visible en `adb devices -l`, con Google Play Services para FCM/Google login. Usar dispositivo dedicado o perfil de trabajo de pruebas. No limpiar ni reemplazar aplicaciones estables.
2. Proyecto Firebase de staging separado de pag-leads-8c6ef, aplicación registrada como `com.pinedaagencygroup.leads.staging`, configuración pública completa (seis campos del ejemplo), OAuth configurado con el certificado debug de este entorno. La clave Firebase cliente es configuración pública, no una contraseña; las restricciones de API y reglas siguen siendo necesarias.
3. Gateway Apps Script de pruebas con hoja exclusivamente sintética y configuración servidor separada; pruebas de pertenencia/autorización. Esta tarea no crea ni despliega esos servicios.
4. Cuentas sintéticas owner/agent-A/agent-B y suspendida, con correos verificados y reglas de staging auditadas. Nunca usar cuentas, tokens, hojas o perfiles productivos.

La plantilla `scripts/validation/staging-config.example.json` está vacía deliberadamente. Completar fuera del checkout. La preparación rechaza valores vacíos, valores conocidos de main/qa que apuntan a producción, número/proyecto inconsistente, paquete estable y gateway ajeno a Apps Script HTTPS. No puede demostrar por sí sola que un proyecto desconocido pertenezca a staging: confirmar su propiedad y configuración antes de usarlo.

## Preparación reproducible

Desde la raíz del repositorio, usando rutas absolutas:

```sh
python3 scripts/validation/prepare_staging.py \
  --config /ruta/segura/staging-client.json \
  --expected-project ID_FIREBASE_STAGING \
  --output /workspace/pag-staging-config-NUEVO

JAVA_HOME=/workspace/toolchains/jdk-17.0.17+10 \
ANDROID_HOME=/workspace/toolchains/android-sdk \
GRADLE_USER_HOME=/workspace/toolchains/gradle-home \
/workspace/toolchains/gradle-8.13/bin/gradle \
  -I /workspace/Pineda-Insurance-Group/scripts/validation/staging.init.gradle \
  -PpagStagingOverlay=/workspace/pag-staging-config-NUEVO \
  -p /workspace/Pineda-Insurance-Group/pag-leads-android \
  -Djavax.net.ssl.trustStore=/etc/ssl/certs/java/cacerts \
  -Dhttps.proxyHost=proxy -Dhttps.proxyPort=8080 \
  assembleStaging assembleStagingAndroidTest lintStaging --no-daemon --max-workers=2
```

No combinar con qa.init.gradle, que retira INTERNET. Las fuentes originales conservan sus valores; únicamente la variante staging carga el overlay completo. El comprobante SHA del overlay detecta cambios accidentales, no es una firma ni una autorización de despliegue.

Antes de instalar: comprobar aapt badging (ID .staging, versión -STAGING), recursos compilados y manifiesto, apksigner, hashes y ausencia de URLs/IDs productivos en recursos fusionados. No distribuir el APK conectado hasta esa comprobación.

```sh
python3 scripts/validation/device_preflight.py \
  --serial SERIAL_AUTORIZADO \
  --apk /ruta/app-staging.apk \
  --report /workspace/preflight-NUEVO.json
```

El preflight es de solo lectura. Si ya existe una instalación .staging, detenerse para revisar firma y fixtures; no usar `adb install -r` ni `pm clear` automáticamente. Registrar modelo/API y huellas de certificados estables solo si el propietario lo autoriza; no extraer sus datos.

Tras instalación nueva exclusivamente en dispositivo dedicado, iniciar manualmente sesión con cuenta sintética. Ejecutar el runner con los identificadores de pruebas, sin contraseñas ni tokens como argumentos:

```sh
adb -s SERIAL_AUTORIZADO shell am instrument -w \
  -e expectedProject ID_FIREBASE_STAGING -e expectedUid UID_SINTETICO \
  com.pinedaagencygroup.leads.staging.test/com.pinedaagencygroup.leads.StagingFunctionalInstrumentation
```

El runner requiere .staging y proyecto/UID explícitos, renueva token, lee perfil desde servidor, obtiene token FCM y prueba un almacén local sintético de TokenVault. No imprime credenciales, no escribe Firestore y no envía notificaciones/mensajes. Un PASS del runner no certifica los casos siguientes.

## Matriz de aceptación (todos pendientes en dispositivo)

| Caso | Preparación / acción | Evidencia esperada |
|---|---|---|
| Auth | Login email y Google en staging, logout, reinicio | UID/proyecto correctos; nunca se pasa token a JavaScript ni logs |
| Revocación | Suspender solo cuenta sintética en staging, volver al primer plano | Gate cerrado; callbacks antiguos no muestran datos |
| Aislamiento | Dos agentes con prospectos ficticios distintos | Cada uno ve solo sus asignaciones; acceso cruzado denegado por reglas |
| Sync | Dos dispositivos/perfiles de pruebas editan una nota ficticia con revisión conocida | Auditoría atómica, conflicto visible, borrador conservado; sin duplicar eventos |
| Offline | Cortar conectividad tras cargar fixture | Estado obsoleto indicado; ninguna autorización nueva por caché |
| Notificaciones | Denegar/permitir POST_NOTIFICATIONS, preferencias apagadas | Sin crash; estado de permisos respetado. No enviar push a usuarios reales |
| FCM | Obtener token del dispositivo de pruebas | Registro restringido al proyecto de pruebas. Recepción de un push sintético requiere ruta staging dedicada, sin topics ni multicast |
| Privacidad | Vista recientes/pantalla bloqueada, contenido ficticio | Sin datos de contacto ni tokens; FLAG_SECURE respetado |
| Upgrade | APK semilla sintético con MISMO ID .staging y MISMA firma, origen file y preferencias antiguas | Notas/borradores conservados, token migrado AES-GCM, plaintext retirado |
| Interrupción | Cerrar durante migración, reiniciar; simular falta de espacio/JSON corrupto | Error recuperable, sin éxito ficticio ni pérdida silenciosa |
| Keystore | Fixture nuevo/tamper; reinicio; dispositivo diferente | Corrupción falla cerrada, reautenticación segura, no exportación de claves |
| WebView | URLs externas/iframe/script inválido con fixtures | Sin acceso al puente desde origen externo; navegación controlada |

No instalar binarios productivos como semilla. El runner UpgradeStorageInstrumentation anterior espera fixtures y paquete legado: no usarlo directamente con .staging ni contarlo como aprobado. Falta preparar y probar la semilla aislada de actualización cuando exista dispositivo; hasta entonces la migración real permanece pendiente.

Para cada caso registrar PASS/FAIL/BLOCKED/NOT_RUN, fecha, APK SHA256, API/WebView/Play Services, fixture, expected/actual, evidencia sin PII y limpieza solo de fixtures staging. Logs de dispositivo deben filtrarse; no capturar tokens ni exportar bases estables.
