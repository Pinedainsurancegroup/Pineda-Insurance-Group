# Instrucciones de Codex para este repositorio

Actualizado 2026-11-08. Política aprobada para el desarrollo de las aplicaciones existentes.

## Principios de trabajo
- Usar Codex para editar, revisar, probar y preparar código; GitHub para controlar versiones. Las aplicaciones y servicios de producción continúan en sus alojamientos actuales hasta que un cambio separado sea autorizado.
- Antes de empezar, identificar la rama fuente correcta, los cambios posteriores, el paquete/versión ya validado y el destino de publicación. No usar la rama main como si contuviera necesariamente las últimas versiones: verificar las ramas de PAG Leads, PIMFLEX TV Android e iOS.
- Mantener un proyecto por producto o por componentes estrechamente relacionados. En PIMFLEX TV, compartir código de iPhone y iPad cuando tenga sentido, pero validar interfaces y dispositivos por separado.
- No reconstruir ni sobrescribir trabajo existente; no force-push, no eliminar ramas, no crear nuevas aplicaciones o cuentas cuando puede mantenerse lo existente. Trabajar en rama y documentar pruebas y revisiones.
- **Este repositorio es público.** No agregar datos personales ni comerciales, bases de clientes, archivos de contactos, credenciales, cookies, claves de firma, tokens, APK/AAB con secretos o material interno que no sea apto para publicación. Para software confidencial, planificar el traslado a un repositorio privado sin reescribir ni borrar trabajo antes de comprobar la migración; lo publicado puede quedar en el historial.
- Codex NO es un servidor de producción ni una base de datos. Firebase, Apple, Meta/WhatsApp, HighLevel, bases, alojamiento y proveedores siguen operando fuera de Codex.
- No lanzar campañas, mensajería, operaciones financieras reales, compras, cambios de credenciales, publicaciones en tiendas o migraciones de base sin autorización específica. No cambiar un sistema en uso por una copia de desarrollo.
- Para cada entrega, distinguir: código versionado, compilación y pruebas, publicación real, prueba física y función en producción. Conservar evidencia y reversión.
- Priorizar continuidad de PAG Leads y PIMFLEX; cualquier nuevo software se inventaría antes de migrarse.

La política central del propietario está conservada en un repositorio privado de la misma cuenta; este archivo contiene únicamente normas aptas para lectura pública.