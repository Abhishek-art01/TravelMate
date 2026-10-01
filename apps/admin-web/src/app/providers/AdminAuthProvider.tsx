import { useEffect, useState, type ReactNode } from 'react'
import { useQueryClient } from '@tanstack/react-query'
import type { Session } from '@supabase/supabase-js'
import { signOut as signOutUser, supabase } from '../../services/auth/supabase'
import { AdminAuthContext } from './auth-context'

export function AdminAuthProvider({ children }: { children: ReactNode }) {
  const [session, setSession] = useState<Session | null>(null)
  const [loading, setLoading] = useState(true)
  const queryClient = useQueryClient()

  useEffect(() => {
    let active = true
    void supabase.auth.getSession().then(({ data }) => {
      if (active) {
        setSession(data.session)
        setLoading(false)
      }
    }).catch(() => {
      if (active) setLoading(false)
    })

    const { data: { subscription } } = supabase.auth.onAuthStateChange((_event, nextSession) => {
      setSession(nextSession)
      setLoading(false)
      if (nextSession) void queryClient.invalidateQueries({ queryKey: ['admin-access'] })
      else queryClient.clear()
    })

    const onUnauthorized = () => {
      void signOutUser()
      setSession(null)
      queryClient.clear()
    }
    window.addEventListener('admin:unauthorized', onUnauthorized)

    return () => {
      active = false
      subscription.unsubscribe()
      window.removeEventListener('admin:unauthorized', onUnauthorized)
    }
  }, [queryClient])

  async function signOut() {
    await signOutUser()
    setSession(null)
    queryClient.clear()
  }

  return <AdminAuthContext.Provider value={{ session, user: session?.user ?? null, loading, signOut }}>{children}</AdminAuthContext.Provider>
}
