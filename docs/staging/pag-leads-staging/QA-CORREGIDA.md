# QA staging corregida

Base 92add6c; rama dev/pag-security-audit-20261102. Configuración auténtica importada fuera del checkout, sin gateway. No se publicó el JSON ni se instalaron APK o desplegaron servicios.

## Cambios y resultados

LeadMonitorService permanece declarado con specialUse pero deshabilitado en el manifiesto staging. El tipo se indica también en el overlay porque lint inspecciona ese manifiesto. onCreate y onStartCommand rechazan staging antes de iniciar foreground/polling. La variante estable conserva su comportamiento. No se añadió SuppressLint, baseline ni desactivación de diagnósticos.

Google distingue NoCredentialException y permite reintentar tras añadir una cuenta de pruebas. Los identificadores Firebase son recursos no traducibles: se evita que traducciones alteren valores técnicos, sin cambiar sus valores.

- assembleStaging, assembleStagingAndroidTest, lintStaging: PASS.
- lint: 0 errores, 42 advertencias; anteriormente 1 error y 45 advertencias.
- Node: 51/51; Python: 14/14, incluida regresión de manifiesto con servicio deshabilitado y tipo explícito.
- Java AccessCheckTest y StagingPolicyTest ejecutados con -ea: PASS.
- testStagingUnitTest: NO-SOURCE; no se presenta como suite adicional aprobada.
- Reglas de identidad: no ejecutadas; la descarga de cloud-firestore-emulator-v1.22.0.jar está bloqueada. No se alteraron reglas remotas para eludirlo.
- APK e instrumentación: apksigner verify y zipalign aprobados. Paquetes .staging y .staging.test, versión app 1.9-INVITATIONS-QA3-STAGING / 18.
- Recursos/manifiesto: pag-leads-staging, 301600139735, flag staging true, gateway vacío, enlace staging, servicio legacy disabled. Sin ID/número productivos conocidos. Esto no sustituye la comprobación dinámica de tráfico en dispositivo.

Artefactos y evidencias: /workspace/pag-staging-lintfix-auth-v2/artifacts; build.log y python-tests.log en su directorio superior. Node y revisión Git: /workspace/pag-staging-lintfix-auth. Configuración y recursos extraídos se mantienen fuera de Git.

## Revisión de las 45 advertencias originales

| Diagnóstico | Original | Actual | Decisión |
|---|---:|---:|---|
| CredentialManagerMisuse | 1 | 0 | Manejar explícitamente ausencia de credenciales Google, sin registrar tokens. |
| Typos | 1 | 0 | Clave API cliente no traducible; no modificar su contenido por sugerencia ortográfica. |
| TypographyDashes | 1 | 0 | Identificadores OAuth no traducibles; conservar guiones ASCII. |
| OldTargetApi | 1 | 1 | target 35 conservado; subir a 36 requiere validar cambios de comportamiento en Android real. |
| GradleDependency | 1 | 1 | compileSdk 35 conservado para esta corrección; actualización separada con compatibilidad. |
| UnusedAttribute | 1 | 1 | fillType del icono requiere API24; comprobar apariencia API23 y preparar fallback visual si difiere. |
| SetJavaScriptEnabled | 1 | 1 | WebView local necesita JS. Se conservan CSP, origen local HTTPS y bloqueos de archivos/red. Pendiente pruebas de ataques/navigation en dispositivo; aviso visible. |
| SetTextI18n | 38 | 38 | Textos españoles/concatenaciones; deuda de internacionalización, sin efecto de autorización. Extraer a recursos con placeholders y probar UI en una siguiente corrección. |

No se suprimió ninguna advertencia. El inventario de ubicaciones se incluye en LINT-INVENTARIO.md.

## Revisión de configuración en Git

Se revisaron 140 archivos rastreados y 2245 objetos alcanzables desde las referencias locales: ningún blob contiene el app ID real ni la API key del adjunto staging. En el árbol rastreado no hay marcadores PEM de clave privada ni JSON service_account. No hay google-services.json, .jks o keystore rastreados. Los recursos cliente Firebase originales de main/qa ya estaban versionados: no son claves privadas, y no se usaron en el APK staging.

Alcance: árbol actual y referencias descargadas; esto no prueba ausencia de secretos de cualquier formato, claves codificadas en históricos, objetos remotos no descargados, artifacts de Actions o forks. No se afirma una auditoría completa de secretos de toda la organización. Antes del commit se revisó la selección de archivos; outputs y JSON quedaron fuera.

## Firma

SHA-1: F0:9F:A0:58:20:BF:2F:B1:88:9E:FF:C2:26:30:05:1E:70:8B:7C:E7

SHA-256: 53:8C:07:CE:2B:20:8F:D5:00:BB:4B:17:31:16:48:16:D2:C9:9C:D3:A6:56:16:03:0F:72:58:50:F4:E4:97:81

Ambos APK coinciden con las huellas QA documentadas. El JSON adjunto acredita coincidencia del cliente OAuth Android/SHA-1. Necesita verificación adicional el registro SHA-256 en Firebase Console → pag-leads-staging → configuración → app com.pinedaagencygroup.leads.staging → huellas. También puede consultarlo una identidad autorizada mediante Firebase Management API. No compartir claves privadas. No se ha consultado el registro remoto en esta sesión.

## Intervención externa indispensable

1. Android de pruebas autorizado con Google Play Services para pruebas funcionales; no hay dispositivo conectado disponible.
2. Permitir la descarga del emulador Firestore en la política de red del entorno; ejecutar ambas suites locales de reglas antes de proponer reglas mínimas en staging.
3. Confirmación del registro SHA-256 por propietario/lector autorizado de staging.
4. Para sincronización positiva: fixtures sintéticos y reglas mínimas revisadas en staging; el gateway de pruebas independiente sigue ausente. Con reglas cerradas se espera denegación, no éxito de sincronización.

La compilación no declara la aplicación lista para producción.
