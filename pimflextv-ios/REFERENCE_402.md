# Referencia Android 4.0.2 para la versión iOS

Este documento describe la referencia obtenida de los archivos aportados por el usuario. El análisis fue **estático**: lectura de recursos, Manifest y referencias de layouts en los tres DEX. **No se ejecutó la app Android, no se hicieron solicitudes a sus servicios y no se certifica una reproducción exacta píxel por píxel.** Las pantallas y funciones descritas aquí son evidencia del original, no una declaración de que todas estén implementadas en iOS.

## Archivos de origen

| Archivo | Tamaño en bytes | SHA-256 |
|---|---:|---|
| `Pim Flex TV(4.0.2).apk` | 98,935,063 | `c1fa614b2e2aec9399bbde9ca91491b8a4f03e010bd47a4074e57d7b0f6f6a36` |
| `Pim Flex TV(4.0.2).aab` | 120,710,426 | `852be7a751dfb44264deccb2f85aa0b2a2375f7d1146ca1a71d5d4d410ef6fe9` |

Paquete: `com.pimflextv.pimflextviptvbox`. La interfaz utiliza actividades y XML nativos de Android. El AAB conserva los nombres originales de recursos, mientras que el APK ofusca muchos nombres de archivo. Los APK/AAB, los DEX y los volcados XML de la auditoría no forman parte de este repositorio.

## Selección del tema que contiene el binario

`LoginActivity.onCreate` selecciona `login_new` en teléfono y `login_new_tv` para el tipo de pantalla `TV`.

`NewDashboardActivity.onCreate` distingue cuentas Stalker, la bandera `u`, el tipo de pantalla y la bandera `m`. El inicializador `Ldh/a.<clinit>` asigna **`u=false` y `m=false`**; la búsqueda de escrituras a esos campos en los tres DEX sólo encontró dichas asignaciones. Para una cuenta normal de teléfono, esa combinación selecciona **`new_dashboard_layout_without_freetrail_cl`**. La variante TV es `new_dashboard_layout_without_freetrail_tv_cl`; las cuentas Stalker tienen layouts propios.

El tema `_cl` usa tarjetas raster azules. Los gradientes verde/azul, naranja/rosa y azul/morado pertenecen a los layouts clásicos que también se incluyen en el paquete. Su presencia no demuestra que sean el dashboard seleccionado por esta versión.

También se verificaron por SHA-256 estas correspondencias:

| Archivo ofuscado del APK | Nombre original en el AAB | Evidencia de uso |
|---|---|---|
| `res/1CT.jpg` | `login_new_bg.jpg` | Fondo púrpura; no se encontró referencia XML ni constante de recurso en los tres DEX. |
| `res/xbj.png` | `curved_focused_box.png` | Estado de foco en RoutingActivity y mantenimiento; no es la tarjeta principal del dashboard. |
| `res/VXc.png` | `list_focusedgrade.png` | Estado de foco en RoutingActivity. |
| `res/Dks.png` | `iptv_smarters_white_large.png` | No se encontró referencia XML ni constante de recurso en los tres DEX. |
| `res/DQz.png` | `logo_dark.png` | Marca PT turquesa/morada con nombre negro, 800×312. |

La ausencia de una referencia estática no prueba por sí sola la imposibilidad de un uso dinámico. La implementación visual se basa en los layouts cuya selección sí está documentada.

## Login original

- Fondo `login_bg.jpg` (1920×1080), azul/cian poligonal; panel `login_box.png` (827×941), azul marino; marca `logo.png` (480×153); botón `login_button.png` (447×85).
- El panel horizontal ocupa aproximadamente la mitad del ancho. El XML define pesos `.26`, `.49` y `.28` para espacio izquierdo, panel y espacio derecho, además de margen de panel `10sdp`.
- Contenedores de nombre de lista (`rl_name`), usuario (`rl_email`) y contraseña (`rl_password`), más un control para mostrar u ocultar la contraseña. Los EditText se construyen en `LoginActivity.M1`.
- Ese método usa `anyname.png`, `email.png`, `pa.png` y `newselector_login_fields`, cuyo estado normal/con foco escoge `login_field.png` / `login_field_focused.png`.
- El contenedor de URL del servidor existe como `rl_server_url`, pero está **oculto en el XML**. Mostrar configuración del servidor en iOS debe describirse como adaptación.
- Título: 20sp, negrita, blanco, `sans-serif`. Botón principal: 18sp, negrita, mayúsculas. Existe el acceso a la lista de usuarios. VPN y otros controles tienen estados de visibilidad condicionados.

## Dashboard `_cl`

