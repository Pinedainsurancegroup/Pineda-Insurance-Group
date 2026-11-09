# Continuidad de APP PIMFLEXTV en Codex

## Continuación para instalar en iPad — 2026-11-08 (California)

Se recuperaron de la entrega privada la IPA 0.3.0/build 3 y su informe, sin recompilar ni modificar el ejecutable. Su SHA-256 coincide con la exportación validada; el plist confirma `com.pimflextv.ios`, familias `[1,2]` y SDK `iphoneos26.2`.

La sesión de App Store Connect conserva acceso a la ficha existente. TestFlight mostró expresamente **«No hay compilaciones»** y **«Envía una compilación para empezar las pruebas»**. Juan completó personalmente la aceptación y respondió «listo». Se verificó en el portal **«Se ha aprobado tu solicitud para acceder a la API de App Store Connect»**, con **Activa (0)**. No se creó ninguna clave API ni se cargó la IPA.

La creación de la clave de carga quedó bloqueada por revisión automática: es una credencial permanente y la aceptación de condiciones no constituye autorización específica para crearla. Antes de generar una clave, obtener autorización concreta para su creación, custodia privada y uso con rol Desarrollador para cargar PIMFLEX TV a TestFlight. Las claves de equipo se aplican a todas las apps de la cuenta y permanecen activas hasta revocarse. La autorización previa de la identidad y secretos de firma no es autorización de esta nueva credencial. Después, cargar la IPA existente, esperar procesamiento y preparar la prueba interna iPad/iPhone. No repetir registro, pago, identidad de firma ni compilaciones ya validadas. No exponer la IPA ni material privado en GitHub.

## Estado actual de firma — 2026-11-08

La IPA **0.3.0 / build 3** universal se exportó y validó en macOS con
Xcode **26.3**, SDK **iOS 26.2**, commit
`5f6323b6acab811a77d38144e1c5c32cd7b7817c`.
Ejecución: https://github.com/Pinedainsurancegroup/Pineda-Insurance-Group/actions/runs/42533688228
(`success`, preflight y signed-export correctos).
SHA-256 de la IPA: `ab37d76ba2103ac7065d9a9c214215453a2f81c13cde4cff51116f77795741b4`.
La firma, los entitlements, el perfil y las familias iPhone/iPad se comprobaron
en el runner; tras recuperar el artefacto se verificaron HMAC, SHA-256 y la
coincidencia exacta del perfil embebido con el original validado.
La IPA y el informe se conservaron privadamente. **Todavía no se ha cargado a
App Store Connect ni procesado en TestFlight**; falta carga con credenciales
Apple autorizadas y prueba física. No se crearon credenciales de carga.

## Autorizaciones y custodia vigentes

La membresía individual se confirmó activa en correos oficiales y el portal,
vigente hasta 2027-11-08; Team ID `U47SH3LZM6`. El App ID explícito es
`com.pimflextv.ios`. App Store Connect contiene la ficha interna **PIMFLEX TV**,
Apple ID **6832365413**, SKU `PIMFLEXTV-IOS`, Español (México), plataforma iOS.
La versión inicial de ficha es 1.0, «En preparación para el envío»; el código
candidato es 0.3.0/build 3. No hubo publicación ni envío a revisión.

Juan aceptó personalmente los acuerdos y autorizó expresamente la ficha interna,
la identidad Apple Distribution y el acceso de GitHub Actions macOS a los tres
secretos de firma. El entorno `pimflextv-apple-signing` (**26657933808**) quedó
configurado y verificado: revisor propietario `Pinedainsurancegroup`, rama exacta
`pimflextv-ios-20261029`, sin omisión por administradores. Secretos:
`PIMFLEX_SIGNING_P12_B64`, `PIMFLEX_SIGNING_P12_PASSWORD`,
`PIMFLEX_PROFILE_B64`. Esta autorización ya está concedida; no pedirla otra vez.
No incluye publicación en App Store, merge, otras claves ni cambios de credenciales.

