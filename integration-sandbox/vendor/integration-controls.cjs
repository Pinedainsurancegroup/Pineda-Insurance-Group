"use strict";
// STAGING ONLY. Pure validation/planning: no authentication, I/O or permission grant.
// Inputs MUST come from authenticated server adapters, not an LLM or client JSON.
const ID = /^[A-Za-z0-9][A-Za-z0-9_-]{0,127}$/;
const MESSAGE_ID = /^[A-Za-z0-9._:\/=+-]{1,512}$/;
const LEAD = /^r_[a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12}$/;
const PHONE = /^\+[1-9]\d{7,14}$/;
function record(v, keys) {
  if (!v || ![Object.prototype, null].includes(Object.getPrototypeOf(v))) throw Error("invalid-record");
  const o = {};
  for (const k of keys) {
    const d = Object.getOwnPropertyDescriptor(v, k);
    if (!d || !Object.hasOwn(d, "value")) throw Error("invalid-field");
    o[k] = d.value;
  }
  return o;
}
function array(v) {
  if (!Array.isArray(v) || v.length > 2000) throw Error("invalid-batch");
  for (let i = 0; i < v.length; i++) {
    const d = Object.getOwnPropertyDescriptor(v, String(i));
    if (!d || !Object.hasOwn(d, "value")) throw Error("invalid-batch");
  }
  return v;
}
function str(v, re) { if (typeof v !== "string" || !re.test(v)) throw Error("invalid-id"); return v; }
function integer(v) { if (!Number.isSafeInteger(v) || v < 0 || Object.is(v, -0)) throw Error("invalid-number"); return v; }
function flag(v) { if (v === true || v === 1) return true; if (v === false || v === 0) return false; throw Error("unknown-control"); }
function counts(items) { const m = new Map(); for (const v of items) m.set(v, (m.get(v) || 0) + 1); return m; }

// These are PAG Leads <-> HIGHLEVEL identity candidates, NOT PAG CRM mappings.
// IMPORTED is a source label, not a consent flag or a recruitment lifecycle state.
function inspectSourceIdentities(input) {
  const {sourceIds, highLevelRows, locationId, sourceReadComplete} = record(input, ["sourceIds", "highLevelRows", "locationId", "sourceReadComplete"]);
  if (sourceReadComplete !== true) throw Error("incomplete-source");
  str(locationId, ID); array(sourceIds); array(highLevelRows);
  const ids = sourceIds.filter(x => x !== "").map(x => str(x, LEAD));
  const sourceCounts = counts(ids);
  const rows = highLevelRows.map(x => {
    const r = record(x, ["contactId", "sourceLeadId", "importStatus"]);
    str(r.contactId, ID); str(r.sourceLeadId, LEAD);
    if (typeof r.importStatus !== "string" || r.importStatus.length > 40) throw Error("invalid-import-status");
    return r;
  });
  const byLead = counts(rows.map(r => r.sourceLeadId));
  const byContact = counts(rows.map(r => r.contactId));
  const summary = {sourceIds: ids.length, importRows: rows.length, matched: 0, orphaned: 0, ambiguous: 0, notImported: 0};
  const candidates = [];
  for (const r of rows) {
    if (r.importStatus !== "IMPORTED") { summary.notImported++; continue; }
    if (!sourceCounts.has(r.sourceLeadId)) { summary.orphaned++; continue; }
    if (sourceCounts.get(r.sourceLeadId) !== 1 || byLead.get(r.sourceLeadId) !== 1 || byContact.get(r.contactId) !== 1) {
      summary.ambiguous++; continue;
    }
    summary.matched++;
    candidates.push(Object.freeze({sourceLeadId: r.sourceLeadId, highLevelContactId: r.contactId, locationId}));
  }
  return Object.freeze({mode: "source-identity-preview", writesEnabled: false, crmLinked: false,
    summary: Object.freeze(summary), candidates: Object.freeze(candidates)});
}

