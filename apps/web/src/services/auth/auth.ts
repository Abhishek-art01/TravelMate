import { createClient, type Session, type User } from '@supabase/supabase-js'
import { appConfig, isSupabaseConfigured } from '../../app/config/env'

export const supabase = createClient(appConfig.supabaseUrl, appConfig.supabaseAnonKey, {
  auth: {
    persistSession: true,
    autoRefreshToken: true,
    detectSessionInUrl: true,
  },
})

export type AuthResult = {
  session: Session | null
  user: User | null
}

function requireSupabaseConfiguration() {
  if (!isSupabaseConfigured) {
    throw new Error('Authentication is not configured yet. Add the public Supabase URL and anon key to the web environment.')
  }
}

export async function signInWithPassword(email: string, password: string) {
  requireSupabaseConfiguration()
  return supabase.auth.signInWithPassword({ email, password })
}

export async function signUpWithEmail(email: string, password: string, metadata: Record<string, unknown> = {}) {
  requireSupabaseConfiguration()
  return supabase.auth.signUp({
    email,
    password,
    options: { data: metadata },
  })
}

export async function signInWithOAuth(provider: 'google' | 'apple' | 'instagram') {
  requireSupabaseConfiguration()
  return supabase.auth.signInWithOAuth({
    provider,
    options: {
      redirectTo: `${window.location.origin}/auth/callback`,
    },
  })
}

export async function sendPasswordReset(email: string) {
  requireSupabaseConfiguration()
  return supabase.auth.resetPasswordForEmail(email, {
    redirectTo: `${window.location.origin}/auth/callback`,
  })
}

export async function signOut() {
  return supabase.auth.signOut()
}

export async function getSessionSnapshot(): Promise<AuthResult> {
  const { data, error } = await supabase.auth.getSession()

  if (error) {
    return { session: null, user: null }
  }

  return {
    session: data.session,
    user: data.session?.user ?? null,
  }
}
