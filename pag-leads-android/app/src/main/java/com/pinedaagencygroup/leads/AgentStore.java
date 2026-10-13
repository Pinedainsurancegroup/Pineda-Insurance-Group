package com.pinedaagencygroup.leads;

import com.google.android.gms.tasks.Task;
import com.google.firebase.auth.FirebaseAuth;
import com.google.firebase.firestore.*;
import java.util.*;

/** All authority is enforced again by Firestore rules; no administrative credential in the app. */
final class AgentStore {
    final FirebaseFirestore db = FirebaseFirestore.getInstance();
    static long revision(DocumentSnapshot doc) {
        Long n = doc.getLong("revision"); return n == null ? 0L : n;
    }
    Task<Void> save(String bucket, String id, Map<String,Object> values, long expected) {
        String uid = FirebaseAuth.getInstance().getCurrentUser().getUid();
        DocumentReference ref = db.collection(bucket).document(id);
        DocumentReference event = ref.collection("audit").document(UUID.randomUUID().toString());
        return db.runTransaction(tx -> {
            DocumentSnapshot previous = tx.get(ref);
            if (revision(previous) != expected) throw new IllegalStateException("CONFLICT");
            Map<String,Object> after = new HashMap<>(values);
            after.put("revision", expected + 1); after.put("lastEventId", event.getId());
            after.put("updatedBy", uid); after.put("updatedAt", FieldValue.serverTimestamp());
            Map<String,Object> audit = new HashMap<>();
            audit.put("before", previous.exists() ? previous.getData() : new HashMap<>());
            audit.put("after", after); audit.put("actorUid", uid); audit.put("createdAt", FieldValue.serverTimestamp());
            tx.set(ref, after); tx.set(event, audit); return null;
        });
    }
    static boolean conflict(Exception e) {
        for (Throwable t = e; t != null; t = t.getCause()) if ("CONFLICT".equals(t.getMessage())) return true;
        return false;
    }
}
