export const adminConfig = {
  apiBaseUrl: (import.meta.env.VITE_API_BASE_URL as string | undefined) ?? 'http://localhost:8000/api/v1',
  supabaseUrl: (import.meta.env.VITE_SUPABASE_URL as string | undefined) ?? 'https://placeholder.supabase.co',
  supabaseAnonKey: (import.meta.env.VITE_SUPABASE_ANON_KEY as string | undefined) ?? 'placeholder-anon-key',
} as const

export const isSupabaseConfigured =
  !adminConfig.supabaseUrl.includes('placeholder') &&
  !adminConfig.supabaseAnonKey.includes('placeholder')
