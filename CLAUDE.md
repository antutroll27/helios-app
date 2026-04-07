# HELIOS — Circadian Intelligence Engine

## What This Is
A hackathon-winning circadian intelligence app that uses live NASA satellite data, NOAA space weather, and peer-reviewed circadian science to generate personalized daily biological protocols. Features a 3D globe, AI chat (7 providers), protocol cards, and data visualizations.

## Tech Stack
- **Frontend**: Vue 3 + Composition API (`<script setup>`), TypeScript
- **Styling**: Tailwind CSS v4.2 with `@theme` tokens in `src/style.css`, plus scoped CSS for component-specific values
- **State**: Pinia stores (`src/stores/`)
- **3D Globe**: globe.gl + Three.js with DirectionalLight sunlit dayside, solar terminator, auroral ovals
- **Astronomy**: SunCalc.js (client-side solar position, sunrise/sunset calculations)
- **AI Chat**: 7 providers — OpenAI, Anthropic, Google Gemini, Perplexity, Moonshot AI, Alibaba Qwen, Zhipu AI (`src/composables/useAI.ts`)
- **APIs**: NASA DONKI, NOAA SWPC (space weather), Open-Meteo (weather), AQICN (air quality)
- **Build**: Vite 8, vite-plugin-pwa + workbox
- **Research**: Python MCTQ chronotype engine (`research/chronotype_engine.py`)
- **Deployment**: Vercel (https://helios-app-six.vercel.app/)

## Project Structure
```
helios-app/
├── src/
│   ├── components/
│   │   ├── HeliosGlobe.vue      # 3D globe with HUD overlays
│   │   ├── NavBar.vue            # Fixed glassmorphism navbar
│   │   ├── ProtocolCard.vue      # Swiss-style colored circle cards
│   │   ├── ProtocolTimeline.vue  # 3x2 protocol grid with section header
│   │   ├── SpaceWeatherGauge.vue # Kp index + disruption indicator
│   │   ├── SocialJetLagScore.vue # Circular border score display
│   │   ├── EnvironmentBadge.vue  # 2x2 UV/Temp/AQI/Humidity grid
│   │   ├── ChatInterface.vue     # AI chat with 7 providers
│   │   └── OnboardingModal.vue   # First-run location + sleep setup
│   ├── composables/
│   │   ├── useAI.ts              # Multi-provider AI adapter + scientific knowledge base
│   │   └── useTheme.ts           # Dark/light mode toggle
│   ├── stores/
│   │   ├── protocol.ts           # Daily protocol generation (wake, light, focus, caffeine, wind-down, sleep)
│   │   ├── spaceWeather.ts       # NOAA SWPC live data (Kp, solar wind, Bz)
│   │   ├── solar.ts              # SunCalc-based solar position tracking
│   │   ├── environment.ts        # Open-Meteo + AQICN data
│   │   ├── geo.ts                # Geolocation + reverse geocoding
│   │   ├── donki.ts              # NASA DONKI CME/flare events
│   │   └── user.ts               # User preferences (sleep time, provider, API keys)
│   ├── pages/
│   │   ├── HomePage.vue          # Main dashboard layout
│   │   └── SettingsPage.vue      # AI provider + sleep config
│   └── style.css                 # Tailwind v4 @theme tokens, CSS variables, utility classes
├── research/
│   └── chronotype_engine.py      # MCTQ, protocol scoring, circadian phase estimation
├── vercel.json                   # SPA rewrites + --legacy-peer-deps install
└── .env                          # VITE_AQICN_TOKEN, VITE_NASA_API_KEY
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
- `src/components/HeliosGlobe.vue` — Complex HUD positioning with scoped CSS. Globe, terminator, auroral rings, sunlight are tightly coupled.
- `src/components/ChatInterface.vue` — Extensive scoped styles that work correctly. No Tailwind conversion needed.

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

### Hermes Memory System
Each user has a per-account Hermes agent that learns from their conversations and wearable data:
- **Uses the user's own LLM key** — zero extra API costs
- After each chat session, Hermes processes the transcript and extracts circadian insights
- Insights stored as structured markdown in `user_memories` table (one row per user)
- Before each LLM call, memory.md is injected into the system prompt as `[USER PROFILE FROM MEMORY]`
- Memory evolves over time: sleep patterns, caffeine habits, protocol adherence, communication preferences
- No Mem0, no pgvector, no shared API keys — just Postgres + markdown + user's own LLM

### Shared Key (Free Tier)
Users without their own API key get a shared "house" model (default: Kimi via DeepInfra):
- Rate-limited to 20 messages/day per user
- Hermes learning still works using the shared key
- Frontend shows upgrade prompt: "Add your own key for unlimited access"

### Backend Structure
```
backend/
├── main.py                    # FastAPI app, CORS, routers
├── config.py                  # Supabase, encryption, provider configs, shared key
├── schema.sql                 # Full Supabase migration with RLS
├── auth/supabase_auth.py      # JWT verification + Fernet API key encryption
├── chat/
│   ├── router.py              # /chat/send, /chat/end-session, /chat/memory
│   ├── prompt_builder.py      # System prompt with scientific KB + memory injection
│   └── llm_proxy.py           # Multi-provider LLM caller
├── memory/
│   ├── hermes_learner.py      # Session processor → markdown memory updates
│   └── memory_service.py      # CRUD for user_memories in Supabase
├── wearable/parsers/          # Platform-specific file parsers (Oura, Whoop, etc.)
└── circadian/                 # Research module wrappers
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
```

## Research Modules (`research/`)

### Built
- `chronotype_engine.py` — MCTQ (MSFsc, SJL), protocol scoring, circadian phase estimation
- `caffeine_model.py` — Personalized pharmacokinetics (CYP1A2, ADORA2A), multi-dose tracking, optimal cutoff
- `space_weather_bio.py` — Kp→HRV impact (Alabdali 2022), melatonin modifier, cognitive advisory, composite disruption
- `light_model.py` — Melanopic EDI zones (Brown 2022), melatonin suppression model (Gimenez 2022), screen/lamp impact

### Planned
- `wearable_pipeline.py` — Garmin/Oura/Fitbit data parsers → SleepLog
- `jetlag_optimizer.py` — Kronauer model, optimal light schedules

## Wearable Data Import (No OAuth Required)
Users export their own data and upload to HELIOS:
- **Oura** (JSON) → trivial, maps 1:1 to SleepLog
- **Whoop** (CSV) → easy, clean columns
- **Fitbit** (JSON via Google Takeout) → easy
- **Samsung** (CSV) → easy
- **Garmin** (FIT binary) → medium, needs fitparse
- **Apple Health** (XML) → hard, streaming parse, but universal import for iOS users

## Key Architectural Decisions
1. **Client-side astronomy** — SunCalc runs in browser, no server needed for solar calculations
2. **No auth required** for NASA DONKI / NOAA SWPC APIs — public endpoints
3. **Night owl support** — Wake window uses sleep time + 8h instead of forcing sunrise for late chronotypes
4. **Social jet lag capped at 360 min** — Prevents midnight wrap-around producing 1800+ min values
5. **BYOK + shared key** — Users bring their own API key OR use the free tier shared model
6. **Scientific knowledge base** — Injected into AI system prompt with exact citations (Burke et al., NASA ISS protocols, etc.)
7. **Hermes uses user's own key** — Background learning costs us nothing, each user's agent is independent
8. **Markdown memory files** — No vector DB needed, plain text in Postgres, structured categories, GDPR-deletable

## Project Status
- **Hackathon Winner** — Won the Da Nang Digital Nomad Fest hackathon (March 2026)
- **Investor Interest** — Investors are interested in the app's future scientific capabilities (circadian intelligence, MCTQ chronotype engine, peer-reviewed protocol scoring)
- **Landing Page** — Astro.js project scaffolded at `../landing_page/` for SEO-optimized marketing site (separate from the Vue SPA)

## Git Workflow
- `master` — production branch (deployed to Vercel)
- `dev` — development branch (backend + research modules)
- Feature branches: `feature/fastapi-backend`, `feature/python-research`, `feature/wearable-integration`
- **Do NOT push to GitHub** without explicit user permission
