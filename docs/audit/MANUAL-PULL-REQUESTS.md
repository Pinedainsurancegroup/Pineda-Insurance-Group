# Pull Requests: diagnóstico y apertura manual

El proxy devuelve HTTP403 al CONNECT hacia api.github.com antes de establecer TLS con GitHub. Reproducido con curl sin cabeceras de autenticación. El repositorio puede recibir push a través del proxy Git, pero esto no demuestra permisos API ni permiso para abrir PR.

Se guardaron api.github.com y storage.googleapis.com como adiciones a los dominios personalizados del borrador del entorno, conservando presets. Guardar el borrador no modifica la red en ejecución. Revisar/guardar esos cambios y publicar el entorno en su configuración; esto publica la configuración del entorno de desarrollo, no una versión de las aplicaciones. Después, comprobar el estado de red y repetir la consulta autenticada. Si la conexión llega a GitHub, distinguir entonces errores de credencial, autorización de aplicación y permisos de repositorio. No insertar un PAT en chat ni asumir que GH_TOKEN es una credencial Git utilizable.

## Alternativa desde el navegador autenticado

1. Abrir el enlace de comparación correspondiente y confirmar que base/head son los indicados.
2. Seleccionar **Create pull request**, pegar la descripción y elegir **Create draft pull request**.
3. Adjuntar resultados de pruebas; dejar pendiente instrumentación, Firestore y pruebas de actualización. No fusionar, desplegar ni publicar APK como release.

PAG Leads:
https://github.com/Pinedainsurancegroup/Pineda-Insurance-Group/compare/pag-leads-v1.9-agents...dev/pag-security-audit-20261102?expand=1

Base: pag-leads-v1.9-agents. Head: dev/pag-security-audit-20261102. Usar PR-DRAFT.md y VALIDATION-PACKAGES-2026-11-02.md. No seleccionar main: incorporaría el desarrollo 1.9 completo además de las correcciones.

PIMFLEX:
https://github.com/Pinedainsurancegroup/Pineda-Insurance-Group/compare/pimflextv-production-hardening...dev/pimflex-lint-20261102?expand=1

Base: pimflextv-production-hardening. Head: dev/pimflex-lint-20261102. Descripción: «Corrige once errores lint de compatibilidad API23/Media3 sin alterar el transporte. APK debug y lint pasan. Transporte HTTP/redirecciones, pruebas de login/stream y dispositivos siguen pendientes. Sin despliegues ni firma de distribución.»

Si GitHub no muestra Create pull request al usuario autenticado, revisar permisos del repositorio y políticas de la organización desde esa sesión. Hasta entonces, no se puede atribuir el bloqueo actual a falta de permisos.
