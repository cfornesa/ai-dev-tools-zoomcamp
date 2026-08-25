import { createHmac, timingSafeEqual } from "node:crypto";

type CanvasClaims = { kind: string; session_id: string; role: string; exp: number };

export function verifyCanvasToken(raw: string, room: string, secret: string): CanvasClaims | null {
  try {
    const [head, payload, signature] = raw.split(".");
    const expected = createHmac("sha256", secret).update(`${head}.${payload}`).digest("base64url");
    if (!signature || signature.length !== expected.length || !timingSafeEqual(Buffer.from(signature), Buffer.from(expected))) return null;
    const claims = JSON.parse(Buffer.from(payload, "base64url").toString()) as CanvasClaims;
    return claims.kind === "canvas" && claims.session_id === room && claims.exp * 1000 > Date.now() && ["candidate", "facilitator"].includes(claims.role) ? claims : null;
  } catch { return null; }
}
