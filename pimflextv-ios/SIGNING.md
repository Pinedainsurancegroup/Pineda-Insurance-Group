# Firma de PIMFLEX TV para iPhone e iPad

El producto universal usa `com.pimflextv.ios` y el equipo `U47SH3LZM6`.
El App ID está registrado. Juan autorizó la identidad Apple Distribution y la
ficha interna en App Store Connect para TestFlight; no autorizó una publicación
en App Store. La clave cifrada y el CSR existentes están respaldados privadamente.
No generar otra clave al retomar ni incluir material privado en este repositorio.

## Estado verificable

La emisión del certificado aún no está confirmada. El portal vuelve a mostrar
“Your session has expired” al efectuar la consulta, incluso después del inicio
de sesión informado por el propietario. App Store Connect también muestra
su pantalla de acceso. Una pantalla anterior conservada no acredita una sesión
vigente. Inspeccionar la lista de certificados antes de repetir la emisión.
Si existe un certificado, comparar su clave pública con el CSR guardado.
La ficha de App Store Connect, el perfil y la IPA aún no se han creado.

El CI de `29f2a56ebf0cf14275c4c2dbf695cd6284c4193c` aprobó la configuración
del equipo y la compilación sin firma. Eso no certifica una distribución firmada.

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
otra identidad. Se pueden ejecutar con:

```bash
cd pimflextv-ios
python3 -m unittest discover -s scripts/tests -p 'test_*.py'
bash -n scripts/archive-signed.sh
```

Los perfiles de prueba son sintéticos; no contienen certificados reales ni
claves. La exportación Xcode con firma no se ha ejecutado: faltan el certificado
emitido y el perfil. Una IPA exportada para App Store Connect se instala mediante
TestFlight después de su carga/procesamiento; no es una instalación directa por
descarga. La carga, el procesamiento y la prueba física siguen pendientes.

Fuentes oficiales:
- https://developer.apple.com/help/account/provisioning-profiles/create-an-app-store-provisioning-profile/
- https://help.apple.com/xcode/mac/current/en.lproj/devcac6ab5b3.html
- https://help.apple.com/xcode/mac/current/en.lproj/dev23ea8b877.html
