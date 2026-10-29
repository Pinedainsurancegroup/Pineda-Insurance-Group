"use strict";
const test = require("node:test");
const assert = require("node:assert/strict");
const {createRecruitmentStatusSnapshot: make, isRecruitmentStatusSnapshot: valid,
  compareRecruitmentStatus: compare} = require("../bridge.cjs");
const stableId = "r_11111111-2222-4333-8444-555555555555";
const row = {stableId, status: "Nuevo", revision: 0};
const good = make(row);

for (const [label, id] of [
  ["all hyphens", "r_" + "-".repeat(36)],
  ["unseparated hex", "r_" + "a".repeat(36)],
  ["wrong groups", "r_1111111-12222-4333-8444-555555555555"],
  ["uppercase", stableId.toUpperCase()],
  ["trailing newline", stableId + "\n"],
  ["wrong namespace", stableId.replace("r_", "c_")]
]) test(`rejects malformed identifier: ${label}`, () => {
  assert.throws(() => make({...row, stableId: id}), /invalid-stable-id/);
});

for (const [label, incoming] of [["null", null], ["missing", undefined], ["empty object", {}],
  ["missing fields", {schema: good.schema}], ["array", []]]) {
  test(`missing target never accepts invalid incoming: ${label}`, () => {
    assert.equal(compare(null, incoming), "invalid-snapshot");
    assert.equal(compare(good, incoming), "invalid-snapshot");
  });
}

for (const [label, patch] of [["source", {source: "foreign"}], ["schema", {schema: "foreign"}],
  ["key", {idempotencyKey: "0".repeat(64)}], ["revision", {sourceRevision: "0"}],
  ["status", {status: "Hired"}], ["contact data", {phone: "secret-marker"}]]) {
  test(`rejects persisted snapshot corruption: ${label}`, () => {
    const corrupt = {...good, ...patch};
    assert.equal(valid(corrupt), false);
    assert.equal(compare(corrupt, good), "invalid-snapshot");
    assert.equal(compare(null, corrupt), "invalid-snapshot");
  });
}

test("source accessors are not executed", () => {
  let calls = 0;
  const value = {...row};
  Object.defineProperty(value, "status", {get() { calls++; return "Nuevo"; }});
  assert.throws(() => make(value), /invalid-data-field/);
  assert.equal(calls, 0);
});

test("snapshot accessors and symbols are rejected", () => {
  let calls = 0;
  const value = {...good};
  Object.defineProperty(value, "status", {get() { calls++; return "Nuevo"; }});
  assert.equal(valid(value), false);
  assert.equal(calls, 0);
  assert.equal(valid({...good, [Symbol("hidden")]: "secret"}), false);
});

test("inherited objects are rejected; own null-prototype fields work", () => {
  assert.throws(() => make(Object.create(row)), /expected-object/);
  assert.equal(valid(make(Object.assign(Object.create(null), row))), true);
});

test("non-finite, fractional, unsafe and negative-zero revisions are rejected", () => {
  for (const revision of [NaN, Infinity, -Infinity, -0, -1, .5, "0", null, Number.MAX_SAFE_INTEGER + 1]) {
    assert.throws(() => make({...row, revision}), /invalid-revision/);
  }
  assert.equal(valid(make({...row, revision: Number.MAX_SAFE_INTEGER})), true);
});

test("same identity/revision but different state is a conflict, not a second event", () => {
  const changed = make({...row, status: "Seguimiento"});
  assert.equal(changed.idempotencyKey, good.idempotencyKey);
  assert.equal(compare(good, changed), "conflict");
});

test("comparison remains monotonic across 200 deterministic revision pairs", () => {
  for (let revision = 0; revision < 200; revision++) {
    const previous = make({...row, revision});
    const next = make({...row, revision: revision + 1});
    assert.equal(compare(previous, next), "newer");
    assert.equal(compare(next, previous), "stale");
    assert.equal(compare(next, next), "duplicate");
  }
});
