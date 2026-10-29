"use strict";

// Read-only orchestration over TRUSTED, server-owned adapters. No HTTP client,
// credentials, writes, messages, schedules, or built-in authentication.
const {createRecruitmentStatusSnapshot: snapshot} = require("./bridge.cjs");
const {createReconciliationPreview: preview} = require("./preview.cjs");
const READERS = ["sourceRows", "links", "projections"];
const PAGE_KEYS = ["items", "nextCursor", "snapshotId", "capturedAt", "scopeId"];
const ACCESS_KEYS = ["scopeId", "active", "readOnly", "recruitment", "expiresAt"];
const ROW_KEYS = {
  sourceRows: ["stableId", "status", "revision"],
  links: ["sourceLeadId", "crmContactId", "module", "verified", "enabled"],
  projections: ["crmContactId", "snapshot"]
};
const REVIEW = ["conflict", "unlinked", "link-disabled", "ambiguous-link",
  "duplicate-source", "invalid-source", "invalid-link", "stale"];
const DEFAULTS = {pageSize: 100, maxPages: 10, maxRows: 1000, timeoutMs: 10000, maxAgeMs: 300000};
const BOUNDS = {pageSize: [1, 100], maxPages: [1, 20], maxRows: [1, 1000],
  timeoutMs: [5, 30000], maxAgeMs: [1000, 300000]};
class AuditError extends Error {}
function stop(code) { throw new AuditError(code); }
function record(value) {
  return !!value && typeof value === "object" && !Array.isArray(value) &&
    [Object.prototype, null].includes(Object.getPrototypeOf(value));
}
function exact(value, keys) {
  if (!record(value) || Reflect.ownKeys(value).length !== keys.length) return false;
  return keys.every(key => {
    const d = Object.getOwnPropertyDescriptor(value, key);
    return d && Object.hasOwn(d, "value");
  });
}
function text(value, max = 256) {
  return typeof value === "string" && value.length > 0 && value.length <= max;
}
function isoTime(value) {
  if (typeof value !== "string") return NaN;
  const n = Date.parse(value);
  return Number.isFinite(n) && new Date(n).toISOString() === value ? n : NaN;
}
function active(signal) { if (signal.aborted) stop("audit-timeout"); }
function limits(input) {
  if (!record(input)) stop("invalid-options");
  const out = {...DEFAULTS};
  for (const key of Reflect.ownKeys(input)) {
    const d = Object.getOwnPropertyDescriptor(input, key);
    if (!Object.hasOwn(BOUNDS, key) || !d || !Object.hasOwn(d, "value")) stop("invalid-options");
    const n = d.value;
    if (!Number.isSafeInteger(n) || n < BOUNDS[key][0] || n > BOUNDS[key][1]) stop("invalid-options");
    out[key] = n;
  }
  return out;
}
function selectionIds(input) {
  if (!Array.isArray(input) || input.length === 0 || input.length > 100) stop("invalid-selection");
  const ids = [];
  for (let i = 0; i < input.length; i++) {
    const d = Object.getOwnPropertyDescriptor(input, i);
    if (!d || !Object.hasOwn(d, "value")) stop("invalid-selection");
    try { snapshot({stableId: d.value, status: "Nuevo", revision: 0}); }
    catch (_) { stop("invalid-selection"); }
    ids.push(d.value);
  }
  if (new Set(ids).size !== ids.length) stop("invalid-selection");
  return Object.freeze(ids);
}

