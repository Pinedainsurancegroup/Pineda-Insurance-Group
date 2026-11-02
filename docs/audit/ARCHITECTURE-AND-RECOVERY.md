# Separación propuesta y recuperación

No se crean repositorios ni se cambia visibilidad en esta tarea.

| Repositorio privado propuesto | Fuente | Responsabilidad |
|---|---|---|
| pag-leads-android | pag-leads-android en 1.9 | UI, identidad del dispositivo, cliente Firebase; ningún secreto servidor embebido |
| pag-leads-backend | firebase + pag-leads-private-api | Reglas, Functions, Apps Script, contratos y pruebas de autorización |
| pag-crm-bridge | pag-leads-bridge en rama CRM | Adaptadores aislados, dry-run por defecto, STOP/BAJA, deduplicación y único respondedor |
| pimflex-tv-android | pimflextv-rebuild en hardening | Reproducción y contrato de proveedor |
| pimflex-tv-ios | pimflextv-ios en rama iOS | SwiftUI/AVKit, Keychain y pruebas Xcode |
| taty-nails | reconstrucción base + overlays verificados | Fuentes legibles, assets y build reproducible |
| pag-ai / pag-crm / whatsapp-receiver | fuentes pendientes | No inferir implementación a partir del bridge |

Migración: congelar SHA origen, inventariar licencias y archivos LFS/submódulos, escanear secretos y PII incluyendo ZIPs, importar historia por ruta en repositorios privados, verificar hashes/contenido, ejecutar CI de pruebas aisladas y documentar contratos versionados. No borrar ramas originales ni rotar secretos sin plan aprobado. Ninguna transferencia pública de fuentes adicionales.

Versiones verificadas: main Android 1.7; 1.9 versionCode 18 / 1.9-INVITATIONS-QA3, AGP 8.13.2, Gradle 8.13, SDK compile/target 35, min 23, Firebase BOM 34.19.0, Credentials 1.3.0, googleid 1.1.1; añadido WebKit 1.12.1. PIMFLEX hardening declara 2.1.1/code12, compile36/target35/min21, Media3 1.4.1, libVLC 3.7.6; no equiparar estas etiquetas con versión instalada. iOS README declara candidata 0.1.0. Firebase tests fija firebase12.19.0, rules-unit-testing5.0.2, firebase-tools15.31.0; Functions espera Node22.

Recuperación antes de cualquier despliegue: registrar SHA, checksum y certificado de firma del APK instalado; exportar reglas/configuración y versionar Apps Script; mantener certificados fuera de Git y respaldos cifrados de datos con prueba de restauración en sandbox. Separar claves QA/producción, IDs y proyectos Firebase. Realizar simulacro con datos ficticios.

Rollback de este PR: revertir commit en desarrollo y reconstruir QA. No instalar una versión antigua sobre datos migrados sin ensayo: el token ya no estará en preferencias planas y el origen WebView habrá cambiado. Mantener notas originales durante transición; recuperar acceso mediante autenticación/reaprovisionamiento, nunca descifrar/exportar tokens para restaurarlos en texto plano. Android Keystore no se transfiere entre dispositivos; el respaldo se excluye deliberadamente. Ningún rollback automático de reglas o bases reales.

CI recomendado: Node22 + JDK17 + Gradle8.13; tests Node/Java, emuladores demo de reglas, instrumentación Android con fixtures, lint, escáner de secretos, dependencias con lockfiles y artefactos QA privados. Publicación y envíos requieren workflow separado y aprobación humana.
