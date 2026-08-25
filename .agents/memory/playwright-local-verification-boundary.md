# Playwright local verification boundary

## Description

The local macOS sandbox cannot reliably launch the repository's Playwright Chromium binary. This is a verification boundary, not evidence that the application tests pass locally.

## Evidence

The disposable POC command reached Playwright, but Chromium exited with `mach_port_rendezvous ... Permission denied (1100)` and the workers then reported browser contexts closing. The PR's Linux CI output is the authoritative evidence for the two application/test failures: issues #86 and #87.

## Next action

Use CI or an approved environment with Chromium process permissions to validate the focused Circle regression and updated POC tests. Do not mark either issue complete from local unit/build results alone.

## Links

- Issue #86: https://github.com/cfornesa/ai-dev-tools-zoomcamp/issues/86
- Issue #87: https://github.com/cfornesa/ai-dev-tools-zoomcamp/issues/87
