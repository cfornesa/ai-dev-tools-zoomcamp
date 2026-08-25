<!--
These are issue-ready task definitions. File and complete them in numerical order
unless a task's dependencies have already been met. Issue numbers below refer to
the task numbers in this document until the tasks are created as GitHub issues.
-->

# Interview Canvas MVP task backlog

## 1. Establish the local development stack
GitHub issue: https://github.com/cfornesa/ai-dev-tools-zoomcamp/issues/22

### Goal

Provide a repeatable local/demo environment for the Interview Canvas MVP, with isolated services for PostgreSQL, the FastAPI backend, the React frontend, and canvas sync.

### Acceptance criteria

- [ ] `docker compose up --build` starts `postgres`, `backend`, `frontend`, and `canvas-sync` as separately named services.
- [ ] PostgreSQL uses a named volume, and data created in the database remains after the stack is stopped and started again.
- [ ] Each service has a health check or documented readiness command; dependent services do not claim readiness before their required dependency is reachable.
- [ ] A root `.env.example` documents every required environment variable with non-secret development defaults, including database, admin-session, invite-token, canvas-sync, CORS, and WebSocket-origin settings.
- [ ] The project README gives a new contributor the exact commands to configure environment variables, start the stack, stop it, and run backend and frontend tests from their respective directories.

### Out of scope

- Production hosting, managed services, autoscaling, and cloud deployment are deferred to a future project issue.
- Application schema design and migrations are handled in task 2.

### Constraints

- Keep all implementation inside `02_interviews/`.
- Use Docker Compose and PostgreSQL; do not add external hosting or email services.
- Do not add dependencies without user approval.

## 2. Create the backend persistence foundation and initial migration
GitHub issue: https://github.com/cfornesa/ai-dev-tools-zoomcamp/issues/23

### Goal

Create a FastAPI backend with SQLAlchemy and Alembic, and make PostgreSQL the authoritative store for the MVP domain.

### Acceptance criteria

- [ ] The backend starts through the Compose service and exposes a documented health endpoint that reports success only when its database connection is usable.
- [ ] Alembic can upgrade an empty PostgreSQL database to the latest revision using a documented command.
- [ ] The initial migration creates `admin_users`, `interview_sessions`, `session_invites`, `session_participants`, `session_extensions`, `scorecard_templates`, `evaluations`, `evaluation_scores`, and `evaluation_notes` with primary keys and required foreign-key relationships.
- [ ] Session records store candidate display data, scheduled time, duration, lifecycle state, start/end timestamps, and facilitator assignment.
- [ ] Invite, participant, extension, and evaluation records store the metadata required by the plan without storing a raw candidate invite token.
- [ ] Automated tests exercise a migration against a PostgreSQL-compatible test configuration and demonstrate that the expected tables are available afterward.

### Out of scope

- Authentication endpoints and password/session credential design are handled in task 5.
- Audit-event persistence is deferred to task 18.
- UI routes and forms are handled in tasks 3, 6, and 8.

### Constraints

- Depend on task 1.
- Use SQLAlchemy and Alembic; do not use ORM auto-create as a replacement for migrations.
- Keep migrations and database access inside `02_interviews/backend/`.

## 3. Scaffold the React application and authorized route boundaries
GitHub issue: https://github.com/cfornesa/ai-dev-tools-zoomcamp/issues/24

### Goal

Create the Vite React TypeScript application and its route structure so admin, candidate, live-session, and evaluation experiences have clear, testable boundaries.

### Acceptance criteria

- [ ] The frontend service starts through Docker Compose and renders a reachable application page.
- [ ] React Router defines routes for `/login`, `/admin`, `/admin/sessions`, `/admin/sessions/:sessionId`, `/invite/:token`, `/session/:sessionId`, and `/admin/sessions/:sessionId/evaluation`.
- [ ] Admin routes render an unauthenticated state that redirects users to `/login` instead of showing protected content.
- [ ] Candidate and facilitator session routes expose a distinct loading, authorized, and access-denied state without revealing data from another session.
- [ ] The source tree separates `admin`, `auth`, `evaluation`, and `interview` features, with shared components and API utilities outside those feature folders.
- [ ] Component tests verify the admin redirect and the visible states for a pending and denied route authorization decision.

### Out of scope

- Real administrator authentication is handled in task 5.
- Session dashboards, invite entry, and live workspace content are handled in tasks 8, 9, and 12.

### Constraints

- Depend on task 1.
- Use Vite, React, TypeScript, and React Router.
- Keep all frontend work in `02_interviews/frontend/`.

## 4. Define the canvas-only architecture boundary and run canvas sync
GitHub issue: https://github.com/cfornesa/ai-dev-tools-zoomcamp/issues/25

### Goal

Commit the MVP architecture decision and run a separate TypeScript canvas-sync service without prematurely adding shared code editing or code execution.

### Acceptance criteria

- [ ] `docs/adr/0001-mvp-canvas-only.md` records the accepted decision to ship a collaborative canvas only, defer shared code editing and execution, and require an isolated runner if execution is added later.
- [ ] The `canvas-sync` Compose service builds and starts independently of the React frontend process.
- [ ] The service exposes a documented local endpoint and configuration variable consumed by the frontend integration.
- [ ] The service contract documents that room identifiers are derived from opaque session identifiers and that lifecycle, invitations, and evaluations remain backend-owned.
- [ ] The service does not accept an unauthenticated arbitrary room name as sufficient authority to join a room.

### Out of scope

- Backend-issued canvas credentials and end-to-end room authorization are handled in task 11.
- Rendering and interacting with the collaborative canvas are handled in task 12.
- Shared code editing and code execution are explicitly deferred beyond this MVP.

### Constraints

- Depend on task 1.
- Place the service under `02_interviews/frontend/canvas-sync/`.
- Use the tldraw Sync stack; do not duplicate canvas synchronization over the FastAPI WebSocket channel.

## 5. Implement administrator authentication and protected backend access
GitHub issue: https://github.com/cfornesa/ai-dev-tools-zoomcamp/issues/26

### Goal

Allow an administrator to sign in and use protected admin APIs and routes, while rejecting unauthenticated requests.

### Acceptance criteria

- [ ] A seeded or documented development administrator can sign in through `/login` with credentials that are not committed as plaintext application data.
- [ ] Successful login establishes an administrator session/credential accepted by protected API requests and WebSocket handshakes.
- [ ] Unauthenticated requests to admin session-management endpoints receive an authorization failure and no session data.
- [ ] The frontend shows a successful post-login transition to `/admin` and provides a logout action that removes access to protected routes.
- [ ] Login attempts are rate-limited, with a visible API response when the configured limit is exceeded.
- [ ] Tests cover valid login, invalid login, logout, protected API denial, and protected-route redirect.

### Out of scope

- Dedicated interviewer accounts and enterprise identity-provider integration are deferred beyond the MVP.
- Candidate invitation access is handled in task 9.

### Constraints

- Depend on tasks 2 and 3.
- Store password credentials using an appropriate password-hashing mechanism; never return them from API responses.
- Keep the chosen admin session secret configurable through the environment.

## 6. Implement administrator session CRUD and lifecycle persistence
GitHub issue: https://github.com/cfornesa/ai-dev-tools-zoomcamp/issues/27

### Goal

Give authenticated administrators durable APIs to create, list, view, and edit scheduled interview sessions.

### Acceptance criteria

- [ ] An authenticated administrator can create a session with candidate display details, scheduled time, duration, and facilitator assignment.
- [ ] A created session is listed in the administrator's session collection and can be retrieved by its opaque session identifier.
- [ ] An administrator can update the candidate display details, scheduled time, duration, and facilitator assignment while the session is scheduled.
- [ ] Invalid or missing required fields produce field-specific validation errors and no partial session record.
- [ ] A session begins in the documented `scheduled` state and API responses expose its state, scheduled time, and duration.
- [ ] API tests cover create, list, detail, valid update, invalid input, and unauthenticated denial.

### Out of scope

- Dashboard forms and list/detail presentation are handled in task 8.
- Starting, expiring, extending, and completing sessions are handled in task 13.
- Candidate invite creation is handled in task 7.

### Constraints

- Depend on tasks 2 and 5.
- Scope every endpoint to authenticated administrators.
- Do not add candidate accounts or email delivery.

## 7. Implement secure candidate invite lifecycle APIs
GitHub issue: https://github.com/cfornesa/ai-dev-tools-zoomcamp/issues/28

### Goal

Allow administrators to generate, inspect, revoke, and regenerate a signed, expiring URL for exactly one interview session.

### Acceptance criteria

- [ ] An authenticated administrator can generate an invite for a scheduled session and receives one full candidate URL containing a high-entropy signed token.
- [ ] Invite persistence contains a token hash or identifier, session scope, expiration, creation metadata, redemption state, and revocation state; it never persists the raw token.
- [ ] A generated token validates only for its associated session and before its expiration time.
- [ ] Revoking an invite prevents future validation or redemption, and regenerating creates a new usable token without reactivating the revoked one.
- [ ] Invite generation and lifecycle endpoints reject unauthenticated administrators and unknown sessions.
- [ ] Unit and API tests cover token signing, expiration, session scoping, revocation, regeneration, and raw-token non-persistence.

