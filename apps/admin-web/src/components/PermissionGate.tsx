import type { ReactNode } from 'react'
import { hasPermission, useAdminAccess } from '../app/permissions/useAdminAccess'
import { AccessDenied } from './AccessState'

export function PermissionGate({ permission, children }: { permission: string; children: ReactNode }) {
  const access = useAdminAccess()
  if (access.isLoading) return null
  if (!access.data || !hasPermission(access.data.permissions, permission)) return <AccessDenied />
  return children
}