function route(v) {
  const r = record(v, ["locationId", "contactId", "from", "to", "channel"]);
  str(r.locationId, ID); str(r.contactId, ID); str(r.from, PHONE); str(r.to, PHONE);
  if (r.from === r.to || r.channel !== "whatsapp") throw Error("invalid-route");
  return r;
}
function sameRoute(a, b) { return ["locationId", "contactId", "from", "to", "channel"].every(k => a[k] === b[k]); }
function safetyState(v, r, now) {
  const s = record(v, ["locationId", "contactId", "revision", "observedAt", "paused", "optedOut"]);
  if (s.locationId !== r.locationId || s.contactId !== r.contactId) throw Error("state-identity-mismatch");
  integer(s.revision); integer(s.observedAt);
  if (s.observedAt > now || now - s.observedAt > 5000) throw Error("stale-control-read");
  return {...s, paused: flag(s.paused), optedOut: flag(s.optedOut)};
}
const deny = reason => Object.freeze({decision: "blocked", reason, sendAuthorized: false});
// Eligibility only. Still requires an atomic authorization/lease check in the REAL executor.
function evaluatePilotSafety(input, now) {
  try {
    integer(now);
    const {destination, crm, receiver, policy, draft} = record(input, ["destination", "crm", "receiver", "policy", "draft"]);
    const r = route(destination);
    const p = record(policy, ["enabled", "transport", "singleResponderVerified", "pausePropagationVerified", "allowlist"]);
    if (p.enabled !== true || p.transport !== "highlevel" || p.singleResponderVerified !== true || p.pausePropagationVerified !== true) return deny("pilot-not-ready");
    const list = array(p.allowlist).map(route);
    if (list.filter(x => sameRoute(r, x)).length !== 1) return deny("not-exactly-allowlisted");
    const c = safetyState(crm, r, now), w = safetyState(receiver, r, now);
    if (c.optedOut || w.optedOut) return deny("opted-out");
    if (c.paused || w.paused) return deny("human-pause");
    const d = record(draft, ["crmRevision", "receiverRevision", "inboundAt", "replyToId", "latestInboundId", "dnd"]);
    integer(d.crmRevision); integer(d.receiverRevision); integer(d.inboundAt);
    str(d.replyToId, MESSAGE_ID); str(d.latestInboundId, MESSAGE_ID);
    if (flag(d.dnd)) return deny("provider-dnd");
    if (d.crmRevision !== c.revision || d.receiverRevision !== w.revision) return deny("controls-changed");
    if (d.replyToId !== d.latestInboundId) return deny("superseded-inbound");
    if (d.inboundAt > now || now - d.inboundAt >= 86400000) return deny("outside-reply-window");
    return Object.freeze({decision: "eligible-for-locked-recheck", sendAuthorized: false, requiresAtomicRecheck: true});
  } catch (_) { return deny("invalid-or-unavailable-controls"); }
}

const LEVEL = new Map([["pending", 0], ["sent", 1], ["delivered", 2], ["read", 3]]);
// Provider envelope must be independently verified by an authenticated read adapter.
// Plans a local compare-and-set only. Never changes HighLevel status and NEVER resends.
function planDeliveryReconciliation(local, provider, now) {
  try {
    integer(now);
    const l = record(local, ["destination", "messageId", "conversationId", "bodySha256", "status", "revision"]);
    const p = record(provider, ["destination", "messageId", "conversationId", "bodySha256", "status", "direction", "observedAt", "providerUpdatedAt"]);
    const a = route(l.destination), b = route(p.destination);
    str(l.messageId, ID); str(l.conversationId, ID); integer(l.revision);
    str(l.bodySha256, /^[a-f0-9]{64}$/);
    if (!sameRoute(a, b) || p.messageId !== l.messageId || p.conversationId !== l.conversationId ||
        p.bodySha256 !== l.bodySha256 || p.direction !== "outbound") throw Error("mismatch");
    integer(p.observedAt); integer(p.providerUpdatedAt);
    if (p.observedAt > now || now - p.observedAt > 60000 || p.providerUpdatedAt > p.observedAt) throw Error("stale-evidence");
    if (!LEVEL.has(l.status) || !LEVEL.has(p.status)) throw Error("unhandled-status");
    if (LEVEL.get(p.status) <= LEVEL.get(l.status)) return Object.freeze({action: "keep", resend: false});
    return Object.freeze({action: "reconcile-local-only", expectedRevision: l.revision,
      nextStatus: p.status, providerUpdatedAt: p.providerUpdatedAt, resend: false,
      requiresCompareAndSet: true});
  } catch (_) { return Object.freeze({action: "manual-review", resend: false}); }
}
module.exports = {inspectSourceIdentities, evaluatePilotSafety, planDeliveryReconciliation};
