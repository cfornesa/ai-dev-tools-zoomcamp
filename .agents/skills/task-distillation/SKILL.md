---
name: task-distillation
description: Discover, deduplicate, groom, and reconcile all actionable backlog work and its memory topics for one project.
---

# Task distillation

Use this skill to turn a user request, review feedback, failures, or readiness findings into a reconciled project backlog. It is batch-aware and idempotent: do not create duplicate GitHub issues or memory topics when an existing record already covers the work.

## Discovery and reconciliation

1. Identify exactly one project and read its `tasks.md`, relevant plan, `_docs/process.md`, and applicable acceptance criteria and constraints.
2. Inspect the current worktree and relevant repository history without overwriting user changes.
3. Use the authenticated GitHub connector to enumerate open issues associated with the project. Compare GitHub issues, `tasks.md`, existing memory topics, related PRs, and the user's evidence.
4. Build or update an issue manifest containing issue number, URL, goal, dependencies, priority/order, duplicate links, scope, and status.
5. Order work by dependencies, then backlog order, then priority. Mark already-completed, duplicate, blocked, and dependency-blocked items explicitly.

## Distillation loop

For each gap:

1. State the current behavior, desired behavior, evidence, and verification boundary.
2. Identify actionable implementation items, decisions, blockers, lessons, constraints, and context.
3. Reuse or update an existing GitHub issue when it covers the item. Create a new issue only when the work is genuinely absent and the user authorized issue creation.
4. Give each issue a clear goal, checkable acceptance criteria, constraints, out-of-scope links, dependencies, and exact next action.
5. Create or update memory topics only for durable decisions, blockers, verification boundaries, lessons, constraints, actionable context, or other information needed by a later session. Link each topic to its issue(s).
6. Reconcile issue status, backlog entry, memory topic, PR/commit evidence, and next action before moving on.

## Required outputs

Produce:

- a complete project issue manifest;
- a duplicate and already-covered-work report;
- one criterion-ready issue definition for each actionable item;
- linked memory topics for durable context;
- a dependency/order rationale;
- an explicit list of unresolved blockers and verification boundaries.

No actionable item may be left only in prose. No issue or memory topic may be created twice because a prior session already captured it. If external tooling is unavailable, record the attempted tool, exact failure, impact, and next action.

## Exit criteria

Exit only when every discovered gap is one of:

- linked to an existing or newly authorized issue;
- explicitly classified as duplicate or already covered;
- documented as blocked with an exact next action; or
- documented as non-actionable with a reason.

Return the manifest to the caller so backlog-session can process every remaining open issue sequentially.