El Manifest declara `sensorLandscape` para SplashActivity, LoginActivity y NewDashboardActivity. La referencia principal es horizontal; una disposición vertical de iPhone es una adaptación.

| Parte | Recurso o disposición original |
|---|---|
| Fondo | `black_background.jpg`, 1920×1080, visualmente azul marino. |
| Barra lateral izquierda | Peso `.14` del ancho; contenido derecho `.83`. |
| Cabecera / área principal / pie | Pesos 24 / 64 / 12 dentro del contenido derecho. |
| Cabecera | `logo_white.png`, 60dp de alto en el layout horizontal; hora, fecha y búsqueda. |
| Tarjetas principales | `live_tv.png`, `movies.png`, `series.png`, cada una 509×451; tres columnas con igual peso `.45` y separación `15sdp`. |
| Títulos de tarjetas | 20sp, negrita, blanco; dibujados por separado del bitmap. |
| Accesos inferiores | `catchup.png`, `multiscreen.png`, `live_with_epg.png`, cada uno 515×208; etiquetas de 12sp en negrita. |
| Cuenta / ajustes / usuarios | `user.png`, `settings.png`, `list_user.png`; vistas de 40×38dp con padding de 10dp. |

Las tarjetas principales **ya contienen el icono y el aro decorativo**. Superponer otro icono equivalente lo duplicaría. El orden XML de los accesos inferiores, de izquierda a derecha, es grabación oculta, CATCH UP, PANTALLA MULTIPLE y EPG. La barra lateral también contiene controles de VPN, radio, descargas, actualización, notificaciones, grabación y guía deportiva cuya disponibilidad depende del estado o la configuración. Las etiquetas laterales están normalmente ocultas en XML.

### Textos españoles del paquete

| Clave | Texto |
|---|---|
| `credential_detail` | DETALLES DE ACCESO |
| `login_user` | Iniciar sesión |
| `list_users` | Lista de Usuarios |
| `live_tv` | TV EN DIRECTO |
| `on_demand` | CINE |
| `series` / `series1` | SERIES |
| `epg_live` | EPG |
| `multiscreen` | PANTALLA MULTIPLE |
| `catch_up` | CATCH UP |
| `master_search` | Búsqueda maestra |
| `menu_settings` | Ajustes |
| `menu_account_info` | Mi Información |

## Marca y fuentes

El Manifest usa `@mipmap/ic_launcher`: fondo blanco, PT turquesa/morada y nombre negro. Su mayor bitmap es 192×192. `base/res/drawable/logo_dark.png` (800×312) permite conservar el arte original al componer un icono iOS de mayor tamaño sobre blanco. El cambio de tamaño y la composición del icono son transformaciones para iOS, no una nueva marca.

Las tablas de nombres de los TTF identifican estas fuentes extraídas de los archivos aportados:

| Miembro del AAB | Familia y estilo | Nombre PostScript |
|---|---|---|
| `base/assets/fonts/open_sans.ttf` | Open Sans Bold | `OpenSans-Bold` |
| `base/assets/fonts/open_sans_regular.ttf` | Open Sans Regular | `OpenSans` |
| `base/res/font/roboto_medium_numbers.ttf` | Roboto Medium, subconjunto numérico | `Roboto-Medium` |

La presencia de estas fuentes no demuestra que todas las vistas las utilicen; el título del login declara `sans-serif`. Esta auditoría registra su procedencia y sus metadatos, **sin afirmar que los archivos aportados incluyan una licencia de redistribución** ni atribuirles una licencia que no se haya verificado.

## Qué se reproduce mediante código y qué necesita servicios

La composición de pantallas, navegación local, recursos de marca, colores, tamaños, estados de foco, textos, campos de acceso y controles del reproductor pueden implementarse como interfaz iOS a partir de esta evidencia. Los dp/sp/sdp de Android son referencias de diseño; su adaptación a puntos de iOS y a tamaños de pantalla distintos necesita revisión visual.

La autenticación real, cuentas y vencimientos, catálogo de canales/películas/series, búsquedas sobre ese catálogo, EPG, URLs de reproducción, catch-up y disponibilidad del contenido requieren respuestas válidas del servicio configurado. Notificaciones, grabación/descargas, VPN y reproducción simultánea también requieren implementaciones e integraciones específicas de iOS; dibujar sus accesos no demuestra que funcionen. Los archivos Android no constituyen una copia de los servidores ni una autorización para sus cuentas.

Para declarar paridad visual o funcional falta comparar ejecuciones reales con datos autorizados, incluida la reproducción en un iPhone. Este documento no certifica esas comprobaciones.
