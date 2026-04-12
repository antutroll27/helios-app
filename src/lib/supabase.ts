import { createClient } from '@supabase/supabase-js'

// TODO: replace `any` with generated Database type when schema types are generated
export const supabase = createClient<any>(
  import.meta.env.VITE_SUPABASE_URL,
  import.meta.env.VITE_SUPABASE_ANON_KEY
)
