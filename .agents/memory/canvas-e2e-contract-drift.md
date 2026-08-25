# Canvas E2E contract drift

## Description

The disposable canvas POC browser tests encoded the pre-PR toolbar contract (`Select` and `Move`) and incomplete synthetic pointer events. The editor now intentionally exposes one `Select / Move` interaction and uses pointer capture, so stale tests reported missing shapes even when the failure was in the harness.

## Evidence

PR #85 CI failed in `02_interviews/frontend/e2e/canvas-poc.spec.ts` while looking for a rectangle and persisted connector. The same test requests the removed `Move` button. The failure is tracked in GitHub issue #87.

Commit `b54e019` updates the toolbar assertions and uses real page mouse drags. Commit `415ca39` hardens persisted mxGraph conversion by iterating direct `mxCell` children, covering the previously missing connector.

## Next action

The updated POC contract and pointer sequence now reach a distinct deletion failure tracked in issue #88: after the real drag and Save XML, Delete leaves one `svg rect`. Trace selection persistence through the captured gesture, then verify issue #88 and the full Linux E2E suite. Local unit/build checks pass, but the sandbox cannot launch Chromium reliably.

The 2026-08-25 Linux rerun initially failed both POC acceptance paths: the moved rectangle had no `svg rect.selected` after the real drag, and the persisted mxGraph fixture had no `svg line` connector. The full suite reported 9 passed and 2 failed. These were recorded on issues #88 and #87 respectively; the PR remains open.

The follow-up implementation fixed both contract gaps. `host.html` now preserves raw XML snapshots in localStorage instead of silently replacing them with the default document. `editor.html` now maps the responsive SVG viewport directly to its viewBox, so bounding-box pointer coordinates remain drawable, and only SVG-owned shapes can enter select/move state. The focused POC browser suite passes 2/2 in an approved Chromium environment; frontend unit tests pass 30/30 and the production build passes.

## Links

- Issue: https://github.com/cfornesa/ai-dev-tools-zoomcamp/issues/87
- Issue #88: https://github.com/cfornesa/ai-dev-tools-zoomcamp/issues/88
- PR: https://github.com/cfornesa/ai-dev-tools-zoomcamp/pull/85

## Next action after rerun

Run the focused and full Linux E2E suites against the PR branch, then update issues #87 and #88 and close them if CI confirms the same passing behavior. The local approved run does not replace PR CI as the final Linux verification boundary.
