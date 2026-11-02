# Accesos indispensables y dónde obtenerlos

No enviar contraseñas, tokens, claves privadas ni JSON de cuentas de servicio al chat. Preferir roles delegados de lectura o recursos de prueba; secretos, solo en settings/vault apropiado si llegan a ser necesarios.

| Acceso o dato | Dónde obtenerlo | Para qué se necesita / mínimo |
|---|---|---|
| ID del proyecto Firebase staging y número de proyecto | Firebase Console → Project settings → General (o crear proyecto nuevo de pruebas) | Selección explícita e independiente; el propietario decide región y titularidad |
| App Android `.staging` y sus identificadores públicos | Project settings → Your apps → registrar Android nuevo; google-services.json de esa app | App ID/sender/API key cliente; guardar configuración cliente fuera del checkout. No registrar sobre app estable |
| OAuth web client de pruebas | Google Cloud Console del proyecto staging → APIs & Services → Credentials | Google login; registrar huella debug desde la firma real del APK staging, no copiar clave de firma estable |
| Dominio Auth/links de pruebas y certificados | Firebase Authentication → Settings; configuración Android/assetlinks del proyecto | Email links solo a `.staging`, sin capturar enlaces de app estable |
| Gateway y hoja de pruebas | Google Sheets: hoja nueva; Apps Script: standalone nuevo, no proyecto activo | URL del despliegue de prueba y IDs de hoja/Owner. Esos recursos se crean/revisan por el propietario; no en esta sesión |
| Cuentas y roles sintéticos | Firebase Auth y Firestore del staging confirmado | Owner de pruebas y dos agentes aislados; bootstrap admin autorizado. Sin usuarios reales |
| Android autorizado | Ajustes del teléfono → Opciones de desarrollador → Depuración USB; Android Platform Tools en PC propio | Cable USB con prompt de autorización. Si se usa cloud, ruta ADB/VPN específica proporcionada por propietario; no escanear redes ni exponer ADB a Internet |
| Código PAG AI | GitHub → repositorios privados de propietario/organización, equipo desarrollador; si es Apps Script, editor/exports del proyecto correcto | URL exacta y lectura de fuente/commit/manifest; no dar admin de producción |
| Código PAG CRM v22 | Repositorio privado o export de fuente proporcionado por desarrollador/administrador del despliegue | Fuente ejecutable, dependencias, esquema/migraciones y contratos. HighLevel bridge no es CRM completo |
| Código WhatsApp Receiver v23 | Repositorio o export del servicio webhook, mantenedor del servicio | Fuente, commit desplegado, verificación de firmas, inbox/outbox y payloads de prueba anonimizados. No se necesita enviar mensajes reales |
| Proyecto/servicios de integración staging | Administrador de AI/CRM/Receiver, cuando se localicen | URLs y contratos de prueba; credenciales solo por binding seguro y solo si la fase las necesita |
| API GitHub / emulador Firestore | Configuración del entorno cloud → dominios; borrador ya añade api.github.com y storage.googleapis.com | Aplicar/publicar configuración del entorno de desarrollo. Después comprobar si la autorización API alcanza; Git push no prueba permisos de PR |

## Procedimiento en tu teléfono (sin sustituir versiones estables)

1. Usar preferentemente perfil de pruebas o teléfono dedicado. Anotar versiones estables visibles sin exportar sus datos. No desinstalar, limpiar almacenamiento ni aplicar backups reales.
2. En PC propio instalar Android Platform Tools desde la fuente oficial. Activar depuración USB temporalmente y autorizar únicamente ese PC. Confirmar `adb devices -l`; para esta sesión cloud un cable al PC local no aparece automáticamente: hace falta ruta aprobada o ejecutar las comprobaciones localmente.
3. Verificar SHA256 y certificado del APK de pruebas antes de instalar; comprobar ID con aapt. Solo `.staging` para futuro PAG conectado, `.audit` para PIMFLEX/Taty, o `.qa` para offline anterior. Si ese mismo ID ya existe, detenerse para comparar firma y preservar sus fixtures; no usar reemplazo automático.
4. Instalar SOLO como aplicación nueva desde tu PC/teléfono. No usar `adb install -r`, `-d`, `pm clear` ni cambiar firmas de versiones estables. Los APK offline existentes están en la entrega anterior y no se recompilan aquí.
5. Ejecutar matrices de docs/functional-tests. En PAG conectado usar cuentas reales DE PRUEBA creadas en staging; mientras no exista ese entorno solo se puede revisar la UI offline, no certificar autenticación/sync.
6. PIMFLEX: no tocar servidor/cuentas guardadas de versión estable. Taty: solo citas sintéticas y calendario nuevo exclusivo de pruebas; el APK offline anterior no permite calendario.
7. Registrar PASS/FAIL/NOT_RUN con API/WebView, hash del APK y evidencia sin datos personales. Retirar permisos de depuración al terminar; no enviar logcat sin filtrarlo.

No se pide ninguna credencial por chat. Lo primero indispensable es identificar/crear el proyecto de pruebas, conseguir las URLs de código faltante y conectar un dispositivo; el resto de la preparación está versionado.
