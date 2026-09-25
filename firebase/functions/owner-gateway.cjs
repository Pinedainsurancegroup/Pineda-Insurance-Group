"use strict";

// Only the existing private Apps Script is the recruitment source; this function
// never stores leads or returns credentials to the Android application.
function createRecruitmentHandler({ profileForUid, privateUrl, privateToken, request, timeoutMs = 10000 }) {
  return async (call) => {
    const uid = call.auth?.uid;
    if (!uid) throw new Error("unauthenticated");
    const action = call.data?.action;
    if (action !== "ping" && action !== "list") throw new Error("invalid-argument");
    const profile = await profileForUid(uid);
    if (!profile || profile.role !== "owner" || profile.active !== true || profile.suspended === true) {
      throw new Error("permission-denied");
    }
    const url = privateUrl();
    const token = privateToken();
    if (!url || !token || !/^https:\/\/script\.google\.com\/macros\/s\/[^/?#]+\/exec$/.test(url)) {
      throw new Error("failed-precondition");
    }
    let response;
    try {
      response = await request(url, {
        method: "POST",
        headers: { "Content-Type": "text/plain;charset=utf-8" },
        body: JSON.stringify({ action, token }),
        signal: AbortSignal.timeout(timeoutMs),
        redirect: "follow"
      });
      if (!response.ok || Number(response.headers.get("content-length") || 0) > 2_000_000) {
        throw new Error("upstream failure");
      }
      const body = await response.text();
      if (body.length > 2_000_000) throw new Error("oversized response");
      const data = JSON.parse(body);
      if (data?.ok !== true || (action === "list" && !Array.isArray(data.leads))) {
        throw new Error("upstream rejection");
      }
      // Never return an arbitrary upstream object, which might include secrets.
      if (action === "ping") return { ok: true, version: String(data.version || "PAG Leads") };
      return { ok: true, leads: data.leads.filter(lead => lead && lead.type === "agent") };
    } catch (_) {
      throw new Error("unavailable");
    }
  };
}

module.exports = { createRecruitmentHandler };
