-- ================================================================
-- HELIOS Biometrics Schema v2
-- PostgreSQL / Supabase (native, no TimescaleDB)
-- Run in Supabase SQL Editor AFTER schema.sql (v1)
-- All DDL is idempotent — safe to re-run
-- ================================================================

-- Extensions (pgvector already enabled in v1)
CREATE EXTENSION IF NOT EXISTS vector;
CREATE EXTENSION IF NOT EXISTS pgcrypto;

-- ================================================================
-- SECTION A: ENHANCE EXISTING TABLES
-- ================================================================

-- A1. users — body metrics, wearable IDs, pharmacokinetic fields
ALTER TABLE public.users
  ADD COLUMN IF NOT EXISTS usual_wake_time             TIME DEFAULT '07:00',
  ADD COLUMN IF NOT EXISTS height_cm                   FLOAT,
  ADD COLUMN IF NOT EXISTS weight_kg                   FLOAT,
  ADD COLUMN IF NOT EXISTS sex                         TEXT CHECK (sex IN ('male','female','other','prefer_not_to_say')),
  ADD COLUMN IF NOT EXISTS date_of_birth               DATE,
  ADD COLUMN IF NOT EXISTS oura_user_id                TEXT,
  ADD COLUMN IF NOT EXISTS fitbit_user_id              TEXT,
  ADD COLUMN IF NOT EXISTS garmin_user_id              TEXT,
  -- CaffeineModel personalisation (research/caffeine_model.py)
  ADD COLUMN IF NOT EXISTS cyp1a2_genotype             TEXT DEFAULT 'unknown'
    CHECK (cyp1a2_genotype IN ('fast','slow','unknown')),
  ADD COLUMN IF NOT EXISTS adora2a_sensitivity         TEXT DEFAULT 'unknown'
    CHECK (adora2a_sensitivity IN ('sensitive','insensitive','unknown')),
  ADD COLUMN IF NOT EXISTS is_smoker                   BOOLEAN DEFAULT false,
  ADD COLUMN IF NOT EXISTS uses_oral_contraceptive     BOOLEAN DEFAULT false,
  -- CircadianLightModel personalisation (research/light_model.py)
  ADD COLUMN IF NOT EXISTS is_light_sensitive          BOOLEAN DEFAULT false,
  -- AlcoholModel personalisation: Widmark r (0.68 male / 0.55 female)
  ADD COLUMN IF NOT EXISTS alcohol_distribution_factor FLOAT;

-- A2. sleep_logs — granular metrics missing from v1
ALTER TABLE public.sleep_logs
  ADD COLUMN IF NOT EXISTS sleep_latency_min     INT,
  ADD COLUMN IF NOT EXISTS light_sleep_min       INT,
  ADD COLUMN IF NOT EXISTS awake_min             INT,
  ADD COLUMN IF NOT EXISTS hrv_min               FLOAT,
  ADD COLUMN IF NOT EXISTS hrv_max               FLOAT,
  ADD COLUMN IF NOT EXISTS avg_hr                FLOAT,
  ADD COLUMN IF NOT EXISTS respiratory_rate_avg  FLOAT,
  ADD COLUMN IF NOT EXISTS spo2_avg              FLOAT,
  ADD COLUMN IF NOT EXISTS spo2_min              FLOAT,
  ADD COLUMN IF NOT EXISTS readiness_score       INT,
  ADD COLUMN IF NOT EXISTS nap_preceded          BOOLEAN DEFAULT false,
  ADD COLUMN IF NOT EXISTS alcohol_preceding     BOOLEAN DEFAULT false,
  ADD COLUMN IF NOT EXISTS import_id             UUID REFERENCES public.data_imports(id);

-- UNIQUE constraint for wearable upsert (on_conflict="user_id,date")
-- Note: ADD CONSTRAINT has no IF NOT EXISTS — use DO block for idempotency
DO $$ BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_constraint
    WHERE conname = 'sleep_logs_user_date_unique'
      AND conrelid = 'public.sleep_logs'::regclass
  ) THEN
    ALTER TABLE public.sleep_logs ADD CONSTRAINT sleep_logs_user_date_unique UNIQUE (user_id, date);
  END IF;
