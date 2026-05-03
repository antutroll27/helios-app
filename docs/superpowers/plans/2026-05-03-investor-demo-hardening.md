# Investor Demo Hardening Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Remove the highest-risk security, privacy, science, and documentation contradictions before the next demo.

**Architecture:** Keep the current frontend/backend split. Patch only the auth callback, lab route boundary, science copy, tests, and deployment docs needed to restore credibility.

**Tech Stack:** Vue 3, Pinia, Supabase JS, FastAPI, pytest, Vitest, Vite.

---

### Task 1: Auth Callback Browser Session Boundary

**Files:**
- Modify: `src/lib/supabase.ts`
- Modify: `src/pages/AuthCallbackPage.vue`

- [x] Add `persistSession: false` to the Supabase client auth config.
- [x] After exchanging the PKCE code and sending the Supabase access token to `/api/auth/oauth`, call `supabase.auth.signOut({ scope: 'local' })`.
- [x] Restrict stored redirect targets to app-local absolute paths.
- [x] Fix mojibake in the callback loading/error copy.
- [x] Run `npm run test -- --run`.

### Task 2: Lab Route Privacy Boundary

**Files:**
- Modify: `backend/lab/router.py`

- [x] Update module documentation so only generic calculators are called public.
- [x] Add authenticated user dependency to routes accepting user health-adjacent inputs: `/supplements`, `/sleep-regularity`, `/nocturnal-hrv`, and `/jetlag-plan`.
- [x] Keep generic public calculators public: `/exercise-timing`, `/meal-window`, and `/cold-exposure`.
- [x] Run Python tests and add/adjust route tests if failures expose expected auth behavior gaps.

### Task 3: Science Wording and Test Drift

**Files:**
- Modify: `backend/tests/test_auth_router.py`
- Modify: `research/space_weather_bio.py`

- [x] Update the auth test fake to support Supabase-style `upsert`.
- [x] Restore "uncertain individual relevance" language to cognitive advisory outputs.
- [x] Label composite disruption as `exploratory_heuristic`.
- [x] Ensure composite advisory and evidence profile state "not validated for individual prediction" and "context only".
- [x] Run `python -m pytest backend/tests research/tests -q`.

### Task 4: Deployment Docs and Env Guidance

**Files:**
- Modify: `.env.example`
- Modify: `docs/deploy-cloudflare-pages.md`

- [x] Replace `VITE_AQICN_TOKEN` and `VITE_NASA_API_KEY` with backend-owned `AQICN_TOKEN` and `NASA_API_KEY`.
- [x] Remove frontend Cloudflare Pages instructions for AQICN/NASA tokens.
- [x] Add a short note that source tokens belong in backend/Railway env vars, not the browser bundle.

### Task 5: Verification

**Commands:**
- `npm run build`
- `npm run test -- --run`
- `python -m pytest backend/tests research/tests -q`

- [x] Record pass/fail status.
- [x] Summarize any remaining production-security and science-platform work under Tracks 2 and 3.
