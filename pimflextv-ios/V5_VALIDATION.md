# Validación de la candidata PIMFLEX TV 5.0.0 (8)

## Continuidad

Base: `f7f3cb43b5c287ee776f39f751e1a138f690ea80`, candidata 0.4.0. Nueva rama: `pimflextv-ios-smarters5-20261110`. La estable y PR #6, y la candidata anterior del PR #11, se conservan. La referencia Android nueva es un paquete compilado 5.0/código 108; `REFERENCE_500.md` registra su procedencia y límites. El cambio de numeración iOS no acredita equivalencia con todas las funciones de Smarters.

## Cambios acotados

- Actualización de grupos de audio, subtítulos y variantes HLS al abrir el selector nativo, preservando Automático, Desactivados y opciones manuales válidas. Resultados cancelados o de un item anterior no se aplican. Un límite de calidad que deja de estar disponible vuelve a Automático para evitar una preferencia oculta.
- Se conserva el temporizador de cuatro segundos y sus excepciones de interacción/accesibilidad documentadas en `PLAYER_VALIDATION.md`. Nueva prueba con MP4 real, sin el argumento DEBUG que mantiene controles visibles, para verificar ocultación de cabecera, pausa y progreso mientras continúa la reproducción.
- Versión 5.0.0/build 8 y automatización TestFlight coherente. Se conserva el producto Apple y el proceso de firma existente.
- Artefacto de proyecto Xcode separado del ZIP de simulador, para descargar las fuentes generadas sin incluir una aplicación incompatible con dispositivos.

## Comprobaciones de esta revisión

Código: `76cff20fdfac694a9bbe2b49c20760d0fc862f41`. [PR borrador #12](https://github.com/Pinedainsurancegroup/Pineda-Insurance-Group/pull/12). [Mac CI 42984142698](https://github.com/Pinedainsurancegroup/Pineda-Insurance-Group/actions/runs/42984142698), Xcode 16.4 y SDK/simuladores iOS/iPadOS 18.5. Resultado final **success**, intento 2. Sólo se repitió el trabajo iPhone con el mismo código y las mismas aserciones; los resultados de build, mini y Pro se conservan del primer intento.

| Comprobación | Resultado |
| --- | --- |
| Núcleo Swift | 37 aprobadas, cero fallos |
| Python de exportación | 23 aprobadas |
| Sintaxis Bash/Ruby/Gemfile/Fastlane | Aprobada en Mac |
| Debug universal, simulador | Compilación aprobada |
| Release universal, iPhone/iPad | Compilación sin firma aprobada |
| UI iPhone 16 Pro | 16 aprobadas, 4 exclusivas iPad omitidas, cero fallos en el reintento |
| UI iPad mini (A17 Pro) | 20 aprobadas, cero fallos, primer intento |
| UI iPad Pro 13-inch (M4) | 20 aprobadas, cero fallos, primer intento |

Los tres destinos aprueban la prueba real de MP4 que comprueba ocho elementos visibles, ocultación por inactividad, avance del reloj real mientras están ocultos y recuperación mediante un toque. Aprueban asimismo los grupos reales de audio/subtítulos, ambos idiomas y reapertura conservando selección manual, Automático y Desactivados. Se mantiene el parser estricto del reloj; no se sustituyen lecturas ausentes por cero.

El primer intento iPhone encontró una lectura de accesibilidad sin valor en `CompatiblePlaybackTests.swift:26`, tras reconocer la pausa del MKV existente. Las comprobaciones posteriores de búsqueda, reanudación, audio, cierre y reapertura no registraron fallos. Los siete tests de `PlayerControlsTests`, incluidos los dos cambios de esta candidata, aprobaron. El archivo de prueba MKV y su motor no cambian respecto a la candidata anterior. El único reintento iPhone aprobó el MKV y toda su suite sin alterar el código ni debilitar las aserciones. Se conserva el resultado inicial y el síntoma de lectura transitoria; no se atribuye una ejecución inicial sin fallos a iPhone.

Se inspeccionaron las nueve capturas de esta ejecución: tres iPhone del intento 2 y tres por cada iPad del intento 1, con controles completamente ocultos y subtítulos español/inglés visibles. Estas imágenes son de medios locales propios, sin proveedor. La muestra MP4 de ocultación es un remux del fixture anterior y conserva su rótulo visual «Prueba MKV»; el caso usa AVPlayer y el archivo MP4, no VLC.

Los 23 tests Python también pasaron localmente, junto a sintaxis Bash y diff. Ruby no estaba instalado en Linux; su comprobación se ejecutó en Mac CI. Los 60 recursos de la rama estable coinciden byte por byte; todos los recursos, núcleo, AppModel, Info.plist y solicitud de firma de la candidata 0.4.0 permanecen intactos. El entorno local no tiene Xcode.

## Descarga y continuidad

El [artefacto del proyecto Xcode generado](https://github.com/Pinedainsurancegroup/Pineda-Insurance-Group/actions/runs/42984142698/artifacts/13838369088) corresponde a `76cff20`. El ZIP interior `PIMFLEXTV-iOS-Source.zip` tiene SHA-256 `b75e7e631a068d6eb49cbbc233f6127dd7561fad7dadaf24df745abe8c900c52`: 116 archivos fuente/recursos coinciden con el checkout y el proyecto generado declara 5.0.0/build 8. El ZIP exterior del artefacto tiene SHA-256 `b5332b84de85c64bd719ec50fe1d793fbe4c3fb167afb3615731e0acc443d77e`. CRC de ambos correcto. Dentro de SourcePackage, ejecutar `bash scripts/prepare-ios.sh` en Mac y abrir `PimflexTV.xcworkspace` para resolver la dependencia VLC.

El artefacto conserva los documentos del commit compilado; este cierre posterior sólo cambia Markdown y no altera los insumos de compilación. La rama Android paralela `pimflextv-android-smarters5-reference-20261110`, commit `1dd9f6561b6947a4eb286d88e2b19ff7c8289c59`, contiene únicamente el vínculo y la referencia saneada, sin reconstruir ni sustituir Android. Las dos ramas quedan respaldadas en el mismo repositorio.

`prepare` y `export` sin `--execute` pasan con un plan privado del commit limpio `76cff20`; no acceden a Apple ni a credenciales. Si se exporta el commit de cierre documental, generar un plan nuevo de ese SHA limpio. El parche de esta continuación parte de `f7f3cb4` y se comprueba aplicándolo en un índice aislado hasta obtener el mismo árbol Git.

## Límites

Las pruebas usan catálogos ficticios y medios locales propios. No demuestran cuenta/proveedor real, audibilidad física, adaptación HLS multivariante, AirPlay o equivalencia visual completa con Android 5.0. No se ejecutó la APK Android. Los recursos PIMFLEX, núcleo de acceso/catálogos/favoritos, política HTTP/TLS y credenciales se preservan.

La candidata todavía no tiene firma/exportación/carga Apple. `TESTFLIGHT_500.md` prepara ese paso con las identidades existentes, sin recrearlas; el build 8 requiere comprobar disponibilidad. No fusionar ramas ni publicar en App Store. Funciones pendientes en `PARITY.md`.
