# Integration controls — staging, NOT deployed

Date: 2026-10-29. Continue draft PR #8 without merging, rebuilding applications, changing subscriptions or enabling messaging.

## What this change does

`integration-controls.cjs` is a pure validator/planner. It does not fetch private records, authenticate requests, modify a database, receive webhooks, call OpenAI or send WhatsApp messages. Nothing imports it into the deployed PAG CRM/Receiver. A passing test does not establish production readiness.

- `inspectSourceIdentities`: compare original `PAG_LEAD_ID` values with an explicit HighLevel import reference (`CONTACT_ID`, `STATUS`, `LEAD_ID`). It emits HIGHLEVEL identity candidates, **not** PAG CRM contact IDs. `IMPORTED` does not grant consent or map to a lifecycle stage. Missing source references are review items, not permission to recreate deleted data. Raw source IDs remain linkable private data; publish aggregate counts only.
- `evaluatePilotSafety`: require an exact pilot tuple (location, contact, business number, destination, channel); use the restrictive union of CRM and Receiver pauses/opt-outs; block missing, stale or contradictory control reads and changed draft revisions. It never authorizes sending: an eligible result requires the executor's real atomic recheck.
- `planDeliveryReconciliation`: compare message, conversation, tenant, contact, route and content hash; plan a monotonic local status update with an expected revision. Never resend or write a provider's status. Never infer an acceptance timestamp from a delivery observation.

## Tests and limits

Run `node --test pag-leads-bridge/tests/*.test.cjs`.

There are 66 new synthetic cases, with 161 total local cases passing on Node 22.16.0 at preparation. CI must be checked for the actual resulting commit. Existing production tests and previous counts are separate evidence.

Adapters must be trusted server code with current authorization. JSON booleans, hashes, timestamps, revision numbers, `sourceReadComplete` and this module's outputs are not proof of identity/authorization. The five-second control-read freshness bound and one-minute provider observation bound are proposed guardrails, not platform guarantees. They do not eliminate races.

## Required integration against existing projects (still pending)

1. Open the **currently deployed** sources for PAG CRM and PAG WhatsApp Receiver. Read current version, configuration and schema; back up before changing anything. Do not overwrite with an older backup. The inspection report exists, but the current runtime source and operator write access are not available in this editing session.
2. Implement authenticated adapters for the existing CRM control state and Receiver control state. Normalize real database booleans explicitly (0/1 or true/false); a missing field or failed read is UNKNOWN, not false. Use primary/consistent reads for dispatch decisions. Never expose operator secrets in code, APK, logs or public PRs.
3. Keep existing human pauses. Propagate pauses/opt-outs through a durable, authenticated control event with versioned conflict handling; STOP must block locally immediately even if propagation is temporarily unavailable. A delayed resume must not undo a newer stop. Administrative opt-out anywhere must block sending everywhere. Operator resume is separate, narrow, audited and cannot silently clear opt-out.
4. At the verified webhook entry, handle outgoing human echo events as control events. A verified own-system outbox message is not a human takeover. Unknown origin should remain conservative pending reconciliation. Test duplicate/out-of-order echoes, app-originated messages, STOP, stale resume and a paused contact's later inbound message. Do not invent Meta payload fields from this module.
5. Recheck restrictive controls before generation and immediately before dispatch. Serialize the dispatch claim and control revision check in the existing durable store. A freshness timestamp alone is insufficient. D1 batch transactions apply to that database; they are NOT a transaction with an external HTTP send. Preserve uncertain sends and reconcile rather than retry. Already accepted in-flight messages cannot be retracted by a later pause.
6. For a previously delivered message that remains locally pending, use the **existing** authenticated Receiver reconciliation path after reviewing its input contract. Verify provider message/tenant/contact/conversation and body match. Update only local delivery state with concurrency checks, without sending again, fabricating acceptance times or changing provider status. This session does not have the operator credential and does not call that path.
7. Validate the pilot tuple inside the executor with protected existing configuration. Verify other auto-responders (including business-app greeting/away settings) and operator pause before allowing a two-turn test. Keep general sends and Meta-direct sends disabled. Do not claim the historical delivered message is a new end-to-end test.
8. Connect the source-identity reader through the already approved owner path. `highLevelContactId` is not `crmContactId`. Current CRM manually captured test records may legitimately have no source record: report unlinked, do not forge `r_` IDs or match on name/phone alone. Confirm Firestore revisions and authenticated mappings before feeding the existing audit module. No import, migration or bidirectional synchronization in this change.

## Control inputs

`evaluatePilotSafety` expects normalized internal snapshots with locationId, contactId, revision, observedAt (epoch ms), paused and optedOut. The draft binds CRM/Receiver revisions, last inbound ID/time and provider DND. Policy flags must be computed from actual configuration and checks, never user or model claims. Input schema is an adapter contract, **not a claim about existing DB columns**.

`planDeliveryReconciliation` uses semantic statuses pending/sent/delivered/read. Translate existing enums only after inspecting their implementation. The body hash must be calculated on the same exact UTF-8 content at both ends; never log raw body. The resulting `nextStatus` is a plan, not a SQL patch. Preserve pre-existing accepted_at.

## External reference contracts

- HighLevel message GET (read only): https://marketplace.gohighlevel.com/docs/ghl/conversations/get-message/index.html
- Cloudflare D1 batch/session semantics: https://developers.cloudflare.com/d1/worker-api/d1-database/

No TinyFish, no LeadConnector disconnect/migration, no new services, no production claims, no real-contact fixtures in GitHub.
