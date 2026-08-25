import { FormEvent, useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";
import { service, Session } from "../../lib/service";

type Sort = "scheduled-asc" | "scheduled-desc" | "candidate-asc";
const statuses = ["scheduled", "active", "expired", "completed"] as const;

function matches(session: Session, query: string) {
  const needle = query.trim().toLocaleLowerCase();
  if (!needle) return true;
  return [session.candidate_name, session.candidate_email, session.id]
    .filter(Boolean)
    .some(value => value!.toLocaleLowerCase().includes(needle));
}

function statusLabel(state: string) {
  return state === "expired" ? "expired-pending-facilitator-action" : state;
}

export function SessionDashboard() {
  const [items, setItems] = useState<Session[]>([]);
  const [error, setError] = useState("");
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [facilitator, setFacilitator] = useState("");
  const [when, setWhen] = useState("");
  const [duration, setDuration] = useState("45");
  const [query, setQuery] = useState("");
  const [status, setStatus] = useState("all");
  const [sort, setSort] = useState<Sort>("scheduled-asc");

  async function load() {
    try { setItems(await service.listSessions()); }
    catch (cause) { setError(String(cause)); }
  }
  useEffect(() => { void load(); }, []);

  async function create(event: FormEvent) {
    event.preventDefault();
    try {
      await service.createSession({ candidate_name: name, candidate_email: email || undefined, facilitator_id: facilitator || undefined, scheduled_at: new Date(when).toISOString(), duration_minutes: Number(duration) });
      setName(""); setEmail(""); setFacilitator(""); setWhen(""); setError(""); await load();
    } catch (cause) { setError(String(cause)); }
  }

  const visible = useMemo(() => items
    .filter(session => matches(session, query))
    .filter(session => status === "all" || session.state === status)
    .sort((left, right) => {
      if (sort === "candidate-asc") return left.candidate_name.localeCompare(right.candidate_name) || left.id.localeCompare(right.id);
      const direction = sort === "scheduled-desc" ? -1 : 1;
      return (Date.parse(left.scheduled_at) - Date.parse(right.scheduled_at)) * direction || left.id.localeCompare(right.id);
    }), [items, query, sort, status]);

  const hasCriteria = Boolean(query.trim()) || status !== "all" || sort !== "scheduled-asc";
  function clearCriteria() { setQuery(""); setStatus("all"); setSort("scheduled-asc"); }

  return <main className="card">
    <h1>Sessions</h1>
    <form className="inline-form" onSubmit={create}>
      <input aria-label="Candidate name" placeholder="Candidate name" value={name} onChange={event => setName(event.target.value)} required />
      <input aria-label="Candidate email" type="email" placeholder="Candidate email (optional)" value={email} onChange={event => setEmail(event.target.value)} />
      <input aria-label="Facilitator ID" placeholder="Facilitator ID (optional)" value={facilitator} onChange={event => setFacilitator(event.target.value)} />
      <input aria-label="Scheduled time" type="datetime-local" value={when} onChange={event => setWhen(event.target.value)} required />
      <input aria-label="Duration" type="number" min="1" value={duration} onChange={event => setDuration(event.target.value)} required />
      <button>Create</button>
    </form>
    <section aria-label="Session list controls" className="inline-form">
      <label>Search sessions<input aria-label="Search sessions" type="search" value={query} onChange={event => setQuery(event.target.value)} placeholder="Name, email, or session ID" /></label>
      <label>Status<select aria-label="Status filter" value={status} onChange={event => setStatus(event.target.value)}><option value="all">All</option>{statuses.map(value => <option key={value} value={value}>{statusLabel(value)}</option>)}</select></label>
      <label>Sort<select aria-label="Sort sessions" value={sort} onChange={event => setSort(event.target.value as Sort)}><option value="scheduled-asc">Scheduled date ascending</option><option value="scheduled-desc">Scheduled date descending</option><option value="candidate-asc">Candidate name A–Z</option></select></label>
    </section>
    {error && <p className="error">{error}</p>}
    {items.length === 0 ? <p className="status">No sessions yet.</p> : visible.length === 0 ? <p className="status">No sessions match the current criteria. <button type="button" className="secondary" onClick={clearCriteria}>Clear criteria</button></p> : <ul className="sessions">{visible.map(session => <li key={session.id}><Link to={`/admin/sessions/${session.id}`}>{session.candidate_name}</Link><span>{new Date(session.scheduled_at).toLocaleString()} · {statusLabel(session.state)} · {session.duration_minutes} min · {session.id}</span></li>)}</ul>}
    {items.length > 0 && hasCriteria && visible.length > 0 && <button type="button" className="secondary" onClick={clearCriteria}>Clear criteria</button>}
  </main>;
}
