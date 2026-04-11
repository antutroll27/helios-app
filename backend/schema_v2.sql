-- ============================================================
-- HELIOS — schema_v2.sql
-- Additive migration on top of schema.sql
-- Run in Supabase SQL Editor AFTER schema.sql has been applied
-- DO NOT drop or recreate any existing tables
-- ============================================================

-- Ensure required extensions are present (idempotent)
CREATE EXTENSION IF NOT EXISTS vector;
CREATE EXTENSION IF NOT EXISTS pgcrypto;


-- ============================================================
-- SECTION A: ALTER EXISTING TABLES
-- ============================================================

-- ────────────────────────────────────────────────────────────
-- A1. public.users — new columns
-- ────────────────────────────────────────────────────────────

ALTER TABLE public.users ADD COLUMN IF NOT EXISTS usual_wake_time          TIME    DEFAULT '07:00';
ALTER TABLE public.users ADD COLUMN IF NOT EXISTS height_cm                FLOAT;
ALTER TABLE public.users ADD COLUMN IF NOT EXISTS weight_kg                FLOAT;
ALTER TABLE public.users ADD COLUMN IF NOT EXISTS sex                      TEXT    CHECK (sex IN ('male','female','other','prefer_not_to_say'));
ALTER TABLE public.users ADD COLUMN IF NOT EXISTS date_of_birth            DATE;
ALTER TABLE public.users ADD COLUMN IF NOT EXISTS oura_user_id             TEXT;
ALTER TABLE public.users ADD COLUMN IF NOT EXISTS fitbit_user_id           TEXT;
ALTER TABLE public.users ADD COLUMN IF NOT EXISTS garmin_user_id           TEXT;

-- CaffeineModel personalisation
ALTER TABLE public.users ADD COLUMN IF NOT EXISTS cyp1a2_genotype          TEXT    DEFAULT 'unknown'
    CHECK (cyp1a2_genotype IN ('fast','slow','unknown'));
ALTER TABLE public.users ADD COLUMN IF NOT EXISTS adora2a_sensitivity      TEXT    DEFAULT 'unknown'
    CHECK (adora2a_sensitivity IN ('sensitive','insensitive','unknown'));

-- Caffeine half-life modifiers
ALTER TABLE public.users ADD COLUMN IF NOT EXISTS is_smoker                BOOLEAN DEFAULT false;
ALTER TABLE public.users ADD COLUMN IF NOT EXISTS uses_oral_contraceptive  BOOLEAN DEFAULT false;

-- CircadianLightModel
ALTER TABLE public.users ADD COLUMN IF NOT EXISTS is_light_sensitive       BOOLEAN DEFAULT false;

-- AlcoholModel — Widmark r factor (0.68 male / 0.55 female)
ALTER TABLE public.users ADD COLUMN IF NOT EXISTS alcohol_distribution_factor FLOAT;


-- ────────────────────────────────────────────────────────────
-- A2. public.sleep_logs — new columns + unique constraint
-- ────────────────────────────────────────────────────────────

ALTER TABLE public.sleep_logs ADD COLUMN IF NOT EXISTS sleep_latency_min       INT;
ALTER TABLE public.sleep_logs ADD COLUMN IF NOT EXISTS light_sleep_min         INT;
ALTER TABLE public.sleep_logs ADD COLUMN IF NOT EXISTS awake_min               INT;
ALTER TABLE public.sleep_logs ADD COLUMN IF NOT EXISTS hrv_min                 FLOAT;
ALTER TABLE public.sleep_logs ADD COLUMN IF NOT EXISTS hrv_max                 FLOAT;
ALTER TABLE public.sleep_logs ADD COLUMN IF NOT EXISTS avg_hr                  FLOAT;
ALTER TABLE public.sleep_logs ADD COLUMN IF NOT EXISTS respiratory_rate_avg    FLOAT;
ALTER TABLE public.sleep_logs ADD COLUMN IF NOT EXISTS spo2_avg                FLOAT;
ALTER TABLE public.sleep_logs ADD COLUMN IF NOT EXISTS spo2_min                FLOAT;
ALTER TABLE public.sleep_logs ADD COLUMN IF NOT EXISTS readiness_score         INT;
ALTER TABLE public.sleep_logs ADD COLUMN IF NOT EXISTS nap_preceded            BOOLEAN DEFAULT false;
ALTER TABLE public.sleep_logs ADD COLUMN IF NOT EXISTS alcohol_preceding       BOOLEAN DEFAULT false;
ALTER TABLE public.sleep_logs ADD COLUMN IF NOT EXISTS import_id               UUID    REFERENCES public.data_imports(id);

