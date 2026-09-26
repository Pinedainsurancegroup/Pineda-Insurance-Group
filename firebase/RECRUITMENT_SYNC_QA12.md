# Recruitment metadata sync — QA12

Applied September 26, 2026. Scope: owner recruitment metadata only, Spark, separate QA package. Stable v1.7 and original Apps Script are untouched.

## Data and safeguards

| Path / field | Purpose | Writer |
|---|---|---|
| Sheet `PAG_LEAD_ID` | Immutable UUID on each complete source row | Private identity helper, blank cells only |
| `recruitmentSources/{id}` | Enabled source registry + hashed source key; no contact PII | Administrative Apps Script |
| `recruitmentState/{id}` | Current status, note, revision, event ID, author and timestamp | Active owner through Rules |
| `recruitmentState/{id}/activity/{eventId}` | Immutable before/after history or local backup | Active owner, atomic audited transaction |
| local `pagov` | Original legacy snapshot | Preserved; not deleted by migration |
| local per-UID bindings/receipts/drafts | Reviewed identity, confirmed migration receipt, recoverable pending edit | QA app only |

A source ID travels with its whole row. Never sort selected answer columns independently, reuse an ID for a different person, or generate new IDs on existing rows. No app-side source creation, FE import, agent access, token upload or role escalation is enabled.

## Live rollout

1. Run `pagInspectRecruitmentIdentity` before writes. Observed seven leads, seven missing IDs, new column 10.
2. `pagPrepareRecruitmentIdentity` filled seven blank IDs and registered seven source documents. Existing answers and old row IDs remain compatible.
3. `pagInstallIdentityTrigger` added only `pagAssignRecruitmentIdentity`. Existing `pagOnRecruitmentSubmit` and `pagRetryPendingPush` are unchanged.
4. Gateway `SparkOwnerGateway.gs` now returns both identifiers. Existing deployment URL retained, version 3. `ValidacionPrivada.gs` at HEAD performs a manual read-only count/uniqueness check; result: seven leads/seven unique permanent IDs. That diagnostic is not a web entry point and was updated after deployment v3.
5. `firebase/firestore.rules` passed emulator tests and was published at 04:46 California. Published text matches the repository exactly. Old rules are retained in Firebase version history; existing rule blocks are unchanged.
6. QA12 build versionCode 12 was signed with the existing PAG identity; install only as a QA update.

## Phone acceptance

- Open QA12 with Juan's Google account, wait for the account-backup connection, and verify all source leads load.
- If offered, open **Revisar cambios de este teléfono**. Check each prospect name against the local status/note, then select only confirmed entries and use **Respaldar los cambios marcados**. Unchecked/unidentified records remain untouched. Do not guess if an old Sheet row was reordered.
- Change one lead and note; save until **Guardado en tu cuenta**. Other leads must retain their own state. Open **Ver historial** and verify actor/date/previous values.
- Close/reopen QA; verify values persist. With another phone signed into the same owner, verify live state and history. Test simultaneous edits: the older editor must receive a conflict and retain its draft until the user decides.
- Repeat real form → unique source ID → lead load → generic FCM notice and notification opening. Do not equate a previous FCM acceptance with this test.

Do not clear app data/uninstall for these tests. QA11/local backups and QA12 cloud records coexist. v1.7 notes are not copied across Android package sandboxes; that migration belongs to a later signed stable update.

## Limits and recovery

- App watches up to 500 known source IDs, in queries of 30; history pages contain 30 events. The identity preflight caps at 5,000 eligible source rows. These are review limits, not a promise of unlimited Spark capacity.
- Each edit writes state+event; migration to existing state adds one backup event. Source list refresh and Rules lookups also consume quotas. Listeners run while the authorized UI is active; no minute-by-minute metadata polling or billing upgrade is added. Spark exhaustion can interrupt service and must not trigger automatic Blaze.
- Identity assignment and push are independent triggers, so a very early app refresh can temporarily see a new row without its ID. Refresh once the trigger completes. If provisioning fails, inspect execution errors and run the idempotent preparation function; never regenerate an existing UUID.
- Rules or listener failure blocks cloud saves. Unconfirmed edits stay local with the same event ID for retry. History does not reconstruct events that predate tracking.
- If QA12 fails, leave v1.7 installed and stop using QA12 for writes while diagnosing. Do not uninstall QA or downgrade with data deletion. The old Gateway v2 can be selected for rollback but QA12 sync then lacks IDs; preserve all added IDs/history and never erase cloud data as a rollback.
- Registry disabling blocks new writes but does not replace user suspension. Suspend the user profile to deny all new server reads. Existing offline private files cannot be remotely erased; future agents never receive the old shared token.

## Verification

Build run 36239378807 and rules run 36239378811 succeeded at code commit 5cc41bbe72cdf8c2c5b1814411305ebee4a16769. Android asset bytes match source. Separate emulator sessions verify authorization, live listeners, revisions, append-only audit and idempotent backup; they are not two physical-phone tests. Real Gateway missing-token request returned denied; real anonymous Firestore query returned 403. QA12 phone validation and stable update remain pending.
