package com.pinedaagencygroup.leads;

/** A server result may only unlock the foreground session that requested it. */
final class AccessCheck {
    private int generation;
    private boolean foreground;
    private String uid;

    int begin(String currentUid) {
        foreground = true;
        uid = currentUid;
        return ++generation;
    }

    void cancel() {
        foreground = false;
        uid = null;
        generation++;
    }

    boolean accepts(int ticket, String currentUid) {
        return foreground && ticket == generation && uid != null && uid.equals(currentUid);
    }
}
