# Plan de integración aislada: CRM, AI y WhatsApp Receiver

Estado: diseño; no servicios conectados. El bridge existente es el punto de partida, no evidencia de que CRM v22, AI o Receiver v23 implementen estos contratos.

## Contrato propuesto v1

Envelope: schemaVersion, eventId UUID, correlationId, tenantId, contactId opaco, occurredAt UTC, producer y payload tipado. Sin tokens ni PII en logs; minimización de campos. Autenticar servicio mediante credenciales en vault y verificar firma, timestamp y replay antes de aceptar eventos. tenantId nunca basta como autorización: compararlo con identidad verificada.

Eventos: LeadUpserted (CRM conserva identidad/canonización), ConsentChanged (canal, finalidad, fuente y evidencia), ConversationPaused, InboundMessageReceived, SuggestionCreated (AI solo propone), OutboundMessageRequested y DeliveryUpdated. Ningún productor obtiene permiso de envío por emitir un evento.

Receiver valida webhook, deduplica por proveedor+messageId y registra recepción antes de responder. Inbox transaccional y outbox evitan duplicados en reintentos; confirmar ACK solo tras persistencia. CRM mantiene consentimiento y pausa como fuente autorizada. Cola de errores con reintento exponencial limitado, TTL y revisión humana; no reactivar campañas al recuperar cola.

STOP/BAJA tiene prioridad sobre respuestas pendientes. Reevaluar consentimiento, pausa y propietario de conversación justo antes de enviar. Usar un lease por tenant/contacto/canal para único respondedor; idempotencyKey por intención y destinatario. Una revocación invalida sugerencias y envíos aún no ejecutados. AI no recibe claves de WhatsApp, no cambia consentimiento y no puede ejecutar herramientas por instrucciones del mensaje entrante.

## Fases y pruebas de aceptación

1. Obtener fuentes autorizadas y SHA de CRM/AI/Receiver, esquemas y muestras ficticias; documentar correspondencia con despliegue sin consultar datos reales.
2. Adaptadores in-memory y contratos JSON versionados; credenciales sintéticas y salida de red bloqueada. Reutilizar controles del bridge.
3. Probar duplicados, replay, eventos fuera de orden, tenants cruzados, STOP concurrente, vencimiento de lease, timeouts, caída tras ACK, webhook inválido, AI prompt injection y recuperación de outbox. Afirmar cero llamadas a transporte real.
4. Sandbox separado del proveedor, números de prueba permitidos explícitamente, aprobaciones de canal y kill switch. Esta fase requiere autorización nueva; no está ejecutada.
5. Revisión de seguridad, prueba de reversión y decisión humana antes de cualquier activación real.

Deshabilitado por defecto: sendEnabled=false, AI en modo propuesta, allowlist de contactos de prueba vacía. Configuración por entorno, límites por contacto y presupuesto global. No crear estos flags en servicios activos durante este trabajo.

## Recuperación

Pausar consumidores de envío; conservar inbox/outbox y marcas de idempotencia. Restaurar snapshot solo en sandbox, reproducir fixtures y comprobar cero envíos. Descartar/revalidar intenciones expiradas tras recuperación; nunca resetear deduplicación para forzar reenvíos. RPO/RTO y retención deben acordarse cuando se conozcan los servicios reales.
