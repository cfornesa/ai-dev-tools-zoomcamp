- Tasks are GitHub issues, one at a time
- Read the acceptance criteria before starting and before closing
- Commit regularly

Roles

- PM - grooms a task before anyone implements it, follows _docs/team/pm.md
- Engineer - implements one groomed task, follows _docs/team/software-engineer.md
- QA - checks the result against the acceptance criteria, follows _docs/team/qa-engineer.md

GitHub issue workflow

- Every new backlog task must be added to the relevant project's `tasks.md` and
  created as a GitHub issue before implementation begins.
- Use the authenticated GitHub connector (`github_create_issue` and related
  GitHub tools) for issue operations. Do not rely on the local `gh` CLI token;
  it may be invalid even when the user's connected GitHub credentials work.
- Record the resulting issue URL in the backlog entry so the task and issue can
  be cross-checked.
