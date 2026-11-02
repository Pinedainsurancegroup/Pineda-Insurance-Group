# Contratos de integración: simulación local

Ejecutar `node --test --test-isolation=none integration-sandbox/tests/*.test.cjs` desde la raíz.

La copia de `vendor/integration-controls.cjs` procede del commit `fbbe987e83ae4b4153f1dfe4d7bc051ca80f69bc`, ruta `pag-leads-bridge/integration-controls.cjs`, SHA256 `86b78fb6b0a2e5ef012d844e500237bc91391de5e623871e30c4abc6179db73c`. No se modificó ese módulo. La copia permite pruebas reproducibles sin depender de archivos externos ni de servicios activos.

Se prueban STOP posterior a propuesta AI, pausa humana, estado obsoleto, evidencia de otro tenant/contacto, propuesta superada y reconciliación de entrega sin reenvío. La elegibilidad nunca concede autorización de envío. Seis escenarios pasan con fixtures sintéticos.

Estos tests prueban decisiones de contrato. No implementan ni verifican autenticación real, locks distribuidos, inbox/outbox persistentes, firma del proveedor o APIs de PAG AI/CRM/Receiver. No hay adaptador de transporte, SDK del proveedor, credenciales ni función de envío. Una propuesta AI no se interpreta como instrucción ejecutable.
