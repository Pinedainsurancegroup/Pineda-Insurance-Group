package com.pinedaagencygroup.leads;

public final class AccessCheckTest {
    public static void main(String[] args) {
        AccessCheck check = new AccessCheck();
        int first = check.begin("juan");
        assert check.accepts(first, "juan");
        assert !check.accepts(first, "other-user");
        assert !check.accepts(first, null);
        check.cancel();
        assert !check.accepts(first, "juan") : "A paused callback cannot reveal leads";
        int resumed = check.begin("juan");
        assert !check.accepts(first, "juan") : "An earlier foreground result is stale";
        assert check.accepts(resumed, "juan");
        int switched = check.begin("other-user");
        assert !check.accepts(resumed, "juan");
        assert !check.accepts(switched, "juan");
        check.cancel();
        assert !check.accepts(switched, "other-user") : "Timeout/revocation invalidates pending results";
        System.out.println("AccessCheck: pause, resume, account switch and cancellation passed");
    }
}
