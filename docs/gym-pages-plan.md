# Gym Pages: planning and decisions

Higher-level plan for building Gym Pages step by step. The full vision is in `docs/gym-pages.md`. This doc records the decisions made so far and the build order. Update it as decisions change.

## Build order

1. **Static gym detail page** with sample data. No models, no handlers. Tweak the look and feel until it works well.
2. Backend for the detail page: models, services, view, real data.
3. Editing (equipment first, then the other blocks).
4. Gym list page with search and a few essential filters.
5. Map view (second view of the same list results).
6. Later: richer filters, exercise-equipment link, AI integration, community, owners (see `docs/gym-pages.md`).

Step 1 in progress: static page at `/gyms/demo/` (`gyms/views.py` sample context, `templates/gyms/`, `static/css/gyms.css`, `static/js/gyms.js`).

## Gym detail page (V1)

Mobile-first. Photo hero with name and city, then sticky tabs (tap only, no tab swiping). Compose UI from `base.css` / `frontend-css.mdc` (`panel`, `btn`, `form-control`, `gainz-modal`, typography utilities). Area CSS in `gyms.css` only for hero, photo viewer, amenity bubbles, equipment status column, map embed.

### Hero
- Swipeable photos; tap opens full-screen viewer (X and browser back to close). Empty state: “Be the first to add a picture.”
- Save/like in hero. Hero scrolls away; tab bar stays pinned.

### Tab 1: Overview (default)
- Description only (no address; address on Info).
- Open now / closed + today’s hours; tap jumps to Info → opening hours section.
- One discipline scores card (multiple disciplines); one modal with scrollable checklists for all.
- One prices card with two rows: day pass and subscription cost; tap opens full prices modal.
- Footer: shared info `last updated` date.

### Tab 2: Info
- Sections as `panel` cards: rules (yes/no/unknown list), amenities (bubble tags for present items, or empty copy), opening hours (`#gym-hours-panel`), contact (icon rows with `tel:` / `mailto:` / website / Instagram when set), location (Google Maps link + OSM embed iframe).
- Footer: same info `last updated` as Overview.
- Editing info/overview blocks: next step after static UI.

### Last updated (UI)
- **Two dates:** `info_updated_at` on Overview and Info footers; `equipment_updated_at` on Equipment footer only.

### Tab 3: Equipment
- Search + bodypart + status controls (same layout idea as exercise list). **Static step:** controls are visible only; they do not filter the list yet.
- Rows: name left, fixed-width status right (`Confirmed`, `Confirmed · 2`, `Assumed`, `Missing`). Tap row → modal with status buttons; quantity field when Confirmed (empty = unknown). Client-only until backend; reload resets.
- Groups: essentials, cardio, then bodypart groups. Items pre-sorted confirmed → assumed → missing within each group.
- Add equipment modal: search + bodypart select (non-functional in static step); list shows catalog items **not** already on the page.
- Footer: equipment `last updated`.

### Equipment voting (later idea, not V1)
- Weight recent reports over old ones when flipping confirmed/missing; needs design before backend. Not on the static page.

### Editing
- Equipment modal pattern chosen for V1 static preview. Other blocks TBD. Good-faith edits when wired; backup/history TBD.

## Backend direction (not yet decided in detail)

- Every piece of info is its own model field (no JSON blobs for structured data).
- Anything that will be used as a filter must be structured: opening hours (with timezone, for "open now"), prices as numbers (day pass, cheapest monthly), latitude/longitude (distance), chain.
- One big `Gym` model vs submodels: leaning towards one `Gym` model for the scalar fields (name, address, description, contact, prices). Equipment is naturally rows (one per gym and item), so it is a separate model regardless.
- Open question: opening hours (per-day fields on `Gym` vs a separate hours model), and rules/amenities (fields on `Gym` vs rows like equipment).
- **Chains (later):** one template record per chain (or per chain + country). New locations copy template data onto the gym at creation. Edits to the template can propagate to locations that still have untouched (assumed) values; confirmed/missing at a location stay put. Filters query gym rows directly, not chain fallback at read time.
- Equipment catalog (all known items, with a category), default list per chain / gym type, and per-gym rows for confirmed/missing (+ quantity, brand). Assumed = in template, no override row.
- Models only; the user runs migrations. Logic goes in `services.py` (see `.cursor/rules/gainz2.mdc`).

## Gym list page (later step)

Similar to Airbnb: search box, filter chips, list of gym cards. Map is a second view of the same results (a JS map library will be needed, decide when we get there).

- Essential filters first: name search, distance, open now, max day pass price, chain.
- Later filters: discipline score, chain vs independent, equipment-based (item present, brand, e.g. Eleiko rack), numeric item attributes such as max dumbbell weight (not in the model yet).
- Prefer tags derived from data over manually entered tags.
- Equipment filters need a "confirmed only" option because assumed is not confirmed.
- A good filter and search system is the main thing that makes this better than Google Maps.

## Open decisions

- Opening hours storage format
- Rules and amenities storage (fields vs rows)
- Prices: which numbers are headline (day pass, cheapest monthly, yearly basis or not)
- Backup / history approach
- Base data source for gyms (OpenStreetMap or manual seeding)
- Staleness period for confirmations
- Whether Confirmed/Assumed/Missing also tracks number of reports (trust wording from the vision)
- Equipment status voting / weighted reports (see above)
