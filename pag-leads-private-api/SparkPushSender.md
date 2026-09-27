# Private Spark push sender — QA activation and RC transition

## RC transition (26 September 2026)

Juan verified QA form delivery, then RC1 installation, its manual FCM notice,
notification tap, notes, state and history. The initial QA-only status below is
historical. Juan subsequently confirmed a new form notification in the background,
opening the app by tapping it, the new lead on both phones, and synchronized
Contactado status, notes and history (26 September 2026, California). This closes
the physical automatic-delivery gate for RC1. It does not approve a second push
destination, measure latency, or retire the fallback monitor. See
`firebase/RELEASE_STABLE_v1.8.md` for the metadata-only stable promotion.

`QA_DEVICE_ID` keeps the original approved QA installation. Optional
`PUSH_PRIMARY_DEVICE_ID` selects the single destination for new automatic events;
when absent, QA remains the default. `CANDIDATE_DEVICE_ID` is a separate reviewed
RC target. `pagActivateCandidateAutomaticPush` validates the active Owner,
preferences, device approval and current token with FCM validation-only, then
sets the primary destination and a route audit under the existing script lock.
It creates no lead, sends no visible message, changes no triggers or permissions,
and preserves the QA approval and identifier. Do not run before physical RC tests.

Each new queue record stores its original device ID. Retries keep that target
even if the primary route changes; records from before this change remain on QA.
The explicit QA approval/test functions continue to use QA_DEVICE_ID. The RC
single-attempt probe stays outside the automatic retry queue. All sends retain
the same Owner, preference, approved-token and global daily-cap checks.

For an authorized rollback, validate the existing QA target first and restore
the primary property to QA_DEVICE_ID (or remove only the primary property).
Already queued RC events remain pinned to RC; evaluate them separately rather
than silently redirecting them. Never delete user devices or operational history.

## Original QA setup

2026-09-26 UTC: Juan explicitly approved the five OAuth scopes below and the
specific QA phone. The separate private script was authorized, the phone approved,
and `pagVerifyPushSender` returned `PAG_PUSH_VALIDATE_ACCEPTED`. PUSH_ENABLED is
true and `pagInstallPushTriggers` returned `PAG_PUSH_TRIGGERS_READY`. This remains
QA: a real form event and visible handset receipt still need verification.

Use a **new private standalone Apps Script** belonging to Juan. No web app, no
`doPost`, no service-account key, no Blaze/Cloud Functions. Do not edit the live
v1.7 API, the existing email notification script, or Owner Gateway permissions.

Before activation, Juan must approve the new OAuth permissions and specific QA
device. The Sheets trigger requires the **full Sheets scope**, including editing,
although this code never writes spreadsheet cells. OAuth `datastore` can act
administratively on Firestore under Juan's IAM privileges; it is not restricted
by client Rules. `firebase.messaging` enables sends. `script.scriptapp` installs
triggers and `script.external_request` calls the Google APIs. Do not characterize
these permissions as read-only or exclusively scoped to the one sheet.

Keep the script private. It checks an active, unsuspended owner and notification
preferences for every attempt, then requires an enabled admin-created device
record with the exact approved token hash. A deviceRequest cannot approve itself.
A changed token requires renewed administrative approval; never copy tokens into
chat or a public repository. The initial implementation targets only one approved
QA device; future multiple-device support needs explicit expansion and tests.

Script properties: FIREBASE_PROJECT_ID, OWNER_UID, SPREADSHEET_ID, SHEET_NAME,
QA_DEVICE_ID, PUSH_ENABLED (`false` until validated). Values stay out of GitHub.

After approval: copy code/manifest into the separate project, authorize, check
FCM and Firestore APIs available for its OAuth consumer project, explicitly approve
the selected device with `pagApproveQaDevice`, then `pagVerifyPushSender` must report
`PAG_PUSH_VALIDATE_ACCEPTED`. This uses `validate_only`, sends nothing. Set
PUSH_ENABLED=true and run `pagInstallPushTriggers`. Do not deploy as web app.

`pagSendQaTestNotification` is an administrative phone probe. It uses the same
authorization, approved-device checks, cap and retries, marks its private ledger
record as a test, and creates no spreadsheet row or lead. The visible notification
is generic recruitment text. Do not count it as evidence of a real form trigger.

The form-submit event sends immediately through FCM. The five-minute trigger
only retries pending failures, at most three sends per event and 500 attempts/day.
It never polls or reads lead rows. The bounded private event ledger stores only
hashed coordinates/timestamp and status, up to 100 events for seven days.
If that capacity is reached, new events fail visibly in execution logs; increase
only after reviewing volume. At-least-once attempts can repeat after a crash;
the event ID gives Android a stable notification ID. Delivery is not guaranteed
or instantaneous when the phone/network/Google service is unavailable.

Verify one real form submission and phone receipt, with foreground/background
tests and notifications disabled test. FCM `ACCEPTED` is not delivery evidence.
Existing polling remains until this real path is verified. Disable only this
sender by setting PUSH_ENABLED=false. Never rotate the old token during this step.

References:
- https://developers.google.com/apps-script/reference/script/trigger-builder#forspreadsheetkey
- https://developers.google.com/apps-script/reference/script/script-app#getoauthtoken
- https://firebase.google.com/docs/firestore/use-rest-api
- https://firebase.google.com/docs/reference/fcm/rest/v1/projects.messages/send
