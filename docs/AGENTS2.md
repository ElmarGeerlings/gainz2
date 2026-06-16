# Gainz2 — agent implementation guide

Authoritative guide for agents working in this repo. Supersedes older draft text that referenced `gainz/` or `stolen_js.js` line-by-line without the implemented gainz2 contract.

## 1. Product scope (phase 1)

**In scope**

- Workout **logging** (sessions, exercises, sets, completion, editing flow).
- **Programs** and **routines** (templates, scheduling you need, starting a workout from a routine, and related management).

Scope grows only when the product owner extends it in writing.

**Primary use context — mobile first**

- Most real-world use is **in the gym on a phone**, not at a desktop.
- Design and ship **one** mobile-first UI: layout, density, and interactions optimized for small screens and touch (including WebSocket-driven updates during a session).
- Do **not** maintain parallel desktop vs mobile templates (no alternate HTML trees chosen by cookie, user agent, or “desktop mode”). One template set per screen; use **responsive CSS** only for graceful scaling on larger viewports if needed — the **reference device** is always a phone in hand.

---

## 2. Architectural principles

1. **Operations first**  
   Business behavior lives in plain Python **service** functions in `workouts/services.py` (etc.). **HTTP views** and **WS handlers** parse input, call services, build response dicts / render templates.

2. **Interactive client ↔ server**  
   Mutations and partial updates use **WebSocket** (see §7). **HTTP** handles first paint, auth, health checks, normal GET.

3. **Sync Django**  
   Sync views and sync ORM. **Channels** + `database_sync_to_async` around sync dispatch in `MainConsumer`.

4. **Persistence and responses**  
   Django models + ORM. HTML via templates; WS envelopes via dicts + `render_to_string`.

5. **Python 3.10+** compatible unless the team agrees otherwise.

---

## 3. Repository / Django layout

Project **root** (same directory as **`manage.py`**); **`DJANGO_SETTINGS_MODULE`** is **`settings`**.

```
project_root/
  manage.py
  settings.py
  gainz2/
    asgi.py
    routing.py
    consumers.py
    ws_dispatch.py
    urls.py
    utils.py              
  workouts/
    models.py
    services.py
    ws_handlers.py
    views.py
  exercises/
    models.py
  utils/
    templatetags/
      formatting.py       
  templates/
    base.html
    components/
      toast.html
    workouts/
      workout_detail.html
      set_modal.html
      set_row_cells.html
      exercise_sets_block.html
  static/
    css/
      base.css
      workouts.css
    js/
      app.js              # WS, ws_request, toasts, modals
      workouts.js         # workout detail page handlers
```

**`gainz2/urls.py`** — HTTP routes.  
**`gainz2/routing.py`** — socket URL → `MainConsumer`.  
**`gainz2/ws_dispatch.py`** — **`WS_ENDPOINT_REGISTRY`** (source of truth for message endpoints).  
**`gainz2/consumers.py`** — thin receive/send; no per-feature logic.  
**`workouts/ws_handlers.py`** — workout WS handlers; imported into registry.

**Apps** hold **models**, **migrations**, **admin**, **`services.py`** (operations), **`views.py`** (thin HTTP handlers). Split into extra modules or `views/` / `services/` packages when a file grows too large.

**Agents:** core rules live in **Python services**; views and consumers call services and return responses.

---

## 4. Frontend — templates

- **Django templates** for UI.
- **`base.html`**: layout, blocks (`content`, `extra_css`, `extra_js`), shared chrome — structured for **mobile-first** (see §1).
- **Partials** for fragments returned over the wire for **HTML swaps**.

---

## 5. Frontend — JavaScript

### Declarative attributes

| Attribute | Meaning |
|-----------|--------|
| `data-endpoint="click->workouts/update_set"` | **`ws_request`**: `sendWsRequest` + standard response handling (§7). Use when one WS round-trip and generic morph/reload/toast is enough. |
| `data-function="click->openSetModal"` | **`window[funcName](event)`** — top-level functions in `app.js` or `workouts.js`. |
| `data-routing="workouts/set_edit_modal_form"` | **WS route for a reusable `data-function`**. The function reads `data-routing` and calls `sendWsRequest` with custom client-side handling (e.g. morph into a modal, inline edit save). Same JS, different endpoints from the template — often `{{ endpoint_ns }}/...` for workout vs routine. |
| `data-close-modal="#set-modal"` | On **200**, hide modal (used with `data-endpoint` on Confirm). |
| `data-refresh` | Full page reload on response. |
| `data-target` | Fallback morph selector if server omits `json_content.target`. |

**Bundles**

- **`static/js/app.js`** — WebSocket, `sendWsRequest`, `ws_request`, `appendToast`, `dismissToast`, modal helpers, `MutationObserver` for `data-endpoint` / `data-function`.
- **`static/js/workouts.js`** — workout detail: carousel, `openSetModal`, placeholders. Loaded via `extra_js` on that page.

**Choosing an attribute**

- **`data-endpoint`** — generic pipeline only; no bespoke JS.
- **`data-routing` + `data-function`** — reusable handler that needs its own WS flow or DOM updates beyond `ws_request` (e.g. `MorphingModal`, `openSetModal`, inline edit save).
- **Hardcoded endpoint in JS** — handler is tied to a single route (e.g. `toggleSetDone` → `workouts/toggle_set_done`).
- **`data-endpoint-ns` on a shell element** — build the route in JS when the handler is shared across workout/routine pages but buttons do not carry a per-action route (e.g. add/remove exercise, refresh exercise view).

### `ws_request` behavior (implemented)

On response:

