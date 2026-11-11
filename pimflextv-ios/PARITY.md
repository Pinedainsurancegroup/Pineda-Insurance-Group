# Paridad de PIMFLEX TV — referencias Android 4.0.2 y Smarters 5.0

## Candidata 5.0.0 (8)

Continúa desde 0.4.0 sin sustituir el login, las rutas, el almacenamiento por cuenta ni los recursos PIMFLEX. La nueva referencia Android 5.0/código 108 se analiza estáticamente en `REFERENCE_500.md`; el paquete compilado no aporta un proyecto iOS ni los servicios WHMCS. El selector nativo se actualiza al abrirse, conserva sus elecciones y concilia las opciones con AVPlayer. Se añade una prueba de ocultación completa a cuatro segundos con MP4 local real. `V5_VALIDATION.md` identifica los resultados del nuevo SHA; la CI de 0.4.0 que sigue abajo es histórica.

No se ha firmado ni enviado 5.0.0 (8) a TestFlight. Continúan pendientes proveedor/dispositivo real, calidad HLS efectiva, AirPlay, Catchup, XMLTV completo, grabación/descargas, control parental y el resto de la tabla. No hay migración automática de favoritos Android ni implementación nueva de WHMCS, Stalker o servicios de la APK.

## Antecedente 0.4.0

Conserva los recursos y la reproducción de 0.3.3/build 6. El usuario confirma inicio de sesión y reproducción actuales; falta validar los cambios de la candidata en dispositivos reales. El ZIP descompilado Android 4.0.2 ya se reconstruyó de cinco partes y se revisó estáticamente. El reproductor es una adaptación iOS; no afirmar paridad total.

