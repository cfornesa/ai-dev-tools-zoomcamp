from datetime import datetime, timedelta, timezone

import pytest
from starlette.websockets import WebSocketDisconnect

from test_api import auth, session_payload


def test_supported_admin_candidate_evaluation_smoke(client):
    admin_headers = auth(client)
    created = client.post(
        "/admin/sessions",
        json={**session_payload(), "scheduled_at": (datetime.now(timezone.utc) - timedelta(minutes=1)).isoformat()},
        headers=admin_headers,
    ).json()
    session_id = created["id"]

    invite_url = client.post(f"/admin/sessions/{session_id}/invite", headers=admin_headers).json()["url"]
    raw_invite = invite_url.rsplit("/", 1)[-1]
    assert raw_invite and raw_invite not in invite_url[: -len(raw_invite)]
    redeemed = client.post("/invites/redeem", json={"token": raw_invite})
    assert redeemed.status_code == 200
    candidate_headers = {"Authorization": f"Bearer {redeemed.json()['candidate_token']}"}
    assert client.get(f"/sessions/{session_id}", headers=candidate_headers).json()["state"] == "active"

    admin_token = admin_headers["Authorization"].split(" ", 1)[1]
    with client.websocket_connect(f"/ws/sessions/{session_id}?token={admin_token}", headers={"Origin": "http://localhost:5173"}) as facilitator:
        assert facilitator.receive_json()["type"] == "presence"
        assert facilitator.receive_json()["type"] == "session"
    candidate_token = candidate_headers["Authorization"].split(" ", 1)[1]
    with client.websocket_connect(f"/ws/sessions/{session_id}?token={candidate_token}", headers={"Origin": "http://localhost:5173"}) as candidate_socket:
        assert candidate_socket.receive_json()["session_id"] == session_id
        assert candidate_socket.receive_json()["state"] == "active"

    assert client.post(f"/admin/sessions/{session_id}/end", headers=admin_headers).status_code == 200
    scores = [{"category": name, "rating": 4, "rationale": "Observed evidence."} for name in ["problem solving", "technical fundamentals", "communication", "collaboration"]]
    saved = client.post(f"/admin/sessions/{session_id}/evaluation", json={"scores": scores, "recommendation": "hire", "overall_rating": 4, "overall_notes": "Clear signal."}, headers=admin_headers)
    assert saved.status_code == 200
    assert client.get(f"/admin/sessions/{session_id}/evaluation", headers=admin_headers).json()["overall_rating"] == 4


def test_origin_and_cross_session_canvas_denials(client):
    admin_headers = auth(client)
    first = client.post("/admin/sessions", json=session_payload(), headers=admin_headers).json()
    second = client.post("/admin/sessions", json={**session_payload(), "candidate_name": "Other"}, headers=admin_headers).json()
    raw = client.post(f"/admin/sessions/{first['id']}/invite", headers=admin_headers).json()["url"].rsplit("/", 1)[-1]
    candidate_token = client.post("/invites/redeem", json={"token": raw}).json()["candidate_token"]
    candidate_headers = {"Authorization": f"Bearer {candidate_token}"}
    assert client.post(f"/sessions/{second['id']}/canvas-token", headers=candidate_headers).status_code == 403

    allowed = client.options("/health", headers={"Origin": "http://localhost:5173", "Access-Control-Request-Method": "GET"})
    assert allowed.headers.get("access-control-allow-origin") == "http://localhost:5173"
    denied = client.options("/health", headers={"Origin": "http://evil.example", "Access-Control-Request-Method": "GET"})
    assert "access-control-allow-origin" not in denied.headers
    with pytest.raises(WebSocketDisconnect):
        with client.websocket_connect(f"/ws/sessions/{first['id']}?token={candidate_token}", headers={"Origin": "http://evil.example"}):
            pass
