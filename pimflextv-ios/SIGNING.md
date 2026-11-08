# Firma de PIMFLEX TV para iPhone e iPad

El producto universal usa `com.pimflextv.ios` y el equipo `U47SH3LZM6`.
El App ID está registrado. Juan autorizó la identidad Apple Distribution y la
ficha interna en App Store Connect para TestFlight; no autorizó una publicación
en App Store. La clave cifrada y el CSR existentes están respaldados privadamente.
No generar otra clave al retomar ni incluir material privado en este repositorio.

## Estado verificable

La ficha interna **PIMFLEX TV**, Apple ID **6832365413**, está creada en App
Store Connect (Español México, SKU `PIMFLEXTV-IOS`), sin publicación.
El certificado Apple Distribution **4FQY49J2JC** y el perfil
**PIMFLEX TV App Store 2026** (**92LSL5KN37**) vencen el **8 de noviembre de 2027**.

El propietario adjuntó los dos archivos oficiales. Se comprobó que:
- El certificado, el CSR y la clave privada existente comparten la misma clave pública.
- La firma CMS del perfil es válida y su cadena se verifica contra Apple Root CA,
  con huella SHA-256 contrastada con la lista oficial de Apple.
- El perfil UUID `ED0CBB48-09A0-4031-A16F-DB7C242C3181` corresponde al App ID
  explícito `U47SH3LZM6.com.pimflextv.ios`, al equipo correcto y al certificado
  seleccionado; es App Store Connect, no desarrollo/Ad Hoc/Enterprise.
- Se creó un PKCS#12 cifrado y se verificó su recuperación. La clave no cambió.

La huella SHA-1 de la identidad es `8C2189D902AEA4E06493D80603886E98E1A35BD6`.
El material real y su recuperación se conservan privadamente, fuera del repositorio.
Todavía no hay IPA firmada ni compilación cargada a TestFlight.

## Compilación protegida en GitHub Actions

Se preparó `.github/workflows/sign-pimflextv-ios.yml`. No usa `pull_request_target`
ni expone credenciales a los trabajos ordinarios de previsualización.
Se activa únicamente al cambiar `pimflextv-ios/SIGNING_REQUEST.json` en la rama
`pimflextv-ios-20261029`; ese archivo aún no se ha creado, así que la exportación
no se ha solicitado. El archivo debe contener un `build_number` entero disponible
entre 1 y 9999. El código se recupera por el SHA exacto del evento.

Antes de firmar, un trabajo macOS comprueba núcleo, validadores y Release sin
firma. El trabajo de firma usa el entorno `pimflextv-apple-signing`, una identidad
en llavero temporal y los secretos previstos:
- `PIMFLEX_SIGNING_P12_B64`: PKCS#12 cifrado.
- `PIMFLEX_SIGNING_P12_PASSWORD`: contraseña de recuperación existente.
- `PIMFLEX_PROFILE_B64`: perfil App Store Connect validado.

El entorno vacío se creó con ID **26657933808**. **Su protección y secretos
todavía no están configurados**: la revisión automática bloqueó guardar al
propietario `Pinedainsurancegroup` como revisor por requerir autorización
específica. Antes de cargar secretos se deben guardar/verificar ese revisor,
la restricción a la rama exacta y la desactivación de la omisión de reglas por
administradores. La autorización debe cubrir también el acceso del compilador
macOS a estos tres secretos para firmar PIMFLEX TV.

El resultado se cifra con AES-256-CBC/PBKDF2 y se autentica con HMAC-SHA256
usando derivaciones separadas de la contraseña privada existente. Sólo se suben
el resultado cifrado y sus metadatos de autenticación, durante un día. Nunca
subir IPA en claro, PKCS#12, contraseña, llavero o perfil como artefactos públicos.
Al terminar se retiran el llavero temporal y los archivos privados del runner.
La entrega se recupera y descifra privadamente con `scripts/signing_artifact.py`.
No se sube a Apple ni se publica automáticamente.

## Preparación de exportación manual

`scripts/archive-signed.sh` prepara un archivo Release y exporta una IPA para
App Store Connect en macOS. Se necesita Xcode, XcodeGen y Python 3, una identidad
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
chat, commits, issues ni archivos de configuración públicos. Antes de configurar
un runner de CI con la identidad, acordar el acceso y usar secretos privados
protegidos; no se ha configurado ese acceso en esta tarea.

## Validación y límites

Las pruebas de `scripts/tests/test_signing_profile.py` ejercitan el rechazo de
perfiles de otro equipo/app, caducados, de desarrollo, Ad Hoc, Enterprise y de
otra identidad. Tres pruebas adicionales comprueban cifrado/recuperación y
rechazo de alteraciones o contraseñas incorrectas en los artefactos. Se pueden ejecutar con:

```bash
cd pimflextv-ios
python3 -m unittest discover -s scripts/tests -p 'test_*.py'
bash -n scripts/archive-signed.sh
```

Los perfiles de prueba son sintéticos; no contienen certificados reales ni
claves. La exportación Xcode con firma no se ha ejecutado: falta aprobar y configurar
la custodia y el acceso del runner macOS a los secretos. Una IPA exportada para App Store Connect se instala mediante
TestFlight después de su carga/procesamiento; no es una instalación directa por
descarga. La carga, el procesamiento y la prueba física siguen pendientes.

Fuentes oficiales:
- https://support.apple.com/en-us/126047
- https://docs.github.com/en/actions/reference/workflows-and-actions/deployments-and-environments
- https://developer.apple.com/help/account/provisioning-profiles/create-an-app-store-provisioning-profile/
- https://help.apple.com/xcode/mac/current/en.lproj/devcac6ab5b3.html
- https://help.apple.com/xcode/mac/current/en.lproj/dev23ea8b877.html
