# Canvas Circle narrow-layout regression

## Description

Circle creation was not reliable in the narrow-layout browser flow. The CI test completed the drag but observed no `ellipse[data-tool="circle"]` after Rectangle and Square had already been created.

## Evidence

PR #85 CI failed at `02_interviews/frontend/e2e/canvas-editor.spec.ts:93` with expected ellipse count 1 and received 0. The failure is tracked in GitHub issue #86.

The cause was that the pointer-down handler returned whenever the pointer started over an existing SVG shape, even for drawing tools. Commit `b54e019` permits drawing tools to start on existing shapes and adds a reverse-drag regression test.

## Next action

Verify the focused Circle regression and full E2E suite on the next Linux CI run; local unit/build checks pass, but the sandbox cannot launch Chromium reliably.

## Links

- Issue: https://github.com/cfornesa/ai-dev-tools-zoomcamp/issues/86
- PR: https://github.com/cfornesa/ai-dev-tools-zoomcamp/pull/85
