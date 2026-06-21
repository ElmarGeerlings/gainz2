# Gainz

A workout tracking app for logging your training in the gym. It's live at **[elgainz.com](https://elgainz.com)**.

I built it because the lifting apps I tried didn't fit my needs. First and foremost it's a workout app where one can log workouts, except it's done smart so you don't have to manually change or edit every set. But it's not just for logging workouts; it is a platform with sections for goals, leaderboards, community, AI agents and much more.
Gainz is designed with a mobile-first approach, as that is the device that you use when you are in the gym.

## Try it

Head to [elgainz.com](https://elgainz.com) and hit **"Try a demo!"** on the home page. It drops you straight into a demo account with no signup, so you can poke around workout logging, routines, programs, and progress without committing to anything.

## What it does right now

- **Workout logging** — track exercises, sets, reps, and weights, and edit them mid-session. The set editing happens over a live connection, so updates land instantly without full page reloads.
- **Routines and programs** — build reusable templates and start a workout from a routine instead of setting everything up from scratch every time.
- **Exercise library** — keep your exercises in one place and reuse them across routines.
- **Progress** — period stats (workouts, volume, PR count, most trained bodypart), per-exercise charts (estimated 1RM or volume, with rep-range filters), and a personal records page grouped by exercise type with all-time and period bests.

## Where it's going

This is phase one. The plan is a fair bit bigger, and some of it is already sketched out on the home page:

- Smarter workouts: suggested loads across sessions, plus richer set types (tempo, bands, etc.)
- A rest timer tied to your profile and routines
- Sharing and discovering routines and programs from other lifters
- Community features: a feed, leaderboards, and head-to-head progress with people you pick
- AI agents that help build and refine routines, and eventually give training advice

## Tech

It's a Django app, but deliberately not a typical request/response CRUD one. The interesting part is how the client and server talk.

- **Backend:** Django 6 with Channels for WebSockets, running on Daphne (ASGI). PostgreSQL for data. Redis and django-rq for background and periodic tasks (scheduled jobs, cleanup, etc.) as the feature set grows.
- **Frontend:** server-rendered Django templates with a mostly vanilla Javascript layer.
- **Interaction model:** mutations and partial updates go over a **single WebSocket** instead of REST endpoints. The client sends a message with an `endpoint` name and the relevant form/data attributes; the server runs the operation and sends back a small envelope describing what to do; morph one element's HTML, show a toast, redirect, or reload. HTTP is left to do what it's good at: first paint, auth, and normal GETs.
- **Structure:** business logic lives in plain Python service functions. HTTP views and WebSocket handlers stay thin — they parse input, call a service, and shape the response. This keeps the same logic reusable whether it's hit over HTTP or the socket.
- **Frontend conventions:** behavior is driven by `data-*` attributes (`data-endpoint` for the generic WebSocket pipeline, `data-function` for client-side steps), so most new features are wired up in the template rather than in bespoke JS.

### Running it
The app runs in Docker (managed with `docker compose`) and is deployed on a Hetzner VPS, with Caddy sitting in front as the HTTPS edge and serving static files, proxying everything else (including the WebSocket) to the app container.