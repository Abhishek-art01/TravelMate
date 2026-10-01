import { useQuery } from '@tanstack/react-query'
import { adminApi } from '../../services/api/admin'
import { useAdminAuth } from '../providers/auth-context'

export function useAdminAccess() {
  const { session, user } = useAdminAuth()
  return useQuery({
    queryKey: ['admin-access', user?.id],
    queryFn: ({ signal }) => adminApi.checkAccess(signal),
    enabled: Boolean(session),
    retry: false,
    staleTime: 0,
    refetchOnWindowFocus: 'always',
  })
}

export function hasPermission(permissions: readonly string[], permission: string) {
  return permissions.includes(permission)
}
