# Auditoría de solo lectura — sin conexión a producción

**29-oct-2026 · continuación de PR #8.** `audit.cjs` organiza las lecturas paginadas de una muestra y las entrega al conciliador existente. Se probó únicamente con adaptadores simulados. NO incluye URLs, credenciales, conectores, un servidor de autenticación, escritura, envío de mensajes ni despliegue.

## Qué permite preparar

- Una muestra explícita de 1 a 100 IDs estables; nunca una consulta general por selección vacía.
- Lectura secuencial de estados, correspondencias y proyecciones, con autorización consultada antes de cada página y al finalizar.
- Límites de páginas, registros y tiempo; señal de cancelación para los lectores.
- Detección de cuentas distintas, páginas repetidas, cambio de snapshot y observaciones antiguas o incompletas.
- Informe agregado sin IDs, nombres, teléfonos, correos, notas ni detalles crudos de errores. Las cuentas agregadas también pueden ser información interna: no publicarlas automáticamente.
- Tres resultados: `blocked`, `needs-review` o `ready-for-human-review`. Ninguno autoriza sincronización; `productionApproved`, `writesEnabled` y `messagesEnabled` siempre son `false`.

## Contrato para el ejecutor real

```js
const {runReadOnlyAudit} = require('./audit.cjs');
const result = await runReadOnlyAudit({
  adapter,          // Objeto interno, NO recibido desde el móvil o una petición pública.
  selection,        // Lista autorizada de IDs r_<UUID>, máximo 100.
  expectedScope,    // Identidad de cuenta/ámbito comprobada en el servidor.
  options: {pageSize: 100, maxPages: 10, maxRows: 1000, timeoutMs: 10000}
});
```

El adaptador debe tener exactamente cuatro funciones: `authorize`, `sourceRows`, `links`, `projections`.

`authorize({expectedScope, signal})` debe verificar el acceso REAL y devolver:

```js
{scopeId, active: true, readOnly: true, recruitment: true, expiresAt}
```

`expiresAt` es la expiración en milisegundos UTC. Esos campos NO son una prueba criptográfica de permisos. El módulo confía en un adaptador interno auditado. Una declaración JSON del usuario o `verified=true` no concede ningún acceso. La selección y la autorización deben verificarse en las API reales, no solo después de descargar los datos.

Cada lector recibe `{selection, cursor, limit, signal}` y entrega exactamente:

```js
{items, nextCursor, snapshotId, capturedAt, scopeId}
```

`nextCursor=null` indica que terminó la lectura de esa selección; `snapshotId` y `capturedAt` deben ser estables entre páginas del mismo lector. `capturedAt` usa ISO UTC con milisegundos. Antigüedad máxima: cinco minutos; tolerancia de reloj futuro: cinco segundos. El adaptador no debe inventar un snapshot consistente si el servicio no lo proporciona: implementar una exportación privada coherente o detenerse.

Los elementos normalizados son los del contrato de `preview.cjs`. Los estados contienen solamente `{stableId, status, revision}`. Campos extra se rechazan. No enviar nombres/notas al auditor para luego filtrarlos.

## Garantías y límites

- Se vuelve a comprobar acceso al terminar, pero existe una carrera temporal entre una comprobación y el servicio externo. El servicio REAL debe controlar los permisos de cada lectura.
- Los snapshots de distintos lectores NO constituyen una transacción atómica entre sistemas. El informe lo declara expresamente.
- Una demora provoca cancelación y bloquea lecturas posteriores. El lector debe respetar `AbortSignal`; no se puede deshacer una solicitud ya recibida por un proveedor.
- Los adaptadores son código de confianza. No se ejecuta código, archivos ni direcciones proporcionados por un prospecto. El auditor no puede impedir que un adaptador malicioso haga otras acciones: revisar sus permisos y código antes de conectarlo.
- Fallar una página, alcanzar un límite o no encontrar un ID seleccionado bloquea el informe; no se presenta un lote parcial como completo.
- No se certifican consentimiento, STOP/BAJA, mensajería ni reglas de Firebase mediante estas pruebas. El piloto WhatsApp mantiene su auditoría independiente.

## Pruebas locales verificadas

Node v22.16.0. Reejecución de la base: **58/58**. Con el auditor: **95/95** pruebas, cero fallidas/omitidas; **37 casos nuevos**. Datos y lectores ficticios; no se consultó PAG CRM real.

```bash
node --test pag-leads-bridge/tests/*.test.cjs
```

La ejecución incluye revocación antes/durante/después de lectura, falta de permisos, timeout, respuesta tardía, errores privados, ámbito incorrecto, paginación incompleta, cursor cíclico, datos vencidos, selección incompleta, datos de clientes fuera de alcance y conflictos para revisión humana. La prueba de caducidad usa un reloj simulado; no depende de esperar cinco minutos.

## Criterio siguiente

Inspeccionar el esquema y la revisión ACTUAL de PAG CRM y PAG WhatsApp Receiver. Implementar sus lectores reales con permisos de solo lectura, sin suponer endpoints ni copiar credenciales al chat/repositorio. Probar una muestra autorizada y contrastarla con los sistemas de origen. No activar cuentas, sincronización, mensajes, reglas Firebase o APK por aprobar estas pruebas unitarias.
