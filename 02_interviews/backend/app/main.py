from datetime import datetime, timedelta, timezone
import os
import asyncio
from collections import defaultdict, deque
from fastapi import Depends, FastAPI, HTTPException, Request, Response, WebSocket, WebSocketDisconnect
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import text
from sqlalchemy.orm import Session
from .config import settings
from .db import get_db, SessionLocal
from .models import *
from .schemas import *
from .security import *

app=FastAPI(title="Interview Canvas API")
app.add_middleware(CORSMiddleware,allow_origins=[x.strip() for x in settings.frontend_origins.split(",")],allow_credentials=True,allow_methods=["*"],allow_headers=["*"])
bearer=HTTPBearer(auto_error=False)
login_attempts=defaultdict(deque)
invite_attempts=defaultdict(deque)
connections=defaultdict(set)
connection_meta={}
DEFAULT_CATEGORIES=[{"name":"problem solving","description":"Frames problems and reasons through trade-offs."},{"name":"technical fundamentals","description":"Demonstrates relevant technical knowledge."},{"name":"communication","description":"Explains thinking clearly and collaborates effectively."},{"name":"collaboration","description":"Works constructively with the interviewer."}]

@app.middleware("http")
async def csrf_for_cookie_sessions(request:Request,call_next):
    protected_cookie_path=request.url.path.startswith("/admin") or request.url.path=="/auth/logout"
    if request.method in {"POST","PUT","PATCH","DELETE"} and protected_cookie_path and request.cookies.get("app_session") and not request.headers.get("authorization"):
        csrf=request.headers.get("x-csrf-token")
        if not csrf or csrf!=request.cookies.get("app_csrf"):
            return JSONResponse({"detail":"csrf validation failed"},status_code=403)
    response=await call_next(request)
    response.headers["Content-Security-Policy"]="default-src 'self'; base-uri 'self'; object-src 'none'; frame-ancestors 'none'; style-src 'self' 'unsafe-inline'; script-src 'self' https://accounts.google.com https://www.google.com; frame-src 'self' https://accounts.google.com https://www.google.com; connect-src 'self' https://accounts.google.com https://www.google.com"
    response.headers["X-Content-Type-Options"]="nosniff"
    response.headers["Referrer-Policy"]="strict-origin-when-cross-origin"
    return response

@app.on_event("startup")
def seed_dev_admin():
    email,password=os.getenv("DEV_ADMIN_EMAIL"),os.getenv("DEV_ADMIN_PASSWORD")
    if email and password:
        db=SessionLocal()
        if not db.query(AdminUser).filter_by(email=email).first(): db.add(AdminUser(email=email,password_hash=hash_password(password))); db.commit()
        db.close()

def admin(request:Request,creds:HTTPAuthorizationCredentials=Depends(bearer),db:Session=Depends(get_db)):
    session_raw=request.cookies.get("app_session")
    if session_raw and not creds:
        row=db.query(ApplicationSession).filter_by(token_hash=session_digest(session_raw),revoked_at=None).first()
        if row and aware(row.expires_at)>datetime.now(timezone.utc):
            legacy=db.get(AdminUser,row.user_id)
            if legacy and legacy.is_active:return legacy
        raise HTTPException(401,"invalid application session")
    if not creds: raise HTTPException(401,"authentication required")
    try: data=decode(creds.credentials,"admin",settings.admin_session_secret)
    except Exception: raise HTTPException(401,"invalid authentication")
    user=db.get(AdminUser,data.get("sub"))
    if not user or not user.is_active: raise HTTPException(401,"invalid authentication")
    return user
def candidate(creds:HTTPAuthorizationCredentials=Depends(bearer),db:Session=Depends(get_db)):
    if not creds: raise HTTPException(401,"candidate authentication required")
    try: data=decode(creds.credentials,"candidate",settings.invite_token_secret)
    except Exception: raise HTTPException(401,"invalid candidate authentication")
    if data.get("role")!="candidate": raise HTTPException(401,"invalid candidate authentication")
    item=db.get(InterviewSession,data.get("session_id"))
    if not item: raise HTTPException(403,"session access denied")
    advance(item); db.commit()
    return item
