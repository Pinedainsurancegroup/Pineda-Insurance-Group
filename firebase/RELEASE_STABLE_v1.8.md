# PAG Leads v1.8 STABLE — 26 September 2026, California

The Owner confirmed the final RC1 physical test: a new website form produced a
background notification; tapping it opened PAG Leads; the lead appeared on the
second phone; changing Nuevo to Contactado synchronized to the main phone; notes
and history were present on both. This completes the outstanding automatic
delivery test after the reviewed RC sender transition. Evidence is the Owner's
report, not remote inspection of either handset or a measured latency test.

Earlier recorded gates include Owner Google and linked PAG password access,
Firestore isolation/suspension tests, two-phone state/notes/history sync, RC1
update on the stable package, source loading, and receipt/opening of its FCM
notification. A claim about every historical local note or a physical concurrent
edit conflict is outside this evidence. Local import still requires explicit
record matching and preserves originals.

## Changes from the tested RC1 application

- Keep package `com.pinedaagencygroup.leads` and the existing PAG signing identity.
- Increment versionCode 14 to 15, versionName to `1.8-STABLE`, and visible release
  label to `PAG LEADS v1.8 · STABLE`. The separate, undelivered QA build says QA15.
- Update the existing synthetic storage-upgrade test's expected version to 15.
- No functional, dependency, Firebase resource, permission, data-model, Rules,
  gateway, sender-code or device-route change. The last sender change remains
  `c77442dceaf2b5060ff88f773a527480ce320326`.

## Delivery checks

Require the existing build, access/UI and synthetic Android storage-upgrade
checks on this commit, plus comparison of the signed release certificate with
the archived actual PAG APK. CI uses a disposable debug signature and synthetic
data; private PAG signing happens outside GitHub. Never deliver CI's debug APK.
Store the signed APK, hashes, commit, check results and dated release record in
the private Drive backup. Do not put keystores, passwords, tokens or lead data
in this repository.

Install over the current PAG Leads CANDIDATA 1 without uninstalling or clearing
data. QA remains separate. This newly built binary still needs its installation
and opening confirmed on the real phone; the RC1 physical results remain recorded
as RC1 evidence, not a claim that this binary was already installed.

## Preserved operating constraints

Firebase Spark; no paid infrastructure; Form → private Sheet → private Apps
Script as Recruitment source; independent authenticated Owner Gateway; one
approved automatic push destination with pinned retries; generic no-PII notices;
one-minute fallback monitor; old-token rotation deferred. Recruitment remains
Owner-only; FE structure is reserved with no real clients, agents or leaders.
Existing backups and the stable signing identity remain recoverable privately.
