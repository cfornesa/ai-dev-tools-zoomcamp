from datetime import datetime, timedelta, timezone
from app.db import SessionLocal
from app.models import AuditEvent, InterviewSession, SessionInvite, SessionParticipant
from app.config import settings
from app.security import _used_recaptcha, verify_recaptcha
from app import security
import json

def auth(client):
    response=client.post("/auth/login",json={"email":"admin@example.test","password":"correct-horse"})
    assert response.status_code==200
    return {"Authorization":f"Bearer {response.json()['access_token']}"}

def session_payload(): return {"candidate_name":"Candidate","candidate_email":"candidate@example.test","scheduled_at":(datetime.now(timezone.utc)+timedelta(hours=1)).isoformat(),"duration_minutes":45}

def test_health_and_protected_access(client):
    assert client.get("/health").json()=={"ok":True}
    assert client.get("/admin/sessions").status_code==401
    assert auth(client)

def test_cookie_session_is_current_revocable_and_csrf_protected(client):
    response=client.post("/auth/login",json={"email":"admin@example.test","password":"correct-horse"})
    assert response.status_code==200 and response.cookies.get("app_session")
    assert client.get("/auth/session").status_code==200
    assert client.post("/admin/sessions",json=session_payload()).status_code==403
    csrf=response.cookies.get("app_csrf")
    allowed=client.post("/admin/sessions",json=session_payload(),headers={"X-CSRF-Token":csrf})
    assert allowed.status_code==200
    assert client.post("/auth/logout",headers={"X-CSRF-Token":csrf}).json()=={"ok":True}
    assert client.get("/auth/session").status_code==401

def test_cookie_session_can_authorize_websocket_without_bearer_token(client):
    response=client.post("/auth/login",json={"email":"admin@example.test","password":"correct-horse"})
    assert response.status_code==200
    created=client.post("/admin/sessions",json=session_payload(),headers={"X-CSRF-Token":response.cookies.get("app_csrf")}).json()
    with client.websocket_connect(f"/ws/sessions/{created['id']}",headers={"Origin":"http://localhost:5173"}) as socket:
        assert socket.receive_json()["role"]=="admin"
        assert socket.receive_json()["type"]=="session"

def test_google_mock_verification_identity_uniqueness_and_safe_linking(client):
    previous=(settings.google_provider_mode,settings.google_auto_approve)
    settings.google_provider_mode="mock"; settings.google_auto_approve=True
    try:
        first=client.post("/auth/google",json={"credential":"mock:google-sub-1:person@example.test:verified"})
        assert first.status_code==200 and first.json()["user"]["email"]=="person@example.test"
        assert client.get("/auth/session").status_code==200
        repeat=client.post("/auth/google",json={"credential":"mock:google-sub-1:person@example.test:verified"})
        assert repeat.status_code==200
        assert client.post("/auth/google",json={"credential":"mock:google-sub-2:person@example.test:verified"}).status_code==409
        assert client.post("/auth/google",json={"credential":"mock:google-sub-3:other@example.test:unverified"}).status_code==401
    finally:
        settings.google_provider_mode,settings.google_auto_approve=previous

def test_recaptcha_mock_bands_replay_and_action_boundaries(client):
    _used_recaptcha.clear(); previous=settings.recaptcha_mode; settings.recaptcha_mode="mock"
    try:
        assert verify_recaptcha("mock:allow:one","login",settings)["decision"]=="allow"
        assert verify_recaptcha("mock:allow:one","login",settings)["decision"]=="deny"
        assert verify_recaptcha("mock:step_up:two","invite_redeem",settings)["decision"]=="step_up"
        assert verify_recaptcha("mock:deny:three","login",settings)["decision"]=="deny"
    finally: settings.recaptcha_mode=previous; _used_recaptcha.clear()