def audit(db,event,actor=None,session_id=None,metadata=None): db.add(AuditEvent(event_type=event,actor_id=getattr(actor,"id",None),actor_role=getattr(actor,"role",None),session_id=session_id,metadata_json=metadata or {}))
def aware(value): return value if value.tzinfo else value.replace(tzinfo=timezone.utc)
def advance(item):
    now=datetime.now(timezone.utc)
    if item.state==SessionState.scheduled and aware(item.scheduled_at)<=now:
        item.state=SessionState.active; item.started_at=item.started_at or now; item.end_at=item.end_at or now+timedelta(minutes=item.duration_minutes)
    if item.state==SessionState.active and item.end_at and aware(item.end_at)<=now: item.state=SessionState.expired
    return item
async def broadcast(sid,message):
    stale=[]
    for peer in list(connections[sid]):
        try: await peer.send_json(message)
        except Exception: stale.append(peer)
    for peer in stale:
        connections[sid].discard(peer)
        connection_meta.pop(peer,None)
def login_allowed(key,limit=10):
    now=datetime.now(timezone.utc); q=login_attempts[key]
    while q and q[0] < now-timedelta(minutes=1): q.popleft()
    if len(q)>=limit: return False
    q.append(now); return True
def invite_allowed(key):
    now=datetime.now(timezone.utc); q=invite_attempts[key]
    while q and q[0] < now-timedelta(minutes=1): q.popleft()
    if len(q)>=20: return False
    q.append(now); return True
def invite_session_joinable(item):
    return item.state in {SessionState.scheduled, SessionState.active, SessionState.expired}
def create_invite(item, user, db):
    raw=random_token(); expiry=datetime.now(timezone.utc)+timedelta(minutes=settings.invite_expiry_minutes)
    db.add(SessionInvite(session_id=item.id,token_hash=digest(raw),expires_at=expiry)); audit(db,"invite.created",user,item.id); db.commit()
    return {"url":f"{settings.frontend_url.rstrip('/')}/invite/{raw}","expires_at":expiry}
@app.get("/health")
def health(db:Session=Depends(get_db)):
    try: db.execute(text("SELECT 1")); return {"ok":True}
    except Exception: raise HTTPException(503,"database unavailable")
def issue_application_session(db:Session,user_id:str,response:Response):
    raw=random_token(); csrf=csrf_token(); now=datetime.now(timezone.utc)
    previous=db.query(ApplicationSession).filter(ApplicationSession.user_id==user_id,ApplicationSession.revoked_at.is_(None)).order_by(ApplicationSession.created_at.desc()).first()
    if previous: previous.revoked_at=now
    db.add(ApplicationSession(user_id=user_id,token_hash=session_digest(raw),csrf_hash=session_digest(csrf),created_at=now,expires_at=now+timedelta(minutes=settings.app_session_ttl_minutes),rotated_from=previous.id if previous else None))
    response.set_cookie("app_session",raw,max_age=settings.app_session_ttl_minutes*60,httponly=True,secure=settings.app_cookie_secure,samesite="lax",domain=settings.app_cookie_domain)
    response.set_cookie("app_csrf",csrf,max_age=settings.app_session_ttl_minutes*60,httponly=False,secure=settings.app_cookie_secure,samesite="lax",domain=settings.app_cookie_domain)

@app.post("/auth/login")
def login(payload:Login,response:Response,request:Request,db:Session=Depends(get_db)):
    risk=verify_recaptcha(payload.recaptcha_token,"login",settings)
    if risk["decision"]=="unavailable": raise HTTPException(503,"verification temporarily unavailable")
    if risk["decision"]!="allow": raise HTTPException(429 if risk["decision"]=="step_up" else 401,"authentication could not be verified")
    ip=request.client.host if request.client else "unknown"
    if not login_allowed(payload.email.lower()) or not login_allowed(f"ip:{ip}",30): raise HTTPException(429,"too many login attempts; retry later")
    user=db.query(AdminUser).filter_by(email=payload.email).first()
    if not user or not verify_password(payload.password,user.password_hash): raise HTTPException(401,"invalid credentials")
    app_user=db.get(ApplicationUser,user.id)
    if not app_user:
        db.add(ApplicationUser(id=user.id,email=user.email,email_verified=True,role=user.role,status="active"))
        db.flush()
    issue_application_session(db,user.id,response); audit(db,"auth.login",user,metadata={"risk_band":risk.get("decision")}); db.commit()
    return {"access_token":token("admin",{"sub":user.id},480,settings.admin_session_secret),"token_type":"bearer","session":True}

