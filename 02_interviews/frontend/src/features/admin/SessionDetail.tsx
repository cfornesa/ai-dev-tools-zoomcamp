import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { service, Session, Invite } from "../../lib/service";

type InviteLoadState = "loading" | "ready" | "unavailable";

function sessionLabel(state: string) {
  return state === "expired" ? "Expired — facilitator action needed" : state;
}

function inviteDescription(invite: Invite | undefined, unavailable: boolean) {
  if (unavailable) return "Invitation status is temporarily unavailable";
  if (!invite) return "No invite has been generated.";
  if (invite.revoked) return "Invite revoked";
  if (invite.redeemed) return "Invite redeemed";
  if (invite.active === false) return "Invite expired";
  return "Active invite";
}

export function SessionDetail() {
  const { sessionId } = useParams();
  const [item, setItem] = useState<Session>();
  const [invite, setInvite] = useState("");
  const [inviteState, setInviteState] = useState<Invite>();
  const [inviteLoadState, setInviteLoadState] = useState<InviteLoadState>("loading");
  const [message, setMessage] = useState("");
  const [busy, setBusy] = useState("");
  const [candidateName, setCandidateName] = useState("");
  const [candidateEmail, setCandidateEmail] = useState("");
  const [facilitator, setFacilitator] = useState("");
  const [scheduledAt, setScheduledAt] = useState("");
  const [duration, setDuration] = useState("45");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  async function load() {
    setLoading(true); setError("");
    try {
      const next = await service.getSession(sessionId!, "admin");
      setItem(next); setCandidateName(next.candidate_name); setCandidateEmail(next.candidate_email || "");
      setFacilitator(next.facilitator_id || ""); setScheduledAt(new Date(next.scheduled_at).toISOString().slice(0, 16)); setDuration(String(next.duration_minutes));
      if (next.state === "completed") { setInviteState(undefined); setInviteLoadState("ready"); return; }
      setInviteLoadState("loading");
      try { setInviteState((await service.listInvites(sessionId!))[0]); setInviteLoadState("ready"); }
      catch (cause) { setInviteState(undefined); setInviteLoadState("unavailable"); setMessage(`Invitation status unavailable: ${String(cause)}`); }
    } catch (cause) { setError(String(cause)); }
    finally { setLoading(false); }
  }
  useEffect(() => { void load(); }, [sessionId]);
  if (loading) return <main className="card"><p className="status" role="status">Loading session details…</p></main>;
  if (error || !item) return <main className="card"><div role="alert" className="error"><p>{error || "Session details are unavailable."}</p><button type="button" onClick={() => void load()}>Retry</button></div></main>;

  async function run(action: string, callback: () => Promise<void>) {
    setBusy(action); try { await callback(); } catch (error) { setMessage(String(error)); } finally { setBusy(""); }
  }
  async function save() { await run("save", async () => { await service.updateSession(sessionId!, { candidate_name: candidateName, candidate_email: candidateEmail || undefined, facilitator_id: facilitator || undefined, scheduled_at: new Date(scheduledAt).toISOString(), duration_minutes: Number(duration) }); setMessage("Session details saved"); await load(); }); }
  async function generate() { await run("invite", async () => { const result = await service.createInvite(sessionId!); setInvite(result.url || ""); setMessage("Invite generated"); await load(); }); }
  async function regenerate() { await run("invite", async () => { const result = await service.regenerateInvite(sessionId!); setInvite(result.url || ""); setMessage("Invite regenerated"); await load(); }); }
  async function copy() { try { await navigator.clipboard.writeText(invite); setMessage("Invite copied"); } catch { setMessage("Clipboard unavailable; copy the URL manually"); } }
  async function revoke() { await run("revoke", async () => { await service.revokeInvite(sessionId!); setMessage("Invite revoked"); await load(); }); }
  async function finish() { await run("finish", async () => { await service.endSession(sessionId!); setMessage("Session finished"); await load(); }); }

  const completed = item.state === "completed";
  const unavailable = inviteLoadState === "unavailable";
  return <main className="card detail-card">
    <header className="detail-header"><div><p className="supporting">Interview session</p><h1>{item.candidate_name}</h1></div><p className="detail-meta" aria-label="Session summary"><strong>{sessionLabel(item.state)}</strong><span>{item.duration_minutes} minutes</span></p></header>
    {item.state === "scheduled" && <section className="detail-section" aria-labelledby="details-heading"><h2 id="details-heading">Session details</h2><div className="inline-form">
      <label>Candidate name<input aria-label="Candidate name" value={candidateName} onChange={event => setCandidateName(event.target.value)} /></label><label>Candidate email<input aria-label="Candidate email" type="email" value={candidateEmail} onChange={event => setCandidateEmail(event.target.value)} /></label><label>Facilitator ID<input aria-label="Facilitator ID" value={facilitator} onChange={event => setFacilitator(event.target.value)} /></label><label>Scheduled time<input aria-label="Scheduled time" type="datetime-local" value={scheduledAt} onChange={event => setScheduledAt(event.target.value)} /></label><label>Duration<input aria-label="Duration" type="number" min="1" value={duration} onChange={event => setDuration(event.target.value)} /></label>
    </div><div className="action-group"><button type="button" onClick={save} disabled={Boolean(busy)}>{busy === "save" ? "Saving…" : "Save details"}</button></div></section>}
    <section className="detail-section" aria-label="Session actions"><h2>Session actions</h2><div className="action-group">{!completed && <Link className="button" to={`/session/${sessionId}`}>Open live workspace</Link>}{completed && <Link className="button" to={`/admin/sessions/${sessionId}/evaluation`}>Open evaluation</Link>}{!completed && <button type="button" className="destructive" onClick={finish} disabled={Boolean(busy)}>{busy === "finish" ? "Finishing…" : "Finish session"}</button>}</div></section>
      <section className="invite detail-section" aria-labelledby="invite-heading"><h2 id="invite-heading">Candidate invitation</h2><p className={`invite-status ${unavailable ? "error" : inviteState?.active ? "status" : "supporting"}`}>{inviteLoadState === "loading" ? "Checking invitation status…" : completed ? <><span>No invite has been generated.</span> Invitation recovery is unavailable because this session is completed.</> : inviteDescription(inviteState, unavailable)}</p>
      {!completed && !unavailable && inviteLoadState === "ready" && <div className="action-group"><button type="button" onClick={inviteState ? regenerate : generate} disabled={Boolean(busy)}>{busy === "invite" ? "Working…" : inviteState ? "Regenerate invite" : "Generate invite"}</button>{inviteState?.active && <button type="button" className="destructive" onClick={revoke} disabled={Boolean(busy)}>{busy === "revoke" ? "Revoking…" : "Revoke invite"}</button>}</div>}
      {invite && <div className="action-group"><input aria-label="Invite URL" value={invite} readOnly /><button type="button" className="secondary" onClick={copy}>Copy</button></div>}{message && <p className={message.includes("unavailable") || message.startsWith("Error") ? "error" : "status"} role="status">{message}</p>}
    </section>
  </main>;
}
