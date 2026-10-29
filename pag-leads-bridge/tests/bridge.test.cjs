"use strict";
const test = require("node:test");
const assert = require("node:assert/strict");
const { createRecruitmentStatusSnapshot, compareRecruitmentStatus } = require("../bridge.cjs");
const stableId = "r_11111111-2222-4333-8444-555555555555";
const sample = { stableId, status: "Contactado", revision: 2 };

test("projects only non-PII operational fields", () => {
  const row = { ...sample, name: "Private Name", phone: "+19999999999", email: "private@example.test", note: "private note", assignedTo: "uid" };
  const result = createRecruitmentStatusSnapshot(row);
  assert.deepEqual(Object.keys(result), ["schema", "source", "sourceLeadId", "sourceRevision", "status", "idempotencyKey"]);
  assert.equal(result.sourceLeadId, stableId);
  assert.equal(result.sourceRevision, 2);
  assert.equal(result.status, "Contactado");
  for (const privateValue of [row.name, row.phone, row.email, row.note, row.assignedTo]) {
    assert.equal(JSON.stringify(result).includes(privateValue), false);
  }
  assert.equal(Object.isFrozen(result), true);
});

test("stable id + revision gives deterministic idempotency key", () => {
  const a = createRecruitmentStatusSnapshot(sample);
  const b = createRecruitmentStatusSnapshot({ revision: 2, status: "Contactado", stableId });
  assert.equal(a.idempotencyKey, b.idempotencyKey);
  assert.match(a.idempotencyKey, /^[a-f0-9]{64}$/);
});

test("rejects old row indexes, FE identifiers and unknown statuses", () => {
  for (const badId of ["PAG-A-4", "client-123", "r_invalid", ""]) {
    assert.throws(() => createRecruitmentStatusSnapshot({ ...sample, stableId: badId }), /invalid-stable-id/);
  }
  assert.throws(() => createRecruitmentStatusSnapshot({ ...sample, status: "Cerrado" }), /invalid-status/);
});

test("rejects bad revisions", () => {
  for (const revision of [-1, 1.1, "2", Number.MAX_SAFE_INTEGER + 1]) {
    assert.throws(() => createRecruitmentStatusSnapshot({ ...sample, revision }), /invalid-revision/);
  }
});

test("compares new, newer, duplicate and stale updates", () => {
  const rev2 = createRecruitmentStatusSnapshot(sample);
  const rev3 = createRecruitmentStatusSnapshot({ ...sample, status: "Seguimiento", revision: 3 });
  assert.equal(compareRecruitmentStatus(null, rev2), "new");
  assert.equal(compareRecruitmentStatus(rev2, rev3), "newer");
  assert.equal(compareRecruitmentStatus(rev3, rev2), "stale");
  assert.equal(compareRecruitmentStatus(rev2, rev2), "duplicate");
});

test("detects same-revision changes and mismatched identity", () => {
  const rev2 = createRecruitmentStatusSnapshot(sample);
  const mutated = createRecruitmentStatusSnapshot({ ...sample, status: "Cita" });
  const other = createRecruitmentStatusSnapshot({ ...sample, stableId: "r_aaaaaaaa-bbbb-4ccc-8ddd-eeeeeeeeeeee" });
  assert.equal(compareRecruitmentStatus(rev2, mutated), "conflict");
  assert.equal(compareRecruitmentStatus(rev2, other), "invalid-link");
});