@app.get("/auth/session")
def current_session(request:Request,db:Session=Depends(get_db)):
    raw=request.cookies.get("app_session")
    row=db.query(ApplicationSession).filter_by(token_hash=session_digest(raw or ""),revoked_at=None).first() if raw else None
    if not row or aware(row.expires_at)<=datetime.now(timezone.utc): raise HTTPException(401,"no active session")
    user=db.get(ApplicationUser,row.user_id)
    if not user or user.status!="active": raise HTTPException(401,"no active session")
    return {"id":user.id,"email":user.email,"role":user.role}

@app.post("/auth/logout")
def logout(request:Request,response:Response,db:Session=Depends(get_db)):
    raw=request.cookies.get("app_session"); row=db.query(ApplicationSession).filter_by(token_hash=session_digest(raw or ""),revoked_at=None).first() if raw else None
    if row: row.revoked_at=datetime.now(timezone.utc); audit(db,"auth.logout",session_id=row.user_id); db.commit()
    response.delete_cookie("app_session",domain=settings.app_cookie_domain); response.delete_cookie("app_csrf",domain=settings.app_cookie_domain)
    return {"ok":True}

@app.post("/auth/google")
def google_login(payload:dict,response:Response,db:Session=Depends(get_db)):
    risk=verify_recaptcha(payload.get("recaptcha_token"),"login",settings)
    if risk["decision"]=="unavailable": raise HTTPException(503,"verification temporarily unavailable")
    if risk["decision"]!="allow": raise HTTPException(429 if risk["decision"]=="step_up" else 401,"provider authentication failed")
    try: claims=verify_google_credential(payload.get("credential"),settings)
    except Exception: raise HTTPException(401,"provider authentication failed")
    email=claims["email"].lower(); subject=claims["sub"]
    if settings.google_allowed_domains and email.rsplit("@",1)[-1] not in {x.strip().lower() for x in settings.google_allowed_domains.split(",")}: raise HTTPException(403,"account not approved")
    identity=db.query(ExternalIdentity).filter_by(provider="google",provider_subject=subject).first()
    if identity: user=db.get(ApplicationUser,identity.user_id)
    else:
        existing=db.query(ApplicationUser).filter_by(email=email).first()
        if existing:
            audit(db,"auth.account_link.denied",session_id=existing.id,metadata={"provider":"google","reason":"email_only_linking"}); db.commit()
            raise HTTPException(409,"account linking requires an authenticated account")
        user=ApplicationUser(email=email,email_verified=True,role="admin",status="active" if settings.google_auto_approve else "pending"); db.add(user); db.flush()
        db.add(ExternalIdentity(user_id=user.id,provider="google",provider_subject=subject,provider_email=email))
    if not user or user.status!="active": raise HTTPException(403,"account not approved")
    legacy=db.get(AdminUser,user.id)
    if not legacy: db.add(AdminUser(id=user.id,email=user.email,password_hash=hash_password(random_token()),role=user.role,is_active=True))
    issue_application_session(db,user.id,response); audit(db,"auth.google.verified",session_id=user.id,metadata={"provider":"google","decision":"allow","risk_band":risk.get("decision")}); db.commit()
    return {"user":{"id":user.id,"email":user.email,"role":user.role},"authenticated":True}
def serialize(item): return SessionOut(id=item.id,state=item.state.value,candidate_name=item.candidate_name,candidate_email=item.candidate_email,scheduled_at=item.scheduled_at,duration_minutes=item.duration_minutes,facilitator_id=item.facilitator_id,end_at=item.end_at)
def validate_facilitator(facilitator_id,db):
    if facilitator_id and not db.get(AdminUser,facilitator_id): raise HTTPException(422,"facilitator_id does not identify an administrator")
@app.post("/admin/sessions",response_model=SessionOut)
def create_session(payload:SessionIn,user=Depends(admin),db:Session=Depends(get_db)):
    validate_facilitator(payload.facilitator_id,db)
    item=InterviewSession(**payload.model_dump()); db.add(item); db.commit(); db.refresh(item); return serialize(item)
@app.get("/admin/sessions",response_model=list[SessionOut])
def list_sessions(user=Depends(admin),db:Session=Depends(get_db)): return [serialize(x) for x in db.query(InterviewSession).all()]
@app.get("/admin/sessions/{sid}",response_model=SessionOut)
def get_session(sid,user=Depends(admin),db:Session=Depends(get_db)):
    item=db.get(InterviewSession,sid)
    if not item: raise HTTPException(404,"session not found")
    advance(item); db.commit()
    return serialize(item)
