package com.pinedaagencygroup.leads;

import com.google.firebase.FirebaseNetworkException;
import com.google.firebase.auth.FirebaseAuthException;
import com.google.firebase.firestore.FirebaseFirestoreException;

/** Display only SDK codes and developer-supplied operation labels, never exception messages/URLs. */
final class OperationErrors {
    static String describe(String operation, Exception error) {
        // Transaction libraries can wrap domain failures in UNKNOWN; preserve only these fixed codes.
        for (Throwable t = error; t != null; t = t.getCause()) {
            String message = t.getMessage();
            if ("CONFLICT".equals(message) || "INVITATION_REQUIRED".equals(message) || "EMAIL_REQUIRED".equals(message))
                return OperationMessages.describe(operation, message);
        }
        String code = "UNKNOWN";
        for (Throwable t = error; t != null; t = t.getCause()) {
            if (t instanceof FirebaseFirestoreException) {
                code = ((FirebaseFirestoreException)t).getCode().name(); break;
            }
            if (t instanceof FirebaseAuthException) {
                code = ((FirebaseAuthException)t).getErrorCode(); break;
            }
            if (t instanceof FirebaseNetworkException) { code = "NETWORK_ERROR"; break; }
            if ("CONFLICT".equals(t.getMessage())) { code = "CONFLICT"; break; }
            if ("INVITATION_REQUIRED".equals(t.getMessage())) { code = "INVITATION_REQUIRED"; break; }
            if ("EMAIL_REQUIRED".equals(t.getMessage())) { code = "EMAIL_REQUIRED"; break; }
        }
        return OperationMessages.describe(operation, code);
    }
}
