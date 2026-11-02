# Validación y paquetes de prueba — 2026-11-02

## Resultado

Fuentes verificadas: PAG `aa74ef9`, PIMFLEX `8a0de0f`; Taty rama `64a333bf8baa0d6f5785ff6e56b33ca9dbe787ae` reconstruida con overlays según FOLLOWUP. No se modificaron las fuentes de esos commits para construir los APK. Los ajustes de empaquetado están en scripts/validation/qa.init.gradle y offline-manifest.xml; el manifiesto generado de cada APK se comprobó con aapt.

| Proyecto | Variante / código | ID instalado del paquete de prueba | Resultado |
|---|---|---|---|
| PAG Leads | 1.9-INVITATIONS-QA3-QA-OFFLINE / 18 | com.pinedaagencygroup.leads.qa | assembleQa, assembleDebugAndroidTest, lintQa pasan |
| PIMFLEX TV | 2.1.1-AUDIT-OFFLINE / 12 | com.pimflextv.next.audit | assembleDebug, lintDebug pasan |
| Taty Nails | 4.1-AUDIT-OFFLINE / 5 | com.tatynails.app.audit | assembleDebug, lintDebug pasan |

El número PIMFLEX procede del build.gradle/APK, no de su texto de UI ni de una versión instalada desconocida. Los identificadores .qa/.audit evitan sustituir las aplicaciones estables con IDs originales. Podrían existir otras instalaciones QA con el mismo ID: no reemplazarlas sin revisar firma y datos.

## Pruebas

- PAG UI/lifecycle, migración, Apps Script y Functions: 45 pasan. `node --test --test-isolation=none pag-leads-android/tests/*.test.cjs pag-leads-private-api/*.test.cjs firebase/functions/tests/*.test.cjs`.
- AccessCheck Java con aserciones habilitadas: pasa.
- Bridge CRM, commit fbbe987e83ae4b4153f1dfe4d7bc051ca80f69bc: 161 pruebas pasan, todas aisladas.
- Nuevos contratos de integración: 6 pasan; STOP, pausa, evidencia obsoleta/cruzada, propuesta superada, AI sin autorización de envío y reconciliación sin reenvío. Ver integration-sandbox/README.md para procedencia y limitaciones.
- Gradle testQaUnitTest/testDebugUnitTest: NO-SOURCE en los tres proyectos. No contar como tests unitarios ejecutados.
- Firestore: reintentado npm run test:rules exclusivamente con demo-pag-leads. Bloqueo 403 al descargar el emulador desde storage.googleapis.com; aserciones no ejecutadas.
- Instrumentación Android: APK compilado, no ejecutado. Sin dispositivo/emulador ni /dev/kvm en la máquina. El runner de actualización existente requiere fixtures/paquetes exactos; no se entrega como una prueba ya pasada.
- iOS fuera del paquete Android: no disponible Swift/Xcode/macOS; no ejecutado.

## Entrega y firma

APK disponibles localmente en /workspace/test-packages-20261102. Cada APK tiene informe .signature.txt y .manifest.txt; manifest.json y SHA256SUMS.txt registran hashes de archivo y certificado. Todos verifican con apksigner y pasan zipalign. Firmados con certificado Android Debug, huella SHA256:

`538c07ce2b208fd500bb4b1731164816d2c99cd3a65616030f725850f4e49781`

No se usaron certificados de producción. No se subieron APK a Git ni se publicaron releases. scripts/validation/build_all.py y package_apks.py permiten reproducir el proceso en las rutas de este workspace; los logs quedan en /workspace/validation-20261102. La primera preparación detectó versión/firma QA no finalizada: se corrigió el override usando finalizeDsl y se repitieron compilaciones y comprobaciones. Los hashes del manifiesto corresponden únicamente a los archivos finales.

## Restricciones de los paquetes

Los APK entregados NO contienen permiso INTERNET. Taty además NO contiene READ_CALENDAR/WRITE_CALENDAR. Es una variante offline para revisión local: PAG no puede autenticar/leer leads; PIMFLEX no puede reproducir streams; Taty no puede sincronizar calendario. Esas limitaciones impiden que el paquete de prueba contacte servicios activos. No se ejecutaron ni instalaron durante la sesión.

Se mantienen sin verificar: actualización real de almacenamiento/WebView, Android Keystore, permisos, identidad Firebase en staging, login/streaming PIMFLEX y calendario Taty con fixtures. Los APK offline no sustituyen esas pruebas. Preparar recursos Firebase/proveedor y datos ficticios en staging autorizado antes de una candidata conectada. Mantener sendEnabled=false y AI en modo propuesta.

## Red y Pull Requests

El proxy continúa devolviendo 403 a CONNECT para api.github.com y storage.googleapis.com. Guardadas adiciones de esos dominios en el borrador del entorno; requieren revisión/guardado y publicación de la configuración de desarrollo para aplicarse. No se publicó el entorno en esta tarea. No se ha determinado falta de permisos de PR, porque la conexión no llega a GitHub. Ver MANUAL-PULL-REQUESTS.md con enlaces y pasos para crear ambos PR como borrador desde navegador.

## Decisión de estabilidad

Ningún proyecto se declara listo para producción. Puertas pendientes: instrumentación y reglas Firestore, actualización/recuperación con fixtures, TLS/redirects y login PIMFLEX, backup/notificaciones/calendario Taty, fuentes de CRM/AI/Receiver y revisión humana de cambios. Sin despliegues, fusiones, envíos ni modificaciones de datos reales.
