export type Json =
  | string
  | number
  | boolean
  | null
  | { [key: string]: Json | undefined }
  | Json[]

export type Database = {
  // Allows to automatically instantiate createClient with right options
  // instead of createClient<Database, { PostgrestVersion: 'XX' }>(URL, KEY)
  __InternalSupabase: {
    PostgrestVersion: "14.5"
  }
  public: {
    Tables: {
      activity_logs: {
        Row: {
          active_calories: number | null
          active_min: number | null
          avg_daytime_hr: number | null
          created_at: string | null
          date: string
          id: string
          import_id: string | null
          moderate_intensity_min: number | null
          peak_hr: number | null
          sedentary_min: number | null
          source: string
          steps: number | null
          total_calories: number | null
          user_id: string
          vigorous_intensity_min: number | null
        }
        Insert: {
          active_calories?: number | null
          active_min?: number | null
          avg_daytime_hr?: number | null
          created_at?: string | null
          date: string
          id?: string
          import_id?: string | null
          moderate_intensity_min?: number | null
          peak_hr?: number | null
          sedentary_min?: number | null
          source?: string
          steps?: number | null
          total_calories?: number | null
          user_id: string
          vigorous_intensity_min?: number | null
        }
        Update: {
          active_calories?: number | null
          active_min?: number | null
          avg_daytime_hr?: number | null
          created_at?: string | null
          date?: string
          id?: string
          import_id?: string | null
          moderate_intensity_min?: number | null
          peak_hr?: number | null
          sedentary_min?: number | null
          source?: string
          steps?: number | null
          total_calories?: number | null
          user_id?: string
          vigorous_intensity_min?: number | null
        }
        Relationships: [
          {
            foreignKeyName: "activity_logs_import_id_fkey"
            columns: ["import_id"]
            isOneToOne: false
            referencedRelation: "data_imports"
            referencedColumns: ["id"]
          },
          {
            foreignKeyName: "activity_logs_user_id_fkey"
            columns: ["user_id"]
            isOneToOne: false
            referencedRelation: "users"
            referencedColumns: ["id"]
          },
        ]
      }
      alcohol_logs: {
        Row: {
          bac_estimate: number | null
          consumed_at: string
          created_at: string | null
          drink_type: string | null
          drinks: number
          hours_before_bed: number | null
          id: string
          notes: string | null
          user_id: string
        }
        Insert: {
          bac_estimate?: number | null
          consumed_at: string
          created_at?: string | null
          drink_type?: string | null
          drinks: number
          hours_before_bed?: number | null
          id?: string
          notes?: string | null
          user_id: string
        }
        Update: {
          bac_estimate?: number | null
          consumed_at?: string
          created_at?: string | null
          drink_type?: string | null
          drinks?: number
          hours_before_bed?: number | null
          id?: string
          notes?: string | null
          user_id?: string
        }
        Relationships: [
          {
            foreignKeyName: "alcohol_logs_user_id_fkey"
            columns: ["user_id"]
            isOneToOne: false
            referencedRelation: "users"
            referencedColumns: ["id"]
          },
        ]
      }
      app_sessions: {
        Row: {
          created_at: string
          csrf_token_hash: string
          email_snapshot: string | null
          expires_at: string
          id: string
          ip_hash: string | null
          last_seen_at: string | null
          revoked_at: string | null
          rotated_at: string | null
          user_agent_hash: string | null
          user_id: string
        }
        Insert: {
          created_at?: string
          csrf_token_hash: string
          email_snapshot?: string | null
          expires_at: string
          id: string
          ip_hash?: string | null
          last_seen_at?: string | null
          revoked_at?: string | null
          rotated_at?: string | null
          user_agent_hash?: string | null
          user_id: string
        }
        Update: {
          created_at?: string
          csrf_token_hash?: string
          email_snapshot?: string | null
          expires_at?: string
          id?: string
          ip_hash?: string | null
          last_seen_at?: string | null
          revoked_at?: string | null
          rotated_at?: string | null
          user_agent_hash?: string | null
          user_id?: string
        }
        Relationships: [
          {
            foreignKeyName: "app_sessions_user_id_fkey"
            columns: ["user_id"]
            isOneToOne: false
            referencedRelation: "users"
            referencedColumns: ["id"]
          },
        ]
      }
      biometric_logs: {
        Row: {
          created_at: string | null
          id: string
          metric: string
          sleep_log_id: string | null
          source: string | null
          timestamp: string
          user_id: string
          value: number
        }
        Insert: {
          created_at?: string | null
          id?: string
          metric: string
          sleep_log_id?: string | null
          source?: string | null
          timestamp: string
          user_id: string
          value: number
        }
        Update: {
          created_at?: string | null
          id?: string
          metric?: string
          sleep_log_id?: string | null
          source?: string | null
          timestamp?: string
          user_id?: string
          value?: number
        }
        Relationships: [
          {
            foreignKeyName: "biometric_logs_sleep_log_id_fkey"
            columns: ["sleep_log_id"]
            isOneToOne: false
            referencedRelation: "sleep_logs"
            referencedColumns: ["id"]
          },
          {
            foreignKeyName: "biometric_logs_user_id_fkey"
            columns: ["user_id"]
            isOneToOne: false
            referencedRelation: "users"
            referencedColumns: ["id"]
          },
        ]
      }
      breathwork_sessions: {
        Row: {
          breaths_per_min: number | null
          created_at: string | null
          duration_min: number | null
          ended_at: string | null
          goal: string | null
          hrv_after: number | null
          hrv_before: number | null
          hrv_delta: number | null
          id: string
          notes: string | null
          started_at: string
          target_bpm: number | null
          technique: string
          user_id: string
        }
        Insert: {
          breaths_per_min?: number | null
          created_at?: string | null
          duration_min?: number | null
          ended_at?: string | null
          goal?: string | null
          hrv_after?: number | null
          hrv_before?: number | null
          hrv_delta?: number | null
          id?: string
          notes?: string | null
          started_at: string
          target_bpm?: number | null
          technique: string
          user_id: string
        }
        Update: {
          breaths_per_min?: number | null
          created_at?: string | null
          duration_min?: number | null
          ended_at?: string | null
          goal?: string | null
          hrv_after?: number | null
          hrv_before?: number | null
          hrv_delta?: number | null
          id?: string
          notes?: string | null
          started_at?: string
          target_bpm?: number | null
          technique?: string
          user_id?: string
        }
        Relationships: [
          {
            foreignKeyName: "breathwork_sessions_user_id_fkey"
            columns: ["user_id"]
            isOneToOne: false
            referencedRelation: "users"
            referencedColumns: ["id"]
          },
        ]
      }
      caffeine_logs: {
        Row: {
          created_at: string | null
          id: string
          mg: number
          source: string | null
          time: string
          user_id: string
        }
        Insert: {
          created_at?: string | null
          id?: string
          mg: number
          source?: string | null
          time: string
          user_id: string
        }
        Update: {
          created_at?: string | null
          id?: string
          mg?: number
          source?: string | null
          time?: string
          user_id?: string
        }
        Relationships: [
          {
            foreignKeyName: "caffeine_logs_user_id_fkey"
            columns: ["user_id"]
            isOneToOne: false
            referencedRelation: "users"
            referencedColumns: ["id"]
          },
        ]
      }
      chat_messages: {
        Row: {
          content: string
          id: string
          role: string
          session_id: string
          timestamp: string | null
          visual_cards: Json | null
        }
        Insert: {
          content: string
          id?: string
          role: string
          session_id: string
          timestamp?: string | null
          visual_cards?: Json | null
        }
        Update: {
          content?: string
          id?: string
          role?: string
          session_id?: string
          timestamp?: string | null
          visual_cards?: Json | null
        }
        Relationships: [
          {
            foreignKeyName: "chat_messages_session_id_fkey"
            columns: ["session_id"]
            isOneToOne: false
            referencedRelation: "chat_sessions"
            referencedColumns: ["id"]
          },
        ]
      }
      chat_sessions: {
        Row: {
          created_at: string | null
          encrypted_api_key: string | null
          ended_at: string | null
          hermes_processed: boolean | null
          hermes_processing: boolean | null
          id: string
          message_count: number | null
          provider: string | null
          started_at: string | null
          user_id: string
        }
        Insert: {
          created_at?: string | null
          encrypted_api_key?: string | null
          ended_at?: string | null
          hermes_processed?: boolean | null
          hermes_processing?: boolean | null
          id?: string
          message_count?: number | null
          provider?: string | null
          started_at?: string | null
          user_id: string
        }
        Update: {
          created_at?: string | null
          encrypted_api_key?: string | null
          ended_at?: string | null
          hermes_processed?: boolean | null
          hermes_processing?: boolean | null
          id?: string
          message_count?: number | null
          provider?: string | null
          started_at?: string | null
          user_id?: string
        }
        Relationships: [
          {
            foreignKeyName: "chat_sessions_user_id_fkey"
            columns: ["user_id"]
            isOneToOne: false
            referencedRelation: "users"
            referencedColumns: ["id"]
          },
        ]
      }
      daily_summaries: {
        Row: {
          adherence_pct: number | null
          alcohol_drinks: number | null
          caffeine_mg_total: number | null
          computed_at: string | null
          date: string
          deep_pct: number | null
          disruption_score: number | null
          hrv_7d_avg: number | null
          hrv_avg: number | null
          hrv_vs_30d_mean: number | null
          id: string
          kp_max: number | null
          light_pct: number | null
          readiness_score: number | null
          rem_pct: number | null
          resting_hr: number | null
          sleep_delta_min: number | null
          sleep_efficiency: number | null
          sleep_score: number | null
          steps: number | null
          total_sleep_min: number | null
          user_id: string
          wake_delta_min: number | null
        }
        Insert: {
          adherence_pct?: number | null
          alcohol_drinks?: number | null
          caffeine_mg_total?: number | null
          computed_at?: string | null
          date: string
          deep_pct?: number | null
          disruption_score?: number | null
          hrv_7d_avg?: number | null
          hrv_avg?: number | null
          hrv_vs_30d_mean?: number | null
          id?: string
          kp_max?: number | null
          light_pct?: number | null
          readiness_score?: number | null
          rem_pct?: number | null
          resting_hr?: number | null
          sleep_delta_min?: number | null
          sleep_efficiency?: number | null
          sleep_score?: number | null
          steps?: number | null
          total_sleep_min?: number | null
          user_id: string
          wake_delta_min?: number | null
        }
        Update: {
          adherence_pct?: number | null
          alcohol_drinks?: number | null
          caffeine_mg_total?: number | null
          computed_at?: string | null
          date?: string
          deep_pct?: number | null
          disruption_score?: number | null
          hrv_7d_avg?: number | null
          hrv_avg?: number | null
          hrv_vs_30d_mean?: number | null
          id?: string
          kp_max?: number | null
          light_pct?: number | null
          readiness_score?: number | null
          rem_pct?: number | null
          resting_hr?: number | null
          sleep_delta_min?: number | null
          sleep_efficiency?: number | null
          sleep_score?: number | null
          steps?: number | null
          total_sleep_min?: number | null
          user_id?: string
          wake_delta_min?: number | null
        }
        Relationships: [
          {
            foreignKeyName: "daily_summaries_user_id_fkey"
            columns: ["user_id"]
            isOneToOne: false
            referencedRelation: "users"
            referencedColumns: ["id"]
          },
        ]
      }
      data_imports: {
        Row: {
          error_message: string | null
          file_size_bytes: number | null
          filename: string
          id: string
          parsed_from: string | null
          parsed_to: string | null
          platform: string
          records_imported: number | null
          status: string | null
          storage_path: string | null
          uploaded_at: string | null
          user_id: string
        }
        Insert: {
          error_message?: string | null
          file_size_bytes?: number | null
          filename: string
          id?: string
          parsed_from?: string | null
          parsed_to?: string | null
          platform: string
          records_imported?: number | null
          status?: string | null
          storage_path?: string | null
          uploaded_at?: string | null
          user_id: string
        }
        Update: {
          error_message?: string | null
          file_size_bytes?: number | null
          filename?: string
          id?: string
          parsed_from?: string | null
          parsed_to?: string | null
          platform?: string
          records_imported?: number | null
          status?: string | null
          storage_path?: string | null
          uploaded_at?: string | null
          user_id?: string
        }
        Relationships: [
          {
            foreignKeyName: "data_imports_user_id_fkey"
            columns: ["user_id"]
            isOneToOne: false
            referencedRelation: "users"
            referencedColumns: ["id"]
          },
        ]
      }
      hermes_memories: {
        Row: {
          category: string | null
          created_at: string | null
          embedding: string | null
          id: string
          memory_text: string
          source_session_id: string | null
          user_id: string
        }
        Insert: {
          category?: string | null
          created_at?: string | null
          embedding?: string | null
          id?: string
          memory_text: string
          source_session_id?: string | null
          user_id: string
        }
        Update: {
          category?: string | null
          created_at?: string | null
          embedding?: string | null
          id?: string
          memory_text?: string
          source_session_id?: string | null
          user_id?: string
        }
        Relationships: [
          {
            foreignKeyName: "hermes_memories_source_session_id_fkey"
            columns: ["source_session_id"]
            isOneToOne: false
            referencedRelation: "chat_sessions"
            referencedColumns: ["id"]
          },
          {
            foreignKeyName: "hermes_memories_user_id_fkey"
            columns: ["user_id"]
            isOneToOne: false
            referencedRelation: "users"
            referencedColumns: ["id"]
          },
        ]
      }
      light_exposure_logs: {
        Row: {
          created_at: string | null
          device_type: string | null
          duration_min: number | null
          hours_before_sleep: number | null
          id: string
          logged_at: string
          melanopic_edi_lux: number
          notes: string | null
          source_type: string
          user_id: string
          zone: string | null
        }
        Insert: {
          created_at?: string | null
          device_type?: string | null
          duration_min?: number | null
          hours_before_sleep?: number | null
          id?: string
          logged_at: string
          melanopic_edi_lux: number
          notes?: string | null
          source_type: string
          user_id: string
          zone?: string | null
        }
        Update: {
          created_at?: string | null
          device_type?: string | null
          duration_min?: number | null
          hours_before_sleep?: number | null
          id?: string
          logged_at?: string
          melanopic_edi_lux?: number
          notes?: string | null
          source_type?: string
          user_id?: string
          zone?: string | null
        }
        Relationships: [
          {
            foreignKeyName: "light_exposure_logs_user_id_fkey"
            columns: ["user_id"]
            isOneToOne: false
            referencedRelation: "users"
            referencedColumns: ["id"]
          },
        ]
      }
      nap_logs: {
        Row: {
          alertness_boost: string | null
          created_at: string | null
          duration_min: number | null
          ended_at: string | null
          followed_protocol: boolean | null
          hours_after_wake: number | null
          id: string
          nap_type: string | null
          notes: string | null
          sleep_inertia_min: number | null
          started_at: string
          user_id: string
        }
        Insert: {
          alertness_boost?: string | null
          created_at?: string | null
          duration_min?: number | null
          ended_at?: string | null
          followed_protocol?: boolean | null
          hours_after_wake?: number | null
          id?: string
          nap_type?: string | null
          notes?: string | null
          sleep_inertia_min?: number | null
          started_at: string
          user_id: string
        }
        Update: {
          alertness_boost?: string | null
          created_at?: string | null
          duration_min?: number | null
          ended_at?: string | null
          followed_protocol?: boolean | null
          hours_after_wake?: number | null
          id?: string
          nap_type?: string | null
          notes?: string | null
          sleep_inertia_min?: number | null
          started_at?: string
          user_id?: string
        }
        Relationships: [
          {
            foreignKeyName: "nap_logs_user_id_fkey"
            columns: ["user_id"]
            isOneToOne: false
            referencedRelation: "users"
            referencedColumns: ["id"]
          },
        ]
      }
      protocol_effectiveness: {
        Row: {
          composite_score: number | null
          created_at: string | null
          date: string
          deep_sleep_score: number | null
          disruption_score: number | null
          duration_score: number | null
          hrv_score: number | null
          id: string
          kp_index: number | null
          protocol_log_id: string | null
          rem_score: number | null
          sleep_log_id: string | null
          timing_score: number | null
          user_id: string
        }
        Insert: {
          composite_score?: number | null
          created_at?: string | null
          date: string
          deep_sleep_score?: number | null
          disruption_score?: number | null
          duration_score?: number | null
          hrv_score?: number | null
          id?: string
          kp_index?: number | null
          protocol_log_id?: string | null
          rem_score?: number | null
          sleep_log_id?: string | null
          timing_score?: number | null
          user_id: string
        }
        Update: {
          composite_score?: number | null
          created_at?: string | null
          date?: string
          deep_sleep_score?: number | null
          disruption_score?: number | null
          duration_score?: number | null
          hrv_score?: number | null
          id?: string
          kp_index?: number | null
          protocol_log_id?: string | null
          rem_score?: number | null
          sleep_log_id?: string | null
          timing_score?: number | null
          user_id?: string
        }
        Relationships: [
          {
            foreignKeyName: "protocol_effectiveness_protocol_log_id_fkey"
            columns: ["protocol_log_id"]
            isOneToOne: false
            referencedRelation: "protocol_logs"
            referencedColumns: ["id"]
          },
          {
            foreignKeyName: "protocol_effectiveness_sleep_log_id_fkey"
            columns: ["sleep_log_id"]
            isOneToOne: false
            referencedRelation: "sleep_logs"
            referencedColumns: ["id"]
          },
          {
            foreignKeyName: "protocol_effectiveness_user_id_fkey"
            columns: ["user_id"]
            isOneToOne: false
            referencedRelation: "users"
            referencedColumns: ["id"]
          },
        ]
      }
      protocol_logs: {
        Row: {
          actual_sleep: string | null
          actual_wake: string | null
          created_at: string | null
          date: string
          disruption_score: number | null
          id: string
          kp_index: number | null
          recommended_sleep: string
          recommended_wake: string
          social_jet_lag_min: number | null
          user_id: string
        }
        Insert: {
          actual_sleep?: string | null
          actual_wake?: string | null
          created_at?: string | null
          date: string
          disruption_score?: number | null
          id?: string
          kp_index?: number | null
          recommended_sleep: string
          recommended_wake: string
          social_jet_lag_min?: number | null
          user_id: string
        }
        Update: {
          actual_sleep?: string | null
          actual_wake?: string | null
          created_at?: string | null
          date?: string
          disruption_score?: number | null
          id?: string
          kp_index?: number | null
          recommended_sleep?: string
          recommended_wake?: string
          social_jet_lag_min?: number | null
          user_id?: string
        }
        Relationships: [
          {
            foreignKeyName: "protocol_logs_user_id_fkey"
            columns: ["user_id"]
            isOneToOne: false
            referencedRelation: "users"
            referencedColumns: ["id"]
          },
        ]
      }
      public_api_cache: {
        Row: {
          cache_key: string
          created_at: string
          expires_at: string
          fetched_at: string
          id: string
          payload: Json
          source: string
        }
        Insert: {
          cache_key: string
          created_at?: string
          expires_at: string
          fetched_at?: string
          id?: string
          payload: Json
          source: string
        }
        Update: {
          cache_key?: string
          created_at?: string
          expires_at?: string
          fetched_at?: string
          id?: string
          payload?: Json
          source?: string
        }
        Relationships: []
      }
      shared_llm_usage: {
        Row: {
          count: number
          updated_at: string
          usage_date: string
          user_id: string
        }
        Insert: {
          count?: number
          updated_at?: string
          usage_date: string
          user_id: string
        }
        Update: {
          count?: number
          updated_at?: string
          usage_date?: string
          user_id?: string
        }
        Relationships: [
          {
            foreignKeyName: "shared_llm_usage_user_id_fkey"
            columns: ["user_id"]
            isOneToOne: false
            referencedRelation: "users"
            referencedColumns: ["id"]
          },
        ]
      }
      sleep_logs: {
        Row: {
          alcohol_preceding: boolean | null
          avg_hr: number | null
          awake_min: number | null
          created_at: string | null
          date: string
          deep_sleep_min: number | null
          hrv_avg: number | null
          hrv_max: number | null
          hrv_min: number | null
          id: string
          import_id: string | null
          light_sleep_min: number | null
          nap_preceded: boolean | null
          readiness_score: number | null
          rem_sleep_min: number | null
          respiratory_rate_avg: number | null
          resting_hr: number | null
          skin_temp_delta: number | null
          sleep_latency_min: number | null
          sleep_onset: string
          sleep_score: number | null
          source: string | null
          spo2_avg: number | null
          spo2_min: number | null
          total_sleep_min: number
          user_id: string
          wake_time: string
        }
        Insert: {
          alcohol_preceding?: boolean | null
          avg_hr?: number | null
          awake_min?: number | null
          created_at?: string | null
          date: string
          deep_sleep_min?: number | null
          hrv_avg?: number | null
          hrv_max?: number | null
          hrv_min?: number | null
          id?: string
          import_id?: string | null
          light_sleep_min?: number | null
          nap_preceded?: boolean | null
          readiness_score?: number | null
          rem_sleep_min?: number | null
          respiratory_rate_avg?: number | null
          resting_hr?: number | null
          skin_temp_delta?: number | null
          sleep_latency_min?: number | null
          sleep_onset: string
          sleep_score?: number | null
          source?: string | null
          spo2_avg?: number | null
          spo2_min?: number | null
          total_sleep_min: number
          user_id: string
          wake_time: string
        }
        Update: {
          alcohol_preceding?: boolean | null
          avg_hr?: number | null
          awake_min?: number | null
          created_at?: string | null
          date?: string
          deep_sleep_min?: number | null
          hrv_avg?: number | null
          hrv_max?: number | null
          hrv_min?: number | null
          id?: string
          import_id?: string | null
          light_sleep_min?: number | null
          nap_preceded?: boolean | null
          readiness_score?: number | null
          rem_sleep_min?: number | null
          respiratory_rate_avg?: number | null
          resting_hr?: number | null
          skin_temp_delta?: number | null
          sleep_latency_min?: number | null
          sleep_onset?: string
          sleep_score?: number | null
          source?: string | null
          spo2_avg?: number | null
          spo2_min?: number | null
          total_sleep_min?: number
          user_id?: string
          wake_time?: string
        }
        Relationships: [
          {
            foreignKeyName: "sleep_logs_import_id_fkey"
            columns: ["import_id"]
            isOneToOne: false
            referencedRelation: "data_imports"
            referencedColumns: ["id"]
          },
          {
            foreignKeyName: "sleep_logs_user_id_fkey"
            columns: ["user_id"]
            isOneToOne: false
            referencedRelation: "users"
            referencedColumns: ["id"]
          },
        ]
      }
      sleep_stages: {
        Row: {
          created_at: string | null
          duration_min: number
          end_time: string
          id: string
          sleep_log_id: string
          source: string
          stage: string
          start_time: string
          user_id: string
        }
        Insert: {
          created_at?: string | null
          duration_min: number
          end_time: string
          id?: string
          sleep_log_id: string
          source?: string
          stage: string
          start_time: string
          user_id: string
        }
        Update: {
          created_at?: string | null
          duration_min?: number
          end_time?: string
          id?: string
          sleep_log_id?: string
          source?: string
          stage?: string
          start_time?: string
          user_id?: string
        }
        Relationships: [
          {
            foreignKeyName: "sleep_stages_sleep_log_id_fkey"
            columns: ["sleep_log_id"]
            isOneToOne: false
            referencedRelation: "sleep_logs"
            referencedColumns: ["id"]
          },
          {
            foreignKeyName: "sleep_stages_user_id_fkey"
            columns: ["user_id"]
            isOneToOne: false
            referencedRelation: "users"
            referencedColumns: ["id"]
          },
        ]
      }
      space_weather_cache: {
        Row: {
          bz_component: number | null
          created_at: string | null
          disruption_score: number | null
          flare_class: string | null
          g_scale: number | null
          id: string
          kp_index: number
          observed_at: string
          solar_wind_speed: number | null
        }
        Insert: {
          bz_component?: number | null
          created_at?: string | null
          disruption_score?: number | null
          flare_class?: string | null
          g_scale?: number | null
          id?: string
          kp_index: number
          observed_at: string
          solar_wind_speed?: number | null
        }
        Update: {
          bz_component?: number | null
          created_at?: string | null
          disruption_score?: number | null
          flare_class?: string | null
          g_scale?: number | null
          id?: string
          kp_index?: number
          observed_at?: string
          solar_wind_speed?: number | null
        }
        Relationships: []
      }
      user_insights: {
        Row: {
          accent_hex: string | null
          body: string
          computed_at: string | null
          confidence: string
          created_at: string | null
          data_window_days: number | null
          expires_at: string | null
          id: string
          insight_type: string
          is_dismissed: boolean | null
          metric: string
          title: string
          user_id: string
        }
        Insert: {
          accent_hex?: string | null
          body: string
          computed_at?: string | null
          confidence: string
          created_at?: string | null
          data_window_days?: number | null
          expires_at?: string | null
          id?: string
          insight_type: string
          is_dismissed?: boolean | null
          metric: string
          title: string
          user_id: string
        }
        Update: {
          accent_hex?: string | null
          body?: string
          computed_at?: string | null
          confidence?: string
          created_at?: string | null
          data_window_days?: number | null
          expires_at?: string | null
          id?: string
          insight_type?: string
          is_dismissed?: boolean | null
          metric?: string
          title?: string
          user_id?: string
        }
        Relationships: [
          {
            foreignKeyName: "user_insights_user_id_fkey"
            columns: ["user_id"]
            isOneToOne: false
            referencedRelation: "users"
            referencedColumns: ["id"]
          },
        ]
      }
      user_memories: {
        Row: {
          memory_md: string
          updated_at: string | null
          user_id: string
        }
        Insert: {
          memory_md?: string
          updated_at?: string | null
          user_id: string
        }
        Update: {
          memory_md?: string
          updated_at?: string | null
          user_id?: string
        }
        Relationships: [
          {
            foreignKeyName: "user_memories_user_id_fkey"
            columns: ["user_id"]
            isOneToOne: true
            referencedRelation: "users"
            referencedColumns: ["id"]
          },
        ]
      }
      users: {
        Row: {
          adora2a_sensitivity: string | null
          alcohol_distribution_factor: number | null
          chronotype: string | null
          created_at: string | null
          cyp1a2_genotype: string | null
          date_of_birth: string | null
          display_name: string | null
          encrypted_api_keys: Json | null
          fitbit_user_id: string | null
          garmin_user_id: string | null
          height_cm: number | null
          id: string
          is_light_sensitive: boolean | null
          is_smoker: boolean | null
          oura_user_id: string | null
          sex: string | null
          updated_at: string | null
          uses_oral_contraceptive: boolean | null
          usual_sleep_time: string | null
          usual_wake_time: string | null
          weight_kg: number | null
        }
        Insert: {
          adora2a_sensitivity?: string | null
          alcohol_distribution_factor?: number | null
          chronotype?: string | null
          created_at?: string | null
          cyp1a2_genotype?: string | null
          date_of_birth?: string | null
          display_name?: string | null
          encrypted_api_keys?: Json | null
          fitbit_user_id?: string | null
          garmin_user_id?: string | null
          height_cm?: number | null
          id: string
          is_light_sensitive?: boolean | null
          is_smoker?: boolean | null
          oura_user_id?: string | null
          sex?: string | null
          updated_at?: string | null
          uses_oral_contraceptive?: boolean | null
          usual_sleep_time?: string | null
          usual_wake_time?: string | null
          weight_kg?: number | null
        }
        Update: {
          adora2a_sensitivity?: string | null
          alcohol_distribution_factor?: number | null
          chronotype?: string | null
          created_at?: string | null
          cyp1a2_genotype?: string | null
          date_of_birth?: string | null
          display_name?: string | null
          encrypted_api_keys?: Json | null
          fitbit_user_id?: string | null
          garmin_user_id?: string | null
          height_cm?: number | null
          id?: string
          is_light_sensitive?: boolean | null
          is_smoker?: boolean | null
          oura_user_id?: string | null
          sex?: string | null
          updated_at?: string | null
          uses_oral_contraceptive?: boolean | null
          usual_sleep_time?: string | null
          usual_wake_time?: string | null
          weight_kg?: number | null
        }
        Relationships: []
      }
      wearable_connections: {
        Row: {
          connection_type: string
          created_at: string | null
          encrypted_access_token: string | null
          encrypted_refresh_token: string | null
          external_user_id: string | null
          id: string
          is_active: boolean | null
          last_sync_at: string | null
          records_synced: number | null
          sync_error: string | null
          sync_status: string | null
          token_expires_at: string | null
          updated_at: string | null
          user_id: string
          wearable: string
        }
        Insert: {
          connection_type: string
          created_at?: string | null
          encrypted_access_token?: string | null
          encrypted_refresh_token?: string | null
          external_user_id?: string | null
          id?: string
          is_active?: boolean | null
          last_sync_at?: string | null
          records_synced?: number | null
          sync_error?: string | null
          sync_status?: string | null
          token_expires_at?: string | null
          updated_at?: string | null
          user_id: string
          wearable: string
        }
        Update: {
          connection_type?: string
          created_at?: string | null
          encrypted_access_token?: string | null
          encrypted_refresh_token?: string | null
          external_user_id?: string | null
          id?: string
          is_active?: boolean | null
          last_sync_at?: string | null
          records_synced?: number | null
          sync_error?: string | null
          sync_status?: string | null
          token_expires_at?: string | null
          updated_at?: string | null
          user_id?: string
          wearable?: string
        }
        Relationships: [
          {
            foreignKeyName: "wearable_connections_user_id_fkey"
            columns: ["user_id"]
            isOneToOne: false
            referencedRelation: "users"
            referencedColumns: ["id"]
          },
        ]
      }
    }
    Views: {
      [_ in never]: never
    }
    Functions: {
      [_ in never]: never
    }
    Enums: {
      [_ in never]: never
    }
    CompositeTypes: {
      [_ in never]: never
    }
  }
}

