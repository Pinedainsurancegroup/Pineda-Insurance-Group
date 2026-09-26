# PAG Leads QA13 — acceso manual del Owner

Decisión de Juan, 26/09/2026: permitir escribir correo y contraseña en el segundo teléfono sin agregar allí una cuenta de Google. Los futuros agentes solo tendrán acceso tras autorización de PAG. Esta versión sigue siendo QA.

## Cuenta e identidad

- La contraseña es exclusiva de PAG Leads. No se solicita la contraseña de Google en la app ni en el chat.
- Primer teléfono, con sesión del Owner: Ajustes → Crear contraseña de PAG Leads. Un diálogo nativo pide contraseña y confirmación; `linkWithCredential(EmailAuthProvider...)` conserva el UID existente y el proveedor Google.
- Segundo teléfono: Entrar con correo · Owner. `signInWithEmailAndPassword` y la comprobación posterior del perfil del servidor son obligatorios.
- La app no crea cuentas con contraseña, no escribe roles ni concede permisos por coincidencia de correo. El acceso manual y la vinculación se limitan además a la identidad del Owner existente. Las Security Rules siguen imponiendo rol, estado activo y suspensión en el servidor.
- Firebase habilita proveedores por proyecto, no por rol. Aunque alguien intentara registrar otra identidad directamente en Auth, no obtendría un perfil autorizado ni datos. No se crea autoservicio de alta o aprobación. La futura autorización de agentes requiere provisionamiento administrativo y su app/área correspondiente.

## Contraseña

Entrada nativa oculta y protegida contra capturas; no pasa al HTML/JavaScript, preferencias, historial ni registros. Se borra de los campos al terminar/cerrar/salir. Se exige de 12 a 128 caracteres para la vinculación inicial. Los errores se muestran sin datos internos. Recuperar contraseña solo envía el correo de Firebase cuando el usuario toca esa opción.

## Configuración y prueba pendientes

Habilitar Email/Password conservando Google en Firebase Authentication; no habilitar enlace sin contraseña ni cambiar facturación. La sesión administrativa estaba cerrada al preparar esta versión: no considerar aplicado hasta verificación de la consola. Juan debe elegir y enviar su nueva contraseña personalmente desde el teléfono; nunca establecer una contraseña por él.

La prueba de emuladores cubre Google → contraseña sobre el mismo UID, acceso desde otra sesión a notas/historial, conservación de Google, contraseña incorrecta, cuenta no autorizada y suspensión de ambas sesiones. No certifica la experiencia del selector/teclado Android ni la vinculación real en producción. Verificar en los dos teléfonos después de habilitar el proveedor.

v1.7, fuente de reclutamiento, reglas, asignaciones, FCM y firma estable siguen bajo los criterios anteriores. No promover QA13 a STABLE por esta modificación.