### Out of scope

- Candidate redemption and scoped candidate credentials are handled in task 9.
- Copying and displaying the invite in the dashboard are handled in task 8.
- Automated invitation email delivery is outside the MVP.

### Constraints

- Depend on tasks 2, 5, and 6.
- Configure signing secrets and default expiration through environment variables.
- Use a URL path compatible with `/invite/:token`.

## 8. Build the administrator session dashboard and invite-copy workflow
GitHub issue: https://github.com/cfornesa/ai-dev-tools-zoomcamp/issues/29

### Goal

Provide administrators with a usable dashboard to manage sessions and manually copy candidate invite URLs.

### Acceptance criteria

- [ ] `/admin/sessions` shows the authenticated administrator a list of sessions with candidate display data, scheduled time, duration, and current lifecycle state.
- [ ] The dashboard provides a create-session flow that visibly reports validation failures and displays the new session after successful submission.
- [ ] `/admin/sessions/:sessionId` shows editable scheduled-session details and saves allowed changes through the backend API.
- [ ] The session detail view can generate an invite, displays the resulting full candidate URL, and provides a copy action with clear success and failure feedback.
- [ ] The detail view visibly distinguishes an active invite from expired or revoked status and provides allowed revoke/regenerate actions.
- [ ] Component or integration tests cover the create form's invalid state, successful session rendering, copy-link success/failure, and revoked-invite state.

### Out of scope

- Active-session presence, timer observation, and facilitator controls are handled in tasks 12 and 14.
- Post-session evaluation entry is handled in task 16.
- Email delivery is outside the MVP.

### Constraints

- Depend on tasks 3, 6, and 7.
- Follow `_docs/design-system.md` before implementing UI.
- Use the browser clipboard API with a visible fallback/error state; do not send invitations externally.

## 9. Validate and redeem candidate invitations into scoped access
GitHub issue: https://github.com/cfornesa/ai-dev-tools-zoomcamp/issues/30

### Goal

Let a candidate enter the single session named by a valid invite while preventing that invite from granting any broader access.

### Acceptance criteria

- [ ] Opening `/invite/:token` visibly shows loading, valid-invite, invalid-invite, expired-invite, and revoked-invite states.
- [ ] Redeeming a valid invite creates or establishes a candidate credential limited to the invited session and the candidate role.
- [ ] A candidate credential can retrieve only the minimum session metadata required to enter its own live workspace.
- [ ] A candidate credential cannot access admin APIs, another session's metadata, or evaluation endpoints.
- [ ] Invite-redemption requests are rate-limited and invalid tokens do not disclose whether an unrelated session exists.
- [ ] API and component tests cover valid redemption, expiration, revocation, cross-session denial, and candidate denial from evaluator/admin resources.

### Out of scope

- The live workspace is handled in task 12.
- Application WebSocket authorization is handled in task 10.
- Candidate account creation, password login, and history are outside the MVP.

### Constraints

- Depend on tasks 3 and 7.
- Validate the invitation server-side before issuing candidate access.
- Do not expose the candidate token or private administrator data in page logs or API responses.

## 10. Implement authorized application WebSockets for session events
GitHub issue: https://github.com/cfornesa/ai-dev-tools-zoomcamp/issues/31

### Goal

Synchronize interview-product events—presence, roles, session state, timer state, and facilitator commands—without carrying canvas document data.

### Acceptance criteria

- [ ] `/ws/sessions/{sessionId}` accepts only an authenticated administrator/facilitator or a candidate credential scoped to that exact session.
- [ ] An authorized client receives participant join, leave, role, and display-name presence events for its session.
- [ ] The channel delivers authoritative session-status and timer-state events, including active, expired-pending-facilitator-action, extended, and completed.
- [ ] Candidate attempts to send facilitator-only controls are rejected and do not change persistent session state.
- [ ] A client attempting to connect to a different session, with missing credentials, or with an unapproved origin is refused before subscription.
- [ ] WebSocket tests cover authorized joins, unauthorized denial, presence delivery, cross-session isolation, and rejected candidate controls.

### Out of scope

- Persistent timer/lifecycle transition rules are handled in task 13.
- Facilitator control UI is handled in task 14.
- tldraw document synchronization is handled by canvas sync in tasks 11 and 12.

### Constraints

- Depend on tasks 5 and 9.
- Apply origin validation and authorization at the handshake.
- Do not serialize or relay tldraw canvas document changes through this endpoint.

## 11. Authorize session-specific canvas rooms
GitHub issue: https://github.com/cfornesa/ai-dev-tools-zoomcamp/issues/32

### Goal

Create the trusted handoff from FastAPI authorization to canvas sync so only participants authorized for a session can join its opaque tldraw room.

### Acceptance criteria

- [ ] The backend issues a short-lived canvas-access credential only after verifying the requester has access to the requested session.
- [ ] The credential binds the participant role and opaque session identifier and is rejected for a different session or after expiration.
- [ ] Canvas sync verifies the credential before granting room access and derives the room name from the opaque session identifier.
- [ ] A valid candidate and authorized facilitator for the same session are admitted to the same room.
- [ ] A candidate cannot join a room for another session by changing a URL, room name, or client payload.
- [ ] Integration tests cover same-session admission, cross-session denial, invalid credential denial, and expired credential denial.

### Out of scope

- Rendering the tldraw editor and its recovery UI are handled in task 12.
- Canvas persistence policies beyond the service's normal synchronization behavior are deferred beyond this MVP.

### Constraints

- Depend on tasks 4, 5, and 9.
- Keep FastAPI authoritative for session access and keep canvas sync independent of interview lifecycle state.
- Do not use candidate display data in room names.

## 12. Deliver the live interview workspace
GitHub issue: https://github.com/cfornesa/ai-dev-tools-zoomcamp/issues/33

### Goal

Give authorized candidates and facilitators a live session page with a collaborative tldraw canvas, participant/session header, synchronized timer, and clear connection states.

### Acceptance criteria

- [ ] `/session/:sessionId` renders only after the current user has been authorized for that session; other users see a denial state with no session content.
- [ ] Authorized participants see a session header with participant presence, current session state, and the server-synchronized timer.
- [ ] The canvas pane connects to the authorized session-specific tldraw room and allows two authorized same-session clients to see one another's canvas changes.
- [ ] The page has visible joining, waiting, disconnected, and canvas-sync-unavailable states; an unavailable canvas does not overwrite or alter interview lifecycle state.
- [ ] Candidates do not see facilitator controls or evaluation information in the workspace.
- [ ] Integration tests cover active rendering, cross-session denial, same-session canvas room selection, and canvas-sync-unavailable recovery messaging.

### Out of scope

- Facilitator end/extend controls are handled in task 14.
- Timer transition rules are handled in task 13.
- Shared code editor and execution surfaces are outside the MVP.

### Constraints

- Depend on tasks 3, 9, 10, and 11.
- Follow `_docs/design-system.md` before implementing UI.
- Keep canvas collaboration separate from application WebSocket events.

## 13. Implement authoritative session timing and completion transitions
GitHub issue: https://github.com/cfornesa/ai-dev-tools-zoomcamp/issues/34

### Goal

Persist and enforce the session lifecycle so a facilitator can end a session, timer expiry requires a facilitator decision, and extensions are recorded durably.

### Acceptance criteria

- [ ] An authorized facilitator can transition an eligible session from scheduled/active to completed, and the completed timestamp is stored.
- [ ] When the authoritative timer reaches zero, the session changes to `expired-pending-facilitator-action` and connected clients receive that status.
- [ ] An authorized facilitator can extend an expired-pending session by a valid positive duration; the new end time and an extension-history record are persisted and broadcast.
- [ ] A candidate cannot end or extend a session, and duplicate or invalid lifecycle transitions are rejected without changing data.
- [ ] Completed sessions no longer accept candidate live-session access or new active-session controls.
- [ ] Unit, API, and WebSocket tests cover timer calculations, manual end, expiry, extension, invalid transitions, and candidate denial.

### Out of scope

- Facilitator prompts and buttons are handled in task 14.
- Evaluation persistence and UI are handled in tasks 15 and 16.
- Pause/resume is deferred beyond the MVP.

### Constraints

- Depend on tasks 2, 6, and 10.
- Make the backend the source of truth for current time and lifecycle transitions.
- Preserve extension initiator and timestamp metadata.

## 14. Build facilitator controls and live completion states
GitHub issue: https://github.com/cfornesa/ai-dev-tools-zoomcamp/issues/35

### Goal

Expose the authorized end/extend workflow in the live UI and keep candidate-facing behavior accurate as the session changes state.

### Acceptance criteria

