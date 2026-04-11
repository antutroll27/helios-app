# HELIOS — Circadian Intelligence Engine

## What This Is
A hackathon-winning circadian intelligence app that uses live NASA satellite data, NOAA space weather, and peer-reviewed circadian science to generate personalized daily biological protocols. Features a COBE 3D globe, AI chat (4 providers), protocol cards, and data visualizations.

## Tech Stack
- **Frontend**: Vue 3 + Composition API (`<script setup>`), TypeScript
- **Styling**: Tailwind CSS v4.2 with `@theme` tokens in `src/style.css`, plus scoped CSS for component-specific values
- **State**: Pinia stores (`src/stores/`)
- **3D Globe**: COBE library (`cobe`) — canvas-based WebGL globe with drag, idle drift, and marker support
- **Astronomy**: SunCalc.js (client-side solar position, sunrise/sunset calculations)
- **AI Chat**: 4 providers — OpenAI, Claude (Anthropic), Kimi via DeepInfra, GLM via Zhipu AI (`src/composables/useAI.ts`)
- **APIs**: NASA DONKI, NOAA SWPC (space weather), Open-Meteo (weather), AQICN (air quality)
- **Build**: Vite 8, vite-plugin-pwa + workbox
- **Research**: Python research engine — 7 peer-reviewed modules (`research/`)
- **Deployment**: Vercel (https://helios-app-six.vercel.app/)

## Project Structure
```
helios-app/
├── src/
│   ├── components/
│   │   ├── globe/
│   │   │   ├── HeliosCobeGlobe.vue    # COBE canvas globe — drag, idle drift, markers
│   │   │   ├── HeliosGlobePanel.vue   # Globe container + all overlays (orchestrator)
│   │   │   ├── GlobeComparisonHud.vue # Right-rail destination selector
│   │   │   ├── GlobeOrbitalContext.vue # Top-left solar phase + space weather HUD
│   │   │   └── GlobeStatStrip.vue     # Bottom pill strip (anchor, target, solar shift)
│   │   ├── home/
│   │   │   ├── HomeChatPlaceholder.vue # Loading skeleton for chat section
│   │   │   └── HomeGlobePlaceholder.vue # Animated loading state for globe
│   │   ├── NavBar.vue            # Fixed glassmorphism navbar
│   │   ├── ProtocolCard.vue      # Swiss-style colored circle cards
│   │   ├── ProtocolTimeline.vue  # 3x2 protocol grid with section header
│   │   ├── SpaceWeatherGauge.vue # Kp index + disruption indicator
│   │   ├── SocialJetLagScore.vue # Solar alignment score display
│   │   ├── EnvironmentBadge.vue  # 2x2 UV/Temp/AQI/Humidity grid
│   │   ├── ChatInterface.vue     # AI chat with 4 providers
│   │   └── OnboardingModal.vue   # First-run location + sleep setup
│   ├── composables/
│   │   ├── useAI.ts              # Multi-provider AI adapter + scientific knowledge base
│   │   ├── useTheme.ts           # Dark/light mode toggle
│   │   ├── useCobeGlobeData.ts   # Globe data aggregator (solar, geo, space weather, jet lag)
│   │   ├── useHomeDeferredSections.ts # IntersectionObserver-based deferred loading
│   │   └── useStagedReveal.ts    # Timed reveal (globe: 450ms delay, chat: 1400ms)
│   ├── stores/
│   │   ├── protocol.ts           # Daily protocol generation (wake, light, focus, caffeine, wind-down, sleep)
│   │   ├── spaceWeather.ts       # NOAA SWPC live data (Kp, solar wind, Bz)
│   │   ├── solar.ts              # SunCalc-based solar position tracking
│   │   ├── environment.ts        # Open-Meteo + AQICN data
│   │   ├── geo.ts                # Geolocation + reverse geocoding
│   │   ├── donki.ts              # NASA DONKI CME/flare events
│   │   ├── jetlag.ts             # Jet lag recovery schedule generator (IANA timezone cities)
│   │   └── user.ts               # User preferences (sleep time, provider, API keys)
│   ├── lib/
│   │   └── circadianTruth.ts     # Protocol copy helpers (alignment metric, caffeine cutoff narrative)
│   ├── pages/
│   │   ├── HomePage.vue          # Main dashboard layout
│   │   └── SettingsPage.vue      # AI provider + sleep config
│   └── style.css                 # Tailwind v4 @theme tokens, CSS variables, utility classes
├── research/                     # Python research engine (7 peer-reviewed modules — see below)
├── backend/                      # FastAPI backend (see backend phase status below)
├── vercel.json                   # SPA rewrites + --legacy-peer-deps install
└── .env                          # VITE_AQICN_TOKEN, VITE_NASA_API_KEY (do NOT commit secrets)
```

## Design System

### Palette
| Token | Hex | Usage |
|---|---|---|
| Onyx | `#0A171D` | Dark backgrounds, text on light |
| Wheat | `#FFF6E9` | Light backgrounds, text on dark |
| Oceanic | `#003F47` | Accents, secondary surfaces |
| Nectarine | `#FFBD76` | Primary accent, highlights |
| Calm | `#00D4AA` | Success, aligned states |
| Storm | `#FF4444` | Error, misaligned states |

### Typography
- Display: Sora / Space Grotesk
- Body: Plus Jakarta Sans / Inter
- Mono: Geist Mono / JetBrains Mono

### @theme Font Size Tokens (in `style.css`)
These generate standard Tailwind classes — use these instead of arbitrary values:
| Class | Size | Usage |
|---|---|---|
| `text-5xs` | 0.35rem | Env sub-labels, tagline |
| `text-4xs` | 0.4rem | Live dot indicator |
| `text-3xs` | 0.45rem | Coordinates, MIN label |
| `text-2xs` | 0.48rem | Citations |
| `text-xs2` | 0.5rem | Badges, live dots |
| `text-xs3` | 0.55rem | Section meta labels |
| `text-xs4` | 0.6rem | Attribution footer |
| `text-xs5` | 0.65rem | Location name, descriptions |
| `text-xs6` | 0.7rem | Subtitles, gauge values |
| `text-sm2` | 0.85rem | Env badge numbers |
| `text-md2` | 0.9rem | Disruption label |
| `text-lg2` | 1.35rem | Protocol card time |

### @theme Tracking Tokens
| Class | Value |
|---|---|
| `tracking-micro` | 0.03em |
| `tracking-tight2` | -0.02em |
| `tracking-fine` | 0.05em |
| `tracking-spread` | 0.08em |
| `tracking-label` | 0.15em |
| `tracking-ultra` | 0.25em |

## Critical CSS Rules

### DO: Hybrid Tailwind + Scoped CSS
- **Use Tailwind** for layout (`flex`, `grid`, `items-center`), standard spacing (`gap-2`, `pt-8`, `mb-3`), colors (`text-(--text-primary)`, `bg-(--bg-card)`), and `@theme` token classes (`text-xs6`, `tracking-spread`)
- **Use scoped CSS** for component-specific pixel values (90px circle, 52px gauge, 220px grid), gradients, hover transforms, compound card styles, and the 960px content container

### DON'T: No Arbitrary Bracket Values
**Never use Tailwind arbitrary values** like `text-[0.55rem]`, `max-w-[960px]`, `tracking-[0.08em]`, `gap-[0.6rem]`. These fail to compile in Vite HMR dev server, causing localhost to look broken while the production build looks correct. Use `@theme` tokens or scoped CSS instead.

### Content Centering
The `.content-container` class in `HomePage.vue` uses scoped CSS (`max-width: 960px; margin: 0 auto;`). Do NOT replace this with Tailwind's `max-w-*` — it breaks in dev.

## Files — Do Not Touch
- `src/components/globe/HeliosCobeGlobe.vue` — COBE canvas globe with drag/settle/idle-drift animation loop. Tightly coupled internal state.
- `src/components/globe/HeliosGlobePanel.vue` — Layout and overlay positioning is pixel-precise. Don't restructure.
- `src/components/ChatInterface.vue` — Extensive scoped styles that work correctly. No Tailwind conversion needed.

## AI Providers

**4 providers implemented** in `useAI.ts`. Do not add fake providers or claim more than exist.

| ID | Display Name | Format |
|---|---|---|
| `openai` | OpenAI | OpenAI chat completions |
| `claude` | Claude | Anthropic messages API (x-api-key header, system top-level) |
| `kimi` | Kimi (DeepInfra) | OpenAI-compatible via DeepInfra |
| `glm` | GLM | OpenAI-compatible via Zhipu AI |

Model IDs in `PROVIDERS` and `PROVIDER_CONFIGS` should be updated when providers release new versions. Do not document specific model version strings — they go stale.

## Build & Deploy

### Install
```bash
npm install --legacy-peer-deps  # Required — vite-plugin-pwa doesn't support Vite 8
```

### Dev
```bash
npm run dev  # Vite dev server, usually localhost:5173
```

### Build
```bash
npm run build  # Output to dist/
```

### Environment Variables
```
VITE_AQICN_TOKEN=<aqicn api token>
VITE_NASA_API_KEY=<nasa api key, falls back to DEMO_KEY>
```

### Vercel Config
- `vercel.json` has `installCommand` with `--legacy-peer-deps`
- SPA rewrites: `{ "source": "/(.*)", "destination": "/index.html" }`

## Backend (FastAPI + Supabase)

### Architecture
```
Vue 3 Frontend (useAI.ts)
    │ POST /api/chat/send
    ▼
FastAPI Backend (backend/)
    ├── Auth (Supabase JWT)
    ├── Hermes Memory Learner (per-user markdown memory files)
    ├── LLM Proxy (OpenAI, Claude, Kimi, GLM + shared key fallback)
    ├── Wearable Parsers (Oura, Whoop, Fitbit, Garmin, Apple Health, Samsung)
    ├── Research Modules (chronotype, caffeine, space weather, light)
    └── Supabase (auth, user DB, memories, chat logs, sleep logs)
```

### Backend Phase Status

| Phase | What | Status |
|---|---|---|
| **1 — Chat Proxy** | `/chat/send`, `/chat/end-session`, LLM proxy, prompt builder, Supabase auth | **Built** — uses in-memory session storage; needs Supabase wiring to persist across restarts |
| **2 — Hermes Memory** | Session → insight extraction, per-user markdown memory, prompt injection | **Hermes learner built** — memory service framework exists but not wired to Supabase; memory is currently always empty in live requests |
| **3 — Supabase Wiring** | Connect sessions, memories, chat history to Supabase DB | **Pending** — blocked until UI and use cases are finalised |
| **4 — Wearable Import** | Upload endpoint, file parsers (Oura, Whoop, Fitbit, Garmin, Apple, Samsung) | **Pending** — router and parsers are empty stubs |
| **5 — Circadian Routes** | `/chronotype`, `/protocol/today`, research module API endpoints | **Pending** — research modules built in Python but not wired to any route |

### Hermes Memory System
Each user has a per-account Hermes agent that learns from their conversations:
- **Uses the user's own LLM key** — zero extra API costs
- After each chat session, Hermes processes the transcript and extracts circadian insights
- Insights stored as structured markdown in `user_memories` table (one row per user)
- Before each LLM call, memory is injected into the system prompt as `[USER PROFILE FROM MEMORY]`
- Memory evolves over time: sleep patterns, caffeine habits, protocol adherence, communication preferences
- No Mem0, no pgvector, no shared API keys — just Postgres + markdown + user's own LLM

### Shared Key (Free Tier)
Users without their own API key get a shared "house" model (default: Kimi via DeepInfra):
- Rate-limited to 20 messages/day per user
- Hermes learning still works using the shared key

### Backend Structure
```
backend/
├── main.py                    # FastAPI app, CORS, routers (Phase 1 active; 2-5 commented out pending Supabase)
├── config.py                  # Supabase, encryption, provider configs, shared key
├── schema.sql                 # Full Supabase migration with RLS
├── auth/supabase_auth.py      # JWT verification + Fernet API key encryption
├── chat/
│   ├── router.py              # /chat/send, /chat/end-session, /chat/memory (in-memory for now)
│   ├── prompt_builder.py      # System prompt with scientific KB + memory injection placeholder
│   └── llm_proxy.py           # Multi-provider LLM caller (async httpx)
├── memory/
│   ├── hermes_learner.py      # Session processor → markdown memory (built, not yet wired)
│   └── memory_service.py      # CRUD for user_memories in Supabase (framework only)
├── wearable/parsers/          # Stub — routers and parsers not yet implemented
└── circadian/                 # Stub — research module routes not yet implemented
```

### Backend Environment Variables
```
SUPABASE_URL=<supabase project url>
SUPABASE_KEY=<supabase service role key>
SUPABASE_JWT_SECRET=<jwt secret for token verification>
ENCRYPTION_KEY=<fernet key for API key encryption>
SHARED_LLM_PROVIDER=kimi
SHARED_LLM_KEY=<api key for shared/free tier>
SHARED_LLM_RATE_LIMIT=20
CORS_ORIGINS=http://localhost:5173,https://helios-app-six.vercel.app
```

## Research Modules (`research/`)

### Built — V1
- `chronotype_engine.py` — MCTQ (MSFsc, SJL), protocol scoring, circadian phase estimation
- `caffeine_model.py` — Personalized pharmacokinetics (CYP1A2, ADORA2A), multi-dose tracking, optimal cutoff
- `space_weather_bio.py` — Kp→HRV impact (Alabdali 2022), melatonin modifier (Burch 2008, labeled "preliminary"), composite disruption
- `light_model.py` — Melanopic EDI zones (Brown 2022), melatonin suppression model (Gimenez 2022), screen/lamp impact

### Built — V2
- `alcohol_model.py` — BAC pharmacokinetics (Widmark), HRV/deep sleep impact per drink count (Pietilä 2018, n=4,098)
- `breathwork_model.py` — Resonance frequency finder, HRV dose-response (Laborde 2022 meta-analysis)
- `nap_model.py` — NASA 26-min nap protocol, duration/timing optimization, coffee nap sequencing (Rosekind 1995)

### Planned
- `meal_timing_model.py` — Time-restricted feeding, peripheral clock alignment (Sutton 2018)
- `exercise_timing_model.py` — First human exercise PRC (Youngstedt 2019)
- `supplement_model.py` — Mg glycinate, melatonin, glycine (meta-analysis effect sizes)
- `cold_exposure_model.py` — Cold water HRV rebound, norepinephrine (Espeland 2022)
- `hrv_sleep_model.py` — Sleep regularity index, bedtime deviation penalty (Windred 2024)
- `wearable_pipeline.py` — Garmin/Oura/Fitbit data parsers → SleepLog
- `jetlag_optimizer.py` — Kronauer model, optimal light schedules

## Wearable Data Import (No OAuth Required)
Users export their own data and upload to HELIOS. Parser stubs exist in `backend/wearable/parsers/`:
- **Oura** (JSON) — parser stub exists, needs implementation
- **Whoop** (CSV) — planned
- **Fitbit** (JSON via Google Takeout) — planned
- **Samsung** (CSV) — planned
- **Garmin** (FIT binary) — planned, needs fitparse
- **Apple Health** (XML) — planned, streaming parse

## Key Architectural Decisions
1. **Client-side astronomy** — SunCalc runs in browser, no server needed for solar calculations
2. **No auth required** for NASA DONKI / NOAA SWPC APIs — public endpoints
3. **Night owl support** — Wake window uses sleep time + 8h instead of forcing sunrise for late chronotypes
4. **Solar alignment gap capped at 360 min** — Prevents midnight wrap-around producing 1800+ min values
5. **BYOK + shared key** — Users bring their own API key OR use the free tier shared model
6. **Scientific knowledge base** — Injected into AI system prompt with exact citations (Burke et al., NASA ISS protocols, etc.)
7. **Hermes uses user's own key** — Background learning costs us nothing, each user's agent is independent
8. **Markdown memory files** — No vector DB needed, plain text in Postgres, structured categories, GDPR-deletable
9. **COBE globe** — Replaced globe.gl/Three.js with COBE (canvas WebGL, lighter); comparison mode shows jet-lag destination deltas

## Project Status
- **Hackathon Winner** — Won the Da Nang Digital Nomad Fest hackathon (March 2026)
- **Investor Interest** — Investors are interested in the app's future scientific capabilities (circadian intelligence, MCTQ chronotype engine, peer-reviewed protocol scoring)
- **Landing Page** — Astro.js project scaffolded at `../landing_page/` — do not edit until explicitly told to

## Git Workflow
- `master` — production branch (deployed to Vercel)
- `dev` — development branch (backend + research modules)
- Feature branches: `feature/fastapi-backend`, `feature/python-research`, `feature/wearable-integration`
- **Do NOT push to GitHub** without explicit user permission
