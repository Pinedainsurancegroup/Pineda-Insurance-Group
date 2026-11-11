# Preparación de TestFlight — 0.4.0 (7)

> Registro histórico de 0.4.0. Para la candidata actual 5.0.0 (8), consultar `V5_VALIDATION.md` y `TESTFLIGHT_500.md`; los scripts de esta rama ya requieren la versión nueva.

La candidata continúa en `pimflextv-ios-controls-20261110`, PR borrador #11, separada de `pimflextv-ios-20261029` y de Android. La automatización de exportación y carga conserva certificados, perfiles, credenciales y el workflow protegido de firma. La continuación del reproductor añade estados de carga de pistas y una prueba local de selección real, por lo que exige validar y preparar un nuevo SHA. No se ha firmado ni enviado esta candidata a Apple.

## Fuente y continuidad

La continuación actual corresponde a `4da1a91abef19ffdd159deaf6adc8ce000a52440`: [CI 42952718270](https://github.com/Pinedainsurancegroup/Pineda-Insurance-Group/actions/runs/42952718270), con 37 core, 23 Python y compilaciones Debug simulador/Release universal sin firma aprobadas. Resultado final **success** con 15 UI iPhone (4 exclusivas iPad omitidas), 19 mini y 19 Pro; un único reintento del trabajo Pro resolvió una lectura de accesibilidad transitoria del MKV existente con código/pruebas idénticos. `PLAYER_VALIDATION.md` registra esa incidencia y las capturas de ambos subtítulos inspeccionadas en los tres destinos. Las pruebas de scripts usan archivos ficticios y no validan una firma o carga efectiva de 0.4.0. La validación de la versión anterior no sustituye la del SHA que se vaya a exportar.

Las fuentes, recursos, pruebas y generadores están versionados. `PimflexTV.xcworkspace` y el proyecto Xcode se generan en Mac con `bash scripts/prepare-ios.sh`; Pods, DerivedData, apps compiladas, IPA, planes privados y llaves no se incorporan al repositorio. Una app de simulador no se convierte en una IPA de dispositivo añadiéndole una firma.

El ZIP Android 4.0.2 se reconstruyó de cinco partes y pasó el CRC de sus 42.465 entradas. Su manifiesto declara 4.0.2/código 102; `REFERENCE_402.md` registra el SHA-256 y la comparación. El mapa detallado y las fuentes descompiladas se conservan internamente. Se mantienen el acceso, las rutas, los identificadores y los favoritos iOS existentes; no se afirma equivalencia completa ni se migra el almacenamiento Android a iOS por inferencia. Cada cambio posterior requiere un plan nuevo del SHA que finalmente se vaya a exportar.

## Qué hace la automatización

`scripts/testflight_candidate.py` ofrece cuatro operaciones. Sin verbo, ejecuta `prepare`.

| Operación | Comportamiento |
| --- | --- |
| `prepare` | Crea un plan privado nuevo, ligado al commit limpio, hashes de insumos, versión 0.4.0, build 7, workspace Release y SDK de dispositivo. No lee llaves ni accede a Apple. |
| `export` | Sin `--execute`, comprueba el plan y prepara la operación. Con `--execute`, exige Mac y reutiliza `scripts/archive-signed.sh` con la identidad instalada y el perfil existente. |
| `verify` | Comprueba metadatos, hash de IPA y vinculación del informe de exportación con el plan. Puede ejecutarse en Linux; no sustituye la comprobación `codesign` realizada por el exportador en Mac. |
| `upload` | Sin `--execute`, verifica la IPA sin acceder a Apple. Con `--execute`, vuelve a verificarla y llama a Fastlane con la clave App Store Connect externa existente. |

Se rechazan otros builds, otra fuente, IPA alteradas, paquetes de simulador, muestras DEBUG en Release y archivos ajenos al control de versiones dentro de las carpetas que el exportador copia. Cambiar fuentes o resolver un lockfile diferente después de preparar el plan exige preparar uno nuevo. Las salidas deben quedar fuera del repositorio y no se sobrescriben exportaciones previas.

## Requisitos del siguiente paso en Mac

- Checkout limpio del SHA candidato que se vaya a exportar, con Git y Python 3.
- Xcode 26 o posterior y SDK iPhoneOS 26 o posterior, XcodeGen, Ruby y CocoaPods 1.16.2. La validación UI histórica con Xcode 16.4 no sustituye este requisito de exportación.
- La identidad **Apple Distribution** existente, con su clave privada utilizable en el llavero, y el perfil App Store Connect correspondiente. Una identidad Apple Development no sirve para TestFlight. Los scripts no crean ni importan identidades.
- Para cargar: Ruby 3.2 o posterior, Bundler y las dependencias de `Gemfile`; Fastlane está fijado en 2.241.2. `Gemfile.lock` se resolvió con Ruby 3.3.8 y Bundler 2.5.22 para Linux y Darwin ARM/Intel; se recomienda ese Ruby/Bundler para conservar el lockfile. La clave API App Store Connect existente se proporciona mediante su archivo `.p8` privado, separado de la identidad que firma.
- Comprobar en App Store Connect que el build 7 sigue disponible antes de exportar. No hay incremento automático ni creación de otra ficha de aplicación.

Instalar las herramientas y las dependencias antes de preparar el plan definitivo. Desde `pimflextv-ios`, usar `BUNDLE_FROZEN=true bundle _2.5.22_ install` para conservar las versiones del lockfile. La carga también usa Bundler en modo frozen. No introducir valores de credenciales en código, documentación, argumentos de commits o conversaciones.

## Comandos preparados

Desde un checkout limpio de la candidata, los dos primeros comandos sólo preparan; las rutas siguientes son ejemplos que deben apuntar a carpetas privadas existentes fuera del repositorio.

```sh
python3 pimflextv-ios/scripts/testflight_candidate.py prepare \
  --plan /ruta/privada/PIMFLEX-0.4.0-7-plan.json

python3 pimflextv-ios/scripts/testflight_candidate.py export \
  --plan /ruta/privada/PIMFLEX-0.4.0-7-plan.json \
  --export-dir /ruta/privada/PIMFLEX-0.4.0-7-export
```

Para la futura exportación efectiva, el Mac recibe `PIMFLEX_PROFILE_PATH` como ruta del perfil existente y `PIMFLEX_SIGNING_IDENTITY` como huella de la identidad instalada. Añadir `--execute` al comando `export` genera una nueva IPA y `verification.json`, sin subirlos a Apple. No se copian llaves al checkout.

```sh
python3 pimflextv-ios/scripts/testflight_candidate.py verify \
  --plan /ruta/privada/PIMFLEX-0.4.0-7-plan.json \
  --export-dir /ruta/privada/PIMFLEX-0.4.0-7-export

python3 pimflextv-ios/scripts/testflight_candidate.py upload \
  --plan /ruta/privada/PIMFLEX-0.4.0-7-plan.json \
  --export-dir /ruta/privada/PIMFLEX-0.4.0-7-export
```

Ese último comando también es sólo preparación. Para la carga efectiva del siguiente paso, configurar privadamente `PIMFLEX_ASC_KEY_PATH`, `PIMFLEX_ASC_KEY_ID` y `PIMFLEX_ASC_ISSUER_ID` con la clave existente, instalar el bundle y añadir `--execute`. La lane `ios upload_verified` vuelve a verificar plan/IPA antes de leer la clave. No asigna testers o grupos, no solicita distribución externa y no publica en App Store. La asignación automática de un grupo existente sigue dependiendo de la configuración de Apple.

`upload-attempt.json` registra cada intento. Un resultado incierto exige comprobar el estado en Apple antes de decidir un reintento; el script no lo repite automáticamente. Una transferencia completada no confirma procesamiento válido ni disponibilidad en TestFlight. Conservar la IPA, los informes y el plan en almacenamiento privado.

## Comprobaciones de esta preparación

En Linux se aprobaron 23 tests Python con archivos ficticios: preparación sin credenciales, fuente modificada, contenido privado ignorado por Git, plataforma/versión/build incorrectos, IPA alterada, vinculación de exportación, exclusión de las tres muestras DEBUG y ausencia de reintentos implícitos. Los ZIP mínimos usados por esos tests no son ejecutables ni están firmados.

La sintaxis de `Gemfile` y `fastlane/Fastfile` se comprobó con Ruby 3.3.8 aislado; Bundler resolvió y analizó el lockfile de 112 specs sin instalar Fastlane. No se ejecutaron Xcode, `codesign`, importación de llaves, Fastlane contra Apple ni carga real. Las pruebas físicas, el proveedor real, la paridad restante y los límites de capturas siguen en `PLAYER_VALIDATION.md` y `PARITY.md`.
