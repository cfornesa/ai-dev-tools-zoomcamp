# MVP implementation decisions

The scorecard uses a required integer rating scale from 1 (does not meet expectations) to 5 (exceptional). Default categories are problem solving, technical fundamentals, communication, and collaboration. Recommendations are `hire`, `no-hire`, `strong-hire`, or `strong-no-hire`. Notes are evaluator-private.

The UI uses a small accessible system: native form controls, visible labels, keyboard-usable buttons and links, high-contrast text, and explicit success/error/status messages. Canvas availability never changes backend-owned lifecycle state.
