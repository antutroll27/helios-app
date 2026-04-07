-- HELIOS Backend — Supabase Schema Migration
-- Run this in the Supabase SQL Editor

-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS vector;
CREATE EXTENSION IF NOT EXISTS pgcrypto;

-- ─── Users (extends Supabase Auth) ──────────────────────────────────────────

CREATE TABLE IF NOT EXISTS public.users (
    id UUID PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
    display_name TEXT,
    chronotype TEXT DEFAULT 'intermediate' CHECK (chronotype IN ('early', 'intermediate', 'late')),
    usual_sleep_time TIME DEFAULT '23:00',
    encrypted_api_keys JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- ─── Chat Sessions ──────────────────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS public.chat_sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES public.users(id) ON DELETE CASCADE,
    started_at TIMESTAMPTZ DEFAULT NOW(),
    ended_at TIMESTAMPTZ,
    message_count INT DEFAULT 0,
    hermes_processed BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_chat_sessions_user ON public.chat_sessions(user_id);

-- ─── Chat Messages ──────────────────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS public.chat_messages (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id UUID NOT NULL REFERENCES public.chat_sessions(id) ON DELETE CASCADE,
    role TEXT NOT NULL CHECK (role IN ('user', 'assistant', 'system')),
    content TEXT NOT NULL,
    visual_cards JSONB,
    timestamp TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_chat_messages_session ON public.chat_messages(session_id);

-- ─── Sleep Logs (maps to SleepLog dataclass) ────────────────────────────────

CREATE TABLE IF NOT EXISTS public.sleep_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES public.users(id) ON DELETE CASCADE,
    date DATE NOT NULL,
    sleep_onset TIMESTAMPTZ NOT NULL,
    wake_time TIMESTAMPTZ NOT NULL,
    total_sleep_min INT NOT NULL,
    deep_sleep_min INT,
    rem_sleep_min INT,
    hrv_avg FLOAT,
    skin_temp_delta FLOAT,
    resting_hr FLOAT,
    sleep_score INT,
    source TEXT DEFAULT 'manual' CHECK (source IN ('manual', 'oura', 'fitbit', 'garmin', 'samsung', 'whoop', 'apple_health')),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_sleep_logs_user_date ON public.sleep_logs(user_id, date);

-- ─── Data Imports (wearable file uploads) ───────────────────────────────────

CREATE TABLE IF NOT EXISTS public.data_imports (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES public.users(id) ON DELETE CASCADE,
    filename TEXT NOT NULL,
    platform TEXT NOT NULL,
    uploaded_at TIMESTAMPTZ DEFAULT NOW(),
    status TEXT DEFAULT 'pending' CHECK (status IN ('pending', 'processing', 'complete', 'failed')),
    records_imported INT DEFAULT 0,
    error_message TEXT
);

-- ─── Protocol Logs (maps to ProtocolLog dataclass) ──────────────────────────

CREATE TABLE IF NOT EXISTS public.protocol_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES public.users(id) ON DELETE CASCADE,
    date DATE NOT NULL,
    recommended_sleep TIMESTAMPTZ NOT NULL,
    actual_sleep TIMESTAMPTZ,
    recommended_wake TIMESTAMPTZ NOT NULL,
    actual_wake TIMESTAMPTZ,
    kp_index FLOAT,
    disruption_score INT,
    social_jet_lag_min INT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_protocol_logs_user_date ON public.protocol_logs(user_id, date);

-- ─── Caffeine Logs ──────────────────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS public.caffeine_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES public.users(id) ON DELETE CASCADE,
    mg FLOAT NOT NULL,
    time TIMESTAMPTZ NOT NULL,
    source TEXT DEFAULT 'manual',
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_caffeine_logs_user_date ON public.caffeine_logs(user_id, time);

-- ─── Biometric Logs (HR, HRV, skin temp, etc.) ─────────────────────────────

CREATE TABLE IF NOT EXISTS public.biometric_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES public.users(id) ON DELETE CASCADE,
    timestamp TIMESTAMPTZ NOT NULL,
    metric TEXT NOT NULL CHECK (metric IN ('hr', 'hrv_rmssd', 'hrv_sdnn', 'skin_temp', 'respiratory_rate', 'spo2')),
    value FLOAT NOT NULL,
    source TEXT DEFAULT 'manual',
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_biometric_logs_user_metric ON public.biometric_logs(user_id, metric, timestamp);

-- ─── Row Level Security ─────────────────────────────────────────────────────

ALTER TABLE public.users ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.chat_sessions ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.chat_messages ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.sleep_logs ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.data_imports ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.protocol_logs ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.caffeine_logs ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.biometric_logs ENABLE ROW LEVEL SECURITY;

-- Users can only access their own data
CREATE POLICY users_own_data ON public.users FOR ALL USING (auth.uid() = id);
CREATE POLICY sessions_own_data ON public.chat_sessions FOR ALL USING (auth.uid() = user_id);
CREATE POLICY messages_own_data ON public.chat_messages FOR ALL USING (
    session_id IN (SELECT id FROM public.chat_sessions WHERE user_id = auth.uid())
);
CREATE POLICY sleep_own_data ON public.sleep_logs FOR ALL USING (auth.uid() = user_id);
CREATE POLICY imports_own_data ON public.data_imports FOR ALL USING (auth.uid() = user_id);
CREATE POLICY protocol_own_data ON public.protocol_logs FOR ALL USING (auth.uid() = user_id);
CREATE POLICY caffeine_own_data ON public.caffeine_logs FOR ALL USING (auth.uid() = user_id);
CREATE POLICY biometric_own_data ON public.biometric_logs FOR ALL USING (auth.uid() = user_id);
