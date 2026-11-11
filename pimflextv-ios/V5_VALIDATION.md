# Validación de la candidata PIMFLEX TV 5.0.0 (8)

## Continuidad

Base: `f7f3cb43b5c287ee776f39f751e1a138f690ea80`, candidata 0.4.0. Nueva rama: `pimflextv-ios-smarters5-20261110`. La estable y PR #6, y la candidata anterior del PR #11, se conservan. La referencia Android nueva es un paquete compilado 5.0/código 108; `REFERENCE_500.md` registra su procedencia y límites. El cambio de numeración iOS no acredita equivalencia con todas las funciones de Smarters.

## Cambios acotados

- Actualización de grupos de audio, subtítulos y variantes HLS al abrir el selector nativo, preservando Automático, Desactivados y opciones manuales válidas. Resultados cancelados o de un item anterior no se aplican. Un límite de calidad que deja de estar disponible vuelve a Automático para evitar una preferencia oculta.
- Se conserva el temporizador de cuatro segundos y sus excepciones de interacción/accesibilidad documentadas en `PLAYER_VALIDATION.md`. Nueva prueba con MP4 real, sin el argumento DEBUG que mantiene controles visibles, para verificar ocultación de cabecera, pausa y progreso mientras continúa la reproducción.
- Versión 5.0.0/build 8 y automatización TestFlight coherente. Se conserva el producto Apple y el proceso de firma existente.
- Artefacto de proyecto Xcode separado del ZIP de simulador, para descargar las fuentes generadas sin incluir una aplicación incompatible con dispositivos.

## Comprobaciones de esta revisión

Comprobaciones locales: 23 tests Python aprobados; sintaxis Bash y diff correctos. Los 60 recursos de la rama estable coinciden byte por byte; todos los recursos de la candidata 0.4.0, núcleo, AppModel, Info.plist y solicitud de firma permanecen intactos. Ruby no está instalado localmente; su comprobación queda en Mac CI. Pendiente registrar el SHA y el resultado de Mac CI después de publicar la candidata. La ejecución anterior `42952718270` sólo valida 0.4.0. El entorno Codex local es Linux, sin Xcode; los tests Python y la inspección estática no sustituyen compilación iOS.

## Límites

Las pruebas usan catálogos ficticios y medios locales propios. No demuestran cuenta/proveedor real, audibilidad física, adaptación HLS multivariante, AirPlay o equivalencia visual completa con Android 5.0. No se ejecutó la APK Android. Los recursos PIMFLEX, núcleo de acceso/catálogos/favoritos, política HTTP/TLS y credenciales se preservan.

La candidata todavía no tiene firma/exportación/carga Apple. `TESTFLIGHT_500.md` prepara ese paso con las identidades existentes, sin recrearlas; el build 8 requiere comprobar disponibilidad. No fusionar ramas ni publicar en App Store. Funciones pendientes en `PARITY.md`.
