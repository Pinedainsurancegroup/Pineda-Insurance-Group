"use strict";

const test = require("node:test");
const assert = require("node:assert/strict");
const { createRecruitmentHandler } = require("../owner-gateway.cjs");

const url = "https://script.google.com/macros/s/example/exec";
const owner = { role: "owner", active: true, suspended: false };
function setup(profile = owner) {
  const calls = [];
  const handler = createRecruitmentHandler({
    profileForUid: async uid => { calls.push("profile:" + uid); return profile; },
    privateUrl: () => url,
    privateToken: () => "private-value",
    request: async (target, opts) => {
      calls.push("upstream");
      assert.equal(target, url);
      assert.equal(opts.headers["Content-Type"], "text/plain;charset=utf-8");
      assert.deepEqual(JSON.parse(opts.body), { action: "list", token: "private-value" });
      return { ok: true, headers: { get: () => null }, text: async () => JSON.stringify({ ok: true, leads: [{ id: "example", type: "agent" }, { id: "fe", type: "client" }] }) };
    }
  });
  return { handler, calls };
}

test("unauthenticated and invalid actions do not read profile or source", async () => {
  const { handler, calls } = setup();
  await assert.rejects(handler({ data: { action: "list" } }), { message: "unauthenticated" });
  await assert.rejects(handler({ auth: { uid: "a" }, data: { action: "delete" } }), { message: "invalid-argument" });
  assert.deepEqual(calls, []);
});

test("suspended owner and agents cannot read recruitment, including an old signed-in session", async () => {
  for (const profile of [{ ...owner, suspended: true }, { ...owner, active: false }, { ...owner, role: "agent" }, null]) {
    const { handler, calls } = setup(profile);
    await assert.rejects(handler({ auth: { uid: "old-session" }, data: { action: "list" } }), { message: "permission-denied" });
    assert.deepEqual(calls, ["profile:old-session"]);
  }
});

test("active owner receives existing leads without receiving the private API token", async () => {
  const { handler, calls } = setup();
  assert.deepEqual(await handler({ auth: { uid: "owner" }, data: { action: "list" } }), { ok: true, leads: [{ id: "example", type: "agent" }] });
  assert.deepEqual(calls, ["profile:owner", "upstream"]);
});
