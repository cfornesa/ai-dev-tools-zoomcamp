---
name: backlog-session
description: Process every remaining open backlog issue for one project sequentially, with explicit PM, engineering, QA, reconciliation, evidence, and handoff gates.
---

# Backlog session

Use this skill when the user asks to work through a project backlog and its GitHub issues. A session is a complete run for one project: discover every remaining open backlog issue, process issues one at a time in dependency order, and leave every issue with a terminal status. Never claim the project batch is complete when a required gate was skipped.

## Scope and invariants

- Work in exactly one project per session. If the project is unclear, ask before changing files.
- At session start, discover and reconcile every open GitHub issue associated with that project against its `tasks.md`. Do not silently omit, duplicate, or invent an issue.
- Process issues sequentially, never in parallel. A blocker on one issue does not stop independent issues; dependency-blocked issues receive a documented handoff and are not implemented prematurely.
- Build an issue manifest before implementation. Every manifest item must end as `completed`, `blocked`, `dependency-blocked`, or `handed-off`.
- Inspect `git status --short --branch` before editing. Classify pre-existing changes as unrelated, user-owned relevant work, or session work. Preserve unrelated and user-owned changes; do not commit them without clear authorization.
- Do not add dependencies without the user's approval.
- Use the authenticated GitHub connector for issue, comment, and PR operations. Do not use a local `gh` token as a substitute.
- Read acceptance criteria before implementation and again during QA.

## Batch manifest

Record this manifest in the working notes and final handoff:

| Issue | URL | Backlog entry | Dependencies | Scope | Status | Next action |
| --- | --- | --- | --- | --- | --- | --- |

Order by explicit dependencies, then project backlog order, then priority. If GitHub and `tasks.md` disagree, reconcile the records before implementation. Existing issues must be updated or reused; create a new issue only for genuinely new work authorized by the user.

## Per-issue loop

Run these passes for every manifest issue, labeling artifacts with the issue number. If delegation is unavailable, perform the passes yourself in sequence and say so; never imply another agent ran.

### PM pass — groom

Read the issue, relevant `tasks.md`, `_docs/process.md`, `_docs/team/pm.md`, and any required project guidance. Confirm or update:

- goal and checkable acceptance criteria;
- constraints, dependencies, files in scope, and out-of-scope follow-ups;
- duplicate/related issue links;
- criterion-by-criterion implementation plan;
- backlog entry and GitHub issue URL.

If the issue is not implementable because a dependency is unresolved, record `dependency-blocked`, its exact prerequisite, and its next action. Continue to the next independent issue.

### Engineer pass — implement

Read `_docs/team/software-engineer.md`. Before writing tests, read `_docs/testing-guidelines.md`; for UI work, also read `_docs/design-system.md` when those files exist. Implement only the current issue, add focused regression coverage, and run its documented checks. Commit coherent issue-scoped changes before advancing. Do not close the issue.

If implementation is blocked, do not modify unrelated code. Record the attempted command or tool, exact failure, impact, and next action, then mark the issue `blocked` or `handed-off` and continue with independent issues.

### QA pass — verify

Read `_docs/team/qa-engineer.md` and the issue acceptance criteria again. Do not modify code during QA. Exercise every criterion against the running result using the exact commands and environment specified by the issue where possible. Run focused tests and the full relevant suite, plus required builds/checks. Separate local, approved-browser, CI, and production evidence.

Post a GitHub comment for the issue beginning with `## QA: PASS` or `## QA: FAIL`, including a criterion matrix, commands, results, environment, and exact next action. A focused test never substitutes for the full relevant suite. A failed issue does not prevent QA of later independent issues.

### Issue handoff

Set the manifest status and reconcile the backlog entry, issue comment, commits, memory links, and next action. An issue is `completed` only when every acceptance criterion and required check passes. Otherwise use `blocked`, `dependency-blocked`, or `handed-off` with evidence.

## Batch completion pass

After the per-issue loop, run [session-completion](../session-completion/SKILL.md) with the complete manifest. It must reconcile all issues, memory topics, decisions, lessons, constraints, blockers, verification boundaries, and the final verification boundary. Run [task-distillation](../task-distillation/SKILL.md) for newly discovered work or context changes, and [production-readiness](../production-readiness/SKILL.md) when its conditions require it.

Do not create a PR while any required issue is incomplete, unverified, or missing a terminal status. A PR may be created or updated only after the batch completion pass confirms that all intended issues pass and no required follow-up remains.

## Required evidence

Include per issue and as a batch rollup:

| Gate | Required evidence |
| --- | --- |
| Scope | Project, complete issue manifest, ordering, worktree classification |
| PM | Grooming result, issue URL, acceptance matrix, plan |
| Engineer | Changed files, focused tests, commits, dependency decisions |
| QA | Exact focused/full commands, environment, results, criterion verdicts, GitHub comment |
| Memory | Updated or explicitly unchanged topics, linked to issues |
| Session completion | Batch reconciliation result and remaining-item audit |
| Handoff | Every issue's status, blocker, owner/context, and exact next action |

The final rollup must state counts for discovered, completed, blocked, dependency-blocked, handed-off, and missing-terminal-status issues. Missing-terminal-status must be zero.

## Completion gate

The project batch may be reported complete only when:

- every discovered issue has a terminal status;
- every issue reported as completed has all acceptance criteria passing;
- full relevant suites and required builds/checks pass for completed issues;
- QA results are recorded on every processed issue;
- changes are committed without unrelated files;
- backlog, GitHub, and memory links are reconciled;
- session completion has run; and
- the issue/PR state reflects the actual batch result.

If any issue is blocked or incomplete, report `INCOMPLETE` or `BLOCKED`, keep the issue open, list the failed gate, and give one concrete next action per issue. Do not imply that blocked work is complete.
