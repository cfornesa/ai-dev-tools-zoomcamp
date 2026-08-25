import { useEffect, useRef, useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import { canEndSession, expiryMessage, remainingMinutes, shouldApplySessionEvent } from "./presentation";
import { service, ServiceError, Session, sessionWebSocketUrl } from "../../lib/service";
import { DrawioCanvas } from "./DrawioCanvas";

type Presence = { key: string; role: string; display_name: string };

export function LiveWorkspace() {
  const { sessionId } = useParams();
  const navigate = useNavigate();
  const [item, setItem] = useState<Session>();
  const [canvasToken, setCanvasToken] = useState("");
  const canvasTokenRef = useRef("");
  const [presence, setPresence] = useState<Presence[]>([]);
  const [realtime, setRealtime] = useState("Connecting to session events…");
  const [error, setError] = useState<ServiceError>();
  const [message, setMessage] = useState("");
  const [canvasError, setCanvasError] = useState("");
  const [extension, setExtension] = useState("15");
  const [now, setNow] = useState(Date.now());
  const [retry, setRetry] = useState(0);
  const [loading, setLoading] = useState(true);
  const canvasUrl = import.meta.env.VITE_CANVAS_SYNC_URL || "http://localhost:8787";
  const facilitator = Boolean(localStorage.getItem("admin_token"));
  const role = facilitator ? "admin" : "candidate";
  const terminal = Boolean(error && [401, 403, 404].includes(error.status)) || item?.state === "completed";

  useEffect(() => {
    let cancelled = false;
    let inFlight = false;
    const refresh = async () => {
      if (cancelled || inFlight || terminal) return;
      inFlight = true;
      setNow(Date.now());
      try {
        const next = await service.getSession(sessionId!, facilitator ? "admin" : "candidate");
        if (cancelled) return;
        setItem(next);
        setError(undefined);
        if (next.state !== "completed" && !canvasTokenRef.current) {
          try {
            const canvas = await service.canvasToken(sessionId!, facilitator ? "admin" : "candidate");
            if (!cancelled) { canvasTokenRef.current = canvas.token; setCanvasToken(canvas.token); setCanvasError(""); }
          } catch (cause) {
            if (!cancelled) setCanvasError((cause as Error).message || "Canvas authorization unavailable");
          }
        }
      } catch (cause) { if (!cancelled) setError(cause as ServiceError); }
      finally { inFlight = false; setLoading(false); }
    };
    void refresh();
    const timer = window.setInterval(refresh, 2000);
    return () => { cancelled = true; window.clearInterval(timer); };
  }, [sessionId, facilitator, retry, terminal]);

  useEffect(() => {
    if (!sessionId || terminal || typeof WebSocket === "undefined") return;
    const token = facilitator ? localStorage.getItem("admin_token") || undefined : localStorage.getItem("candidate_token") || undefined;
    const socket = new WebSocket(sessionWebSocketUrl(sessionId, token));
    const participants = new Map<string, Presence>();
    socket.onopen = () => setRealtime("Connected to session events");
    socket.onmessage = event => {
      try {
        const data = JSON.parse(event.data) as { type?: string; status?: string; role?: string; display_name?: string; state?: string; end_at?: string | null };
        if (data.type === "presence" && data.role && data.display_name) {
          const key = `${data.role}:${data.display_name}`;
          if (data.status === "left") participants.delete(key);
          else participants.set(key, { key, role: data.role, display_name: data.display_name });
          setPresence([...participants.values()]);
        }
        if (data.type === "session" && data.state) {
          setItem(previous => previous && shouldApplySessionEvent(previous, data.state!, data.end_at) ? { ...previous, state: data.state!, end_at: data.end_at } : previous);
          setNow(Date.now());
        }
      } catch { setRealtime("Session sent an invalid event"); }
    };
    socket.onerror = () => setRealtime("Session events unavailable; using recovery polling");
    socket.onclose = () => setRealtime("Session events disconnected; retrying through polling");
    return () => socket.close();
  }, [sessionId, facilitator, retry, terminal]);

  async function end() {
    try { await service.endSession(sessionId!); setMessage("Session ended"); setRetry(value => value + 1); }
    catch (cause) { setMessage((cause as Error).message); }
  }
  async function extend() {
    const minutes = Number(extension);
    if (!Number.isInteger(minutes) || minutes < 1) { setMessage("Enter a positive whole number of minutes"); return; }
      try { const next = await service.extendSession(sessionId!, minutes); setItem(next); setNow(Date.now()); setMessage(`Session extended by ${minutes} minutes`); setRetry(value => value + 1); }
    catch (cause) { setMessage((cause as Error).message); }
  }

  const leave = () => navigate(facilitator ? "/admin/sessions" : "/login");
  if (error) return <main className="card"><h1>{terminal ? "Session unavailable" : "Session temporarily unavailable"}</h1><p className="error">{error.message}</p>{!terminal && <button onClick={() => { setError(undefined); setRetry(value => value + 1); }}>Retry</button>}<button className="secondary" onClick={leave}>Leave</button></main>;
  if (loading || !item) return <main className="card"><p>Joining session…</p></main>;
  const remaining = remainingMinutes(item.end_at, now);
  return <main className="card live">
    <div className="live-heading"><div><h1>Live interview</h1><p>{item.candidate_name} · <strong>{item.state}</strong>{remaining !== null && item.state !== "completed" && <span> · {remaining} min remaining</span>}</p><p className="status" role="status">{realtime}</p>{presence.length > 0 && <p className="status">Participants: {presence.map(participant => participant.display_name).join(", ")}</p>}</div><div className="inline-form"><button className="secondary" onClick={leave}>Leave</button>{canEndSession(role, item.state) && <button onClick={end}>Finish session</button>}</div></div>
    {item.state === "expired-pending-facilitator-action" || item.state === "expired" ? <div className="controls"><strong>{expiryMessage(role)}</strong>{facilitator && <><input aria-label="Extension minutes" type="number" min="1" value={extension} onChange={event => setExtension(event.target.value)} /><button onClick={extend}>Extend session</button></>}</div> : null}
    {item.state === "completed" && facilitator && <Link className="button" to={`/admin/sessions/${sessionId}/evaluation`}>Open evaluation</Link>}
    {item.state === "completed" && !facilitator && <p className="status">This session has ended. You may leave this page.</p>}
    {message && <p className="status">{message}</p>}
    {canvasError && <p className="error" role="alert">Canvas unavailable: {canvasError}</p>}
    {!canvasError && canvasToken && item.state !== "completed" && <DrawioCanvas sessionId={sessionId!} token={canvasToken} canvasUrl={canvasUrl} editorUrl={import.meta.env.VITE_DRAWIO_EDITOR_URL || "http://localhost:8090/editor.html"} />}
  </main>;
}
