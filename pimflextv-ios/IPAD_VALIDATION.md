# Candidata universal iPhone / iPad 0.3.0 (build 3)

Base de código: `6d690679e7accf4514118579328b300c1b2aacb6`, rama `pimflextv-ios-20261029`, PR #6. La adaptación usa SwiftUI dentro del proyecto existente y no modifica Android, la autenticación productiva ni el motor de reproducción.

## Cambios

- Catálogo con categorías a la izquierda cuando el ancho de la ventana alcanza 900 pt. Al reducir el ancho o usar texto de accesibilidad vuelve al selector compacto. El estado vive fuera de las ramas de presentación.
- Búsqueda y filtro de favoritos compartidos entre ambas disposiciones.
- Cuatro pantallas en horizontal: grilla centrada limitada por la altura disponible, con cabecera medida y video 16:9; en ventanas demasiado pequeñas o texto de accesibilidad se conserva el desplazamiento.
- Carátulas 2:3, con recorte del arte al tamaño del contenedor; columnas según ancho disponible.
- Familias iPhone/iPad, mismo bundle ID, cuatro orientaciones iPad y ventanas redimensionables ya configurados y conservados.
- Datos y ancho de muestra disponibles sólo con `DEBUG` y `--ui-testing`.
- CI: 26 regresiones del núcleo, compilación universal Debug para simulador y Release sin firma, seis pruebas UI existentes y cuatro pruebas iPad en mini y Pro grande. En iPhone se omiten las cuatro exclusivas de iPad.

## Validación completada — 2026-11-08 (California)

Código validado: `2eeeea894d3cdbfad5112914a85ec7949d3101d7`.
Mac CI: https://github.com/Pinedainsurancegroup/Pineda-Insurance-Group/actions/runs/42467076147 — resultado global `success`.

| Comprobación | Resultado |
| --- | --- |
| Núcleo Swift Package | 26 pruebas, 0 fallos |
| Simulador universal Debug | Compilación correcta |
| Dispositivos iPhone/iPad Release, sin firma | Compilación correcta |
| iPhone 16 Pro | 6 pruebas UI, 0 fallos; las 4 exclusivas iPad se omiten |
| iPad mini (A17 Pro) | 10 pruebas UI, 0 fallos |
| iPad Pro 13-inch (M4) | 10 pruebas UI, 0 fallos |

Las pruebas verifican login local, navegación, usuarios guardados, búsqueda/favoritos, episodios, selección y audio exclusivo de pantalla múltiple. Las pruebas iPad añaden conservación de categoría/búsqueda al girar, carátulas 2:3, contenido limitado a 390 pt y controles de las cuatro pantallas visibles en horizontal. Las capturas finales de ambos iPad se exportaron para revisión visual.

La revisión visual de iPad mini y iPad Pro confirmó que las cuatro pantallas y sus controles quedan completos en horizontal y que el dashboard conserva el arte original. La grilla de Cine muestra las categorías a la izquierda y carátulas sin estirar. Los errores de identificadores detectados en la primera ejecución fueron corregidos antes del CI satisfactorio.

La prueba de 390 pt limita el contenido en el simulador: no automatiza Split View/Stage Manager. No hay autenticación ni transmisión real en estas pruebas ficticias. Este entorno Linux no ejecutó Xcode localmente; las compilaciones y pruebas provienen del CI Mac indicado.

Los 62 archivos del núcleo, reproductor individual y recursos se compararon con la base de iPhone y permanecen idénticos. Las clases de reproducción/audio de pantalla múltiple también se preservan; sólo cambia su disposición visual. Android, PAG y Taty no tienen cambios.

Una actualización posterior de este registro modifica sólo Markdown; el SHA ejecutable probado sigue siendo el indicado arriba.

## Distribución Apple — 2026-11-09

La identidad Apple y la firma ya se completaron. La misma IPA universal 0.3.0/build 3
se cargó a la ficha existente y Apple confirmó COMPLETE/VALID. No se recompiló en
esta etapa. El titular aprobó guardar la declaración de cifrado y ese paso se completó.
El grupo interno contiene un tester Invitado y una compilación **En pruebas**.
La instalación mediante TestFlight está habilitada para el titular. Sigue pendiente
probar cuenta, streams y reproducción en dispositivos físicos iPhone/iPad. Consultar `CODEX_HANDOFF.md` para retomar sin repetir estos pasos.
Los pendientes funcionales de `PARITY.md` y la ficha/privacidad para distribución
pública continúan abiertos. No hay publicación en App Store.