- [ ] A facilitator sees controls to end an active session; a candidate does not see those controls.
- [ ] On timer expiry, a facilitator sees an explicit prompt to end or extend the session, while candidates see a waiting/status message rather than controls.
- [ ] Extending through the UI requires a valid positive duration, updates the displayed timer, and returns the workspace to the active state.
- [ ] Ending through the UI updates connected participants to a completed state and directs facilitators to the evaluation entry point.
- [ ] Failed control requests and disconnected WebSockets produce a visible recoverable error without falsely showing a state change.
- [ ] Integration tests cover role-based visibility, expiry prompt, valid extension, completion state, and rejected/failed control behavior.

### Out of scope

- Backend authorization and lifecycle enforcement are handled in task 13.
- Evaluation form content is handled in task 16.

### Constraints

- Depend on tasks 12 and 13.
- Follow `_docs/design-system.md` before implementing UI.
- Treat server events, not local countdown completion alone, as authoritative.

## 15. Implement private evaluation and scorecard APIs
GitHub issue: https://github.com/cfornesa/ai-dev-tools-zoomcamp/issues/36

### Goal

Persist structured evaluator feedback and private notes for completed sessions, and enforce that candidates can never read or write them.

### Acceptance criteria

- [ ] An authorized evaluator can retrieve the configured scorecard categories and submit category ratings, category rationales, recommendation, optional overall rating, overall notes, and private freeform notes for a completed session.
- [ ] Submitted evaluations record evaluator identity, submission timestamps, associated session, and per-category score/rationale records.
- [ ] Evaluation submission is rejected for a session that is not completed, missing categories/required ratings, invalid rating values, or an unauthorized requester.
- [ ] Candidate credentials receive authorization denial for every evaluation read and write endpoint and no feedback content is present in the response.
- [ ] The selected rating scale and default category definitions are documented in API/schema behavior and exposed consistently to the UI.
- [ ] API tests cover valid submission, validation failures, completed-session enforcement, evaluator retrieval, and candidate denial.

### Out of scope

- Evaluation screens and form validation are handled in task 16.
- Multiple independent evaluator experiences beyond the selected MVP behavior are deferred until a product decision is recorded.

### Constraints

- Depend on tasks 2, 5, and 13.
- Keep freeform notes private to authorized administrators/evaluators.
- Do not add weighted scoring unless it is explicitly approved.

## 16. Build the completed-session evaluation experience
GitHub issue: https://github.com/cfornesa/ai-dev-tools-zoomcamp/issues/37

### Goal

Enable an authorized evaluator to submit and review the MVP scorecard and private notes after an interview ends.

### Acceptance criteria

- [ ] A completed session's admin detail page visibly offers an evaluation entry point; a scheduled, active, or expired-pending session does not.
- [ ] `/admin/sessions/:sessionId/evaluation` renders the configured category names, rating controls, required rationale fields, recommendation choice, optional overall rating/notes, and private freeform-notes field.
- [ ] The form clearly identifies missing or invalid required values and does not submit incomplete scorecards.
- [ ] A successful submission shows an unambiguous confirmation and renders the saved values when the evaluator returns to the page.
- [ ] Candidate navigation and direct route access cannot reveal the evaluation screen or its contents.
- [ ] Component or integration tests cover completed-only entry, validation, successful submission, saved review, and candidate denial.

### Out of scope

- Evaluation API authorization and persistence are handled in task 15.
- Automated decisioning, AI evaluation, and candidate-visible feedback are outside the MVP.

### Constraints

- Depend on tasks 3, 8, 14, and 15.
- Follow `_docs/design-system.md` before implementing UI.
- Treat all evaluator notes as private content.

## 17. Add failure handling and authorization hardening across the product
GitHub issue: https://github.com/cfornesa/ai-dev-tools-zoomcamp/issues/38

### Goal

Make expected failure states safe and understandable for local/demo users while closing the key cross-session and origin/security gaps.

### Acceptance criteria

- [ ] Invalid, expired, revoked, and already-unusable invite links each lead to a clear non-sensitive page state with no access to session content.
- [ ] Backend CORS and WebSocket origin validation allow only configured frontend origins and reject unapproved origins.
- [ ] Browser-visible errors for API, WebSocket, and canvas-sync disconnection distinguish retryable unavailability from access denial without exposing stack traces, tokens, or secrets.
- [ ] Cross-session API, WebSocket, and canvas-room requests are denied for both candidate and administrator credentials unless the requester is authorized for the target session.
- [ ] Application logs avoid recording raw invite tokens, credentials, password material, private evaluation text, and secret configuration values.
- [ ] Automated security-focused tests cover configured-origin rejection, token-safe error responses, cross-session denials, and candidate evaluation denial.

### Out of scope

- External security audits, enterprise SSO, and production observability are deferred beyond the Docker Compose MVP.
- Core feature-specific authorization is implemented in tasks 5, 7, 9, 10, 11, and 15.

### Constraints

- Depend on tasks 5 through 16.
- Retain environment-driven CORS and origin configuration.
- Do not add third-party authentication, logging, or monitoring services without approval.

## 18. Add audit events for security-relevant session actions
GitHub issue: https://github.com/cfornesa/ai-dev-tools-zoomcamp/issues/39

### Goal

Record a minimal durable audit trail for sensitive invitation, lifecycle, and evaluation actions without exposing private content.

### Acceptance criteria

- [ ] An Alembic migration creates an `audit_events` table with event type, actor identity/role where available, session reference where applicable, timestamp, and non-sensitive event metadata.
- [ ] Invite creation, redemption, revocation, session end, extension, and evaluation submission create one audit event each on successful completion.
- [ ] Audit metadata identifies the action and affected resource without storing raw invite tokens, credentials, or freeform evaluation text.
- [ ] Failed/unauthorized attempts do not create misleading successful-action events.
- [ ] Authorized administrators can retrieve the audit entries for a session through a protected API response; candidates cannot retrieve them.
- [ ] Tests cover one event per successful action, no sensitive fields, and candidate denial.

### Out of scope

- A dedicated audit-log UI, external log shipping, and compliance retention policies are deferred beyond the MVP.

### Constraints

- Depend on tasks 2, 7, 9, 13, and 15.
- Keep the feature in the FastAPI/PostgreSQL boundary.
- Do not block the core live-session workflow if optional audit display is unavailable.

## 19. Complete end-to-end quality coverage and demo documentation
GitHub issue: https://github.com/cfornesa/ai-dev-tools-zoomcamp/issues/40

### Goal

Verify the supported MVP path across services and leave a reliable handoff for local demos.

### Acceptance criteria

- [ ] Backend tests cover token expiry, authorization decisions, session state transitions, timer behavior, WebSocket authorization/presence, and evaluation privacy.
- [ ] Frontend tests cover protected routes, invite states, timer display, facilitator-only controls, scorecard validation, and invite-copy feedback.
- [ ] An end-to-end smoke test covers: administrator signs in, creates a session, generates/copies an invite, candidate enters, facilitator and candidate share the session, facilitator ends it, and evaluator submits feedback.
- [ ] A separate end-to-end or integration test proves one candidate cannot enter a different session's canvas room or evaluation data.
- [ ] README documentation lists all per-service test commands, migration commands, local demo startup steps, known non-goals, and the expected recovery behavior when canvas sync is unavailable.
- [ ] The full documented test suite passes from the project-specific `02_interviews` working directory.

### Out of scope

- Performance/load testing, production deployment checks, and feature work outside the documented MVP are deferred beyond this project.

### Constraints

- Depend on tasks 1 through 18.
- Read `_docs/testing-guidelines.md` before writing or changing automated tests.
- Run only this project's commands; do not run every repository project together.

## Article reconciliation backlog

The following tasks reconcile this project with the workflow and handoff details described in “Build and Ship a Full-Stack App with AI Coding Assistants, Part 2.” Each task has exactly one matching GitHub issue.

## 20. Make environment-variable setup explicit and repeatable
GitHub issue: https://github.com/cfornesa/ai-dev-tools-zoomcamp/issues/41

### Goal

Make environment-variable setup explicit and easy to follow for local development and demos.

### Acceptance criteria

- [ ] Inventory all environment variables consumed by the backend, frontend, canvas-sync service, Docker Compose, and Playwright smoke test.
- [ ] Update `.env.example` with safe, non-secret development placeholders and concise explanations.
- [ ] Document which variables are required versus optional and where each variable is consumed.
- [ ] Make local startup and test commands work with the documented environment-file workflow.
- [ ] Ensure secrets and real credentials are not committed.
- [ ] Document common port-conflict and missing-variable recovery steps.
- [ ] Verify the documented setup with the project test suite.

## 21. Add a standalone product specification and OpenAPI contract
GitHub issue: https://github.com/cfornesa/ai-dev-tools-zoomcamp/issues/42

### Goal

Reconcile the project with the article's specification-first workflow by making product behavior and the frontend/backend agreement explicit artifacts.

### Acceptance criteria

- [ ] Add `docs/spec.md` describing roles, session lifecycle, invite redemption, live collaboration, evaluation privacy, and MVP non-goals.
- [ ] Add `openapi.yaml` covering implemented REST endpoints, methods, request bodies, response schemas, authentication rules, and error responses.
- [ ] Include application WebSocket and canvas-token authorization boundaries in the contract documentation.
- [ ] Compare the contract with FastAPI's generated OpenAPI schema and resolve material mismatches.
- [ ] Add a documented command or check for repeating the contract comparison after API changes.

