# Harden PAG Leads 1.9 local credentials and WebView isolation

Draft PR; base `pag-leads-v1.9-agents`, head `dev/pag-security-audit-20261102`.

PAG Leads 1.9 exposed its legacy credential to JavaScript and persistent web settings, allowed universal file-origin access, and allowed backup of application data. This change moves the UI to an intercepted HTTPS asset origin, blocks remote resources/frames, migrates local notes and drafts, stores legacy tokens with Android Keystore AES-GCM, and routes legacy requests through restricted native HTTPS transport. Backup/transfer and screenshots are restricted, and an assignment callback checks the current account before displaying data.

Includes migration/UI tests, vault instrumentation assertions, seven existing Android lint constant fixes, branch inventory, audit limitations, repository separation and recovery plan. No backend deployments, sends, database changes or releases.

Validation: see RESULTS.md. Keep this PR in draft until real WebView upgrade/instrumentation tests and Firestore emulator tests pass. In particular, verify Android 6+/modern WebView migration, corrupt/unavailable Keystore, account switching, notification denial, app links, and notes/borradores before considering merge. Arbitrary legacy endpoints are deliberately rejected; only Apps Script HTTPS is supported.

Rollback requires a tested migration plan; do not reinstall old binaries assuming plaintext tokens or the old WebView origin remain authoritative.
