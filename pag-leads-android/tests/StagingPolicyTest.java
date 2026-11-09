package com.pinedaagencygroup.leads;
public final class StagingPolicyTest {
    public static void main(String[] args) {
        // App-ID strings here are parser inputs, not credentials or deployed app configs.
        assert StagingPolicy.accepts("pag-leads-staging", "301600139735", "1:301600139735:android:abc123");
        assert !StagingPolicy.accepts("pag-leads-8c6ef", "301600139735", "1:301600139735:android:abc123");
        assert !StagingPolicy.accepts("pag-leads-staging", "880973015225", "1:880973015225:android:abc123");
        assert !StagingPolicy.accepts("other-project", "301600139735", "1:301600139735:android:abc123");
        assert !StagingPolicy.accepts("pag-leads-staging", "301600139735", null);
        assert !StagingPolicy.accepts("pag-leads-staging", "301600139735", "1:301600139735:android:INVALID");
        assert StagingPolicy.allowsScreenshots("com.pinedaagencygroup.leads.staging");
        assert !StagingPolicy.allowsScreenshots("com.pinedaagencygroup.leads");
        assert !StagingPolicy.allowsScreenshots("com.pinedaagencygroup.leads.qa");
        assert !StagingPolicy.allowsScreenshots("com.pinedaagencygroup.leads.staging.fake");
        assert !StagingPolicy.allowsScreenshots(null);
        System.out.println("StagingPolicy: identity guards and Staging-only screenshot policy passed");
    }
}
