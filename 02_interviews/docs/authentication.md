# Authentication and account security model

## Decisions

- Public signup is disabled for the MVP. Administrator access is provisioned
  by an approved operator; the current local development admin remains an
  environment-seeded compatibility path only.
- Candidates never create accounts. They enter through a signed, short-lived,
  single-session invite and receive only a session-scoped candidate credential.
- Google Identity Services is the approved administrator sign-in direction.
  The browser may provide a Google ID token, but the backend must verify its
  signature, issuer, audience, expiry, and stable `sub` before using identity
  data. Email or client-supplied profile fields are never proof of identity.
- A verified Google `sub` is the external identity key. Email-only linking is
  forbidden. Adding another provider requires an authenticated account and an
  explicit linking action.
- Application sessions are server-managed, revocable, short-lived, rotated on
  sensitive transitions, and protected with secure, HttpOnly, SameSite cookies
  plus CSRF protection. The existing bearer-token development adapter must be
  retired or explicitly isolated before production rollout.
- The current environment-seeded development administrator is migrated lazily
  into the same application-user/session tables on its first successful login;
  its bearer response remains a compatibility adapter while clients move to
  the HttpOnly session cookie.
- Roles are `admin`/evaluator and `candidate`. Candidates remain denied from
  administration, audit data, and evaluation data even when they know another
  session identifier.

## Provider flow and redirect policy

The MVP selects the Google Identity Services credential/ID-token flow rather
than an OAuth authorization-code redirect. The browser sends the short-lived
credential directly to the backend over HTTPS; the backend validates issuer,
audience, signature, expiry, and `sub`. This keeps provider codes and client
secrets out of the browser application and avoids an application callback URL.
Production configuration must still allowlist the exact frontend origins in
Google and in backend CORS/CSP settings. No request parameter is used as a
post-login redirect; the frontend navigates only to the fixed `/admin` route.
Cookie-authenticated state changes require the separate CSRF token described
above.

## Risk and recovery policy

reCAPTCHA v3 is an abuse signal, not an authentication mechanism. Actions are
`signup`, `login`, and `invite_redeem`. The backend verifies the token, expected
action, configured hostname, freshness, and duplicate-use status. Thresholds
are environment configuration with three bands: allow, rate-limit/step-up,
and deny. Provider outage, quota failure, privacy blocking, or malformed input
must produce a generic retry/step-up result in production; local and CI use a
deterministic mock explicitly marked as non-production.

Google and reCAPTCHA configuration is environment-specific: client IDs/site
keys, secrets, allowed origins/redirects/hostnames, score bands, and key
rotation metadata are never committed. Consent, provider disclosure, CSP, and
data-retention requirements must be reviewed before enabling real providers.

## Threat model

The backend is authoritative for identity, role assignment, account linking,
session revocation, invite scope, and risk decisions. Threats include
credential stuffing, automated signup, forged client profiles, replayed Google
ID tokens, replayed reCAPTCHA tokens, account takeover by email, invite leakage,
cross-session identifier substitution, CSRF, open redirects, origin confusion,
rate-limit evasion, provider outage, and sensitive logging. Logs and errors
must not contain provider credentials, invite tokens, passwords, reCAPTCHA
tokens, private evaluation text, or secret configuration.

## Rollout boundary

Issues 56–59 may add the durable identity/session and provider verification
foundation. They must preserve the invite candidate path and maintain a
deterministic provider-double mode for tests. No real provider is required for
local startup or CI; a separate manual smoke test is required for production
credentials.

## Manual real-provider smoke test

For a non-production staging deployment only:

1. Set `GOOGLE_PROVIDER_MODE=real`, a Google client ID, a backend verification
   key/JWKS strategy, configured frontend origin, and approved hosted domains.
2. Set `RECAPTCHA_MODE=real`, a server-only `RECAPTCHA_SECRET`, allowed
   hostnames, and reviewed score bands. Never put either secret in Vite
   variables or browser logs.
3. Confirm the Google console origin/redirect allowlist and reCAPTCHA site-key
   domains match the deployment exactly. Verify CSP permits only the configured
   provider origins.
4. Exercise successful login, wrong-domain denial, expired/invalid provider
   credential, low-risk step-up, provider outage, logout, session revocation,
   and candidate invite redemption. Inspect logs to confirm that no raw
   provider credential, reCAPTCHA token, invite token, or private evaluation
   text is present.

Signup remains disabled during this smoke test; there is no public account
creation flow to expose.
