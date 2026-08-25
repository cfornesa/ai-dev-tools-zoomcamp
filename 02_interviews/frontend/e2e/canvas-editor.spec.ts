import {expect,test} from "@playwright/test";

const editorUrl=process.env.E2E_CANVAS_EDITOR_URL||"http://localhost:8090/editor.html";

async function canvasBox(page:any){
  const box=await page.locator("#canvas").boundingBox();
  if(!box) throw new Error("canvas is not visible");
  return box;
}

test("canvas pointer tools, text editing, cancellation, and narrow layout",async({page})=>{
  await page.setViewportSize({width:390,height:720});
  await page.goto(editorUrl);
  const canvas=page.locator("#canvas");
  const box=await canvasBox(page);
  const count=()=>canvas.locator(":scope > *").count();

  await page.getByRole("button",{name:"Select / Move"}).click();
  await page.mouse.click(box.x+box.width*.8,box.y+box.height*.8);
  expect(await count()).toBe(0);

  await page.getByRole("button",{name:"Rectangle"}).click();
  await page.waitForTimeout(50);
  const rectangleBox=await canvasBox(page);
  await page.mouse.move(rectangleBox.x+rectangleBox.width*.75,rectangleBox.y+rectangleBox.height*.5);
  await page.mouse.down();
  await page.mouse.move(rectangleBox.x+rectangleBox.width*.25,rectangleBox.y+rectangleBox.height*.15,{steps:4});
  await page.mouse.up();
  expect(await canvas.locator("rect").count()).toBe(1);
  expect(Number(await canvas.locator("rect").getAttribute("width"))).toBeGreaterThan(0);
  expect(Number(await canvas.locator("rect").getAttribute("height"))).toBeGreaterThan(0);

  await page.getByRole("button",{name:"Select / Move"}).click();
  const rectangle=canvas.locator("rect").first();
  const rectangleStart=await rectangle.boundingBox();
  if(!rectangleStart) throw new Error("rectangle is not visible");
  await page.mouse.move(rectangleStart.x+10,rectangleStart.y+10);
  await page.mouse.down();
  await page.mouse.move(rectangleStart.x+45,rectangleStart.y+35,{steps:3});
  await page.mouse.up();
  expect((await rectangle.boundingBox())?.x).toBeGreaterThan(rectangleStart.x+20);

  await page.getByRole("button",{name:"Connector"}).click();
  await page.mouse.move(box.x+box.width*.2,box.y+box.height*.1);
  await page.mouse.down();
  await page.mouse.move(box.x+box.width*.7,box.y+box.height*.5,{steps:4});
  await page.mouse.up();
  const line=canvas.locator("line");
  expect(await line.count()).toBe(1);
  expect(Number(await line.getAttribute("x2"))).toBeGreaterThan(Number(await line.getAttribute("x")));

  await page.getByRole("button",{name:"Freehand"}).click();
  await page.mouse.move(box.x+30,box.y+30);
  await page.mouse.down();
  await page.mouse.move(box.x+60,box.y+60,{steps:3});
  await page.mouse.move(box.x+100,box.y+40,{steps:3});
  await page.mouse.up();
  expect((await canvas.locator("path").getAttribute("d"))?.split("L").length).toBeGreaterThan(2);

  await page.getByRole("button",{name:"Text"}).click();
  await page.mouse.click(box.x+box.width*.9,box.y+box.height*.1);
  await page.getByRole("textbox",{name:"Text"}).fill("Committed");
  await page.getByLabel("Font size").fill("24");
  await page.getByRole("button",{name:"Apply"}).click();
  expect(await canvas.locator("text").textContent()).toBe("Committed");
  expect(await canvas.locator("text").getAttribute("font-size")).toBe("24");

  await page.getByRole("button",{name:"Rectangle"}).click();
  await page.mouse.move(box.x+40,box.y+80);
  await page.mouse.down();
  await page.mouse.move(box.x+120,box.y+140);
  await page.mouse.up();
  const editableRectangle=canvas.locator("rect").last();
  const widthBefore=Number(await editableRectangle.getAttribute("width"));
  await page.keyboard.press("Shift+ArrowRight");
  expect(Number(await editableRectangle.getAttribute("width"))).toBe(widthBefore+10);

  await page.getByRole("button",{name:"Square"}).click();
  await page.mouse.move(box.x+180,box.y+180);
  await page.mouse.down();
  await page.mouse.move(box.x+120,box.y+120,{steps:3});
  await page.mouse.up();
  const square=canvas.locator('rect[data-tool="square"]');
  expect(await square.count()).toBe(1);
  expect(await square.getAttribute("width")).toBe(await square.getAttribute("height"));

  await page.getByRole("button",{name:"Circle / Ellipse"}).click();
  await page.mouse.move(box.x+220,box.y+220);
  await page.mouse.down();
  await page.mouse.move(box.x+280,box.y+260,{steps:3});
  await page.mouse.up();
  const circle=canvas.locator('ellipse[data-tool="circle"]');
  expect(await circle.count()).toBe(1);
  expect(await circle.getAttribute("rx")).toBe(await circle.getAttribute("ry"));

  await page.getByRole("button",{name:"Freehand"}).click();
  await page.mouse.move(box.x+150,box.y+150);
  await page.mouse.down();
  await page.locator("#viewport").dispatchEvent("pointercancel",{pointerId:1});
  await page.mouse.up();
  expect(await page.getByRole("status").innerText()).toContain("Gesture cancelled");
});

test("circle creation survives a reverse drag over existing shapes",async({page})=>{
  await page.setViewportSize({width:390,height:720});
  await page.goto(editorUrl);
  const canvas=page.locator("#canvas");
  const box=await canvasBox(page);
  await page.getByRole("button",{name:"Connector"}).click();
  await page.mouse.move(box.x+box.width*.15,box.y+box.height*.15);
  await page.mouse.down();
  await page.mouse.move(box.x+box.width*.8,box.y+box.height*.65,{steps:3});
  await page.mouse.up();
  await page.getByRole("button",{name:"Circle / Ellipse"}).click();
  await page.mouse.move(box.x+box.width*.8,box.y+box.height*.65);
  await page.mouse.down();
  await page.mouse.move(box.x+box.width*.55,box.y+box.height*.35,{steps:3});
  await page.mouse.up();
  const circle=canvas.locator('ellipse[data-tool="circle"]');
  await expect(circle).toHaveCount(1);
  expect(await circle.getAttribute("rx")).toBe(await circle.getAttribute("ry"));
});
