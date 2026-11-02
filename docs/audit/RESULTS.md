# Resultados y reproducción

## Validación local

- Node PAG 1.9: siete archivos de suite pasan, incluyendo nuevas pruebas de persistencia sin credenciales y migración idempotente/inyección. El runner del entorno resume archivos; no interpretar siete como total de aserciones.
- Java `AccessCheckTest`: pasa con `-ea`, cubre pausa, reanudación, cambio de cuenta y cancelación.
- PAG 1.8: cinco archivos de suite pasan.
- CRM bridge: cinco archivos de suite pasan; solo mocks/dry-run.
- Firestore: bloqueado antes de ejecutar tests por 403 descargando JAR de storage.googleapis.com.
- Instrumentación Android: compilación solicitada; ejecución pendiente por ausencia de emulador/dispositivo. Las pruebas de vault requieren Android Keystore real.
- Git diff --check: pasa.
- Escaneo limitado del historial: 507 blobs, cero candidatos en firmas seleccionadas; no equivale a escaneo exhaustivo.
- Taty Nails: CRC del ZIP base válido, overlays y build pendientes.

## Comandos

Desde `/workspace/Pineda-Insurance-Group`:

```sh
node --test pag-leads-android/tests/*.test.cjs pag-leads-private-api/*.test.cjs firebase/functions/tests/*.test.cjs
mkdir -p /tmp/pag-access-test
/workspace/toolchains/jdk-17.0.17+10/bin/javac -d /tmp/pag-access-test pag-leads-android/app/src/main/java/com/pinedaagencygroup/leads/AccessCheck.java pag-leads-android/tests/AccessCheckTest.java
/workspace/toolchains/jdk-17.0.17+10/bin/java -ea -cp /tmp/pag-access-test com.pinedaagencygroup.leads.AccessCheckTest
export JAVA_HOME=/workspace/toolchains/jdk-17.0.17+10
export ANDROID_HOME=/workspace/toolchains/android-sdk
export GRADLE_USER_HOME=/workspace/toolchains/gradle-home
/workspace/toolchains/gradle-8.13/bin/gradle -p pag-leads-android -Djavax.net.ssl.trustStore=/etc/ssl/certs/java/cacerts -Dhttps.proxyHost=proxy -Dhttps.proxyPort=8080 -Dhttp.proxyHost=proxy -Dhttp.proxyPort=8080 :app:assembleQa :app:assembleDebugAndroidTest :app:lintQa --no-daemon --max-workers=2
```

El almacén CA del entorno mantiene verificación TLS; no usar trust-all ni desactivar TLS. JDK17 y Gradle8.13 se instalaron con SHA256 oficiales. Repetir reglas desde `firebase` mediante `npm run test:rules` una vez autorizado storage.googleapis.com. No sustituir demo-pag-leads por un proyecto real.

API GitHub bloqueada (Forbidden en api.github.com); preparar PR remoto requiere acceso a ese dominio y permisos adecuados. No solicitar PAT por fallo de `gh auth status`: Git usa autenticación de proxy independiente.

## Resultado final Android

`assembleQa`, `assembleDebugAndroidTest` y `lintQa`: **BUILD SUCCESSFUL**, 98 tareas (8 ejecutadas, 90 actualizadas) en la última ejecución. Se corrigieron siete errores WrongConstant preexistentes. Permanecen advertencias de APIs/dependencias, traducción y uso de JavaScript; no se silenciaron comprobaciones. APK QA y APK de instrumentación generados localmente; no instalados ni publicados.
