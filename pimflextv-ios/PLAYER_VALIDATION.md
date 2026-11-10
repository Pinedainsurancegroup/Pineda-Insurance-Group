# Candidata 0.4.0 / build 7 — controles de reproducción

Base: `56e66e8ac785b45d84f2ba3df955858d91a5c64f`, 0.3.3/build 6. El propietario confirma que la app actual inicia sesión y reproduce contenido. Esta candidata conserva APIClient, importación M3U, Keychain, selección de motor, MobileVLCKit 3.7.5, URL de reproducción, recursos visuales y firma/configuración Apple existentes. La versión entregada en TestFlight sigue siendo 0.3.3/build 6 hasta completar la validación y distribución de la candidata.

## Comparación y alcance

| Área | Referencia disponible | Cambio de la candidata / límite |
| --- | --- | --- |
| Inicio | Layout `_cl` y bitmaps 4.0.2 documentados; captura iOS aportada | Conservados. No se sustituye el tema ni se dibujan iconos sobre los ya incluidos en tarjetas. |
| Menú compacto | Cuenta, ajustes y usuarios en la barra lateral de 4.0.2 | Más opciones da acceso a cuenta, usuarios, favoritos, actualización y cierre de sesión cuando no cabe la barra lateral. |
| Reproductor | La referencia archivada no especifica medidas de todos los controles Android | Interfaz iOS nueva: cerrar, pausa/reanudar, reloj, búsqueda VOD, opciones; conserva selección de motor y reanudación. No afirmar igualdad visual exacta. |
| Inactividad | Requisito explícito del propietario: cuatro segundos | El temporizador se reinicia al interactuar; pausa al usar opciones, slider, AirPlay o VoiceOver, durante carga/error y fuera de la escena activa. Un toque vuelve a mostrar controles. También se ocultan si el usuario pausa y deja de interactuar. |
| Audio/subtítulos | Disponibilidad dependiente del medio/proveedor | AVMediaSelectionGroup en AVPlayer; índices y nombres ofrecidos por VLC. Automático nativo y desactivación cuando la selección lo admite. No se inventan pistas en producción. |
| Calidad | Depende de variantes de la transmisión | AVURLAsset variants: Automático o límite preferido de bitrate publicado. Puede adaptarse por debajo del límite; no fuerza una variante. VLC no expone selector de calidad aquí. |
| Android 4.0.1 | ZIP adjunto supera 32 MiB | Transferencia bloqueada por límite del entorno. No se ha abierto ni se asume idéntico a 4.0.2. Comparación directa pendiente. |

## Pruebas

El 2026-11-10 el propietario autorizó expresamente publicar el MP4 de prueba derivado de la muestra MKV existente. Ambos contienen el mismo video H.264 de muestra (hash de video decodificado idéntico); no contienen cuentas ni contenido del proveedor. El MP4 conserva audio AAC y se usa exclusivamente en pruebas DEBUG.