-- Prevent duplicate records per user per calendar date
DO $$ BEGIN
    ALTER TABLE public.sleep_logs
        ADD CONSTRAINT sleep_logs_user_date_unique UNIQUE (user_id, date);
EXCEPTION
    WHEN duplicate_table THEN NULL;   -- Postgres raises duplicate_table for duplicate constraints
    WHEN others          THEN RAISE;
END $$;


-- ────────────────────────────────────────────────────────────
-- A3. public.biometric_logs — expanded metric CHECK + new column + indexes
-- ────────────────────────────────────────────────────────────

-- Replace the old metric CHECK constraint with an expanded set
DO $$ BEGIN
    ALTER TABLE public.biometric_logs
        DROP CONSTRAINT biometric_logs_metric_check;
EXCEPTION
    WHEN undefined_object THEN NULL;  -- already dropped or never existed under this name
    WHEN others           THEN RAISE;
END $$;

DO $$ BEGIN
    ALTER TABLE public.biometric_logs
        ADD CONSTRAINT biometric_logs_metric_check
        CHECK (metric IN (
            'hr','hrv_rmssd','hrv_sdnn',
            'skin_temp','skin_temp_delta',
            'respiratory_rate','spo2',
            'stress_score','body_battery','readiness'
        ));
EXCEPTION
    WHEN duplicate_object THEN NULL;
    WHEN others           THEN RAISE;
END $$;

ALTER TABLE public.biometric_logs ADD COLUMN IF NOT EXISTS sleep_log_id UUID REFERENCES public.sleep_logs(id);

-- Replace the original single-column index with a composite covering (user, metric, ts DESC)
DROP INDEX IF EXISTS idx_biometric_logs_user_metric;

CREATE INDEX IF NOT EXISTS idx_biometric_logs_user_metric_ts
    ON public.biometric_logs(user_id, metric, timestamp DESC);

CREATE INDEX IF NOT EXISTS idx_biometric_logs_sleep_log
    ON public.biometric_logs(sleep_log_id)
    WHERE sleep_log_id IS NOT NULL;


-- ────────────────────────────────────────────────────────────
-- A4. public.data_imports — new columns
-- ────────────────────────────────────────────────────────────

ALTER TABLE public.data_imports ADD COLUMN IF NOT EXISTS storage_path      TEXT;
ALTER TABLE public.data_imports ADD COLUMN IF NOT EXISTS file_size_bytes   BIGINT;
ALTER TABLE public.data_imports ADD COLUMN IF NOT EXISTS parsed_from       TIMESTAMPTZ;
ALTER TABLE public.data_imports ADD COLUMN IF NOT EXISTS parsed_to         TIMESTAMPTZ;


-- ============================================================
-- SECTION B: sleep_stages
-- Granular per-epoch sleep stage data from wearables
-- ============================================================