END $$;

-- A3. biometric_logs — expand metric enum, add sleep_log FK
ALTER TABLE public.biometric_logs
  DROP CONSTRAINT IF EXISTS biometric_logs_metric_check;

ALTER TABLE public.biometric_logs
  ADD CONSTRAINT biometric_logs_metric_check CHECK (metric IN (
    'hr', 'hrv_rmssd', 'hrv_sdnn', 'skin_temp', 'skin_temp_delta',
    'respiratory_rate', 'spo2', 'stress_score', 'body_battery', 'readiness'
  )),
  ADD COLUMN IF NOT EXISTS sleep_log_id UUID REFERENCES public.sleep_logs(id);

CREATE INDEX IF NOT EXISTS idx_biometric_logs_user_metric_ts
  ON public.biometric_logs(user_id, metric, timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_biometric_logs_sleep_log
  ON public.biometric_logs(sleep_log_id) WHERE sleep_log_id IS NOT NULL;

-- A4. data_imports — storage path and file size
ALTER TABLE public.data_imports
  ADD COLUMN IF NOT EXISTS storage_path    TEXT,
  ADD COLUMN IF NOT EXISTS file_size_bytes BIGINT,
  ADD COLUMN IF NOT EXISTS parsed_from     TIMESTAMPTZ,
  ADD COLUMN IF NOT EXISTS parsed_to       TIMESTAMPTZ;

-- ================================================================
-- SECTION B: NEW TABLES — Sleep Detail
-- ================================================================

-- B1. sleep_stages — intra-sleep stage breakdown (multiple rows per sleep_log)
CREATE TABLE IF NOT EXISTS public.sleep_stages (
  id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  sleep_log_id  UUID NOT NULL REFERENCES public.sleep_logs(id) ON DELETE CASCADE,
  user_id       UUID NOT NULL REFERENCES public.users(id) ON DELETE CASCADE,
  stage         TEXT NOT NULL CHECK (stage IN ('awake','light','deep','rem')),
  start_time    TIMESTAMPTZ NOT NULL,
  end_time      TIMESTAMPTZ NOT NULL,
  duration_min  INT NOT NULL,
  source        TEXT NOT NULL DEFAULT 'oura'
    CHECK (source IN ('manual','oura','fitbit','garmin','samsung','whoop','apple_health')),
  created_at    TIMESTAMPTZ DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_sleep_stages_log     ON public.sleep_stages(sleep_log_id);
CREATE INDEX IF NOT EXISTS idx_sleep_stages_user_ts ON public.sleep_stages(user_id, start_time DESC);
ALTER TABLE public.sleep_stages ENABLE ROW LEVEL SECURITY;
DO $$ BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_policies WHERE schemaname='public' AND tablename='sleep_stages' AND policyname='sleep_stages_user_rls') THEN
    CREATE POLICY sleep_stages_user_rls ON public.sleep_stages
      USING (user_id = auth.uid()) WITH CHECK (user_id = auth.uid());
  END IF;
END $$;

-- ================================================================
-- SECTION C: NEW TABLES — Behavioral Logs
-- ================================================================

-- C1. alcohol_logs — enables AlcoholModel.sleep_impact()
CREATE TABLE IF NOT EXISTS public.alcohol_logs (
  id               UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id          UUID NOT NULL REFERENCES public.users(id) ON DELETE CASCADE,
  drinks           FLOAT NOT NULL CHECK (drinks >= 0),
  drink_type       TEXT CHECK (drink_type IN ('beer','wine','spirits','mixed','other')),
  consumed_at      TIMESTAMPTZ NOT NULL,
  hours_before_bed FLOAT,
  bac_estimate     FLOAT,
  notes            TEXT,
  created_at       TIMESTAMPTZ DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_alcohol_logs_user_time ON public.alcohol_logs(user_id, consumed_at DESC);
ALTER TABLE public.alcohol_logs ENABLE ROW LEVEL SECURITY;
DO $$ BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_policies WHERE schemaname='public' AND tablename='alcohol_logs' AND policyname='alcohol_logs_user_rls') THEN
    CREATE POLICY alcohol_logs_user_rls ON public.alcohol_logs
      USING (user_id = auth.uid()) WITH CHECK (user_id = auth.uid());
  END IF;
END $$;

-- C2. breathwork_sessions — enables BreathworkModel.hrv_response()
CREATE TABLE IF NOT EXISTS public.breathwork_sessions (
  id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id         UUID NOT NULL REFERENCES public.users(id) ON DELETE CASCADE,
  started_at      TIMESTAMPTZ NOT NULL,
  ended_at        TIMESTAMPTZ,
  duration_min    INT,
  technique       TEXT NOT NULL CHECK (technique IN ('resonance','box','4-7-8','coherent','wim_hof','custom')),
  breaths_per_min FLOAT,
  target_bpm      FLOAT,
  hrv_before      FLOAT,
  hrv_after       FLOAT,
  hrv_delta       FLOAT,
  goal            TEXT CHECK (goal IN ('stress','sleep','focus','recovery')),
  notes           TEXT,
  created_at      TIMESTAMPTZ DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_breathwork_user_date ON public.breathwork_sessions(user_id, started_at DESC);
ALTER TABLE public.breathwork_sessions ENABLE ROW LEVEL SECURITY;
DO $$ BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_policies WHERE schemaname='public' AND tablename='breathwork_sessions' AND policyname='breathwork_sessions_user_rls') THEN
    CREATE POLICY breathwork_sessions_user_rls ON public.breathwork_sessions
      USING (user_id = auth.uid()) WITH CHECK (user_id = auth.uid());
  END IF;
END $$;

-- C3. nap_logs — enables NapModel.recommendation()
CREATE TABLE IF NOT EXISTS public.nap_logs (
  id                UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id           UUID NOT NULL REFERENCES public.users(id) ON DELETE CASCADE,
  started_at        TIMESTAMPTZ NOT NULL,
  ended_at          TIMESTAMPTZ,
  duration_min      INT,
  nap_type          TEXT CHECK (nap_type IN ('power','nasa_26','full_cycle','coffee_nap','unknown')),
  hours_after_wake  FLOAT,
  sleep_inertia_min INT,
  alertness_boost   TEXT CHECK (alertness_boost IN ('none','mild','moderate','strong')),
  followed_protocol BOOLEAN DEFAULT false,
  notes             TEXT,
  created_at        TIMESTAMPTZ DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_nap_logs_user_date ON public.nap_logs(user_id, started_at DESC);
ALTER TABLE public.nap_logs ENABLE ROW LEVEL SECURITY;
DO $$ BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_policies WHERE schemaname='public' AND tablename='nap_logs' AND policyname='nap_logs_user_rls') THEN
    CREATE POLICY nap_logs_user_rls ON public.nap_logs
      USING (user_id = auth.uid()) WITH CHECK (user_id = auth.uid());
  END IF;
END $$;

-- C4. light_exposure_logs — enables CircadianLightModel.melatonin_suppression()
CREATE TABLE IF NOT EXISTS public.light_exposure_logs (
  id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id             UUID NOT NULL REFERENCES public.users(id) ON DELETE CASCADE,
  logged_at           TIMESTAMPTZ NOT NULL,
  melanopic_edi_lux   FLOAT NOT NULL,
  source_type         TEXT NOT NULL CHECK (source_type IN ('outdoor','screen','indoor_cool','indoor_warm','lamp','unknown')),
  device_type         TEXT CHECK (device_type IN ('phone','tablet','laptop','tv','e-reader','bulb','other')),
  duration_min        INT,
  hours_before_sleep  FLOAT,
  zone                TEXT CHECK (zone IN ('daytime','evening','sleep')),
  notes               TEXT,
  created_at          TIMESTAMPTZ DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_light_logs_user_time ON public.light_exposure_logs(user_id, logged_at DESC);
ALTER TABLE public.light_exposure_logs ENABLE ROW LEVEL SECURITY;
DO $$ BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_policies WHERE schemaname='public' AND tablename='light_exposure_logs' AND policyname='light_logs_user_rls') THEN
    CREATE POLICY light_logs_user_rls ON public.light_exposure_logs
      USING (user_id = auth.uid()) WITH CHECK (user_id = auth.uid());
  END IF;
END $$;

-- C5. activity_logs — steps + intensity from wearables
CREATE TABLE IF NOT EXISTS public.activity_logs (
  id                     UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id                UUID NOT NULL REFERENCES public.users(id) ON DELETE CASCADE,
  date                   DATE NOT NULL,
  steps                  INT,
  active_calories        INT,
  total_calories         INT,
  active_min             INT,
  sedentary_min          INT,
  moderate_intensity_min INT,
  vigorous_intensity_min INT,
  peak_hr                INT,
  avg_daytime_hr         FLOAT,
  source                 TEXT NOT NULL DEFAULT 'manual'
    CHECK (source IN ('manual','oura','fitbit','garmin','samsung','whoop','apple_health')),
  import_id              UUID REFERENCES public.data_imports(id),
  created_at             TIMESTAMPTZ DEFAULT now(),
  UNIQUE(user_id, date, source)
);
CREATE INDEX IF NOT EXISTS idx_activity_logs_user_date ON public.activity_logs(user_id, date DESC);
ALTER TABLE public.activity_logs ENABLE ROW LEVEL SECURITY;
DO $$ BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_policies WHERE schemaname='public' AND tablename='activity_logs' AND policyname='activity_logs_user_rls') THEN
    CREATE POLICY activity_logs_user_rls ON public.activity_logs
      USING (user_id = auth.uid()) WITH CHECK (user_id = auth.uid());
  END IF;
