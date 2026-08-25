# Canvas replacement discovery

## Scope and result

Issue 51 validated whether a self-hosted draw.io-compatible editor can replace
the previous canvas without introducing a hosted editor dependency. The local
editor is in `canvas-poc/`; run it with `python3 canvas-poc/server.py` and open
`http://127.0.0.1:8090/editor.html`, or use the Compose `canvas-editor` service.

The editor proves the security-sensitive integration boundary: a local
iframe, exact `postMessage` origin and source checks, explicit `init`/`load`,
`saved`, `state`, and `error` messages, and XML snapshots held by the host. Its
editor exercises freehand, text, rectangle, connector, selection, keyboard
delete, undo/redo, zoom, pan controls, and XML serialization. Ctrl+wheel is
handled inside the canvas viewport and does not scroll the host page.

The selected implementation is the repository's dependency-free
`canvas-poc/editor.html` compatibility editor, version `0.1.0` (the same
source is served by the Compose `canvas-editor` service). It is intentionally
not a vendored upstream draw.io distribution. The upstream `jgraph/drawio`
`dev` source is the feature and licensing reference only; no upstream commit
was bundled, so there is no third-party JavaScript dependency inventory to
ship. If the implementation changes to vendored upstream assets, pin the
commit and regenerate notices before distribution.

The replacement path reports connecting, connected, saving, saved, reconnecting,
disconnected, conflict/reload, and ended states. The supported viewport is a
responsive 1000×600 canvas inside the live-session card; smaller screens scroll
the host card rather than the editor document. Diagnostics contain only status,
revision, and bounded XML length—never tokens or XML contents.

When embedded in the live workspace, the parent owns the single visible status
area; the iframe hides its local status strip while continuing to send bounded
state events to the parent. The standalone POC host keeps the local strip for
protocol inspection.

## Upstream and licensing findings

- Upstream source: [jgraph/drawio](https://github.com/jgraph/drawio), `dev`
  branch; the repository README identifies the source as Apache License 2.0.
- The upstream README says icon sets, stencils, and templates have additional
  terms, including a restriction on Atlassian products/marketplaces. It also
  says the draw.io/diagrams.net names and logos are trademarks and must not be
  used to imply endorsement.
- The source includes third-party JavaScript libraries. Before production use,
  the selected commit's dependency/license inventory must be captured in a
  generated NOTICE file and reviewed for compatibility.
- The upstream README documents GitHub Pages/self-hosting as a way to run the
  editor without relying on `embed.diagrams.net`; the hosted origin is not used
  by this project.

## Decision

**Go for the dependency-free self-hosted replacement path.** The application
ships the local XML editor and its room protocol rather than loading
`embed.diagrams.net`. This intentionally avoids a large bundled upstream
runtime; the supported feature set and limitations are recorded below.

## Implementation gates for the next issues

1. Preserve the exact local-origin/source checks from the editor and validate a
   small allowlist of message types; never accept arbitrary frame commands.
2. Keep XML document state and authorization in the existing session service;
   do not couple it to editor-specific data structures.

## Canonical document model

The editor renders a small canonical SVG-backed model serialized as:
`<canvas version="1"><shape type="rect|text|freehand|connector" ... /></canvas>`.
Incoming `mxfile/mxGraphModel` documents are converted at the editor boundary;
raw `mxCell` nodes are never inserted into the SVG. Vertex geometry becomes a
rectangle or text shape, edge geometry becomes a connector, and unsupported
styles are reduced to the supported shape properties. Empty, malformed, or
oversized documents produce a recoverable error. This deliberately preserves
the room's XML transport contract while documenting that arbitrary draw.io
stencils, rich HTML labels, and unsupported style attributes are not losslessly
round-tripped.

## Interaction model

The compatibility editor groups tools into canvas, edit, viewport, and
persistence controls. Select shows a visible selection box; Move drags the
selected element, Delete and the Delete/Backspace keys remove it, and double
clicking text opens a browser edit prompt. Hand/Pan drags the bounded
viewport, while Zoom controls, Ctrl+wheel, and Reset/Fit change the document
view without scrolling the interview page. Every tool exposes an accessible
name, title, and active state. The editor remains intentionally smaller than
upstream draw.io: resizing handles, arbitrary stencil libraries, rich text,
and lossless style round-tripping are not supported.
