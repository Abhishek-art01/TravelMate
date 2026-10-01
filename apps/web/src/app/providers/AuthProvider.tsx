import { useEffect, useState, type ReactNode } from 'react'
import type { Session } from '@supabase/supabase-js'
import { getSessionSnapshot, signOut as signOutUser, supabase } from '../../services/auth/auth'
import { AuthContext } from './auth-context'

export function AuthProvider({ children }: { children: ReactNode }) {
  const [session, setSession] = useState<Session | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    let alive = true
    void getSessionSnapshot().then((snapshot) => {
      if (alive) {
        setSession(snapshot.session)
        setLoading(false)
      }
    })

    const { data: { subscription } } = supabase.auth.onAuthStateChange((_event, nextSession) => {
      setSession(nextSession)
      setLoading(false)
    })

    const handleUnauthorized = () => {
      void signOutUser()
      setSession(null)
    }
    window.addEventListener('travelmate:unauthorized', handleUnauthorized)

    return () => {
      alive = false
      subscription.unsubscribe()
      window.removeEventListener('travelmate:unauthorized', handleUnauthorized)
    }
  }, [])

  async function signOut() {
    await signOutUser()
    setSession(null)
  }

  return (
    <AuthContext.Provider value={{ session, user: session?.user ?? null, loading, signOut }}>
      {children}
    </AuthContext.Provider>
  )
}
