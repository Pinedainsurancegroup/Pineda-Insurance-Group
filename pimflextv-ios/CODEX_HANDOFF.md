# Continuidad de APP PIMFLEXTV en Codex

### Autorización de ficha interna y sesión — 2026-11-08

Juan respondió expresamente «si autorizo» a la creación de la ficha interna PIMFLEX TV en App Store Connect, vinculada a com.pimflextv.ios, para TestFlight y sin publicación. Esta autorización ya está concedida: no pedirla nuevamente. Al retomar «Nueva app», App Store Connect redirigió a /login; no se llegó al formulario ni se creó ficha. La sesión Developer también estaba esperando inicio de sesión. Retomar tras autenticar en el navegador en la nube; reutilizar la clave cifrada y CSR ya guardados. No confundir las pantallas conservadas con sesiones vigentes.

## Firma Apple — 2026-11-08 (California)

La activación fue confirmada por los correos oficiales de bienvenida de Apple Developer y App Store Connect. Tras el inicio de sesión realizado por Juan, el portal oficial muestra membresía individual vigente hasta el 8 de noviembre de 2027 y Team ID `U47SH3LZM6`. Certificates, Identifiers & Profiles está accesible.

Se registró y verificó en la lista de Apple el App ID explícito **PIMFLEX TV**, `com.pimflextv.ios`, para el producto universal existente. No se habilitaron capacidades adicionales opcionales. `project.yml` ahora configura `DEVELOPMENT_TEAM: U47SH3LZM6` en el target de aplicación. No cambian las versiones ni el núcleo.

Juan autorizó expresamente crear el certificado Apple Distribution y su clave privada. Se generó una única clave RSA 2048 cifrada en PKCS#8 y un CSR SHA-256 cuya firma fue verificada. La clave cifrada, el CSR y los metadatos se respaldaron privadamente; la contraseña de recuperación quedó en un archivo privado separado. No regenerar la clave ni el CSR al retomar. Apple recibió el archivo CSR en el formulario, pero al pulsar Continue mostró «Your session has expired. Please log in.». Una consulta fresca de Certificates también redirigió al inicio de sesión. **La emisión no está confirmada**: inspeccionar primero la lista y comparar la clave pública antes de reintentar, para evitar certificados duplicados. No enviar materiales privados por chat, PR, commits o artefactos públicos. Antes de usar CI con firma, acordar custodia privada y acceso del runner a los materiales; no guardar secretos de firma en el repositorio público.

Juan informó que aceptó los términos de App Store Connect; la inspección posterior confirmó acceso a Apps, sin el acuerdo bloqueante y con la lista vacía. La revisión automática bloqueó iniciar «Nueva app» por considerar que la creación de la ficha no estaba incluida en la autorización de firma. Se necesita autorización específica para crear la ficha interna de PIMFLEX TV vinculada al App ID existente; esto no equivale a publicación. No se creó ficha, perfil ni IPA; no se publicó en TestFlight/App Store ni se repitieron pagos. El CI 42527378218 confirmó success para el commit 29f2a56ebf0cf14275c4c2dbf695cd6284c4193c, que añade DEVELOPMENT_TEAM. Sigue siendo compilación sin firma.

Continuación: resolver los términos y la autorización de firma, generar/custodiar la identidad Apple Distribution y el perfil App Store Connect del App ID registrado; configurar compilación/exportación firmada en macOS y validar la IPA antes de distribuirla. Reutilizar el producto universal y preservar el PR #6 en borrador.

## Ampliación iPad — 2026-11-08 (California)

El propietario solicita Android, iPhone e iPad, con toda la programación en Codex. Se amplía el producto universal existente; no se crea otro identificador ni se altera la producción Android. Candidata 0.3.0 / build 3: categorías laterales según ancho de ventana, controles compactos al reducirlo y carátulas 2:3. Se agregan cuatro pruebas específicas iPad y CI con iPhone, iPad mini y iPad Pro grande. Las cuatro pantallas se ajustan a la altura disponible en horizontal. El núcleo y las credenciales permanecen intactos. Ver `IPAD_VALIDATION.md`.

Cierre técnico: código `2eeeea894d3cdbfad5112914a85ec7949d3101d7`, CI https://github.com/Pinedainsurancegroup/Pineda-Insurance-Group/actions/runs/42467076147, resultado `success`: 26 pruebas de núcleo, 6 UI iPhone, 10 UI iPad mini y 10 UI iPad Pro, sin fallos. Debug simulador y Release universal sin firma correctos. Las cuatro pruebas exclusivas iPad se omiten en iPhone. Capturas finales exportadas; revisión visual del catálogo y cuatro pantallas. El registro posterior sólo cambia Markdown. Continuar desde HEAD remoto, preservando estas mejoras; pendiente firma y prueba física/proveedor.

