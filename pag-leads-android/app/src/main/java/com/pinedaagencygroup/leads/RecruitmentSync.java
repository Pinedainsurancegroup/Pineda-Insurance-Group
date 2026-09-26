package com.pinedaagencygroup.leads;

import com.google.firebase.Timestamp;
import com.google.firebase.firestore.*;
import org.json.*;
import java.nio.charset.StandardCharsets;
import java.security.MessageDigest;
import java.text.SimpleDateFormat;
import java.util.*;

/** Owner-only operational metadata. Source PII remains in the private Sheet. */
final class RecruitmentSync {
    interface Reply { void done(boolean ok, JSONObject value); }
    interface Watch { void changed(JSONObject value); }
    private final FirebaseFirestore db = FirebaseFirestore.getInstance();
    private final String uid, deviceId;
    private final List<ListenerRegistration> listeners = new ArrayList<>();
    private String watching = "";
    private int generation;
    RecruitmentSync(String uid, String deviceId) { this.uid = uid; this.deviceId = deviceId; }
    static boolean validId(String id) { return id != null && id.matches("r_[a-f0-9-]{36}"); }
    void stop() { generation++; for (ListenerRegistration l : listeners) l.remove(); listeners.clear(); watching = ""; }
    void watch(List<String> ids, Watch sink) {
        Collections.sort(ids);
        String key = ids.toString();
        if (key.equals(watching)) return;
        stop(); watching = key; final int current = generation;
        for (int start = 0; start < ids.size(); start += 30) {
            final List<String> batch = new ArrayList<>(ids.subList(start, Math.min(start + 30, ids.size())));
            listeners.add(db.collection("recruitmentState").whereIn(FieldPath.documentId(), batch)
                .addSnapshotListener(MetadataChanges.INCLUDE, (snapshot, error) -> {
                    if (generation != current) return;
                    JSONObject result = new JSONObject();
                    try {
                        result.put("ids", new JSONArray(batch));
                        if (error != null) { result.put("error", true).put("all", true); stop(); sink.changed(result); return; }
                        // Never treat cache/pending writes as a server acknowledgement.
                        if (snapshot == null || snapshot.getMetadata().isFromCache() || snapshot.getMetadata().hasPendingWrites()) return;
                        JSONObject states = new JSONObject();
                        for (DocumentSnapshot doc : snapshot.getDocuments()) states.put(doc.getId(), stateJson(doc.getData()));
                        result.put("states", states); sink.changed(result);
                    } catch (JSONException ignored) {}
                }));
        }
    }
    void save(JSONObject input, Reply reply) {
        try {
            String id = input.getString("leadId"), status = input.getString("status"), note = input.getString("note");
            boolean importing = input.optBoolean("importing", false);
            String original = input.optString("originalUpdatedAt", "");
            long expected = input.getLong("baseRevision");
            String eventId = importing ? hash(new JSONArray(Arrays.asList("import-v1", uid, id, original, status, note)).toString())
                    : input.getString("eventId");
            if (!validId(id) || !Arrays.asList("Nuevo", "Contactado", "Cita", "Seguimiento", "Completado").contains(status) ||
                note.length() > 4000 || original.length() > 80 || expected < 0 || !eventId.matches("[a-zA-Z0-9_-]{16,80}"))
                throw new IllegalArgumentException();
            DocumentReference state = db.collection("recruitmentState").document(id);
            DocumentReference event = state.collection("activity").document(eventId);
            db.runTransaction(tx -> {
                DocumentSnapshot previousEvent = tx.get(event), previous = tx.get(state);
                Map<String, Object> old = previous.exists() ? previous.getData() : emptyState();
                long revision = ((Number) old.get("revision")).longValue();
                if (previousEvent.exists()) {
                    if (!status.equals(previousEvent.getString("status")) || !note.equals(previousEvent.getString("note")) ||
                        !uid.equals(previousEvent.getString("actorUid"))) throw new IllegalStateException("IDEMPOTENCY_MISMATCH");
                    return response("saved", old, "already-recorded");
                }
                if (!importing && revision != expected) return response("conflict", old, "");
                String kind = importing ? (previous.exists() ? "backup" : "import") : "edit";
                boolean apply = !"backup".equals(kind);
                Map<String, Object> activity = new HashMap<>();
                activity.put("actorUid", uid); activity.put("deviceId", deviceId); activity.put("kind", kind);
                activity.put("status", status); activity.put("note", note);
                activity.put("previousStatus", old.get("status")); activity.put("previousNote", old.get("note"));
                activity.put("baseRevision", revision); activity.put("revision", apply ? revision + 1 : revision);
                activity.put("createdAt", FieldValue.serverTimestamp()); activity.put("originalUpdatedAt", original);
                Map<String, Object> next = new HashMap<>();
                next.put("status", status); next.put("note", note); next.put("revision", revision + 1);
                next.put("lastEventId", eventId); next.put("updatedBy", uid); next.put("updatedAt", FieldValue.serverTimestamp());
                tx.set(event, activity);
                if (apply) tx.set(state, next);
                return response("saved", apply ? next : old, kind);
            }).addOnSuccessListener(result -> reply.done(true, result))
              .addOnFailureListener(error -> reply.done(false, new JSONObject()));
        } catch (Exception ignored) { reply.done(false, new JSONObject()); }
    }
    void history(JSONObject input, Reply reply) {
        try {
            String id = input.getString("leadId"); if (!validId(id)) throw new IllegalArgumentException();
            Query q = db.collection("recruitmentState").document(id).collection("activity")
                    .orderBy("createdAt", Query.Direction.DESCENDING).orderBy(FieldPath.documentId(), Query.Direction.DESCENDING).limit(30);
            JSONObject cursor = input.optJSONObject("cursor");
            if (cursor != null) q = q.startAfter(new Timestamp(cursor.getLong("seconds"), cursor.getInt("nanos")), cursor.getString("id"));
            q.get(Source.SERVER).addOnSuccessListener(snapshot -> {
                JSONObject output = new JSONObject(); JSONArray events = new JSONArray();
                try {
                    for (DocumentSnapshot doc : snapshot.getDocuments()) {
                        Map<String, Object> data = doc.getData(); JSONObject item = stateJson(data);
                        item.put("id", doc.getId()); item.put("kind", doc.getString("kind"));
                        item.put("actorUid", doc.getString("actorUid")); item.put("deviceId", doc.getString("deviceId"));
                        item.put("previousStatus", doc.getString("previousStatus")); item.put("previousNote", doc.getString("previousNote"));
                        item.put("originalUpdatedAt", doc.getString("originalUpdatedAt"));
                        item.put("createdAt", date(doc.getTimestamp("createdAt"))); events.put(item);
                    }
                    output.put("events", events);
                    if (snapshot.size() == 30) {
                        DocumentSnapshot last = snapshot.getDocuments().get(snapshot.size() - 1); Timestamp t = last.getTimestamp("createdAt");
                        output.put("cursor", new JSONObject().put("seconds", t.getSeconds()).put("nanos", t.getNanoseconds()).put("id", last.getId()));
                    }
                    reply.done(true, output);
                } catch (Exception ignored) { reply.done(false, new JSONObject()); }
            }).addOnFailureListener(error -> reply.done(false, new JSONObject()));
        } catch (Exception ignored) { reply.done(false, new JSONObject()); }
    }
    private static Map<String, Object> emptyState() {
        Map<String, Object> m = new HashMap<>(); m.put("status", "Nuevo"); m.put("note", ""); m.put("revision", 0L); return m;
    }
    private static JSONObject response(String outcome, Map<String, Object> state, String kind) {
        try { return new JSONObject().put("outcome", outcome).put("state", stateJson(state)).put("kind", kind); }
        catch (JSONException e) { throw new IllegalStateException(); }
    }
    private static JSONObject stateJson(Map<String, Object> data) throws JSONException {
        JSONObject j = new JSONObject(); j.put("status", data.get("status")); j.put("note", data.get("note"));
        j.put("revision", data.get("revision"));
        Object t = data.get("updatedAt"); if (t instanceof Timestamp) j.put("updatedAt", date((Timestamp)t));
        return j;
    }
    private static String date(Timestamp t) {
        if (t == null) return "";
        SimpleDateFormat f = new SimpleDateFormat("yyyy-MM-dd'T'HH:mm:ss.SSS'Z'", Locale.US); f.setTimeZone(TimeZone.getTimeZone("UTC")); return f.format(t.toDate());
    }
    private static String hash(String value) throws Exception {
        byte[] b = MessageDigest.getInstance("SHA-256").digest(value.getBytes(StandardCharsets.UTF_8));
        StringBuilder out = new StringBuilder(); for (byte n : b) out.append(String.format(Locale.US, "%02x", n & 255)); return out.toString();
    }
}
