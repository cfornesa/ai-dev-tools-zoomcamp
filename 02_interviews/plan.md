# Interview Canvas MVP — Product and Architecture Plan

## 1. Purpose

Build a local/demo-ready collaborative technical-interview application. Administrators create and manage interview sessions. Candidates join a single assigned session through a signed, expiring invite link. Interviewers and candidates collaborate live on a self-hosted XML canvas, while facilitators manage session timing and participants. After a session ends, evaluators submit structured scorecards and private freeform notes.

This document records the agreed MVP decisions and provides implementation boundaries for the repository.

## 2. MVP Decisions

| Area | Decision |
|---|---|
| Repository layout | Monorepo-style repository with `/frontend` and `/backend` |
| Frontend application | One React application containing both admin-dashboard and live-interview experiences |
| Frontend tooling | Vite, React, TypeScript, React Router |
| Canvas sync service | A separate TypeScript self-hosted XML canvas sync service at `/frontend/canvas-sync` |
| Backend | Python FastAPI application in `/backend` |
| Live session events | WebSockets for bidirectional application events such as presence, timer state, facilitator controls, and session state |
| Canvas collaboration | self-hosted XML canvas sync handles canvas document collaboration independently of application WebSockets |
| Admin access | Authenticated administrator accounts |
| Candidate access | Signed, expiring, invite-only URLs scoped to one interview session |
| Candidate invitation delivery | Admin manually copies a generated candidate URL from the dashboard |
| Database | PostgreSQL from the first iteration, run through Docker Compose |
| ORM and migrations | SQLAlchemy and Alembic |
| Workspace scope | Collaborative self-hosted XML canvas only for the MVP |
| Future workspace scope | Plan boundaries for shared code editing and isolated code execution, but do not ship either in v1 |
| Evaluation | Structured scorecard plus private freeform evaluator notes |
| Session completion | Facilitator may end a session manually; timer expiry prompts end or extend; ending opens evaluation |
| Deployment scope | Docker Compose only, intended for local development and demos |

## 3. Repository Structure

```text
.
├── backend/
│   ├── app/
│   │   ├── api/
│   │   ├── auth/
│   │   ├── db/
│   │   ├── models/
│   │   ├── schemas/
│   │   ├── services/
│   │   ├── websocket/
│   │   └── main.py
│   ├── alembic/
│   ├── tests/
│   ├── alembic.ini
│   ├── Dockerfile
│   └── requirements.txt
├── frontend/
│   ├── canvas-sync/
│   │   ├── src/
│   │   ├── Dockerfile
│   │   └── package.json
│   ├── src/
│   │   ├── app/
│   │   ├── components/
│   │   ├── features/
│   │   │   ├── admin/
│   │   │   ├── auth/
│   │   │   ├── evaluation/
│   │   │   └── interview/
│   │   ├── lib/
│   │   ├── routes/
│   │   └── main.tsx
│   ├── Dockerfile
│   ├── package.json
│   └── vite.config.ts
├── docs/
│   └── adr/
│       └── 0001-mvp-canvas-only.md
├── docker-compose.yml
├── .env.example
├── README.md
└── plan.md
```

The frontend remains one deployable React application. Role-aware React Router routes separate administrator workflows from candidate/interviewer session workflows. The self-hosted XML canvas sync service is deliberately colocated under `/frontend/canvas-sync` because it is a TypeScript service supporting the frontend canvas stack, although it runs as its own process/container.

## 4. Core Roles and Access

### Administrator

Administrators authenticate through the admin login flow. They can:

- Create, view, edit, and schedule interview sessions.
- Configure the session duration and facilitator/interviewer assignments.
- Generate a candidate-specific signed invite URL.
- Copy the generated URL for manual delivery outside the product.
- Observe active-session state and participant presence.
- End a session or extend it after the timer has expired.
- Submit evaluator scorecards and freeform notes after a session.

### Candidate

Candidates do not need an account for the MVP. A candidate joins through a signed, expiring link that is scoped to exactly one interview session. The link must not grant dashboard access, access to other sessions, or evaluator-feedback access.

### Interviewer/Facilitator

An administrator may act as the interviewer/facilitator in the MVP. The authorization model should nevertheless distinguish facilitator permissions from candidate permissions so that a dedicated interviewer role can be added later without redesigning session controls.

## 5. Main User Flows

### Admin creates and invites

1. An administrator signs in.
2. The administrator creates an interview session with candidate identity/display details, scheduled time, and duration.
3. The backend creates a candidate invite token with session scope and an expiration.
4. The dashboard displays the full candidate URL with a copy action.
5. The administrator shares the URL manually.