def test_recaptcha_real_verification_checks_action_host_freshness_score_and_outage(monkeypatch):
    class Reply:
        def __init__(self,body): self.body=body
        def __enter__(self): return self
        def __exit__(self,*args): return False
        def read(self): return self.body
    previous=(settings.recaptcha_mode,settings.recaptcha_secret,settings.recaptcha_allowed_hostnames)
    settings.recaptcha_mode="real"; settings.recaptcha_secret="test-secret"; settings.recaptcha_allowed_hostnames="app.example.test"; _used_recaptcha.clear()
    try:
        now=datetime.now(timezone.utc).isoformat().replace("+00:00","Z")
        result={"success":True,"action":"login","hostname":"app.example.test","challenge_ts":now,"score":0.9}
        monkeypatch.setattr(security.urllib.request,"urlopen",lambda *args,**kwargs:Reply(json.dumps(result).encode()))
        assert verify_recaptcha("real-token","login",settings)["decision"]=="allow"
        assert verify_recaptcha("real-token-2","wrong",settings)["decision"]=="deny"
        result["action"]="wrong"; assert verify_recaptcha("real-token-3","login",settings)["decision"]=="deny"
        result["action"]="login"; result["hostname"]="evil.example"; assert verify_recaptcha("real-token-4","login",settings)["decision"]=="deny"
        result["hostname"]="app.example.test"; result["score"]=0.2; assert verify_recaptcha("real-token-5","login",settings)["decision"]=="deny"
        monkeypatch.setattr(security.urllib.request,"urlopen",lambda *args,**kwargs:(_ for _ in ()).throw(TimeoutError()))
        assert verify_recaptcha("real-token-6","login",settings)["decision"]=="unavailable"
    finally:
        settings.recaptcha_mode,settings.recaptcha_secret,settings.recaptcha_allowed_hostnames=previous; _used_recaptcha.clear()

def test_invalid_login_and_rate_limit(client):
    assert client.post("/auth/login",json={"email":"admin@example.test","password":"wrong"}).status_code==401
    for _ in range(10): client.post("/auth/login",json={"email":"rate@example.test","password":"wrong"})
    assert client.post("/auth/login",json={"email":"rate@example.test","password":"wrong"}).status_code==429

def test_session_invite_and_raw_token_is_not_persisted(client):
    headers=auth(client)
    created=client.post("/admin/sessions",json=session_payload(),headers=headers)
    assert created.status_code==200 and created.json()["state"]=="scheduled"
    invite=client.post(f"/admin/sessions/{created.json()['id']}/invite",headers=headers)
    assert invite.status_code==200
    raw=invite.json()["url"].rsplit("/",1)[-1]
    with SessionLocal() as db:
        row=db.query(SessionInvite).one()
        assert raw not in row.token_hash
    redeemed=client.post("/invites/redeem",json={"token":raw})
    assert redeemed.status_code==200 and redeemed.json()["session_id"]==created.json()["id"]

def test_session_crud_validation_and_update(client):
    headers=auth(client)
    assert client.post("/admin/sessions",json={"candidate_name":"","duration_minutes":0},headers=headers).status_code==422
    created=client.post("/admin/sessions",json=session_payload(),headers=headers).json()
    assert len(client.get("/admin/sessions",headers=headers).json())==1
    assert client.get(f"/admin/sessions/{created['id']}",headers=headers).status_code==200
    updated={**session_payload(),"candidate_name":"Updated Candidate"}
    response=client.patch(f"/admin/sessions/{created['id']}",json=updated,headers=headers)
    assert response.status_code==200,response.text
    assert response.json()["candidate_name"]=="Updated Candidate"

def test_session_facilitator_reference_is_validated_without_partial_create(client):
    headers=auth(client)
    response=client.post("/admin/sessions",json={**session_payload(),"facilitator_id":"missing-admin"},headers=headers)
    assert response.status_code==422
    assert client.get("/admin/sessions",headers=headers).json()==[]

def test_invite_revoke_and_regenerate(client):
    headers=auth(client); created=client.post("/admin/sessions",json=session_payload(),headers=headers).json()
    first=client.post(f"/admin/sessions/{created['id']}/invite",headers=headers).json(); raw=first["url"].rsplit("/",1)[-1]
    assert client.post(f"/admin/sessions/{created['id']}/invite/revoke",headers=headers).status_code==200
    assert client.post("/invites/redeem",json={"token":raw}).status_code==400
    second=client.post(f"/admin/sessions/{created['id']}/invite/regenerate",headers=headers).json()
    assert second["url"]!=first["url"] and client.post("/invites/redeem",json={"token":second["url"].rsplit("/",1)[-1]}).status_code==200

def test_expired_invite_is_rejected(client):
    headers=auth(client); created=client.post("/admin/sessions",json=session_payload(),headers=headers).json(); result=client.post(f"/admin/sessions/{created['id']}/invite",headers=headers).json(); raw=result["url"].rsplit("/",1)[-1]
    with SessionLocal() as db:
        row=db.query(SessionInvite).one(); row.expires_at=datetime.now(timezone.utc)-timedelta(minutes=1); db.commit()
    assert client.post("/invites/redeem",json={"token":raw}).status_code==400

