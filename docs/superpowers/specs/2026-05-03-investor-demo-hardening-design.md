# Investor Demo Hardening Design

## Goal

Make the current working tree defensible for an investor demo by removing the highest-risk trust contradictions without starting a broad rewrite.

## Track 1: Investor-Demo Hardening

This pass fixes the issues that make the app look scientifically or operationally careless:

- Python tests must pass again.
- Space-weather outputs must remain explicitly observational and exploratory for individual predictions.
- The browser Supabase client must not persist OAuth sessions after the backend httpOnly session is established.
- Public lab endpoints must not claim "no user data" while accepting sleep, HRV, age, or travel inputs.
- Deployment docs and `.env.example` must stop instructing users to expose AQICN/NASA tokens as `VITE_*` frontend variables.

## Track 2: Production Security Roadmap

Parked for the next security phase:

- Move OAuth callback ownership fully to the backend so the browser never handles Supabase access tokens.
- Remove bearer-token fallback after the frontend has fully migrated to backend sessions.
- Replace in-memory/shared-key rate limiting with a durable store.
- Make session-ending idempotent under retries and duplicate requests.
- Stream wearable uploads, enforce tighter per-source size limits, and return import summaries instead of full raw logs.
- Add origin, CSRF, and session regression tests around all authenticated mutation routes.

## Track 3: Science Platform Roadmap

Parked for the next science phase:

- Collapse duplicated `research/` and `backend/research/` modules into one canonical package used by both tests and backend routes.
- Attach an evidence contract to every user-facing algorithm.
- Add supplement contraindication screening and stronger clinician-consult copy.
- Add wearable-derived confidence scoring so recommendations can distinguish measured, inferred, and missing data.
- Expand chronotype/light/jetlag validation notes with clear "validated vs exploratory" language.

## Acceptance Criteria

- Frontend build still passes.
- Frontend tests still pass.
- Backend/research Python tests pass.
- No public docs instruct users to place non-public AQICN/NASA tokens in `VITE_*`.
- OAuth callback does not leave a persisted Supabase browser session behind.
- Lab route comments accurately describe public vs personal-data route boundaries.
