# Responsive UI conventions

The frontend uses a fluid shell and cards, a 640px phone breakpoint, and a
minimum 44px interactive control height. The type scale is `2rem` for page
titles, `1.25rem` for section headings, `1rem` for body text, and `.875rem`
for supporting metadata. Session detail uses a compact title on phones and a
maximum `2.4rem` title on larger screens. Focus indicators use a visible amber
outline and are available for keyboard users.

Cards use 1rem–2rem responsive padding, sections are separated by 1rem–2rem
of space, and action groups use flex wrapping with at least .75rem gaps. Primary
actions come first, secondary navigation follows, and destructive actions are
visually separated and labeled. Disabled/loading controls retain their layout
and expose a disabled state rather than disappearing.

The live canvas fills the remaining workspace height with a 260px minimum on
phones, uses dynamic viewport units, and never exceeds its card width.

The document viewport uses `viewport-fit=cover`; shell padding and the live canvas account for iOS safe-area insets. Canvas pointer handling is isolated to the iframe so touch, mouse, and stylus gestures do not scroll or activate controls in the parent page. Reduced-motion users receive no animated transitions. Virtual keyboards and rotation are handled by the browser through fluid sizing; the canvas remains usable in portrait and landscape, with the toolbar available through the editor viewport.

## Control taxonomy

Links are used for navigation and receive the `.button` treatment so their
destination remains available to keyboard and screen-reader users. Native
buttons are reserved for mutations and local editor commands. Primary actions
use the default blue style, secondary navigation uses `.secondary`, and
irreversible or lifecycle-destructive actions use `.destructive`. Controls are
grouped with a minimum `.75rem` gap, retain a 44px minimum target, expose
loading/disabled state, and keep focus indicators independent of hover.

Verify responsive behavior with `make test-frontend`, `make build-frontend`, and `make e2e`. The supported manual matrix is iOS Safari, iPadOS Safari, Android Chrome, Android tablet Chrome, and current desktop Chromium, Firefox, and WebKit. Small screens use a stacked header and controls; drawing remains available in portrait and landscape orientations. The repository has no additional UI design-system or testing-guidance file, so these conventions and the Playwright viewport checks are the project-local fallback.
