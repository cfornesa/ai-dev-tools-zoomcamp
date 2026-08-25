import { expect, test } from "@playwright/test";

test.describe("self-hosted canvas protocol POC", () => {
  test.skip(!process.env.CANVAS_POC_URL, "Set CANVAS_POC_URL to run the disposable POC browser checks");

  test("renders, moves, saves, deletes, and restores a shape", async ({ page }) => {
    await page.goto(`${process.env.CANVAS_POC_URL}/host.html`);
    const editor = page.frameLocator("iframe[title='Local canvas editor']");
    await expect(page.getByRole("status")).toContainText("Editor initialized locally");
    for (const tool of ["Freehand", "Text", "Move", "Rectangle", "Connector", "Undo", "Redo", "Zoom +", "Zoom −"]) {
      await expect(editor.getByRole("button", { name: tool })).toBeVisible();
    }
    await editor.getByRole("button", { name: "Rectangle" }).click();
    await editor.locator("#canvas").dispatchEvent("pointerdown", { clientX: 100, clientY: 100 });
    await editor.locator("#canvas").dispatchEvent("pointerup");
    await expect(editor.locator("svg rect")).toHaveCount(1);
    await editor.getByRole("button", { name: "Move" }).click();
    await editor.locator("svg rect").dispatchEvent("pointerdown", { clientX: 100, clientY: 100 });
    await editor.locator("svg rect").dispatchEvent("pointermove", { clientX: 130, clientY: 130 });
    await editor.locator("svg rect").dispatchEvent("pointerup");
    await editor.getByRole("button", { name: "Save XML" }).click();
    await expect(page.getByRole("status")).toContainText("Saved revision");
    await editor.getByRole("button", { name: "Delete" }).click();
    await expect(editor.locator("svg rect")).toHaveCount(0);
    await editor.getByRole("button", { name: "Reload XML" }).click();
    await expect(editor.locator("svg rect")).toHaveCount(1);
  });

  test("converts a persisted mxGraphModel into visible editor elements", async ({ page }) => {
    await page.goto(`${process.env.CANVAS_POC_URL}/host.html`);
    await page.evaluate(() => localStorage.setItem("canvas-poc-xml", `<mxfile><diagram><mxGraphModel><root><mxCell id="0"/><mxCell id="1" parent="0"/><mxCell id="2" value="Persisted node" style="rounded=0;whiteSpace=wrap;html=1;" vertex="1" parent="1"><mxGeometry x="120" y="90" width="220" height="100" as="geometry"/></mxCell><mxCell id="3" edge="1" parent="1"><mxGeometry x="420" y="120" width="180" height="60" as="geometry"/></mxCell></root></mxGraphModel></diagram></mxfile>`));
    await page.reload();
    const editor = page.frameLocator("iframe[title='Local canvas editor']");
    await expect(editor.locator("svg rect")).toHaveCount(0);
    await expect(editor.locator("svg text")).toHaveCount(1);
    await expect(editor.locator("svg line")).toHaveCount(1);
    await expect(editor.locator("svg text").first()).toContainText("Persisted node");
    await expect(editor.locator("#canvas mxCell")).toHaveCount(0);
    const box = await editor.locator("svg text").first().boundingBox();
    expect(box?.width).toBeGreaterThan(0);
    expect(box?.height).toBeGreaterThan(0);
  });
});
