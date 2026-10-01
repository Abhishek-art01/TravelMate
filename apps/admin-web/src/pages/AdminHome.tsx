import { useQuery } from '@tanstack/react-query'
import { adminApi } from '../services/api/admin'
import { hasPermission, useAdminAccess } from '../app/permissions/useAdminAccess'
import { AdminApiError } from '../services/api/client'
import { Button } from '../components/Button'

export default function AdminHome() {
  const access = useAdminAccess()
  const canReadSystem = access.data ? hasPermission(access.data.permissions, 'system.manage') : false
  const system = useQuery({
    queryKey: ['admin-system-status'],
    queryFn: ({ signal }) => adminApi.getSystemStatus(signal),
    enabled: canReadSystem,
    retry: false,
  })
  const systemError = system.error instanceof AdminApiError ? system.error : null
  const systemLabel = !canReadSystem
    ? 'Permission not granted'
    : system.isLoading
      ? 'Checking…'
      : system.data?.ok
        ? 'Connected'
        : systemError?.status === 403
          ? 'Permission not granted'
          : system.isError
            ? 'Unavailable'
            : 'Not checked'

  return (
    <div className="page-content">
      <div className="page-heading"><div><p className="eyebrow">OPERATIONS OVERVIEW</p><h1>Admin workspace</h1><p className="page-subtitle">Access and service state from TravelMate APIs. No operational metrics are connected yet.</p></div><span className="secure-badge"><span /> BACKEND AUTHORIZED</span></div>
      <section className="status-grid" aria-label="Connected services">
        <article className="status-card"><div className="card-heading"><span className="status-icon icon-green">✓</span><span className="eyebrow">AUTHORIZATION</span></div><h2>Verified</h2><p>Admin access confirmed by <code>/admin/access</code>.</p><div className="card-foot">{access.data?.permissions.length ?? 0} effective permissions</div></article>
        <article className="status-card"><div className="card-heading"><span className={`status-icon ${system.data?.ok ? 'icon-green' : 'icon-muted'}`}>{system.data?.ok ? '✓' : '—'}</span><span className="eyebrow">SYSTEM API</span></div><h2>{systemLabel}</h2><p>{canReadSystem ? 'Live result from the system health endpoint.' : 'This session does not include system.manage.'}</p><div className="card-foot">{canReadSystem ? 'GET /api/v1/admin/system' : 'No request made'}</div></article>
      </section>
      <section className="operations-placeholder"><div><p className="eyebrow">DATA SOURCES</p><h2>Operational metrics are not connected yet.</h2><p>User, verification, moderation, payment, and analytics APIs are not available to the admin console. No sample records or statistics are shown.</p></div><div className="source-status"><span className="source-led" /><span>Waiting for backend endpoints</span></div></section>
      {system.isError && canReadSystem && systemError && systemError.status !== 403 && <div className="inline-error" role="alert"><span>{systemError.message}</span><Button variant="secondary" onClick={() => void system.refetch()}>Retry</Button>{systemError.requestId && <code>Request {systemError.requestId}</code>}</div>}
      <section className="permission-section"><div className="section-heading"><div><p className="eyebrow">CURRENT SESSION</p><h2>Effective permissions</h2></div><span>Provided by the authorization endpoint</span></div><div className="permission-list">{(access.data?.permissions ?? []).map((permission) => <code key={permission}>{permission}</code>)}</div></section>
    </div>
  )
}
