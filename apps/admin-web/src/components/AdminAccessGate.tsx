import { Navigate, useLocation } from 'react-router-dom'
import { useAdminAccess } from '../app/permissions/useAdminAccess'
import { useAdminAuth } from '../app/providers/auth-context'
import { AccessDenied, AccessUnavailable, LoadingState } from './AccessState'
import { AdminLayout } from './AdminLayout'
import { AdminApiError } from '../services/api/client'

export function AdminAccessGate() {
  const { user, loading } = useAdminAuth()
  const access = useAdminAccess()
  const location = useLocation()

  if (loading) return <LoadingState label="Restoring secure session…" />
  if (!user) return <Navigate to="/admin/login" replace state={{ from: location.pathname }} />
  if (access.isLoading) return <LoadingState />
  if (access.error instanceof AdminApiError && access.error.status === 403) return <AccessDenied />
  if (access.error instanceof AdminApiError && access.error.status === 401) return <Navigate to="/admin/login" replace />
  if (access.isError) return <AccessUnavailable retry={() => void access.refetch()} />
  if (!access.data?.authorized) return <AccessDenied />

  return <AdminLayout />
}
