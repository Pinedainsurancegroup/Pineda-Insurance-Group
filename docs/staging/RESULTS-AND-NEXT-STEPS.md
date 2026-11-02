# Preparación técnica independiente de PAG/PIG

## Entregado

- Revisión de configuración existente y diferencias para staging: CONFIGURATION-GAPS.md.
- Generador local prepare_firebase_staging.py: reglas bootstrap deny-all, copia exacta de reglas candidatas, alias staging sin default, configuración sin Functions y gateway nuevo parametrizado al proyecto de pruebas. Solo prepara archivos, no autentica ni despliega.
- Corrección de preparación Android: manifiesto staging con dominio Auth independiente y hashes de recurso/manifiesto; evita heredar el filtro de enlaces de la versión estable. Sin cambios de comportamiento de aplicaciones estables.
- Recuperación del puente CRM con SHA256 y procedencia; búsqueda ampliada en historial/archivos. No se encontró fuente completo de AI/CRM v22/Receiver v23 dentro del alcance examinado.
- Procedimiento para teléfono y accesos con ubicación exacta: ACCESS-CHECKLIST.md. Matrices funcionales previas siguen vigentes.

## Pruebas locales ejecutadas

- Node PAG + contratos aislados: 51/51 pasan.
- Bridge recuperado: 161/161 pasan.
- Python de validación/preparación: 10/10 pasan. Los casos locales usan identificadores demo/datos de unidad temporales; no se autenticó con claves inventadas ni se creó un backend/configuración conectado.
- Sintaxis de 10 fuentes GS/JS/CJS y AST de 9 archivos Python: pasan.
- git diff --check: pasa.

No se repitieron compilaciones offline, ni se generó/instaló un APK conectado. No se usaron cuentas, contraseñas, tokens ni claves privadas para estas tareas. No se enviaron mensajes ni se ejecutaron scripts sobre servicios reales.

## Pendientes genuinos

- Identificar/crear proyecto Firebase staging, registrar app/OAuth/dominio y disponer de gateway/hoja/cuentas de prueba. No hay esos recursos ni configuración en el entorno.
- Firestore emulator y reglas: las aserciones siguen sin ejecutar por JAR bloqueado. No se confunde revisión estática/copia de reglas con validación efectiva de autorización.
- Android real autorizado: falta dispositivo/ruta ADB. No se comprobó login, sincronización, notificaciones ni migración en dispositivo.
- Nuevo manifiesto staging: validado estructuralmente por tests; falta fusionado/empaquetado con configuración real y verificación de dominio/assetlinks.
- PR API: bloqueo de red previo; borrador de dominios requiere aplicarse en el entorno de desarrollo. Procedimientos manuales ya preparados, sin PR creado/fusión.
- Fuentes adicionales: URL exacta/export autorizado y lectura de PAG AI, PAG CRM v22, WhatsApp Receiver v23.

Ningún proyecto se declara listo para producción. El siguiente paso requiere únicamente las intervenciones concretas listadas en ACCESS-CHECKLIST.md; todo el material preparatorio es local y versionado.