END $$;

-- ================================================================
-- SECTION D: NEW TABLES — Protocol & Effectiveness
-- ================================================================

-- D1. protocol_effectiveness — ProtocolScorer output linked to actual sleep
CREATE TABLE IF NOT EXISTS public.protocol_effectiveness (
  id               UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id          UUID NOT NULL REFERENCES public.users(id) ON DELETE CASCADE,
  date             DATE NOT NULL,
  protocol_log_id  UUID REFERENCES public.protocol_logs(id),
  sleep_log_id     UUID REFERENCES public.sleep_logs(id),
  timing_score     FLOAT CHECK (timing_score BETWEEN 0 AND 1),
  duration_score   FLOAT CHECK (duration_score BETWEEN 0 AND 1),
  hrv_score        FLOAT CHECK (hrv_score BETWEEN 0 AND 1),
  deep_sleep_score FLOAT CHECK (deep_sleep_score BETWEEN 0 AND 1),
  rem_score        FLOAT CHECK (rem_score BETWEEN 0 AND 1),
  composite_score  FLOAT CHECK (composite_score BETWEEN 0 AND 1),
  kp_index         FLOAT,
  disruption_score INT,
  created_at       TIMESTAMPTZ DEFAULT now(),
  UNIQUE(user_id, date)
);
CREATE INDEX IF NOT EXISTS idx_effectiveness_user_date
  ON public.protocol_effectiveness(user_id, date DESC);
