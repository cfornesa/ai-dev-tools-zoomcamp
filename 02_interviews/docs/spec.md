# Interview Canvas MVP specification

## Roles and access

Administrators authenticate with the backend and manage sessions, invitations,
timing, participants, and private evaluations. Candidates have no account: a
signed, expiring invitation redeems into a credential scoped to exactly one
session. A candidate credential cannot access admin routes or evaluation data.
After completion it may retrieve the terminal session status needed to show an
ended page, but it cannot obtain a canvas credential or active controls.

## Session lifecycle

Sessions are created as `scheduled`, become `active` when their scheduled time
arrives, become `expired-pending-facilitator-action` when the timer ends, and
become `completed` when a facilitator finishes them. A facilitator may extend
an expired session or finish it. Completion opens evaluation and ends
candidate live/canvas access.

## Collaboration and authorization boundaries

The FastAPI REST API owns identities, invitations, session state, timer events,
and evaluations. The application WebSocket carries presence and lifecycle
events. The self-hosted canvas service carries XML document changes only. The
backend issues a short-lived canvas token; the canvas service verifies that
token and requires its session claim to match the opaque room identifier.

## Evaluation privacy

Authorized administrators submit structured category scores, recommendation,
and private notes after completion. Candidate APIs never return evaluations.

## MVP non-goals

The MVP does not include email delivery, production SSO, shared code editing,
code execution, load testing, or production deployment automation. If execution
is added later it must run in an isolated runner outside the API process.

## Authentication decision boundary

Public signup is disabled. Google Identity Services is a planned administrator
provider whose ID token is verified server-side by issuer, audience, signature,
expiry, and stable subject; email alone cannot link or authenticate an account.
Candidates remain invite-only and session-scoped. reCAPTCHA v3 is an optional,
action-specific abuse signal for signup, login, and invite redemption with
configured allow, step-up/rate-limit, and deny bands. Provider doubles are used
in local/CI; real provider availability is not a startup dependency. See
`docs/authentication.md` for the threat model, session/CSRF requirements, and
rollout gates.
