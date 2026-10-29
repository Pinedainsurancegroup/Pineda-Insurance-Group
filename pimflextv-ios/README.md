# PIMFLEX TV para iPhone — 0.1.0, candidata técnica

Port nativo SwiftUI/AVKit independiente de Android. No convierte los binarios APK/AAB en una aplicación iOS. El código Android y la versión estable 3.1.0 permanecen sin cambios.

## Qué incluye el código

- Acceso Xtream por servidor HTTPS, usuario y contraseña; validación de cuenta activa.
- Lista M3U por URL HTTPS, enlaces relativos y detección de manifiestos HLS.
- TV en vivo, películas, categorías, búsqueda y favoritos por cuenta.
- Series con temporadas y episodios ordenados numéricamente.
- Guía corta del proveedor Xtream; horas convertidas a la zona del dispositivo.
- AVPlayer/AVPlayerViewController con controles nativos, audio/subtítulos del medio y salida externa cuando el medio/dispositivo lo permitan.
- Reanudación de VOD; historial local por cuenta. Credenciales y URL de lista en Keychain.
- Logo aprobado reutilizado desde el código propio Android.
- Cancelación, reintentos, errores sin URLs/contraseñas, límite de respuestas de 32 MiB, sin caché persistente de respuestas ni cookies.

## Compilar

Requiere un Mac con Xcode, herramientas de línea de comandos y XcodeGen.

```sh
cd pimflextv-ios
swift test
brew install xcodegen
xcodegen generate
open PimflexTV.xcodeproj
```

Elegir el esquema `PimflexTV`. Para simulador no hace falta firma de distribución. Para un iPhone, seleccionar el equipo Apple del propietario en Signing & Capabilities y resolver el identificador `com.pimflextv.ios` con ese equipo antes de instalar.

La tarea `.github/workflows/build-pimflextv-ios.yml` ejecuta tests de núcleo, compila para simulador y dispositivo (sin firma), y ejecuta una prueba UI de acceso. Produce un `.app` de simulador y el proyecto fuente generado. **Ninguno es un instalador para iPhone.** No se genera un IPA simulado ni se publica una versión automáticamente.

## Puerta de salida a TestFlight

1. Confirmar el resultado de CI y probar cuenta/servidor reales en un iPhone.
2. Adaptar las transmisiones y funciones marcadas pendientes en `PARITY.md`.
3. Configurar equipo Apple Developer, identificador, firma y registro App Store Connect del propietario.
4. Añadir icono de distribución, política de privacidad pública, contacto de soporte y ficha; revisar declaraciones de privacidad y cifrado con los servicios realmente utilizados. El manifiesto actual declara únicamente UserDefaults propios, sin analítica de la app. El proveedor recibe las solicitudes de cuenta y reproducción.
5. Archive, validación y distribución mediante TestFlight. La aprobación de Apple no está garantizada por compilar.

No hay cuentas, claves de firma, contraseñas ni canales precargados. Los tests solo usan dominios `example.com` y datos ficticios. No enviar credenciales por comentarios del repositorio público.

## Estado verificable

Fecha inicial: 29 de octubre de 2026. Consultar la ejecución de CI asociada al commit, no asumir éxito a partir de este archivo. Hasta probar una cuenta real y un iPhone, la reproducción de ese proveedor es **no verificada**. Esta candidata no tiene equivalencia completa con la referencia 4.0.2.

El propietario autorizó publicar el código iOS y su configuración de pruebas en este repositorio público. Consultar los resultados de CI del commit actual; no confundir un proyecto fuente con un instalador firmado para iPhone.

Fuentes de implementación: https://developer.apple.com/documentation/avfoundation/using-avfoundation-to-play-and-persist-http-live-streams ; https://developer.apple.com/documentation/xcode/distributing-your-app-for-beta-testing-and-releases ; https://yonaskolb.github.io/XcodeGen/Docs/ProjectSpec.html