@app.patch("/admin/sessions/{sid}",response_model=SessionOut)
def update_session(sid,payload:SessionIn,user=Depends(admin),db:Session=Depends(get_db)):
    item=db.get(InterviewSession,sid)
    if not item: raise HTTPException(404,"session not found")
    if item.state!=SessionState.scheduled: raise HTTPException(409,"only scheduled sessions can be edited")
    validate_facilitator(payload.facilitator_id,db)
    for k,v in payload.model_dump().items(): setattr(item,k,v)
    db.commit(); return serialize(item)
@app.post("/admin/sessions/{sid}/invite",response_model=InviteOut)
def invite(sid,user=Depends(admin),db:Session=Depends(get_db)):
    item=db.get(InterviewSession,sid)
    if not item: raise HTTPException(404,"session not found")
    advance(item)
    if not invite_session_joinable(item): raise HTTPException(409,"invites cannot be generated for completed sessions")
    return create_invite(item,user,db)
@app.post("/invites/redeem")
def redeem(body:dict,request:Request,db:Session=Depends(get_db)):
    if not invite_allowed(request.client.host if request.client else "unknown"): raise HTTPException(429,"invalid invitation")
    risk=verify_recaptcha(body.get("recaptcha_token"),"invite_redeem",settings)
    if risk["decision"]=="unavailable": raise HTTPException(503,"verification temporarily unavailable")
    if risk["decision"]!="allow": raise HTTPException(429 if risk["decision"]=="step_up" else 400,"invalid invitation")
    raw=body.get("token",""); row=db.query(SessionInvite).filter_by(token_hash=digest(raw)).first()
    if not row: raise HTTPException(400,"invalid invitation")
    if row.revoked: raise HTTPException(400,"revoked invitation")
    if row.redeemed_at: raise HTTPException(400,"already-used invitation")
    if aware(row.expires_at)<=datetime.now(timezone.utc): raise HTTPException(400,"expired invitation")
    item=db.get(InterviewSession,row.session_id)
    if not item or item.state==SessionState.completed: raise HTTPException(400,"invalid invitation")
    row.redeemed_at=datetime.now(timezone.utc); audit(db,"invite.redeemed",session_id=row.session_id); db.commit()
    return {"candidate_token":token("candidate",{"session_id":row.session_id,"role":"candidate"},60,settings.invite_token_secret),"session_id":row.session_id}
@app.get("/scorecards/default",response_model=list[ScorecardCategory])
def scorecard_categories(user=Depends(admin)): return DEFAULT_CATEGORIES
@app.post("/admin/sessions/{sid}/evaluation")
def submit_evaluation(sid,payload:EvaluationIn,user=Depends(admin),db:Session=Depends(get_db)):
    item=db.get(InterviewSession,sid); advance(item) if item else None
    if not item or item.state!=SessionState.completed: raise HTTPException(409,"evaluation requires a completed session")
    valid={x["name"] for x in DEFAULT_CATEGORIES}; received={x.get("category") for x in payload.scores}
    if len(payload.scores)!=len(valid) or received!=valid or any(not isinstance(x.get("rating"),int) or not 1<=x["rating"]<=5 or not x.get("rationale") for x in payload.scores): raise HTTPException(422,"all scorecard categories require ratings from 1 to 5 and rationale")
    if payload.recommendation not in {"hire","no-hire","strong-hire","strong-no-hire"}: raise HTTPException(422,"invalid recommendation")
    evaluation=Evaluation(session_id=sid,evaluator_id=user.id,recommendation=payload.recommendation,overall_rating=payload.overall_rating,overall_notes=payload.overall_notes); db.add(evaluation); db.flush()
    for score in payload.scores: db.add(EvaluationScore(evaluation_id=evaluation.id,category=score["category"],rating=score["rating"],rationale=score["rationale"]))
    if payload.private_notes: db.add(EvaluationNote(evaluation_id=evaluation.id,author_id=user.id,note=payload.private_notes))
    audit(db,"evaluation.submitted",user,sid); db.commit(); return {"id":evaluation.id,"submitted_at":evaluation.submitted_at}
@app.get("/admin/sessions/{sid}/evaluation")
def get_evaluation(sid,user=Depends(admin),db:Session=Depends(get_db)):
    evaluation=db.query(Evaluation).filter_by(session_id=sid).order_by(Evaluation.submitted_at.desc()).first()
    if not evaluation: raise HTTPException(404,"evaluation not found")
    return {"id":evaluation.id,"recommendation":evaluation.recommendation,"overall_rating":evaluation.overall_rating,"overall_notes":evaluation.overall_notes,"scores":[{"category":x.category,"rating":x.rating,"rationale":x.rationale} for x in db.query(EvaluationScore).filter_by(evaluation_id=evaluation.id).all()],"private_notes":[x.note for x in db.query(EvaluationNote).filter_by(evaluation_id=evaluation.id).all()]}
