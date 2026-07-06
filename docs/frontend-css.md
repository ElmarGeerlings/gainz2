# Frontend CSS — conventions

This doc is the detailed styling policy for gainz2. **`AGENTS.md` §6 stays short**; agents and humans should follow this file when adding or moving CSS.

## File layout

- **`static/css/base.css`** — design tokens, resets, reusable **components** (e.g. `.panel`, `.btn`), and **generic utilities** (e.g. spacing, typography) used across the app.
- **`static/css/<area>.css`** (e.g. `workouts.css`) — loaded only on relevant templates via `extra_css`. Use for **page- or feature-specific** rules that should not affect other screens.

Every page should load `base.css` (via `base.html`). Area CSS is optional.

## Styleguide (`/design/`)

- **URL:** `/design/` (requires login).
- **Purpose:** The **only** visual reference needed to design a new feature (lists, auth, programs, etc.). Shows core tokens and components from `base.css`.
- **Rule:** Compose new UI from what appears on the styleguide. If a core class or token is missing, add it to `base.css` and the styleguide first.
- **Not on the styleguide:** Page-specific UI (workout set table columns, carousel, feedback toggles, inline-edit, etc.). Those live in scoped area CSS and feature templates.
- **`styleguide.css`** is layout-only for the styleguide page; not part of the reusable system.

## Area CSS (scoped overrides)

Page-specific CSS must **extend** core components, not replace them globally.

- Use a **scoped class** on the feature markup (e.g. `workout-sets-table` on the sets table).
- **Do not** target bare `.table`, `.btn`, or `.table-compact` for layout that only one page needs.
- Example: column widths and cell triggers for workout sets are under `.workout-sets-table` in `workouts.css`, not under `.table-compact` globally.

Promote a pattern to `base.css` (and the styleguide) when a **second** feature needs the same thing.

## Core components

Markup below is the contract; see `/design/` for live examples.

### Page shell

- **Use when:** Any full-screen view.
- **Classes:** `page`, `page-narrow` (centered max width on main).

```html
<main class="page page-narrow">…</main>
```

### Panel

- **Use when:** Grouped content, cards, form sections.
- **Classes:** `panel`, optional `surface-soft`, `stack-sm` / `stack-md` for vertical spacing inside.

```html
<section class="panel stack-sm">…</section>
```

### Typography

- **Use when:** Titles and body copy.
- **Classes:** `title-lg`, `title-md`, `title-sm`, `text-sm`, `text-muted`, `fw-700`.

### Layout utilities

- **Use when:** Spacing and alignment without new CSS.
- **Classes:** `stack-xs` … `stack-lg`, `gap-sm`, `gap-md`, `row-between`, `row-center`, `grid-3`, `mt-*`, `mb-*`, `p-*`, `m-0`, `text-center`, `w-100`.

### Button

- **Use when:** Actions, submits, icon dismiss.
- **Base:** `btn`
- **Variants:** `btn-primary`, `btn-outline`, `btn-success`, `btn-warning`, `btn-danger`, `btn-danger-outline`, `icon-btn`, `link-btn`
- **State:** `disabled` attribute on `<button>`

```html
<button type="button" class="btn btn-primary w-100">Save</button>
```

### Form

- **Use when:** Label + input stacks (no Django Forms).
- **Classes:** `form-stack`, `form-control` on inputs/textareas; `label` wraps text in `form-stack label` styling via child `label` elements.

```html
<div class="form-stack">
  <label for="field-id">Label</label>
  <input id="field-id" type="text" class="form-control">
</div>
```

### Table

- **Use when:** Tabular data.
- **Structure:** `table-shell` > `table`
- **Dense variant:** add `table-compact` (smaller font only in `base.css`; no column overrides in core)

```html
<div class="table-shell">
  <table class="table">
    <thead><tr><th>…</th></tr></thead>
    <tbody><tr><td>…</td></tr></tbody>
  </table>
</div>
```

### Modal

- **Use when:** Focused overlay content; visibility toggled in JS.
- **Classes:** `gainz-modal`, `gainz-modal-content`, `gainz-modal-close`

### Set modal + value picker

- **Use when:** Set edit/add modals and progression step modals with scroll-wheel weight/reps pickers.
- **Classes:** `set-modal-fields-row`, `set-modal-times`, `set-modal-actions`, `value-picker`, `value-picker-window`, `value-picker-list`, `value-picker-item`, `is-center` / `is-near` on items.

