package com.pinedaagencygroup.leads;

/** Pure, testable mapping: unknown SDK codes are redacted, not echoed. */
final class OperationMessages {
    static String describe(String operation, String code) {
        String message;
        switch (code) {
            case "PERMISSION_DENIED": message="Permiso denegado. Revisa las reglas y la autorización de este usuario en staging."; break;
            case "UNAUTHENTICATED": case "ERROR_USER_TOKEN_EXPIRED": case "ERROR_INVALID_USER_TOKEN":
                message="Sesión vencida o no válida. Vuelve a iniciar sesión."; break;
            case "ERROR_USER_DISABLED": message="Cuenta suspendida. El administrador debe revisar el acceso."; break;
            case "NETWORK_ERROR": case "ERROR_NETWORK_REQUEST_FAILED":
                message="Fallo de red. Comprueba la conexión y reintenta."; break;
            case "CLIENT_TIMEOUT": message="La aplicación dejó de esperar la respuesta. Este tiempo de espera local no determina la causa del fallo."; break;
            case "UNAVAILABLE": case "DEADLINE_EXCEEDED":
                message="Servicio no disponible o sin respuesta. Puede ser conectividad o indisponibilidad del servicio; no implica falta de permisos."; break;
            case "ERROR_OPERATION_NOT_ALLOWED": case "ERROR_UNAUTHORIZED_DOMAIN": case "ERROR_INVALID_API_KEY":
                message="Servicio de autenticación no configurado para esta operación. Revisa proveedor, dominio y configuración staging."; break;
            case "FAILED_PRECONDITION": message="Falta un requisito del servicio; revisar índices y configuración. No es necesariamente un fallo de red."; break;
            case "ERROR_EXPIRED_ACTION_CODE": case "ERROR_INVALID_ACTION_CODE": case "ERROR_INVALID_CREDENTIAL":
                message="Enlace o credencial inválidos o vencidos. Utiliza una nueva credencial de pruebas."; break;
            case "INVITATION_REQUIRED": message="No hay una invitación activa sin reclamar para esta identidad."; break;
            case "EMAIL_REQUIRED": message="Se requiere una sesión con correo verificado."; break;
            case "CONFLICT": case "ABORTED": message="El registro cambió. Tu edición sigue en pantalla; vuelve a abrirlo antes de guardar."; break;
            case "RESOURCE_EXHAUSTED": case "ERROR_TOO_MANY_REQUESTS": message="Límite del servicio alcanzado. Espera antes de reintentar; no actives facturación."; break;
            default: code="UNKNOWN"; message="No se pudo completar la operación. No se confirmó ningún cambio.";
        }
        return message+" ["+operation+" · "+code+"]";
    }
}
