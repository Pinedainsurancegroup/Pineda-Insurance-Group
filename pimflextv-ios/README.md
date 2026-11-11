# PIMFLEX TV para iPhone y iPad — 5.0.0 candidata (8)

Aplicación nativa SwiftUI para iOS / iPadOS 16 o posterior. Conserva AVFoundation para HLS/MP4 y MobileVLCKit 3.7.5 para contenedores adicionales, el acceso y los recursos PIMFLEX existentes. Esta candidata continúa desde `f7f3cb43b5c287ee776f39f751e1a138f690ea80` en `pimflextv-ios-smarters5-20261110`, [PR borrador #12](https://github.com/Pinedainsurancegroup/Pineda-Insurance-Group/pull/12); la rama estable `pimflextv-ios-20261029` y la candidata 0.4.0 del PR #11 se conservan.

## Referencia Smarters 5.0 y controles

Las tres partes del adjunto reconstruyen un paquete Android compilado de 77.156.195 bytes, con 6.012 entradas y CRC válido. El manifiesto declara `com.nst.iptvsmarterstvbox`, versión 5.0, código 108. Contiene DEX y bibliotecas Android; no incluye fuentes de un proyecto Xcode ni librerías iOS reutilizables. `REFERENCE_500.md` documenta el análisis estático y su correspondencia con la app nativa. No se incorporan el APK, DEX, volcados, cuentas ni servicios del paquete al repositorio.

La numeración 5.0.0 identifica esta candidata PIMFLEX; no acredita paridad completa ni una implementación del backend WHMCS. Se mantiene el dashboard `_cl` y sus bitmaps originales, documentados en `REFERENCE_402.md`. El acceso, las rutas Xtream/M3U, los identificadores y los favoritos iOS permanecen intactos.

Los controles de reproducción se ocultan a los cuatro segundos de inactividad. Audio y subtítulos se obtienen de los grupos reales de AVPlayer; el selector vuelve a consultarlos al abrirse y conserva Automático, Desactivados y la selección manual. Los idiomas sólo aparecen cuando el medio los publica. La calidad HLS ofrece Automático y un límite preferido de bitrate según las variantes disponibles; no garantiza una resolución fija. El modo compatible mantiene sus opciones reales de VLC.

Código validado: `76cff20fdfac694a9bbe2b49c20760d0fc862f41`, [CI 42984142698](https://github.com/Pinedainsurancegroup/Pineda-Insurance-Group/actions/runs/42984142698), resultado final **success**: 37 core, 23 Python, 16 UI iPhone (4 exclusivas iPad omitidas), 20 mini y 20 Pro; Debug simulador y Release universal sin firma. iPhone aprobó tras un único reintento por una lectura de accesibilidad ausente en la prueba MKV existente, con código y aserciones idénticos. `V5_VALIDATION.md` conserva ambos resultados y la inspección de controles ocultos/subtítulos en los tres destinos. Este cierre sólo actualiza documentación; la CI anterior `42952718270` corresponde a 0.4.0. Las pruebas usan muestras locales propias y datos ficticios; falta comprobar cuenta, streaming, pistas y calidad con el proveedor en dispositivos físicos.

## Preparación para TestFlight

La automatización existente se actualiza a 5.0.0/build 8; véase [`TESTFLIGHT_500.md`](TESTFLIGHT_500.md). Genera primero un plan privado del commit limpio y sólo exporta/carga al solicitar ejecución en Mac con la identidad Apple Distribution, perfil y clave API existentes. El build 8 es provisional hasta confirmar su disponibilidad en App Store Connect. No se modifican certificados, credenciales, `SIGNING_REQUEST.json` ni el workflow protegido de firma.

El proyecto Xcode se genera en Mac CI y se publica como artefacto de fuentes separado. La compilación Release sin firma y la app de simulador no son una IPA instalable. No se ha cargado esta candidata a TestFlight ni publicado en App Store.

## Adaptación para iPad

El mismo producto Apple `com.pimflextv.ios` admite iPhone y iPad (familias 1 y 2). Se conserva el diseño, los recursos y el núcleo existentes. En ventanas de al menos 900 puntos aparece una lista lateral de categorías; en ventanas menores vuelve el selector compacto. Búsqueda, categoría y favoritos conservan su estado al rotar o cambiar el ancho. Las carátulas mantienen proporción 2:3 y la grilla distribuye las columnas según el espacio disponible. La vista de cuatro pantallas ajusta su ancho a la altura disponible en horizontal para mantener visibles los controles, conservando el video 16:9. Se conservan las cuatro orientaciones de iPad y la configuración que permite ventanas de distintos tamaños.

Las pruebas UI incluyen iPhone, iPad mini y iPad Pro de 13 pulgadas. La prueba de contenido limitado a 390 puntos usa un contenedor Debug y no certifica Split View o Stage Manager del sistema. Consultar `IPAD_VALIDATION.md` para el estado comprobado.

## Implementado en esta revisión

- Login con el logo, fondo azul/cian, panel, campos, botón y fuentes de la referencia original.
- Dashboard `_cl` identificado en el DEX: barra lateral, fondo azul marino y tres tarjetas originales de TV en directo, Cine y Series. Disposición horizontal fiel a esa estructura y adaptación vertical para iPhone.
- Catálogos por categoría, tarjetas de películas/series, búsqueda en los tres catálogos, favoritos, episodios y guía corta EPG.
- Lista de usuarios guardada en un único vault Keychain, con selección activa, eliminación individual y migración de la sesión anterior. Cerrar sesión conserva la lista; eliminar un usuario retira sus credenciales guardadas.
- Pantalla múltiple con dos o cuatro canales seleccionados, un único audio activo, errores/reintentos por pantalla y liberación de transmisiones al salir o ir al fondo.
- Reproductor AVPlayer para HLS/MP4 y modo compatible para MKV/AVI/FLV/WMV/WebM/TS/M2TS/MPEG/MPG. Permite pausa y búsqueda cuando el medio lo admite; los errores nativos ofrecen probar el modo compatible. No garantiza todos los códecs o servidores.
- Normalización de direcciones terminadas en `login.php`, `player_api.php` y `get.php`, preservando los datos de listas M3U y las rutas codificadas.
- Mayor tolerancia a las formas reales de respuestas Xtream y redirecciones de listas dentro del mismo origen.
- Icono iOS de 1024 px compuesto con el logo negro original de 800×312, sin rediseñar ni interpolar el logo.

La presencia de código no equivale a validación en un iPhone físico. Consultar el resultado de CI del commit actual y las diferencias en `PARITY.md`.

## Conexión del proveedor

HTTPS sigue siendo el valor predeterminado. La opción explícita del proveedor admite los hosts exactos `moonspelltools.cc` y `my-vionex.com`, sin subdominios. El usuario debe activar esa opción antes de enviar datos por HTTP. El texto del login informa que esa conexión transmite los datos sin cifrar.

Las excepciones ATS se limitan a esos dominios. No se habilita una excepción global de transporte ni se desactiva la validación de certificados TLS. El control estricto de redirecciones revisado pertenece a las peticiones API y a la descarga M3U por `APIClient`: rechaza cambios de origen y degradaciones de HTTPS a HTTP. Las cargas multimedia de AVPlayer/MobileVLCKit y las imágenes de `AsyncImage` necesitan comprobación propia; no quedan validadas por ese control. Un endpoint HTTPS del proveedor sigue siendo preferible. El puerto y la ruta los introduce el usuario; no hay cuentas, contraseñas ni canales precargados.

El propietario confirmó el inicio de sesión en el dispositivo y aportó una captura del rechazo local de formato. La prueba de decodificación usa un MKV propio, sin contenido ni credenciales del proveedor. La reproducción de la nueva versión con ese proveedor en un dispositivo físico requiere su comprobación.

## Compilar y comprobar

Se necesita macOS con Xcode, XcodeGen y Ruby/CocoaPods para construir la aplicación. En un Mac:

```sh
cd pimflextv-ios
swift test
brew install xcodegen
bash scripts/prepare-ios.sh
open PimflexTV.xcworkspace
```

El script usa CocoaPods 1.16.2 y el podspec oficial de MobileVLCKit 3.7.5 conservado en `Vendor`, con URL y SHA-256 exactos del archivo de VideoLAN y sin dependencias transitivas. La biblioteca permanece sin modificar. Ajustes incluye licencia y enlaces al código fuente; no se guardan sus binarios en Git. Las muestras MKV y MP4 se incluyen sólo en Debug y se excluyen de Release.

El workflow `.github/workflows/build-pimflextv-ios.yml` ejecuta las pruebas del núcleo, compila para simulador y para iPhone sin firma, ejecuta pruebas UI y exporta capturas mediante `xcresulttool`. Las pruebas UI usan datos explícitamente ficticios compilados sólo en Debug; no abren transmisiones de un proveedor.

Los artefactos de CI incluyen fuente/proyecto generado, aplicación de simulador y evidencia de pruebas. **No son un instalador firmado para iPhone.** No se genera un IPA ficticio. Consultar la ejecución asociada al SHA antes de afirmar que una compilación o prueba pasó.

## Continuidad en Codex

Entorno privado: **PIMFLEX TV iOS**. Repositorio: `Pinedainsurancegroup/Pineda-Insurance-Group`. Base estable: `pimflextv-ios-20261029`, PR borrador **#6**. Candidata actual: `pimflextv-ios-smarters5-20261110`. Antecedente 0.4.0: `pimflextv-ios-controls-20261110`, PR borrador **#11**.

El **2026-11-06**, el propietario respondió explícitamente «Si te autorizo» y autorizó publicar las imágenes y fuentes originales junto con el código iOS en el repositorio público `Pinedainsurancegroup/Pineda-Insurance-Group`, actualizar el PR #6 y ejecutar Mac CI. Con esta confirmación queda resuelto el bloqueo previo de publicación por falta de autorización para esos recursos. El PR permanece en borrador; la autorización no incluye merge ni publicación en App Store. No incorporar APK/AAB, DEX, secretos, claves de firma, sesiones, credenciales ni respuestas de proveedores al repositorio.

La validación `1487328dd5f69c9f04ce5148e854532d10e8598d` pasó [CI 42747510260](https://github.com/Pinedainsurancegroup/Pineda-Insurance-Group/actions/runs/42747510260): 37 pruebas núcleo, 10 Python de firma, Debug/Release universales, 8 UI en iPhone (4 exclusivas iPad omitidas), 12 mini y 12 Pro. Incluye decodificación MKV local, pausa, búsqueda y reapertura; no usa streams del proveedor. La IPA firmada conserva el código `326c714262ca9aa4c896fd11fd202e3ac37bacd3`: sólo cambian la muestra DEBUG y su prueba UI entre ambos SHA, con insumos Release idénticos. Ver `IPAD_VALIDATION.md` para evidencia y límites.

Leer `V5_VALIDATION.md`, `REFERENCE_500.md` y `PARITY.md` para el estado actual; `CODEX_HANDOFF.md` y `REFERENCE_402.md` conservan el historial y la referencia visual. El entorno de onboarding tuvo un fallo de conectividad al recuperar la rama; una copia verificada del código puede usarse como punto de partida sin resetear trabajo posterior. La configuración o el nombre del entorno no demuestran por sí solos que el código esté recuperado o probado allí.

## Distribución

La versión **0.3.3 (6)** universal está firmada, procesada como COMPLETE/VALID y habilitada IN_BETA_TESTING en el grupo interno del titular. Se actualiza desde TestFlight sobre la app existente. Falta comprobar el mismo video del proveedor en el dispositivo y completar metadatos, soporte, privacidad y declaraciones del producto final para distribución pública. No hay envío a revisión ni publicación en App Store.

Referencias oficiales:
- https://developer.apple.com/documentation/xcode/preparing-your-app-for-distribution
- https://developer.apple.com/documentation/xcode/distributing-your-app-for-beta-testing-and-releases
- https://developer.apple.com/documentation/Xcode-Release-Notes/xcode-16_3-release-notes
