import type { ReactNode } from 'react'
import { PermissionGate } from './PermissionGate'

export function RequirePermission({ permission, children }: { permission: string; children: ReactNode }) {
  return <PermissionGate permission={permission}>{children}</PermissionGate>
}