ALTER TABLE public.protocol_effectiveness ENABLE ROW LEVEL SECURITY;
DO $$ BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_policies WHERE schemaname='public' AND tablename='protocol_effectiveness' AND policyname='effectiveness_user_rls') THEN
    CREATE POLICY effectiveness_user_rls ON public.protocol_effectiveness
      USING (user_id = auth.uid()) WITH CHECK (user_id = auth.uid());
  END IF;
END $$;

-- ================================================================
-- SECTION E: NEW TABLES — Wearable Management
-- ================================================================

-- E1. wearable_connections — OAuth tokens + sync state per device
CREATE TABLE IF NOT EXISTS public.wearable_connections (
  id                      UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id                 UUID NOT NULL REFERENCES public.users(id) ON DELETE CASCADE,
  wearable                TEXT NOT NULL
    CHECK (wearable IN ('oura','fitbit','garmin','samsung','whoop','apple_health')),
  connection_type         TEXT NOT NULL CHECK (connection_type IN ('oauth','upload_only','api_key')),
  encrypted_access_token  TEXT,
  encrypted_refresh_token TEXT,
  token_expires_at        TIMESTAMPTZ,
  external_user_id        TEXT,
  last_sync_at            TIMESTAMPTZ,
  sync_status             TEXT DEFAULT 'idle'
    CHECK (sync_status IN ('idle','syncing','success','error','rate_limited')),
  sync_error              TEXT,
  records_synced          INT DEFAULT 0,
  is_active               BOOLEAN DEFAULT true,
  created_at              TIMESTAMPTZ DEFAULT now(),
  updated_at              TIMESTAMPTZ DEFAULT now(),
  UNIQUE(user_id, wearable)
);
CREATE INDEX IF NOT EXISTS idx_wearable_connections_user
  ON public.wearable_connections(user_id);