def test_joinable_sessions_can_replace_invites_but_completed_sessions_cannot(client):
    headers=auth(client)
    created=client.post("/admin/sessions",json={**session_payload(),"scheduled_at":(datetime.now(timezone.utc)-timedelta(minutes=2)).isoformat()},headers=headers).json()
    first=client.post(f"/admin/sessions/{created['id']}/invite",headers=headers)
    assert first.status_code==200
    second=client.post(f"/admin/sessions/{created['id']}/invite/regenerate",headers=headers)
    assert second.status_code==200 and second.json()["url"]!=first.json()["url"]
    old_raw=first.json()["url"].rsplit("/",1)[-1]
    assert client.post("/invites/redeem",json={"token":old_raw}).status_code==400
    assert client.post(f"/admin/sessions/{created['id']}/end",headers=headers).status_code==200
    assert client.post(f"/admin/sessions/{created['id']}/invite",headers=headers).status_code==409
    assert client.post(f"/admin/sessions/{created['id']}/invite/regenerate",headers=headers).status_code==409

def test_candidate_credential_is_scoped_to_one_session(client):
    headers=auth(client); first=client.post("/admin/sessions",json=session_payload(),headers=headers).json(); second=client.post("/admin/sessions",json={**session_payload(),"candidate_name":"Other"},headers=headers).json()
    raw=client.post(f"/admin/sessions/{first['id']}/invite",headers=headers).json()["url"].rsplit("/",1)[-1]
    candidate_token=client.post("/invites/redeem",json={"token":raw}).json()["candidate_token"]
    candidate_headers={"Authorization":f"Bearer {candidate_token}"}
    assert client.get(f"/sessions/{first['id']}",headers=candidate_headers).status_code==200
    assert client.get(f"/sessions/{second['id']}",headers=candidate_headers).status_code==403
    assert client.get(f"/admin/sessions/{first['id']}/evaluation",headers=candidate_headers).status_code==401
    assert client.post(f"/admin/sessions/{first['id']}/evaluation",json={},headers=candidate_headers).status_code in {401,422}

def test_admin_canvas_credential_uses_admin_route(client):
    headers=auth(client); created=client.post("/admin/sessions",json=session_payload(),headers=headers).json()
    response=client.post(f"/admin/sessions/{created['id']}/canvas-token",headers=headers)
    assert response.status_code==200 and response.json()["room"]==created["id"]

def test_websocket_authorization_presence_and_candidate_control_denial(client):
    headers=auth(client); created=client.post("/admin/sessions",json=session_payload(),headers=headers).json(); admin_token=headers["Authorization"].split(" ",1)[1]
    with client.websocket_connect(f"/ws/sessions/{created['id']}?token={admin_token}",headers={"Origin":"http://localhost:5173"}) as socket:
        assert socket.receive_json()["type"]=="presence"
        assert socket.receive_json()["type"]=="session"
    raw=client.post(f"/admin/sessions/{created['id']}/invite",headers=headers).json()["url"].rsplit("/",1)[-1]; candidate_token=client.post("/invites/redeem",json={"token":raw}).json()["candidate_token"]
    with client.websocket_connect(f"/ws/sessions/{created['id']}?token={candidate_token}",headers={"Origin":"http://localhost:5173"}) as socket:
        socket.receive_json(); socket.receive_json(); socket.send_json({"type":"end"}); assert socket.receive_json()["type"]=="error"

def test_websocket_presence_is_broadcast_and_participants_are_persisted(client):
    headers=auth(client); created=client.post("/admin/sessions",json=session_payload(),headers=headers).json(); admin_token=headers["Authorization"].split(" ",1)[1]
    raw=client.post(f"/admin/sessions/{created['id']}/invite",headers=headers).json()["url"].rsplit("/",1)[-1]
    candidate_token=client.post("/invites/redeem",json={"token":raw}).json()["candidate_token"]
    with client.websocket_connect(f"/ws/sessions/{created['id']}?token={admin_token}",headers={"Origin":"http://localhost:5173"}) as admin_socket:
        assert admin_socket.receive_json()["status"]=="joined"
        assert admin_socket.receive_json()["type"]=="session"
        with client.websocket_connect(f"/ws/sessions/{created['id']}?token={candidate_token}",headers={"Origin":"http://localhost:5173"}) as candidate_socket:
            joined=candidate_socket.receive_json(); assert joined["display_name"]=="Candidate"
            assert candidate_socket.receive_json()["type"]=="session"
            observed=admin_socket.receive_json(); assert observed["status"]=="joined" and observed["role"]=="candidate"
        left=admin_socket.receive_json(); assert left["status"]=="left" and left["role"]=="candidate"
    with SessionLocal() as db:
        participants=db.query(SessionParticipant).filter_by(session_id=created["id"]).all()
        assert len(participants)==2 and all(row.left_at is not None for row in participants)

