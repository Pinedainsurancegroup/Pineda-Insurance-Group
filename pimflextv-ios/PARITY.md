# Equivalencia con PIMFLEX TV Android 4.0.2

## Candidata 0.4.0

Conserva los recursos y la reproducción de 0.3.3/build 6. El usuario confirma inicio de sesión y reproducción actuales; falta validar estos cambios en dispositivos reales. Android 4.0.1 no pudo inspeccionarse: su ZIP supera el límite de transferencia de 32 MiB. El reproductor nuevo es una adaptación iOS; la documentación 4.0.2 no contiene medidas o capturas verificadas de todos sus controles. No afirmar paridad total.

`4a22b4668896191d893657291ff46930659e9534` aprobó [CI 42918344913](https://github.com/Pinedainsurancegroup/Pineda-Insurance-Group/actions/runs/42918344913): 37 core, 10 Python, 14 UI iPhone (4 exclusivas iPad omitidas), 18 mini, 18 Pro, Debug y Release universal sin firma. Véase `PLAYER_VALIDATION.md` para distinguir decodificación local, selecciones sintéticas y revisión de capturas.

## Referencia verificable

- APK SHA-256: `c1fa614b2e2aec9399bbde9ca91491b8a4f03e010bd47a4074e57d7b0f6f6a36`
- AAB SHA-256: `852be7a751dfb44264deccb2f85aa0b2a2375f7d1146ca1a71d5d4d410ef6fe9`

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
| Favoritos y reanudar | Separados por cuenta | Ciclos de vida reales |
| EPG | Guía corta Xtream | XMLTV completo y datos reales |
| Pantalla múltiple | Dos/cuatro canales, un audio, selección y limpieza | Codecs, carga de dispositivo y límite de conexiones del proveedor |
| Audio/subtítulos/AirPlay | Candidata 0.4.0: controles propios, pistas publicadas por AVPlayer/VLC y AirPlay nativo | Cambio audible/visible con pistas reales, AirPlay y ambos motores en dispositivo; no equivale a Chromecast |
| Ocultación de controles | Cuatro segundos de inactividad; ocultación, recuperación, reinicio y opciones aprobados en CI iPhone/mini/Pro | Dispositivos reales, VoiceOver y AirPlay físicos |
| Calidad | Candidata: Automático y límites preferidos derivados de variantes HLS de AVPlayer; sin calidades inventadas en VLC | Verificar adaptación efectiva con un master multivariante real |
| Catch up | Entrada visible marcada no disponible | Archivo, ventana de retención, zona horaria y ruta del proveedor |
| Grabación/descargas | Pendiente | Implementación y límites iOS |
| Control parental | Pendiente | PIN, bloqueo efectivo y pruebas |
| VPN | Pendiente | Servicio y configuración/entitlements del propietario |
| PiP | Desactivado en candidata | Ciclo de vida y pruebas físicas |
| MKV/AVI y otros contenedores | MobileVLCKit 3.7.5; MKV H.264/AAC decodificado en CI iPhone/mini/Pro con pausa, búsqueda, progreso real y reapertura | Formatos/códecs y medios reales del proveedor en dispositivo |
| Stalker, WHMCS, notificaciones, código TV | Pendiente | Servicios y configuración propios |
| Respaldo Android `.pimbackup` | No importado | Compatibilidad de formato y cifrado |
| Distribución | 0.3.3/build 6 firmada y en TestFlight; acceso/reproducción actuales confirmados por el propietario. Candidata 0.4.0/build 7 con CI sin firma | Exportar/cargar el SHA candidato mediante proceso protegido sin sustituir la rama estable; prueba física de estos cambios; ficha/privacidad pública |

La pantalla de acceso muestra la URL del servidor porque todavía no se ha establecido una configuración de proveedor verificable para ocultarla. Algunos controles de la referencia se adaptan a navegación y controles nativos de iOS. Los datos de muestra usados para pruebas están aislados detrás de `#if DEBUG` y no demuestran funcionamiento de un servicio real.

## Criterio de finalización

No etiquetar esta candidata como clon completo ni proveedor plenamente validado hasta cerrar la comparación visual, probar cuenta y streams en la IPA, resolver las funciones pendientes y confirmar instalación/reproducción de la beta en dispositivos físicos. CI sólo certifica lo que sus pasos y artefactos muestran para el SHA exacto.