## 22. Introduce a replaceable frontend service layer with mock mode
GitHub issue: https://github.com/cfornesa/ai-dev-tools-zoomcamp/issues/43

### Goal

Reconcile the project with the article's frontend-first workflow by centralizing backend calls behind a replaceable service boundary and providing a mock implementation for frontend-only development.

### Acceptance criteria

- [ ] Move authentication, sessions, invites, live-session metadata, canvas credentials, lifecycle controls, and evaluation calls behind one typed frontend service interface.
- [ ] Provide a mock implementation with representative seeded data and failure states so the frontend runs without FastAPI or Postgres.
- [ ] Select the real or mock implementation through an explicit environment/configuration setting.
- [ ] Preserve real-backend behavior and authorization boundaries when the real adapter is selected.
- [ ] Add unit/component coverage for the mock path and adapter selection.
- [ ] Document mock mode and how it differs from the Compose-backed demo.

## 23. Add Makefile-style local development commands
GitHub issue: https://github.com/cfornesa/ai-dev-tools-zoomcamp/issues/44

### Goal

Provide the simple command interface described in the article so contributors can run, test, migrate, and validate the project without memorizing per-service commands.

### Acceptance criteria

- [ ] Add a project-level `Makefile` with targets for starting/stopping Compose, backend tests, frontend tests/build, canvas-sync type checking, migrations, and the browser smoke test.
- [ ] Targets run only commands inside `02_interviews/` and preserve the documented environment-variable workflow.
- [ ] Add a help/default target listing available commands.
- [ ] Update the README to use Makefile targets as the primary local workflow while retaining direct commands for troubleshooting.
- [ ] Verify targets from a clean project shell and document required prerequisites.

## 24. Reconcile SQLite development persistence with the Postgres-first plan
GitHub issue: https://github.com/cfornesa/ai-dev-tools-zoomcamp/issues/45

### Goal

Explicitly reconcile the article's SQLite development progression with this project's decision to use PostgreSQL from the first Compose iteration, while preserving database portability.

### Acceptance criteria

- [ ] Record the decision to keep PostgreSQL as the default Compose/demo database and explain how it differs from the article's SQLite-first sequence.
- [ ] Verify SQLAlchemy/Alembic usage remains database-agnostic and does not depend on PostgreSQL-only behavior for the MVP domain.
- [ ] Provide a documented SQLite profile or command for lightweight local backend development where practical, without making it the default Compose path.
- [ ] Add a persistence restart check proving data survives a backend restart for the supported default profile.
- [ ] Ensure migration and test instructions clearly identify which database each command uses.

## 25. Add CI coverage for the documented full-stack checks
GitHub issue: https://github.com/cfornesa/ai-dev-tools-zoomcamp/issues/46

### Goal

Make the project's ready-state checks repeatable on every change, reflecting the article's next-step requirement for integration tests and CI.

### Acceptance criteria

- [ ] Add a repository workflow scoped to `02_interviews/`.
- [ ] Run backend tests, frontend unit tests, frontend production build, and canvas-sync type checking in CI.
- [ ] Run the browser smoke/integration path against Compose services with required non-secret development variables.
- [ ] Publish actionable logs or artifacts for failed browser checks.
- [ ] Keep secrets and real credentials out of workflow files and committed configuration.
- [ ] Document the CI workflow and its local equivalent in the README.

## 26. Stop live-workspace polling after authorization or terminal errors
GitHub issue: https://github.com/cfornesa/ai-dev-tools-zoomcamp/issues/47

### Goal

Make the live workspace stop background work when the session cannot be loaded or the participant is no longer allowed to enter it.

### Acceptance criteria

- [ ] The live workspace performs no further session or canvas-token requests after a terminal authentication, authorization, not-found, or completed-session response.
- [ ] Polling requests are cancelled or made non-overlapping when a transient retryable failure occurs.
- [ ] The UI distinguishes access denied, not found, completed, and temporarily unavailable states.
- [ ] A user-visible retry action is available for retryable failures and does not create duplicate polling loops.
- [ ] Component tests cover cleanup on unmount, terminal authorization failure, and retryable failure recovery.
- [ ] A browser-level check verifies that terminal failure does not continue producing requests.

## 27. Add a graceful live-session leave/end flow and release canvas resources
GitHub issue: https://github.com/cfornesa/ai-dev-tools-zoomcamp/issues/48

### Goal

Give participants and facilitators a clear way to leave or finish a live session and ensure the backend services release connection-related resources.

### Acceptance criteria

- [ ] The live workspace exposes a clear Leave/Close action that closes client connections and returns the user to a known page without changing lifecycle state.
- [ ] Facilitators have a clearly labeled Finish session action that changes the session to completed and shows the resulting terminal state.
- [ ] Candidates cannot finish or extend a session, and they see a clear waiting/ended state when the facilitator finishes it.
- [ ] The UI shows connecting, connected, reconnecting, disconnected, and ended states without trapping the user on an indefinite loading screen.
- [ ] Canvas-sync removes or disposes a room after its last client disconnects, or documents and tests an equivalent bounded resource policy.
- [ ] Backend and canvas service logs make connect, disconnect, finish, and cleanup events diagnosable without exposing tokens.
- [ ] Tests cover browser leave, facilitator finish, candidate denial, socket disconnect, and room cleanup.

## 28. Add an end-to-end live-session resilience scenario
GitHub issue: https://github.com/cfornesa/ai-dev-tools-zoomcamp/issues/49

### Goal

Verify the complete administrator/candidate live-session workflow under refresh, reconnect, authorization failure, and finish conditions.

### Acceptance criteria

- [ ] The scenario starts from a clean browser context, authenticates an administrator, creates a session, and opens the live workspace.
- [ ] The scenario verifies that the workspace reaches a connected/usable state rather than remaining in joining/loading indefinitely.
- [ ] The scenario opens the same session through a valid candidate invite and verifies same-session access.
- [ ] The scenario refreshes one participant, temporarily disconnects or restarts canvas-sync, and verifies a visible recoverable state followed by successful rejoin.
- [ ] The scenario opens a session without valid credentials and verifies a terminal access-denied state with no continuing request loop.
- [ ] The scenario finishes the session through the facilitator flow and verifies both participants see the ended/completed state.
- [ ] The test emits bounded diagnostics for failed requests, WebSocket closure, console errors, and service logs without recording passwords or tokens.
- [ ] The scenario is runnable locally and is integrated with the project's CI checks.

## Open-source canvas replacement backlog

These tasks replace the Tldraw SDK with a self-hosted, Apache-2.0-compatible draw.io/diagrams.net integration while preserving the existing session authorization, two-sided collaboration, drawing, text, shape, selection, and reconnect behavior. The current canvas remains the fallback until the replacement passes the full acceptance criteria.

## 29. Prove the self-hosted draw.io integration and license boundary
GitHub issue: https://github.com/cfornesa/ai-dev-tools-zoomcamp/issues/51

### Goal

Confirm that a self-hosted draw.io editor can be embedded and controlled locally without depending on the hosted `embed.diagrams.net` service, and document the licensing/dependency decision before implementation.

### Acceptance criteria

- [ ] Build a disposable proof of concept under `02_interviews/` that serves the draw.io editor from a local/self-hosted asset or Compose service.
- [ ] Verify the editor can be embedded in the React frontend and can exchange load/save events with the parent application without relying on a third-party hosted origin.
- [ ] Verify the local editor supports freehand drawing, text, shapes, selection, undo/redo, zoom/pan, and XML serialization needed by the live workspace.
- [ ] Record the selected draw.io source/version, Apache 2.0 notices, bundled dependency notices, and any trademark/branding obligations in `docs/canvas-replacement.md`.
- [ ] Record a go/no-go decision and a fallback plan if self-hosted embedding is not supported by the selected draw.io build.
- [ ] Do not remove Tldraw or change the production canvas path in this discovery task.

### Constraints

- Depend on tasks 4, 11, 12, and 28.
- Do not use `embed.diagrams.net` as the production dependency for the replacement.
- Do not add a dependency or vendor a large editor bundle until the user-approved implementation path is documented.

## 30. Integrate the self-hosted draw.io editor into the live workspace
GitHub issue: https://github.com/cfornesa/ai-dev-tools-zoomcamp/issues/50

### Goal

Replace the Tldraw UI in the live workspace with the approved self-hosted draw.io editor while preserving the current participant and facilitator experience.

### Acceptance criteria

- [ ] The live workspace renders the self-hosted draw.io editor for both facilitator and candidate participants.
- [ ] The editor provides usable freehand drawing, text, shapes, connectors, selection, deletion, undo/redo, zoom/pan, and keyboard interaction.
- [ ] The editor is constrained to the canvas container and does not cover or shift the session header, leave, finish, timer, or status controls.
- [ ] The parent application handles editor initialization, load, save, exit, and error events without exposing tokens or internal stack traces.
- [ ] The editor origin and frame messaging are restricted to the configured local origin and validated event types.
- [ ] The Tldraw-specific React components, stylesheet import, and runtime dependency are no longer required by the live workspace.

