import {afterEach,describe,expect,it,vi} from "vitest";
import {createService,mockService,realService} from "./service";

describe("frontend service adapters",()=>{
  afterEach(()=>vi.restoreAllMocks());
  it("selects explicit real and mock implementations",()=>{expect(createService("real")).toBe(realService);expect(createService("mock")).toBe(mockService);expect(mockService.mode).toBe("mock")});
  it("provides seeded mock data and representative failure states",async()=>{const item=await mockService.getSession("mock-session-1","candidate");expect(item.candidate_name).toBe("Mock Candidate");await expect(mockService.redeemInvite("invalid")).rejects.toMatchObject({status:400});});
});
