import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { useState, type ReactNode } from 'react'
import { AdminAuthProvider } from './AdminAuthProvider'

export function AdminProviders({ children }: { children: ReactNode }) {
  const [client] = useState(() => new QueryClient({
    defaultOptions: { queries: { retry: 1, staleTime: 30_000, refetchOnWindowFocus: true } },
  }))
  return <QueryClientProvider client={client}><AdminAuthProvider>{children}</AdminAuthProvider></QueryClientProvider>
}
