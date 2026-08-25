import {fireEvent,render,screen} from "@testing-library/react";
import {MemoryRouter,Route,Routes} from "react-router-dom";
import {afterEach,describe,expect,it,vi} from "vitest";
import "@testing-library/jest-dom/vitest";
import {LiveWorkspace} from "./LiveWorkspace";

describe("live-session controls",()=>{afterEach(()=>{vi.restoreAllMocks();localStorage.clear()});it("keeps finish controls out of candidate sessions and supports leaving",async()=>{localStorage.setItem("candidate_token","candidate-token");vi.stubGlobal("fetch",vi.fn().mockImplementation((url:string)=>url.endsWith("/canvas-token")?Promise.resolve({ok:true,json:async()=>({token:"canvas-token"})}):Promise.resolve({ok:true,json:async()=>({id:"session-1",candidate_name:"Candidate",state:"active",end_at:null})})));render(<MemoryRouter initialEntries={["/session/session-1"]}><Routes><Route path="/session/:sessionId" element={<LiveWorkspace/>}/><Route path="/login" element={<h1>Login</h1>}/></Routes></MemoryRouter>);expect(await screen.findByRole("heading",{name:"Live interview"})).toBeVisible();expect(screen.queryByRole("button",{name:"Finish session"})).not.toBeInTheDocument();fireEvent.click(screen.getByRole("button",{name:"Leave"}));expect(await screen.findByRole("heading",{name:"Login"})).toBeVisible()})});
