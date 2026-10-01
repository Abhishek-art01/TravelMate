import type { ReactNode } from 'react'
import { hasPermission, useAdminAccess } from './useAdminAccess'

export function PermissionGate({ permission, children, fallback = null }: {
  permission: string
  children: ReactNode
  fallback?: ReactNode
}) {
  const access = useAdminAccess()
  return access.data && hasPermission(access.data.permissions, permission) ? children : fallback
}