type DatabaseWithoutInternals = Omit<Database, "__InternalSupabase">

type DefaultSchema = DatabaseWithoutInternals[Extract<keyof Database, "public">]

export type Tables<
  DefaultSchemaTableNameOrOptions extends
    | keyof (DefaultSchema["Tables"] & DefaultSchema["Views"])
    | { schema: keyof DatabaseWithoutInternals },
  TableName extends DefaultSchemaTableNameOrOptions extends {
    schema: keyof DatabaseWithoutInternals
  }
    ? keyof (DatabaseWithoutInternals[DefaultSchemaTableNameOrOptions["schema"]]["Tables"] &
        DatabaseWithoutInternals[DefaultSchemaTableNameOrOptions["schema"]]["Views"])
    : never = never,
> = DefaultSchemaTableNameOrOptions extends {
  schema: keyof DatabaseWithoutInternals
}
  ? (DatabaseWithoutInternals[DefaultSchemaTableNameOrOptions["schema"]]["Tables"] &
      DatabaseWithoutInternals[DefaultSchemaTableNameOrOptions["schema"]]["Views"])[TableName] extends {
      Row: infer R
    }
    ? R
    : never
  : DefaultSchemaTableNameOrOptions extends keyof (DefaultSchema["Tables"] &
        DefaultSchema["Views"])
    ? (DefaultSchema["Tables"] &
        DefaultSchema["Views"])[DefaultSchemaTableNameOrOptions] extends {
        Row: infer R
      }
      ? R
      : never
    : never

