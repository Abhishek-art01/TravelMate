import { createClient } from '@supabase/supabase-js'
import { adminConfig, isSupabaseConfigured } from '../../app/config/env'

export const supabase = createClient(adminConfig.supabaseUrl, adminConfig.supabaseAnonKey, {
  auth: { persistSession: true, autoRefreshToken: true, detectSessionInUrl: true },
})

export async function signIn(email: string, password: string) {
  if (!isSupabaseConfigured) {
    throw new Error('Admin authentication is not configured. Add the public Supabase URL and anon key to the Admin Web environment.')
  }
  return supabase.auth.signInWithPassword({ email, password })
}

export async function signOut() {
  return supabase.auth.signOut()
}
