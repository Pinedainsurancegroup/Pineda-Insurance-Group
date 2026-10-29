"use strict";
const test = require("node:test");
const assert = require("node:assert/strict");
const {runReadOnlyAudit} = require("../audit.cjs");
const {createRecruitmentStatusSnapshot: snapshot} = require("../bridge.cjs");
const NOW = Date.parse("2026-10-29T20:00:00.000Z"), SCOPE = "synthetic-scope";
const A = "r_11111111-2222-4333-8444-555555555555";
const B = "r_aaaaaaaa-bbbb-4ccc-8ddd-eeeeeeeeeeee";
const C = "r_99999999-8888-4777-8666-555555555555";
const row = (stableId = A, revision = 2) => ({stableId, status: "Contactado", revision});
const link = (sourceLeadId = A, crmContactId = "fake-contact-A") =>
  ({sourceLeadId, crmContactId, module: "recruitment", verified: true, enabled: true});
function fixture() {
  const calls = [], access = {scopeId: SCOPE, active: true, readOnly: true,
    recruitment: true, expiresAt: NOW + 60000};
  const data = {sourceRows: [row()], links: [link()],
    projections: [{crmContactId: "fake-contact-A", snapshot: snapshot(row(A, 1))}]};
  const page = items => ({items, nextCursor: null, snapshotId: "synthetic-snapshot",
    capturedAt: new Date(NOW).toISOString(), scopeId: SCOPE});
  const adapter = {authorize: async args => { calls.push({kind: "authorize", args}); return {...access}; }};
  for (const kind of Object.keys(data)) adapter[kind] = async args => {
    calls.push({kind, args}); return page(data[kind]);
  };
  const input = {adapter, selection: [A], expectedScope: SCOPE, now: () => NOW};
  return {calls, access, data, page, adapter, input};
}
const blocked = (report, reason) => {
  assert.equal(report.decision, "blocked"); assert.equal(report.reason, reason);
  assert.equal(report.writesEnabled, false); assert.equal(report.messagesEnabled, false);
  assert.equal(report.productionApproved, false); assert.equal(report.summary, undefined);
};

test("audit reads a bounded selection and returns counts, not identifiers", async () => {
  const f = fixture(), result = await runReadOnlyAudit(f.input);
  assert.equal(result.decision, "ready-for-human-review");
  assert.equal(result.summary["candidate-newer"], 1);
  assert.equal(result.accessChecks, 4);
  assert.deepEqual(result.pages, {sourceRows: 1, links: 1, projections: 1});
  assert.deepEqual(result.counts, {selected: 1, sourceRows: 1, links: 1, projections: 1});
  assert.equal(result.productionApproved, false);
  assert.equal(result.consistency, "per-reader-snapshot-not-cross-system-transaction");
  for (const value of [A, SCOPE, "fake-contact-A", "synthetic-snapshot"]) assert.equal(JSON.stringify(result).includes(value), false);
  for (const call of f.calls.filter(c => c.kind !== "authorize")) {
    assert.deepEqual(call.args.selection, [A]); assert.equal(call.args.limit, 100);
    assert.ok(Object.isFrozen(call.args.selection)); assert.ok(call.args.signal.aborted);
  }
});

test("audit follows pages without missing selected rows", async () => {
  const f = fixture(); f.input.selection.push(B);
  f.data.links.push(link(B, "fake-contact-B"));
  f.adapter.sourceRows = async args => ({...f.page([row(args.cursor ? B : A)]), nextCursor: args.cursor ? null : "page-2"});
  const r = await runReadOnlyAudit(f.input);
  assert.equal(r.pages.sourceRows, 2); assert.equal(r.counts.sourceRows, 2);
  assert.equal(r.summary["candidate-new"], 1); assert.equal(r.summary["candidate-newer"], 1);
});

for (const [name, change] of [
  ["suspended", a => a.active = false], ["wrong scope", a => a.scopeId = "wrong"],
  ["not read-only", a => a.readOnly = false], ["wrong module", a => a.recruitment = false],
  ["expired", a => a.expiresAt = NOW], ["missing field", a => delete a.active],
  ["unexpected field", a => a.token = "private-secret"]
]) test(`access fails closed: ${name}`, async () => {
  const f = fixture(); change(f.access);
  blocked(await runReadOnlyAudit(f.input), "access-denied");
  assert.equal(f.calls.filter(c => c.kind !== "authorize").length, 0);
});

