import {expect,test} from "@playwright/test";

test("session rows keep an explicit View Session action on a phone",async({page})=>{
  await page.setViewportSize({width:390,height:844});
  await page.addInitScript(()=>localStorage.setItem("admin_token","test-admin"));
  await page.route("http://localhost:8000/admin/sessions",async route=>route.fulfill({status:200,contentType:"application/json",body:JSON.stringify([{id:"session-long",candidate_name:"A candidate with a deliberately long name",candidate_email:"candidate@example.test",scheduled_at:"2026-01-01T12:00:00Z",duration_minutes:45,state:"expired-pending-facilitator-action"}])}));
  await page.goto("/admin/sessions");
  const action=page.getByRole("link",{name:"View Session"});
  await expect(action).toHaveCount(1);
  await expect(action).toHaveAttribute("href","/admin/sessions/session-long");
  await expect(page.getByText("A candidate with a deliberately long name",{exact:true})).toBeVisible();
  expect(await page.evaluate(()=>document.documentElement.scrollWidth)).toBeLessThanOrEqual(390);
});
