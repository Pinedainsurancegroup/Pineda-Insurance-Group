# Continuidad de APP PIMFLEXTV en Codex

## Compatibilidad de reproducción — candidata 0.3.3 / build 6

El propietario confirmó que ya inicia sesión. Su nueva captura en iPhone muestra el error local `unsupportedFormat` antes de abrir un video. Endpoint.playback rechazaba MKV/AVI/FLV/WMV. Se conserva el reproductor nativo para HLS/MP4 y se incorpora MobileVLCKit 3.7.5 oficial, fijado por podspec local y SHA-256 del archivo del proveedor, para contenedores adicionales. No se cambia la producción Android.

El reproductor compatible integra pausa, búsqueda, avance/retroceso, reanudación y cierre/limpieza. Sólo recibe URLs previamente validadas. Se suprimen logs del backend que podrían incluir una URL con credenciales. Hay una prueba local MKV H.264/AAC generada por FFmpeg, sin contenido del proveedor, y una prueba UI que debe verificar video real, pausa, búsqueda y reapertura. El acceso a la prueba es DEBUG; Release excluye el archivo de muestra. Los límites de red, HTTP/ATS y Keychain se mantienen.

CocoaPods 1.16.2 usa el podspec oficial 3.7.5 del registro, conservado localmente con URL/sha256 exactos. Se compila el workspace, incluidas las exportaciones firmadas. La biblioteca y libVLC permanecen sin modificar; se incorporan licencia y enlaces de código fuente en Ajustes. No se incluyen binarios del proveedor en Git.