Juan informa que ya pagó la membresía y espera activación. Esta tarea no revisa ni modifica la cuenta Apple, los acuerdos, certificados o App Store Connect. No tomar ese pago reportado como confirmación técnica de activación.

## Objetivo del propietario

Clonar la apariencia y las funciones de la app Android PIMFLEX TV 4.0.2 adjunta para iPhone, trabajando en Codex. Continuar este código nativo; no abrir otro repositorio ni regenerar APKs para esta tarea.

## Ubicación

- Repositorio: `Pinedainsurancegroup/Pineda-Insurance-Group`
- Rama: `pimflextv-ios-20261029`
- PR existente en borrador: https://github.com/Pinedainsurancegroup/Pineda-Insurance-Group/pull/6
- Código: `pimflextv-ios/`
- Mac CI: `.github/workflows/build-pimflextv-ios.yml`
- Base anterior verificada: `518d65fc60f888680bf3d2e489cf214c5b675bd6`; consultar HEAD actual antes de editar, conservar avances posteriores.

## Autorización de publicación — 2026-11-06

El propietario respondió explícitamente «Si te autorizo» y autorizó publicar las imágenes y fuentes originales junto con el código iOS en el repositorio público `Pinedainsurancegroup/Pineda-Insurance-Group`, actualizar el PR #6 y ejecutar Mac CI. La falta de autorización que motivó el bloqueo previo de publicación queda resuelta. Mantener el PR en borrador; esta autorización no incluye merge ni publicación en App Store y no cambia las exclusiones de material privado indicadas abajo.

La versión del ZIP parte del commit local `154a31dcccb1ed7c1526370e4bcfe50f5ec99cb5` e incluye correcciones posteriores. El CI de octubre asociado a `518d65f` pertenece a la versión anterior y no valida este ZIP ni el código actualizado. Las comprobaciones locales anteriores fueron estáticas en Linux, sin Swift, Xcode ni XcodeGen. Al registrar esta autorización no se ha confirmado un resultado de CI para la nueva versión: verificar las compilaciones, los 26 tests del núcleo y los 6 UI en la ejecución correspondiente al commit actualizado.

## Límites de trabajo

Trabajar únicamente en iOS de PIMFLEX TV y su workflow. Preservar producción Android 3.1.0 y su núcleo de reproducción. El repositorio incluye otros proyectos; no editar PAG ni Taty Nails. No incorporar APK/AAB, DEX, claves de firma, sesiones, credenciales o respuestas de proveedores al repositorio público. Los assets visuales aquí presentes proceden de los adjuntos del propietario; el análisis completo de esos binarios es material privado de referencia.

## Comprobaciones

1. Revisar estado local y rama remota antes de editar o actualizar el PR; no resetear cambios ajenos.
2. Leer `REFERENCE_402.md`, `PARITY.md` y el código actual. La plantilla real es `_cl`; no sustituirla por el fondo púrpura ni los gradients de otra plantilla.
3. En Linux hacer las comprobaciones disponibles y usar el workflow macOS para compilar, probar UI y recuperar capturas. No afirmar compilación Xcode local si no existe Xcode.
4. Verificar cada resultado de CI por commit. Revisar capturas horizontal/vertical; las muestras DEBUG no son una prueba de cuenta o streaming real.
5. Mantener PR en borrador; no fusionar a producción ni publicar en App Store como parte de desarrollo.

## Pendientes de producto

Resolver las diferencias de `PARITY.md`, empezando por login/reproducción con el proveedor real, Catch up/EPG completo y comparación visual. La opción HTTP sólo permite el dominio exacto documentado tras una decisión explícita en la app; no ampliar dominios o excepciones globales sin evidencia de necesidad. Mantener el aislamiento por cuenta, los datos sensibles en Keychain y la validación TLS.

El control estricto de redirecciones revisado corresponde a las peticiones API y a la descarga M3U por `APIClient`: rechaza cambios de origen y degradaciones de HTTPS a HTTP. Las cargas nativas multimedia de AVPlayer y las imágenes de `AsyncImage` requieren comprobación propia; ese control no certifica su comportamiento.

La cuenta Apple Developer y la firma seguían sin estar disponibles al iniciar esta revisión. No pedir contraseñas, certificados privados o tokens por chat o en un PR público. Preparar el código y las pruebas antes de solicitar la intervención necesaria para la distribución.
