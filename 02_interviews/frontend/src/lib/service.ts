export type Session={id:string;candidate_name:string;candidate_email?:string;scheduled_at:string;duration_minutes:number;facilitator_id?:string|null;state:string;end_at?:string|null};
export type Invite={id?:string;url?:string;expires_at?:string;active?:boolean;redeemed?:boolean;revoked?:boolean};
export type ScorecardCategory={name:string;description?:string};
export type Evaluation={recommendation:string;overall_rating?:number|null;overall_notes?:string;private_notes?:string[];scores:Array<{category:string;rating:number;rationale:string}>};
export type SessionInput={candidate_name:string;candidate_email?:string;facilitator_id?:string;scheduled_at:string;duration_minutes:number};
export type ServiceMode="real"|"mock";
declare global { interface Window { grecaptcha?: {ready:(callback:()=>void)=>void;execute:(siteKey:string,options:{action:string})=>Promise<string>} } }

export class ServiceError extends Error{constructor(message:string,readonly status=500){super(message)}}
export interface InterviewService{
  readonly mode:ServiceMode;
  login(email:string,password:string):Promise<{access_token:string}>;
  googleLogin(credential:string):Promise<{user:{id:string;email:string;role:string}}>; 
  logout():Promise<{ok:boolean}>;
  listSessions():Promise<Session[]>; createSession(input:SessionInput):Promise<Session>;
  getSession(id:string,scope:"admin"|"candidate"):Promise<Session>; updateSession(id:string,input:SessionInput):Promise<Session>;
  listInvites(id:string):Promise<Invite[]>; createInvite(id:string):Promise<Invite>; revokeInvite(id:string):Promise<unknown>; regenerateInvite(id:string):Promise<Invite>;
  redeemInvite(rawToken:string):Promise<{candidate_token:string;session_id:string}>;
  canvasToken(id:string,scope:"admin"|"candidate"):Promise<{token:string;room:string}>;
  endSession(id:string):Promise<Session>; extendSession(id:string,minutes:number):Promise<Session>;
  scorecardCategories():Promise<ScorecardCategory[]>; getEvaluation(id:string):Promise<Evaluation|null>; submitEvaluation(id:string,payload:unknown):Promise<unknown>;
}

const API=import.meta.env.VITE_API_URL||"http://localhost:8000";
async function fetchJson(path:string,init:RequestInit={},scope:"admin"|"candidate"|"public"="admin"){
  const token=scope==="admin"?localStorage.getItem("admin_token"):scope==="candidate"?localStorage.getItem("candidate_token"):undefined;
  const csrf=document.cookie.split(";").map(x=>x.trim()).find(x=>x.startsWith("app_csrf="))?.split("=")[1]||"";
  const method=(init.method||"GET").toUpperCase();
  const cookieMutation=token==="session-cookie"&&method!=="GET"&&method!=="HEAD";
  const response=await fetch(`${API}${path}`,{...init,credentials:"include",headers:{"content-type":"application/json",...(token&&token!=="session-cookie"?{Authorization:`Bearer ${token}`}:{}) ,...(cookieMutation?{"X-CSRF-Token":decodeURIComponent(csrf)}:{}),...(init.headers||{})}});
  const body=await response.json().catch(()=>({detail:"Request failed"}));
  if(!response.ok)throw new ServiceError(body.detail||"Request failed",response.status);
  return body;
}
let recaptchaScript:Promise<void>|undefined;
async function recaptchaToken(action:string){const mode=import.meta.env.VITE_RECAPTCHA_MODE||"mock";if(mode==="mock")return `mock:allow:${action}-${crypto.randomUUID()}`;const siteKey=import.meta.env.VITE_RECAPTCHA_SITE_KEY;if(!siteKey)throw new ServiceError("Risk verification is unavailable",503);if(!window.grecaptcha){recaptchaScript??=new Promise<void>((resolve,reject)=>{const script=document.createElement("script");script.src=`https://www.google.com/recaptcha/api.js?render=${encodeURIComponent(siteKey)}`;script.async=true;script.onload=()=>resolve();script.onerror=()=>reject(new ServiceError("Risk verification is unavailable",503));document.head.appendChild(script)});await recaptchaScript}if(!window.grecaptcha)throw new ServiceError("Risk verification is unavailable",503);return new Promise<string>((resolve,reject)=>window.grecaptcha!.ready(()=>window.grecaptcha!.execute(siteKey,{action}).then(resolve).catch(()=>reject(new ServiceError("Risk verification is unavailable",503)))))}
export const sessionWebSocketUrl=(sessionId:string,token?:string)=>{const base=API.replace(/^http/,"ws");return `${base}/ws/sessions/${encodeURIComponent(sessionId)}${token&&token!=="session-cookie"?`?token=${encodeURIComponent(token)}`:""}`};
const real:InterviewService={mode:"real",login:async(email,password)=>fetchJson("/auth/login",{method:"POST",body:JSON.stringify({email,password,recaptcha_token:await recaptchaToken("login")})},"public"),googleLogin:async credential=>fetchJson("/auth/google",{method:"POST",body:JSON.stringify({credential,recaptcha_token:await recaptchaToken("login")})},"public"),logout:async()=>{const csrf=document.cookie.split(";").map(x=>x.trim()).find(x=>x.startsWith("app_csrf="))?.split("=")[1]||"";return fetchJson("/auth/logout",{method:"POST",headers:{"X-CSRF-Token":decodeURIComponent(csrf)}},"public")},listSessions:()=>fetchJson("/admin/sessions"),createSession:input=>fetchJson("/admin/sessions",{method:"POST",body:JSON.stringify(input)}),getSession:(id,scope)=>fetchJson(`${scope==="admin"?"/admin":""}/sessions/${id}`,{},scope),updateSession:(id,input)=>fetchJson(`/admin/sessions/${id}`,{method:"PATCH",body:JSON.stringify(input)}),listInvites:id=>fetchJson(`/admin/sessions/${id}/invites`),createInvite:id=>fetchJson(`/admin/sessions/${id}/invite`,{method:"POST"}),revokeInvite:id=>fetchJson(`/admin/sessions/${id}/invite/revoke`,{method:"POST"}),regenerateInvite:id=>fetchJson(`/admin/sessions/${id}/invite/regenerate`,{method:"POST"}),redeemInvite:async rawToken=>fetchJson("/invites/redeem",{method:"POST",body:JSON.stringify({token:rawToken,recaptcha_token:await recaptchaToken("invite_redeem")})},"public"),canvasToken:(id,scope)=>fetchJson(`${scope==="admin"?"/admin":""}/sessions/${id}/canvas-token`,{method:"POST"},scope),endSession:id=>fetchJson(`/admin/sessions/${id}/end`,{method:"POST"}),extendSession:(id,minutes)=>fetchJson(`/admin/sessions/${id}/extend`,{method:"POST",body:JSON.stringify({minutes})}),scorecardCategories:()=>fetchJson("/scorecards/default"),getEvaluation:id=>fetchJson(`/admin/sessions/${id}/evaluation`).catch(e=>e.status===404?null:Promise.reject(e)),submitEvaluation:(id,payload)=>fetchJson(`/admin/sessions/${id}/evaluation`,{method:"POST",body:JSON.stringify(payload)})};