ALTER TABLE public.wearable_connections ENABLE ROW LEVEL SECURITY;
DO $$ BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_policies WHERE schemaname='public' AND tablename='wearable_connections' AND policyname='wearable_connections_user_rls') THEN
    CREATE POLICY wearable_connections_user_rls ON public.wearable_connections
      USING (user_id = auth.uid()) WITH CHECK (user_id = auth.uid());
  END IF;
END $$;

-- ================================================================
-- SECTION F: NEW TABLES — External Data Cache
-- ================================================================

-- F1. space_weather_cache — NOAA Kp/Bz archive for retrospective HRV correlation
-- No RLS — shared read-only table (no user_id)
CREATE TABLE IF NOT EXISTS public.space_weather_cache (
  id               UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  observed_at      TIMESTAMPTZ NOT NULL UNIQUE,
  kp_index         FLOAT NOT NULL,
  solar_wind_speed FLOAT,
  bz_component     FLOAT,
  disruption_score FLOAT,
  flare_class      TEXT,
  g_scale          INT CHECK (g_scale BETWEEN 0 AND 5),
  created_at       TIMESTAMPTZ DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_space_weather_ts
  ON public.space_weather_cache(observed_at DESC);

-- ================================================================
-- SECTION G: NEW TABLES — AI & Insights
-- ================================================================

-- G1. user_insights — computed circadian insight cards (persisted)
CREATE TABLE IF NOT EXISTS public.user_insights (
  id               UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id          UUID NOT NULL REFERENCES public.users(id) ON DELETE CASCADE,
  insight_type     TEXT NOT NULL
    CHECK (insight_type IN ('correlation','trend','adherence','anomaly','recommendation')),
  metric           TEXT NOT NULL,
  title            TEXT NOT NULL,
  body             TEXT NOT NULL,
  confidence       TEXT NOT NULL CHECK (confidence IN ('low','medium','high')),
  accent_hex       TEXT,
  data_window_days INT,
  expires_at       TIMESTAMPTZ,
  is_dismissed     BOOLEAN DEFAULT false,
  computed_at      TIMESTAMPTZ DEFAULT now(),
  created_at       TIMESTAMPTZ DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_insights_user_active
  ON public.user_insights(user_id, computed_at DESC)
  WHERE NOT is_dismissed;
ALTER TABLE public.user_insights ENABLE ROW LEVEL SECURITY;
DO $$ BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_policies WHERE schemaname='public' AND tablename='user_insights' AND policyname='insights_user_rls') THEN
    CREATE POLICY insights_user_rls ON public.user_insights
      USING (user_id = auth.uid()) WITH CHECK (user_id = auth.uid());
  END IF;
END $$;

-- G2. hermes_memories — pgvector embeddings (Phase 2 upgrade path)
-- Current Hermes uses plain markdown in user_memories; this enables semantic search later.
CREATE TABLE IF NOT EXISTS public.hermes_memories (
  id                UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id           UUID NOT NULL REFERENCES public.users(id) ON DELETE CASCADE,
  memory_text       TEXT NOT NULL,
  category          TEXT CHECK (category IN (
    'sleep','caffeine','light','adherence','biometrics','lifestyle','preference'
  )),
  embedding         vector(1536),
  source_session_id UUID REFERENCES public.chat_sessions(id),
  created_at        TIMESTAMPTZ DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_hermes_memories_user
  ON public.hermes_memories(user_id);
CREATE INDEX IF NOT EXISTS idx_hermes_memories_hnsw
  ON public.hermes_memories USING hnsw (embedding vector_l2_ops);
ALTER TABLE public.hermes_memories ENABLE ROW LEVEL SECURITY;
DO $$ BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_policies WHERE schemaname='public' AND tablename='hermes_memories' AND policyname='hermes_memories_user_rls') THEN
    CREATE POLICY hermes_memories_user_rls ON public.hermes_memories
      USING (user_id = auth.uid()) WITH CHECK (user_id = auth.uid());
  END IF;
END $$;

-- ================================================================
-- SECTION H: DASHBOARD PERFORMANCE TABLE
-- ================================================================

-- H1. daily_summaries — pre-aggregated daily metrics for O(1) dashboard queries
-- Auto-populated by trigger on sleep_logs INSERT/UPDATE
CREATE TABLE IF NOT EXISTS public.daily_summaries (
  id                UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id           UUID NOT NULL REFERENCES public.users(id) ON DELETE CASCADE,
  date              DATE NOT NULL,
  -- Sleep aggregate (from sleep_logs)
  total_sleep_min   INT,
  sleep_efficiency  FLOAT,
  deep_pct          FLOAT,
  rem_pct           FLOAT,
  light_pct         FLOAT,
  sleep_score       INT,
  readiness_score   INT,
  -- Biometric aggregate
  hrv_avg           FLOAT,
  hrv_7d_avg        FLOAT,
  hrv_vs_30d_mean   FLOAT,
  resting_hr        FLOAT,
  -- Space weather context
  kp_max            FLOAT,
  disruption_score  FLOAT,
  -- Protocol adherence
  sleep_delta_min   INT,
  wake_delta_min    INT,
  adherence_pct     INT,
  -- Behavioral
  caffeine_mg_total FLOAT,
  alcohol_drinks    FLOAT,
  steps             INT,
  computed_at       TIMESTAMPTZ DEFAULT now(),
  UNIQUE(user_id, date)
);
CREATE INDEX IF NOT EXISTS idx_daily_summaries_user_date
  ON public.daily_summaries(user_id, date DESC);
ALTER TABLE public.daily_summaries ENABLE ROW LEVEL SECURITY;
DO $$ BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_policies WHERE schemaname='public' AND tablename='daily_summaries' AND policyname='daily_summaries_user_rls') THEN
    CREATE POLICY daily_summaries_user_rls ON public.daily_summaries
      USING (user_id = auth.uid()) WITH CHECK (user_id = auth.uid());
  END IF;
