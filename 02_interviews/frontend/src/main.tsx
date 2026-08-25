import React,{useEffect,useState} from "react";
import {createRoot} from "react-dom/client";
import {BrowserRouter,Link,Navigate,Route,Routes,useNavigate,useParams} from "react-router-dom";
import {RouteGate} from "./routes/guards";
import {SessionDetail} from "./features/admin/SessionDetail";
import {SessionDashboard} from "./features/admin/SessionDashboard";
import {SessionEvaluation} from "./features/evaluation/SessionEvaluation";
import {LiveWorkspace} from "./features/interview/LiveWorkspace";
import {service} from "./lib/service";
import {GoogleSignIn} from "./features/auth/GoogleSignIn";
import "./style.css";

const Shell=({children}:{children:React.ReactNode})=><div className="shell"><header><Link className="button secondary brand-link" to="/admin">Interview Canvas</Link><nav><Link className="button secondary" to="/admin/sessions">Sessions</Link><button className="secondary" onClick={async()=>{await service.logout().catch(()=>undefined);localStorage.clear();location.href="/login"}}>Log out</button></nav></header>{children}</div>;
const Protected=({children}:{children:React.ReactNode})=><RouteGate authorized={Boolean(localStorage.getItem("admin_token"))}><Shell>{children}</Shell></RouteGate>;
function Login(){const nav=useNavigate();const [email,setEmail]=useState("");const [password,setPassword]=useState("");const [error,setError]=useState("");async function submit(e:React.FormEvent){e.preventDefault();try{const result=await service.login(email,password);localStorage.setItem("admin_token",result.access_token);nav("/admin")}catch(e){setError(String(e))}}const googleSuccess=(user:{id:string;email:string;role:string})=>{localStorage.setItem("admin_token","session-cookie");nav("/admin")};return <main className="card narrow"><h1>Administrator login</h1><form onSubmit={submit}><label>Email<input type="email" value={email} onChange={e=>setEmail(e.target.value)} required/></label><label>Password<input type="password" value={password} onChange={e=>setPassword(e.target.value)} required/></label>{error&&<p className="error">{error}</p>}<button>Sign in</button></form><hr/><GoogleSignIn onSuccess={googleSuccess}/></main>}
function Dashboard(){return <main className="card"><h1>Interview Canvas</h1><p>Manage interview sessions, candidate invitations, and evaluations.</p><Link className="button" to="/admin/sessions">Open sessions</Link></main>}
export function Invite(){const {token}=useParams();const [state,setState]=useState("loading");useEffect(()=>{service.redeemInvite(token||"").then(result=>{localStorage.setItem("candidate_token",result.candidate_token);setState(result.session_id)}).catch(e=>setState(String(e).replace("Error: ","")))},[token]);return <main className="card narrow"><h1>Candidate invitation</h1>{state==="loading"?<p>Validating invitation…</p>:state.includes("expired")||state.includes("revoked")||state.includes("already-used")||state.includes("invalid")?<p className="error">{state}</p>:<><p>Invitation accepted.</p><Link className="button" to={`/session/${state}`}>Enter session</Link></>}</main>}
function App(){return <Routes><Route path="/login" element={<Login/>}/><Route path="/admin" element={<Protected><Dashboard/></Protected>}/><Route path="/admin/sessions" element={<Protected><SessionDashboard/></Protected>}/><Route path="/admin/sessions/:sessionId" element={<Protected><SessionDetail/></Protected>}/><Route path="/admin/sessions/:sessionId/evaluation" element={<Protected><SessionEvaluation/></Protected>}/><Route path="/invite/:token" element={<Invite/>}/><Route path="/session/:sessionId" element={<LiveWorkspace/>}/><Route path="*" element={<Navigate to="/admin" replace/>}/></Routes>}
const root=document.getElementById("root");
if(root) createRoot(root).render(<BrowserRouter><App/></BrowserRouter>);
