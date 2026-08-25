# Canvas connection lifecycle

The canvas-sync process authorizes every HTTP and WebSocket room request with a
short-lived backend-issued canvas token. A room is keyed by the opaque session
identifier, never by candidate data. Each WebSocket close/error disconnects its
client from the `DrawioRoom`; when its last active session is removed, the room
is closed and deleted from the process map. This bounds memory across repeated
local demos.

The frontend reports connecting, connected, and disconnected states. Backend and
canvas logs include the opaque session/room identifier and role or cleanup event,
but never access tokens.

## Draw.io document contract

The replacement path uses `/drawio/rooms/{opaqueSessionId}`. The sync service
keeps one XML snapshot and an integer revision per
room. A connection receives the current `{type: "document", revision, xml}`
message. Saves must include the client's base revision; stale saves receive a
`conflict` response and cannot overwrite the authoritative snapshot. Accepted
saves increment the revision, persist a bounded JSON snapshot under
`DRAWIO_STATE_DIR`, and broadcast the new document to both participants.

The backend-issued canvas token binds the opaque session identifier and role;
the service verifies that binding before opening the WebSocket. Room names are
validated identifiers, never candidate display data. Empty live rooms are
removed from the in-memory registry while their latest snapshot remains on
disk for refresh/restart recovery. XML is capped at 2 MB and logs never include
tokens or document contents.

## Convergence and reconnect policy

FastAPI owns session authorization and lifecycle; canvas-sync owns only the
latest accepted XML snapshot and its monotonically increasing room revision.
The first save received with the current base revision wins. A stale save is
rejected with the authoritative snapshot, so clients reload before retrying
and never silently overwrite a newer edit. Accepted snapshots are broadcast
to every authorized client, including the sender; clients replace their local
document with that canonical snapshot, which prevents duplicate echoed
objects. Selection and viewport state are local presentation state and may be
cleared when a remote snapshot is applied.

On refresh, WebSocket reconnect, or canvas-sync restart, the room reads its
durable snapshot from `DRAWIO_STATE_DIR` and sends it immediately after token
authorization. The host distinguishes connecting, saved, conflict/reloaded,
disconnected/retrying, invalid-document, and session-ended states. If the
service is unavailable, the live-session controls remain usable and no token,
raw XML, or stack trace is shown. This is an optimistic single-writer
revision policy; it does not merge concurrent edits at object level.
