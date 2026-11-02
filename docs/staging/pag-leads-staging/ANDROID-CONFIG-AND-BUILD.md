# Obtener configuración autorizada y preparar APK

## Acceso probado y faltante

La sesión puede leer el Git existente. No tiene una identidad Google/Firebase operativa: `firebase apps:list ANDROID --project pag-leads-staging --non-interactive --json` falla con Failed to authenticate. Hay un fichero de configuración CLI pero no se leyó su contenido ni se extrajeron credenciales. Runtime no ofrece bindings/identidad GCP. No se encontró google-services.json de staging en archivos transferidos.

El proxy además rechaza CONNECT a firebase.googleapis.com y pag-leads-staging.firebaseapp.com. Se guardaron esas adiciones y oauth2.googleapis.com en el borrador del entorno, preservando dominios previos de GitHub/Storage. Revisión/guardado y publicación de la configuración del entorno de desarrollo aplican el cambio; no son despliegue de la app. No se publicó ese entorno en esta sesión.

Canales válidos, sin secretos en chat:

1. Firebase Console autenticada → proyecto existente → configuración → app Android ya registrada → descargar google-services.json actualizado. Colocarlo en un archivo local autorizado fuera del checkout o indicar el recurso compartido que ChatGPT Work haya generado.
2. Sesión Firebase CLI/Google autorizada en este entorno con permisos de lectura de apps/configuración del proyecto: Firebase Viewer (`roles/firebase.viewer`) o rol personalizado de lectura validado contra las operaciones de listar apps/obtener configuración SDK; no asumir permisos adicionales sin comprobar el error concreto de la API. Probar la operación específica; no pedir admin de producción. Para registrar SHA/OAuth el propietario puede usar su consola, no es necesario ceder ese permiso a esta sesión.

Si se habilita el CLI, listar apps Android del proyecto indicado y usar `firebase apps:sdkconfig ANDROID APP_ID_REAL --project pag-leads-staging`; no inventar APP_ID a partir del número de proyecto. No imprimir tokens ni copiar credenciales a Git.

Datos realmente pendientes del archivo autorizado: mobilesdk_app_id de la app existente, API key CLIENTE del staging y OAuth Web Client ID. La API key Firebase cliente es configuración pública, no una cuenta de servicio; no reemplaza reglas ni autenticación. La configuración no puede reconstruirse solo con project ID y project number.

## Importación y build (no ejecutados con configuración real todavía)

```sh
python3 scripts/validation/import_staging_android.py \
  --google-services /ruta/autorizada/google-services.json \
  --output /workspace/pag-leads-staging-client-NUEVO
```

Por defecto el gateway queda vacío: variante auth-only. No se usa URL de producción como fallback. Cuando exista el gateway de pruebas independiente, pasar `--gateway-url-file /ruta/autorizada/staging-gateway-url.txt`. El importador exige project ID/number/paquete exactos y cliente OAuth web del proyecto correcto; falla ante datos ausentes/ambiguos.

```sh
JAVA_HOME=/workspace/toolchains/jdk-17.0.17+10 \
ANDROID_HOME=/workspace/toolchains/android-sdk \
GRADLE_USER_HOME=/workspace/toolchains/gradle-home \
/workspace/toolchains/gradle-8.13/bin/gradle \
  -I /workspace/Pineda-Insurance-Group/scripts/validation/staging.init.gradle \
  -PpagStagingOverlay=/workspace/pag-leads-staging-client-NUEVO \
  -p /workspace/Pineda-Insurance-Group/pag-leads-android \
  -Djavax.net.ssl.trustStore=/etc/ssl/certs/java/cacerts \
  -Dhttps.proxyHost=proxy -Dhttps.proxyPort=8080 \
  assembleStaging assembleStagingAndroidTest lintStaging --no-daemon --max-workers=2
```

Antes de entregar: extraer badging/permisos/recursos, comprobar package .staging, project pag-leads-staging, número301600139735, appId real, host de enlaces staging y gateway vacío o staging aprobado. Verificar apksigner y zipalign, registrar SHA256 del APK y certificado. Rechazar cualquier recurso productivo conocido en el artefacto; revisar rutas legacy deshabilitadas. No instalar ni sustituir versiones estables.

En dispositivo, confirmar proyecto mediante FirebaseApp options y requests dirigidos al project staging; filtrar logs/capturas, sin tokens. Los dominios Auth/Firestore son compartidos: mirar solo el hostname no demuestra aislamiento. Verificar projectId/audience/rutas sin registrar token completo. Pruebas de Google/correo/sync/FCM permanecen pendientes, no aprobadas por la compilación.

Firestore cerrado significa que auth puede completarse pero la lectura de perfiles/sync será denegada. No abrir reglas para ocultar ese resultado; preparar las identidades aprobadas y revisar emuladores primero.
