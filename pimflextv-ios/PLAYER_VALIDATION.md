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

- Se conservan los 37 tests de núcleo y las pruebas existentes de login, M3U, iPad, multivista y decodificación MKV.
- Se añade cobertura UI de ocultación, recuperación y reinicio del plazo, opciones y selecciones ficticias, menú compacto y reproducción nativa de muestra.
- Las opciones sintéticas están detrás de DEBUG y `--ui-testing`; no validan cambios audibles de idioma, subtítulos visibles ni adaptación real HLS. La muestra local MKV y su remux MP4 H.264/AAC prueban decodificación y controles sin proveedor. Ambas muestras se excluyen de Release.
- En el entorno local Linux no existen Swift/Xcode/XcodeGen. Las verificaciones locales de estructura y los tests Python no constituyen una compilación iOS. Registrar el resultado Mac por SHA de esta candidata; los resultados históricos de 0.3.3 no la validan.
- Revisar manualmente las capturas iPhone portrait/landscape, iPad mini/Pro, ventanas estrechas y texto accesible. Probar pistas múltiples reales, subtítulos forzados, errores/redirecciones multimedia, AirPlay, calidad HLS, fondo/retorno y reanudación con el proveedor autorizado en dispositivo.

## Preparación para TestFlight

Versión 0.4.0/build 7, mismo identificador y familias iPhone/iPad. Proyecto generado mediante `bash scripts/prepare-ios.sh`; abrir `PimflexTV.xcworkspace` por la dependencia VLC. CI prepara Debug y Release sin firma y prueba los tres simuladores en una rama separada. La configuración permite validar PR hacia la rama iOS, además de la base original; no activa firma.

Tras aprobar la candidata, el proceso de firma existente debe recibir una solicitud que apunte al SHA exacto validado y use la identidad/perfil actuales. No se ha cambiado `SIGNING_REQUEST.json`, emitido certificados, alterado credenciales, firmado ni subido esta candidata a Apple. El número 7 es provisional hasta comprobar que sigue libre al preparar esa exportación. No fusionar PR ni publicar en App Store. No es todavía una IPA de 0.4.0 instalable.

Catchup, XMLTV completo, descarga/grabación, controles parentales y el resto de `PARITY.md` siguen pendientes. No se certifica paridad del 100 % ni funcionamiento de la candidata en dispositivos reales.