Identidad única Apple Distribution **4FQY49J2JC**, SHA-1
`8C2189D902AEA4E06493D80603886E98E1A35BD6`; perfil
**PIMFLEX TV App Store 2026**, ID **92LSL5KN37**, UUID exacto
`ed0cbb48-09a0-4031-a16f-db7c242c3181`, ambos hasta 2027-11-08.
El certificado, CSR y clave original coinciden. El CMS del perfil y su cadena se
verificaron con Apple Root CA, huella contrastada con Apple. Se mantienen el
PKCS#12 moderno cifrado, la clave PKCS#8 cifrada y su recuperación por separado
en un respaldo privado. No regenerar identidades ni perfiles duplicados.

## Proceso validado y siguiente paso

El workflow protegido se activa sólo al modificar `SIGNING_REQUEST.json` en
esta rama. Recupera el SHA exacto, comprueba Xcode/SDK 26 o posterior, ejecuta
pruebas y Release sin firma, espera revisión del propietario y firma con llavero
temporal. El PKCS#12 moderno se convierte a formato compatible sólo dentro del
runner, sin escribir claves en claro. Se conserva el UUID exacto de Apple, emitido en minúsculas. Tras el error de perfil
no encontrado se retiró su conversión a mayúsculas y se seleccionó Xcode 26.3.
La salida pública de Actions contiene únicamente un artefacto cifrado y autenticado
con retención de un día; la IPA recuperada permanece privada. La limpieza de
llavero y archivos temporales terminó correctamente.

El preflight final pasó **26 tests del núcleo + 10 de firma**, y la exportación
firmada pasó con Xcode 26.3/iOS SDK 26.2. Las comprobaciones completas de interfaz
anteriores (iPhone, iPad mini y iPad Pro) pasaron en 42532088588; la compilación
sin firma y iPad mini de d1be897 también pasaron. No afirmar pruebas físicas ni
de proveedor real, ni pruebas de interfaz en iOS 26: siguen pendientes.

Siguiente paso: cargar la IPA privada a la ficha existente mediante
Transporter/Xcode con autenticación Apple autorizada, esperar procesamiento y
habilitar una prueba interna en TestFlight. No hay credenciales de carga
configuradas en CI. No pedir contraseñas, códigos ni claves por chat, ni tratar
la IPA App Store Connect como instalación directa. No repetir pagos ni aceptar
acuerdos por el propietario. Conservar PR #6 en borrador y las exclusiones de
otros proyectos descritas abajo.

## Ampliación iPad — 2026-11-08 (California)

El propietario solicita Android, iPhone e iPad, con toda la programación en Codex. Se amplía el producto universal existente; no se crea otro identificador ni se altera la producción Android. Candidata 0.3.0 / build 3: categorías laterales según ancho de ventana, controles compactos al reducirlo y carátulas 2:3. Se agregan cuatro pruebas específicas iPad y CI con iPhone, iPad mini y iPad Pro grande. Las cuatro pantallas se ajustan a la altura disponible en horizontal. El núcleo y las credenciales permanecen intactos. Ver `IPAD_VALIDATION.md`.

Cierre técnico: código `2eeeea894d3cdbfad5112914a85ec7949d3101d7`, CI https://github.com/Pinedainsurancegroup/Pineda-Insurance-Group/actions/runs/42467076147, resultado `success`: 26 pruebas de núcleo, 6 UI iPhone, 10 UI iPad mini y 10 UI iPad Pro, sin fallos. Debug simulador y Release universal sin firma correctos. Las cuatro pruebas exclusivas iPad se omiten en iPhone. Capturas finales exportadas; revisión visual del catálogo y cuatro pantallas. El registro posterior sólo cambia Markdown. Continuar desde HEAD remoto, preservando estas mejoras; pendiente firma y prueba física/proveedor.

La membresía Apple Developer se confirmó activa posteriormente mediante correos oficiales y el portal; véase el estado de firma al comienzo.

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

No pedir contraseñas, certificados privados o tokens por chat o en un PR público. Reutilizar la identidad y el entorno protegido existentes.
