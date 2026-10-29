# PAG Leads ↔ PAG CRM — Etapa 0 de integración segura

**Estado (29-oct-2026):** prototipo de contrato y pruebas **sin despliegue**. Este módulo NO conecta a PAG CRM, NO lee Google Sheets/Firestore y NO envía mensajes. Se construye en una rama de trabajo separada para proteger la APK **PAG Leads v1.8 STABLE**.

## Arquitectura que se preserva

- **PAG Leads:** la fuente privada Google Forms → Sheets → Apps Script sigue siendo la autoridad de los datos originales de *reclutamiento*; el identificador estable es `r_<UUID>` (nunca el antiguo índice `PAG-A-*`).
- **Firestore:** `recruitmentState/{stableId}` conserva estados, notas, revisiones e historial, con reglas actuales. La rama `pag-leads-v1.9-agents` contiene trabajo de permisos y asignaciones **QA no desplegadas**, que tampoco se modifica en producción.
- **PAG CRM:** conservará su propio historial de conversaciones WhatsApp, identificación de contacto y tareas; aún falta revisar su esquema vivo y los permisos del servicio antes de conectar los dos sistemas.
- **Puente:** sincronizará información mínima mediante un ejecutor autenticado, con correlación verificada y registro de idempotencia. El teléfono móvil no recibirá claves privadas de PAG CRM.

## Primer avance de código

`bridge.cjs` crea una proyección **solamente de estado operacional no PII**: `schema`, `source`, `sourceLeadId`, `sourceRevision`, `status` e `idempotencyKey`. Valida IDs estables, estados y revisiones. Compara versiones y rechaza eventos obsoletos, conflictos de misma revisión o identidades diferentes. No incluye nombres, teléfonos, correos, notas ni asignaciones, aunque alguien los envíe como campos adicionales.

Ejecutar pruebas locales:

```bash
node --test pag-leads-bridge/tests/bridge.test.cjs
```

## Pasos posteriores antes de conectar datos reales

1. **Auditar el PAG CRM existente** (modelo de contactos, eventos, permisos, endpoints internos, revisiones y cambios posteriores al 27-oct). No crear otro CRM ni asumir que una API privada está disponible.
2. Definir un identificador de correspondencia `stableId ↔ crmContactId` comprobado **en servidor**. Nunca deduplicar por nombre o confiar en un índice de fila. Los datos personales originales solo podrán consultarse por una ruta protegida, bajo permisos y consentimiento correspondientes.
3. Crear adaptador **read-only** para consultar primero una muestra sintética y luego una muestra autorizada, sin cambios en estado, permisos, contactos ni envíos.
4. Después del visto bueno, diseñar una cola idempotente de actualizaciones mínimas con conflictos explícitos, auditoría y reversión. No habilitar sincronización bidireccional hasta definir qué sistema manda para cada campo.
5. Separar estrictamente *reclutamiento* de *clientes Final Expense*. No importar clientes reales ni activar cuentas de agentes como parte de este puente.
6. Verificar Firebase owner/agent permissions, respaldo recuperable y notificaciones FCM sin datos personales. Mantener `v1.8 STABLE` y la rama `v1.9` actuales sin desplegar cambios.

## Criterios de aceptación de esta etapa

- Tests deterministas aprobados usando IDs ficticios.
- Cero secretos y cero PII en GitHub/fixtures/registro de prueba.
- Ningún cambio en APK, Firestore Rules, formularios, CRM, webhooks o notificaciones de producción.
- Se documentan las incertidumbres de PAG CRM y el estado de acceso antes de pasar a datos reales.

**No usar TinyFish ni contratar plataformas nuevas.** Integración mediante servicios existentes y permisos mínimos.
