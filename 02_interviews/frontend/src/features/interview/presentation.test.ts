import {describe,expect,it} from "vitest";
import {shouldApplySessionEvent} from "./presentation";

describe("session event ordering",()=>{
  it("accepts an authoritative extension and rejects its stale expiry",()=>{
    const current={state:"expired",end_at:"2026-08-25T20:00:00Z"};
    expect(shouldApplySessionEvent(current,"active","2026-08-25T20:15:00Z")).toBe(true);
    expect(shouldApplySessionEvent({state:"active",end_at:"2026-08-25T20:15:00Z"},"expired","2026-08-25T20:00:00Z")).toBe(false);
  });

  it("does not let an old event revive a completed session",()=>{
    expect(shouldApplySessionEvent({state:"completed",end_at:null},"active","2026-08-25T20:15:00Z")).toBe(false);
  });
});
