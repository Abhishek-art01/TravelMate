import { createContext, useContext } from 'react'
import type { Session, User } from '@supabase/supabase-js'

export type AdminAuthState = {
  session: Session | null
  user: User | null
  loading: boolean
  signOut: () => Promise<void>
}

export const AdminAuthContext = createContext<AdminAuthState | null>(null)

export function useAdminAuth() {
  const value = useContext(AdminAuthContext)
  if (!value) throw new Error('useAdminAuth must be used inside AdminAuthProvider')
  return value
}
