# PAG Leads v1.8 — Firebase Cloud Messaging

Estado al 24/09/2026: proyecto Firebase `pag-leads-8c6ef` y app Android registrados; proveedor Google habilitado. Firestore no creado, reglas no desplegadas, SHA-1 estable no registrado y push real no probado. No instalar en producción. Ver `../firebase/ARCHITECTURE_v1.8.md` y `../firebase/firestore.rules`.

## Objetivo
Mantener Google Forms → Google Sheets privada → Apps Script como sistema de registro y usar Firebase Cloud Messaging únicamente para avisar al teléfono cuando entra un lead nuevo.

## Firebase Console
1. Registrar la SHA-1 del certificado de firma estable de PAG (y la SHA-256 si corresponde) sin publicar el almacén de claves.
2. Descargar la configuración Android actualizada tras habilitar Google. Completar los valores públicos de `firebase_config.xml` y el ID del cliente web requerido por Credential Manager. Nunca añadir claves administrativas al repositorio.
3. Completar inicio de sesión, verificar UID de Juan y provisionar su perfil owner en un canal administrativo antes de habilitar lectura.
4. Crear Firestore en la ubicación aprobada, desplegar y probar las reglas. La región es permanente.
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
