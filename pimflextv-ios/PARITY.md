# Alcance y diferencias con Android 4.0.2

Inspección directa del APK/AAB del proyecto el 29-10-2026: archivos ZIP sin errores CRC; los tres DEX coinciden entre ambos. Las huellas coinciden con la revisión anterior:

- APK SHA-256: `c1fa614b2e2aec9399bbde9ca91491b8a4f03e010bd47a4074e57d7b0f6f6a36`
- AAB SHA-256: `852be7a751dfb44264deccb2f85aa0b2a2375f7d1146ca1a71d5d4d410ef6fe9`

Se observaron nombres de actividades de TV, VOD, series, M3U, EPG, grabación, VPN, WHMCS, Cast y acceso por código; marcadores `player_api.php`, `get_live_streams`, `get_vod_streams`, `get_series_info` y `get_short_epg`. Su presencia no demuestra disponibilidad en un servidor concreto. No se ejecutó la referencia aquí ni se copiaran sus bibliotecas Android, servicios comerciales o claves.

| Función | Candidata iOS | Validación que falta |
|---|---|---|
| Login Xtream | Implementado, HTTPS y cuenta activa | Cuenta real y comportamiento del proveedor |
| M3U | URL, categorías y deduplicación | Listas reales; importación local pendiente |
| TV / películas | Catálogo, búsqueda y reproducción AVKit | Codec, HLS y carga real |
| Series | Temporadas y episodios | Respuesta real del proveedor |
| EPG | Guía corta Xtream | XMLTV completo pendiente |
| Favoritos / reanudar | Locales, separados por cuenta | Ciclo de vida en dispositivo |
| Audio / subtítulos | Controles de AVKit si el medio ofrece pistas | Subtítulos externos / OpenSubtitles pendientes |
| Salida AirPlay | AVPlayer permite salida externa | Dispositivo/stream real; no equivale a Chromecast |
| PiP | Desactivado en esta candidata | Ciclo de vida y pruebas de dispositivo |
| HTTP sin cifrar | No habilitado | Confirmar HTTPS del proveedor o diseñar excepción de alcance limitado |
| MKV / AVI / IJK / VLC | No se trasladan binarios Android | Motor iOS adicional o transcodificación; revisar licencias |
| Radio | URL de audio compatible en M3U | Sección dedicada pendiente |
| Catch up / XMLTV / Stalker | Pendiente | Implementación y portal autorizado |
| Grabación / descargas / multipantalla | Pendiente | Implementación nativa y límites de iOS |
| Control parental | Pendiente | PIN, bloqueo efectivo y pruebas antes de uso familiar |
| Múltiples cuentas / respaldo importable | Una sesión; preferencias separadas | Selector e importación de respaldo Android pendientes |
| VPN / WHMCS / anuncios / push / código TV | Pendiente | Servicios y configuración del propietario |
| Fidelidad visual | Logo propio, inicio equivalente adaptado a móvil | Comparación en dispositivo; no se afirma clon píxel por píxel |
| Distribución | Proyecto Xcode y CI | Firma, icono de tienda, metadatos, privacidad, TestFlight y revisión |

La API no autentica contra servidores embebidos en el APK; el propietario introduce su servicio autorizado. La contraseña nunca se incorpora al código ni al repositorio. Una lista M3U sin metadatos de temporadas no puede convertirse fiablemente en catálogo de series: esos archivos se presentan como películas o transmisiones.