export type TablesInsert<
  DefaultSchemaTableNameOrOptions extends
    | keyof DefaultSchema["Tables"]
    | { schema: keyof DatabaseWithoutInternals },
  TableName extends DefaultSchemaTableNameOrOptions extends {
    schema: keyof DatabaseWithoutInternals
  }
    ? keyof DatabaseWithoutInternals[DefaultSchemaTableNameOrOptions["schema"]]["Tables"]
    : never = never,
> = DefaultSchemaTableNameOrOptions extends {
  schema: keyof DatabaseWithoutInternals
}
  ? DatabaseWithoutInternals[DefaultSchemaTableNameOrOptions["schema"]]["Tables"][TableName] extends {
      Insert: infer I
    }
    ? I
    : never
  : DefaultSchemaTableNameOrOptions extends keyof DefaultSchema["Tables"]
    ? DefaultSchema["Tables"][DefaultSchemaTableNameOrOptions] extends {
        Insert: infer I
      }
      ? I
      : never
    : never

export type TablesUpdate<
  DefaultSchemaTableNameOrOptions extends
    | keyof DefaultSchema["Tables"]
    | { schema: keyof DatabaseWithoutInternals },
  TableName extends DefaultSchemaTableNameOrOptions extends {
    schema: keyof DatabaseWithoutInternals
  }
    ? keyof DatabaseWithoutInternals[DefaultSchemaTableNameOrOptions["schema"]]["Tables"]
    : never = never,
