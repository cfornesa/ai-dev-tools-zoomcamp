import { expect, test } from "@playwright/test";

test("expired session detail exposes separated recovery actions on a phone", async ({ page }) => {
  await page.setViewportSize({ width: 390, height: 844 });
  await page.addInitScript(() => localStorage.setItem("admin_token", "test-admin"));
  await page.route("http://localhost:8000/admin/sessions/session-1", async route => {
    await route.fulfill({ status: 200, contentType: "application/json", body: JSON.stringify({ id: "session-1", candidate_name: "A candidate with a deliberately long name", scheduled_at: "2026-01-01T12:00:00Z", duration_minutes: 45, state: "expired" }) });
  });
  await page.route("http://localhost:8000/admin/sessions/session-1/invites", async route => {
    await route.fulfill({ status: 200, contentType: "application/json", body: "[]" });
  });
  await page.goto("/admin/sessions/session-1");
  await expect(page.getByText("Expired — facilitator action needed")).toBeVisible();
  await expect(page.getByText("No invite has been generated.")).toBeVisible();
  await expect(page.getByRole("button", { name: "Generate invite" })).toBeVisible();
  await expect(page.getByRole("heading", { name: "Session actions" })).toBeVisible();
  expect(await page.evaluate(() => document.documentElement.scrollWidth)).toBeLessThanOrEqual(390);
  for (const control of await page.locator("button, input, a.button").all()) expect((await control.boundingBox())?.height || 0).toBeGreaterThanOrEqual(40);
});
