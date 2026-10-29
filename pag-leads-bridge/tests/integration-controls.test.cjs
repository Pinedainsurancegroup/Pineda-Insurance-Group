"use strict";
const test = require("node:test");
const assert = require("node:assert/strict");
const {inspectSourceIdentities: inspect, evaluatePilotSafety: evaluate, planDeliveryReconciliation: plan} = require("../integration-controls.cjs");
const id = n => `r_11111111-2222-3333-4444-${String(n).padStart(12, "0")}`;
function source() {
  return {locationId: "tenant_test", sourceReadComplete: true, sourceIds: ["", id(1), id(2)], highLevelRows: [
    {contactId: "provider_1", sourceLeadId: id(1), importStatus: "IMPORTED"},
    {contactId: "provider_2", sourceLeadId: id(2), importStatus: "IMPORTED"},
    {contactId: "provider_3", sourceLeadId: id(3), importStatus: "IMPORTED"}]};
}
test("source IDs match only explicit HighLevel references, not CRM contacts", () => {
  const r = inspect(source());
  assert.deepEqual(r.summary, {sourceIds: 2, importRows: 3, matched: 2, orphaned: 1, ambiguous: 0, notImported: 0});
  assert.equal(r.crmLinked, false); assert.equal(r.writesEnabled, false);
  assert.ok(r.candidates.every(c => !Object.hasOwn(c, "crmContactId")));
});
for (const kind of ["source", "lead-link", "provider-link"]) test(`duplicate ${kind} is not silently resolved`, () => {
  const x = source();
  if (kind === "source") x.sourceIds.push(id(1));
  if (kind === "lead-link") x.highLevelRows.push({...x.highLevelRows[0], contactId: "other"});
  if (kind === "provider-link") x.highLevelRows[1].contactId = x.highLevelRows[0].contactId;
  const r = inspect(x); assert.ok(r.summary.ambiguous > 0);
  assert.ok(!r.candidates.some(c => c.sourceLeadId === id(1)));
});
test("unconfirmed imports are not mappings or consent", () => {
  const x = source(); x.highLevelRows[0].importStatus = "PENDING";
  const r = inspect(x); assert.equal(r.summary.notImported, 1); assert.equal(r.summary.matched, 1);
});
for (const bad of [null, {}, {sourceIds: []}, {...source(), sourceReadComplete: false}, {...source(), sourceIds: ["PAG-A-2"]}, {...source(), sourceIds: [undefined]}, {...source(), sourceIds: new Array(2)}]) {
  test("incomplete or malformed source is blocked", () => assert.throws(() => inspect(bad)));
}
test("source reader does not leak extra name/phone/email columns", () => {
  const x = source(); Object.assign(x.highLevelRows[0], {name: "Private Person", phone: "secret-phone", email: "private@example.test"});
  const text = JSON.stringify(inspect(x));
  for (const value of ["Private Person", "secret-phone", "private@example.test"]) assert.ok(!text.includes(value));
});
test("source field getters are not executed", () => {
  const x = source(); let ran = false;
  Object.defineProperty(x.highLevelRows[0], "contactId", {get() {ran = true; return "injected";}});
  assert.throws(() => inspect(x)); assert.equal(ran, false);
});
const NOW = 1800000000000;
const route = {locationId: "tenant_test", contactId: "contact_test", from: "+12025550101", to: "+12025550102", channel: "whatsapp"};
function normal() {
  const s = {locationId: route.locationId, contactId: route.contactId, revision: 3, observedAt: NOW, paused: 0, optedOut: 0};
  return {destination: {...route}, crm: {...s}, receiver: {...s},
    policy: {enabled: true, transport: "highlevel", singleResponderVerified: true, pausePropagationVerified: true, allowlist: [{...route}]},
    draft: {crmRevision: 3, receiverRevision: 3, inboundAt: NOW - 10000, replyToId: "wamid.TEST/123=", latestInboundId: "wamid.TEST/123=", dnd: false}};
}
test("eligible candidate is NOT an authorization to send", () => {
  const r = evaluate(normal(), NOW); assert.equal(r.decision, "eligible-for-locked-recheck");
  assert.equal(r.sendAuthorized, false); assert.equal(r.requiresAtomicRecheck, true);
});
for (const origin of ["crm", "receiver"]) {
  test(`${origin} human pause blocks even if the other source says active`, () => {
    const x = normal(); x[origin].paused = 1; assert.equal(evaluate(x, NOW).reason, "human-pause");
  });
  test(`${origin} opt-out blocks even if the other source says opted in`, () => {
    const x = normal(); x[origin].optedOut = true; assert.equal(evaluate(x, NOW).reason, "opted-out");
  });
  for (const missing of ["paused", "optedOut", "revision", "observedAt"]) test(`${origin} missing ${missing} fails closed`, () => {
    const x = normal(); delete x[origin][missing]; assert.equal(evaluate(x, NOW).decision, "blocked");
  });
}
for (const change of [
  x => x.policy.enabled = false,
  x => x.policy.enabled = "true",
  x => x.policy.transport = "meta",
  x => x.policy.singleResponderVerified = false,
  x => x.policy.pausePropagationVerified = false,
  x => x.policy.allowlist = [],
  x => x.policy.allowlist.push({...route}),
  x => x.policy.allowlist[0].contactId = "other",
  x => x.policy.allowlist[0].locationId = "other",
  x => x.policy.allowlist[0].to = "+13025550102",
  x => x.crm.contactId = "other",
  x => x.crm.observedAt = NOW - 5001,
  x => x.receiver.observedAt = NOW + 1,
  x => x.crm.paused = "false",
  x => x.draft.dnd = true,
  x => x.draft.dnd = undefined,
  x => x.draft.crmRevision = 2,
  x => x.draft.receiverRevision = 2,
  x => x.draft.latestInboundId = "newer",
  x => x.draft.inboundAt = NOW - 86400000,
  x => x.draft.inboundAt = NOW + 1
]) test("unsafe or stale pilot input remains blocked", () => {
  const x = normal(); change(x); const r = evaluate(x, NOW); assert.equal(r.decision, "blocked"); assert.equal(r.sendAuthorized, false);
});
test("untrusted getters are not executed by send gate", () => {
  const x = normal(); let ran = false;
  Object.defineProperty(x.crm, "paused", {get() {ran = true; return false;}});
  assert.equal(evaluate(x, NOW).decision, "blocked"); assert.equal(ran, false);
});
function delivery() {
  const common = {destination: {...route}, messageId: "message_test", conversationId: "thread_test", bodySha256: "a".repeat(64)};
  return [{...common, status: "pending", revision: 7}, {...common, destination: {...route}, status: "delivered", direction: "outbound", observedAt: NOW, providerUpdatedAt: NOW - 10000}];
}
test("delivered pending message is reconciled, NEVER resent; no invented acceptance time", () => {
  const [l, p] = delivery(); const r = plan(l, p, NOW);
  assert.equal(r.action, "reconcile-local-only"); assert.equal(r.nextStatus, "delivered");
  assert.equal(r.expectedRevision, 7); assert.equal(r.resend, false); assert.equal(r.requiresCompareAndSet, true);
  assert.ok(!Object.hasOwn(r, "acceptedAt"));
});
for (const status of ["delivered", "read"]) test(`do not downgrade ${status} to older provider evidence`, () => {
  const [l, p] = delivery(); l.status = status; p.status = "sent"; assert.equal(plan(l, p, NOW).action, "keep");
});
for (const key of ["messageId", "conversationId", "bodySha256", "direction"]) test(`provider mismatch ${key} blocks reconciliation`, () => {
  const [l, p] = delivery(); p[key] = "wrong"; assert.deepEqual(plan(l, p, NOW), {action: "manual-review", resend: false});
});
for (const key of ["locationId", "contactId", "from", "to", "channel"]) test(`provider route mismatch ${key} blocks reconciliation`, () => {
  const [l, p] = delivery(); p.destination[key] = "wrong"; assert.equal(plan(l, p, NOW).action, "manual-review");
});
for (const change of [p => p.status = "unknown", p => p.observedAt = NOW - 60001, p => p.providerUpdatedAt = NOW + 1]) test("unknown or stale delivery evidence stays manual", () => {
  const [l, p] = delivery(); change(p); assert.equal(plan(l, p, NOW).action, "manual-review");
});
test("acknowledged sent is not promoted to delivered", () => {
  const [l, p] = delivery(); p.status = "sent"; assert.equal(plan(l, p, NOW).nextStatus, "sent");
});
test("a repeated provider delivery observation is a no-op", () => {
  const [l, p] = delivery(); l.status = "delivered"; assert.equal(plan(l, p, NOW).action, "keep");
});
