export const appConfig = {
  apiBaseUrl:
    (import.meta.env.VITE_API_BASE_URL as string | undefined) ??
    'http://localhost:8000/api/v1',
  supabaseUrl:
    (import.meta.env.VITE_SUPABASE_URL as string | undefined) ??
    'https://placeholder.supabase.co',
  supabaseAnonKey:
    (import.meta.env.VITE_SUPABASE_ANON_KEY as string | undefined) ??
    'placeholder-anon-key',
} as const

export const isSupabaseConfigured =
  Boolean(appConfig.supabaseUrl) &&
  Boolean(appConfig.supabaseAnonKey) &&
  !appConfig.supabaseUrl.includes('placeholder') &&
  !appConfig.supabaseAnonKey.includes('placeholder')

export const configuredOAuthProviders = ((import.meta.env.VITE_AUTH_PROVIDERS as string | undefined) ?? '')
  .split(',')
  .map((provider) => provider.trim().toLowerCase())
  .filter((provider): provider is 'google' | 'apple' | 'instagram' => provider === 'google' || provider === 'apple' || provider === 'instagram')
