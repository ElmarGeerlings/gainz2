# New project — agent implementation guide

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
   Business behavior lives in plain Python **service / operation** functions (e.g. `start_workout_from_routine(user, routine_id)`, `complete_set(...)`, `list_workouts(...)`). **HTTP views** and **WebSocket consumers** authenticate, parse input, call those functions, and shape the response (HTML page, HTML fragment, JSON envelope, redirect).

2. **Interactive client ↔ server**  
   Interactive mutations and partial updates use the **WebSocket** message contract (see §7). **HTTP** handles first paint, auth pages, health checks, and other standard GET/POST flows.

3. **Sync Django for typical work**  
   **Sync** views and **sync** ORM for normal request/response. **Channels** handles WebSockets; consumers may use `database_sync_to_async` around sync services when needed.

4. **Persistence and responses**  
   **Django models + ORM** for all persisted data. **JSON and HTML** are built with dicts, small helpers, and templates.

5. **Python**  
   **Python 3.10+** compatible code unless the team agrees otherwise.

---

## 3. Repository / Django layout

Project **root** (same directory as **`manage.py`**) holds site wiring; **`DJANGO_SETTINGS_MODULE`** is **`settings`** (i.e. `settings.py` at root).

```
project_root/
  manage.py
  gainz/
    settings.py
    urls.py
    asgi.py
    routing.py
    consumers.py
    ws_dispatch.py
  workouts/
    models.py
    admin.py
    services.py
    ws_handlers.py
    views.py
  programs/
    models.py
    admin.py
    services.py
    views.py
  templates/
    base.html
    workouts/
    programs/
  static/
    css/
      base.css
      workouts.css
      programs.css
    js/
      app.js
```

**`urls.py`** — all HTTP routes in one file (import views from apps as needed).  
**`routing.py`** — WebSocket **connection** URL → consumer class (Channels).  
**`ws_dispatch.py`** — WebSocket **message** `endpoint` string → handler callable (application registry; grouped like `urls.py`).  
**`consumers.py`** — WebSocket receive/send; delegates dispatch to **`ws_dispatch`** (thin).  
**`asgi.py`** — ASGI application combining Django HTTP and Channels.

**Apps** hold **models**, **migrations**, **admin**, **`services.py`** (operations), **`views.py`** (thin HTTP handlers). Split into extra modules or `views/` / `services/` packages when a file grows too large.

**Agents:** core rules live in **Python services**; views and consumers call services and return responses.

---

## 4. Frontend — templates

- **Django templates** for UI.
- **`base.html`**: layout, blocks (`content`, `extra_css`, `extra_js`), shared chrome — structured for **mobile-first** (see §1).
- **Partials** for fragments returned over the wire for **HTML swaps**.

---

## 5. Frontend — JavaScript

**Declarative attributes** (same idea as your reference `stolen_js.js`):

| Attribute | Meaning |
|-----------|--------|
| `data-endpoint="click->server_route_name"` | **Generic** pipeline: collect element attributes (+ form context), send WS message with `endpoint` = `server_route_name`, apply **standard** response handling (redirect, reload, replace `innerHTML` for a target, toasts). |
| `data-function="click->handlerName"` | Calls `window.handlerName(event)`; may read `data-*` and call **`sendWsRequest(endpoint, element)`** for server work. |

**One main bundle (`app.js`):** WebSocket connection, **`sendWsRequest`** with **`request_id`** and a **`Map`**, **`onmessage`** resolver, **`MutationObserver`** for new `data-endpoint` / `data-function` nodes, shared loading UI if you use it.

Prefer **`data-endpoint`** when generic handling is enough; use **`data-function`** when the client needs extra steps while still sending authoritative work to the server via **`sendWsRequest`**.

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
  "endpoint": "string registered on server",
  "attributes": { "data-* and special keys flattened": "..." }
}
```

**Server → client:** include `request_id`, `status`, and payload fields your client expects (`html_content`, `json_content` with target + html, etc.) — match your real **`stolen_js.js`** contract.

### Endpoint registry (`gainz2/ws_dispatch.py`)

- **`routing.py`** maps the **socket URL** (e.g. `/ws/`) to **`MainConsumer`**. It does **not** define per-message endpoints.
- **`ws_dispatch.py`** holds **`WS_ENDPOINT_REGISTRY`**: one dict mapping **`endpoint` string → sync handler**, organized in grouped sections (e.g. **`CORE`**, **`WORKOUTS`**) like **`urls.py`**.
- **Adding a feature:** register the endpoint string in **`WS_ENDPOINT_REGISTRY`**, implement a **handler** `(user, attributes) -> response dict`. Handler implementations for an app may live in **`workouts/ws_handlers.py`** (or similar) and are **imported** into **`ws_dispatch`** — the **index of all message endpoints stays in one file**.
- **Handlers** stay thin: parse **`attributes`**, call **`services.py`** for business logic, build **`html_content` / `json_content`** for the client. **`services`** are the internal API shared with HTTP views where behavior overlaps.
- **`MainConsumer.receive`** runs sync dispatch via **`database_sync_to_async(dispatch_ws_endpoint)`** so sync ORM/services do not block the ASGI event loop.

**Dispatch:** registry **`endpoint` string → callable**; callable receives **user** and **attributes**; returns the response dict. **Django Channels** + ASGI for WebSockets.

---

## 8. Backend — HTTP

**`urls.py`** and views serve initial pages, auth, health checks, and normal GET/POST. They call the **same service functions** as the consumer where behavior overlaps.

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