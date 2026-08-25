# Self-hosted canvas attribution and notices

The shipped `canvas-poc/` editor is a dependency-free local XML editor and does
not vendor or load code from `embed.diagrams.net`, Google, or another hosted
canvas origin. Its runtime dependencies are the Python standard library in the
static server and browser platform APIs; there are no newly bundled JavaScript
editor dependencies.

The feature and XML conventions were evaluated against the upstream
[jgraph/drawio project](https://github.com/jgraph/drawio), whose authored source
is published under Apache License 2.0. No upstream draw.io source files, icon
sets, stencil libraries, templates, logos, or trademarks are included in this
repository. If upstream assets are added later, their Apache/third-party
notices and the additional icon/template terms must be copied here before
distribution.

The project must not present the `draw.io` or `diagrams.net` marks or logos as
an affiliation or endorsement. The local feature is therefore described in UI
and configuration as the self-hosted canvas editor.
