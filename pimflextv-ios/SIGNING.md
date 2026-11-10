# Firma de PIMFLEX TV para iPhone e iPad

El producto universal usa `com.pimflextv.ios` y el equipo `U47SH3LZM6`.
El App ID está registrado. Juan autorizó la identidad Apple Distribution y la
ficha interna en App Store Connect para TestFlight; no autorizó una publicación
en App Store. La clave cifrada y el CSR existentes están respaldados privadamente.
No generar otra clave al retomar ni incluir material privado en este repositorio.

## Estado verificable

La actualización **0.3.3 / build 6**, código `326c714262ca9aa4c896fd11fd202e3ac37bacd3`, se exportó con la identidad y perfil existentes. [Firma 42743958787](https://github.com/Pinedainsurancegroup/Pineda-Insurance-Group/actions/runs/42743958787): success, Xcode 26.3/SDK 26.2, 37 pruebas núcleo y 10 de firma correctas en preflight, Release universal y firma/perfil/entitlements/familias verificados. IPA SHA-256 `b9be339aefc1dde3f9b947adf7c8fabf22ab059481880b8459091a3aa683edaa`. HMAC/hash, perfil exacto, framework/licencia incluidos y muestra MKV ausente comprobados. Se usa el workspace y el SDK oficial fijado se prepara antes de importar la identidad privada.

[CI 42747510260](https://github.com/Pinedainsurancegroup/Pineda-Insurance-Group/actions/runs/42747510260) final **success** en `1487328dd5f69c9f04ce5148e854532d10e8598d`; el diff respecto de la IPA sólo modifica la muestra DEBUG y la prueba UI, con insumos de Release idénticos. No regenerar la IPA por ese cambio de pruebas. Apple confirmó COMPLETE/VALID e IN_BETA_TESTING, sin errores ni advertencias. La API oficial verifica el build exacto `9b533fa7-c06f-4bf2-95d4-85c88e38d72c` en el grupo interno automático «PIMFLEX TV - Juan», con cuatro builds y un único tester titular. Archivo de carga `98f5e8d7-fa37-4173-a152-0ffc5b8d3ecf`. La versión **0.3.3 (6)** está habilitada en TestFlight para iPhone e iPad. No repetir carga, pago, firma ni creación de credenciales.

`ITSAppUsesNonExemptEncryption=false` está en la IPA aceptada; ésta incorpora ahora un SDK multimedia de terceros. No describir la versión actual como si sólo usara bibliotecas de cifrado de Apple. La distribución pública, sus metadatos/declaraciones finales y la reproducción física siguen pendientes.

### Historial 0.3.2 / build 5

La actualización **0.3.2 / build 5** se exportó desde el commit
`20564dea4dd396205e50a597edc34ca98e6194ea`.
[Exportación 42735483216](https://github.com/Pinedainsurancegroup/Pineda-Insurance-Group/actions/runs/42735483216):
success (33 pruebas del núcleo, 10 de firma, Release universal y firma/exportación
correctos), Xcode 26.3/iOS SDK 26.2. IPA SHA-256:
`3f141f8c06bb9e4fa2e919cc50838ff0bcbafd4b0d38ebbb978fdc0ea5de2be8`.
HMAC, hashes y perfil embebido exacto verificados al recuperar el artefacto.
Apple confirmó carga COMPLETE, build VALID e IN_BETA_TESTING, sin errores ni advertencias. La API oficial verifica el build exacto en «PIMFLEX TV - Juan», grupo interno automático con tres builds y un único tester titular. Build/carga `1a11c0b9-4b3f-47d1-abb8-f13ee66bad87`; archivo `aa302fb0-a06f-4485-b1cf-4271310e9ad1`. La actualización 0.3.2 (5) está habilitada en TestFlight. No se crean claves, invitaciones ni declaraciones nuevas y no hay publicación en App Store. Se reutilizan identidad, perfil y clave de carga
existentes; no se crean credenciales ni se cambia la declaración de cifrado.

### Historial 0.3.1 / build 4

La actualización **0.3.1 / build 4** se exportó desde el commit
`b7022c7224962f5fe9dd92bced949b35721d450f` con la misma identidad y perfil.
[Ejecución 42718451601](https://github.com/Pinedainsurancegroup/Pineda-Insurance-Group/actions/runs/42718451601):
`success`, Xcode 26.3/iOS SDK 26.2, 28 pruebas del núcleo, 10 de firma,
Release universal y exportación/firma/perfil/entitlements correctos.
SHA-256 de IPA: `52bd39eccf29c2cbeb4e47310ec1641a3b1476d34f6022ead7d62194f0e63051`.
Se verificaron el HMAC y los hashes antes de recuperar la IPA privada; el perfil
embebido coincide exactamente con el original. Apple confirmó la carga COMPLETE,
el build VALID e IN_BETA_TESTING, sin errores/advertencias. La API oficial confirma
el build exacto en el grupo interno automático del titular (dos builds, un tester).
Build/carga `d8f8f26b-8c51-4e63-8f27-8e13014bc96b`; archivo
`e5052cc3-dad8-4756-b76c-19c85a1461a5`. Disponible para actualizar en TestFlight.
`ITSAppUsesNonExemptEncryption=false` incorpora la declaración previamente
autorizada para esta misma app, sin introducir criptografía nueva.

### Identidad vigente e historial de build 3

La ficha interna **PIMFLEX TV**, Apple ID **6832365413**, está creada en App
Store Connect (Español México, SKU `PIMFLEXTV-IOS`), sin publicación.
El certificado Apple Distribution **4FQY49J2JC** y el perfil
**PIMFLEX TV App Store 2026** (**92LSL5KN37**) vencen el **8 de noviembre de 2027**.

El propietario adjuntó los dos archivos oficiales. Se comprobó que:
- El certificado, el CSR y la clave privada existente comparten la misma clave pública.
- La firma CMS del perfil es válida y su cadena se verifica contra Apple Root CA,
  con huella SHA-256 contrastada con la lista oficial de Apple.
- El perfil UUID `ed0cbb48-09a0-4031-a16f-db7c242c3181` corresponde al App ID
  explícito `U47SH3LZM6.com.pimflextv.ios`, al equipo correcto y al certificado
  seleccionado; es App Store Connect, no desarrollo/Ad Hoc/Enterprise.
- Se creó un PKCS#12 cifrado y se verificó su recuperación. La clave no cambió.

La huella SHA-1 de la identidad es `8C2189D902AEA4E06493D80603886E98E1A35BD6`.
El material real y su recuperación se conservan privadamente, fuera del repositorio.
La IPA **0.3.0 / build 3** universal se exportó y validó en macOS con
Xcode **26.3**, SDK **iOS 26.2**, commit
`5f6323b6acab811a77d38144e1c5c32cd7b7817c`.
Ejecución: https://github.com/Pinedainsurancegroup/Pineda-Insurance-Group/actions/runs/42533688228
(`success`, preflight y signed-export correctos).
SHA-256 de la IPA: `ab37d76ba2103ac7065d9a9c214215453a2f81c13cde4cff51116f77795741b4`.
La firma, los entitlements, el perfil y las familias iPhone/iPad se comprobaron
en el runner; tras recuperar el artefacto se verificaron HMAC, SHA-256 y la
coincidencia exacta del perfil embebido con el original validado.
La IPA y el informe se conservaron privadamente. Esta misma IPA se cargó a Apple
el 2026-11-09 mediante la API oficial: carga COMPLETE y compilación VALID,
sin errores/advertencias. El titular autorizó guardar la declaración de cifrado y se completó ese paso.
El grupo interno ya contiene el build 0.3.0 (3), con estado En pruebas y titular
Invitado. La instalación y reproducción en dispositivos físicos siguen pendientes.

## Clave de carga a TestFlight — 2026-11-09

El propietario autorizó creación, custodia privada y uso de una clave API de equipo
con rol Desarrollador para cargar PIMFLEX TV, y posteriormente la revocación y
sustitución de la primera clave cuya descarga no pudo recuperarse. La anterior
quedó anulada y **PIMFLEX TV TestFlight Upload 2** activa. La sustituta se recuperó,
validó como P-256 y respaldó como PKCS#8 cifrado, con recuperación separada y
verificación de descifrado. No contiene ni requiere otra identidad de firma.
No se configuró esta clave API en CI ni se incluyó material privado en GitHub.

La API creó `buildUploads` y `buildUploadFiles`, recibió la IPA y confirmó su
checksum MD5; el SHA-256 coincide con la exportación firmada original. Carga y
build: `3dc91609-ea08-426f-bcb1-6053df676dbd`. Apple confirmó COMPLETE/VALID.
Se creó el grupo interno del titular. Tras su aprobación explícita, se guardó la
declaración de cifrado y la compilación se habilitó automáticamente al grupo:
**En pruebas**, un tester **Invitado**. La revisión automática anterior quedó
resuelta. Consultar `CODEX_HANDOFF.md` antes de retomar.
No regenerar claves ni repetir firma, pago, carga o procesamiento ya completados.

## Compilación protegida en GitHub Actions

Se preparó `.github/workflows/sign-pimflextv-ios.yml`. No usa `pull_request_target`
ni expone credenciales a los trabajos ordinarios de previsualización.
Se activa únicamente al cambiar `pimflextv-ios/SIGNING_REQUEST.json` en la rama
`pimflextv-ios-20261029`. La solicitud existente pide build **6**. El archivo
debe contener un `build_number` entero disponible entre 1 y 9999. El código se recupera por el SHA exacto del evento.

Antes de firmar, un trabajo macOS comprueba núcleo, validadores y Release sin
firma. El trabajo de firma usa el entorno `pimflextv-apple-signing`, una identidad
en llavero temporal y los secretos previstos:
- `PIMFLEX_SIGNING_P12_B64`: PKCS#12 cifrado.
- `PIMFLEX_SIGNING_P12_PASSWORD`: contraseña de recuperación existente.
- `PIMFLEX_PROFILE_B64`: perfil App Store Connect validado.

Juan autorizó y se verificó el entorno **26657933808** con el propietario
`Pinedainsurancegroup` como revisor requerido, sólo la rama exacta
`pimflextv-ios-20261029` permitida y sin omisión de reglas por administradores.
Los tres secretos están configurados. Su uso en macOS para firmar está autorizado;
no volver a solicitar esa autorización. La aprobación del trabajo libera el acceso
a la identidad únicamente a esta ejecución protegida.

El PKCS#12 persistido conserva su cifrado moderno. El importador de Apple rechazó
ese formato; el runner lo convierte a un envoltorio compatible SHA-1/3DES sólo de
forma temporal antes de importar en su llavero efímero. La clave en claro pasa por
memoria y no se escribe en disco. Se conserva el mismo certificado y clave.
La conversión local verificó que ambos coinciden. El identificador UUID se conserva
exactamente como lo emite Apple, sin cambiar mayúsculas/minúsculas. La instalación
del perfil usa la carpeta nueva de Xcode 16 o posterior.

La exportación protegida selecciona Xcode **26.3** e iOS SDK **26.2** en macOS 15.
El preflight verifica Xcode/SDK 26 o posterior y la IPA debe contener DTSDKName de
iOS 26 o posterior. La versión predeterminada Xcode 16.4 del runner no satisface
las cargas actuales de App Store Connect; no usarla para una entrega TestFlight.

El resultado se cifra con AES-256-CBC/PBKDF2 y se autentica con HMAC-SHA256
usando derivaciones separadas de la contraseña privada existente. Sólo se suben
el resultado cifrado y sus metadatos de autenticación, durante un día. Nunca
subir IPA en claro, PKCS#12, contraseña, llavero o perfil como artefactos públicos.
Al terminar se retiran el llavero temporal y los archivos privados del runner.
La entrega se recupera y descifra privadamente con `scripts/signing_artifact.py`.
No se sube a Apple ni se publica automáticamente.

## Preparación de exportación manual

`scripts/archive-signed.sh` prepara un archivo Release y exporta una IPA para
App Store Connect en macOS. Se necesita Xcode 26 o posterior con SDK iOS 26 o posterior, XcodeGen y Python 3, una identidad
Apple Distribution con su clave privada ya instalada en el llavero, y un perfil
App Store Connect válido del App ID. La instalación/custodia de la identidad
debe resolverse de forma privada antes de ejecutar el script.

El script no genera credenciales, no importa llaveros, no inicia sesión y no
solicita actualizaciones automáticas de perfiles. No sube la app a Apple.
Comprueba equipo, App ID explícito, vencimiento, distribución sin depuración,
tipo App Store Connect y correspondencia del certificado antes de compilar.
Después valida la firma de la app exportada, sus entitlements y las familias
iPhone/iPad. La carpeta final contiene únicamente `PimflexTV.ipa` y el informe
`verification.json`, con hash SHA-256, versión y build.

Ejecutar desde una copia de esta rama, con el material privado fuera del código:

```bash
export PIMFLEX_PROFILE_PATH='/ruta/privada/PIMFLEXTV.mobileprovision'
export PIMFLEX_SIGNING_IDENTITY='HUELLA_SHA1_DE_40_CARACTERES_DEL_CERTIFICADO'
export PIMFLEX_EXPORT_DIR='/ruta/privada/nueva-exportacion'
# Opcional: siguiente build disponible en App Store Connect (entero 1–9999).
export PIMFLEX_BUILD_NUMBER='3'
bash pimflextv-ios/scripts/archive-signed.sh
```

La huella se obtiene con `security find-identity -v -p codesigning` en el Mac
que tiene la identidad instalada. No pegar contraseñas o claves en comandos,
chat, commits, issues ni archivos de configuración públicos. El runner autorizado
usa los secretos del entorno protegido descrito arriba.

## Validación y límites

Las pruebas de `scripts/tests/test_signing_profile.py` ejercitan el rechazo de
perfiles de otro equipo/app, caducados, de desarrollo, Ad Hoc, Enterprise y de
otra identidad. Una comprobación conserva la forma exacta del UUID y rechaza formatos no canónicos.
Tres pruebas adicionales comprueban cifrado/recuperación y
rechazo de alteraciones o contraseñas incorrectas en los artefactos. Se pueden ejecutar con:

```bash
cd pimflextv-ios
python3 -m unittest discover -s scripts/tests -p 'test_*.py'
bash -n scripts/archive-signed.sh
```

Los perfiles de prueba son sintéticos; no contienen certificados reales ni
claves. La exportación firmada real terminó correctamente en la ejecución 42533688228,
con 26 pruebas del núcleo y 10 pruebas de firma correctas en el preflight. Una IPA exportada para App Store Connect se instala mediante
TestFlight después de su carga/procesamiento; no es una instalación directa por
descarga. La carga y el procesamiento terminaron; la declaración autorizada y la prueba interna ya están habilitadas; sigue pendiente la prueba física.

Fuentes oficiales:
- https://cryptography.io/en/latest/hazmat/primitives/asymmetric/serialization/
- https://developer.apple.com/documentation/xcode-release-notes/xcode-16-release-notes
- https://developer.apple.com/help/app-store-connect/manage-builds/upload-builds
- https://support.apple.com/en-us/126047
- https://docs.github.com/en/actions/reference/workflows-and-actions/deployments-and-environments
- https://developer.apple.com/help/account/provisioning-profiles/create-an-app-store-provisioning-profile/
- https://help.apple.com/xcode/mac/current/en.lproj/devcac6ab5b3.html
- https://help.apple.com/xcode/mac/current/en.lproj/dev23ea8b877.html