CREATE TABLE IF NOT EXISTS public.sleep_stages (
    id            UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
    sleep_log_id  UUID        NOT NULL REFERENCES public.sleep_logs(id) ON DELETE CASCADE,
    user_id       UUID        NOT NULL REFERENCES public.users(id) ON DELETE CASCADE,
    stage         TEXT        NOT NULL CHECK (stage IN ('awake','light','deep','rem')),
    start_time    TIMESTAMPTZ NOT NULL,
    end_time      TIMESTAMPTZ NOT NULL,
    duration_min  INT         NOT NULL,
    source        TEXT        NOT NULL DEFAULT 'oura'
                              CHECK (source IN ('manual','oura','fitbit','garmin','samsung','whoop','apple_health')),
    created_at    TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_sleep_stages_log
    ON public.sleep_stages(sleep_log_id);

CREATE INDEX IF NOT EXISTS idx_sleep_stages_user_ts
    ON public.sleep_stages(user_id, start_time DESC);

ALTER TABLE public.sleep_stages ENABLE ROW LEVEL SECURITY;

CREATE POLICY "sleep_stages_user_rls" ON public.sleep_stages
    USING  (user_id = auth.uid())
    WITH CHECK (user_id = auth.uid());


-- ============================================================
-- SECTION C: Behavioral logs
-- ============================================================

-- ────────────────────────────────────────────────────────────
-- C1. alcohol_logs
-- Tracks alcohol intake; feeds AlcoholModel BAC simulation
-- ────────────────────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS public.alcohol_logs (
    id                UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id           UUID        NOT NULL REFERENCES public.users(id) ON DELETE CASCADE,
    drinks            FLOAT       NOT NULL CHECK (drinks >= 0),
    drink_type        TEXT        CHECK (drink_type IN ('beer','wine','spirits','mixed','other')),
    consumed_at       TIMESTAMPTZ NOT NULL,
    hours_before_bed  FLOAT,
    bac_estimate      FLOAT,
    notes             TEXT,
    created_at        TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_alcohol_logs_user_ts
    ON public.alcohol_logs(user_id, consumed_at DESC);

ALTER TABLE public.alcohol_logs ENABLE ROW LEVEL SECURITY;

CREATE POLICY "alcohol_logs_user_rls" ON public.alcohol_logs
    USING  (user_id = auth.uid())
    WITH CHECK (user_id = auth.uid());


-- ────────────────────────────────────────────────────────────
-- C2. breathwork_sessions
-- Feeds BreathworkModel HRV dose-response tracking
-- (Laborde 2022 meta-analysis — resonance at 5.5 bpm)
-- ────────────────────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS public.breathwork_sessions (
    id            UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id       UUID        NOT NULL REFERENCES public.users(id) ON DELETE CASCADE,
    started_at    TIMESTAMPTZ NOT NULL,
    ended_at      TIMESTAMPTZ,
    duration_min  INT,
    technique     TEXT        NOT NULL
                              CHECK (technique IN ('resonance','box','4-7-8','coherent','wim_hof','custom')),
    breaths_per_min  FLOAT,
    target_bpm       FLOAT,
    hrv_before       FLOAT,
    hrv_after        FLOAT,
    hrv_delta        FLOAT,   -- computed by trigger; can also be set manually
    goal          TEXT        CHECK (goal IN ('stress','sleep','focus','recovery')),
    notes         TEXT,
    created_at    TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_breathwork_user_ts
    ON public.breathwork_sessions(user_id, started_at DESC);

ALTER TABLE public.breathwork_sessions ENABLE ROW LEVEL SECURITY;

CREATE POLICY "breathwork_sessions_user_rls" ON public.breathwork_sessions
    USING  (user_id = auth.uid())
    WITH CHECK (user_id = auth.uid());


-- ────────────────────────────────────────────────────────────
-- C3. nap_logs
-- Tracks naps; feeds NapModel (NASA 26-min, coffee nap, etc.)
-- ────────────────────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS public.nap_logs (
    id                  UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id             UUID        NOT NULL REFERENCES public.users(id) ON DELETE CASCADE,
    started_at          TIMESTAMPTZ NOT NULL,
    ended_at            TIMESTAMPTZ,
    duration_min        INT,
    nap_type            TEXT        CHECK (nap_type IN ('power','nasa_26','full_cycle','coffee_nap','unknown')),
    hours_after_wake    FLOAT,
    sleep_inertia_min   INT,
    alertness_boost     TEXT        CHECK (alertness_boost IN ('none','mild','moderate','strong')),
    followed_protocol   BOOLEAN     DEFAULT false,
    notes               TEXT,
    created_at          TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_nap_logs_user_ts
    ON public.nap_logs(user_id, started_at DESC);

ALTER TABLE public.nap_logs ENABLE ROW LEVEL SECURITY;

CREATE POLICY "nap_logs_user_rls" ON public.nap_logs
    USING  (user_id = auth.uid())
    WITH CHECK (user_id = auth.uid());


-- ────────────────────────────────────────────────────────────
-- C4. light_exposure_logs
-- Feeds CircadianLightModel (Brown 2022, Gimenez 2022)
-- ────────────────────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS public.light_exposure_logs (
    id                   UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id              UUID        NOT NULL REFERENCES public.users(id) ON DELETE CASCADE,
    logged_at            TIMESTAMPTZ NOT NULL,
    melanopic_edi_lux    FLOAT       NOT NULL,
    source_type          TEXT        NOT NULL
                                     CHECK (source_type IN ('outdoor','screen','indoor_cool','indoor_warm','lamp','unknown')),
    device_type          TEXT        CHECK (device_type IN ('phone','tablet','laptop','tv','e-reader','bulb','other')),
    duration_min         INT,
    hours_before_sleep   FLOAT,
    zone                 TEXT        CHECK (zone IN ('daytime','evening','sleep')),
    notes                TEXT,
    created_at           TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_light_exposure_user_ts
    ON public.light_exposure_logs(user_id, logged_at DESC);

ALTER TABLE public.light_exposure_logs ENABLE ROW LEVEL SECURITY;

CREATE POLICY "light_exposure_logs_user_rls" ON public.light_exposure_logs
    USING  (user_id = auth.uid())
    WITH CHECK (user_id = auth.uid());


-- ────────────────────────────────────────────────────────────
-- C5. activity_logs
-- Daily activity summary from wearables; supports cross-
-- source deduplication via UNIQUE(user_id, date, source)
-- ────────────────────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS public.activity_logs (
    id                       UUID    PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id                  UUID    NOT NULL REFERENCES public.users(id) ON DELETE CASCADE,
    date                     DATE    NOT NULL,
    steps                    INT,
    active_calories          INT,
    total_calories           INT,
    active_min               INT,
    sedentary_min            INT,
    moderate_intensity_min   INT,
    vigorous_intensity_min   INT,
    peak_hr                  INT,
    avg_daytime_hr           FLOAT,
    source                   TEXT    NOT NULL DEFAULT 'manual'
                                     CHECK (source IN ('manual','oura','fitbit','garmin','samsung','whoop','apple_health')),
    import_id                UUID    REFERENCES public.data_imports(id),
    created_at               TIMESTAMPTZ DEFAULT now(),
    UNIQUE(user_id, date, source)
);

CREATE INDEX IF NOT EXISTS idx_activity_logs_user_date
    ON public.activity_logs(user_id, date DESC);

ALTER TABLE public.activity_logs ENABLE ROW LEVEL SECURITY;

CREATE POLICY "activity_logs_user_rls" ON public.activity_logs
    USING  (user_id = auth.uid())
    WITH CHECK (user_id = auth.uid());


-- ============================================================
-- SECTION D: protocol_effectiveness
-- Outcome tracking — did following the protocol improve sleep?
-- ============================================================

CREATE TABLE IF NOT EXISTS public.protocol_effectiveness (
    id                UUID    PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id           UUID    NOT NULL REFERENCES public.users(id) ON DELETE CASCADE,
    date              DATE    NOT NULL,
    protocol_log_id   UUID    REFERENCES public.protocol_logs(id),
    sleep_log_id      UUID    REFERENCES public.sleep_logs(id),
    timing_score      FLOAT   CHECK (timing_score    BETWEEN 0 AND 1),
    duration_score    FLOAT   CHECK (duration_score  BETWEEN 0 AND 1),
    hrv_score         FLOAT   CHECK (hrv_score       BETWEEN 0 AND 1),
    deep_sleep_score  FLOAT   CHECK (deep_sleep_score BETWEEN 0 AND 1),
    rem_score         FLOAT   CHECK (rem_score       BETWEEN 0 AND 1),
    composite_score   FLOAT   CHECK (composite_score BETWEEN 0 AND 1),
    kp_index          FLOAT,
    disruption_score  INT,
    created_at        TIMESTAMPTZ DEFAULT now(),
    UNIQUE(user_id, date)
);

CREATE INDEX IF NOT EXISTS idx_protocol_effectiveness_user_date
    ON public.protocol_effectiveness(user_id, date DESC);

ALTER TABLE public.protocol_effectiveness ENABLE ROW LEVEL SECURITY;

CREATE POLICY "protocol_effectiveness_user_rls" ON public.protocol_effectiveness
    USING  (user_id = auth.uid())
    WITH CHECK (user_id = auth.uid());


-- ============================================================
-- SECTION E: wearable_connections
-- OAuth / upload-only connection state per user per device
-- ============================================================

CREATE TABLE IF NOT EXISTS public.wearable_connections (
    id                      UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id                 UUID        NOT NULL REFERENCES public.users(id) ON DELETE CASCADE,
    wearable                TEXT        NOT NULL
                                        CHECK (wearable IN ('oura','fitbit','garmin','samsung','whoop','apple_health')),
    connection_type         TEXT        NOT NULL
                                        CHECK (connection_type IN ('oauth','upload_only','api_key')),
    encrypted_access_token  TEXT,
    encrypted_refresh_token TEXT,
    token_expires_at        TIMESTAMPTZ,
    external_user_id        TEXT,
    last_sync_at            TIMESTAMPTZ,
    sync_status             TEXT        DEFAULT 'idle'
                                        CHECK (sync_status IN ('idle','syncing','success','error','rate_limited')),
    sync_error              TEXT,
    records_synced          INT         DEFAULT 0,
    is_active               BOOLEAN     DEFAULT true,
    created_at              TIMESTAMPTZ DEFAULT now(),
    updated_at              TIMESTAMPTZ DEFAULT now(),
    UNIQUE(user_id, wearable)
);

CREATE INDEX IF NOT EXISTS idx_wearable_connections_user
    ON public.wearable_connections(user_id);

ALTER TABLE public.wearable_connections ENABLE ROW LEVEL SECURITY;

CREATE POLICY "wearable_connections_user_rls" ON public.wearable_connections
    USING  (user_id = auth.uid())
    WITH CHECK (user_id = auth.uid());


-- ============================================================
-- SECTION F: space_weather_cache
-- Shared, read-only cache populated by the FastAPI background
-- worker. No RLS — all authenticated users may read.
-- ============================================================

CREATE TABLE IF NOT EXISTS public.space_weather_cache (
    id              UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
    observed_at     TIMESTAMPTZ NOT NULL UNIQUE,
    kp_index        FLOAT       NOT NULL,
    solar_wind_speed FLOAT,
    bz_component    FLOAT,
    disruption_score FLOAT,
    flare_class     TEXT,
    g_scale         INT         CHECK (g_scale BETWEEN 0 AND 5),
    created_at      TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_space_weather_ts
    ON public.space_weather_cache(observed_at DESC);

-- No RLS — shared read-only table; server-side writes via service role only


-- ============================================================
-- SECTION G: user_insights + hermes_memories
-- ============================================================

-- ────────────────────────────────────────────────────────────
-- G1. user_insights
-- Structured facts extracted by the Hermes learner from chat
-- sessions and wearable data. One insight row per observation.
-- ────────────────────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS public.user_insights (
    id            UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id       UUID        NOT NULL REFERENCES public.users(id) ON DELETE CASCADE,
    category      TEXT        NOT NULL
                              CHECK (category IN (
                                  'sleep_pattern','chronotype','caffeine_habit',
                                  'light_exposure','stress','recovery',
                                  'alcohol','breathwork','nap','exercise',
                                  'supplement','other'
                              )),
    insight       TEXT        NOT NULL,     -- human-readable extracted fact
    confidence    FLOAT       DEFAULT 0.8  CHECK (confidence BETWEEN 0 AND 1),
    source        TEXT        NOT NULL
                              CHECK (source IN ('chat','wearable','manual','hermes')),
    observed_at   TIMESTAMPTZ,
    session_id    UUID        REFERENCES public.chat_sessions(id) ON DELETE SET NULL,
    created_at    TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_user_insights_user_category
    ON public.user_insights(user_id, category);

CREATE INDEX IF NOT EXISTS idx_user_insights_user_ts
    ON public.user_insights(user_id, created_at DESC);

ALTER TABLE public.user_insights ENABLE ROW LEVEL SECURITY;

CREATE POLICY "user_insights_user_rls" ON public.user_insights
    USING  (user_id = auth.uid())
    WITH CHECK (user_id = auth.uid());


-- ────────────────────────────────────────────────────────────
-- G2. hermes_memories
-- Semantic vector store for Hermes per-user memory retrieval.
-- Uses pgvector HNSW index for ANN search.
-- Embedding dimension: 1536 (OpenAI text-embedding-3-small)
-- ────────────────────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS public.hermes_memories (
    id          UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id     UUID        NOT NULL REFERENCES public.users(id) ON DELETE CASCADE,
    content     TEXT        NOT NULL,           -- the memory chunk text
    embedding   vector(1536),                   -- pgvector embedding
    category    TEXT        CHECK (category IN (
                                'sleep_pattern','chronotype','caffeine_habit',
                                'light_exposure','stress','recovery',
                                'alcohol','breathwork','nap','exercise',
                                'supplement','preference','other'
                            )),
    source      TEXT        CHECK (source IN ('chat','wearable','manual','hermes')),
    session_id  UUID        REFERENCES public.chat_sessions(id) ON DELETE SET NULL,
    created_at  TIMESTAMPTZ DEFAULT now(),
    updated_at  TIMESTAMPTZ DEFAULT now()
);

-- HNSW index for fast approximate nearest-neighbour search (cosine distance)
CREATE INDEX IF NOT EXISTS idx_hermes_memories_embedding
    ON public.hermes_memories
    USING hnsw (embedding vector_cosine_ops)
    WITH (m = 16, ef_construction = 64);

CREATE INDEX IF NOT EXISTS idx_hermes_memories_user
    ON public.hermes_memories(user_id);

ALTER TABLE public.hermes_memories ENABLE ROW LEVEL SECURITY;

CREATE POLICY "hermes_memories_user_rls" ON public.hermes_memories
    USING  (user_id = auth.uid())
    WITH CHECK (user_id = auth.uid());


-- ============================================================
-- SECTION H: daily_summaries
-- Materialised daily roll-up per user — refreshed by trigger
-- and by the FastAPI background scheduler.
-- Realtime enabled so the frontend can subscribe.
-- ============================================================

CREATE TABLE IF NOT EXISTS public.daily_summaries (
    id                   UUID    PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id              UUID    NOT NULL REFERENCES public.users(id) ON DELETE CASCADE,
    date                 DATE    NOT NULL,

    -- Sleep quality
    total_sleep_min      INT,
    deep_sleep_min       INT,
    rem_sleep_min        INT,
    light_sleep_min      INT,
    awake_min            INT,
    sleep_latency_min    INT,
    sleep_efficiency     FLOAT   CHECK (sleep_efficiency BETWEEN 0 AND 1),
    deep_pct             FLOAT   CHECK (deep_pct  BETWEEN 0 AND 1),
    rem_pct              FLOAT   CHECK (rem_pct   BETWEEN 0 AND 1),
    light_pct            FLOAT   CHECK (light_pct BETWEEN 0 AND 1),

    -- Biometrics
    hrv_avg              FLOAT,
    hrv_min              FLOAT,
    hrv_max              FLOAT,
    resting_hr           FLOAT,
    avg_hr               FLOAT,
    spo2_avg             FLOAT,
    spo2_min             FLOAT,
    respiratory_rate_avg FLOAT,
    readiness_score      INT,
    sleep_score          INT,

    -- Protocol adherence
    social_jet_lag_min   INT,
    disruption_score     INT,
    kp_index             FLOAT,
    composite_protocol_score FLOAT CHECK (composite_protocol_score BETWEEN 0 AND 1),

    -- Activity
    steps                INT,
    active_min           INT,
    active_calories      INT,

    -- Behavioral flags
    alcohol_day          BOOLEAN DEFAULT false,
    nap_day              BOOLEAN DEFAULT false,
    breathwork_day       BOOLEAN DEFAULT false,

    -- Linked foreign keys
    sleep_log_id         UUID    REFERENCES public.sleep_logs(id),
    protocol_log_id      UUID    REFERENCES public.protocol_logs(id),
    protocol_effectiveness_id UUID REFERENCES public.protocol_effectiveness(id),

    created_at           TIMESTAMPTZ DEFAULT now(),
    updated_at           TIMESTAMPTZ DEFAULT now(),

    UNIQUE(user_id, date)
);

CREATE INDEX IF NOT EXISTS idx_daily_summaries_user_date
    ON public.daily_summaries(user_id, date DESC);

ALTER TABLE public.daily_summaries ENABLE ROW LEVEL SECURITY;

CREATE POLICY "daily_summaries_user_rls" ON public.daily_summaries
    USING  (user_id = auth.uid())
    WITH CHECK (user_id = auth.uid());

-- Enable Realtime so the Vue frontend can subscribe to daily summary updates
ALTER PUBLICATION supabase_realtime ADD TABLE public.daily_summaries;


-- ============================================================
-- SECTION I: Triggers and Functions
-- ============================================================

-- ────────────────────────────────────────────────────────────
-- I1. Generic updated_at updater
-- Applied to: public.users, public.wearable_connections
--             public.hermes_memories, public.daily_summaries
-- ────────────────────────────────────────────────────────────

CREATE OR REPLACE FUNCTION public.update_updated_at()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
BEGIN
    NEW.updated_at = now();
    RETURN NEW;
END;
$$;

-- users
DROP TRIGGER IF EXISTS trg_users_updated_at ON public.users;
CREATE TRIGGER trg_users_updated_at
    BEFORE UPDATE ON public.users
    FOR EACH ROW EXECUTE FUNCTION public.update_updated_at();

-- wearable_connections
DROP TRIGGER IF EXISTS trg_wearable_connections_updated_at ON public.wearable_connections;
CREATE TRIGGER trg_wearable_connections_updated_at
    BEFORE UPDATE ON public.wearable_connections
    FOR EACH ROW EXECUTE FUNCTION public.update_updated_at();

-- hermes_memories
DROP TRIGGER IF EXISTS trg_hermes_memories_updated_at ON public.hermes_memories;
CREATE TRIGGER trg_hermes_memories_updated_at
    BEFORE UPDATE ON public.hermes_memories
    FOR EACH ROW EXECUTE FUNCTION public.update_updated_at();

-- daily_summaries
DROP TRIGGER IF EXISTS trg_daily_summaries_updated_at ON public.daily_summaries;
CREATE TRIGGER trg_daily_summaries_updated_at
    BEFORE UPDATE ON public.daily_summaries
    FOR EACH ROW EXECUTE FUNCTION public.update_updated_at();


-- ────────────────────────────────────────────────────────────
-- I2. Auto-compute hrv_delta on breathwork_sessions
-- Fires BEFORE INSERT OR UPDATE; sets hrv_delta when both
-- hrv_before and hrv_after are present.
-- ────────────────────────────────────────────────────────────

CREATE OR REPLACE FUNCTION public.set_breathwork_hrv_delta()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
BEGIN
    IF NEW.hrv_before IS NOT NULL AND NEW.hrv_after IS NOT NULL THEN
        NEW.hrv_delta := NEW.hrv_after - NEW.hrv_before;
    END IF;
    RETURN NEW;
END;
$$;

DROP TRIGGER IF EXISTS trg_breathwork_hrv_delta ON public.breathwork_sessions;
CREATE TRIGGER trg_breathwork_hrv_delta
    BEFORE INSERT OR UPDATE ON public.breathwork_sessions
    FOR EACH ROW EXECUTE FUNCTION public.set_breathwork_hrv_delta();


-- ────────────────────────────────────────────────────────────
-- I3. Refresh daily_summaries from sleep_logs
-- Fires AFTER INSERT OR UPDATE on public.sleep_logs.
-- Upserts a daily_summaries row with computed sleep fractions
-- and efficiency so the frontend always has a fresh roll-up.
-- ────────────────────────────────────────────────────────────

CREATE OR REPLACE FUNCTION public.refresh_daily_summary_from_sleep()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
DECLARE
    v_total     INT  := NEW.total_sleep_min;
    v_deep      INT  := COALESCE(NEW.deep_sleep_min, 0);
    v_rem       INT  := COALESCE(NEW.rem_sleep_min, 0);
    v_light     INT  := COALESCE(NEW.light_sleep_min, 0);
    v_awake     INT  := COALESCE(NEW.awake_min, 0);
    v_latency   INT  := COALESCE(NEW.sleep_latency_min, 0);
    v_eff       FLOAT;
    v_deep_pct  FLOAT;
    v_rem_pct   FLOAT;
    v_light_pct FLOAT;
    v_total_window INT;
BEGIN
    -- sleep efficiency = total_sleep / (total_sleep + awake + latency)
    v_total_window := v_total + v_awake + v_latency;
    IF v_total_window > 0 THEN
        v_eff := v_total::FLOAT / v_total_window::FLOAT;
    ELSE
        v_eff := NULL;
    END IF;

    -- stage percentages (guard division by zero)
    IF v_total > 0 THEN
        v_deep_pct  := v_deep::FLOAT  / v_total::FLOAT;
        v_rem_pct   := v_rem::FLOAT   / v_total::FLOAT;
        v_light_pct := v_light::FLOAT / v_total::FLOAT;
    ELSE
        v_deep_pct  := NULL;
        v_rem_pct   := NULL;
        v_light_pct := NULL;
    END IF;

    INSERT INTO public.daily_summaries (
        user_id,
        date,
        total_sleep_min,
        deep_sleep_min,
        rem_sleep_min,
        light_sleep_min,
        awake_min,
        sleep_latency_min,
        sleep_efficiency,
        deep_pct,
        rem_pct,
        light_pct,
        hrv_avg,
        hrv_min,
        hrv_max,
        resting_hr,
        avg_hr,
        spo2_avg,
        spo2_min,
        respiratory_rate_avg,
        readiness_score,
        sleep_score,
        sleep_log_id,
        updated_at
    )
    VALUES (
        NEW.user_id,
        NEW.date,
        v_total,
        NEW.deep_sleep_min,
        NEW.rem_sleep_min,
        NEW.light_sleep_min,
        NEW.awake_min,
        NEW.sleep_latency_min,
        v_eff,
        v_deep_pct,
        v_rem_pct,
        v_light_pct,
        NEW.hrv_avg,
        NEW.hrv_min,
        NEW.hrv_max,
        NEW.resting_hr,
        NEW.avg_hr,
        NEW.spo2_avg,
        NEW.spo2_min,
        NEW.respiratory_rate_avg,
        NEW.readiness_score,
        NEW.sleep_score,
        NEW.id,
        now()
    )
    ON CONFLICT (user_id, date) DO UPDATE SET
        total_sleep_min      = EXCLUDED.total_sleep_min,
        deep_sleep_min       = EXCLUDED.deep_sleep_min,
        rem_sleep_min        = EXCLUDED.rem_sleep_min,
        light_sleep_min      = EXCLUDED.light_sleep_min,
        awake_min            = EXCLUDED.awake_min,
        sleep_latency_min    = EXCLUDED.sleep_latency_min,
        sleep_efficiency     = EXCLUDED.sleep_efficiency,
        deep_pct             = EXCLUDED.deep_pct,
        rem_pct              = EXCLUDED.rem_pct,
        light_pct            = EXCLUDED.light_pct,
        hrv_avg              = EXCLUDED.hrv_avg,
        hrv_min              = EXCLUDED.hrv_min,
        hrv_max              = EXCLUDED.hrv_max,
        resting_hr           = EXCLUDED.resting_hr,
        avg_hr               = EXCLUDED.avg_hr,
        spo2_avg             = EXCLUDED.spo2_avg,
        spo2_min             = EXCLUDED.spo2_min,
        respiratory_rate_avg = EXCLUDED.respiratory_rate_avg,
        readiness_score      = EXCLUDED.readiness_score,
        sleep_score          = EXCLUDED.sleep_score,
        sleep_log_id         = EXCLUDED.sleep_log_id,
        updated_at           = now();

    RETURN NEW;
END;
$$;

DROP TRIGGER IF EXISTS trg_refresh_daily_summary_from_sleep ON public.sleep_logs;
CREATE TRIGGER trg_refresh_daily_summary_from_sleep
    AFTER INSERT OR UPDATE ON public.sleep_logs
    FOR EACH ROW EXECUTE FUNCTION public.refresh_daily_summary_from_sleep();


-- ============================================================
-- SECTION J: Supabase Storage — wearable-uploads bucket
-- ============================================================

/*
  STORAGE BUCKET SETUP (run once via Supabase Dashboard or Management API)
  -------------------------------------------------------------------------
  Bucket name : wearable-uploads
  Public      : false  (all objects served via signed URL only)
  File size   : 50 MB max (configurable)
  MIME types  : application/json, text/csv, application/octet-stream

  RLS policies on storage.objects:
  ─────────────────────────────────
  -- Allow authenticated user to upload their own files
  CREATE POLICY "wearable_upload_insert" ON storage.objects
      FOR INSERT
      WITH CHECK (
          bucket_id = 'wearable-uploads'
          AND auth.uid()::text = (storage.foldername(name))[1]
      );

  -- Allow authenticated user to read their own files
  CREATE POLICY "wearable_upload_select" ON storage.objects
      FOR SELECT
      USING (
          bucket_id = 'wearable-uploads'
          AND auth.uid()::text = (storage.foldername(name))[1]
      );

  -- Allow server-side deletion (service role only; no user policy needed)

  File path convention:
  ─────────────────────
  {user_id}/{import_id}/{original_filename}

  Example:
  7a3f...uuid/b9c2...uuid/oura_2025-01-01.json

  This path is stored in data_imports.storage_path so the FastAPI
  worker can retrieve the file via the Supabase Storage client for
  background parsing.
*/


-- ============================================================
-- SECTION K: Research Module → Table Mapping
-- ============================================================

/*
  RESEARCH MODULE TO TABLE MAPPING
  =================================

  chronotype_engine.py
    READS  : users.usual_sleep_time, users.usual_wake_time, sleep_logs (last 30 days)
    WRITES : users.chronotype, protocol_logs.social_jet_lag_min

  caffeine_model.py
    READS  : users.cyp1a2_genotype, users.adora2a_sensitivity,
             users.is_smoker, users.uses_oral_contraceptive,
             caffeine_logs (today), sleep_logs.sleep_onset (last night)
    WRITES : caffeine_logs (new dose), protocol_logs (caffeine cutoff recommendation)

  space_weather_bio.py
    READS  : space_weather_cache (latest Kp, solar wind, Bz, G-scale)
             (Alabdali 2022 — Kp→HRV; Burch 2008 — melatonin suppression modifier)
    WRITES : space_weather_cache (via FastAPI background worker, service role)
             protocol_logs.disruption_score, daily_summaries.disruption_score

  light_model.py
    READS  : users.is_light_sensitive, light_exposure_logs (today),
             sleep_logs.sleep_onset
             (Brown 2022 — melanopic EDI zones; Gimenez 2022 — melatonin suppression)
    WRITES : light_exposure_logs (manual/device log), daily_summaries (no direct write)

  alcohol_model.py
    READS  : users.weight_kg, users.sex, users.alcohol_distribution_factor,
             alcohol_logs (today), sleep_logs (prior night)
             (Widmark equation; Pietilä 2018 — HRV/deep sleep impact)
    WRITES : alcohol_logs.bac_estimate, daily_summaries.alcohol_day

  breathwork_model.py
    READS  : breathwork_sessions (user history), biometric_logs (HRV around session)
             (Laborde 2022 meta-analysis — resonance frequency at 5.5 bpm)
    WRITES : breathwork_sessions (new session), daily_summaries.breathwork_day

  nap_model.py
    READS  : nap_logs (user history), sleep_logs (last night),
             users.usual_wake_time
             (Rosekind 1995 — NASA 26-min protocol; coffee nap sequencing)
    WRITES : nap_logs (new nap), sleep_logs.nap_preceded (next night)

  ── PLANNED MODULES ─────────────────────────────────────────

  meal_timing_model.py      → will read/write: meal_logs (table not yet created)
  exercise_timing_model.py  → will read: activity_logs; write: protocol_logs
  supplement_model.py       → will read: users.date_of_birth; write: protocol_logs
  cold_exposure_model.py    → will read: biometric_logs (HRV); write: user_insights
  hrv_sleep_model.py        → will read: sleep_logs, biometric_logs; write: daily_summaries
  wearable_pipeline.py      → will read: data_imports, storage; write: sleep_logs,
                              biometric_logs, activity_logs, sleep_stages
  jetlag_optimizer.py       → will read: users.*, sleep_logs; write: protocol_logs
*/
