# Dispositivos, fuentes y acceso pendientes

## Estado observado en esta continuación

- HEAD inicial ada5e1c confirmado. No dispositivos ADB: lista vacía. No se instalaron ni arrancaron aplicaciones en dispositivos reales.
- Runtime: sin secret bindings/variables staging configuradas. Los recursos main y qa conocidos apuntan al proyecto activo anterior; no se reutilizaron.
- GitHub API: CONNECT del proxy rechazado con 403 antes de TLS. Borrador contiene api.github.com/storage.googleapis.com; runtime todavía declara dominios personalizados vacíos y estado de política unknown. Guardar borrador no aplicó la política.
- No hay herramienta de navegador autenticado ni herramienta GitHub/PR disponible. Git puede leer/subir ramas; eso no abre PR ni prueba permisos API. Los procedimientos manuales siguen en docs/audit/MANUAL-PULL-REQUESTS.md. PR no creado ni fusionado.

## PIMFLEX TV en dispositivo (pendiente)

Usar ID com.pimflextv.next.audit, firma debug, nunca reemplazar com.pimflextv.next. El APK offline de ada5e1c sigue disponible para UI local; no se recompiló. Para pruebas conectadas faltan proveedor/servidor TLS de staging con cuenta sintética, streams autorizados de prueba, política de redirección y un dispositivo Android TV y otro móvil (mando, back, ciclo de vida, audio/subtítulos). No intentar la URL HTTP predeterminada ni credenciales guardadas de la versión estable. Exigir redacción de URLs con usuario/password y verificar que login fallido/timeout no los exponga.

## Taty Nails 4.1 en dispositivo (pendiente)

Usar com.tatynails.app.audit. APK offline previo conserva aislamiento, sin calendario. Probar formulario, solapamientos, fechas/DST, depósitos, cancelación y reinicio con citas sintéticas; no modificar agenda real. Para calendario, crear calendario local exclusivo de pruebas en dispositivo dedicado antes de variante conectada con permisos. Verificar cancelación de alarmas/arranque/POST_NOTIFICATIONS/privacidad en bloqueo. No reutilizar backups con clientes reales ni dar por validadas migraciones SQLite por compilar.

## Qué acceso falta exactamente

Se consultaron ramas del repositorio autorizado, referencias locales y página pública de repositorios del propietario (solo muestra Pineda-Insurance-Group). Esto no permite enumerar repositorios privados y no demuestra que los otros proyectos no existan.

| Proyecto | Lo encontrado | Acceso/artefactos necesarios |
|---|---|---|
| PAG AI | Plan y referencias, sin fuente ejecutable completo | URL exacta repo o export fuente autorizado; lectura Git y commit; manifiesto/lockfiles; contrato de sugerencias/herramientas; endpoint staging; fixtures de prompt injection. Si requiere proveedor AI, binding de credencial solo al endpoint de pruebas, nunca en chat |
| PAG CRM v22 | Bridge HighLevel/controles, no implementación CRM completa | URL repo/export y SHA v22; lectura de código y esquema/migraciones; dataset anonimizado; base/cola aislada staging; contrato consentimiento, pausa, tenancy e idempotencia; config pública y bindings de pruebas |
| WhatsApp Receiver v23 | Controles simulados; sin receptor desplegable completo | URL repo/export y SHA v23; contratos webhook/ACK y fixtures firmados sintéticos; inbox/outbox y estrategia replay; endpoint staging; bindings de verificación solo staging. Ningún permiso de envío real ni teléfono productivo es necesario para revisión |

No se adivinan nombres de repositorios ni se piden permisos administrativos productivos. Para trabajo local basta lectura de los repositorios y fixtures; para validar integraciones, acceso exclusivamente a los servicios de pruebas. No hace falta acceso a campañas ni bases productivas.

PAG staging necesita los seis identificadores públicos del ejemplo, registro .staging/OAuth con certificado de prueba, gateway/hoja sintéticos y cuentas de prueba. Los secretos servidor se introducen únicamente en settings/vault del entorno de pruebas si llegan a ser necesarios. Un Android autorizado debe estar conectado por USB o por la ruta ADB/VPN que el propietario configure; no se escanea la red buscando dispositivos.