### Live interview

1. A candidate opens the signed invite URL.
2. The frontend validates the session invitation with the backend and establishes a scoped candidate session.
3. The candidate enters the live workspace.
4. The interviewer/facilitator joins through the authenticated application.
5. Both participants collaborate in the session-specific canvas room.
6. Application WebSockets synchronize participant presence, timer state, facilitator actions, and session status.
7. self-hosted XML canvas sync independently synchronizes canvas document changes.

### Timer and completion

1. The facilitator may end an interview at any time.
2. When the configured timer reaches zero, clients show the facilitator a prompt to end the session or extend it.
3. Extending records the new end time and continues the active session.
4. Ending marks the session complete and makes the evaluator-feedback workflow available to authorized evaluators.
5. Candidates no longer receive access to private evaluation data.

### Evaluation

1. An authorized evaluator opens the completed session.
2. The evaluator completes a structured scorecard.
3. The evaluator may add private freeform notes.
4. The evaluator chooses a recommendation, such as hire/no-hire.
5. Feedback is stored durably and remains inaccessible to candidates.

## 6. Backend Design

### API responsibilities

FastAPI is the source of truth for identities, authorization, sessions, invitations, timing, feedback, and audit-worthy state transitions. It exposes REST endpoints for durable CRUD actions and WebSocket endpoints for low-latency session events.

Suggested API groups:

- `/auth`: administrator login, refresh/logout behavior, and current-user lookup.
- `/admin/sessions`: session creation, listing, detail, updates, invite generation, and lifecycle actions.
- `/invites`: validation and redemption of candidate invite tokens.
- `/sessions/{session_id}`: authorized session metadata and timer data.
- `/sessions/{session_id}/evaluations`: structured scorecard and freeform-note submission/retrieval.
- `/ws/sessions/{session_id}`: application-level real-time session events.

### WebSocket event boundaries

Use application WebSockets for state that belongs to the interview product rather than the canvas document:

- Participant joined, left, and presence updates.
- Participant role and display-name announcements.
- Session status transitions: scheduled, active, expired-pending-facilitator-action, completed.
- Authoritative timer started, paused if later supported, extended, and ended events.
- Facilitator controls, including end and extend.
- Optional ephemeral signals, such as “facilitator is viewing” or lightweight notifications.

Do not duplicate canvas document synchronization in the FastAPI WebSocket channel. Canvas data should use the self-hosted XML canvas sync service and a deterministic room identifier derived from the authorized session.

### Authentication and invitation security

- Admin accounts use authenticated login and protected API/WebSocket access.
- Candidate invite URLs use signed, random, high-entropy tokens with explicit expiry and session scope.
- Store a token hash or token identifier rather than the raw token where feasible.
- Validate the invitation before granting candidate session access.
- Candidate credentials issued after redemption must remain scoped to the invited session and minimum required capabilities.
- Do not expose evaluator feedback, administrative records, or unrelated session information through candidate APIs or WebSockets.
- Validate every WebSocket handshake and apply authorization before allowing room/event subscription.
- Rate-limit login and invitation-redemption endpoints.

### Persistence entities

Initial PostgreSQL entities should include:

| Entity | Responsibilities |
|---|---|
| `admin_users` | Administrator identity, password credential representation, role, and account status |
| `interview_sessions` | Candidate display data, scheduling, duration, state, start/end timestamps, and facilitator assignment |
| `session_invites` | Session-scoped token metadata, token hash/identifier, expiration, redemption status, and revocation status |
| `session_participants` | Session membership, role, display name, join/leave timestamps, and optional presence history |
| `session_extensions` | Extension history, amount, initiating administrator, and timestamp |
| `scorecard_templates` | Configurable evaluation category definitions and rating scale metadata |
| `evaluations` | Evaluator, completed session, recommendation, overall notes, and submission metadata |
| `evaluation_scores` | Per-category numeric ratings and rationale for each evaluation |
| `evaluation_notes` | Private freeform evaluator notes, with author and timestamps |
| `audit_events` | Optional but recommended lifecycle/security event trail for invite creation, redemption, end, extension, and evaluation submission |

Use Alembic migrations for every schema change. Avoid relying on ORM auto-create behavior outside local experiments.

## 7. Frontend Design

### Routing

Use React Router with route-level authorization and clear feature boundaries.

Suggested routes:

| Route | Audience | Purpose |
|---|---|---|
| `/login` | Admin | Administrator authentication |
| `/admin` | Admin | Dashboard overview |
| `/admin/sessions` | Admin | Session list and creation |
| `/admin/sessions/:sessionId` | Admin | Session management, invite copying, and post-session review |
| `/invite/:token` | Candidate | Invite validation and candidate session entry |
| `/session/:sessionId` | Candidate and authorized facilitator | Live interview workspace |
| `/admin/sessions/:sessionId/evaluation` | Admin/evaluator | Private scorecard and freeform notes |

### Live workspace

The live workspace should compose the following independently testable areas:

- Canvas pane containing the canvas editor connected to a session-specific self-hosted XML canvas sync room.
- Session header with participant state, session state, and synchronized timer.
- Facilitator controls for ending and extending the session, visible only to users with facilitator authority.
- Status/notification layer for joining, waiting, expiration, extension, disconnection, and completion events.

The canvas is the only collaborative work surface in the MVP. Avoid placing code-editor assumptions into route structure or UI state; instead use an extensible workspace model described in the ADR.

### Admin dashboard

The dashboard should support the MVP workflow without requiring email delivery or external services:

- Create and edit interview-session details.
- Generate/revoke/regenerate candidate links as permitted by policy.
- Copy the candidate link to the clipboard.
- See session status, remaining/elapsed time during active sessions, and participant presence where available.
- Start the evaluation workflow once a session is completed.

## 8. Canvas Sync Boundary

The service at `/frontend/canvas-sync` is a separate TypeScript/self-hosted XML canvas sync process. It must:

- Create or authorize one room per interview session.
- Use a room name derived from an opaque session identifier rather than candidate personal data.
- Receive enough trusted authorization context to prevent arbitrary users from joining unrelated rooms.
- Avoid becoming the source of truth for interview lifecycle state, invitations, or evaluation data.
- Run as an independent Docker Compose service.

The FastAPI backend remains responsible for whether a user may access a session. The integration should define a trusted handoff, such as a short-lived canvas access token or backend-verified session credential, before granting canvas room access.

## 9. Evaluation Model

The MVP supports both structured and unstructured feedback.

### Structured scorecard

Support configurable categories, each with:

- Category name, such as problem solving, communication, technical fundamentals, or collaboration.
- Numeric rating on a documented scale.
- Written rationale.
- Optional category weighting if introduced later; do not require weighted scoring in the initial interface.

At the evaluation level, support:

- Overall recommendation, including hire/no-hire.
- Optional overall rating.
- Submission status and timestamps.

### Freeform notes

Freeform notes capture observations that do not fit a rubric. They must be private to authorized evaluators and administrators and never shown to candidates. Preserve author and timestamp metadata so teams can understand provenance.

## 10. Docker Compose Environment

The initial environment is Docker Compose only. The compose file should define at least:

| Service | Role |
|---|---|
| `postgres` | Persistent PostgreSQL database with a named volume |
| `backend` | FastAPI REST API and application WebSocket server |
| `frontend` | Vite React application for local development/demo use |
| `canvas-sync` | TypeScript self-hosted XML canvas sync service |

Configuration should be environment-driven. Provide `.env.example` with non-secret defaults and required variable names, including:

- `POSTGRES_DB`, `POSTGRES_USER`, `POSTGRES_PASSWORD`, `DATABASE_URL`.
- `ADMIN_JWT_SECRET` or equivalent secure admin-session secret.
- `INVITE_TOKEN_SECRET` or a key strategy for signed candidate links.
- `CANVAS_SYNC_URL` and canvas-access credential configuration.
- Frontend/backend origin configuration for CORS and WebSocket origin checks.

Use a named PostgreSQL volume so data survives container restarts. Include health checks and startup sequencing where useful, but make backend migrations an explicit, reliable development command or an intentional startup action.

## 11. Testing Plan

### Backend

- Unit tests for token signing, token expiration, authorization decisions, timer calculations, and session state transitions.
- API tests for administrator authentication, session creation, invite generation/redemption, invite expiration, and candidate scoping.
- WebSocket tests for authorized joins, unauthorized denial, presence events, end actions, timer expiry, and extensions.
- Database integration tests against PostgreSQL-compatible test configuration and Alembic migrations.
- Evaluation tests confirming candidates cannot access or submit evaluator feedback.

### Frontend

- Component tests for protected routes, invite entry states, timer display, facilitator-only controls, scorecard validation, and copy-link flow.
- Integration tests for live-session states, including active, expiry-prompt, extended, and completed.
- End-to-end smoke tests for administrator creates session → copies invite → candidate enters → facilitator ends → evaluator submits feedback.

