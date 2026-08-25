export function remainingMinutes(endAt:string|undefined|null,now=Date.now()){
  if(!endAt)return null;
  return Math.max(0,Math.ceil((new Date(endAt).getTime()-now)/60000));
}
export function canEndSession(role:"admin"|"candidate",state:string){return role==="admin"&&state==="active";}
export function expiryMessage(role:"admin"|"candidate"){return role==="admin"?"Time expired. End or extend the session.":"Time expired. Waiting for the facilitator.";}

const stateRank:Record<string,number>={scheduled:0,active:1,"expired-pending-facilitator-action":2,expired:2,completed:3};
export function shouldApplySessionEvent(current:SessionLike,nextState:string,nextEndAt?:string|null){
  if(nextState==="completed") return true;
  if(current.state==="completed") return false;
  const currentEnd=current.end_at?new Date(current.end_at).getTime():0;
  const nextEnd=nextEndAt?new Date(nextEndAt).getTime():0;
  if(nextState==="active" && current.state!=="active") return nextEnd>=currentEnd;
  if((nextState==="expired"||nextState==="expired-pending-facilitator-action") && current.state==="active") return nextEnd>=currentEnd;
  return (stateRank[nextState]??0)>= (stateRank[current.state]??0);
}

type SessionLike={state:string;end_at?:string|null};
