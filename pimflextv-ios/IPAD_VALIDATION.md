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

## Estado de validación

Comprobaciones locales: configuración universal y plist revisados, referencias de assets comprobadas, formato del workflow y cambios de código revisados. Este entorno Linux no dispone de Swift/Xcode. Los resultados Mac del nuevo commit se registrarán después de su ejecución; el CI anterior de iPhone no certifica esta candidata.

La prueba de 390 pt limita el contenido en el simulador: no automatiza Split View/Stage Manager. Rotación y conservación de filtros se comprueban en ambos iPad. No hay transmisión real en las pruebas ficticias.

## Pendiente para instalar y distribuir

Confirmar activación del equipo Apple, generar firma válida, probar cuenta/streams y reproducción en dispositivos físicos iPhone/iPad, completar los pendientes funcionales de `PARITY.md` y preparar TestFlight/App Store. Este cambio no completa esos pasos ni genera un IPA firmado. El pago reportado por el propietario no fue comprobado en esta tarea.
