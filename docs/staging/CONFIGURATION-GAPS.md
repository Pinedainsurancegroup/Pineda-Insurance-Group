# Configuración Firebase existente y diferencias necesarias

| Elemento inspeccionado | Estado comprobado en Git | Falta para staging independiente |
|---|---|---|
| Android main/res/values/firebase_config.xml | Define proyecto activo, appId, apiKey pública, sender, OAuth y gateway | Los seis campos de un proyecto/app/gateway nuevos de pruebas; no herencia de esos valores |
| Android qa/res/values/firebase_config.xml | Solo reemplaza appId/gateway; resto heredado | No basta un applicationIdSuffix. Registrar `.staging` y reemplazar configuración completa |
| AndroidManifest.xml | Host de enlace Firebase fijado al proyecto activo | Overlay staging con actividad/intent-filter del host de pruebas; generado por prepare_staging.py |
| EmailInvitationAccess.java | Forma dominio desde projectId | Mantener coherencia entre projectId, dominio Auth y manifest/assetlinks de staging |
| SparkOwnerGateway.gs | Constante de proyecto activo; usa propiedades de script | Nuevo standalone con constante staging, nuevo Owner UID/Sheet ID, propiedad Sheet name; acceso de lectura solo a hoja de pruebas |
| firebase/firebase.json | Reglas y functions; emuladores Auth/Firestore | Config separado sin Functions/senders y sin default alias; generador preparado |
| firebase/firestore.rules | Reglas 1.9 con roles, asignación y auditoría | Misma candidata versionada, bootstrap deny-all; pruebas emuladas aún pendientes |
| Índices | No hay fichero de índices actual | Inventario de consultas y validación en staging; fichero vacío generado no acredita suficiencia |
| .firebaserc | No existe en raíz firebase | Alias staging separado, sin default; comandos explícitos de proyecto |
| google-services.json | No encontrado versionado; está ignorado | Puede obtenerse de la app staging registrada; cliente actual usa recursos custom, no depende del plugin Google Services |
| Functions | Callable alternativa con defineSecret PAG_PRIVATE_API_URL/TOKEN | No requerida por el cliente Apps Script actual. No copiar secretos ni desplegar por defecto |
| Cuenta/ADB/staging | No disponibles en el entorno | Intervención del propietario según ACCESS-CHECKLIST.md |

Ninguna URL, ID ni etiqueta QA del código demuestra qué corre en producción. No se consultó producción. No se crearon cuentas ni proyectos y no se generó configuración con claves inventadas. Los proyectos demo de los tests son identificadores locales sin autenticación.

Preparación adicional: generación de manifiesto staging y hash para impedir herencia accidental del host estable. Su XML pasa pruebas estáticas. El nuevo manifiesto fusionado, registro de dominio y links aún requieren validación con configuración real y dispositivo; no se reconstruyeron APK offline ni se compiló un APK conectado con fixtures.
