# Canvas E2E contract drift

## Description

The disposable canvas POC browser tests still encode the pre-PR toolbar contract (`Select` and `Move`) and incomplete synthetic pointer events. The editor now intentionally exposes one `Select / Move` interaction and uses pointer capture, so stale tests report missing shapes even when the failure is in the harness.

## Evidence

PR #85 CI failed in `02_interviews/frontend/e2e/canvas-poc.spec.ts` while looking for a rectangle and persisted connector. The same test requests the removed `Move` button. The failure is tracked in GitHub issue #87.

## Next action

Update the POC test to use the current accessible labels and realistic pointer sequences, then run the disposable POC E2E command in CI.

## Links

- Issue: https://github.com/cfornesa/ai-dev-tools-zoomcamp/issues/87
- PR: https://github.com/cfornesa/ai-dev-tools-zoomcamp/pull/85