La nueva biblioteca puede aportar criptografía estándar de transporte/medios. No debe describirse la versión actual como dependiente sólo de criptografía Apple sin revisar sus componentes. La app es un reproductor dedicado a entretenimiento; BIS describe esa finalidad como excluida de los controles de confidencialidad de categoría 5 (https://media.bis.gov/learn-support/encryption-controls/cryptography-for-data-confidentiality). Apple permite ITSAppUsesNonExemptEncryption=false para usos exentos, incluidas dependencias (https://developer.apple.com/documentation/Security/complying-with-encryption-export-regulations). No se publica ni distribuye en App Store Francia; revisar requisitos antes de cualquier distribución pública. No se afirma una nueva declaración de cifrado aceptada en el portal.

Pruebas Python de firma: 10 correctas localmente; Swift, enlace de VLCKit, interfaz/decodificación y firma de build 6 pendientes de CI Mac. No afirmar compatibilidad o disponibilidad antes de esas verificaciones.

## Corrección del enlace M3U grande — 0.3.2 / build 5

La nueva captura del propietario muestra HTTP activado y el error genérico de respuesta. La comprobación privada del enlace confirmó HTTP 200, cabecera M3U y una lista que supera incluso 128 MiB, con cientos de miles de entradas; la lectura se detuvo sin guardar el catálogo ni sus credenciales. La cuenta se autenticó como Active por la API del mismo proveedor. El límite previo de 32 MiB explica el rechazo observado; aumentar ese límite y cargar el catálogo completo no es necesario para iniciar sesión.

Se importa el usuario/contraseña de enlaces estándar get.php de los dos proveedores exactos conocidos y se autentica la misma cuenta mediante su API. El propietario puede seguir pegando el enlace en «Lista M3U». La cuenta resultante usa el acceso por usuario/contraseña y se guarda en Keychain sin consulta de credenciales en la dirección del servidor. Se conservan el consentimiento HTTP, los hosts y ATS exactos, TLS y redirecciones. Enlaces genéricos, parámetros desconocidos, duplicados o formatos distintos conservan su modo M3U; si exceden el límite reciben un aviso específico. No se modifica el reproductor ni se cambian cuentas reales en el código.

Cinco regresiones nuevas cubren autenticación API de un enlace importado sin descargar get.php, decodificación PHP y rutas de tenant, consentimiento/hosts, listas genéricas ambiguas y el error de tamaño. Código ejecutable `20564dea4dd396205e50a597edc34ca98e6194ea`. [CI 42735491413](https://github.com/Pinedainsurancegroup/Pineda-Insurance-Group/actions/runs/42735491413): success, 33 pruebas del núcleo, 10 de firma, Debug y Release universales; UI iPhone 7 correctas (4 exclusivas iPad omitidas), mini 11 y Pro 11, sin fallos. La prueba M3U verifica el usuario importado después de consentir en los tres simuladores (Xcode 16.4/iOS 18.5, fixtures). [Firma 42735483216](https://github.com/Pinedainsurancegroup/Pineda-Insurance-Group/actions/runs/42735483216): success, Xcode 26.3/iOS SDK 26.2. HMAC y hashes de artefacto/IPA, informe de firma y perfil original exacto comprobados. IPA SHA-256: `3f141f8c06bb9e4fa2e919cc50838ff0bcbafd4b0d38ebbb978fdc0ea5de2be8`.

Los catálogos reales por API se comprobaron privadamente como HTTP 200/JSON válido y compatibles con el límite vigente. No se guardaron respuestas ni se abrieron streams; esto no es prueba de la IPA en dispositivo. Apple confirmó carga COMPLETE, build VALID e IN_BETA_TESTING, sin errores ni advertencias. La API oficial verifica el build exacto en «PIMFLEX TV - Juan», grupo interno automático con tres builds y un único tester titular. Build/carga `1a11c0b9-4b3f-47d1-abb8-f13ee66bad87`; archivo `aa302fb0-a06f-4485-b1cf-4271310e9ad1`. La actualización 0.3.2 (5) está habilitada en TestFlight. No se crean claves, invitaciones ni declaraciones nuevas y no hay publicación en App Store. No repetir la carga. El propietario actualiza en TestFlight, pega el mismo enlace M3U, activa HTTP e inicia sesión. La instalación, login y reproducción del build 5 en dispositivo físico siguen pendientes.

## Corrección de acceso HTTP en iPad — 0.3.1 / build 4

El propietario confirmó que 0.3.0/build 3 se instaló correctamente en su iPad. La captura posterior muestra una lista M3U de `my-vionex.com:8080` por HTTP y el interruptor HTTP apagado. La versión instalada sólo admitía `moonspelltools.cc`; la validación local bloqueó la URL antes de autenticar. No se ha comprobado todavía acceso o reproducción real.

0.3.1/build 4 admite también el host exacto `my-vionex.com`, servidor HTTP proporcionado anteriormente por el propietario. El usuario debe activar «Mi servidor requiere HTTP» en su dispositivo. Se mantienen el consentimiento por cuenta, las reglas de origen en redirecciones y las excepciones ATS por dominio sin subdominios. La app distingue ahora entre consentimiento pendiente y un host HTTP no admitido. La lista M3U conserva su consulta; no se incorpora ninguna cuenta real al código o las pruebas.

La regresión UI del flujo M3U sin/con consentimiento usa datos ficticios. Las pruebas del núcleo incluyen URL, reproducción y redirecciones entre ambos hosts. La declaración ITSAppUsesNonExemptEncryption=false incorpora al plist la declaración ya autorizada para esta misma app; no se introduce criptografía nueva.

Código ejecutable `b7022c7224962f5fe9dd92bced949b35721d450f`. [CI 42718460305](https://github.com/Pinedainsurancegroup/Pineda-Insurance-Group/actions/runs/42718460305): success, 28 pruebas núcleo, 10 Python de firma, compilaciones universales Debug/Release, 7 UI iPhone (4 exclusivas iPad omitidas), 11 UI mini y 11 UI Pro, sin fallos. La nueva regresión M3U pasa en los tres. UI usa Xcode 16.4/iOS 18.5 y fixtures; no prueba proveedor real. [Firma 42718451601](https://github.com/Pinedainsurancegroup/Pineda-Insurance-Group/actions/runs/42718451601): success con Xcode 26.3/SDK 26.2 y la identidad/perfil existentes. Se recuperó el artefacto autenticado y se cotejaron los hashes, informe de firma y perfil exacto. IPA SHA-256: `52bd39eccf29c2cbeb4e47310ec1641a3b1476d34f6022ead7d62194f0e63051`.

Apple confirmó build 4 con carga COMPLETE, processingState VALID y estado interno IN_BETA_TESTING, sin errores ni advertencias. La API oficial verifica que el grupo interno automático «PIMFLEX TV - Juan» contiene builds 3 y 4 y sólo el tester titular. Build/carga `d8f8f26b-8c51-4e63-8f27-8e13014bc96b`; archivo `e5052cc3-dad8-4756-b76c-19c85a1461a5`. No requiere otra declaración de cifrado. La actualización está habilitada en TestFlight. Esta verificación es por API; no se afirma una nueva captura del portal Apple. No repetir carga, claves, pagos ni declaración. El propietario tendrá que actualizar, conservar su URL y activar «Mi servidor requiere HTTP» antes de iniciar sesión. Falta validar autenticación y reproducción con su cuenta real. Las secciones siguientes conservan el historial de build 3.

## Continuación para instalar en iPad — 2026-11-09

El propietario autorizó expresamente revocar la clave de carga que no pudo recuperarse y crear una sustituta con el mismo rol Desarrollador. La anterior quedó **Anulada** y **PIMFLEX TV TestFlight Upload 2** quedó **Activa**. Esta vez se recuperaron y verificaron sus bytes P-256 inmediatamente; se comprobó la recuperación de un respaldo PKCS#8 cifrado y se conservaron privadamente `PIMFLEX_Apple_Upload_Private_20261109.zip` y `PIMFLEX_Apple_Upload_Recovery_20261109.txt` por separado. No volver a crear claves, identidades, perfiles ni pagos. No se añadió la clave API a GitHub ni a CI.

Se cargó la **misma IPA universal 0.3.0 / build 3** ya firmada, sin recompilar ni modificar el ejecutable. Se volvió a comprobar su SHA-256 y su plist antes de enviarla. La API oficial creó la carga y el archivo con HTTP 201; la transferencia terminó HTTP 200 y la confirmación del archivo quedó **COMPLETE**. En esta ejecución el servidor rechazó el checksum SHA_256 y aceptó MD5; el SHA-256 de la IPA se mantiene como comprobación de la entrega original. No repetir la transferencia.

Apple terminó el procesamiento con **BuildUpload COMPLETE**, sin errores ni advertencias, y **Build processingState VALID**. ID de carga/build `3dc91609-ea08-426f-bcb1-6053df676dbd`; archivo `308579a3-4f67-4077-b364-d67dc2acd690`. Mínimo iOS 16.0, audiencia APP_STORE_ELIGIBLE, expiración beta 2027-02-07. La vista TestFlight muestra **Versión 0.3.0 / Compilación 3**. No confundir VALID con una app probada físicamente o ya habilitada para instalar.

Se creó el grupo interno **PIMFLEX TV - Juan**, ID `64f4c997-2789-4c3d-939f-2d877939ab0b`, con distribución automática habilitada y únicamente el titular existente como tester. Después de guardar la declaración autorizada, el grupo incorporó automáticamente la compilación 0.3.0 (3); el portal muestra **1 tester · 1 compilación**, build **En pruebas** y titular **Invitado (9 nov. 2026)**. No se añadió a otras personas ni se habilitó una beta pública.

**TestFlight habilitado.** El propietario autorizó expresamente guardar la declaración de cifrado preparada. Se guardó «Ninguno de los algoritmos mencionados anteriormente»; desapareció MISSING_EXPORT_COMPLIANCE y la compilación pasó a «Lista para enviar». El grupo interno automático incorporó el build y quedó **En pruebas**, con el titular **Invitado**. La opción de añadirlo manualmente aparecía deshabilitada; al abrir el grupo se verificó que ya contenía la compilación. No fue necesario forzar ninguna asignación ni repetir invitaciones.

La declaración se apoya en la revisión de Package.swift y los imports/usos: no hay dependencias externas; CryptoKit sólo calcula SHA-256 para identificadores, Security usa Keychain y HTTPS usa URLSession de Apple. La revisión automática anterior quedó resuelta con la aprobación del propietario; no volver a solicitarla. No se modificó Info.plist ni se cambió el ejecutable. El siguiente paso es instalar TestFlight en el dispositivo del titular, abrir su invitación y probar acceso/streams. El propietario confirmó la instalación física en iPad; autenticación y sesiones de reproducción siguen pendientes.

La autorización para carga/custodia y su sustitución ya está concedida; no volver a pedirla. La autorización para código público no incluye publicar en App Store ni fusionar PR #6, que permanece en borrador. Mantener privados claves, recuperación, JWT, URLs de transferencia y la IPA. El siguiente paso no requiere repetir compilaciones ni el registro Apple.

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
La IPA y el informe se conservaron privadamente. El 2026-11-09 esta IPA se
cargó a Apple y terminó con estado VALID. La información
de exportación autorizada ya se guardó y la prueba interna está habilitada; falta comprobar la instalación y uso físico;
véase el estado al comienzo.

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
La autorización original de firma no incluye publicación en App Store, merge ni otras credenciales; la autorización posterior de la clave de carga figura al comienzo.

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

Siguiente paso: el titular instala TestFlight en su iPhone/iPad, abre la invitación
a su cuenta de desarrollador y prueba login, catálogo y reproducción. El portal
ya confirma En pruebas e Invitado. No pedir otra aprobación para la declaración,
clave o carga completadas. No hay credenciales de carga en CI. No solicitar claves,
contraseñas o códigos por chat. Mantener PR #6 en borrador; no publicar en App Store.

## Ampliación iPad — 2026-11-08 (California)

El propietario solicita Android, iPhone e iPad, con toda la programación en Codex. Se amplía el producto universal existente; no se crea otro identificador ni se altera la producción Android. Candidata 0.3.0 / build 3: categorías laterales según ancho de ventana, controles compactos al reducirlo y carátulas 2:3. Se agregan cuatro pruebas específicas iPad y CI con iPhone, iPad mini y iPad Pro grande. Las cuatro pantallas se ajustan a la altura disponible en horizontal. El núcleo y las credenciales permanecen intactos. Ver `IPAD_VALIDATION.md`.

Cierre técnico: código `2eeeea894d3cdbfad5112914a85ec7949d3101d7`, CI https://github.com/Pinedainsurancegroup/Pineda-Insurance-Group/actions/runs/42467076147, resultado `success`: 26 pruebas de núcleo, 6 UI iPhone, 10 UI iPad mini y 10 UI iPad Pro, sin fallos. Debug simulador y Release universal sin firma correctos. Las cuatro pruebas exclusivas iPad se omiten en iPhone. Capturas finales exportadas; revisión visual del catálogo y cuatro pantallas. El registro posterior sólo cambia Markdown. Continuar desde HEAD remoto, preservando estas mejoras; la firma y carga posteriores figuran al comienzo; pendiente prueba física/proveedor.

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
