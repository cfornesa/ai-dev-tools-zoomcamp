import {afterEach,describe,expect,it,vi} from "vitest";
import {createService,mockService,realService} from "./service";

describe("frontend service adapters",()=>{
  afterEach(()=>vi.restoreAllMocks());
  it("selects explicit real and mock implementations",()=>{expect(createService("real")).toBe(realService);expect(createService("mock")).toBe(mockService);expect(mockService.mode).toBe("mock")});
  it("provides seeded mock data and representative failure states",async()=>{const item=await mockService.getSession("mock-session-1","candidate");expect(item.candidate_name).toBe("Mock Candidate");await expect(mockService.redeemInvite("invalid")).rejects.toMatchObject({status:400});});
  it("attaches CSRF tokens to cookie-authenticated mutations",async()=>{localStorage.setItem("admin_token","session-cookie");document.cookie="app_csrf=csrf-token";const fetchMock=vi.spyOn(globalThis,"fetch").mockResolvedValue({ok:true,json:async()=>({id:"session-1"})} as Response);await realService.createSession({candidate_name:"Candidate",scheduled_at:"2026-01-01T12:00:00Z",duration_minutes:45});expect(fetchMock).toHaveBeenCalledWith(expect.stringContaining("/admin/sessions"),expect.objectContaining({credentials:"include",headers:expect.objectContaining({"X-CSRF-Token":"csrf-token"})}));localStorage.clear();document.cookie="app_csrf=; Max-Age=0"});
});