const seed:Session={id:"mock-session-1",candidate_name:"Mock Candidate",candidate_email:"candidate@example.test",scheduled_at:new Date(Date.now()-60000).toISOString(),duration_minutes:45,state:"active",end_at:new Date(Date.now()+45*60000).toISOString()};
const mockState={sessions:[seed],invited:false,ended:false};
const categories:ScorecardCategory[]=["problem solving","technical fundamentals","communication","collaboration"].map(name=>({name,description:"Representative mock evidence."}));
const mock:InterviewService={mode:"mock",login:async(email,password)=>{if(!email||!password)throw new ServiceError("Email and password are required",422);return {access_token:"mock-admin-token"}},googleLogin:async credential=>{if(!credential)throw new ServiceError("Google provider credential is required",422);return {user:{id:"mock-google-user",email:"mock@example.test",role:"admin"}}},logout:async()=>({ok:true}),listSessions:async()=>mockState.sessions,createSession:async input=>{const item={...input,id:`mock-session-${mockState.sessions.length+1}`,state:"scheduled"};mockState.sessions.push(item);return item},getSession:async(id,scope)=>{const item=mockState.sessions.find(x=>x.id===id);if(!item||scope==="candidate"&&id!=="mock-session-1")throw new ServiceError("session access denied",403);return item},updateSession:async(id,input)=>{const item=await mock.getSession(id,"admin");Object.assign(item,input);return item},listInvites:async()=>mockState.invited?[{active:true,expires_at:new Date(Date.now()+3600000).toISOString()}]:[],createInvite:async()=>{mockState.invited=true;return {url:"http://localhost:5173/invite/mock-token",expires_at:new Date(Date.now()+3600000).toISOString()}},revokeInvite:async()=>{mockState.invited=false;return {revoked:1}},regenerateInvite:async()=>mock.createInvite("mock-session-1"),redeemInvite:async token=>{if(token!=="mock-token")throw new ServiceError("invalid invitation",400);return {candidate_token:"mock-candidate-token",session_id:"mock-session-1"}},canvasToken:async(id,scope)=>{await mock.getSession(id,scope);return {token:`mock-canvas-${scope}`,room:id}},endSession:async id=>{const item=await mock.getSession(id,"admin");item.state="completed";return item},extendSession:async(id,minutes)=>{const item=await mock.getSession(id,"admin");item.state="active";item.end_at=new Date(Date.now()+minutes*60000).toISOString();return item},scorecardCategories:async()=>categories,getEvaluation:async()=>null,submitEvaluation:async()=>({id:"mock-evaluation-1"})};

export const realService:InterviewService=real;
export const mockService:InterviewService=mock;
export function createService(mode:ServiceMode):InterviewService{return mode==="mock"?mockService:realService}
export const service:InterviewService=createService(import.meta.env.VITE_SERVICE_MODE==="mock"?"mock":"real");