@app.get("/sessions/{sid}")
def candidate_session(sid,user=Depends(candidate)):
    if user.id!=sid: raise HTTPException(403,"session access denied")
    return {"id":user.id,"candidate_name":user.candidate_name,"state":user.state.value,"scheduled_at":user.scheduled_at,"duration_minutes":user.duration_minutes,"end_at":user.end_at}
@app.post("/sessions/{sid}/canvas-token")
def candidate_canvas_token(sid,user=Depends(candidate)):
    if user.id!=sid: raise HTTPException(403,"session access denied")
    if user.state==SessionState.completed: raise HTTPException(403,"session ended")
    return {"token":token("canvas",{"session_id":sid,"role":"candidate"},5,settings.canvas_token_secret),"room":sid}
@app.post("/admin/sessions/{sid}/invite/revoke")
def revoke_invites(sid,user=Depends(admin),db:Session=Depends(get_db)):
    rows=db.query(SessionInvite).filter_by(session_id=sid,revoked=False).all()
    for row in rows: row.revoked=True
    audit(db,"invite.revoked",user,sid,{"count":len(rows)}); db.commit(); return {"revoked":len(rows)}
@app.get("/admin/sessions/{sid}/invites")
def list_invites(sid,user=Depends(admin),db:Session=Depends(get_db)):
    return [{"id":row.id,"expires_at":row.expires_at,"redeemed":bool(row.redeemed_at),"revoked":row.revoked,"active":not row.revoked and not row.redeemed_at and aware(row.expires_at)>datetime.now(timezone.utc)} for row in db.query(SessionInvite).filter_by(session_id=sid).order_by(SessionInvite.created_at.desc()).all()]
@app.post("/admin/sessions/{sid}/invite/regenerate",response_model=InviteOut)
def regenerate_invite(sid,user=Depends(admin),db:Session=Depends(get_db)):
    item=db.get(InterviewSession,sid)
    if not item: raise HTTPException(404,"session not found")
    advance(item)
    if not invite_session_joinable(item): raise HTTPException(409,"invites cannot be regenerated for completed sessions")
    rows=db.query(SessionInvite).filter_by(session_id=sid,revoked=False).all()
    for row in rows: row.revoked=True
    audit(db,"invite.revoked",user,sid,{"count":len(rows),"reason":"regenerated"})
    db.flush()
    return create_invite(item,user,db)
@app.post("/admin/sessions/{sid}/end")
def end(sid,user=Depends(admin),db:Session=Depends(get_db)):
    item=db.get(InterviewSession,sid)
    if not item or item.state not in [SessionState.scheduled,SessionState.active,SessionState.expired]: raise HTTPException(409,"invalid lifecycle transition")
    item.state=SessionState.completed; item.completed_at=datetime.now(timezone.utc); audit(db,"session.ended",user,sid); db.commit(); return serialize(item)
@app.post("/admin/sessions/{sid}/extend")
def extend(sid,payload:ExtensionIn,user=Depends(admin),db:Session=Depends(get_db)):
    item=db.get(InterviewSession,sid)
    if not item or item.state!=SessionState.expired: raise HTTPException(409,"session is not awaiting extension")
    item.state=SessionState.active; item.end_at=(item.end_at or datetime.now(timezone.utc))+timedelta(minutes=payload.minutes); db.add(SessionExtension(session_id=sid,minutes=payload.minutes,initiated_by=user.id)); audit(db,"session.extended",user,sid,{"minutes":payload.minutes}); db.commit(); return serialize(item)
@app.post("/admin/sessions/{sid}/canvas-token")
def canvas_token(sid,user=Depends(admin),db:Session=Depends(get_db)):
    if not db.get(InterviewSession,sid): raise HTTPException(404,"session not found")
    return {"token":token("canvas",{"session_id":sid,"role":"facilitator"},5,settings.canvas_token_secret),"room":sid}
