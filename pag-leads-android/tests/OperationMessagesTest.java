package com.pinedaagencygroup.leads;
public final class OperationMessagesTest {
    public static void main(String[] args) {
        String op="agentInvitations GET";
        assert OperationMessages.describe(op,"PERMISSION_DENIED").contains("Permiso denegado");
        assert OperationMessages.describe(op,"UNAUTHENTICATED").contains("Sesión vencida");
        assert OperationMessages.describe(op,"ERROR_UNAUTHORIZED_DOMAIN").contains("no configurado");
        assert OperationMessages.describe(op,"NETWORK_ERROR").contains("Fallo de red");
        assert OperationMessages.describe(op,"UNAVAILABLE").contains("no implica falta de permisos");
        assert OperationMessages.describe(op,"FAILED_PRECONDITION").contains("índices");
        assert OperationMessages.describe(op,"secret-link@example.test").endsWith("UNKNOWN]");
        assert !OperationMessages.describe(op,"secret-link@example.test").contains("secret-link");
        assert OperationMessages.describe(op,"CONFLICT").contains("edición sigue");
        System.out.println("PASS OperationMessages: categories and unknown-code redaction");
    }
}
