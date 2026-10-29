# PAG Leads ↔ PAG CRM — conciliación previa, sin despliegue

**29-oct-2026 · PR #8 · trabajo aislado.** Este módulo NO conecta cuentas, NO lee Firestore/Sheets, NO escribe en PAG CRM y NO envía mensajes. Conserva la app STABLE, el desarrollo QA y los sistemas de producción existentes.

## Qué se implementó

- `bridge.cjs`: proyección mínima de estado, identificador y revisión; validación estricta de datos persistidos; comparación de nuevo, posterior, repetido, obsoleto y conflicto.
- `preview.cjs`: conciliación offline de hasta 1.000 filas, con correspondencias explícitas y revisión de ambigüedades. Produce propuestas, nunca escrituras.
- `tests/`: seis pruebas originales más 52 pruebas adicionales; datos exclusivamente sintéticos.
- `VERIFICATION.md`: entorno, evidencia y límites de las pruebas.

```bash
node --test pag-leads-bridge/tests/*.test.cjs
node --test --experimental-test-coverage pag-leads-bridge/tests/*.test.cjs
```

## Autoridad de cada dato: no migrar ni duplicar a ciegas

La fuente privada Forms → Sheets → Apps Script conserva los datos originales de reclutamiento. Firestore conserva estados/notas/revisiones e historial. PAG CRM conserva conversaciones y tareas según su esquema vivo, que todavía debe inspeccionarse. La app y el puente NO deben inventar una nueva fuente maestra ni sobrescribir notas.

El identificador de origen es `r_<UUID>`: nunca el índice histórico de una fila. Se requiere una correspondencia comprobada con el identificador del CRM. No se enlazan personas automáticamente por nombre, teléfono compartido o suposición.

`Completado` se conserva como estado del sistema de origen: NO demuestra contratación, producción, licencia verificada ni consentimiento para contactar.

## Contrato de vista previa (no describe una API existente)

```js
const { createReconciliationPreview } = require('./preview.cjs');
const result = createReconciliationPreview({
  sourceRows: [],   // { stableId, status, revision }; se omiten otros campos
  links: [],        // { sourceLeadId, crmContactId, module, verified, enabled }
  projections: []   // { crmContactId, snapshot } previamente validado
});
```

- `module` admite solo `recruitment`; el flujo de clientes Final Expense queda separado.
- `verified`/`enabled` son afirmaciones del adaptador: NO autentican al usuario ni conceden permisos. Un futuro servidor debe obtenerlas de su registro protegido, nunca confiar en lo que declare el teléfono o un archivo del usuario.
- No se crea un contacto si falta el enlace; se devuelve `unlinked` para revisión.
- Las correspondencias múltiples, registros repetidos y reasignaciones inconsistentes se bloquean en la vista previa.
- Un registro de correspondencias o proyecciones mal formado detiene el lote completo. Una fila de origen inválida se marca sin copiar su contenido a los errores.
- `candidate-new` y `candidate-newer` son propuestas de proyección, NO acciones autorizadas. No hay ejecutor de escrituras en este módulo.
- El resultado fija `mode=preview`, `writesEnabled=false` y `messagesEnabled=false`. No acepta una opción para activarlos.

## Privacidad y seguridad

No se copian nombres, teléfonos, correos, notas ni datos de salud a la salida. **Los identificadores y estados siguen siendo datos vinculables; no son anónimos ni aptos para publicación.** Los ejemplos del repositorio público son ficticios. Los datos reales requieren autorización, almacenamiento privado y registros limitados.

La clave SHA-256 de idempotencia depende de esquema, ID y revisión. Detecta inconsistencias; NO es una firma, un secreto ni prueba de autenticidad. El mismo ID/revisión con estado diferente produce un conflicto, no otro evento autorizado.

Este módulo no verifica identidad Firebase, permisos Owner/agente, consentimiento, STOP/BAJA, firmas de webhooks ni ventanas de mensajería. Esos controles pertenecen a servicios que aún deben auditarse. No sustituirlos por instrucciones del modelo.

## Pasos siguientes, sobre lo existente

1. Inspeccionar la revisión y el esquema realmente desplegados de PAG CRM y PAG Receiver; preservar cambios recientes.
2. Verificar una ruta de lectura autenticada y su alcance mínimo, sin copiar secretos al chat ni al repositorio.
3. Definir cómo el adaptador obtiene estados y enlaces del servidor. Este contrato normalizado NO implica que exista un endpoint compatible.
4. Ejecutar una prueba de solo lectura con muestra autorizada; comparar manualmente identidad, estado y revisión.
5. Diseñar persistencia transaccional, conflictos concurrentes, reintentos, auditoría y reversión ANTES de cualquier escritura.
6. Mantener el piloto WhatsApp independiente: un único respondedor, baja, pausa humana y evidencia de entrega. El puente no habilita ese piloto.

No cambiar APK, reglas Firebase, Forms/Sheets, Apps Scripts, roles, notificaciones, secretos, Meta ni LeadConnector desde esta etapa. No usar TinyFish ni contratar plataformas. La sincronización bidireccional y la producción siguen sin aprobarse mediante estas pruebas.