END $$;

-- Enable Realtime on daily_summaries only (raw time-series tables are too high-volume)
DO $$ BEGIN
  ALTER PUBLICATION supabase_realtime ADD TABLE public.daily_summaries;
EXCEPTION WHEN OTHERS THEN
  NULL; -- already in publication
END $$;

-- ================================================================
-- SECTION I: TRIGGERS & FUNCTIONS
-- ================================================================

-- I1. Auto-update updated_at on users and wearable_connections
CREATE OR REPLACE FUNCTION public.update_updated_at()
RETURNS TRIGGER LANGUAGE plpgsql AS $$
BEGIN
  NEW.updated_at = now();
  RETURN NEW;
END;
$$;

CREATE OR REPLACE TRIGGER trg_users_updated_at
  BEFORE UPDATE ON public.users
  FOR EACH ROW EXECUTE FUNCTION public.update_updated_at();

CREATE OR REPLACE TRIGGER trg_wearable_connections_updated_at
  BEFORE UPDATE ON public.wearable_connections
  FOR EACH ROW EXECUTE FUNCTION public.update_updated_at();

-- I2. Auto-compute breathwork hrv_delta on INSERT/UPDATE
CREATE OR REPLACE FUNCTION public.set_breathwork_hrv_delta()
RETURNS TRIGGER LANGUAGE plpgsql AS $$
BEGIN
  IF NEW.hrv_before IS NOT NULL AND NEW.hrv_after IS NOT NULL THEN
    NEW.hrv_delta = NEW.hrv_after - NEW.hrv_before;
  END IF;
  RETURN NEW;
