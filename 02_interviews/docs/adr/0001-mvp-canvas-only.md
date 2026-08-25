# ADR 0001: Canvas-only MVP

Status: accepted

The MVP ships one collaborative self-hosted XML canvas per interview session. Shared code editing and code execution are deferred. If execution is added later, it must run in an isolated runner; it must not run inside the API or canvas-sync process. Canvas room identifiers use opaque session identifiers, while invitations, lifecycle, authorization, and evaluation remain backend-owned. Canvas sync must require a backend-issued short-lived credential and never treat an arbitrary room name as authorization.
