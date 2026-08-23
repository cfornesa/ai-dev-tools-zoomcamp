from datetime import datetime, timedelta, timezone
from app.db import SessionLocal
from app.models import AuditEvent, InterviewSession, SessionInvite

def auth(client):
    response=client.post("/auth/login",json={"email":"admin@example.test","password":"correct-horse"})
    assert response.status_code==200
    return {"Authorization":f"Bearer {response.json()['access_token']}"}

def session_payload(): return {"candidate_name":"Candidate","candidate_email":"candidate@example.test","scheduled_at":(datetime.now(timezone.utc)+timedelta(hours=1)).isoformat(),"duration_minutes":45}

def test_health_and_protected_access(client):
    assert client.get("/health").json()=={"ok":True}
    assert client.get("/admin/sessions").status_code==401
    assert auth(client)

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
