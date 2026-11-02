# Harden PAG Leads 1.9 and prepare isolated Firebase staging

Draft PR. Base: pag-leads-v1.9-agents. Head: dev/pag-security-audit-20261102. Do not target main or merge before the pending functional checks.

PAG Leads 1.9 exposed its legacy token to persistent web settings, allowed universal file-origin access and backup of sensitive application state. The change isolates WebView assets, migrates notes/drafts without plaintext token persistence, uses Android Keystore AES-GCM, restricts legacy transport and handles migration errors without reporting false success. It also fixes existing lint constants and checks account identity on an assignment callback.

Staging preparation targets the existing pag-leads-staging project (301600139735) and independent com.pinedaagencygroup.leads.staging package. Runtime checks reject other projects/numbers and unexpected default Firebase app instances. The staging manifest uses its own auth-link domain and removes the legacy polling service; the legacy gateway fallback is disabled. An importer requires the real authorized Android SDK configuration and permits auth-only QA with the gateway unconfigured, rather than inheriting production endpoints. No fake connected APK is supplied.

Includes deny-all bootstrap, an unapplied minimal identity-only rules candidate with a demo emulator suite, a standalone staging gateway preparation bundle, functional-device runbooks, integration contract tests and source recovery evidence. No rule deployment, production access, campaigns or sends.

Validation: Android Java compile passed; StagingPolicy parser/identity assertions passed; 14 Python preparation/import tests and 51 local Node tests passed in the latest phase. Firestore identity suite defines 12 checks but did not execute because the emulator JAR download is blocked. Android device tests, actual staging SDK config/import/build, Google/email login, FCM receipt, sync, WebView/Keystore upgrade and recovery are pending. See docs/staging/pag-leads-staging for exact access failures and certificate fingerprints.

Keep as draft. Rollback and upgrade must be rehearsed with isolated fixtures; do not reinstall older binaries assuming plaintext tokens or the old WebView origin remain authoritative. Offline APKs from the previous phase are not connected staging candidates.