END;
$$;

CREATE OR REPLACE TRIGGER trg_breathwork_hrv_delta
  BEFORE INSERT OR UPDATE ON public.breathwork_sessions
  FOR EACH ROW EXECUTE FUNCTION public.set_breathwork_hrv_delta();

-- I3. Auto-refresh daily_summaries when sleep_log is inserted or updated
CREATE OR REPLACE FUNCTION public.refresh_daily_summary_from_sleep()
RETURNS TRIGGER LANGUAGE plpgsql AS $$
DECLARE
  v_time_in_bed_min INT;
  v_deep_pct        FLOAT;
  v_rem_pct         FLOAT;
  v_light_pct       FLOAT;
  v_efficiency      FLOAT;
BEGIN
  v_time_in_bed_min := EXTRACT(EPOCH FROM (NEW.wake_time - NEW.sleep_onset)) / 60;
  v_deep_pct   := CASE WHEN NEW.total_sleep_min > 0 THEN (COALESCE(NEW.deep_sleep_min,  0)::FLOAT / NEW.total_sleep_min * 100) ELSE NULL END;
  v_rem_pct    := CASE WHEN NEW.total_sleep_min > 0 THEN (COALESCE(NEW.rem_sleep_min,   0)::FLOAT / NEW.total_sleep_min * 100) ELSE NULL END;
  v_light_pct  := CASE WHEN NEW.total_sleep_min > 0 THEN (COALESCE(NEW.light_sleep_min, 0)::FLOAT / NEW.total_sleep_min * 100) ELSE NULL END;
  v_efficiency := CASE WHEN v_time_in_bed_min > 0 THEN (NEW.total_sleep_min::FLOAT / v_time_in_bed_min * 100) ELSE NULL END;

  INSERT INTO public.daily_summaries (
    user_id, date, total_sleep_min, sleep_efficiency,
    deep_pct, rem_pct, light_pct, sleep_score,
    readiness_score, hrv_avg, resting_hr, computed_at
  ) VALUES (
    NEW.user_id, NEW.date, NEW.total_sleep_min, v_efficiency,
    v_deep_pct, v_rem_pct, v_light_pct, NEW.sleep_score,
    NEW.readiness_score, NEW.hrv_avg, NEW.resting_hr, now()
  )
  ON CONFLICT (user_id, date) DO UPDATE SET
    total_sleep_min  = EXCLUDED.total_sleep_min,
    sleep_efficiency = EXCLUDED.sleep_efficiency,
    deep_pct         = EXCLUDED.deep_pct,
    rem_pct          = EXCLUDED.rem_pct,
    light_pct        = EXCLUDED.light_pct,
    sleep_score      = EXCLUDED.sleep_score,
    readiness_score  = EXCLUDED.readiness_score,
    hrv_avg          = EXCLUDED.hrv_avg,
    resting_hr       = EXCLUDED.resting_hr,
    computed_at      = now();

  RETURN NEW;
END;
$$;

CREATE OR REPLACE TRIGGER trg_sleep_log_daily_summary
  AFTER INSERT OR UPDATE ON public.sleep_logs
  FOR EACH ROW EXECUTE FUNCTION public.refresh_daily_summary_from_sleep();

-- ================================================================
-- SECTION J: SUPABASE STORAGE BUCKET (manual step — run in Dashboard)
-- ================================================================
-- Bucket name:  wearable-uploads
-- Access:       Private (not public)
-- Max size:     500 MB
-- Allowed MIME: application/zip, application/json, text/csv, application/octet-stream
--
-- RLS on storage.objects:
--   INSERT: auth.uid()::text = (storage.foldername(name))[1]
--   SELECT: auth.uid()::text = (storage.foldername(name))[1]
--   DELETE: auth.uid()::text = (storage.foldername(name))[1]
--
-- File path convention: {user_id}/{unix_timestamp}_{filename}
-- e.g. "a1b2c3d4.../1744300800_oura_export_2026.zip"
