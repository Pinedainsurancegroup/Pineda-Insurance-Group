# PAG Leads owner recruitment gateway — staged

This function is **not deployed**. The existing Form → private Sheet → private Apps Script remains the source. Deploying this callable does not edit the Apps Script or import clients into Firestore.

## Before deployment

1. Confirm the Firebase project and Cloud Billing plan. As of 2026-09-25 the project `pag-leads-8c6ef` is on Spark; Cloud Functions deployment needs Blaze. Do not upgrade billing without Juan's explicit approval of costs.
2. Verify the current private Apps Script deployment URL and token from an authorized private source, without sending either through chat or committing either to GitHub. Do not rotate the existing token while v1.7 depends on it.
3. Set `PAG_PRIVATE_API_URL` and `PAG_PRIVATE_API_TOKEN` directly in Firebase Secret Manager for this project. Restrict their access to the function's runtime identity. Never put them in the APK, a GitHub Actions secret for public builds, Firestore or a committed `.env` file.
4. From the `firebase` directory, deploy only `functions:ownerRecruitment` to `pag-leads-8c6ef`. Verify a signed-in active owner can `ping` and list the same recruitment records as v1.7; unapproved or suspended users must fail. Check logs without recording lead data or secrets.
5. Build a **new side-by-side QA** and test it on Juan's phone. The installed QA APK does not contain this gateway. Do not replace v1.7 until the full release checklist passes.

The callable accepts only `ping` and `list`, checks the current owner profile on every request, and returns only recruitment agents. Local v1.7 URL/token settings continue to use the legacy path until migration is validated.