async function runReadOnlyAudit(input = {}) {
  const base = {mode: "read-only-audit", writesEnabled: false, messagesEnabled: false,
    productionApproved: false, evidence: "adapter-observations-not-authentication-certificate"};
  let controller, timer;
  try {
    const keys = ["adapter", "selection", "expectedScope", "options", "now"];
    if (!record(input) || Reflect.ownKeys(input).some(key => {
      const d = Object.getOwnPropertyDescriptor(input, key);
      return !keys.includes(key) || !d || !Object.hasOwn(d, "value");
    })) stop("invalid-input");
    const {adapter, selection, expectedScope, options = {}, now = Date.now} = input;
    const cfg = limits(options), ids = selectionIds(selection), allowed = new Set(ids);
    if (!text(expectedScope, 128) || !/^[A-Za-z0-9_-]+$/.test(expectedScope) ||
        !exact(adapter, ["authorize", ...READERS]) || typeof adapter.authorize !== "function" ||
        READERS.some(key => typeof adapter[key] !== "function") || typeof now !== "function") stop("invalid-adapter");
    controller = new AbortController();
    const signal = controller.signal;
    const getTime = () => { const n = now(); if (!Number.isSafeInteger(n) || n < 0) stop("invalid-clock"); return n; };
    let accessChecks = 0;
    const authorize = async () => {
      active(signal);
      let access;
      try { access = await adapter.authorize(Object.freeze({expectedScope, signal})); }
      catch (_) { active(signal); stop("access-check-failed"); }
      active(signal);
      if (!exact(access, ACCESS_KEYS) || access.scopeId !== expectedScope || access.active !== true ||
          access.readOnly !== true || access.recruitment !== true ||
          !Number.isSafeInteger(access.expiresAt) || access.expiresAt <= getTime()) stop("access-denied");
      accessChecks++;
    };
    const pageCounts = {};
    const captureTimes = [];
    const read = async kind => {
      let cursor = null, snapshotId, capturedAt;
      const seen = new Set(), rows = [];
      pageCounts[kind] = 0;
      do {
        if (pageCounts[kind] >= cfg.maxPages) stop("page-limit");
        await authorize();
        let page;
        try { page = await adapter[kind](Object.freeze({selection: ids, cursor, limit: cfg.pageSize, signal})); }
        catch (_) { active(signal); stop("reader-failed"); }
        active(signal);
        if (!exact(page, PAGE_KEYS) || !Array.isArray(page.items) || page.items.length > cfg.pageSize ||
            !text(page.snapshotId) || (page.nextCursor !== null && !text(page.nextCursor, 512))) stop("invalid-page");
        if (page.scopeId !== expectedScope) stop("scope-mismatch");
        const captured = isoTime(page.capturedAt), currentTime = getTime();
        if (!Number.isFinite(captured) || captured > currentTime + 5000 || currentTime - captured > cfg.maxAgeMs) stop("stale-or-invalid-observation");
        if (snapshotId !== undefined && (page.snapshotId !== snapshotId || page.capturedAt !== capturedAt)) stop("snapshot-changed");
        snapshotId = page.snapshotId; capturedAt = page.capturedAt;
        if (rows.length + page.items.length > cfg.maxRows) stop("row-limit");
        for (let i = 0; i < page.items.length; i++) {
          const d = Object.getOwnPropertyDescriptor(page.items, i);
          if (!d || !Object.hasOwn(d, "value") || !exact(d.value, ROW_KEYS[kind])) stop("invalid-row");
          const item = d.value;
          // Validate registry/snapshot structure before consulting its identity.
          try { preview({sourceRows: [], links: kind === "links" ? [item] : [],
            projections: kind === "projections" ? [item] : []}); }
          catch (_) { stop("invalid-row"); }
          let sourceId;
          try { sourceId = kind === "sourceRows" ? snapshot(item).sourceLeadId :
            kind === "links" ? item.sourceLeadId : item.snapshot.sourceLeadId; }
          catch (_) { stop("invalid-row"); }
          if (!allowed.has(sourceId)) stop("out-of-scope-record");
          // Copy normalized JSON so a trusted adapter cannot accidentally mutate
          // a previous page while retrieving subsequent pages.
          rows.push(JSON.parse(JSON.stringify(item)));
        }
        pageCounts[kind]++;
        cursor = page.nextCursor;
        if (cursor !== null) {
          if (seen.has(cursor)) stop("cursor-cycle");
          seen.add(cursor);
        }
      } while (cursor !== null);
      captureTimes.push(isoTime(capturedAt));
      return rows;
    };
    const work = async () => {
      const bundle = {};
      for (const kind of READERS) bundle[kind] = await read(kind);
      await authorize();
      // Missing requested leads must not be reported as an empty successful audit.
      const observed = new Set(bundle.sourceRows.map(item => item.stableId));
      if (ids.some(id => !observed.has(id))) stop("incomplete-selection");
      const finishedAt = getTime();
      if (captureTimes.some(t => finishedAt - t > cfg.maxAgeMs)) stop("stale-or-invalid-observation");
      const result = preview(bundle);
      active(signal);
      return Object.freeze({...base,
        decision: REVIEW.some(key => result.summary[key] > 0) ? "needs-review" : "ready-for-human-review",
        consistency: "per-reader-snapshot-not-cross-system-transaction",
        accessChecks,
        counts: Object.freeze({selected: ids.length, sourceRows: bundle.sourceRows.length,
          links: bundle.links.length, projections: bundle.projections.length}),
        pages: Object.freeze({...pageCounts}), summary: result.summary,
        observedFrom: new Date(Math.min(...captureTimes)).toISOString(),
        observedTo: new Date(Math.max(...captureTimes)).toISOString()});
    };
    const timeout = new Promise((_, reject) => {
      timer = setTimeout(() => { controller.abort(); reject(new AuditError("audit-timeout")); }, cfg.timeoutMs);
    });
    return await Promise.race([work(), timeout]);
  } catch (error) {
    // Do not echo upstream errors, paths, raw exports, scope or record identifiers.
    return Object.freeze({...base, decision: "blocked",
      reason: error instanceof AuditError ? error.message : "audit-failed"});
  } finally {
    if (timer !== undefined) clearTimeout(timer);
    if (controller) controller.abort();
  }
}

module.exports = {runReadOnlyAudit};
