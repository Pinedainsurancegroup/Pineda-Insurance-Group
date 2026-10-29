"use strict";

// Pure projection/comparison only: no network, authentication, writes or messages.
// Opaque identifiers remain linkable data; outputs are NOT anonymous/public data.
const { createHash } = require("node:crypto");
const SOURCE = "pag-leads";
const SCHEMA = "pag.recruitment.status.v1";
const VALID_STATES = new Set(["Nuevo", "Contactado", "Cita", "Seguimiento", "Completado"]);
const STABLE_ID = /^r_[a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12}$/;
const SNAPSHOT_KEYS = ["schema", "source", "sourceLeadId", "sourceRevision", "status", "idempotencyKey"];

function isRecord(value) {
  if (!value || typeof value !== "object" || Array.isArray(value)) return false;
  const prototype = Object.getPrototypeOf(value);
  return prototype === Object.prototype || prototype === null;
}

// Read data properties only. Never execute accessors supplied by an adapter.
function field(record, key) {
  const descriptor = Object.getOwnPropertyDescriptor(record, key);
  if (!descriptor || !Object.hasOwn(descriptor, "value")) throw new TypeError("invalid-data-field");
  return descriptor.value;
}

function keyFor(stableId, revision) {
  return createHash("sha256").update(JSON.stringify([SCHEMA, stableId, revision]), "utf8").digest("hex");
}

function createRecruitmentStatusSnapshot(input) {
  if (!isRecord(input)) throw new TypeError("expected-object");
  const stableId = field(input, "stableId");
  const status = field(input, "status");
  const revision = field(input, "revision");
  if (typeof stableId !== "string" || !STABLE_ID.test(stableId)) throw new TypeError("invalid-stable-id");
  if (!VALID_STATES.has(status)) throw new TypeError("invalid-status");
  if (!Number.isSafeInteger(revision) || revision < 0 || Object.is(revision, -0)) throw new TypeError("invalid-revision");
  return Object.freeze({schema: SCHEMA, source: SOURCE, sourceLeadId: stableId,
    sourceRevision: revision, status, idempotencyKey: keyFor(stableId, revision)});
}

// Rebuild and compare every persisted field; reject extra fields and a forged key.
// The digest detects inconsistency, NOT authenticity. It is not a MAC/signature.
function isRecruitmentStatusSnapshot(value) {
  try {
    if (!isRecord(value) || Reflect.ownKeys(value).length !== SNAPSHOT_KEYS.length ||
        SNAPSHOT_KEYS.some(key => !Object.hasOwn(value, key))) return false;
    const rebuilt = createRecruitmentStatusSnapshot({stableId: field(value, "sourceLeadId"),
      status: field(value, "status"), revision: field(value, "sourceRevision")});
    return SNAPSHOT_KEYS.every(key => field(value, key) === rebuilt[key]);
  } catch (_) { return false; }
}

function compareRecruitmentStatus(existing, incoming) {
  if (!isRecruitmentStatusSnapshot(incoming)) return "invalid-snapshot";
  if (existing === null || existing === undefined) return "new";
  if (!isRecruitmentStatusSnapshot(existing)) return "invalid-snapshot";
  if (existing.sourceLeadId !== incoming.sourceLeadId) return "invalid-link";
  if (incoming.sourceRevision < existing.sourceRevision) return "stale";
  if (incoming.sourceRevision > existing.sourceRevision) return "newer";
  return existing.status === incoming.status ? "duplicate" : "conflict";
}

module.exports = {createRecruitmentStatusSnapshot, isRecruitmentStatusSnapshot, compareRecruitmentStatus};
