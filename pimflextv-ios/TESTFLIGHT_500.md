# Candidata TestFlight — PIMFLEX TV 5.0.0 (8)

Esta candidata continúa la app nativa existente en la rama `pimflextv-ios-smarters5-20261110`, separada de la versión estable y de la candidata 0.4.0. El número 5.0.0 identifica esta continuación; no certifica paridad completa con Android Smarters 5.0. Conserva el identificador de la app, equipo de desarrollo, recursos y automatización de firma existentes. **Build 8 es provisional** hasta comprobar su disponibilidad en App Store Connect.

`TESTFLIGHT_CANDIDATE.md` conserva la evidencia histórica de 0.4.0 (7). Sus resultados no validan esta nueva revisión. Para 5.0.0 (8), los scripts exigen un plan nuevo de un checkout limpio del SHA que finalmente se vaya a exportar. No reutilizar planes o exportaciones de 0.4.0.

## Preparación sin firma

Los comandos se ejecutan desde la raíz del repositorio. Las carpetas privadas de ejemplo deben existir fuera del checkout; el plan y la carpeta de exportación deben ser nuevos.

```sh
python3 pimflextv-ios/scripts/testflight_candidate.py prepare \
  --plan /ruta/privada/PIMFLEX-5.0.0-8-plan.json

python3 pimflextv-ios/scripts/testflight_candidate.py export \
  --plan /ruta/privada/PIMFLEX-5.0.0-8-plan.json \
  --export-dir /ruta/privada/PIMFLEX-5.0.0-8-export
```

Sin `--execute`, estas operaciones no firman, no leen credenciales ni acceden a Apple. El plan liga commit, hashes de insumos Release, versión/build y destino de dispositivo. Cambiar el código o el lockfile obliga a preparar otro plan. Los recursos multimedia de prueba DEBUG siguen excluidos de Release y el verificador rechaza una IPA que los contenga.

## Exportación y carga posteriores en Mac

Se requiere Xcode 26 o posterior con SDK iPhoneOS 26 o posterior, XcodeGen, Python 3, Ruby y CocoaPods 1.16.2. La compilación CI de simulador o de dispositivo sin firma no satisface la exportación TestFlight. Para conservar `Gemfile.lock`, instalar las dependencias desde `pimflextv-ios` con `BUNDLE_FROZEN=true bundle _2.5.22_ install` y Ruby 3.3.8; Fastlane está fijado en 2.241.2.

El Mac de firma debe disponer de la identidad **Apple Distribution** existente y su clave privada utilizable en el llavero, junto con el perfil App Store Connect de esta app. Proporcionar privadamente `PIMFLEX_PROFILE_PATH` y `PIMFLEX_SIGNING_IDENTITY`; añadir `--execute` al comando `export` anterior ejecuta el exportador existente y verifica la firma. Los scripts no crean ni importan certificados, no reemplazan perfiles y no modifican credenciales.

Después de obtener una exportación válida:

```sh
python3 pimflextv-ios/scripts/testflight_candidate.py verify \
  --plan /ruta/privada/PIMFLEX-5.0.0-8-plan.json \
  --export-dir /ruta/privada/PIMFLEX-5.0.0-8-export

python3 pimflextv-ios/scripts/testflight_candidate.py upload \
  --plan /ruta/privada/PIMFLEX-5.0.0-8-plan.json \
  --export-dir /ruta/privada/PIMFLEX-5.0.0-8-export
```

`verify` comprueba metadatos, hash y vinculación de la IPA con el plan; no sustituye `codesign` en Mac. `upload` sin `--execute` sólo prepara la operación. La carga efectiva requiere el archivo `.p8` externo existente de App Store Connect mediante `PIMFLEX_ASC_KEY_PATH`, `PIMFLEX_ASC_KEY_ID` y `PIMFLEX_ASC_ISSUER_ID`, y añadir `--execute`. No introducir sus valores en el repositorio o la conversación.

La lane de Fastlane vuelve a verificar la IPA antes de autenticarse. No asigna testers, solicita distribución externa, hace merge ni publica en App Store. `upload-attempt.json` impide reintentos implícitos tras un resultado incierto; comprobar Apple antes de decidir otra carga. La transferencia completada todavía requiere confirmar el procesamiento y la disponibilidad en TestFlight.

El ZIP de fuentes con proyecto Xcode generado es un proyecto para desarrollo. La app de simulador y la compilación Release sin firma no son una IPA instalable. Siguen pendientes la firma/carga efectiva de esta candidata, pruebas físicas iPhone/iPad, proveedor real y funciones pendientes documentadas en `PARITY.md`.