1. **302** → redirect  
2. **`data-refresh`** → reload  
3. **Morph** — `json_content.target` + `json_content.html` → `innerHTML` (no full page reload; preserves carousel)  
4. **200** + **`data-close-modal`** → hide modal  
5. **200** + **`json_content.toast_html`** → `appendToast(html, toast_delay_ms)`  

---

## 6. Frontend — CSS

- **`base.css`:** design tokens, resets, shared **components** (e.g. buttons, panels, tables), and **generic utilities** (spacing, typography) used across the app.
- **Per-area files** (`workouts.css`, `programs.css`, …) via `extra_css` for rules that must not apply globally (page glue, domain-specific layout).
- **Mobile-first:** base styles assume a narrow viewport; add min-width media queries when larger screens need extra space — not the other way around.
- Prefer touch-friendly control sizes and spacing for logging flows; layout and theme live in stylesheets, not inline.
- **Detailed policy** (what lives in `base.css` vs area CSS, promotion rule, naming): [docs/frontend-css.md](docs/frontend-css.md).

---

## 7. Backend — WebSocket protocol

**Client → server** (freeze field names once, document in repo):

```json
{
  "request_id": "opaque string",
  "endpoint": "string registered in WS_ENDPOINT_REGISTRY",
  "attributes": { "flattened form fields and data-* from trigger element": "..." }
}
```

`sendWsRequest` merges **`closest('form')` FormData** into `attributes` (e.g. set modal: `set_id`, `weight`, `reps`, `is_warmup` when checked).

### Server → client (gainz2 contract)

Every handled message should include **`request_id`** (echoed from client) and **`status`** (app-level code, not HTTP).

```json
{
  "request_id": "...",
  "status": 200,
  "headers": [],
  "json_content": {
    "target": "[data-set-id=\"123\"]",
    "html": "<td>...</td>...",
    "toast_html": "<div class=\"gainz-toast gainz-toast-success\">...</div>",
    "toast_delay_ms": 2500,
    "error": "only on non-200 when configured"
  }
}
```

| Field | Use |
|-------|-----|
| `json_content.target` + `html` | **Morph** one element via `innerHTML` (row = three `<td>`s; warmup reorder = whole `[data-exercise-sets-for]` block). |
| `json_content.toast_html` | **Success** (etc.) server-rendered toast; append only on **200**. |
| `json_content.toast_delay_ms` | Auto-dismiss delay (ms); separate from toast DOM. |
| `json_content.error` | **Configured** errors (e.g. 404 unknown endpoint). Client should show on non-200 when implemented. |


### Endpoint registry (`gainz2/ws_dispatch.py`)

- Flat **`WS_ENDPOINT_REGISTRY`** dict (grouped sections optional).
- Handlers: `(user, attributes) -> dict` in **`workouts/ws_handlers.py`** (etc.), imported into registry.

**Example — `workouts/update_set`**

- Attributes: `set_id`, `weight`, `reps`; `is_warmup` from checkbox (`on` / omitted).
- Service: `update_exercise_set`; if warmup toggled → reorder sets → morph **exercise_sets_block**; else morph **set_row_cells**.
- Message: `Set updated to {weight_display(weight)} x {reps}` via `gainz2.utils.render_toast`.
- Reps: `int(float(attributes["reps"]))` in handler.

**404** (unknown endpoint): `status: 404`, `json_content.error` string — no custom message per case required beyond that.

**Unhandled handler exceptions:** traceback in **Daphne terminal**; client often gets **no** JSON body. Do not assume `status: 500` on the wire unless you add an explicit boundary (team preference: avoid broad try/except in app code).

### Toasts

- **Success:** Python builds `message` string → `render_toast(message, variant="success")` → `toast_html` + `toast_delay_ms` in `json_content`.
- **One template:** `templates/components/toast.html` for all variants.
- **Weight display:** `utils.templatetags.formatting.weight_display` / `format_weight_display()` — one decimal in DB; display omits `.0` on whole numbers.

---

## 8. Backend — HTTP

`gainz2/urls.py` + app views (e.g. `workouts/views.py`) for initial pages. Same services as WS where behavior overlaps.

---

## 9. Data layer, Redis, and queues

- **PostgreSQL** for all application data.
- **Models** define entities, relationships, constraints, and useful indexes.
- **Migrations** for every schema change.

**Redis** and a **job queue** (e.g. **django-rq**) are part of the stack **from the start**. Define what runs **inside** the HTTP/WS response and what is **enqueued** for workers; document at least one enqueue pattern for consistency.

---

## 10. Security

- Resolve **user** on HTTP and WebSocket before running operations.
- Services enforce **ownership** (and roles where applicable) on every read/write of user data.
- CSRF and session policies for cookie-based POST where they apply; WebSocket auth matches the project’s chosen session/token approach.

---

## 11. Agent workflow when given a task

1. Classify: **model**, **service**, **HTTP view**, **WS handler**, **template**, **CSS**, **JS plumbing**.  
2. Implement or extend **services** (and **enqueue** when the task belongs on a worker).  
3. Wire **view** and/or **consumer** to services; build the response.  
4. Update **templates** and **`data-*`**; extend **`app.js`** only when the generic pipeline is not enough.  
5. Add or adjust **scoped CSS**; keep **`base.css`** for shared tokens.

---

## 12. Living documentation

- Keep an **authoritative description** of WS **endpoint names** and expected **attributes**.  
- **CSS/styling conventions:** [docs/frontend-css.md](docs/frontend-css.md).  
- **Tests** for critical flows (e.g. start workout from routine, complete set).  
- **Management commands** or seeds for comfortable local development.

---

This is written so a new agent can **follow the same stack and boundaries** without re-deriving them from chat history. §7 can be expanded later to match **`stolen_js.js`** response keys line-for-line once the repo exists.