test("revocation between pages stops before subsequent data reads", async () => {
  const f = fixture(); const original = f.adapter.sourceRows;
  f.adapter.sourceRows = async args => { const page = await original(args); f.access.active = false; return page; };
  blocked(await runReadOnlyAudit(f.input), "access-denied");
  assert.deepEqual(f.calls.filter(c => c.kind !== "authorize").map(c => c.kind), ["sourceRows"]);
});

test("revocation after last reader prevents a successful report", async () => {
  const f = fixture(), original = f.adapter.projections;
  f.adapter.projections = async args => { const page = await original(args); f.access.active = false; return page; };
  blocked(await runReadOnlyAudit(f.input), "access-denied");
});

test("underlying access and reader errors never leak their contents", async () => {
  for (const kind of ["authorize", "sourceRows"]) {
    const f = fixture(); f.adapter[kind] = async () => { throw Error("token-secret personal@example.test"); };
    const r = await runReadOnlyAudit(f.input);
    blocked(r, kind === "authorize" ? "access-check-failed" : "reader-failed");
    assert.equal(JSON.stringify(r).includes("token-secret"), false);
    assert.equal(JSON.stringify(r).includes("personal@example.test"), false);
  }
});

test("timeout aborts a stalled reader without proceeding to another source", async () => {
  const f = fixture(); let signal;
  f.input.options = {timeoutMs: 10};
  f.adapter.sourceRows = args => { signal = args.signal; return new Promise(() => {}); };
  blocked(await runReadOnlyAudit(f.input), "audit-timeout");
  assert.equal(signal.aborted, true); assert.equal(f.calls.some(c => c.kind === "links"), false);
});

test("a late reader result cannot resume the pipeline after timeout", async () => {
  const f = fixture(); let finish;
  f.input.options = {timeoutMs: 10};
  f.adapter.sourceRows = () => new Promise(resolve => { finish = resolve; });
  blocked(await runReadOnlyAudit(f.input), "audit-timeout");
  finish(f.page([row()]));
  await new Promise(resolve => setImmediate(resolve));
  assert.equal(f.calls.some(c => c.kind === "links"), false);
});

for (const [name, change, reason] of [
  ["scope", p => p.scopeId = "other-account", "scope-mismatch"],
  ["stale", p => p.capturedAt = new Date(NOW - 300001).toISOString(), "stale-or-invalid-observation"],
  ["future", p => p.capturedAt = new Date(NOW + 5001).toISOString(), "stale-or-invalid-observation"],
  ["date format", p => p.capturedAt = "yesterday", "stale-or-invalid-observation"],
  ["metadata", p => p.debug = "private", "invalid-page"],
  ["cursor", p => p.nextCursor = "", "invalid-page"],
  ["rows type", p => p.items = {}, "invalid-page"],
  ["sparse rows", p => p.items = new Array(1), "invalid-row"],
  ["private field", p => p.items[0].email = "private@example.test", "invalid-row"],
  ["outside selection", p => p.items = [row(C)], "out-of-scope-record"]
]) test(`rejects invalid page: ${name}`, async () => {
  const f = fixture(); f.adapter.sourceRows = async () => { const p = f.page([row()]); change(p); return p; };
  blocked(await runReadOnlyAudit(f.input), reason);
});

test("repeated cursor is blocked, not treated as a completed export", async () => {
  const f = fixture(); f.adapter.sourceRows = async () => ({...f.page([row()]), nextCursor: "same"});
  blocked(await runReadOnlyAudit(f.input), "cursor-cycle");
});

test("a changed snapshot or captured time between pages blocks the batch", async () => {
  for (const field of ["snapshotId", "capturedAt"]) {
    const f = fixture(); let n = 0;
    f.adapter.sourceRows = async () => {
      const p = {...f.page([row()]), nextCursor: n++ ? null : "next"};
      if (n > 1) p[field] = field === "snapshotId" ? "changed" : new Date(NOW - 1).toISOString();
      return p;
    };
    blocked(await runReadOnlyAudit(f.input), "snapshot-changed");
  }
});

