import {test} from "node:test";
import assert from "node:assert/strict";
import {RoomRegistry} from "./room-registry";

test("closes and removes a room when its last session leaves",()=>{let onEmpty=()=>{};let closed=false;const registry=new RoomRegistry((_name,cleanup)=>{onEmpty=cleanup;return {close:()=>{closed=true}}});assert.equal(registry.get("opaque-session"),registry.get("opaque-session"));assert.equal(registry.size(),1);onEmpty();assert.equal(closed,true);assert.equal(registry.size(),0)});
