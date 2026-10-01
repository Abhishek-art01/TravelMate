import { adminApiRequest } from './client'

export type AdminAccess = {
  authorized: true
  permissions: string[]
}

export type SystemStatus = {
  ok: boolean
  service: string
  role: string
  permissions: string[]
}

export const adminApi = {
  checkAccess: (signal?: AbortSignal) => adminApiRequest<AdminAccess>('/admin/access', { signal }),
  getSystemStatus: (signal?: AbortSignal) => adminApiRequest<SystemStatus>('/admin/system', { signal }),
}
