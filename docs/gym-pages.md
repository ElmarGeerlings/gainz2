# Gainz: Gym Pages feature overview

Big-picture idea for the whole feature. We build it step by step; this doc is the context to keep in mind while doing so. Nothing here is final until it is built.

## Phases

- **V1: gym pages as a standalone product.** A bit like an upgraded Google Maps for lifters. Gym list and search, public gym page with basic info, equipment, policies, amenities, discipline checklists, attribution and freshness, chain templates, member editing. No dependency on the logger, programs or AI.
- **V2: integration.** Select a gym on workouts, gym-aware program builder and swaps, write-back reports from the AI and post-workout prompt, "Build a program for this gym" button.
- **V3: community and owners.** Who trains where, aggregate activity, discussion spaces, owner claims and moderation, quality control on edits, regional / gym-type template refinement.

Keep V2 and V3 in mind when designing V1 models, but do not build them early.

## Goal and audience

Every gym gets a page with practical info for lifters: what equipment it has, what's allowed, what it costs, and how suitable it is for specific disciplines.

- **Primary audience (first):** travelers and people who are new in town or looking for a new gym. Useful even with zero other users.
- **Secondary audience (later):** regulars who use the community features. These need user density, so they come in a later phase.

Gym pages are mainly an acquisition channel (search traffic, content links). Retention comes from the logger and the AI.

## Gym page content

### Basic info
- Name, address, photos, opening hours
- Ideally pulled from an external source. Licensing must be checked first: Google Places terms restrict storing content beyond place IDs and require photo attribution. OpenStreetMap (free, open map data, attribution required) is the open alternative for the base gym list. Manual seeding is the other option.

### Equipment
- Based on a fixed equipment template (checklist of standard items)
- Every item has one of three states: **unknown** (default), **present**, **absent**
- Absent items are shown explicitly (a "missing" section), because "no squat rack" is valuable info in itself
- Optional details for present items: quantity and brand
- Items have a category/subgroup (like bodypart on exercises), e.g. racks, free weights, machines, cardio
- Goal is a decent overview of what to expect, not a complete inventory. Incomplete data is fine, especially early on.

### Policies / rules
- Deadlifts allowed, chalk allowed, dropping weights allowed, filming allowed
- Prices: day pass, membership costs and terms

### Amenities
- Changing rooms and showers always listed
- Extras if present (sauna etc.)

### Discipline checklists
- A short checklist per discipline: powerlifting, Olympic lifting, maybe CrossFit
- Example for powerlifting: proper rack, power bar, competition-style bench, platform, calibrated plates, deadlifts allowed, chalk allowed
- Shown on the page as a checklist, e.g. "6 of 7 confirmed, 1 unknown". The checklist itself is what users read.
- A score is computed from the checklist behind the scenes, used for search and sorting (e.g. "powerlifting-friendly gyms in Lisbon")

## Data quality and trust

Wrong data is worse than no data. Errors must read as "one report was wrong" or "this is outdated", not as "Gainz is unreliable".

- **Attribution per item:** e.g. "Reported by 3 lifters, last confirmed Sep 2026" instead of a bare checkmark
- **Last-confirmed date** shown on everything so users can judge freshness
- **Single reports** are shown as visibly weaker than multiple confirmations
- **Honest wording:** "Lifters report deadlifts are allowed", not "Deadlifts allowed"
- **"Report incorrect"** button on every item
- **Staleness:** old confirmations may decay back to unknown after some period (e.g. ~1 year), exact period undecided

## Filling the data

### Templates and defaults
- Every gym starts from the equipment template with all items unknown
- Gym types: commercial gyms are the main focus. Hotel gyms get a minimal template (or are deprioritized).
- Templates may later be refined per gym type and per country/region

### Chains
- Chains (e.g. Basic-Fit) get a chain-level template that all locations inherit
- Inherited items are marked "chain default" until confirmed at that specific location
- Per-country/region chain templates later

### Seeding
- Initially seeded manually: local gyms first, plus the big chains via chain templates
- Long term it's a community effort

### Editing
- Initially any member can edit
- Later quality control, e.g. suggestions approved by others, or edits from users who have logged workouts at that gym carry more weight

### Automatic updates from usage (V2)
- When a user tells the AI something like "there's no leg press here", this is recorded as an **absent report** for that gym
- These are reports, not overwrites: an item that was recently confirmed present needs **two independent reports** to flip. An unknown item can flip on one.
- **Post-workout prompt:** after logging a workout at a gym, ask one quick question, e.g. "Deadlifts still allowed here? Yes / No / Didn't check"

### Gym owners (V3)
- Owners can claim their gym page
- Owners can edit equipment, policies and amenities, and post announcements
- Owner-provided info is labeled "verified by gym"; members can flag disagreements
- Owners can moderate their gym's discussion space, but cannot delete community reviews or discussion

## AI integration (V2)
- The program builder and workout editing use the selected gym's data:
  - **Absent:** hard filter, never suggested
  - **Present:** preferred
  - **Unknown:** assumed from a gym-type baseline (e.g. a commercial gym is assumed to have dumbbells and cables). Anything the AI relies on that is assumed rather than confirmed gets a fallback exercise in the program (e.g. "Leg press, or hack squat if not available").
- Mid-workout exercise swaps respect what the gym actually has
- `search_exercises` takes the gym into account; exercises need equipment requirements (an exercise can require multiple items, e.g. barbell bench press needs a barbell and a bench)
- Public gym pages get a **"Build a program for this gym"** button: visitors can try the program builder; saving the program requires signing up

## Public vs members-only

### Public (no account, indexable by search engines)
- Gym pages: basic info, equipment, policies, amenities, discipline checklists, aggregate activity
- Pages should rank for searches like "[gym] [city] deadlifts allowed"

### Members only
- Editing gym data, discussion, individual profiles and workouts, the AI assistant
- Gated buttons are visible to visitors and prompt sign-up when clicked

## Community (V3, needs users)
- Selecting a gym for a workout is optional; workouts can have no gym
- Profiles are public by default, with a private option. Private users are hidden everywhere except aggregate counts.
- Gym page shows (to members) who trains there and their recent workouts
- Workouts show the day only, not the time, unless you follow that person
- Aggregate activity per gym, visible to all: e.g. workouts logged this week, popular lifts (counts include private users)
- Discussion space per gym, e.g. a general questions thread and a thread for finding training partners

## Design notes for building

- Equipment and policies are separate parts of the feature. Whether they share one underlying "fact" table (same states, attribution, decay) or stay separate tables is undecided; decide when designing the models.
- Prefer storing reports and deriving the current state, so rules like "two reports to flip a recently confirmed item" and staleness decay are computed, not hand-maintained.
- Existing `Exercise.equipment_tags` (barbell, dumbbell, bodyweight, machine, cable) is coarse. Item-level equipment and exercise requirements are a V2 concern; do not replace `equipment_tags` in V1.
- Public pages need server-rendered HTTP GET with clean slugs (SEO). Edits and reports go through WebSocket handlers per the project architecture.
- Consider `noindex` for gyms with almost no data, to avoid thin-page SEO issues.

## Open decisions

- Base gym data source: OpenStreetMap import or manual seeding
- One generic fact table vs separate equipment / policy tables
- Staleness period for confirmations
- Equipment categories and the size of the template (keep it quick to fill, roughly 40-60 items)
- How equipment maps to exercises (V2)