def test_websocket_facilitator_controls_broadcast_lifecycle(client):
    headers=auth(client); created=client.post("/admin/sessions",json={**session_payload(),"scheduled_at":(datetime.now(timezone.utc)-timedelta(minutes=2)).isoformat()},headers=headers).json(); admin_token=headers["Authorization"].split(" ",1)[1]
    with SessionLocal() as db:
        row=db.get(InterviewSession,created["id"]); row.end_at=datetime.now(timezone.utc)-timedelta(seconds=1); db.commit()
    with client.websocket_connect(f"/ws/sessions/{created['id']}?token={admin_token}",headers={"Origin":"http://localhost:5173"}) as socket:
        assert socket.receive_json()["status"]=="joined"; assert socket.receive_json()["state"]=="expired-pending-facilitator-action"
        socket.send_json({"type":"extend","minutes":10}); assert socket.receive_json()["state"]=="active"
        socket.send_json({"type":"end"}); assert socket.receive_json()["state"]=="completed"

def test_timer_expiry_and_extension_are_persisted(client):
    headers=auth(client); created=client.post("/admin/sessions",json={**session_payload(),"scheduled_at":(datetime.now(timezone.utc)-timedelta(minutes=2)).isoformat()},headers=headers).json()
    current=client.get(f"/admin/sessions/{created['id']}",headers=headers).json(); assert current["state"]=="active"
    with SessionLocal() as db:
        row=db.get(InterviewSession,created["id"]); row.end_at=datetime.now(timezone.utc)-timedelta(seconds=1); db.commit()
    assert client.get(f"/admin/sessions/{created['id']}",headers=headers).json()["state"]=="expired-pending-facilitator-action"
    assert client.post(f"/admin/sessions/{created['id']}/extend",json={"minutes":15},headers=headers).json()["state"]=="active"

def test_audit_events_are_non_sensitive_and_admin_only(client):
    headers=auth(client); created=client.post("/admin/sessions",json=session_payload(),headers=headers).json(); invite=client.post(f"/admin/sessions/{created['id']}/invite",headers=headers).json(); raw=invite["url"].rsplit("/",1)[-1]; client.post("/invites/redeem",json={"token":raw}); client.post(f"/admin/sessions/{created['id']}/end",headers=headers)
    events=client.get(f"/admin/sessions/{created['id']}/audit",headers=headers).json(); types={x["event_type"] for x in events}; assert {"invite.created","invite.redeemed","session.ended"}<=types
    assert all(raw not in str(x) for x in events)

def test_invalid_transition_does_not_change_session(client):
    headers=auth(client)
    created=client.post("/admin/sessions",json=session_payload(),headers=headers).json()
    assert client.post(f"/admin/sessions/{created['id']}/extend",json={"minutes":10},headers=headers).status_code==409
    assert client.post(f"/admin/sessions/{created['id']}/end",headers=headers).status_code==200
    assert client.post(f"/admin/sessions/{created['id']}/end",headers=headers).status_code==409

def test_private_evaluation_requires_completion_and_is_not_candidate_visible(client):
    headers=auth(client); created=client.post("/admin/sessions",json=session_payload(),headers=headers).json()
    scores=[{"category":x,"rating":4,"rationale":"Strong evidence."} for x in ["problem solving","technical fundamentals","communication","collaboration"]]
    assert client.post(f"/admin/sessions/{created['id']}/evaluation",json={"scores":scores,"recommendation":"hire"},headers=headers).status_code==409
    assert client.post(f"/admin/sessions/{created['id']}/end",headers=headers).status_code==200
    saved=client.post(f"/admin/sessions/{created['id']}/evaluation",json={"scores":scores,"recommendation":"hire","private_notes":"Private."},headers=headers)
    assert saved.status_code==200
    assert client.get(f"/admin/sessions/{created['id']}/evaluation",headers=headers).json()["private_notes"]==["Private."]
    assert client.get(f"/sessions/{created['id']}").status_code==401

def test_candidate_can_see_ended_session_but_cannot_get_canvas_access(client):
    headers=auth(client); created=client.post("/admin/sessions",json=session_payload(),headers=headers).json()
    raw=client.post(f"/admin/sessions/{created['id']}/invite",headers=headers).json()["url"].rsplit("/",1)[-1]
    candidate_token=client.post("/invites/redeem",json={"token":raw}).json()["candidate_token"]
    candidate_headers={"Authorization":f"Bearer {candidate_token}"}
    assert client.post(f"/admin/sessions/{created['id']}/end",headers=headers).status_code==200
    ended=client.get(f"/sessions/{created['id']}",headers=candidate_headers)
    assert ended.status_code==200 and ended.json()["state"]=="completed"
    assert client.post(f"/sessions/{created['id']}/canvas-token",headers=candidate_headers).status_code==403
