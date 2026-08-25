import {render,screen} from "@testing-library/react";
import {MemoryRouter,Route,Routes} from "react-router-dom";
import {afterEach,describe,expect,it,vi} from "vitest";
import "@testing-library/jest-dom/vitest";
import {LiveWorkspace} from "./LiveWorkspace";


describe("LiveWorkspace request lifecycle",()=>{
  afterEach(()=>{vi.restoreAllMocks();localStorage.clear()});
  it("stops polling after a terminal authorization response",async()=>{
    localStorage.setItem("candidate_token","candidate-token");
    const fetchMock=vi.fn().mockResolvedValue({ok:false,status:401,json:async()=>({detail:"session access denied"})});
    vi.stubGlobal("fetch",fetchMock);
    render(<MemoryRouter initialEntries={["/session/missing"]}><Routes><Route path="/session/:sessionId" element={<LiveWorkspace/>}/></Routes></MemoryRouter>);
    expect(await screen.findByRole("heading",{name:"Session unavailable"})).toBeVisible();
    await new Promise(resolve=>setTimeout(resolve,2200));
    expect(fetchMock).toHaveBeenCalledTimes(1);
  });
});
