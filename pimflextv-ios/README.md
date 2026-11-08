# PIMFLEX TV para iPhone y iPad — 0.3.0

Aplicación nativa SwiftUI / AVFoundation para iOS / iPadOS 16 o posterior. Continúa la candidata de iPhone del PR #6 y usa la versión Android 4.0.2 aportada por el propietario como referencia. El desarrollo permanece en `pimflextv-ios-20261029`, sin integrar a producción.

## Adaptación para iPad

El mismo producto Apple `com.pimflextv.ios` admite iPhone y iPad (familias 1 y 2). Se conserva el diseño, los recursos y el núcleo existentes. En ventanas de al menos 900 puntos aparece una lista lateral de categorías; en ventanas menores vuelve el selector compacto. Búsqueda, categoría y favoritos conservan su estado al rotar o cambiar el ancho. Las carátulas mantienen proporción 2:3 y la grilla distribuye las columnas según el espacio disponible. La vista de cuatro pantallas ajusta su ancho a la altura disponible en horizontal para mantener visibles los controles, conservando el video 16:9. Se conservan las cuatro orientaciones de iPad y la configuración que permite ventanas de distintos tamaños.

Las pruebas UI incluyen iPhone, iPad mini y iPad Pro de 13 pulgadas. La prueba de contenido limitado a 390 puntos usa un contenedor Debug y no certifica Split View o Stage Manager del sistema. Consultar `IPAD_VALIDATION.md` para el estado comprobado.

## Implementado en esta revisión

- Login con el logo, fondo azul/cian, panel, campos, botón y fuentes de la referencia original.
- Dashboard `_cl` identificado en el DEX: barra lateral, fondo azul marino y tres tarjetas originales de TV en directo, Cine y Series. Disposición horizontal fiel a esa estructura y adaptación vertical para iPhone.
- Catálogos por categoría, tarjetas de películas/series, búsqueda en los tres catálogos, favoritos, episodios y guía corta EPG.
- Lista de usuarios guardada en un único vault Keychain, con selección activa, eliminación individual y migración de la sesión anterior. Cerrar sesión conserva la lista; eliminar un usuario retira sus credenciales guardadas.
- Pantalla múltiple con dos o cuatro canales seleccionados, un único audio activo, errores/reintentos por pantalla y liberación de transmisiones al salir o ir al fondo.
- Reproductor AVPlayer, reanudación de VOD, tratamiento de interrupciones y protección frente a respuestas antiguas de otra sesión.
- Normalización de direcciones terminadas en `login.php`, `player_api.php` y `get.php`, preservando los datos de listas M3U y las rutas codificadas.
- Mayor tolerancia a las formas reales de respuestas Xtream y redirecciones de listas dentro del mismo origen.
- Icono iOS de 1024 px compuesto con el logo negro original de 800×312, sin rediseñar ni interpolar el logo.

La presencia de código no equivale a validación en un iPhone físico. Consultar el resultado de CI del commit actual y las diferencias en `PARITY.md`.

## Conexión del proveedor

HTTPS sigue siendo el valor predeterminado. Se añadió una opción explícita para el servidor histórico facilitado por el propietario: únicamente `http://moonspelltools.cc`, sin subdominios. El usuario debe activar esa opción antes de enviar datos por HTTP. El texto del login informa que esa conexión transmite los datos sin cifrar.

La excepción ATS se limita al mismo dominio. No se habilita una excepción global de transporte ni se desactiva la validación de certificados TLS. El control estricto de redirecciones revisado pertenece a las peticiones API y a la descarga M3U por `APIClient`: rechaza cambios de origen y degradaciones de HTTPS a HTTP. Las cargas nativas multimedia de AVPlayer y las imágenes de `AsyncImage` necesitan comprobación propia; no quedan validadas por ese control. Un endpoint HTTPS del proveedor sigue siendo preferible. El puerto y la ruta los introduce el usuario; no hay cuentas, contraseñas ni canales precargados.

No se ha autenticado una cuenta real ni comprobado un stream del proveedor en esta revisión. Las comprobaciones anónimas desde el entorno de desarrollo no demostraron disponibilidad del servicio; eso no prueba que falle en el dispositivo del propietario.

## Compilar y comprobar

Se necesita macOS con Xcode y XcodeGen para construir la aplicación. En un Mac:

```sh
cd pimflextv-ios
swift test
brew install xcodegen
xcodegen generate
open PimflexTV.xcodeproj
```

El workflow `.github/workflows/build-pimflextv-ios.yml` ejecuta las pruebas del núcleo, compila para simulador y para iPhone sin firma, ejecuta pruebas UI y exporta capturas mediante `xcresulttool`. Las pruebas UI usan datos explícitamente ficticios compilados sólo en Debug; no abren transmisiones de un proveedor.

Los artefactos de CI incluyen fuente/proyecto generado, aplicación de simulador y evidencia de pruebas. **No son un instalador firmado para iPhone.** No se genera un IPA ficticio. Consultar la ejecución asociada al SHA antes de afirmar que una compilación o prueba pasó.

## Continuidad en Codex

Entorno privado: **PIMFLEX TV iOS**. Repositorio: `Pinedainsurancegroup/Pineda-Insurance-Group`. Rama: `pimflextv-ios-20261029`. PR en borrador: **#6**.

El **2026-11-06**, el propietario respondió explícitamente «Si te autorizo» y autorizó publicar las imágenes y fuentes originales junto con el código iOS en el repositorio público `Pinedainsurancegroup/Pineda-Insurance-Group`, actualizar el PR #6 y ejecutar Mac CI. Con esta confirmación queda resuelto el bloqueo previo de publicación por falta de autorización para esos recursos. El PR permanece en borrador; la autorización no incluye merge ni publicación en App Store. No incorporar APK/AAB, DEX, secretos, claves de firma, sesiones, credenciales ni respuestas de proveedores al repositorio.

El trabajo local parte del commit `154a31dcccb1ed7c1526370e4bcfe50f5ec99cb5` e incluye correcciones posteriores. El CI de octubre asociado a `518d65f` corresponde a la versión anterior y no valida este código ni el ZIP actualizado. Las comprobaciones locales anteriores fueron estáticas en Linux, sin Swift, Xcode ni XcodeGen. Al registrar esta autorización no se ha confirmado un resultado de CI para la nueva versión: los 26 tests del núcleo, los 6 UI y las compilaciones requieren evidencia de la ejecución asociada al commit actualizado.

Leer `CODEX_HANDOFF.md` y `REFERENCE_402.md` antes de continuar. El entorno de onboarding tuvo un fallo de conectividad al recuperar la rama; una copia verificada del código puede usarse como punto de partida sin resetear trabajo posterior. La configuración o el nombre del entorno no demuestran por sí solos que el código esté recuperado o probado allí.

## Distribución

Antes de TestFlight se requieren cuenta/equipo Apple Developer, firma y registro App Store Connect; comprobar login, formatos, reproducción y funciones pendientes con el proveedor y un iPhone real; completar metadatos, soporte, privacidad y las declaraciones que correspondan al producto final. La compilación sin firma y el simulador no sustituyen esos pasos. No se ha enviado la app a revisión ni publicado en App Store.

Referencias oficiales:
- https://developer.apple.com/documentation/xcode/preparing-your-app-for-distribution
- https://developer.apple.com/documentation/xcode/distributing-your-app-for-beta-testing-and-releases
- https://developer.apple.com/documentation/Xcode-Release-Notes/xcode-16_3-release-notes
