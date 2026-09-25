"use strict";

const { onCall, HttpsError } = require("firebase-functions/v2/https");
const { defineSecret } = require("firebase-functions/params");
const { initializeApp } = require("firebase-admin/app");
const { getFirestore } = require("firebase-admin/firestore");
const { createRecruitmentHandler } = require("./owner-gateway.cjs");

initializeApp();
const privateUrl = defineSecret("PAG_PRIVATE_API_URL");
const privateToken = defineSecret("PAG_PRIVATE_API_TOKEN");
const handler = createRecruitmentHandler({
  profileForUid: async uid => {
    const doc = await getFirestore().collection("users").doc(uid).get();
    return doc.exists ? doc.data() : null;
  },
  privateUrl: () => privateUrl.value(),
  privateToken: () => privateToken.value(),
  request: fetch
});

exports.ownerRecruitment = onCall({
  region: "us-central1",
  secrets: [privateUrl, privateToken],
  timeoutSeconds: 15,
  maxInstances: 3
}, async call => {
  try {
    return await handler(call);
  } catch (error) {
    const code = ["unauthenticated", "invalid-argument", "permission-denied", "failed-precondition", "unavailable"]
      .includes(error.message) ? error.message : "unavailable";
    // Do not log upstream responses or URLs: they may contain prospect data or tokens.
    throw new HttpsError(code, code === "unavailable" ? "Conexión privada temporalmente no disponible." : "Acceso no disponible.");
  }
});
