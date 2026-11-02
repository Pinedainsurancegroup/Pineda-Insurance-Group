# Resultado verificable de preparación funcional

## Trabajo realizado

Sin repetir compilaciones offline. Preparados generador de configuración staging (rechaza recursos productivos conocidos y exige paquete .staging), variante Gradle separada, runner Android staging, preflight de dispositivo de solo lectura y matrices funcionales de PAG/PIMFLEX/Taty. Se conservaron las versiones estables y sus datos; no se instaló ninguna app.

## Validaciones ejecutadas

- `python3 -m unittest discover -s scripts/validation/tests -v`: 6/6 pasan. Incluye campos productivos/vacíos, proyecto/paquete/numero incorrecto, gateway ajeno, preservación de configuración existente, rechazo de APK offline antes de consultar dispositivo y detección de instalación staging ausente sin instalar nada.
- Gradle `processStagingResources` con overlay SINTÉTICO: BUILD SUCCESSFUL, 15 tareas. Valida la preparación de variante, no Firebase real.
- Gradle `compileStagingAndroidTestJavaWithJavac` con overlay SINTÉTICO: BUILD SUCCESSFUL, 29 tareas. Runner compilado; no se ejecutó ni generó APK de staging conectado.
- Preflight real contra APK offline previo: rechazado con código2 como se esperaba, antes de consultar dispositivo. No creó informe de éxito ni instaló nada.
- ADB real: lista de dispositivos vacía. Funcional PAG/PIMFLEX/Taty: NOT_RUN.
- API GitHub: CONNECT HTTP403 del proxy, sin llegar a TLS de GitHub. PR remoto no creado; no se fusionó nada. Procedimiento manual: docs/audit/MANUAL-PULL-REQUESTS.md.
- Búsqueda de fuentes: ramas del repositorio autorizado y referencias locales; página pública del propietario solo enlaza al repositorio ya conocido. No se enumeraron repositorios privados ni se inventaron URLs.
- git diff --check: pasa.

Evidencia local de esta fase: /workspace/functional-preparation/staging-unit-tests.log, staging-resources.log, staging-test-compile.log y offline-rejection.log. La configuración sintética es únicamente un fixture de validación; no se entrega ni describe como un backend funcional.

## Entrega APK

No hay nuevo APK conectado de staging: faltan configuración real del proyecto de pruebas, gateway y cuentas sintéticas. Crear un APK con valores inventados o reutilizar la QA anterior apuntando a servicios activos no cumple el aislamiento solicitado.

Siguen disponibles los APK offline entregados en ada5e1c, sin reconstruirlos:

- /workspace/test-packages-20261102/PAG-Leads-1.9-QA-OFFLINE.apk
- /workspace/test-packages-20261102/PIMFLEX-TV-2.1.1-AUDIT-OFFLINE.apk
- /workspace/test-packages-20261102/Taty-Nails-4.1-AUDIT-OFFLINE.apk

Versiones/firmas/SHA256 en /workspace/test-packages-20261102/manifest.json. Son paquetes offline, no pruebas funcionales aprobadas ni sustitutos de la futura variante staging.

## Acciones externas necesarias

1. Facilitar ID y configuración pública completa Firebase de staging, gateway y fixtures de pruebas; registrar app .staging y firma de depuración en OAuth. No compartir secretos en chat.
2. Conectar un Android autorizado por la ruta ADB/VPN preparada por su propietario. No hay dispositivo remoto inferible ni servicio de device farm conectado.
3. Aplicar el borrador de dominios de red en la configuración del entorno de desarrollo (api.github.com/storage.googleapis.com); esto no publica versiones de aplicaciones. Después verificar acceso y permisos API antes de intentar crear PR borrador.
4. Facilitar las URLs exactas y lectura Git de PAG AI, PAG CRM v22 y Receiver v23, más contratos y servicios de staging detallados en DEVICE-AND-ACCESS-BLOCKERS.md.

Ninguna aplicación está lista para producción. Firebase/FCM real, sincronización entre dispositivos, migración WebView/Keystore en dispositivo, TLS/streaming y calendario permanecen sin validar funcionalmente.
