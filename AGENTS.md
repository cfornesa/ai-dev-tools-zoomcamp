Commands

- `uv sync` - install dependencies
- `uv run pytest` - the whole suite
- `uv run pytest tests/test_home.py` - one test file

Rules

- This repo has multiple projects, with each respective plan situated in the home folder of each project, subject to change.
- If unspecified, ask about which project to conduct work. 
- You are not permitted to do work in multiple projects unless explicitly specified by the user.
- If existing GitHub issues are present for a specific folder's project, ensure that all issues for a single project are resolved before starting on or working on a different project's issues to avoid cross-contamination.
- Only task creation and allocation for different projects are allowed when existing GitHub issues are present and defined.
- All projects must be able to run within their respective main folders.
- No single command should run every single project all at once.
- Dependencies are added in `pyproject.toml` per project. Do not add one without asking the user.

Documents

- `_docs/process.md` - how work is organized
- Before writing tests, read `_docs/testing-guidelines.md`
- For anything touching the UI, read `_docs/design-system.md`