### Constraints

- Depend on task 29.
- Preserve the existing session lifecycle and role authorization boundaries.
- Keep the replacement behind a configuration flag until task 33 is complete.

## 31. Add collaborative draw.io document state and conflict-safe persistence
GitHub issue: https://github.com/cfornesa/ai-dev-tools-zoomcamp/issues/52

### Goal

Give both participants a shared, durable draw.io document model with reconnect behavior equivalent to the current canvas workflow.

### Acceptance criteria

- [ ] A session room has one authoritative draw.io XML document and a monotonically increasing revision/version.
- [ ] Authorized facilitator and candidate clients receive the current document when joining and receive subsequent updates from the other participant.
- [ ] Updates are scoped to the session room and reject unauthorized or cross-session clients.
- [ ] Concurrent saves use revision checks, ordered updates, or an equivalent conflict policy that prevents silent last-write data loss.
- [ ] Refreshing a participant and restarting canvas-sync restore the latest accepted document without resetting the room to a blank canvas.
- [ ] Empty-room cleanup and bounded in-memory/storage behavior are documented and tested.
- [ ] Logs and errors remain free of raw credentials, invite tokens, and private session content.

### Constraints

- Depend on tasks 10, 11, 29, and 30.
- Reuse the existing authorization boundary where practical, but do not couple draw.io XML handling to Tldraw data structures.
- Keep the persistence choice explicit; do not silently introduce a new database dependency.

## 32. Reach canvas feature parity and harden the two-sided workflow
GitHub issue: https://github.com/cfornesa/ai-dev-tools-zoomcamp/issues/53

### Goal

Ensure the open-source replacement retains the critical interview functionality and remains usable under normal and degraded conditions.

### Acceptance criteria

- [ ] Browser tests verify facilitator and candidate can draw, add text, create/select/move/delete a shape, and observe the shared result.
- [ ] Browser tests verify undo/redo, zoom/pan, refresh/rejoin, temporary canvas-sync interruption, and session finish behavior.
- [ ] The UI shows explicit connecting, connected, saving/saved, reconnecting, disconnected, and ended states.
- [ ] Canvas keyboard and pointer interactions do not trigger page scrolling, accidental session actions, or focus traps.
- [ ] The editor works at the supported desktop viewport and has a documented behavior for smaller viewports.
- [ ] Test diagnostics identify editor, WebSocket, save, and authorization failures without recording credentials or document contents.

### Constraints

- Depend on tasks 30 and 31.
- Read the project testing and design guidance before adding or changing tests.
- Keep the same candidate/facilitator permissions as the existing workflow.

## 33. Remove Tldraw, document the self-hosted canvas, and switch the default path
GitHub issue: https://github.com/cfornesa/ai-dev-tools-zoomcamp/issues/54

### Goal

Complete the migration so the project ships with the self-hosted open-source canvas as its default and no longer carries the Tldraw SDK licensing or runtime dependency.

### Acceptance criteria

- [x] Remove Tldraw packages, imports, styles, dead adapters, and unused synchronization code from the frontend and lockfiles.
- [x] Update Docker Compose, environment examples, README, architecture/spec documents, and CI to describe the self-hosted XML canvas service and its local startup/test commands.
- [x] Add an open-source attribution/license manifest covering the canvas decision and all newly bundled editor dependencies.
- [x] The full backend, frontend, canvas-sync, and browser test suites pass with the replacement as the default path.
- [x] A clean project setup can start the editor and application without network access to the hosted draw.io editor or other third-party canvas service.
- [x] The final migration issue links the proof-of-concept decision, feature-parity evidence, and known limitations.

### Constraints

- Depend on tasks 29 through 32.
- Do not delete the existing implementation until replacement acceptance criteria are met.
- Keep the existing backend session, invitation, evaluation, and authorization contracts stable unless a migration issue documents a required change.

## Authentication hardening backlog

These tasks investigate and, if approved, add Google Identity Services/OIDC authentication and reCAPTCHA v3 risk signals without weakening the existing role and session boundaries. Google authentication identifies an account; reCAPTCHA is an abuse/risk signal and is not a replacement for password, session, authorization, or invite controls.

## 34. Define the account, role, and authentication security model
GitHub issue: https://github.com/cfornesa/ai-dev-tools-zoomcamp/issues/55

### Goal

Decide how administrator signup/login, Google authentication, candidate invite access, account linking, and reCAPTCHA risk decisions fit the current MVP before changing the auth contract.

### Acceptance criteria

- [ ] Document whether public signup is allowed, administrator-only, invitation-only, or disabled for the MVP; candidate access remains scoped to an interview invite unless explicitly changed.
- [ ] Define supported login methods, account states, role assignment rules, account-linking rules, logout/session revocation behavior, and recovery path.
- [ ] Define the threat model for credential stuffing, automated signup, account takeover, replayed Google ID tokens, replayed reCAPTCHA tokens, CSRF, open redirects, and cross-session access.
- [ ] Decide whether to use Google Identity Services credential/ID-token flow or the OAuth 2.0 authorization-code server flow, with rationale and redirect/CSRF requirements.
- [ ] Define reCAPTCHA actions, hostname/origin policy, score bands, rate-limit interaction, fail-open/closed behavior, privacy/consent requirements, and a non-reCAPTCHA local-test mode.
- [ ] Record the decision in `docs/authentication.md` and update `docs/spec.md` and `openapi.yaml` boundaries without implementing the new flow.

### Constraints

- Depend on tasks 5, 9, 15, and 20.
- Do not accept an email address or Google profile field as proof of identity without verified credentials.
- Keep secrets server-side and candidate invite authorization separate from administrator identity.

## 35. Add durable federated identities and secure application sessions
GitHub issue: https://github.com/cfornesa/ai-dev-tools-zoomcamp/issues/56

### Goal

Create the persistence and backend session foundation needed to support Google-authenticated users without breaking existing administrators or candidate invite credentials.

### Acceptance criteria

- [ ] Add migrations/models for a stable application user, external identity provider, verified provider subject (`sub`), normalized email metadata, role/status, and timestamps without storing Google access tokens unless required by a future feature.
- [ ] Use the provider subject as the Google identity key; prevent unsafe account linking by email alone.
- [ ] Implement server-managed, revocable sessions with secure cookie attributes or a documented equivalent, rotation/expiry, logout, and CSRF protection for cookie-authenticated state changes.
- [ ] Preserve candidate invite tokens as short-lived, session-scoped credentials with no access to admin resources.
- [ ] Migrate or explicitly retire the current development admin login path with a documented compatibility strategy.
- [ ] Add tests for identity uniqueness, role isolation, session expiry/revocation, account-linking denial, and cross-session authorization.

### Constraints

- Depend on task 34.
- Do not store raw OAuth authorization codes, reCAPTCHA secrets, or long-lived provider access tokens in application data.
- Do not add a new persistence dependency without approval.

## 36. Implement Google Identity Services login and approved signup flow
GitHub issue: https://github.com/cfornesa/ai-dev-tools-zoomcamp/issues/57

### Goal

Allow an approved user population to sign up/sign in with Google while the backend remains authoritative for token verification, account creation, role assignment, and application sessions.

### Acceptance criteria

- [ ] Configure development and production Google OAuth client IDs with explicit allowed origins and redirect URIs; keep client secrets out of the frontend and repository.
- [ ] Add frontend Google sign-in/sign-up entry points using the approved Google Identity Services flow and accessible loading, denial, popup/redirect failure, and retry states.
- [ ] Send the Google credential or authorization result to the backend over HTTPS and verify signature, issuer, audience, expiry, and the stable `sub` claim before creating or loading an account.
- [ ] Enforce the account/role policy from task 34, including any allowed Workspace domain restriction and administrator approval process.
- [ ] Prevent duplicate accounts and unsafe email-based account takeover; require explicit authenticated linking for additional login methods.
- [ ] Return only the application session result needed by the frontend; never expose Google tokens to logs, URLs, or unrelated APIs.
- [ ] Add backend and frontend tests using deterministic provider fixtures/mocks, plus a documented manual configuration check for real Google credentials.

### Constraints

- Depend on tasks 34 and 35.
- Use Google Identity Services/OIDC verification guidance; do not trust client-supplied Google user IDs or profile fields.
- Preserve the invite-based candidate path unless the approved product decision explicitly expands it.

## 37. Add reCAPTCHA v3 risk assessment to signup, login, and invite redemption
GitHub issue: https://github.com/cfornesa/ai-dev-tools-zoomcamp/issues/59

### Goal

Use reCAPTCHA v3 as a server-verified, action-specific abuse signal for sensitive unauthenticated flows without making it the sole authentication mechanism.

### Acceptance criteria

