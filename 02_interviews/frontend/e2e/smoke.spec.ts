import {expect,test} from "@playwright/test";
import {execFileSync} from "node:child_process";

const adminEmail=process.env.DEV_ADMIN_EMAIL||"admin@example.test";
const adminPassword=process.env.DEV_ADMIN_PASSWORD||"correct-horse";
function localDateTime(minutesFromNow:number){const date=new Date(Date.now()+minutesFromNow*60_000);const pad=(value:number)=>String(value).padStart(2,"0");return `${date.getFullYear()}-${pad(date.getMonth()+1)}-${pad(date.getDate())}T${pad(date.getHours())}:${pad(date.getMinutes())}`}

test("administrator, candidate, canvas, completion, and evaluation smoke path",async({browser,page})=>{
  const diagnostics:string[]=[];
  page.on("requestfailed",request=>diagnostics.push(`${request.method()} ${new URL(request.url()).pathname}`));
  page.on("console",message=>{if(message.type()==="error")diagnostics.push(`console ${message.text().slice(0,160)}`)});
  page.on("response",response=>{if(response.url().endsWith("/auth/login"))diagnostics.push(`login-status ${response.status()}`)});
  const candidateName=`Browser Smoke Candidate ${Date.now()}`;
  await page.context().grantPermissions(["clipboard-read","clipboard-write"]);
  await page.goto("/login");
  await page.getByLabel("Email").fill(adminEmail);
  await page.getByLabel("Password").fill(adminPassword);
  await page.getByRole("button",{name:"Sign in"}).click();
  await expect(page).toHaveURL(/\/admin\/sessions$/);

  await page.goto("/admin/sessions");
  await page.getByLabel("Candidate name").fill(candidateName);
  await page.getByLabel("Scheduled time").fill(localDateTime(1));
  await page.getByLabel("Duration").fill("30");
  await page.getByRole("button",{name:"Create"}).click();
  await expect(page.getByRole("link",{name:candidateName,exact:true})).toBeVisible();
  await page.getByLabel("Search sessions").fill(candidateName.toLowerCase());
  await expect(page.getByRole("link",{name:candidateName,exact:true})).toBeVisible();
  await page.getByLabel("Status filter").selectOption("scheduled");
  await expect(page.getByRole("link",{name:candidateName,exact:true})).toBeVisible();
  await page.getByRole("button",{name:"Clear criteria"}).click();
  await page.getByRole("link",{name:candidateName,exact:true}).click();
  await page.getByRole("button",{name:"Generate invite"}).click();
  const inviteInput=page.getByLabel("Invite URL");
  await expect(inviteInput).toBeVisible();
  const inviteUrl=await inviteInput.inputValue();
  await page.getByRole("button",{name:"Copy"}).click();
  await expect.poll(()=>page.evaluate(()=>navigator.clipboard.readText())).toBe(inviteUrl);

  const candidateContext=await browser.newContext({permissions:["clipboard-read","clipboard-write"]});
  const candidatePage=await candidateContext.newPage();
  let candidateCanvasTokenResponses=0;
  candidatePage.on("response",response=>{if(response.url().endsWith("/canvas-token"))candidateCanvasTokenResponses+=1});
  await candidatePage.goto(inviteUrl);
  await candidatePage.getByRole("link",{name:"Enter session"}).click();
  await expect(candidatePage.getByRole("heading",{name:"Live interview"})).toBeVisible();
  await expect(candidatePage.locator("iframe[title=\"Collaborative canvas\"]")).toBeVisible();
  await candidatePage.waitForTimeout(4500);
  expect(candidateCanvasTokenResponses).toBe(1);
  const sessionUrl=candidatePage.url();
  execFileSync("docker",["compose","restart","canvas-sync"],{cwd:"..",timeout:30_000,stdio:"pipe"});
  await candidatePage.reload();
  await expect(candidatePage.locator("iframe[title=\"Collaborative canvas\"]")).toBeVisible();
  await candidatePage.getByRole("button",{name:"Leave"}).click();
  await expect(candidatePage).toHaveURL(/\/login$/);
  await candidatePage.goto(sessionUrl);
  await expect(candidatePage.locator("iframe[title=\"Collaborative canvas\"]")).toBeVisible();

  await page.goto(sessionUrl);
  await expect(page.getByRole("heading",{name:"Live interview"})).toBeVisible();
  await expect(page.locator("iframe[title=\"Collaborative canvas\"]")).toBeVisible();
  await page.getByRole("button",{name:"Finish session"}).click();
  await expect(page.getByRole("link",{name:"Open evaluation"})).toBeVisible();
  await candidatePage.reload();
  await expect(candidatePage.getByText("This session has ended. You may leave this page.")).toBeVisible();
  await page.getByRole("link",{name:"Open evaluation"}).click();
  for(const category of ["problem solving","technical fundamentals","communication","collaboration"]){
    await page.getByLabel(`${category} rating`).selectOption("4");
    await page.getByLabel(`${category} rationale`).fill("Observed browser smoke evidence.");
  }
  await page.getByLabel("Overall rating").selectOption("4");
  await page.getByRole("button",{name:"Save evaluation"}).click();
  await expect(page.getByText("Evaluation saved")).toBeVisible();
  expect(diagnostics.filter(item=>!item.includes("token")&&!item.includes("password")).length).toBeLessThan(20);
  await candidateContext.close();
});
