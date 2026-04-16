# HELIOS Backend — Phases 3, 4, 5 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make Supabase persistence live (Phase 3), expose the wearable file upload endpoint (Phase 4), and wire the Python research modules as REST routes (Phase 5).

**Architecture:** The backend code for Phase 3 is already complete — `chat/router.py`, `memory/memory_service.py`, and `auth/session_service.py` all use `request.app.state.supabase`. Phase 3 is a deployment task: apply the SQL schema and set Railway env vars. Phase 4 creates a FastAPI router wrapping the already-implemented `OuraParser`. Phase 5 creates a circadian router that imports `ChronotypeEngine`, `ProtocolScorer`, and `SpaceWeatherBioModel` from `research/` and exposes them as authenticated GET routes.

**Tech Stack:** FastAPI, Supabase (Postgres + Auth), Python 3.11+, research modules in `research/` (numpy, dataclasses), `httpx` for LLM calls.

---

## Key Facts (Read Before Implementing)

- `backend/wearable/parsers/oura.py` is **fully implemented** — `OuraParser.parse_zip()` and `parse_json()` exist and work. Do NOT rewrite them.
- `backend/wearable/__init__.py` and `backend/wearable/parsers/__init__.py` already exist (empty).
- `backend/circadian/__init__.py` already exists (empty).
- `data_imports` table columns (from `schema.sql`): `id`, `user_id`, `filename`, `platform`, `uploaded_at`, `status` ('pending'|'processing'|'complete'|'failed'), `records_imported`, `error_message`.
- `sleep_logs` UNIQUE constraint on `(user_id, date)` is added by `schema_v2.sql` — required for upsert to work.
- `protocol_logs` has: `recommended_sleep TIMESTAMPTZ`, `actual_sleep TIMESTAMPTZ`, `recommended_wake TIMESTAMPTZ`, `actual_wake TIMESTAMPTZ`, `kp_index FLOAT`, `disruption_score INT`, `social_jet_lag_min INT`.
- The `OuraParser` uses a `sys.path.insert` hack to import `SleepLog` from `research/chronotype_engine.py`. The circadian router should do the same pattern from `backend/circadian/`.
- `SpaceWeatherBioModel` is in `research/space_weather_bio.py`. Read it before implementing the space-weather route — check the exact method name and signature (it's called `composite_disruption` but verify args).

---

## File Structure

**Create:**
- `backend/wearable/router.py` — Phase 4 upload endpoint
- `backend/circadian/router.py` — Phase 5 circadian routes

**Modify:**
- `backend/main.py` — uncomment Phase 4 and Phase 5 router includes
- `src/composables/useOuraUpload.ts` — wire real backend call in Phase 2 path

---

## Task 1: Apply Schema to Supabase (Phase 3)

**Files:** No code changes — Supabase SQL Editor only.

- [ ] **Step 1: Open Supabase SQL Editor**

  Navigate to your Supabase project → SQL Editor.

- [ ] **Step 2: Run core schema**

  Paste and run the full contents of `backend/schema.sql`.
  Expected: All tables created without errors. If tables already exist, the `IF NOT EXISTS` guards prevent errors.

- [ ] **Step 3: Run biometrics schema**

  Paste and run the full contents of `backend/schema_v2.sql`.
  Expected: 16 additional tables + triggers created without errors.
  Critical: This adds the `UNIQUE (user_id, date)` constraint on `sleep_logs` needed for Phase 4 upsert.

- [ ] **Step 4: Verify tables exist**

  In Supabase SQL Editor:
  ```sql
  SELECT table_name FROM information_schema.tables
  WHERE table_schema = 'public'
  ORDER BY table_name;
  ```
  Expected output includes: `app_sessions`, `chat_messages`, `chat_sessions`, `data_imports`,
  `daily_summaries`, `protocol_logs`, `sleep_logs`, `user_memories`, `users`, `wearable_connections`.

- [ ] **Step 5: Verify RLS is enabled**

  ```sql
  SELECT tablename, rowsecurity FROM pg_tables
  WHERE schemaname = 'public'
  ORDER BY tablename;
  ```
  Expected: `rowsecurity = true` for all user-data tables.

---

## Task 2: Set Railway Environment Variables (Phase 3)

**Files:** No code changes — Railway dashboard only.

- [ ] **Step 1: Open Railway service → Variables**

  Go to your Railway project → HELIOS backend service → Variables tab.

- [ ] **Step 2: Add / verify all required env vars**

  | Variable | Value |
  |---|---|
  | `SUPABASE_URL` | Your Supabase project URL (e.g. `https://xxx.supabase.co`) |
  | `SUPABASE_KEY` | Service role key (from Supabase → Settings → API) |
  | `SUPABASE_JWT_SECRET` | JWT secret (from Supabase → Settings → API) |
  | `ENCRYPTION_KEY` | Fernet key (generate: `python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"`) |
  | `SHARED_LLM_PROVIDER` | `gemini` |
  | `SHARED_LLM_KEY` | `481bda18fb4415a936602571e2ae1c34` |
  | `SHARED_LLM_RATE_LIMIT` | `20` |
  | `CORS_ORIGINS` | `http://localhost:5173,http://localhost:5174,https://helios-app-six.vercel.app` |

- [ ] **Step 3: Trigger redeploy and verify health**

  ```bash
  curl https://your-railway-backend.up.railway.app/api/health
  ```
  Expected: `{"status": "ok", "service": "helios-backend"}`

  If it fails with startup error: check that SUPABASE_URL and SUPABASE_KEY are set — `main.py` raises `RuntimeError` if either is missing.

---

## Task 3: Integration Smoke Test (Phase 3)

**Files:**
- Create: `backend/tests/test_supabase_integration.py` (manual/local run only — not CI)

- [ ] **Step 1: Write smoke test script**

  Create `backend/tests/test_supabase_integration.py`:

  ```python
  """
  Manual integration smoke test — Phase 3 Supabase wiring.
  Run from repo root: python -m backend.tests.test_supabase_integration

  Requires local .env with real Supabase credentials.
  NOT a unit test — hits real Supabase.
  """
  import asyncio
  import os
  from dotenv import load_dotenv
  from supabase import create_client

  load_dotenv()

  SUPABASE_URL = os.environ["SUPABASE_URL"]
  SUPABASE_KEY = os.environ["SUPABASE_KEY"]


  def test_tables_exist():
      db = create_client(SUPABASE_URL, SUPABASE_KEY)
      required = [
          "users", "user_memories", "app_sessions",
          "chat_sessions", "chat_messages",
          "sleep_logs", "data_imports", "shared_llm_usage",
      ]
      for table in required:
          result = db.table(table).select("id").limit(1).execute()
          # If table doesn't exist, supabase-py raises an exception
          print(f"  ✓ {table}")

  def test_memory_service():
      from backend.memory.memory_service import MemoryService
      db = create_client(SUPABASE_URL, SUPABASE_KEY)
      service = MemoryService(db)

      async def run():
          TEST_USER = "00000000-0000-0000-0000-000000000001"
          memory = await service.get_memory(TEST_USER)
          print(f"  ✓ get_memory returns {len(memory)} chars")
          formatted = await service.get_memory_for_prompt(TEST_USER)
          print(f"  ✓ get_memory_for_prompt returns {len(formatted)} chars (empty = ok for new user)")

      asyncio.run(run())


  if __name__ == "__main__":
      print("Phase 3 Smoke Test")
      print("─" * 40)
      print("Testing tables exist...")
      test_tables_exist()
      print("Testing memory service...")
      test_memory_service()
      print("─" * 40)
      print("All checks passed ✓")
  ```

- [ ] **Step 2: Run the smoke test**

  ```bash
  cd c:\Users\Acer\Desktop\Helios\helios-app
  python -m backend.tests.test_supabase_integration
  ```
  Expected: All checks pass. If `test_tables_exist` fails → schema not applied (go back to Task 1).

---

## Task 4: Create Wearable Upload Router (Phase 4)

**Files:**
- Create: `backend/wearable/router.py`

- [ ] **Step 1: Write the router**

  Create `backend/wearable/router.py`:

  ```python
  """
  HELIOS Backend — Wearable Upload Router
  POST /api/wearable/upload — accepts Oura Ring ZIP or JSON export.
  Parses with OuraParser (already implemented), upserts to sleep_logs.
  """

  import io
  import json
  import logging
  from datetime import datetime, UTC

  from fastapi import APIRouter, Depends, HTTPException, Request, UploadFile, File

  from backend.auth.supabase_auth import get_current_user_from_session
  from backend.wearable.parsers.oura import OuraParser

  logger = logging.getLogger(__name__)
  router = APIRouter()

  _MAX_FILE_BYTES = 100 * 1024 * 1024  # 100 MB


  def _sleep_log_to_row(log, user_id: str) -> dict:
      """
      Map OuraParser SleepLog dataclass to sleep_logs table columns.
      Note: SleepLog.alarm_used is intentionally omitted — schema.sql has no alarm_used column.
      Oura Ring exports don't provide alarm data anyway.
      """
      return {
          "user_id": user_id,
          "date": log.date,
          "sleep_onset": log.sleep_onset.isoformat(),
          "wake_time": log.wake_time.isoformat(),
          "total_sleep_min": log.total_sleep_min,
          "deep_sleep_min": log.deep_sleep_min,
          "rem_sleep_min": log.rem_sleep_min,
          "hrv_avg": log.hrv_avg,
          "skin_temp_delta": log.skin_temp_delta,
          "resting_hr": log.resting_hr,
          "sleep_score": log.sleep_score,
          "source": log.source or "oura",
      }


  @router.post("/upload")
  async def upload_wearable(
      request: Request,
      file: UploadFile = File(...),
      user_id: str = Depends(get_current_user_from_session),
  ):
      """
      Accept Oura Ring data export (.zip or .json).
      Parse into SleepLog records, upsert to sleep_logs, return summary.

      Conflict resolution: upsert on (user_id, date) — newer upload wins.
      Requires schema_v2.sql applied (adds UNIQUE constraint on sleep_logs).
      """
      if not file.filename:
          raise HTTPException(status_code=400, detail="No filename provided.")

      filename = file.filename.lower()
      if not (filename.endswith(".zip") or filename.endswith(".json")):
          raise HTTPException(status_code=400, detail="Upload must be a .zip or .json Oura export.")

      content = await file.read()
      if len(content) > _MAX_FILE_BYTES:
          raise HTTPException(status_code=413, detail="File exceeds 100 MB limit.")

      supabase = request.app.state.supabase
      parser = OuraParser()

      # Parse
      try:
          if filename.endswith(".zip"):
              logs = parser.parse_zip(io.BytesIO(content))
          else:
              data = json.loads(content.decode("utf-8"))
              logs = parser.parse_json(data)
      except Exception as e:
          logger.warning("[wearable] Parse failed for %s: %s", filename, e)
          raise HTTPException(status_code=422, detail=f"Could not parse file: {e}")

      if not logs:
          raise HTTPException(status_code=422, detail="No sleep records found in file.")

      # Record import
      import_result = supabase.table("data_imports").insert({
          "user_id": user_id,
          "filename": file.filename,
          "platform": "oura",
          "status": "processing",
          "records_imported": 0,
      }).execute()
      import_id = import_result.data[0]["id"]

      # Upsert sleep logs
      rows = [_sleep_log_to_row(log, user_id) for log in logs]
      try:
          supabase.table("sleep_logs").upsert(
              rows,
              on_conflict="user_id,date",
          ).execute()
      except Exception as e:
          logger.error("[wearable] sleep_logs upsert failed: %s", e)
          supabase.table("data_imports").update({
              "status": "failed",
              "error_message": str(e),
          }).eq("id", import_id).execute()
          raise HTTPException(status_code=500, detail="Failed to save sleep data.")

      # Mark import complete
      supabase.table("data_imports").update({
          "status": "complete",
          "records_imported": len(logs),
      }).eq("id", import_id).execute()

      return {
          "import_id": import_id,
          "records": len(logs),
          "date_range": {
              "from": min(log.date for log in logs),
              "to": max(log.date for log in logs),
          },
          "logs": [
              {
                  "date": log.date,
                  "total_sleep_min": log.total_sleep_min,
                  "hrv_avg": log.hrv_avg,
                  "sleep_score": log.sleep_score,
                  "source": log.source,
              }
              for log in logs
          ],
      }
  ```

- [ ] **Step 2: Verify imports resolve**

  ```bash
  cd c:\Users\Acer\Desktop\Helios\helios-app
  python -c "from backend.wearable.router import router; print('imports ok')"
  ```
  Expected: `imports ok`

---

## Task 5: Wire Wearable Router into main.py (Phase 4)

**Files:**
- Modify: `backend/main.py` lines 77-79

- [ ] **Step 1: Uncomment wearable router**

  In `backend/main.py`, replace:
  ```python
  # Phase 4: Wearable (uncomment when built)
  # from backend.wearable.router import router as wearable_router
  # app.include_router(wearable_router, prefix="/api/wearable", tags=["wearable"])
  ```
  With:
  ```python
  # Phase 4: Wearable
  from backend.wearable.router import router as wearable_router
  app.include_router(wearable_router, prefix="/api/wearable", tags=["wearable"])
  ```

- [ ] **Step 2: Verify server starts**

  ```bash
  cd c:\Users\Acer\Desktop\Helios\helios-app
  uvicorn backend.main:app --reload --port 8000
  ```
  Expected: Server starts, logs show `[helios] Supabase client initialized`.
  Check: `http://localhost:8000/docs` shows `/api/wearable/upload` route.

- [ ] **Step 3: Manual test with a sample file**

  If you have an Oura export ZIP, test with:
  ```bash
  # Get a session token first (via /api/auth/login), then:
  curl -X POST http://localhost:8000/api/wearable/upload \
    -H "Authorization: Bearer <jwt>" \
    -F "file=@oura_export.zip"
  ```
  Expected: `{"import_id": "...", "records": N, "date_range": {...}, "logs": [...]}`

---

## Task 6: Wire Frontend Upload to Real Endpoint (Phase 4)

**Files:**
- Modify: `src/composables/useOuraUpload.ts`

Current state: Always uses the mock 1.2s simulation (Phase 1).
Target: POST to `/api/wearable/upload`, fall back to mock if backend not available.

- [ ] **Step 1: Update useOuraUpload.ts**

  Replace `src/composables/useOuraUpload.ts` entirely:

  ```typescript
  import { useAuthStore } from '@/stores/auth'
  import { useBiometricsStore } from '@/stores/biometrics'
  import type { SleepLog } from '@/stores/biometrics'

  export function useOuraUpload() {
    const biometrics = useBiometricsStore()

    async function handleFile(file: File): Promise<void> {
      const ext = file.name.toLowerCase()
      if (!ext.endsWith('.zip') && !ext.endsWith('.json')) {
        biometrics.setUploadStatus('error', 'Unsupported file type. Upload a .zip or .json export.')
        return
      }

      biometrics.setUploadStatus('parsing')

      const auth = useAuthStore()
      const backendUrl = import.meta.env.VITE_BACKEND_URL ?? ''

      // Phase 2: real backend upload when authenticated
      if (auth.isAuthenticated && auth.csrfToken) {
        try {
          const formData = new FormData()
          formData.append('file', file)

          const response = await fetch(`${backendUrl}/api/wearable/upload`, {
            method: 'POST',
            credentials: 'include',
            headers: { 'X-HELIOS-CSRF': auth.csrfToken },
            body: formData,
          })

          if (response.ok) {
            const data = await response.json()
            // Map backend SleepLog shape to store SleepLog type
            const logs: SleepLog[] = (data.logs ?? []).map((l: Record<string, unknown>) => ({
              date: l.date as string,
              sleep_onset: l.sleep_onset as string ?? '',
              wake_time: l.wake_time as string ?? '',
              total_sleep_min: l.total_sleep_min as number ?? 0,
              hrv_avg: l.hrv_avg as number | undefined,
              sleep_score: l.sleep_score as number | undefined,
              source: 'oura' as const,
            }))
            biometrics.ingestParsedLogs(logs)
            return
          }

          const errorText = await response.text().catch(() => 'Upload failed')
          biometrics.setUploadStatus('error', errorText)
          return
        } catch {
          // Network error — fall through to mock
        }
      }

      // Phase 1 fallback: simulate parse, retag existing logs as oura
      await new Promise(resolve => setTimeout(resolve, 1200))
      const retagged: SleepLog[] = biometrics.logs.map(l => ({ ...l, source: 'oura' as const }))
      biometrics.ingestParsedLogs(retagged)
    }

    function reset() {
      biometrics.setUploadStatus('idle')
    }

    return { handleFile, reset }
  }
  ```

- [ ] **Step 2: Verify TypeScript compiles**

  ```bash
  cd c:\Users\Acer\Desktop\Helios\helios-app
  npm run build 2>&1 | grep -i "error"
  ```
  Expected: No TypeScript errors.

---

## Task 7: Create Circadian Router (Phase 5)

**Files:**
- Create: `backend/circadian/router.py`

Before writing, read `research/space_weather_bio.py` to confirm the exact class name and method signature for `composite_disruption`. The plan assumes `SpaceWeatherBioModel` with `composite_disruption(kp_index, bz_component, latitude)` — verify this matches.

- [ ] **Step 1: Check SpaceWeatherBioModel interface**

  ```bash
  python -c "
  import sys; sys.path.insert(0, 'research')
  from space_weather_bio import SpaceWeatherBioModel
  import inspect
  print(inspect.getmembers(SpaceWeatherBioModel, predicate=inspect.isfunction))
  "
  ```
  Note the exact method names and signatures. Update the router below if they differ.

- [ ] **Step 2: Write the circadian router**

  Create `backend/circadian/router.py`:

  ```python
  """
  HELIOS Backend — Circadian Research Routes
  Wraps Python research modules as FastAPI endpoints.

  Routes:
    GET /api/circadian/chronotype       — MCTQ chronotype from sleep_logs
    GET /api/circadian/protocol-score   — ProtocolScorer effectiveness from protocol_logs
    GET /api/circadian/space-weather    — SpaceWeatherBioModel advisory (public, no auth)
  """

  import sys
  import os
  import logging
  from datetime import datetime, UTC
  from typing import Optional

  from fastapi import APIRouter, Depends, HTTPException, Query, Request

  # Add research/ to path (same pattern as backend/wearable/parsers/oura.py)
  sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'research'))
  from chronotype_engine import ChronotypeEngine, ProtocolScorer, SleepLog, ProtocolLog
  from space_weather_bio import SpaceWeatherBioModel, SpaceWeatherReading

  from backend.auth.supabase_auth import get_current_user_from_session

  logger = logging.getLogger(__name__)
  router = APIRouter()


  # ─── Helpers ─────────────────────────────────────────────────────────────────

  def _row_to_sleep_log(row: dict) -> SleepLog:
      """Convert Supabase sleep_logs row to SleepLog dataclass."""
      return SleepLog(
          date=row["date"],
          sleep_onset=datetime.fromisoformat(row["sleep_onset"]),
          wake_time=datetime.fromisoformat(row["wake_time"]),
          total_sleep_min=row["total_sleep_min"],
          deep_sleep_min=row.get("deep_sleep_min"),
          rem_sleep_min=row.get("rem_sleep_min"),
          hrv_avg=row.get("hrv_avg"),
          skin_temp_delta=row.get("skin_temp_delta"),
          resting_hr=row.get("resting_hr"),
          sleep_score=row.get("sleep_score"),
          source=row.get("source", "manual"),
      )


  def _fetch_sleep_logs(supabase, user_id: str, days: int) -> list[SleepLog]:
      result = (
          supabase.table("sleep_logs")
          .select("*")
          .eq("user_id", user_id)
          .order("date", desc=True)
          .limit(days)
          .execute()
      )
      return [_row_to_sleep_log(row) for row in (result.data or [])]


  # ─── Chronotype ──────────────────────────────────────────────────────────────

  @router.get("/chronotype")
  async def get_chronotype(
      request: Request,
      days: int = Query(default=30, ge=7, le=90, description="Days of sleep data to analyse"),
      user_id: str = Depends(get_current_user_from_session),
  ):
      """
      Derive MCTQ chronotype (MSFsc, social jet lag) from uploaded sleep logs.
      Requires at least 7 days of data — 14+ recommended for high confidence.
      """
      supabase = request.app.state.supabase
      logs = _fetch_sleep_logs(supabase, user_id, days)

      if not logs:
          raise HTTPException(
              status_code=404,
              detail="No sleep data found. Upload an Oura export via POST /api/wearable/upload first.",
          )

      engine = ChronotypeEngine()
      return engine.chronotype_from_logs(logs)


  # ─── Protocol Score ───────────────────────────────────────────────────────────

  @router.get("/protocol-score")
  async def get_protocol_score(
      request: Request,
      days: int = Query(default=30, ge=7, le=90),
      user_id: str = Depends(get_current_user_from_session),
  ):
      """
      Score protocol effectiveness: HELIOS recommendations vs actual sleep outcomes.
      Requires both sleep_logs (from wearable) and protocol_logs (from app usage).
      """
      supabase = request.app.state.supabase

      # Fetch sleep logs
      sleep_logs = _fetch_sleep_logs(supabase, user_id, days)
      if not sleep_logs:
          raise HTTPException(status_code=404, detail="No sleep data found.")

      sleep_by_date = {log.date: log for log in sleep_logs}
      dates = list(sleep_by_date.keys())

      # Fetch protocol logs for the same dates
      proto_result = (
          supabase.table("protocol_logs")
          .select("*")
          .eq("user_id", user_id)
          .in_("date", dates)
          .execute()
      )
      proto_rows = proto_result.data or []

      if not proto_rows:
          raise HTTPException(
              status_code=404,
              detail=(
                  "No protocol data found for these dates. "
                  "Protocol adherence requires HELIOS to have been used for at least 7 days."
              ),
          )

      scorer = ProtocolScorer()
      daily_scores = []

      for row in proto_rows:
          date = row["date"]
          sleep = sleep_by_date.get(date)
          if not sleep or not row.get("recommended_sleep") or not row.get("recommended_wake"):
              continue

          protocol = ProtocolLog(
              date=date,
              recommended_sleep=datetime.fromisoformat(row["recommended_sleep"]),
              actual_sleep=sleep.sleep_onset,
              recommended_wake=datetime.fromisoformat(row["recommended_wake"]),
              actual_wake=sleep.wake_time,
              kp_index=float(row.get("kp_index") or 0.0),
              disruption_score=int(row.get("disruption_score") or 0),
              social_jet_lag_min=int(row.get("social_jet_lag_min") or 0),
          )
          score = scorer.effectiveness_score(protocol, sleep)
          daily_scores.append({"date": date, **score})

      if not daily_scores:
          raise HTTPException(status_code=422, detail="Could not compute scores — date overlap issue.")

      daily_scores.sort(key=lambda s: s["date"])
      trend = scorer.trend_analysis(daily_scores)

      return {
          "days_analysed": len(daily_scores),
          "trend": trend,
          "daily_scores": daily_scores,
      }


  # ─── Space Weather Advisory (public — no auth required) ──────────────────────

  @router.get("/space-weather")
  async def get_space_weather_advisory(
      kp: float = Query(..., ge=0.0, le=9.0, description="Current Kp index (0–9)"),
      bz: float = Query(default=0.0, description="IMF Bz component in nanoTesla (negative = southward)"),
      sw_speed: float = Query(default=400.0, ge=200.0, le=900.0, description="Solar wind speed km/s (default 400)"),
      lat: float = Query(default=45.0, ge=-90.0, le=90.0, description="Observer latitude (default mid-latitude 45°N)"),
  ):
      """
      Public endpoint — no authentication required.
      Returns biological advisory for current space weather conditions.

      SpaceWeatherReading fields (research/space_weather_bio.py):
        kp_index: float, solar_wind_speed: float, bz: float, timestamp: datetime, latitude: float = 45.0
      composite_disruption() takes a single SpaceWeatherReading object — NOT keyword args.
      """
      try:
          reading = SpaceWeatherReading(
              kp_index=kp,
              solar_wind_speed=sw_speed,
              bz=bz,
              timestamp=datetime.now(UTC),
              latitude=lat,
          )
          model = SpaceWeatherBioModel()
          result = model.composite_disruption(reading)
          return result
      except Exception as e:
          logger.error("[circadian] Space weather model error: %s", e)
          raise HTTPException(status_code=500, detail="Space weather model error.")
  ```

- [ ] **Step 3: Verify imports resolve**

  ```bash
  cd c:\Users\Acer\Desktop\Helios\helios-app
  python -c "from backend.circadian.router import router; print('imports ok')"
  ```
  Expected: `imports ok`

  If `SpaceWeatherBioModel` import fails: check that `research/space_weather_bio.py` exists and that the class name is correct.

---

## Task 8: Wire Circadian Router into main.py + Final Verification (Phase 5)

**Files:**
- Modify: `backend/main.py` lines 81-83

- [ ] **Step 1: Uncomment circadian router**

  In `backend/main.py`, the current commented-out line (line 83) has `prefix="/api"` — this is the placeholder that was written before the router existed. Replace the three commented lines with the correct prefix `/api/circadian`:
  ```python
  # Phase 5: Circadian (uncomment when built)
  # from backend.circadian.router import router as circadian_router
  # app.include_router(circadian_router, prefix="/api", tags=["circadian"])
  ```
  With:
  ```python
  # Phase 5: Circadian
  from backend.circadian.router import router as circadian_router
  app.include_router(circadian_router, prefix="/api/circadian", tags=["circadian"])
  ```

  **Why `/api/circadian` not `/api`**: The router registers paths like `/chronotype`, `/protocol-score`, `/space-weather`. With `prefix="/api/circadian"`, full paths become `/api/circadian/chronotype` etc. Using `prefix="/api"` would produce `/api/chronotype` which would conflict with other routes.

- [ ] **Step 2: Start server and verify all routes appear**

  ```bash
  uvicorn backend.main:app --reload --port 8000
  ```
  Check `http://localhost:8000/docs` shows:
  - `POST /api/wearable/upload`
  - `GET /api/circadian/chronotype`
  - `GET /api/circadian/protocol-score`
  - `GET /api/circadian/space-weather`

- [ ] **Step 3: Smoke test space-weather route (public)**

  ```bash
  curl "http://localhost:8000/api/circadian/space-weather?kp=3.5&lat=42"
  ```
  Expected: JSON with disruption advisory fields (not a 500 error).

  If 500 with "Model signature error": read `research/space_weather_bio.py` and fix the `composite_disruption()` call signature in `router.py`.

- [ ] **Step 4: Update CLAUDE.md phase status**

  In `helios-app/CLAUDE.md`, under "Backend Phase Status", update:
  - Phase 3: Change status to `**Built** — schema applied, Supabase wired end-to-end`
  - Phase 4: Change status to `**Built** — POST /api/wearable/upload wraps OuraParser`
  - Phase 5: Change status to `**Built** — /chronotype, /protocol-score, /space-weather routes live`

---

## Verification Checklist

After all 8 tasks, verify end-to-end:

- [ ] `GET /api/health` → `{"status": "ok"}`
- [ ] Send a chat message → Supabase `chat_sessions` row created
- [ ] End session → Supabase `chat_sessions.ended_at` set, Hermes processes in background
- [ ] `GET /api/chat/memory` → returns memory markdown (may be default for new user)
- [ ] `POST /api/wearable/upload` with Oura ZIP → `{"records": N, ...}`
- [ ] `GET /api/circadian/chronotype?days=30` → chronotype result (after upload)
- [ ] `GET /api/circadian/protocol-score` → 404 until protocol_logs populated (expected)
- [ ] `GET /api/circadian/space-weather?kp=5.0` → advisory JSON (public, no auth)

---

## Known Gaps (Post-Phase-5)

- **Wearable frontend mapping**: `useOuraUpload.ts` maps the full SleepLog response shape. Backend returns a summary (date, total_sleep_min, hrv_avg, sleep_score). Frontend `SleepLog` interface requires all fields — the biometrics store's `ingestParsedLogs` expects complete records. After Phase 4 goes live, fetch full sleep_logs from a new `GET /api/biometrics/sleep-logs` endpoint instead of using the upload response.
- **Protocol logs not yet written**: `/api/circadian/protocol-score` will return 404 until the frontend writes protocol_logs to Supabase. This requires wiring the protocol store to POST each day's recommendations on app load.
- **Space-weather route signature**: `SpaceWeatherBioModel.composite_disruption()` signature must be verified against `research/space_weather_bio.py` — the plan uses the expected interface but the class may have changed since the last refactor.
