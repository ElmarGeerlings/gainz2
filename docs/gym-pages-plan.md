# Gym Pages: planning and decisions

Higher-level plan for building Gym Pages step by step. The full vision is in `docs/gym-pages.md`. This doc records the decisions made so far and the build order. Update it as decisions change.

## Build order

1. **Static gym detail page** with sample data. No models, no handlers. Tweak the look and feel until it works well.
2. Backend for the detail page: models, services, view, real data.
3. Editing (equipment first, then the other blocks).
4. Gym list page with search and a few essential filters.
5. Map view (second view of the same list results).
6. Later items: see **Future ideas** below (not part of the numbered sequence above).

Step 1 in progress: static page at `/gyms/demo/` with **client-only section edits** (pencil → modal → Save updates DOM; close discards). Backend persistence comes in step 2–3.

### Static edit UI (current)
- **Vibe:** Serious / Casual / Unknown (default **Unknown**, shown as “Unknown”).
- **Open now:** static line “Holiday hours may vary.” (no holiday API yet).
- **Prices:** same modal toggles read ↔ edit; add/remove plan rows; overview headlines derived on Save.
- **Equipment:** row modal unchanged (client-only status/qty).
- Edits do not call WebSocket or HTTP save yet.

## Gym detail page (V1)

Mobile-first. Photo hero with name and city, then sticky tabs (tap only, no tab swapping). Compose UI from `base.css` / `frontend-css.mdc` (`panel`, `btn`, `form-control`, `gainz-modal`, typography utilities). Area CSS in `gyms.css` only for hero, photo viewer, amenity bubbles, equipment status column, map embed.

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

### Editing
- Equipment modal pattern chosen for V1 static preview. Other blocks TBD. Good-faith edits when wired; backup/history TBD.

## Backend direction (not yet decided in detail)

- Every piece of info is its own model field (no JSON blobs for structured data).
- Anything that will be used as a filter must be structured: opening hours (with timezone, for "open now"), prices as numbers (day pass, cheapest monthly), latitude/longitude (distance), chain.
- One big `Gym` model vs submodels: leaning towards one `Gym` model for the scalar fields (name, address, description, contact, prices). Equipment is naturally rows (one per gym and item), so it is a separate model regardless.
- Open question: opening hours (per-day fields on `Gym` vs a separate hours model), and rules/amenities (fields on `Gym` vs rows like equipment).
- Equipment catalog (all known items, with a category), default list per chain / gym type, and per-gym rows for confirmed/missing (+ quantity, brand). Assumed = in template, no override row.
- Models only; the user runs migrations. Logic goes in `services.py` (see `.cursor/rules/gainz2.mdc`).

## Gym list page (later step)

Similar to Airbnb: search box, filter chips, list of gym cards. Map is a second view of the same results (a JS map library will be needed, decide when we get there).

- Essential filters first: name search, distance, open now, max day pass price, chain.
- Richer filter ideas (discipline score, chain vs independent, equipment-based filters, numeric item attributes): see **Future ideas**.
- Prefer tags derived from data over manually entered tags.
- Equipment filters need a "confirmed only" option because assumed is not confirmed.
- A good filter and search system is the main thing that makes this better than Google Maps.

## Future ideas

Ideas called out elsewhere in the vision or build notes, grouped here for later design work (not V1 static scope):

- **List & map:** richer filters beyond the essential set; map as second view of list results (library TBD).
- **Exercise ↔ equipment:** link catalog exercises to equipment rows so “does this gym have what I need for my program?” is answerable.
- **AI integration:** assist with descriptions, summarizing reviews, or filling assumed data (product TBD).
- **Community & owners:** verified owners, moderation, trust signals; see `docs/gym-pages.md`.
- **Holiday & hours:** real holiday-hour data and user-facing announcements (static “Holiday hours may vary” today).
- **Amenity groups:** present amenities under groups such as facilities, classes, and training (e.g. a powerlifting team under training); V1 uses a flat alphabetical list with section name “Amenities”.
- **Chains:** template record per chain (or chain + country); new locations copy template; propagate to locations with untouched assumed values; confirmed/missing stay local.
- **Equipment voting:** weight recent reports when flipping confirmed/missing; staleness period and report counts TBD.
- **Backup / history:** approach for reverting bad edits (TBD).

## Open decisions

- Opening hours storage format
- Rules and amenities storage (fields vs rows)
- Prices: which numbers are headline (day pass, cheapest monthly, yearly basis or not)
- Backup / history approach
- Base data source for gyms (OpenStreetMap or manual seeding)
- Staleness period for confirmations
- Whether Confirmed/Assumed/Missing also tracks number of reports (trust wording from the vision)
- Equipment status voting / weighted reports (see **Future ideas**)
