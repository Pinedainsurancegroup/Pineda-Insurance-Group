# Equivalencia con PIMFLEX TV Android 4.0.2

## Referencia verificable

- APK SHA-256: `c1fa614b2e2aec9399bbde9ca91491b8a4f03e010bd47a4074e57d7b0f6f6a36`
- AAB SHA-256: `852be7a751dfb44264deccb2f85aa0b2a2375f7d1146ca1a71d5d4d410ef6fe9`

`REFERENCE_402.md` explica la selección real de layouts y recursos. `Resources/ReferenceAssets.json` registra los hashes de los assets copiados y la composición del icono. Se inspeccionaron recursos y DEX; no se ejecutó la referencia Android en esta sesión. No se afirma equivalencia pixel por pixel ni completa equivalencia funcional.

| Función | Implementación iOS actual | Comprobación pendiente |
| --- | --- | --- |
| Apariencia de acceso e inicio | Recursos originales del login y dashboard `_cl`, fuentes y etiquetas ES; sidebar y tres tarjetas en horizontal | Comparación en dispositivo, estados del proveedor y tamaños físicos |
| iPhone e iPad | Producto universal; catálogo con categorías laterales desde 900 pt, selector compacto y carátulas 2:3 | Validación física y ventanas del sistema |
| Vertical | Adaptación adicional de iPhone/iPad | No tiene equivalente exacto: Android declara `sensorLandscape` |
| Login Xtream | Cuenta activa, normalización de portal y credenciales Keychain | Autenticación real del proveedor |
| HTTP histórico | Opt-in explícito; dominio exacto `moonspelltools.cc`; ATS limitado | Validación en iPhone y endpoint HTTPS preferido |
| Usuarios guardados | Vault Keychain único, activar, salir, eliminar y migrar sesión anterior | Migración persistente y errores Keychain en dispositivo |
| M3U | URL, categorías, enlaces relativos, redirección del mismo origen | Listas reales; archivo local pendiente |
| TV, Cine y Series | Catálogo, categorías, grilla, búsqueda y episodios | Datos y streams reales |
| Búsqueda maestra | TV/Cine/Series en una vista | Volumen y velocidad con catálogo real |
| Favoritos y reanudar | Separados por cuenta | Ciclos de vida reales |
| EPG | Guía corta Xtream | XMLTV completo y datos reales |
| Pantalla múltiple | Dos/cuatro canales, un audio, selección y limpieza | Codecs, carga de dispositivo y límite de conexiones del proveedor |
| Audio/subtítulos/AirPlay | Controles de AVPlayer cuando el medio los ofrece | Dispositivo y pistas reales; no equivale a Chromecast |
| Catch up | Entrada visible marcada no disponible | Archivo, ventana de retención, zona horaria y ruta del proveedor |
| Grabación/descargas | Pendiente | Implementación y límites iOS |
| Control parental | Pendiente | PIN, bloqueo efectivo y pruebas |
| VPN | Pendiente | Servicio y configuración/entitlements del propietario |
| PiP | Desactivado en candidata | Ciclo de vida y pruebas físicas |
| MKV/AVI y motores Android | No incorporados | Motor iOS o transcodificación y compatibilidad |
| Stalker, WHMCS, notificaciones, código TV | Pendiente | Servicios y configuración propios |
| Respaldo Android `.pimbackup` | No importado | Compatibilidad de formato y cifrado |
| Distribución | IPA universal firmada; Apple COMPLETE/VALID; declaración autorizada guardada; TestFlight En pruebas y titular Invitado | Instalación y reproducción físicas; ficha/privacidad para distribución pública |

La pantalla de acceso muestra la URL del servidor porque todavía no se ha establecido una configuración de proveedor verificable para ocultarla. Algunos controles de la referencia se adaptan a navegación y controles nativos de iOS. Los datos de muestra usados para pruebas están aislados detrás de `#if DEBUG` y no demuestran funcionamiento de un servicio real.

## Criterio de finalización

No etiquetar esta candidata como clon completo o app instalable hasta cerrar la comparación visual, probar la cuenta y los streams reales, resolver las funciones solicitadas pendientes y confirmar la instalación/reproducción real de la beta TestFlight ya habilitada. CI sólo certifica lo que sus pasos y artefactos muestran para el SHA exacto.
