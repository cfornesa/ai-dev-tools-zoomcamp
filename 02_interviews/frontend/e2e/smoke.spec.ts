import {expect,test} from "@playwright/test";

const adminEmail=process.env.DEV_ADMIN_EMAIL||"admin@example.test";
const adminPassword=process.env.DEV_ADMIN_PASSWORD||"correct-horse";
function localDateTime(minutesFromNow:number){const date=new Date(Date.now()+minutesFromNow*60_000);const pad=(value:number)=>String(value).padStart(2,"0");return `${date.getFullYear()}-${pad(date.getMonth()+1)}-${pad(date.getDate())}T${pad(date.getHours())}:${pad(date.getMinutes())}`}

test("administrator, candidate, canvas, completion, and evaluation smoke path",async({browser,page})=>{
  const candidateName=`Browser Smoke Candidate ${Date.now()}`;
  await page.context().grantPermissions(["clipboard-read","clipboard-write"]);
  await page.goto("/login");
  await page.getByLabel("Email").fill(adminEmail);
  await page.getByLabel("Password").fill(adminPassword);
  await page.getByRole("button",{name:"Sign in"}).click();
  await expect(page).toHaveURL(/\/admin$/);

  await page.goto("/admin/sessions");
  await page.getByLabel("Candidate name").fill(candidateName);
  await page.getByLabel("Scheduled time").fill(localDateTime(-1));
  await page.getByLabel("Duration").fill("30");
  await page.getByRole("button",{name:"Create"}).click();
  await expect(page.getByRole("link",{name:candidateName,exact:true})).toBeVisible();
  await page.getByRole("link",{name:candidateName,exact:true}).click();
  await page.getByRole("button",{name:"Generate invite"}).click();
  const inviteInput=page.getByLabel("Invite URL");
  await expect(inviteInput).toBeVisible();
  const inviteUrl=await inviteInput.inputValue();
  await page.getByRole("button",{name:"Copy"}).click();
  await expect.poll(()=>page.evaluate(()=>navigator.clipboard.readText())).toBe(inviteUrl);

  const candidateContext=await browser.newContext({permissions:["clipboard-read","clipboard-write"]});
  const candidatePage=await candidateContext.newPage();
  await candidatePage.goto(inviteUrl);
  await candidatePage.getByRole("link",{name:"Enter session"}).click();
  await expect(candidatePage.getByRole("heading",{name:"Live interview"})).toBeVisible();
  await expect(candidatePage.locator(".canvas-editor")).toBeVisible();
  const sessionUrl=candidatePage.url();

  await page.goto(sessionUrl);
  await expect(page.getByRole("heading",{name:"Live interview"})).toBeVisible();
  await expect(page.locator(".canvas-editor")).toBeVisible();
  await page.getByRole("button",{name:"End session"}).click();
  await expect(page.getByRole("link",{name:"Open evaluation"})).toBeVisible();
  await page.getByRole("link",{name:"Open evaluation"}).click();
  for(const category of ["problem solving","technical fundamentals","communication","collaboration"]){
    await page.getByLabel(`${category} rating`).selectOption("4");
    await page.getByLabel(`${category} rationale`).fill("Observed browser smoke evidence.");
  }
  await page.getByLabel("Overall rating").selectOption("4");
  await page.getByRole("button",{name:"Save evaluation"}).click();
  await expect(page.getByText("Evaluation saved")).toBeVisible();
  await candidateContext.close();
});
