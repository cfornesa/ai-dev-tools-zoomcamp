from datetime import datetime, timedelta, timezone
import os
import asyncio
from collections import defaultdict, deque
from fastapi import Depends, FastAPI, HTTPException, WebSocket, WebSocketDisconnect
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
connections=defaultdict(set)
DEFAULT_CATEGORIES=[{"name":"problem solving","description":"Frames problems and reasons through trade-offs."},{"name":"technical fundamentals","description":"Demonstrates relevant technical knowledge."},{"name":"communication","description":"Explains thinking clearly and collaborates effectively."},{"name":"collaboration","description":"Works constructively with the interviewer."}]

@app.on_event("startup")
def seed_dev_admin():
    email,password=os.getenv("DEV_ADMIN_EMAIL"),os.getenv("DEV_ADMIN_PASSWORD")
    if email and password:
        db=SessionLocal()
        if not db.query(AdminUser).filter_by(email=email).first(): db.add(AdminUser(email=email,password_hash=hash_password(password))); db.commit()
        db.close()

def admin(creds:HTTPAuthorizationCredentials=Depends(bearer),db:Session=Depends(get_db)):
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
    item=db.get(InterviewSession,data.get("session_id"))
    if not item or item.state==SessionState.completed: raise HTTPException(403,"session access denied")
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
def login_allowed(key):
    now=datetime.now(timezone.utc); q=login_attempts[key]
    while q and q[0] < now-timedelta(minutes=1): q.popleft()
    if len(q)>=10: return False
    q.append(now); return True
@app.get("/health")
def health(db:Session=Depends(get_db)):
    try: db.execute(text("SELECT 1")); return {"ok":True}
    except Exception: raise HTTPException(503,"database unavailable")
@app.post("/auth/login")
def login(payload:Login,db:Session=Depends(get_db)):
    if not login_allowed(payload.email.lower()): raise HTTPException(429,"too many login attempts; retry later")
    user=db.query(AdminUser).filter_by(email=payload.email).first()
    if not user or not verify_password(payload.password,user.password_hash): raise HTTPException(401,"invalid credentials")
    return {"access_token":token("admin",{"sub":user.id},480,settings.admin_session_secret),"token_type":"bearer"}
def serialize(item): return SessionOut(id=item.id,state=item.state.value,candidate_name=item.candidate_name,candidate_email=item.candidate_email,scheduled_at=item.scheduled_at,duration_minutes=item.duration_minutes,facilitator_id=item.facilitator_id,end_at=item.end_at)
@app.post("/admin/sessions",response_model=SessionOut)
def create_session(payload:SessionIn,user=Depends(admin),db:Session=Depends(get_db)):
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
    for k,v in payload.model_dump().items(): setattr(item,k,v)
    db.commit(); return serialize(item)
@app.post("/admin/sessions/{sid}/invite",response_model=InviteOut)
def invite(sid,user=Depends(admin),db:Session=Depends(get_db)):
    item=db.get(InterviewSession,sid)
    if not item: raise HTTPException(404,"session not found")
    raw=random_token(); expiry=datetime.now(timezone.utc)+timedelta(minutes=settings.invite_expiry_minutes)
    db.add(SessionInvite(session_id=sid,token_hash=digest(raw),expires_at=expiry)); audit(db,"invite.created",user,sid); db.commit()
    return {"url":f"http://localhost:5173/invite/{raw}","expires_at":expiry}
@app.post("/invites/redeem")
def redeem(body:dict,db:Session=Depends(get_db)):
    raw=body.get("token",""); row=db.query(SessionInvite).filter_by(token_hash=digest(raw)).first()
    if not row: raise HTTPException(400,"invalid invitation")
    if row.revoked: raise HTTPException(400,"revoked invitation")
    if row.redeemed_at: raise HTTPException(400,"already-used invitation")
    if aware(row.expires_at)<=datetime.now(timezone.utc): raise HTTPException(400,"expired invitation")
    row.redeemed_at=datetime.now(timezone.utc); audit(db,"invite.redeemed",session_id=row.session_id); db.commit()
    return {"candidate_token":token("candidate",{"session_id":row.session_id,"role":"candidate"},60,settings.invite_token_secret),"session_id":row.session_id}
@app.get("/scorecards/default",response_model=list[ScorecardCategory])
def scorecard_categories(user=Depends(admin)): return DEFAULT_CATEGORIES
@app.post("/admin/sessions/{sid}/evaluation")
def submit_evaluation(sid,payload:EvaluationIn,user=Depends(admin),db:Session=Depends(get_db)):
    item=db.get(InterviewSession,sid); advance(item) if item else None
    if not item or item.state!=SessionState.completed: raise HTTPException(409,"evaluation requires a completed session")
    valid={x["name"] for x in DEFAULT_CATEGORIES}; received={x.get("category") for x in payload.scores}
    if received!=valid or any(not isinstance(x.get("rating"),int) or not 1<=x["rating"]<=5 or not x.get("rationale") for x in payload.scores): raise HTTPException(422,"all scorecard categories require ratings from 1 to 5 and rationale")
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
    revoke_invites(sid,user,db)
    return invite(sid,user,db)
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
    if ws.headers.get("origin") and ws.headers.get("origin") not in settings.ws_allowed_origins.split(","): await ws.close(code=1008); return
    raw=ws.query_params.get("token") or ws.headers.get("authorization","").removeprefix("Bearer ")
    role=None
    try:
        data=decode(raw,"admin",settings.admin_session_secret); role="admin"
    except Exception:
        try:
            data=decode(raw,"candidate",settings.invite_token_secret); role="candidate"
        except Exception: await ws.close(code=1008); return
    if data.get("session_id") and data.get("session_id")!=sid: await ws.close(code=1008); return
    await ws.accept(); connections[sid].add(ws)
    await ws.send_json({"type":"presence","session_id":sid,"role":role,"status":"joined"})
    db=SessionLocal(); item=db.get(InterviewSession,sid); advance(item) if item else None; db.commit()
    await ws.send_json({"type":"session","state":item.state.value if item else "denied","end_at":item.end_at.isoformat() if item and item.end_at else None})
    try:
        previous=item.state.value if item else "denied"
        while True:
            try: message=await asyncio.wait_for(ws.receive_json(),timeout=1)
            except asyncio.TimeoutError: message=None
            if message and message.get("type") in {"end","extend"} and role!="admin": await ws.send_json({"type":"error","message":"facilitator authorization required"})
            db.expire_all(); current=db.get(InterviewSession,sid); advance(current) if current else None; db.commit()
            state=current.state.value if current else "denied"
            if state!=previous:
                await ws.send_json({"type":"session","state":state,"end_at":current.end_at.isoformat() if current and current.end_at else None}); previous=state
    except WebSocketDisconnect:
        connections[sid].discard(ws)
        db.close()
        return
