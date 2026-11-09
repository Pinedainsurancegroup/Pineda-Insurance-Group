# Validación universal iPhone / iPad

## Corrección M3U 0.3.1 / build 4 — 2026-11-09

El propietario confirmó la instalación física de 0.3.0/build 3 en iPad. Su captura mostró una URL M3U HTTP del host exacto `my-vionex.com` y el consentimiento HTTP apagado. La versión anterior sólo admitía `moonspelltools.cc`. La corrección añade el segundo host exacto a la política y a ATS, mantiene el opt-in por cuenta y evita redirecciones entre orígenes o subdominios. No cambia las credenciales del usuario.

Código validado: `b7022c7224962f5fe9dd92bced949b35721d450f`.
[CI de compilación e interfaz 42718460305](https://github.com/Pinedainsurancegroup/Pineda-Insurance-Group/actions/runs/42718460305): `success`.

| Comprobación | Resultado |
| --- | --- |
| Núcleo Swift Package | 28 pruebas, 0 fallos |
| Validadores de firma Python | 10 pruebas, 0 fallos |
| Debug simulador y Release universal sin firma | Correctos |
| iPhone 16 Pro | 7 pruebas UI correctas; 4 exclusivas iPad omitidas |
| iPad mini (A17 Pro) | 11 pruebas UI, 0 fallos |
| iPad Pro 13-inch (M4) | 11 pruebas UI, 0 fallos |
| Regresión M3U HTTP sin/con consentimiento | Correcta en los tres simuladores |

Las pruebas UI usan Xcode 16.4/iOS 18.5 y cuentas ficticias DEBUG. Verifican el aviso antes de consentir y el acceso al dashboard de muestra tras activar el interruptor. No autentican una cuenta real. Las nuevas pruebas del núcleo cubren la conservación de la consulta M3U, normalización del portal, rechazo de hosts parecidos/subdominios y redirecciones entre ambos proveedores, cambio de puerto y downgrade HTTPS.

La [exportación firmada 42718451601](https://github.com/Pinedainsurancegroup/Pineda-Insurance-Group/actions/runs/42718451601) pasó para el mismo SHA con Xcode 26.3/iOS SDK 26.2. Se verificaron HMAC antes de descifrar, SHA-256 de artefacto e IPA, firma reportada por el runner y perfil embebido exacto. IPA SHA-256: `52bd39eccf29c2cbeb4e47310ec1641a3b1476d34f6022ead7d62194f0e63051`.

Distribución de build 4: Apple confirmó carga COMPLETE, procesamiento VALID e IN_BETA_TESTING, sin errores ni advertencias. La API oficial verifica el build exacto en el grupo interno automático del titular; contiene dos builds y un tester. Disponible para actualizar en TestFlight. La instalación del build 3 está confirmada por el propietario; acceso y reproducción con el proveedor real siguen pendientes. No hay pruebas UI en iOS 26 ni prueba automatizada real de Split View/Stage Manager.

## Adaptación 0.3.0 / build 3 (histórico)

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
