# Referencia estática Smarters Android 5.0

Se reconstruyeron en orden `.001`, `.002`, `.003` las tres partes aportadas por el propietario. Archivo: `iptv-smarters-5.0.zip`; tamaño 77.156.195 bytes; SHA-256 `b0db9468428b537719f45fcfb1e0981b41e36ea9bc3772e06daff76c335f90a9`. Las 6.012 entradas pasan CRC; se comprobaron las rutas antes de extraer.

El manifiesto binario decodificado identifica `com.nst.iptvsmarterstvbox`, `versionName=5.0`, `versionCode=108`, SDK objetivo 35. El contenido tiene estructura de APK: cuatro DEX, recursos Android y bibliotecas `.so`. No incluye fuentes de proyecto Xcode, Gradle original ni una biblioteca nativa iOS. JADX 1.5.6 se obtuvo de su distribución oficial y se verificó su SHA-256 `545ea2be9c242511bc145755cf4bda2485ade42966e096f8b4d3da2a230e8974` antes del análisis. La descompilación es una representación parcial; no equivale a recuperar el proyecto original completo.

## Reproductor

`com.nst.iptvsmarterstvbox.view.activity.ExoPlayerMoviesSeries` llama a `u2/v2` con 5.000 ms y los Runnable asociados llegan a `R2/S2`, que ocultan controles. `PlayerView` usa 5.000 ms por defecto. `NSTIJKPlayerVOD` inicializa su plazo en 7.000 ms y `g2(int)` programa la ocultación. Los **4.000 ms** de PIMFLEX iOS responden al requisito explícito del propietario; no son un valor uniforme encontrado en Android 5.0.

`NSTIJKPlayerVOD.k2` consulta `getTrackInfo()`, distingue video/audio/texto, muestra el idioma publicado y selecciona el índice real de la pista. Guarda `currentAudioTrack`, `currentSubtitleTrack` y `currentVideoTrack`. La presencia de estos selectores no asegura que todo medio ofrezca español, inglés, subtítulos o varias calidades.

La adaptación iOS mantiene AVPlayer y sus grupos `.audible`/`.legible`, con selección mediante AVMediaSelection; no importa índices Android ni sustituye el motor nativo por bibliotecas Android. Al abrir opciones se consultan de nuevo los grupos del item actual. Se conservan Automático/Desactivados y se concilia la selección manual con el motor. Las variantes HLS publicadas permiten ofrecer límites preferidos de bitrate; esto no fija una resolución concreta. MobileVLCKit sigue siendo la alternativa compatible existente.

## Continuidad entre plataformas

El código iOS vive en `pimflextv-ios-smarters5-20261110`, derivado de la candidata 0.4.0 `f7f3cb43b5c287ee776f39f751e1a138f690ea80`. La referencia Android existente está en `pimflextv-reference-402-20261007`, commit `2e898d2a6c1aaeb757b5797c4f9826f8939d5afa`. Este último es un proyecto de reconstrucción anterior, no las fuentes originales de la APK 5.0 recibida. El nuevo paquete y su análisis detallado permanecen en el entorno privado; no se publica el volcado compilado ni se reemplaza Android estable.

La interfaz Retrofit `validateLogin` usa `GET player_api.php` con `username`/`password`; los catálogos utilizan `action`, `category_id` y `series_id` según la operación. Los reproductores revisados construyen rutas `/live/`, `/movie/` y `/series/` con identificador/formato. `DatabaseHandler` asocia favoritos a stream, categoría, tipo y usuario; OneStream tiene almacenamiento separado. Estos contratos no justifican alterar las rutas ni convertir índices locales entre plataformas.

Se conserva el formato de acceso y las rutas Xtream/M3U existentes de iOS, sus identificadores de catálogo y favoritos aislados por cuenta. No se copian valores de configuración ni datos embebidos del paquete, ni se importan favoritos o preferencias por índices Android. La marca, fuentes y dashboard `_cl` siguen siendo los recursos PIMFLEX 4.0.2 autorizados. No se implementa un backend WHMCS por la mera presencia de sus clases en Android.

## Límites

Análisis estático, sin ejecutar Android ni conectar con sus servicios. El ZIP no proporciona todos los servicios, cuentas, derechos de contenido o un proyecto Android reconstruible/verificado. Esta entrega adapta el reproductor iOS; no demuestra dos aplicaciones 5.0 equivalentes ni certifica paridad completa. `PARITY.md` y `V5_VALIDATION.md` separan implementación, evidencia Mac y pendientes físicos/proveedor. No se incluyen APK, DEX, fuentes descompiladas, claves o respuestas de servicios en Git.