- [ ] Configure separate site keys/secrets or documented key scopes for local/test/staging/production; never expose the secret key to the frontend.
- [ ] Execute named actions such as `signup`, `login`, and `invite_redeem` immediately before the protected request and send the short-lived token to the backend.
- [ ] Verify every token server-side and require success, expected action, configured hostname, acceptable freshness, and a configurable score policy; reject duplicate/expired/malformed tokens safely.
- [ ] Implement configurable response bands: allow, rate-limit or require step-up/secondary verification, and deny; do not hard-code an unvalidated universal threshold.
- [ ] Combine scores with existing per-IP/account/device rate limits and generic errors that do not reveal account existence.
- [ ] Define behavior when Google reCAPTCHA is unavailable, over quota, blocked by privacy tooling, or disabled in local tests; production protection must not be silently bypassed.
- [ ] Add tests for valid/mismatched action, wrong hostname, low score, duplicate token, provider timeout, provider outage, and local mock mode.

### Constraints

- Depend on tasks 34 and 36.
- Keep the reCAPTCHA secret and verification response out of logs and client responses.
- Document Google reCAPTCHA data-processing, consent, CSP, and privacy implications before production enablement.

## 38. Harden authentication UX, browser policy, and operational configuration
GitHub issue: https://github.com/cfornesa/ai-dev-tools-zoomcamp/issues/58

### Goal

Make the combined Google/reCAPTCHA authentication flow safe, diagnosable, testable, and deployable across local, staging, and production environments.

### Acceptance criteria

- [ ] Update CORS, CSP, frame/ancestor, cookie, redirect, and Google script/origin configuration for the selected GIS and reCAPTCHA integrations.
- [ ] Add frontend states for provider loading, consent/blocked scripts, low-risk step-up, authentication denial, rate limiting, and retry without leaking sensitive details.
- [ ] Add structured, token-safe audit events for signup, login, Google verification result, reCAPTCHA decision band, account linking, logout, and session revocation.
- [ ] Add environment examples and a deployment checklist for client IDs, secrets, allowed origins, redirect URIs, site-key domains, score thresholds, privacy disclosures, and key rotation.
- [ ] Provide deterministic test doubles for CI and a separate manual smoke test with real provider configuration; CI must not require production Google or reCAPTCHA secrets.
- [ ] Verify the existing administrator, candidate invite, live canvas, evaluation privacy, logout, and cross-session tests still pass.

### Constraints

- Depend on tasks 35 through 37.
- Do not log raw Google credentials, reCAPTCHA tokens, invite tokens, passwords, or private evaluation data.
- Do not make external provider availability an unbounded dependency for local development or automated tests.

## 39. Render the collaborative canvas document visibly
GitHub issue: https://github.com/cfornesa/ai-dev-tools-zoomcamp/issues/60

### Goal

Replace the blank XML-snapshot experience with a real, visible drawing surface whose editor model and persisted document format are explicitly converted and kept compatible across participants.

### Acceptance criteria

- [ ] The live interview workspace opens with a visibly usable drawing surface rather than only a status/XML notification.
- [ ] The initial persisted document is converted into renderable editor elements; raw `mxCell` XML nodes are not inserted directly into an SVG renderer.
- [ ] Freehand, text, rectangle, connector, selection, move, delete, undo/redo, zoom, and reload visibly affect the canvas.
- [ ] Edits serialize into the supported room document format and survive save, refresh, reconnect, and canvas-sync restart.
- [ ] Two authorized participants see the same rendered initial document and subsequent edits.
- [ ] Empty, malformed, unsupported, and oversized documents produce recoverable user-facing errors without breaking interview lifecycle state.
- [ ] The canvas viewport remains visible and bounded within the live workspace; toolbar and status controls do not replace it.
- [ ] Browser/component regression coverage asserts rendered shapes and exercises an edit/save/reload path, not just iframe presence, status text, or XML strings.
- [ ] Documentation identifies the canonical editor model, conversion rules, and compatibility limitations.

### Constraints

- Depend on tasks 30 through 33.
- Preserve session authorization, iframe origin/source validation, canvas-sync room authorization, and durable XML persistence contracts.
- Read the available UI/testing guidance before adding coverage; if the guidance files are absent, document the fallback used for the test design.

## 40. Make the UI responsive and normalize button/link styling across devices
GitHub issue: https://github.com/cfornesa/ai-dev-tools-zoomcamp/issues/61

### Goal

Provide a consistent, accessible responsive UI that works through mobile browsers on iPhone, iPad, Android phones/tablets, and desktop browsers with touch, keyboard, mouse, and stylus input where supported.

### Acceptance criteria

- [ ] Navigation links, action links, primary/secondary buttons, destructive actions, and disabled/loading states have consistent visual treatment and correct semantics.
- [ ] Keyboard focus indicators are visible and distinct; hover styling is not the only interaction affordance.
- [ ] Interactive controls meet a documented touch-target minimum and work with mouse, keyboard, touch, and stylus where supported.
- [ ] The shell, cards, forms, session lists, controls, evaluation forms, and live workspace reflow without horizontal page scrolling at representative phone, tablet, and desktop widths.
- [ ] The live canvas/iframe, toolbar, session controls, and forms use responsive sizing rather than fixed desktop assumptions in portrait and landscape layouts.
- [ ] Mobile safe areas, device rotation, virtual keyboards, reduced motion, and text zoom are handled or documented where platform limitations apply.
- [ ] Text, controls, status/error messages, and focus states meet the project’s documented contrast and accessibility expectations.
- [ ] Automated coverage checks representative mobile phone, tablet, and desktop viewports for navigation, forms, session controls, canvas containment, overflow, keyboard focus, and touch-sized controls.
- [ ] A manual device/browser matrix covers iOS Safari, iPadOS Safari, Android Chrome, Android tablet Chrome, and current desktop Chromium/Firefox/WebKit, with known limitations documented.
- [ ] Design/system documentation and README describe responsive breakpoints, component conventions, and local verification commands.

### Constraints

- Depend on the existing UI surfaces from tasks 12, 14, 16, and 30 through 33; this task is independent of the canvas document-rendering fix in task 39.
- Preserve authentication, invitation authorization, interview lifecycle, evaluation privacy, and canvas synchronization contracts.
- Read the available UI/testing guidance before changing UI or adding coverage; if the guidance files are absent, document the fallback used for the test design.

## 41. Restore replacement invite generation for joinable sessions
GitHub issue: https://github.com/cfornesa/ai-dev-tools-zoomcamp/issues/62

### Goal

Allow an administrator to recover a usable candidate session link whenever the session is still joinable and its prior invite is expired, revoked, or already redeemed.

### Acceptance criteria

- [ ] The session detail page clearly distinguishes active, expired, revoked, redeemed, and absent invite states.
- [ ] A scheduled, active, or expired-pending session exposes a Generate or Regenerate action whenever it is not completed, including when the previous invite is expired, revoked, or redeemed.
- [ ] Regeneration invalidates prior usable invites, returns a fresh high-entropy URL with a new expiry, and displays a copyable URL with success/error feedback.
- [ ] The backend applies the same non-completed-session rule as the UI; completed sessions cannot generate or regenerate invites, and newly generated invites cannot be redeemed for completed sessions.
- [ ] Invite history remains auditable and does not expose raw tokens in API responses, logs, or persisted data.
- [ ] Backend, frontend, and browser tests cover expired/revoked/redeemed replacement, completed-session denial, old-token invalidation, and copy feedback.

### Out of scope

- Email or SMS delivery of invitations.
- Reopening or changing the lifecycle of a completed session.

### Constraints

- Depend on tasks 6, 9, 15, and 27.
- Preserve invite hashing, session scoping, expiry, rate limiting, and candidate authorization boundaries.

## 42. Make the sessions page the canonical administrator landing page
GitHub issue: https://github.com/cfornesa/ai-dev-tools-zoomcamp/issues/63

### Goal

Remove the redundant administrator dashboard hop so a successful administrator login opens the complete sessions page directly, with navigation actions presented consistently.

### Acceptance criteria

- [ ] Successful password or Google administrator login navigates directly to `/admin/sessions`.
- [ ] `/admin` redirects to `/admin/sessions` without rendering a separate dashboard page or an “Open sessions” call-to-action.
- [ ] The page title and navigation label use “Sessions” and do not imply that the list contains only open sessions; completed sessions remain visibly included.
- [ ] Header navigation uses the shared button-style treatment for navigational links while retaining link semantics, and action controls remain native buttons with consistent primary, secondary, destructive, disabled, and focus states.
- [ ] The Interview Canvas brand link, Sessions navigation, logout action, session-detail actions, and evaluation navigation follow the same documented control conventions across desktop and mobile widths.
- [ ] Component and browser tests verify the post-login route, `/admin` redirect, absence of the redundant dashboard action, and accessible navigation/button semantics.

### Out of scope

- Session search, sorting, and status filtering are handled in task 43 / issue #64.
- Responsive device-matrix validation remains in task 40 / issue #61.

### Constraints

- Depend on tasks 3, 5, 8, and 40.
- Do not replace navigational links with non-semantic click-only controls.
- Preserve protected-route behavior and logout/session revocation.

## 43. Add search, sorting, and lifecycle filters to the sessions page
GitHub issue: https://github.com/cfornesa/ai-dev-tools-zoomcamp/issues/64

### Goal