test("row limit does not return a successful partial audit", async () => {
  const f = fixture(); f.input.options = {maxRows: 1};
  f.adapter.sourceRows = async () => f.page([row(), row()]);
  blocked(await runReadOnlyAudit(f.input), "row-limit");
});

test("page and page-size limits stop oversized exports", async () => {
  const f = fixture(); f.input.options = {maxPages: 1};
  f.adapter.sourceRows = async () => ({...f.page([row()]), nextCursor: "next"});
  blocked(await runReadOnlyAudit(f.input), "page-limit");
  f.input.options = {pageSize: 1}; f.adapter.sourceRows = async () => f.page([row(), row()]);
  blocked(await runReadOnlyAudit(f.input), "invalid-page");
});

test("missing selected source is not reported as zero successful records", async () => {
  const f = fixture(); f.data.sourceRows = [];
  blocked(await runReadOnlyAudit(f.input), "incomplete-selection");
});

test("out-of-scope links and projections block the batch", async () => {
  for (const kind of ["links", "projections"]) {
    const f = fixture(); f.data[kind] = kind === "links" ? [link(C)] : [{crmContactId: "other", snapshot: snapshot(row(C))}];
    blocked(await runReadOnlyAudit(f.input), "out-of-scope-record");
  }
});

test("malformed registries and Final Expense entries are blocked", async () => {
  const f = fixture(); f.data.links[0].module = "clients";
  blocked(await runReadOnlyAudit(f.input), "invalid-row");
  f.data.links[0].module = "recruitment"; f.data.projections[0].snapshot = {};
  blocked(await runReadOnlyAudit(f.input), "invalid-row");
});

test("unlinked, disabled and conflicting data are routed to human review", async () => {
  for (const scenario of ["unlinked", "link-disabled", "conflict", "stale"]) {
    const f = fixture();
    if (scenario === "unlinked") f.data.links = [];
    if (scenario === "link-disabled") f.data.links[0].enabled = false;
    if (scenario === "conflict") f.data.projections[0].snapshot = snapshot({...row(), status: "Cita"});
    if (scenario === "stale") f.data.projections[0].snapshot = snapshot(row(A, 3));
    const r = await runReadOnlyAudit(f.input);
    assert.equal(r.decision, "needs-review"); assert.equal(r.summary[scenario], 1);
    assert.equal(r.productionApproved, false);
  }
});

test("invalid configuration blocks before any authorization or data reads", async () => {
  for (const alter of [
    f => f.input.selection = [], f => f.input.selection = [A, A],
    f => f.input.selection = ["PAG-A-1"], f => f.input.selection = new Array(1),
    f => f.input.selection = Array(101).fill(A),
    f => f.input.options = {maxRows: 1001}, f => f.input.options = {timeoutMs: 0},
    f => f.input.options = {writesEnabled: true}, f => delete f.adapter.links,
    f => f.input.expectedScope = "https://untrusted.test", f => f.input.options = null
  ]) {
    const f = fixture(); alter(f);
    assert.equal((await runReadOnlyAudit(f.input)).decision, "blocked"); assert.equal(f.calls.length, 0);
  }
});

test("captured data is checked for freshness again before report", async () => {
  const f = fixture(); let n = 0, clock = NOW;
  const original = f.adapter.authorize;
  f.adapter.authorize = async args => {
    if (++n === 4) clock = NOW + 300001;
    return original(args);
  };
  f.input.now = () => clock;
  f.access.expiresAt = NOW + 600000;
  blocked(await runReadOnlyAudit(f.input), "stale-or-invalid-observation");
});

test("undefined input is a blocked audit", async () => {
  assert.equal((await runReadOnlyAudit()).decision, "blocked");
});


test("null and privileged adapter surfaces are rejected", async () => {
  blocked(await runReadOnlyAudit(null), "invalid-input");
  const f = fixture(); f.adapter.write = async () => assert.fail("must never run");
  blocked(await runReadOnlyAudit(f.input), "invalid-adapter");
  assert.equal(f.calls.length, 0);
});

test("input accessors cannot activate side effects", async () => {
  const input = {};
  Object.defineProperty(input, "adapter", {get() { assert.fail("must not invoke accessor"); }});
  blocked(await runReadOnlyAudit(input), "invalid-input");
});
