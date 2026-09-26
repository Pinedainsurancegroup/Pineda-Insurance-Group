# PAG Leads 1.8 RC1 — candidate update, September 26, 2026

Not STABLE. Juan confirmed QA13 password access, two physical phones, notes,
status/history synchronization in both directions, a new form submission,
notification on the approved primary QA phone and the new lead on both phones.
Those results do not prove an update of the stable package.

## Candidate changes

- Stable package remains `com.pinedaagencygroup.leads`; versionCode 14 exceeds
  v1.7 HOTFIX's code 8. Version name `1.8-RC1`, visible label CANDIDATA 1.
- Populate the stable variant's previously empty Owner Gateway resource with
  the same deployed endpoint tested by QA13. The authenticated gateway takes
  precedence over preserved legacy URL/token settings and supplies stable IDs.
- Same Google/Owner password access, Rules and recruitment sync as QA13.
- Keep `pag_native`, `pagset12`, `pagov`, WebView origin and package unchanged.
  Existing cloud state wins; local notes remain available for explicit review.
  Import into an existing cloud record creates a backup history event instead
  of overwriting its state. Original local notes are not erased.
- Existing legacy monitor remains for configured stable installs; no token
  rotation, source replacement, billing upgrade or real FE client data.
- The candidate registers its own device request. QA and stable packages have
  different installations/tokens even on one phone. The current private sender
  still targets the approved QA device. Do not claim candidate push delivery,
  replace that target or retire QA before the new registration is reviewed and
  the sender transition is separately tested.

## Verification

- Eleven Node UI/lifecycle tests, including synthetic legacy configuration +
  cloud state precedence and preservation of original notes for review.
- `check-pag-leads-upgrade.yml` builds a synthetic code-8 baseline, seeds local
  notes, preferences and monitor state, then uses `adb install -r` for code 14.
  Test instrumentation reads both native preferences and the production page's
  same-origin localStorage, with a closed auth gate and no production requests.
- The baseline has matching storage contracts, not the real v1.7 binary. CI
  uses a disposable debug certificate; separate local signature verification
  must compare the deliverable against the archived real v1.7 APK.
- Instrumentation and synthetic fixture data are test-only, absent from the
  signed deliverable. No production keys, tokens or lead data enter CI.

## Physical update gate

Explain the replacement before installation: updating PAG Leads (without QA)
changes v1.7 into this candidate, while PAG Leads QA remains separate. Never
uninstall or clear data to resolve an update error. Do not promise a simple
APK downgrade. Record Juan's decision before this phase.

On the actual phone verify update acceptance, Owner login, source loading,
buttons/navigation, same cloud notes/history, preferences and reviewed local
note preservation. If legacy local notes exist, review each match before
import; no bulk automatic assignment. Review the candidate's FCM registration
and send/receive a real generic push before its stable promotion. Keep the
working QA sender and fallback monitor during the transition. No STABLE label
until these gates are complete.