@app.get("/admin/sessions/{sid}/audit")
def audit_log(sid,user=Depends(admin),db:Session=Depends(get_db)): return db.query(AuditEvent).filter_by(session_id=sid).all()
@app.websocket("/ws/sessions/{sid}")
async def websocket(ws:WebSocket,sid:str):
    allowed_origins={origin.strip() for origin in settings.ws_allowed_origins.split(",") if origin.strip()}
    if ws.headers.get("origin") and ws.headers.get("origin") not in allowed_origins: await ws.close(code=1008); return
    raw=ws.query_params.get("token") or ws.headers.get("authorization","").removeprefix("Bearer ")
    role=None
    data=None
    db=None
    cookie_session=ws.cookies.get("app_session")
    if not raw and cookie_session:
        db=SessionLocal(); row=db.query(ApplicationSession).filter_by(token_hash=session_digest(cookie_session),revoked_at=None).first()
        if row and aware(row.expires_at)>datetime.now(timezone.utc): data={"sub":row.user_id}; role="admin"
        else: db.close(); await ws.close(code=1008); return
    else:
        try:
            data=decode(raw,"admin",settings.admin_session_secret); role="admin"
        except Exception:
            try:
                data=decode(raw,"candidate",settings.invite_token_secret); role="candidate"
            except Exception: await ws.close(code=1008); return
    db=db or SessionLocal(); item=db.get(InterviewSession,sid); advance(item) if item else None; db.commit()
    if data.get("session_id") and data.get("session_id")!=sid or not item:
        db.close(); await ws.close(code=1008); return
    display_name="Facilitator"
    actor_id=data.get("sub")
    if role=="admin":
        administrator=db.get(AdminUser,actor_id)
        if not administrator or not administrator.is_active:
            db.close(); await ws.close(code=1008); return
        display_name=administrator.email
    else:
        display_name=item.candidate_name
    await ws.accept(); connections[sid].add(ws); connection_meta[ws]={"role":role,"display_name":display_name,"participant_id":None}
    participant=SessionParticipant(session_id=sid,role=role,display_name=display_name)
    db.add(participant); db.commit(); connection_meta[ws]["participant_id"]=participant.id
    print(f"session websocket connected session={sid} role={role}")
    await broadcast(sid,{"type":"presence","session_id":sid,"role":role,"display_name":display_name,"status":"joined"})
    await ws.send_json({"type":"session","state":item.state.value,"end_at":item.end_at.isoformat() if item.end_at else None})
    try:
        previous=item.state.value
        while True:
            try: message=await asyncio.wait_for(ws.receive_json(),timeout=1)
            except asyncio.TimeoutError: message=None
            if message and message.get("type") in {"end","extend"}:
                if role!="admin":
                    await ws.send_json({"type":"error","message":"facilitator authorization required"})
                else:
                    current=db.get(InterviewSession,sid)
                    if message.get("type")=="end" and current and current.state in [SessionState.scheduled,SessionState.active,SessionState.expired]:
                        current.state=SessionState.completed; current.completed_at=datetime.now(timezone.utc); audit(db,"session.ended",administrator,sid); db.commit()
                    elif message.get("type")=="extend" and current and current.state==SessionState.expired:
                        try: minutes=int(message.get("minutes"))
                        except (TypeError,ValueError): minutes=0
                        if not 0<minutes<=240: await ws.send_json({"type":"error","message":"extension must be a positive duration"})
                        else:
                            current.state=SessionState.active; current.end_at=(current.end_at or datetime.now(timezone.utc))+timedelta(minutes=minutes); db.add(SessionExtension(session_id=sid,minutes=minutes,initiated_by=administrator.id)); audit(db,"session.extended",administrator,sid,{"minutes":minutes}); db.commit()
                    elif message.get("type")=="end": await ws.send_json({"type":"error","message":"invalid lifecycle transition"})
                    elif message.get("type")=="extend": await ws.send_json({"type":"error","message":"session is not awaiting extension"})
            db.expire_all(); current=db.get(InterviewSession,sid); advance(current) if current else None; db.commit()
            state=current.state.value if current else "denied"
            if state!=previous:
                await broadcast(sid,{"type":"session","state":state,"end_at":current.end_at.isoformat() if current and current.end_at else None}); previous=state
    except WebSocketDisconnect:
        connections[sid].discard(ws)
        participant_id=connection_meta.get(ws,{}).get("participant_id")
        if participant_id:
            row=db.get(SessionParticipant,participant_id)
            if row: row.left_at=datetime.now(timezone.utc); db.commit()
        metadata=connection_meta.pop(ws,{"role":role,"display_name":display_name})
        await broadcast(sid,{"type":"presence","session_id":sid,"role":metadata.get("role"),"display_name":metadata.get("display_name"),"status":"left"})
        print(f"session websocket disconnected session={sid} role={role}")
        db.close()
        return