`4da1a91abef19ffdd159deaf6adc8ce000a52440` tiene [CI 42952718270](https://github.com/Pinedainsurancegroup/Pineda-Insurance-Group/actions/runs/42952718270): resultado final **success**, con 37 core, 23 Python, 15 UI iPhone (4 exclusivas iPad omitidas), 19 mini y 19 Pro, Debug y Release universal sin firma. Pro aprobó tras un único reintento por una lectura de accesibilidad transitoria en el test MKV existente. Véase `PLAYER_VALIDATION.md` para distinguir selección real de pistas locales, opciones sintéticas y revisión de capturas.

## Referencia verificable

- APK SHA-256: `c1fa614b2e2aec9399bbde9ca91491b8a4f03e010bd47a4074e57d7b0f6f6a36`
- AAB SHA-256: `852be7a751dfb44264deccb2f85aa0b2a2375f7d1146ca1a71d5d4d410ef6fe9`
- ZIP descompilado reconstruido: `296966c0892d04487d2b42c43f76084e19178e0800d13199e895992b485aa4d8`; manifiesto 4.0.2/código 102, CRC correcto en 42.465 entradas.

`REFERENCE_402.md` explica la selección real de layouts y recursos. `Resources/ReferenceAssets.json` registra los hashes de los assets copiados y la composición del icono. El análisis original documenta la inspección de recursos y DEX; esta revisión usa esa evidencia y no ejecutó las apps Android. No se afirma equivalencia pixel por pixel ni completa equivalencia funcional.

| Función | Implementación iOS actual | Comprobación pendiente |
| --- | --- | --- |
| Apariencia de acceso e inicio | Recursos originales del login y dashboard `_cl`, fuentes y etiquetas ES; sidebar y tres tarjetas en horizontal | Comparación en dispositivo, estados del proveedor y tamaños físicos; pequeño recorte heredado del logo en mini vertical |
| iPhone e iPad | Producto universal; catálogo con categorías laterales desde 900 pt, selector compacto y carátulas 2:3 | Validación física y ventanas del sistema |
| Vertical | Adaptación adicional de iPhone/iPad | No tiene equivalente exacto: Android declara `sensorLandscape` |
| Login Xtream | Autenticación y catálogos comprobados por API; login físico confirmado por el propietario después de la corrección M3U | Revalidar al cambiar proveedor o cuenta |
| HTTP histórico | Opt-in explícito; hosts exactos `moonspelltools.cc` y `my-vionex.com` en 0.3.3/build 6; ATS por dominio; regresión UI en iPhone/mini/Pro | Cuenta y streams reales; endpoint HTTPS preferido cuando el proveedor lo ofrezca |
| Usuarios guardados | Vault Keychain único, activar, salir, eliminar y migrar sesión anterior | Migración persistente y errores Keychain en dispositivo |
| M3U | Importa cuenta de get.php de proveedores conocidos; acceso físico confirmado; listas genéricas con categorías/enlaces relativos y límite 32 MiB, error de tamaño específico | Variantes genéricas y archivo local pendiente |
| TV, Cine y Series | Catálogo, categorías, grilla, búsqueda y episodios | Datos y streams reales |
| Búsqueda maestra | TV/Cine/Series en una vista | Volumen y velocidad con catálogo real |
| Favoritos y reanudar | Separados por cuenta; conserva identidades iOS. Android 4.0.2 usa almacenamiento local distinto | Ciclos de vida reales; importación/sincronización Android no implementada |
| EPG | Guía corta Xtream | XMLTV completo y datos reales |
| Pantalla múltiple | Dos/cuatro canales, un audio, selección y limpieza | Codecs, carga de dispositivo y límite de conexiones del proveedor |
| Audio/subtítulos/AirPlay | Pistas publicadas por AVPlayer/VLC, carga/error/reintento por apartado y variantes nativas «Solo forzados» identificadas; AirPlay nativo | Cambio audible en dispositivo, medios del proveedor, subtítulos forzados efectivos y AirPlay físico; no equivale a Chromecast |
| Ocultación de controles | Cuatro segundos de inactividad; ocultación, recuperación, reinicio y opciones aprobados en CI iPhone/mini/Pro | Dispositivos reales, VoiceOver y AirPlay físicos |
| Calidad | Candidata: Automático y límites preferidos derivados de variantes HLS de AVPlayer; sin calidades inventadas en VLC | Verificar adaptación efectiva con un master multivariante real |
| Formato live / navegación del reproductor | iOS conserva HLS Xtream y selección desde el catálogo | Selector TS/HLS y canal anterior/siguiente dentro del reproductor; comportamiento exacto y proveedor real |
| Catch up | Entrada visible marcada no disponible | Archivo, ventana de retención, zona horaria y ruta del proveedor |
| Grabación/descargas | Pendiente | Implementación y límites iOS |
| Control parental | Pendiente | PIN, bloqueo efectivo y pruebas |
| VPN | Pendiente | Servicio y configuración/entitlements del propietario |
| PiP | Desactivado en candidata | Ciclo de vida y pruebas físicas |
| MKV/AVI y otros contenedores | MobileVLCKit 3.7.5; MKV H.264/AAC decodificado en CI iPhone/mini/Pro con pausa, búsqueda, progreso real y reapertura | Formatos/códecs y medios reales del proveedor en dispositivo |
| Stalker, WHMCS, notificaciones, código TV | Pendiente | Servicios y configuración propios |
| Respaldo Android `.pimbackup` | No importado | Compatibilidad de formato y cifrado |
| Distribución | 0.3.3/build 6 firmada y en TestFlight; acceso/reproducción actuales confirmados por el propietario. Antecedente 0.4.0/build 7 con CI sin firma; candidata actual 5.0.0/build 8 según `V5_VALIDATION.md` | Exportar/cargar el SHA candidato mediante proceso protegido sin sustituir la rama estable; prueba física de estos cambios; ficha/privacidad pública |

La pantalla de acceso muestra la URL del servidor porque todavía no se ha establecido una configuración de proveedor verificable para ocultarla. Algunos controles de la referencia se adaptan a navegación y controles nativos de iOS. Los datos de muestra usados para pruebas están aislados detrás de `#if DEBUG` y no demuestran funcionamiento de un servicio real.

## Criterio de finalización

No etiquetar esta candidata como clon completo ni proveedor plenamente validado hasta cerrar la comparación visual, probar cuenta y streams en la IPA, resolver las funciones pendientes y confirmar instalación/reproducción de la beta en dispositivos físicos. CI sólo certifica lo que sus pasos y artefactos muestran para el SHA exacto.