- Se conservan los 37 tests de núcleo y las pruebas existentes de login, M3U, iPad, multivista y decodificación MKV.
- Se añade cobertura UI de ocultación, recuperación y reinicio del plazo, opciones y selecciones ficticias, menú compacto y reproducción nativa de muestra.
- Ambas superficies de video exponen estado y tiempo transcurrido a VoiceOver, con el reloj real del modelo. Las pruebas MKV/MP4 observan ese valor permanente para comprobar pausa, búsqueda, avance y reapertura, independientemente de que el overlay se oculte. El análisis del reloj falla ante un valor ausente o mal formado; nunca lo sustituye por cero. Las pruebas independientes de inactividad conservan sus aserciones y el plazo de la app sigue siendo de cuatro segundos.
- Las dos pruebas de decodificación local usan `--keep-playback-controls-visible`: XCTest llegó a tardar más de cuatro segundos entre localizar un botón e inyectar el toque. Esa opción sólo existe en DEBUG y exige simultáneamente `usesTestFixtures` y un argumento de archivo local MKV/MP4; sólo omite programar la ocultación. Conserva el motor, reloj, pistas, pausa, búsqueda y avance reales. Las pruebas específicas de ocultación/reinicio del plazo y opciones no usan esa opción. Por tanto, los tests de decodificación no certifican por sí solos la ocultación automática; ésta se comprueba por separado. Release y DEBUG normal conservan los cuatro segundos.
- Las opciones sintéticas están detrás de DEBUG y `--ui-testing`; no validan cambios audibles de idioma, subtítulos visibles ni adaptación real HLS. La muestra local MKV y su remux MP4 H.264/AAC prueban decodificación y controles sin proveedor. Ambas muestras se excluyen de Release.
- En VLC, las pistas se actualizan al abrir opciones, al terminar la carga con opciones abiertas y tras seleccionar; no se consultan en cada actualización del reloj. La prueba MKV comprueba también que se ofrece y puede seleccionar su pista AAC real, sin inventar subtítulos ni calidad. Una única pista no demuestra cambio audible entre idiomas.
- En el entorno local Linux no existen Swift/Xcode/XcodeGen. Las verificaciones locales de estructura y los tests Python no constituyen una compilación iOS. Registrar el resultado Mac por SHA de esta candidata; los resultados históricos de 0.3.3 no la validan.
- Revisar manualmente las capturas iPhone portrait/landscape, iPad mini/Pro, ventanas estrechas y texto accesible. Probar pistas múltiples reales, subtítulos forzados, errores/redirecciones multimedia, AirPlay, calidad HLS, fondo/retorno y reanudación con el proveedor autorizado en dispositivo.

## Preparación para TestFlight

Versión 0.4.0/build 7, mismo identificador y familias iPhone/iPad. Proyecto generado mediante `bash scripts/prepare-ios.sh`; abrir `PimflexTV.xcworkspace` por la dependencia VLC. CI prepara Debug y Release sin firma y prueba los tres simuladores en una rama separada. La configuración permite validar PR hacia la rama iOS, además de la base original; no activa firma.

El workflow de firma existente y su entorno protegido sólo admiten `pimflextv-ios-20261029`, y firman el SHA del evento de esa rama. La candidata permanece en `pimflextv-ios-controls-20261110`; cambiar únicamente el número de `SIGNING_REQUEST.json` allí no activa la firma. Para exportarla sin reemplazar la rama estable hace falta preparar y aprobar un proceso protegido para el SHA exacto de la candidata, reutilizando la identidad/perfil actuales. Ese cambio queda fuera de esta entrega; no se ha ampliado la política del entorno ni modificado el workflow de firma.

No se ha cambiado `SIGNING_REQUEST.json`, emitido certificados, alterado credenciales, firmado ni subido esta candidata a Apple. El número 7 es provisional hasta comprobar que sigue libre al preparar esa exportación. No fusionar PR ni publicar en App Store. No es todavía una IPA de 0.4.0 instalable.

Texto preparado para «Qué probar» de TestFlight, para usar después de exportar y validar el build exacto:

> PIMFLEX TV 0.4.0: controles de reproducción que se ocultan tras cuatro segundos y reaparecen al tocar el video. Probar pausa, reanudación y saltos de diez segundos en Cine/Series; seleccionar audio, subtítulos y preferencia de calidad cuando el medio los ofrezca. Comprobar el menú Más opciones en pantallas estrechas. Validar acceso y reproducción con la cuenta habitual en iPhone/iPad, sin compartir credenciales. Informar el modelo, versión de iOS, tipo de medio y pasos del fallo; no incluir URLs con usuario/contraseña. Catchup, descargas/grabación y control parental siguen pendientes.

Catchup, XMLTV completo, descarga/grabación, controles parentales y el resto de `PARITY.md` siguen pendientes. No se certifica paridad del 100 % ni funcionamiento de la candidata en dispositivos reales.