### Canvas integration

- Verify the same authorized session participants enter the same canvas room.
- Verify a candidate cannot join a room for a different session.
- Verify canvas-sync unavailability produces a clear recoverable UI state without corrupting session lifecycle data.

## 12. Implementation Milestones

### Milestone 1: Foundation

- Create the repository directories and Docker Compose stack.
- Configure PostgreSQL, FastAPI, Vite/React, and canvas-sync services.
- Add environment configuration, linting/formatting, basic test runners, and README startup instructions.
- Configure SQLAlchemy, Alembic, and the initial migration.

### Milestone 2: Admin and sessions

- Implement admin authentication and protected routes.
- Build session CRUD and session lifecycle persistence.
- Implement dashboard session list/detail views.
- Implement candidate invite generation, display, copy action, expiration, and revocation rules.

### Milestone 3: Live session

- Implement invitation validation and scoped candidate access.
- Create the live session route and session metadata endpoint.
- Implement FastAPI application WebSockets for presence, timer, and facilitator actions.
- Integrate canvas with `/frontend/canvas-sync` using authorized, session-specific rooms.

### Milestone 4: Completion and evaluation

- Implement manual end, timer-expiry prompt, and extension flow.
- Enforce completed-session transition rules.
- Build structured scorecard and freeform-note interfaces.
- Implement private evaluation persistence and authorization.

### Milestone 5: Hardening and demo readiness

- Complete test coverage for key authorization and state-transition paths.
- Add UI states for invalid/expired invites, disconnections, and unavailable services.
- Review CORS, WebSocket origin validation, token handling, logs, and secrets.
- Document local/demo startup, test commands, and known non-goals.

## 13. Non-Goals for MVP

The following are explicitly out of scope for the first release:

- Automated email invitations or an email-service integration.
- Candidate accounts, candidate password login, and candidate dashboard/history.
- Shared source-code editing.
- Code execution, compilation, test runners, terminals, or sandboxing.
- Cloud deployment, managed databases, production hosting, autoscaling, or multi-region availability.
- Recording/replay, video conferencing, transcription, or AI evaluation.
- Complex multi-organization tenancy and enterprise identity-provider integration.

## 14. Architecture Decision Record

A formal ADR must be committed at `docs/adr/0001-mvp-canvas-only.md`.

### Title

MVP uses a collaborative canvas only; shared code editing and code execution are deferred.

### Status

Accepted.

### Context

The product is intended for technical interviews, which may eventually require a shared code editor and code execution. Adding these capabilities in the MVP would substantially increase synchronization, security, infrastructure, and operational complexity.

### Decision

Ship only the canvas collaborative canvas in the MVP. Design the domain and frontend boundaries so a future interview workspace can contain multiple artifact/surface types, including `canvas`, `code_editor`, and `execution`.

Do not add a shared editor or any code-execution feature in v1.

If code execution is added later, it must run in a separate, isolated runner service with strict resource limits, network isolation, timeouts, language/runtime allowlists, and auditability. It must never execute untrusted candidate code in the FastAPI API container, frontend container, canvas-sync container, or PostgreSQL container.

### Consequences

- The MVP can focus on reliable collaboration, invitations, real-time session control, and feedback.
- Future features can be introduced as additional workspace surfaces rather than by replacing the session model.
- A future code editor will require its own synchronization and persistence design.
- A future runner will require a security review and deployment architecture beyond the Docker Compose demo scope.

### Review Trigger

Revisit this decision when shared code editing becomes an approved product requirement, before committing to editor technology or any execution environment.

## 15. Open Implementation Choices

The following choices are intentionally deferred until implementation, while remaining consistent with the decisions above:

- Exact admin authentication implementation and password/session-token storage approach.
- Exact signed-token format and whether candidate link redemption creates a short-lived scoped cookie or bearer credential.
- Rating scale range and initial default scorecard categories.
- Whether a session supports one evaluator or multiple independent evaluator submissions in the first UI.
- Exact self-hosted XML canvas sync authorization adapter and room-access token mechanism.
- Whether the Vite frontend runs as a development server only or is served as a built static asset in a demo-oriented container configuration.

These choices must preserve the core constraints: administrators are authenticated, candidates are constrained to an expiring session invite, PostgreSQL is authoritative, FastAPI owns application state, and untrusted code execution remains out of scope and isolated if introduced later.
