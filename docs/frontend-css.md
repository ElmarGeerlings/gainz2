# Frontend CSS — conventions

This doc is the detailed styling policy for gainz2. **`AGENTS.md` §6 stays short**; agents and humans should follow this file when adding or moving CSS.

## File layout

- **`static/css/base.css`** — design tokens, resets, reusable **components** (e.g. `.panel`, `.btn`), and **generic utilities** (e.g. spacing, typography) used across the app.
- **`static/css/<area>.css`** (e.g. `workouts.css`) — loaded only on relevant templates via `extra_css`. Use for **page- or feature-specific** rules that should not affect other screens.

Every page should load `base.css` (via `base.html`). Area CSS is optional.

## Single source of truth

- **Tokens** (colors, spacing scale, radius, shadows) live in `:root` in `base.css` only.
- **Do not duplicate** the same utility or component in `base.css` and an area file.

## What belongs in `base.css`

Put rules here when any of these apply:

1. **Global** — resets, `html`/`body`, links, box-sizing.
2. **Tokens** — CSS variables in `:root`.
3. **Reusable components** — buttons, panels, tables, form controls, carousel chrome, etc.
4. **Generic utilities** you expect on **multiple** screens — e.g. `mb-3`, `text-muted`, `fw-700`, `opacity-70`.

## What belongs in area CSS (`workouts.css`, etc.)

Use area CSS only for:

1. **Layout glue** unique to that screen (e.g. a fixed min-height so a carousel does not jump between slides).
2. **Domain-specific** presentation that should not leak globally (prefer a clear name, e.g. `.workout-*` or `.set-row--completed`, if you introduce it).
3. **Short-lived** experiments — promote to `base.css` once a second page needs the same thing.

If a rule encodes a **magic number** or behavior only one page needs, area CSS is appropriate.

## Promotion rule

- **First use** on one page: utilities in the template or a small area rule is fine.
- **Second use** on another page or feature: **promote** to `base.css` (as a component or utility).
- **Do not** copy the same block into a second area file.

## Naming

- **Utilities:** short and predictable (`mt-4`, `mb-3`, `p-3`, `text-sm`, `fw-700`).
- **Components:** noun-based (`panel`, `btn-primary`, `table-shell`).
- **Page/domain:** use a prefix when not meant to be global (`workout-card-track`, etc.) so it is obvious.

## Templates

- Prefer **composing** existing utilities and components in HTML.
- Add a **new CSS rule** only when the same combination appears repeatedly or the markup becomes unreadable.

## Mobile-first

- Default styles target a **narrow viewport**; add `min-width` media queries when larger screens need more space — not the other way around.
- Touch targets and spacing for logging flows should stay comfortable on phones (see `AGENTS.md` §1).

## Checklist (before merging CSS changes)

1. No duplicate class definitions across `base.css` and area files.
2. New utilities/components in `base.css` are **generic** enough for reuse, or stay in area CSS with a clear name.
3. Area CSS is loaded only where needed (`extra_css`).
4. No inline styles for layout/theme (prefer classes).
5. Tokens referenced via `var(--...)` instead of hard-coding the same color/spacing in many places.