Make the administrator sessions page useful as the complete session index by supporting fast search, deterministic sorting, and lifecycle filtering, including completed sessions.

### Acceptance criteria

- [ ] The sessions page provides a labeled search field that matches candidate name, candidate email, and session identifier case-insensitively.
- [ ] The page provides a status filter with an All option and options for scheduled, active, expired-pending-facilitator-action, and completed sessions.
- [ ] The page provides deterministic sort choices for candidate name A–Z, scheduled date ascending, and scheduled date descending, with a documented default.
- [ ] Search, filter, and sort can be combined and update the visible result set without losing the current controls or navigation context.
- [ ] Completed sessions are included when All is selected and can be isolated with the completed filter; the page does not label the full list as open sessions.
- [ ] Empty and no-match states explain whether there are no sessions or no sessions matching the current criteria, with a way to clear the criteria.
- [ ] Session rows retain accessible links to details and show candidate, scheduled date, lifecycle status, and relevant duration information in every sort/filter state.
- [ ] Component tests cover case-insensitive matching, each sort direction, every lifecycle filter, combined criteria, completed sessions, and no-match recovery; browser coverage verifies the controls visibly change results.

### Out of scope

- Pagination, saved views, bulk actions, and server-side full-text search.
- Changes to session lifecycle transitions, invitation authorization, or evaluation privacy.

### Constraints

- Depend on tasks 6, 8, 21, and 42.
- Use the existing typed service boundary; do not introduce a new persistence or search dependency.
- Read the available UI/testing guidance before adding coverage; if absent, document the fallback used.

## 44. Bring the self-hosted canvas to a familiar diagram-editor UX
GitHub issue: https://github.com/cfornesa/ai-dev-tools-zoomcamp/issues/65

### Goal

Make the self-hosted canvas feel like a real collaborative drawing workspace, with familiar tldraw/diagrams.net interaction affordances and a coherent visual hierarchy, while preserving the dependency-free local editor and existing authorization/document protocols.

### Acceptance criteria

- [ ] The product documentation and UI accurately distinguish the dependency-free compatibility editor from upstream draw.io, while documenting the supported feature set and limitations.
- [ ] The canvas presents a coherent editor shell with grouped tools for selection, hand/pan, freehand, text, shapes, connectors, delete, undo/redo, zoom, reset/fit, and save/reload; each tool has an accessible name, tooltip or equivalent discoverability, and a visible active/disabled state.
- [ ] Selecting an element visibly shows a selection box and usable manipulation affordances; users can select, move, resize where supported, delete, and edit text without relying on raw XML or browser-default controls.
- [ ] Pan and zoom work through explicit controls and expected pointer/keyboard gestures without scrolling the surrounding interview page; the viewport, canvas background, document bounds, and selection state remain visually understandable at desktop and mobile-supported sizes.
- [ ] Shapes, connectors, freehand strokes, and text have consistent visual styling, render with sufficient contrast, and provide feedback for hover, focus, selection, creation, save, conflict, and error states.
- [ ] The canvas status area is consolidated so users do not see duplicate or contradictory “Edited/Loaded” messages from the host and iframe; connection and persistence states remain understandable without exposing tokens, XML contents, or implementation details.
- [ ] The facilitator/candidate canvas experience remains functionally equivalent and session controls remain visually separate from the editor toolbar; role permissions and lifecycle behavior do not change.
- [ ] Browser coverage exercises tool selection, active states, selection/manipulation, pan/zoom, keyboard shortcuts, text editing, save/reload feedback, and degraded/reconnect states at supported desktop and mobile viewports.
- [ ] Design documentation records the canvas interaction model, supported gestures, keyboard shortcuts, responsive behavior, and known differences from tldraw/upstream draw.io.

### Out of scope

- Replacing the local editor with a hosted `embed.diagrams.net` dependency.
- Arbitrary draw.io stencil libraries, lossless round-tripping of every upstream style, or shared code editing.
- Room authorization, XML persistence, conflict policy, and lifecycle rules handled by tasks 30–33 and issue #52.

### Constraints

- Depend on tasks 30 through 33, 39, and 40; coordinate with issue #53 rather than duplicating its feature-parity coverage.
- Preserve exact iframe origin/source validation, room authorization, revision checks, XML size limits, and token-safe diagnostics.
- Do not add a large editor dependency or vendor upstream assets without documenting licensing, notices, and the migration decision.

## 45. Make the root Compose command work for the Interview Canvas project
GitHub issue: https://github.com/cfornesa/ai-dev-tools-zoomcamp/issues/66

### Goal

Provide one unambiguous, working Compose entrypoint for `02_interviews` and make repository-level project boundaries explicit.

### Acceptance criteria

- [ ] `docker compose up --build` from the repository root starts the `02_interviews` stack, or the root README clearly identifies the exact supported project-scoped command and does not present the root command as supported.
- [ ] The command from `02_interviews/` remains supported.
- [ ] Compose-relative paths, environment files, named volumes, health checks, and service dependencies work from the supported invocation location.
- [ ] Root and project READMEs provide copyable setup, start, stop, test, and rebuild commands and identify the project being started.
- [ ] Verification covers a clean checkout or clean working directory, including the missing-configuration failure mode.
- [ ] No command requires activating the unrelated `01_todo` virtual environment.

### Out of scope

- Changes to the `01_todo` Django runtime.
- Production deployment or managed cloud hosting.

## 46. Fix session-detail visual hierarchy and responsive action layout
GitHub issue: https://github.com/cfornesa/ai-dev-tools-zoomcamp/issues/67

### Goal

Make the administrator session-detail page readable and actionable at desktop and mobile widths while preserving authorization and lifecycle behavior.

### Acceptance criteria

- [ ] Session title, lifecycle status, metadata, section headings, and body text use a documented responsive hierarchy.
- [ ] Primary, secondary, and destructive actions have consistent spacing, grouping, focus, disabled/loading, and touch-target treatment; adjacent buttons do not appear accidentally merged.
- [ ] Session actions remain visually separate from invitation and evaluation sections.
- [ ] The layout reflows without horizontal scrolling at representative phone, tablet, and desktop widths, including long names and lifecycle labels.
- [ ] Loading, empty, and error states are meaningful and do not conceal unavailable data or actions.
- [ ] Component and browser visual/geometry coverage includes an expired-pending session and narrow viewport.
- [ ] UI documentation records type scale, spacing, action-group conventions, and breakpoints.

### Out of scope

- Authentication, invite-token security, lifecycle rules, evaluation privacy, or canvas replacement.

## 47. Surface actionable invitation recovery on expired session details
GitHub issue: https://github.com/cfornesa/ai-dev-tools-zoomcamp/issues/68

### Goal

Make every non-completed session detail view explicitly communicate invitation state and expose the appropriate recovery action.

### Acceptance criteria

- [ ] Scheduled, active, and expired-pending details visibly show no invite, active, expired, redeemed, or revoked state.
- [ ] An expired-pending session with no usable invite offers Generate invite; one with an unusable invite offers Regenerate invite.
- [ ] Generation/regeneration shows success/error feedback and a copyable candidate URL.
- [ ] Completed sessions state that invitation recovery is unavailable and do not show misleading generation controls.
- [ ] Loading, unavailable/error, and no-data states are tested; the invitation section never renders as an unexplained blank area.
- [ ] Component and browser tests cover the screenshot state, link feedback, completed denial, and narrow viewport rendering.
- [ ] Raw invite tokens are not exposed in diagnostics or unrelated page content.

### Dependency

- Depends on issue #62 for the backend non-completed-session invite rule and token invalidation behavior.

## 48. Provide a working repository-root Compose entrypoint
GitHub issue: https://github.com/cfornesa/ai-dev-tools-zoomcamp/issues/69

### Goal

Make the documented command `docker compose up --build` work when run from the
repository root, while keeping `02_interviews/` independently runnable and
keeping the unrelated `01_todo` project out of the Compose stack.

### Acceptance criteria

- [ ] From a clean checkout at the repository root, `docker compose config` resolves the PostgreSQL, backend, frontend, canvas-sync, and canvas-editor services without a missing-configuration error.
- [ ] `docker compose up --build` from the repository root starts the same five services with working build contexts, environment-file defaults, health checks, dependency ordering, ports, and named volumes as the project-scoped command.
- [ ] Running `docker compose up --build` from `02_interviews/` remains supported and does not create a second incompatible project configuration.
- [ ] A root-level `.env.example` or an equivalent documented environment handoff makes all required interpolation values unambiguous; no command requires activating `01_todo/.venv`.
- [ ] Root and project documentation provide copyable setup, start, rebuild, stop, data-reset, test, and troubleshooting commands, including the prior `no configuration file provided` failure mode.
- [ ] Automated verification exercises both invocation directories and asserts that the expected service names and dependency health conditions are present.

### Out of scope

- Invite lifecycle behavior is task 49 / issue https://github.com/cfornesa/ai-dev-tools-zoomcamp/issues/70.
- Shared control styling is task 50 / issue https://github.com/cfornesa/ai-dev-tools-zoomcamp/issues/71.
- Canvas interaction and persistence are tasks 51–52 / issues https://github.com/cfornesa/ai-dev-tools-zoomcamp/issues/72 and https://github.com/cfornesa/ai-dev-tools-zoomcamp/issues/73.

