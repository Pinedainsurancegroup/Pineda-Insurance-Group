# PAG Leads v1.8 — Firebase architecture (draft, 2026-09-24)

Status: Firestore created in nam5; security rules published and tested in the local emulator. Android Google sign-in gate and public Firebase client configuration compiled in GitHub Actions, but login and device behavior remain untested. v1.7 remains the production app. Do not install v1.8 over it until release checks pass.

## Current system and rollout

- Google Form → private Google Sheet → private Apps Script → PAG Leads remains the recruitment source. No client FE import or dual-write has been enabled.
- Firebase project `pag-leads-8c6ef` and Android app `com.pinedaagencygroup.leads` registered. Google provider enabled. Release SHA-1 and SHA-256 were read from the v1.7 HOTFIX APK certificate and registered in Firebase. The private signing key and Auth UID still require verification. Firestore `(default)` Standard edition in `nam5 (United States)` is created and the latest security rules are published. The owner Auth UID and release signing key remain pending.
- Existing v1.8 FCM scaffolding requires server-side authenticated registration, administrative credentials outside GitHub, and a real-device push test. The public Firebase client IDs are populated. Keep the one-minute monitor. Do not ship v1.8 as STABLE before stable signing and device tests.

## Access and data model

`users/{uid}`: `role` (`owner`, future `leader` or `agent`), `active`, `suspended`, `authorizedTeamIds` (empty by default). The initial owner profile must be provisioned through a trusted administrative channel after Juan signs in and the UID is verified. No client can create or promote a profile. Suspending means server changes `suspended: true`; every Firestore read checks the current profile, including an old signed-in session. User deletion is unnecessary.

`users/{uid}/preferences/operational`: synchronized nonsecret settings. `users/{uid}/devices/{deviceId}`: server-managed device registration and authorization; tokens never appear in public code or notification payloads.

`recruitment/{sourceLeadId}`: optional future mirror, owner-only. Source IDs must be stable and deduplicated; no app-side import of real recruitment records until source mapping is checked. Recruitment and FE clients are separate top-level collections.

`clients/{clientId}`: one stable customer ID; `classification: LEAD | B_LEAD`; `assignedTo` UID or null; `teamId` or null; `status`, created/updated dates. Only a trusted admin backend creates or edits the canonical record. `clients/{clientId}/assignments/{eventId}` records each assignment, return to inventory, classification change and reassignment as append-only events, including `actorUid`, previous and next assignee/classification and server timestamp. `clients/{clientId}/activity/{eventId}` records notes, status and results with author UID and server timestamp; clients cannot alter previous events. The UI must display latest activity without erasing history when assignedTo changes. A former agent loses access to the customer after reassignment; owner sees full history. Leader team access remains disabled unless owner adds an authorized team ID.

Rules in `firestore.rules` deny all unlisted paths and client writes to users, roles, assignments and canonical clients. They are **not yet deployed or tested**. A future emulator suite must test cross-agent reads, recruitment denial, stale-session suspension, reassignment, leader grant and malicious field updates. Firestore queries must carry assignment/team constraints; rules do not filter query results.

## Local overlay migration

Current WebView localStorage `pagov` contains status and note per source lead ID. Existing connection URL/token live in `pagset12` and Android SharedPreferences. In a staged owner-only migration: read local overlay, snapshot/export it privately, compare source IDs against the live API, send each status/note once with an idempotency key `(uid, sourceLeadId, updatedAt)` to a trusted authenticated migration endpoint, verify counts and hashes, then display Firestore changes from two signed-in devices. Preserve local overlay until verification and never upload API token to Firestore. Resolve concurrent edits using server timestamps and immutable activity; avoid last-writer-wins overwriting a newer note. A replacement phone cannot recover the old API credential solely from Firebase; a trusted server must proxy the existing source after Auth, or a credential handoff must be designed before claiming full portability.

## Suspension and notification limits

Disable Firestore offline persistence on clients when enabling it. Previously downloaded PII and legacy local WebView storage cannot be remotely erased from an offline device; online Security Rules deny new reads. The old shared Apps Script token remains valid until rotated and its endpoint enforces Auth, so a suspended user with that token could bypass Firestore. Do not enroll future agents in that endpoint. A server must verify the Firebase ID token and active profile for every API/FCM registration and stop sends to suspended devices. FCM messages must be fixed generic text with no prospect name, phone, email or content supplied by the server. Android notification visibility must be private. Do not rotate the old token until the replacement path works on Juan's phone.

## Release gates

Verify Google sign-in with Juan, exact Auth UID and owner profile; Firestore read/write and rules tests; FCM token registration and a real generic push; source lead loading, navigation and controls; same signing certificate and successful update over v1.7 preserving local settings. Only then sign and label v1.8 STABLE and test the update on Juan's phone. No client FE production records or other user accounts in this phase.