```html
<div class="set-modal-fields-row">
  <div class="value-picker" data-picker="weight">…</div>
  <span class="set-modal-times">X</span>
  <div class="value-picker" data-picker="reps">…</div>
</div>
<div class="set-modal-actions">
  <button type="button" class="btn btn-primary">Confirm</button>
</div>
```

### Exercise type badge

- **Use when:** Showing primary / secondary / accessory on exercises.
- **Classes:** `exercise-type-badge`, `exercise-type-badge--primary` | `--secondary` | `--accessory`
- **Partial:** `{% include "components/exercise_type_badge.html" with exercise_type=… %}`

### Dropdown

- **Use when:** Custom select menus (exercise type, start routine).
- **Classes:** `gainz-dropdown`, `gainz-dropdown-full`, `gainz-dropdown-menu`, `gainz-dropdown-item`, `gainz-dropdown-divider`, `gainz-dropdown-empty`
- **JS:** `toggleGainzDropdown` on trigger button.

### Toggle switch

- **Use when:** Boolean settings (program carryover, etc.).
- **Classes:** `gainz-toggle-switch`, `gainz-toggle-input`, `gainz-toggle-slider`

```html
<label class="gainz-toggle-switch">
  <input type="checkbox" class="gainz-toggle-input">
  <span class="gainz-toggle-slider" aria-hidden="true"></span>
</label>
```

### Toast

- **Use when:** Success, warning, or danger feedback.
- **Classes:** `gainz-toast`, `gainz-toast-success` | `gainz-toast-warning` | `gainz-toast-danger`, `gainz-toast-message`, `gainz-toast-close`, optional `gainz-toast-actions`
- **Container:** `.toast-container` in `base.html` for live toasts.

## Single source of truth

- **Tokens** (colors, spacing scale, radius, shadows) live in `:root` in `base.css` only.
- **Do not duplicate** the same utility or component in `base.css` and an area file.

## What belongs in `base.css`

1. **Global** — resets, `html`/`body`, links, box-sizing.
2. **Tokens** — CSS variables in `:root`.
3. **Reusable components** — buttons, panels, tables, form controls, modals, toasts, exercise type badges, dropdowns, toggle switches, set-modal fields and value pickers.
4. **Generic utilities** used on **multiple** screens — e.g. `mb-3`, `text-muted`, `fw-700`.

## What belongs in area CSS (`workouts.css`, etc.)

1. **Layout glue** unique to that screen.
2. **Scoped overrides** on core components (prefixed or wrapper class).
3. **Domain-only** presentation until promoted (e.g. carousel chrome on workout detail only).

## Promotion rule

- **First use** on one page: scoped area CSS is fine.
- **Second use** on another page: **promote** to `base.css` and add to `/design/`.
- **Do not** copy the same block into a second area file.

## Naming

- **Utilities:** short and predictable (`mt-4`, `mb-3`, `p-3`, `text-sm`, `fw-700`).
- **Components:** noun-based (`panel`, `btn-primary`, `table-shell`).
- **Page/domain:** scoped names (`workout-sets-table`, `workout-*`) so globals are not overridden.

## Templates

- Prefer **composing** existing utilities and components in HTML.
- Add a **new CSS rule** only when the same combination appears repeatedly or the markup becomes unreadable.

### Blank lines

- **No blank lines** between HTML siblings (`<section>`, `<label>`, `<input>`, nav items, etc.) — use CSS utilities (`stack-sm`, `mb-*`, …) for spacing.
- **Blank lines only** between Django template blocks: one line before each `{% block … %}` (after `{% extends %}`, `{% load … %}`, or `{% endblock %}`).
- **Partials and includes** stay compact (no blank lines unless they define their own `{% block %}` sections).

## Mobile-first

- Default styles target a **narrow viewport**; add `min-width` media queries when larger screens need more space — not the other way around.
- Touch targets and spacing for logging flows should stay comfortable on phones (see `AGENTS.md` §1).

## Checklist (before merging CSS changes)

1. No duplicate class definitions across `base.css` and area files.
2. New core utilities/components are on `/design/` and generic enough for reuse.
3. Area CSS is scoped and loaded only where needed (`extra_css`).
4. No inline styles for layout/theme (prefer classes).
5. Tokens referenced via `var(--...)` instead of repeating hex.