### Constraints

- Keep the `01_todo` Django project independent.
- Reuse the existing five-service Compose architecture; do not add production hosting.
- Preserve named-volume data and existing port override behavior.

## 49. Make candidate-link generation and regeneration reliable end to end
GitHub issue: https://github.com/cfornesa/ai-dev-tools-zoomcamp/issues/70

### Goal

Ensure an administrator can always see and use the correct Generate or
Regenerate action for a joinable session and can copy the resulting candidate
link without encountering a blank invitation section.

### Acceptance criteria

- [ ] Scheduled, active, and expired-pending session details explicitly render absent, active, expired, redeemed, revoked, loading, and unavailable invitation states.
- [ ] A joinable session with no invite shows Generate invite; a joinable session with an expired, redeemed, or revoked invite shows Regenerate invite; completed sessions show the reason recovery is unavailable and no generation control.
- [ ] Generate and Regenerate return a fresh URL with an expiry, invalidate prior usable invites when required, display the URL in a dedicated copyable field, and provide visible success and clipboard-failure feedback.
- [ ] The API and UI use the same joinable-session rule, including the expired-pending-facilitator-action state; completed-session attempts fail with a visible non-sensitive error.
- [ ] Repeated loading, API failure, and refresh after generation never leave the invitation section blank or hide the session actions.
- [ ] Component and browser tests cover absent, expired, redeemed, revoked, generated, regenerated, completed, API-failure, and clipboard-failure cases without exposing raw tokens in logs or unrelated content.

### Out of scope

- Root Compose invocation is task 48 / issue https://github.com/cfornesa/ai-dev-tools-zoomcamp/issues/69.
- Shared navigation/button visual conventions are task 50 / issue https://github.com/cfornesa/ai-dev-tools-zoomcamp/issues/71.
- Canvas editor behavior is tasks 51–52 / issues https://github.com/cfornesa/ai-dev-tools-zoomcamp/issues/72 and https://github.com/cfornesa/ai-dev-tools-zoomcamp/issues/73.

### Constraints

- Preserve invite hashing, expiry, rate limiting, session scoping, audit history, and candidate authorization.
- Do not add email/SMS delivery or a new persistence dependency.
- Use the existing typed service boundary and backend invite endpoints unless a contract correction is required.

## 50. Normalize action controls and navigation semantics across the application
GitHub issue: https://github.com/cfornesa/ai-dev-tools-zoomcamp/issues/71

### Goal

Give administrators, facilitators, and candidates a consistent control language:
navigational links retain link semantics but look like intentional buttons, and
mutating actions remain native buttons with clear grouping and state feedback.

### Acceptance criteria

- [ ] Brand, Sessions, Open workspace, Evaluation, Enter session, Leave, and other navigation actions have consistent button-style treatment while remaining keyboard- and screen-reader-accessible links.
- [ ] Finish, Extend, Generate, Regenerate, Revoke, Save, Copy, Delete, and editor actions remain native buttons with distinct primary, secondary, destructive, disabled, loading, and success/error states.
- [ ] Adjacent controls have visible separation, predictable ordering, and at least the documented 44px touch target; focus indicators remain visible without relying on hover.
- [ ] Session detail, live workspace, invitation, evaluation, and shell controls reflow without horizontal overflow at phone, tablet, and desktop widths, including long labels.
- [ ] Browser and component tests assert accessible roles/semantics, style/state classes, focusability, touch-target geometry, and the screenshot scenarios that previously rendered plain links or merged buttons.
- [ ] The design documentation records the control taxonomy, spacing, hierarchy, responsive breakpoints, and when to use a link versus a button.

### Out of scope

- Root Compose startup is task 48 / issue https://github.com/cfornesa/ai-dev-tools-zoomcamp/issues/69.
- Invitation state/API behavior is task 49 / issue https://github.com/cfornesa/ai-dev-tools-zoomcamp/issues/70.
- Canvas-specific toolbar interaction is task 51 / issue https://github.com/cfornesa/ai-dev-tools-zoomcamp/issues/72.

### Constraints

- Preserve route semantics, authorization boundaries, lifecycle actions, and evaluation privacy.
- Do not replace links with click-only controls or introduce a UI framework dependency.
- Follow the project-local responsive guidance where the repository has no external design-system file.

## 51. Deliver a familiar tldraw-like canvas interaction surface
GitHub issue: https://github.com/cfornesa/ai-dev-tools-zoomcamp/issues/72

### Goal

Make the self-hosted canvas feel like an understandable collaborative drawing
workspace, with discoverable tools and direct manipulation for drawing, text,
shapes, connectors, selection, and viewport navigation.

### Acceptance criteria

- [ ] The editor presents grouped, accessible tools for select, hand/pan, freehand, text, rectangle/shape, connector, delete, undo, redo, zoom, reset/fit, save, and reload, with tooltips or equivalent discoverability and a visible active/disabled state.
- [ ] Freehand strokes, text, rectangles/shapes, and connectors can be created with pointer or touch input on the visible canvas; creation does not require editing XML or using browser prompts for the initial content.
- [ ] Users can select an element, see a selection box, move it, resize it where supported, edit text, delete it, and use keyboard shortcuts without accidentally scrolling the interview page.
- [ ] Pan, zoom, reset/fit, pointer capture, and bounded document scrolling work at supported desktop and mobile viewport sizes without hiding the canvas beneath the toolbar.
- [ ] Facilitator and candidate receive the same editor affordances and existing role/lifecycle authorization remains unchanged.
- [ ] Browser coverage exercises each tool family, active state, creation, selection/manipulation, text editing, keyboard deletion, pan/zoom, and narrow viewport behavior using visible rendered elements rather than XML-only assertions.
- [ ] Documentation clearly distinguishes this dependency-free compatibility editor from upstream tldraw/draw.io and records supported gestures, shortcuts, limitations, and accessibility behavior.

### Out of scope

- Durable cross-client synchronization and restart recovery are task 52 / issue https://github.com/cfornesa/ai-dev-tools-zoomcamp/issues/73.
- Root Compose startup is task 48 / issue https://github.com/cfornesa/ai-dev-tools-zoomcamp/issues/69.
- Application-wide control styling is task 50 / issue https://github.com/cfornesa/ai-dev-tools-zoomcamp/issues/71.
- Shared code editing and code execution remain outside the MVP.

### Constraints

- Preserve exact iframe origin/source checks, room authorization, XML size limits, and token-safe diagnostics.
- Do not add a large editor dependency or vendor upstream assets without an explicit licensing decision.
- Keep the canonical SVG-backed document model and conversion boundary documented.

## 52. Make canvas persistence, collaboration, and status presentation trustworthy
GitHub issue: https://github.com/cfornesa/ai-dev-tools-zoomcamp/issues/73

### Goal

Ensure the visible canvas is initialized from the authoritative room document,
survives save/reload/reconnect/restart, remains shared between authorized
participants, and presents one coherent status without duplicate or misleading
messages.

### Acceptance criteria

- [ ] The live workspace always shows a bounded, visibly usable canvas after authorization; an empty, malformed, unsupported, or oversized document produces a recoverable inline error while session controls remain usable.
- [ ] The initial persisted document is converted to visible editor elements, and save, refresh, reconnect, canvas-sync restart, and Reload restore the latest accepted document rather than a blank surface.
- [ ] Two authorized participants receive the same initial document and subsequent accepted edits; cross-session, stale-revision, unauthorized, and oversized updates are rejected without replacing the authoritative document.
- [ ] The host and editor expose one consolidated status area covering connecting, connected, edited, saving, saved, conflict/reloaded, disconnected/retrying, and error states; duplicate “Edited/Loaded” strips and raw XML/token diagnostics are absent.
- [ ] The iframe, toolbar, status area, document viewport, and scroll behavior remain bounded and usable at representative phone, tablet, and desktop dimensions.
- [ ] Backend/canvas-sync tests cover revision conflict, restart restoration, room cleanup, authorization, size limits, and token-safe diagnostics; browser tests cover visible render, edit/save/reload, reconnect/degraded state, and multi-client convergence.
- [ ] Documentation identifies the authoritative persistence owner, conflict policy, restart behavior, status vocabulary, and known compatibility limitations.

### Out of scope

- Direct editor tool and manipulation behavior is task 51 / issue https://github.com/cfornesa/ai-dev-tools-zoomcamp/issues/72.
- Root Compose startup is task 48 / issue https://github.com/cfornesa/ai-dev-tools-zoomcamp/issues/69.
- Application-wide navigation/control styling is task 50 / issue https://github.com/cfornesa/ai-dev-tools-zoomcamp/issues/71.

### Constraints

- Keep FastAPI/canvas-sync authoritative for session access and room state; do not move lifecycle or invitation data into the editor.
- Preserve the existing XML transport contract, room identifiers, revision checks, and bounded persistence.
- Do not introduce shared code editing, code execution, or a new database dependency.
