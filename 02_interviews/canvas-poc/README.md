# Self-hosted canvas proof of concept

This dependency-free local editor validates the host/iframe boundary used by the
self-hosted canvas path. It has no npm/runtime dependencies and is served by the
Compose `canvas-editor` service, so the application does not depend on a hosted
editor origin.

Run it from `02_interviews/`:

```bash
python3 canvas-poc/server.py
```

Open <http://127.0.0.1:8090/editor.html>. The editor exchanges load/save
messages through the exact parent origin; in the application path, XML is
persisted by the canvas-sync room. Use its toolbar to exercise freehand strokes,
text, rectangles, connectors, selection, deletion, undo/redo, zoom/pan, and XML
serialization.

Pointer input policy: mouse, touch, and stylus use the same Pointer Events path;
the canvas captures a gesture until pointer-up or pointer-cancel. Freehand
samples are recorded at least 2 SVG units apart and capped at 512 points per
stroke. Coordinates are clamped to the 1000×600 document, and XML is rejected
by the sync service above 2 MB (the editor rejects documents above 500 KB).
Empty selection clears the selection, cancelled gestures are discarded, and
the canvas uses `touch-action: none` so gestures do not scroll the interview
page.

The editor page is a compact draw.io-compatible XML editor implementation. The
source/version, protocol evidence, notices, and known limitations are in
`../docs/canvas-replacement.md`.
