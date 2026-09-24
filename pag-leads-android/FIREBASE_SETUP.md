# PAG Leads v1.8 — Firebase Cloud Messaging

Estado al 24/09/2026: proyecto Firebase `pag-leads-8c6ef` y app Android registrados; proveedor Google habilitado; SHA-1 y SHA-256 del APK v1.7 estable registrados. Firestore creado en `nam5`, reglas publicadas y probadas localmente y en GitHub Actions. El acceso Google y la configuración pública de Firebase compilaron en GitHub Actions; clave privada estable aún no localizada, inicio de sesión y push real no probados. No instalar en producción. Ver `../firebase/ARCHITECTURE_v1.8.md` y `../firebase/firestore.rules`.

## Objetivo
Mantener Google Forms → Google Sheets privada → Apps Script como sistema de registro y usar Firebase Cloud Messaging únicamente para avisar al teléfono cuando entra un lead nuevo.

## Firebase Console
1. La firma estable se recuperó de un respaldo privado y su certificado coincide con v1.7. Se firmó solo una compilación candidata local; conservar el almacén y contraseñas fuera del repositorio y no distribuirla como STABLE.
2. La configuración Android pública y el ID de cliente web de Credential Manager ya están en `firebase_config.xml`; el `google-services.json` descargado y las credenciales administrativas siguen excluidos del repositorio. Confirmar las restricciones de la clave Firebase en Google Cloud antes de distribución.
3. El código de inicio de sesión está preparado. Iniciar sesión con Juan en una compilación de prueba, cotejar su UID en Firebase Authentication y provisionar su perfil owner por un canal administrativo antes de habilitar lectura.
4. Firestore ya está creado en `nam5` y sus reglas publicadas; las pruebas con identidades sintéticas pasaron en el emulador. Falta la prueba real con el UID de Juan. La región es permanente.
5. Integrar el emisor FCM en el proceso privado existente con credenciales fuera del repositorio. Verificar Cloud Messaging HTTP v1 y autenticar cada registro de dispositivo.

## Apps Script
El código `FirebasePush.gs` es una preparación, no una integración comprobada. No añadir el registro de dispositivos al Apps Script privado hasta validar identidad y suspensión. El fragmento siguiente refleja el diseño anterior y no debe desplegarse sin autenticar usuario/dispositivo:

```javascript
if (body.action === 'registerDevice') {
  return json_(registerFcmDevice_(body));
}
```

Después de completar la validación de identidad y el emisor, instalar el trigger una vez y comprobar que no duplique avisos.

## Privacidad
La notificación push no incluye nombre, teléfono, email ni otros datos personales. Solo avisa que existe un nuevo lead; la app obtiene los datos completos desde la API privada existente.

## Migración
v1.7 permanece estable hasta que v1.8 reciba y muestre un push real. El monitor cada 60 segundos no se elimina antes de la verificación. Después del test puede retirarse en una siguiente compilación o quedar como fallback configurable.
