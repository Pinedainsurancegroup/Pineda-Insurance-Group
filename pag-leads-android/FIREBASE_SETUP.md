# PAG Leads v1.8 — Firebase Cloud Messaging

Estado al 24/09/2026: proyecto Firebase `pag-leads-8c6ef`, Auth Google y Firestore `nam5` configurados. La firma estable está recuperada fuera de GitHub y coincide con v1.7. Juan inició sesión y pasó el control owner en la QA separada; todavía faltan la conexión privada de leads, el registro FCM y un push real. No instalar sobre la v1.7 estable. Ver `../firebase/ARCHITECTURE_v1.8.md` y `../firebase/firestore.rules`.

## Objetivo
Mantener Google Forms → Google Sheets privada → Apps Script como sistema de registro y usar Firebase Cloud Messaging únicamente para avisar al teléfono cuando entra un lead nuevo.

## Firebase Console
1. La firma estable se recuperó de un respaldo privado y su certificado coincide con v1.7. Se firmó solo una compilación candidata local; conservar el almacén y contraseñas fuera del repositorio y no distribuirla como STABLE.
2. La configuración Android pública y el ID de cliente web de Credential Manager ya están en `firebase_config.xml`; el `google-services.json` descargado y las credenciales administrativas siguen excluidos del repositorio. Confirmar las restricciones de la clave Firebase en Google Cloud antes de distribución.
3. El perfil owner de Juan se provisionó mediante Firebase Console y la QA verificó su acceso. No crear agentes ni líderes todavía.
4. Las reglas actualmente publicadas pasaron pruebas sintéticas de aislamiento; la ruta nueva `deviceRequests` necesita prueba y publicación. Una solicitud de dispositivo no equivale a autorización de envío.
5. Integrar un emisor FCM de confianza con credenciales fuera del repositorio. El emisor debe comprobar usuario activo, dispositivo autorizado y payload genérico antes de enviar. Probar Cloud Messaging HTTP v1 de extremo a extremo.

## Apps Script
El código `FirebasePush.gs` es una preparación, no una integración comprobada. No añadir el registro de dispositivos al Apps Script privado hasta validar identidad y suspensión. El fragmento siguiente refleja el diseño anterior y no debe desplegarse sin autenticar usuario/dispositivo. La QA solicitará el registro en `users/{uid}/deviceRequests/{deviceId}`, sin enviar el token antiguo de Apps Script:

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
