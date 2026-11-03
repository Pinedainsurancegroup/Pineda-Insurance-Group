# Instalación segura y pruebas funcionales pendientes

Este procedimiento está preparado, no ejecutado. Usar teléfono de pruebas con Google Play Services y datos sintéticos. El APK auth-only puede comunicarse con Firebase staging; no contiene gateway. No pulsar envío de enlaces de correo, recuperación por correo, campañas, WhatsApp o SMS. Ningún envío real está autorizado.

## Instalación sin sustituir aplicaciones

1. Descargar PAG-Leads-1.9-STAGING-auth-corrected.apk y SHA256SUMS.txt del directorio de artefactos de QA-CORREGIDA.md. Comparar sha256sum, apksigner verify --print-certs y aapt2 dump badging con el informe. Exigir paquete exacto com.pinedaagencygroup.leads.staging y certificado QA; abortar ante discrepancias.
2. Activar depuración USB y autorizar únicamente el ordenador de pruebas. Ejecutar adb devices -l y seleccionar explícitamente su serial en todos los comandos mediante adb -s. No ejecutar sobre un dispositivo desconocido.
3. Consultar con adb -s SERIAL shell pm path com.pinedaagencygroup.leads y anotar solo presencia/versión (dumpsys package). Consultar igualmente .staging y .staging.test. Si ya existe staging, detener instalación para conservar sus datos; no desinstalar ni usar -r, -d, pm clear o uninstall.
4. Ejecutar adb -s SERIAL install /workspace/pag-staging-lintfix-auth-v2/artifacts/PAG-Leads-1.9-STAGING-auth-corrected.apk solo cuando staging no exista. El comando no lleva -r. Alternativa: copiar este APK verificado al teléfono e instalarlo como PAG Leads STAGING; cancelar cualquier aviso de actualización/reemplazo.
5. Confirmar que PAG Leads estable sigue instalada y con la misma versión. Abrir únicamente PAG Leads STAGING. Revocar después el permiso de instalar APK al gestor de archivos si se concedió.
6. Instrumentación opcional: verificar también paquete .staging.test, certificado y checksum; instalar sin -r únicamente si no existe. Requiere usuario sintético ya autenticado y UID explícito. No ejecutar antes de cumplir reglas/fixtures.

## Matriz de pruebas y resultados esperados

Registrar versión Android, Play Services/WebView, checksum APK, certificado, caso, PASS/FAIL y evidencia sin tokens ni datos personales. Todo caso sigue PENDIENTE EN DISPOSITIVO.

| Área | Caso sintético | Resultado esperado / prerrequisito |
|---|---|---|
| Google | Sin cuenta, cancelación, cuenta QA, token expirado y cambio de cuenta | Mensaje recuperable sin crash; token/usuario solo staging; revocación borra acceso local. La cuenta Google debe estar controlada para QA. |
| Correo/contraseña | Cuenta creada por administrador staging; contraseña incorrecta y válida | Fallo seguro o autenticación staging; no autorregistro de privilegios. OwnerPasswordAccess restringe el acceso a owner: verificar antes que el fixture aprobado sea compatible; no reutilizar identidad productiva. |
| Enlace de correo | Enlace inválido, vencido o de proyecto ajeno | Rechazo sin revelar datos. Generar/consumir enlaces válidos solo en emulador local; no enviar correos reales. |
| Firestore cerrado | Usuario autenticado intenta leer perfil | PERMISSION_DENIED esperado, sin abrir acceso como solución. |
| Reglas mínimas | Emulador: usuario aprobado, ajeno, sin verificar, anónimo, escritura/listado | Solo GET propio aprobado permitido; resto denegado. test:staging-identity y test:rules deben pasar. No desplegar estas reglas automáticamente. |
| Sincronización | Fixtures de dos agentes/tenants, revocación, offline/reintento, duplicados y respuesta tardía | Aislamiento, idempotencia y ausencia de UI obsoleta. Pruebas Node locales pasan; integración positiva pendiente de reglas/servicio QA. |
| Notificaciones | Permiso Android concedido/denegado, canales y token FCM staging | Sin crash ni mensajes enviados. Token no se imprime; recepción push E2E queda pendiente por prohibición de envíos. |
| Recuperación | Solo preferencias sintéticas staging: corrupción cifrada, reapertura, logout y migración | Fallo cerrado y datos originales preservados. No usar fixture histórico con package estable ni copiar datos de producción. |
| Red | Opciones Firebase activas, proyecto/audience y rutas de requests | Solo pag-leads-staging; no basta observar hostname compartido Google. Captura sin tokens/cuerpos de datos, sin desactivar TLS. |
| Servicio legacy | Intento de iniciar servicio staging explícitamente | Servicio disabled, sin foreground/polling; protección adicional en onCreate/onStartCommand. |

Con fixtures y reglas aprobadas, ejecutar instrumentación con adb -s SERIAL shell am instrument -w -e expectedProject pag-leads-staging -e expectedUid UID_SINTETICO com.pinedaagencygroup.leads.staging.test/com.pinedaagencygroup.leads.StagingFunctionalInstrumentation. SERIAL y UID son valores del dispositivo/fixture, no credenciales. Con Firestore cerrado esta instrumentación debe fallar en lectura de perfil; no presentarlo como un defecto de autenticación.

La instrumentación comprueba renovación de token, lectura de perfil servidor, obtención de token FCM y almacenamiento cifrado sintético. No acredita recepción push, sincronización completa ni migración real entre versiones. No instalar automáticamente ni otorgar permisos con -g.
