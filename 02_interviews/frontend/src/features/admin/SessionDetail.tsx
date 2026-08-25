import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { service, Session, Invite } from "../../lib/service";

export function SessionDetail() {
  const { sessionId } = useParams();
  const [item, setItem] = useState<Session>();
  const [invite, setInvite] = useState("");
  const [inviteState, setInviteState] = useState<Invite>();
  const [message, setMessage] = useState("");
  const [candidateName, setCandidateName] = useState("");
  const [candidateEmail, setCandidateEmail] = useState("");
  const [facilitator, setFacilitator] = useState("");
  const [scheduledAt, setScheduledAt] = useState("");
  const [duration, setDuration] = useState("45");

  async function load() {
    const next = await service.getSession(sessionId!, "admin");
    setItem(next); setCandidateName(next.candidate_name); setCandidateEmail(next.candidate_email || "");
    setFacilitator(next.facilitator_id || ""); setScheduledAt(new Date(next.scheduled_at).toISOString().slice(0, 16));
    setDuration(String(next.duration_minutes)); setInviteState((await service.listInvites(sessionId!))[0]);
  }
  useEffect(() => { load().catch(error => setMessage(String(error))); }, [sessionId]);
  if (!item) return <main className="card"><p>{message || "Loading session…"}</p></main>;

  async function save() {
    try {
      await service.updateSession(sessionId!, { candidate_name: candidateName, candidate_email: candidateEmail || undefined, facilitator_id: facilitator || undefined, scheduled_at: new Date(scheduledAt).toISOString(), duration_minutes: Number(duration) });
      setMessage("Session details saved"); await load();
    } catch (error) { setMessage(String(error)); }
  }
  async function generate() { try { const result = await service.createInvite(sessionId!); setInvite(result.url || ""); setMessage("Invite generated"); await load(); } catch (error) { setMessage(String(error)); } }
  async function copy() { try { await navigator.clipboard.writeText(invite); setMessage("Invite copied"); } catch { setMessage("Clipboard unavailable; copy the URL manually"); } }
  async function revoke() { try { await service.revokeInvite(sessionId!); setMessage("Invite revoked"); await load(); } catch (error) { setMessage(String(error)); } }
  async function regenerate() { try { const result = await service.regenerateInvite(sessionId!); setInvite(result.url || ""); setMessage("Invite regenerated"); await load(); } catch (error) { setMessage(String(error)); } }
  function inviteDescription() {
    if (!inviteState) return "No invite has been generated";
    if (inviteState.revoked) return "Invite revoked";
    if (inviteState.redeemed) return "Invite redeemed";
    if (inviteState.active === false) return "Invite expired";
    return "Active invite";
  }

  return <main className="card">
    <h1>{item.candidate_name}</h1>
    <p>Status: <strong>{item.state}</strong> · {item.duration_minutes} minutes</p>
    {item.state === "scheduled" && <section><h2>Session details</h2><div className="inline-form">
      <label>Candidate name<input aria-label="Candidate name" value={candidateName} onChange={event => setCandidateName(event.target.value)} /></label>
      <label>Candidate email<input aria-label="Candidate email" type="email" value={candidateEmail} onChange={event => setCandidateEmail(event.target.value)} /></label>
      <label>Facilitator ID<input aria-label="Facilitator ID" value={facilitator} onChange={event => setFacilitator(event.target.value)} /></label>
      <label>Scheduled time<input aria-label="Scheduled time" type="datetime-local" value={scheduledAt} onChange={event => setScheduledAt(event.target.value)} /></label>
      <label>Duration<input aria-label="Duration" type="number" min="1" value={duration} onChange={event => setDuration(event.target.value)} /></label>
      <button type="button" onClick={save}>Save details</button>
    </div></section>}
    {item.state !== "completed" && <><Link className="button" to={`/session/${sessionId}`}>Open live workspace</Link><button type="button" onClick={() => service.endSession(sessionId!).then(load).catch(error => setMessage(String(error)))}>Finish session</button></>}
    {item.state === "completed" && <Link className="button" to={`/admin/sessions/${sessionId}/evaluation`}>Evaluation</Link>}
    <section className="invite"><h2>Candidate invitation</h2>
      <p className={inviteState?.active ? "status" : inviteState ? "error" : "status"}>{inviteDescription()}</p>
      {item.state !== "completed" && <><button type="button" onClick={inviteState ? regenerate : generate}>{inviteState ? "Regenerate invite" : "Generate invite"}</button>{inviteState?.active && <button type="button" className="destructive" onClick={revoke}>Revoke</button>}</>}
      {invite && <><input aria-label="Invite URL" value={invite} readOnly /><button type="button" onClick={copy}>Copy</button></>}
      {message && <p className="status">{message}</p>}
    </section>
  </main>;
}
