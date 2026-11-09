package com.pinedaagencygroup.leads;

/** Public identity checks. No credentials, SDK calls or production configuration. */
final class StagingPolicy {
    static final String PROJECT = "pag-leads-staging";
    static final String NUMBER = "301600139735";
    static final String PACKAGE = "com.pinedaagencygroup.leads.staging";
    static boolean accepts(String project, String sender, String applicationId) {
        return PROJECT.equals(project) && NUMBER.equals(sender) && applicationId != null &&
                applicationId.matches("1:" + NUMBER + ":android:[a-fA-F0-9]+");
    }
    // Screenshot capture is permitted only in the isolated PAG Leads Staging app.
    // The stable and generic QA package names retain Android FLAG_SECURE.
    static boolean allowsScreenshots(String installedPackageName) {
        return PACKAGE.equals(installedPackageName);
    }
    private StagingPolicy() {}
}
