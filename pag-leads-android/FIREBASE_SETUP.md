# PAG Leads v1.8 — Firebase Cloud Messaging

Estado: código preparado en rama `pag-leads-v1.8-fcm`. No instalar en producción hasta completar Firebase y validar un push real.

## Objetivo
Mantener Google Forms → Google Sheets privada → Apps Script como sistema de registro y usar Firebase Cloud Messaging únicamente para avisar al teléfono cuando entra un lead nuevo.

## Firebase Console
1. Crear proyecto: `PAG Leads`.
2. Registrar Android app con package `com.pinedaagencygroup.leads`.
3. Tomar del proyecto los valores públicos: Project ID, Android App ID, Web API Key y Sender ID/Project Number.
4. Colocarlos en `app/src/main/res/values/firebase_config.xml`.
5. En Settings → Service accounts, generar una clave JSON exclusiva para el envío FCM.
6. Guardar el JSON únicamente en Script Properties del proyecto Apps Script como `FCM_SERVICE_ACCOUNT_JSON`. Nunca subirlo a GitHub.
7. Confirmar que Firebase Cloud Messaging API (HTTP v1) esté habilitada.

## Apps Script
Integrar `FirebasePush.gs` en el proyecto privado actual y añadir en `doPost`, después de validar API_TOKEN:

```javascript
if (body.action === 'registerDevice') {
  return json_(registerFcmDevice_(body));
}
```

Luego ejecutar una sola vez `setupFirebasePushTriggerOnce()` para crear el trigger de nuevas respuestas.

## Privacidad
La notificación push no incluye nombre, teléfono, email ni otros datos personales. Solo avisa que existe un nuevo lead; la app obtiene los datos completos desde la API privada existente.

## Migración
v1.7 permanece estable hasta que v1.8 reciba y muestre un push real. El monitor cada 60 segundos no se elimina antes de la verificación. Después del test puede retirarse en una siguiente compilación o quedar como fallback configurable.
