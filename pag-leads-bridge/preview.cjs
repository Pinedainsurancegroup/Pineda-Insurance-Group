"use strict";

// Offline reconciliation preview, not a live CRM adapter or authorization service.
// Callers must supply authorized exports; verified link flags are assertions only.
const {createRecruitmentStatusSnapshot: snapshot, isRecruitmentStatusSnapshot: valid,
  compareRecruitmentStatus: compare} = require("./bridge.cjs");
const MAX_ROWS = 1000;
const CONTACT_ID = /^[A-Za-z0-9][A-Za-z0-9_-]{0,127}$/;
const LINK_KEYS = ["sourceLeadId", "crmContactId", "module", "verified", "enabled"];
const PROJECTION_KEYS = ["crmContactId", "snapshot"];
const OUTCOMES = ["candidate-new", "candidate-newer", "duplicate", "stale", "conflict",
  "unlinked", "link-disabled", "ambiguous-link", "duplicate-source", "invalid-source", "invalid-link"];

function exactObject(value, keys) {
  if (!value || typeof value !== "object" || Array.isArray(value) ||
      ![Object.prototype, null].includes(Object.getPrototypeOf(value))) return false;
  return Reflect.ownKeys(value).length === keys.length && keys.every(key => {
    const d = Object.getOwnPropertyDescriptor(value, key);
    return d && Object.hasOwn(d, "value");
  });
}

function boundedArray(value) {
  if (!Array.isArray(value) || value.length > MAX_ROWS) throw new TypeError("invalid-preview-batch");
  // A sparse export must not silently lose records through Array.map.
  for (let i = 0; i < value.length; i++) if (!Object.hasOwn(value, i)) throw new TypeError("invalid-preview-batch");
}

function indexBy(items, key) {
  const map = new Map();
  for (const item of items) {
    const id = item[key];
    if (!map.has(id)) map.set(id, []);
    map.get(id).push(item);
  }
  return map;
}

function createReconciliationPreview(bundle) {
  if (!exactObject(bundle, ["sourceRows", "links", "projections"])) throw new TypeError("invalid-preview-bundle");
  const {sourceRows, links, projections} = bundle;
  [sourceRows, links, projections].forEach(boundedArray);
  // Invalid trusted-side metadata stops the batch. Errors never echo input values.
  for (const link of links) {
    if (!exactObject(link, LINK_KEYS) || typeof link.crmContactId !== "string" ||
        !CONTACT_ID.test(link.crmContactId) || link.module !== "recruitment" ||
        typeof link.verified !== "boolean" || typeof link.enabled !== "boolean") throw new TypeError("invalid-link-registry");
    try { snapshot({stableId: link.sourceLeadId, status: "Nuevo", revision: 0}); }
    catch (_) { throw new TypeError("invalid-link-registry"); }
  }
  for (const item of projections) {
    if (!exactObject(item, PROJECTION_KEYS) || typeof item.crmContactId !== "string" ||
        !CONTACT_ID.test(item.crmContactId) || !valid(item.snapshot)) throw new TypeError("invalid-projection-registry");
  }
  const byLead = indexBy(links, "sourceLeadId");
  const byContact = indexBy(links, "crmContactId");
  const current = indexBy(projections, "crmContactId");
  const currentByLead = indexBy(projections.map(item => ({sourceLeadId: item.snapshot.sourceLeadId, ...item})), "sourceLeadId");
  const incoming = sourceRows.map(row => {
    try { return snapshot(row); } catch (_) { return null; }
  });
  const sourceCounts = indexBy(incoming.filter(Boolean), "sourceLeadId");
  const summary = Object.fromEntries(OUTCOMES.map(outcome => [outcome, 0]));
  const records = incoming.map((item, rowIndex) => {
    let outcome = "invalid-source", crmContactId;
    if (item) {
      const matches = byLead.get(item.sourceLeadId) || [];
      if (sourceCounts.get(item.sourceLeadId).length !== 1) outcome = "duplicate-source";
      else if (matches.length === 0) outcome = "unlinked";
      else if (matches.length !== 1) outcome = "ambiguous-link";
      else {
        const link = matches[0];
        const previous = current.get(link.crmContactId) || [];
        const previousForLead = currentByLead.get(item.sourceLeadId) || [];
        if (byContact.get(link.crmContactId).length !== 1 || previous.length > 1 || previousForLead.length > 1) outcome = "ambiguous-link";
        else if (!link.enabled || !link.verified) outcome = "link-disabled";
        else if (previousForLead.length === 1 && previousForLead[0].crmContactId !== link.crmContactId) outcome = "invalid-link";
        else {
          const comparison = compare(previous[0]?.snapshot, item);
          outcome = comparison === "new" ? "candidate-new" : comparison === "newer" ? "candidate-newer" : comparison;
          if (!OUTCOMES.includes(outcome)) throw new TypeError("invalid-preview-state");
          if (outcome === "candidate-new" || outcome === "candidate-newer") crmContactId = link.crmContactId;
        }
      }
    }
    summary[outcome]++;
    // Never return source names, contact details, notes, raw rows or exceptions.
    return Object.freeze({rowIndex, outcome, ...(item ? {sourceLeadId: item.sourceLeadId} : {}),
      ...(crmContactId ? {crmContactId, proposedSnapshot: item} : {})});
  });
  return Object.freeze({mode: "preview", writesEnabled: false, messagesEnabled: false,
    summary: Object.freeze(summary), records: Object.freeze(records)});
}

module.exports = {createReconciliationPreview};
