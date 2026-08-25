import { createHmac } from "node:crypto";
import { test } from "node:test";
import assert from "node:assert/strict";
import { verifyCanvasToken } from "./canvas-auth";

const token = (claims: Record<string, unknown>, secret = "secret") => {
  const encode = (value: unknown) => Buffer.from(JSON.stringify(value)).toString("base64url");
  const head = encode({ alg: "HS256", typ: "JWT" });
  const payload = encode(claims);
  const signature = createHmac("sha256", secret).update(`${head}.${payload}`).digest("base64url");
  return `${head}.${payload}.${signature}`;
};

test("admits a valid same-session candidate or facilitator token", () => {
  for (const role of ["candidate", "facilitator"]) assert.equal(verifyCanvasToken(token({ kind: "canvas", session_id: "session-a", role, exp: Math.floor(Date.now() / 1000) + 60 }), "session-a", "secret")?.role, role);
});
test("rejects cross-session, expired, malformed, and unsupported-role tokens", () => {
  assert.equal(verifyCanvasToken(token({ kind: "canvas", session_id: "session-a", role: "candidate", exp: Math.floor(Date.now() / 1000) + 60 }), "session-b", "secret"), null);
  assert.equal(verifyCanvasToken(token({ kind: "canvas", session_id: "session-a", role: "candidate", exp: Math.floor(Date.now() / 1000) - 1 }), "session-a", "secret"), null);
  assert.equal(verifyCanvasToken("not-a-token", "session-a", "secret"), null);
  assert.equal(verifyCanvasToken(token({ kind: "canvas", session_id: "session-a", role: "admin", exp: Math.floor(Date.now() / 1000) + 60 }), "session-a", "secret"), null);
});
