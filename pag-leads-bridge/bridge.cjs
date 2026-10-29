"use strict";

// Phase 0: pure, read-only projection. NO network, credentials, CRM writes, or PII.
// This module does not authorize access to Firestore or the private recruitment Sheet.
const { createHash } = require("node:crypto");

const SOURCE = "pag-leads";
const SCHEMA = "pag.recruitment.status.v1";
const VALID_STATES = new Set(["Nuevo", "Contactado", "Cita", "Seguimiento", "Completado"]);
const STABLE_ID = /^r_[a-f0-9-]{36}$/;

function createRecruitmentStatusSnapshot(input) {
  if (!input || typeof input !== "object" || Array.isArray(input)) {
    throw new TypeError("expected-object");
  }
  const { stableId, status, revision } = input;
  if (typeof stableId !== "string" || !STABLE_ID.test(stableId)) {
    throw new TypeError("invalid-stable-id");
  }
  if (!VALID_STATES.has(status)) {
    throw new TypeError("invalid-status");
  }
  if (!Number.isSafeInteger(revision) || revision < 0) {
    throw new TypeError("invalid-revision");
  }
  const idempotencyKey = createHash("sha256")
    .update(JSON.stringify([SCHEMA, stableId, revision]), "utf8")
    .digest("hex");
  return Object.freeze({
    schema: SCHEMA,
    source: SOURCE,
    sourceLeadId: stableId,
    sourceRevision: revision,
    status,
    idempotencyKey
  });
}

// This function only compares two already validated snapshots.
// A matching revision with different content is a conflict, not a new update.
function compareRecruitmentStatus(existing, incoming) {
  if (existing === null || existing === undefined) return "new";
  if (!existing || !incoming || existing.schema !== SCHEMA || incoming.schema !== SCHEMA ||
      existing.sourceLeadId !== incoming.sourceLeadId) return "invalid-link";
  if (incoming.sourceRevision < existing.sourceRevision) return "stale";
  if (incoming.sourceRevision > existing.sourceRevision) return "newer";
  return existing.status === incoming.status ? "duplicate" : "conflict";
}

module.exports = { createRecruitmentStatusSnapshot, compareRecruitmentStatus };
