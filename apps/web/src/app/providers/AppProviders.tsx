import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { useState, type ReactNode } from 'react'
import '../../i18n'
import { AuthProvider } from './AuthProvider'

export function AppProviders({ children }: { children: ReactNode }) {
  const [queryClient] = useState(() => new QueryClient({
    defaultOptions: { queries: { retry: 1, refetchOnWindowFocus: false, staleTime: 30_000 } },
  }))

  return (
    <QueryClientProvider client={queryClient}>
      <AuthProvider>{children}</AuthProvider>
    </QueryClientProvider>
  )
}
