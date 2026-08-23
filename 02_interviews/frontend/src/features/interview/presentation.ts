export function remainingMinutes(endAt:string|undefined,now=Date.now()){
  if(!endAt)return null;
  return Math.max(0,Math.ceil((new Date(endAt).getTime()-now)/60000));
}
export function canEndSession(role:"admin"|"candidate",state:string){return role==="admin"&&state==="active";}
export function expiryMessage(role:"admin"|"candidate"){return role==="admin"?"Time expired. End or extend the session.":"Time expired. Waiting for the facilitator.";}
