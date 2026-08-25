import {expect,test} from "@playwright/test";

test("terminal session authorization stops background polling",async({page})=>{
  let sessionRequests=0;
  await page.route("**/sessions/missing-session",async route=>{
    sessionRequests+=1;
    await route.fulfill({status:401,contentType:"application/json",body:JSON.stringify({detail:"session access denied"})});
  });
  await page.goto("/session/missing-session");
  await expect(page.getByRole("heading",{name:"Session unavailable"})).toBeVisible();
  await page.waitForTimeout(2500);
  expect(sessionRequests).toBe(1);
  await expect(page.getByRole("button",{name:"Leave"})).toBeVisible();
});
