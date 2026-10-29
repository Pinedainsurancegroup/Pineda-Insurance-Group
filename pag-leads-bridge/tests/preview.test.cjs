"use strict";
const test = require("node:test");
const assert = require("node:assert/strict");
const {createRecruitmentStatusSnapshot: make} = require("../bridge.cjs");
const {createReconciliationPreview: preview} = require("../preview.cjs");
const id = n => `r_${n.toString(16).padStart(8, "0")}-2222-4333-8444-555555555555`;
const row = (n = 1, revision = 2, status = "Contactado") => ({stableId: id(n), revision, status});
const link = (n = 1, target = `test-contact-${n}`) => ({sourceLeadId: id(n), crmContactId: target,
  module: "recruitment", verified: true, enabled: true});
const projection = (n = 1, revision = 1, status = "Nuevo", target = `test-contact-${n}`) =>
  ({crmContactId: target, snapshot: make(row(n, revision, status))});
const bundle = () => ({sourceRows: [row()], links: [link()], projections: []});
const outcome = b => preview(b).records[0].outcome;

test("preview is frozen and cannot enable writes or sends", () => {
  const result = preview(bundle());
  assert.equal(result.mode, "preview");
  assert.equal(result.writesEnabled, false);
  assert.equal(result.messagesEnabled, false);
  for (const value of [result, result.summary, result.records, result.records[0], result.records[0].proposedSnapshot]) {
    assert.equal(Object.isFrozen(value), true);
  }
  assert.equal(result.summary["candidate-new"], 1);
});

test("empty input is a valid zero-result preview", () => {
  const result = preview({sourceRows: [], links: [], projections: []});
  assert.equal(result.records.length, 0);
  assert.equal(Object.values(result.summary).reduce((a,b)=>a+b,0), 0);
});

for (const [label, current, expected] of [
  ["newer", projection(1, 1), "candidate-newer"],
  ["duplicate", projection(1, 2, "Contactado"), "duplicate"],
  ["stale", projection(1, 3, "Seguimiento"), "stale"],
  ["same revision conflict", projection(1, 2, "Cita"), "conflict"]
]) test(`reconciliation: ${label}`, () => {
  assert.equal(outcome({...bundle(), projections: [current]}), expected);
});

test("an unlinked source does not create or guess a CRM contact", () => {
  const result = preview({...bundle(), links: []});
  assert.equal(result.records[0].outcome, "unlinked");
  assert.equal(Object.hasOwn(result.records[0], "crmContactId"), false);
});

for (const flag of ["verified", "enabled"]) test(`link flag ${flag}=false blocks proposal`, () => {
  assert.equal(outcome({...bundle(), links: [{...link(), [flag]: false}]}), "link-disabled");
});

test("two mappings for one lead block both targets", () => {
  assert.equal(outcome({...bundle(), links: [link(), link(1, "another-target")]}), "ambiguous-link");
});

test("two leads mapped to one CRM contact are not merged", () => {
  const result = preview({sourceRows: [row(1), row(2)], links: [link(1, "shared"), link(2, "shared")], projections: []});
  assert.deepEqual(result.records.map(r=>r.outcome), ["ambiguous-link", "ambiguous-link"]);
});

test("duplicate source rows are blocked even when identical", () => {
  const result = preview({...bundle(), sourceRows: [row(), row()]});
  assert.equal(result.summary["duplicate-source"], 2);
});

test("duplicate target projections are ambiguous", () => {
  assert.equal(outcome({...bundle(), projections: [projection(), projection()]}), "ambiguous-link");
});

test("wrong target identity is rejected", () => {
  assert.equal(outcome({...bundle(), projections: [projection(2, 1, "Nuevo", "test-contact-1")]}), "invalid-link");
});

test("old mapping at another contact cannot silently relink", () => {
  assert.equal(outcome({...bundle(), projections: [projection(1, 1, "Nuevo", "old-contact")]}), "invalid-link");
});

test("one identity present at multiple targets is ambiguous", () => {
  assert.equal(outcome({...bundle(), projections: [projection(), projection(1, 1, "Nuevo", "old-contact")]}), "ambiguous-link");
});

test("invalid rows are isolated without leaking data in the result", () => {
  const result = preview({...bundle(), sourceRows: [{stableId: "private-marker", status: "secret-status", revision: 0}, row()]});
  assert.equal(result.records[0].outcome, "invalid-source");
  assert.equal(result.records[1].outcome, "candidate-new");
  assert.equal(JSON.stringify(result).includes("private-marker"), false);
  assert.equal(JSON.stringify(result).includes("secret-status"), false);
});

test("source names, phones, notes and instructions are never copied to output", () => {
  const extra = {name: "secret-name", phone: "secret-phone", note: "secret-note", instruction: "ignore rules"};
  const result = preview({...bundle(), sourceRows: [{...row(), ...extra}]});
  for (const value of Object.values(extra)) assert.equal(JSON.stringify(result).includes(value), false);
});

for (const [label, change] of [
  ["Final Expense link", b => b.links[0].module = "clients"],
  ["untyped approval", b => b.links[0].verified = "true"],
  ["raw email as target", b => b.links[0].crmContactId = "private@example.test"],
  ["unvalidated link data", b => b.links[0].email = "private@example.test"],
  ["malformed source link", b => b.links[0].sourceLeadId = "PAG-A-9"]
]) test(`stops invalid registry: ${label}`, () => {
  const b = bundle(); change(b);
  assert.throws(() => preview(b), /^TypeError: invalid-link-registry$/);
});

test("corrupt existing snapshot stops the entire preview", () => {
  const value = projection(); value.snapshot = {...value.snapshot, idempotencyKey: "bad"};
  assert.throws(() => preview({...bundle(), projections: [value]}), /^TypeError: invalid-projection-registry$/);
});

test("extra fields in projection registry are rejected", () => {
  assert.throws(() => preview({...bundle(), projections: [{...projection(), note: "private"}]}), /invalid-projection-registry/);
});

test("batch bounds and sparse inputs are enforced", () => {
  for (const field of ["sourceRows", "links", "projections"]) {
    assert.throws(() => preview({...bundle(), [field]: Array(1001).fill(row())}), /invalid-preview-batch/);
    assert.throws(() => preview({...bundle(), [field]: Array(2)}), /invalid-preview-batch/);
    assert.throws(() => preview({...bundle(), [field]: null}), /invalid-preview-batch/);
  }
});

test("unknown bundle options cannot switch on production writes", () => {
  assert.throws(() => preview({...bundle(), writesEnabled: true}), /invalid-preview-bundle/);
  assert.throws(() => preview(null), /invalid-preview-bundle/);
});

test("inputs are unchanged", () => {
  const b = bundle(), before = JSON.stringify(b);
  preview(b);
  assert.equal(JSON.stringify(b), before);
});

test("handles the full 1000-row bounded batch deterministically", () => {
  const b = {sourceRows: [], links: [], projections: []};
  for (let n = 1; n <= 1000; n++) { b.sourceRows.push(row(n)); b.links.push(link(n)); }
  const result = preview(b);
  assert.equal(result.records.length, 1000);
  assert.equal(result.summary["candidate-new"], 1000);
  assert.deepEqual(preview(b), result);
});