> = DefaultSchemaTableNameOrOptions extends {
  schema: keyof DatabaseWithoutInternals
}
  ? DatabaseWithoutInternals[DefaultSchemaTableNameOrOptions["schema"]]["Tables"][TableName] extends {
      Update: infer U
    }
    ? U
    : never
  : DefaultSchemaTableNameOrOptions extends keyof DefaultSchema["Tables"]
    ? DefaultSchema["Tables"][DefaultSchemaTableNameOrOptions] extends {
        Update: infer U
      }
      ? U
      : never
    : never

export type Enums<
  DefaultSchemaEnumNameOrOptions extends
    | keyof DefaultSchema["Enums"]
    | { schema: keyof DatabaseWithoutInternals },
  EnumName extends DefaultSchemaEnumNameOrOptions extends {
    schema: keyof DatabaseWithoutInternals
  }
    ? keyof DatabaseWithoutInternals[DefaultSchemaEnumNameOrOptions["schema"]]["Enums"]
    : never = never,
> = DefaultSchemaEnumNameOrOptions extends {
  schema: keyof DatabaseWithoutInternals
}
  ? DatabaseWithoutInternals[DefaultSchemaEnumNameOrOptions["schema"]]["Enums"][EnumName]
  : DefaultSchemaEnumNameOrOptions extends keyof DefaultSchema["Enums"]
    ? DefaultSchema["Enums"][DefaultSchemaEnumNameOrOptions]
    : never

export type CompositeTypes<
  PublicCompositeTypeNameOrOptions extends
    | keyof DefaultSchema["CompositeTypes"]
    | { schema: keyof DatabaseWithoutInternals },
  CompositeTypeName extends PublicCompositeTypeNameOrOptions extends {
    schema: keyof DatabaseWithoutInternals
  }
    ? keyof DatabaseWithoutInternals[PublicCompositeTypeNameOrOptions["schema"]]["CompositeTypes"]
    : never = never,
> = PublicCompositeTypeNameOrOptions extends {
  schema: keyof DatabaseWithoutInternals
}
  ? DatabaseWithoutInternals[PublicCompositeTypeNameOrOptions["schema"]]["CompositeTypes"][CompositeTypeName]
  : PublicCompositeTypeNameOrOptions extends keyof DefaultSchema["CompositeTypes"]
    ? DefaultSchema["CompositeTypes"][PublicCompositeTypeNameOrOptions]
    : never

export const Constants = {
  public: {
    Enums: {},
  },
} as const
