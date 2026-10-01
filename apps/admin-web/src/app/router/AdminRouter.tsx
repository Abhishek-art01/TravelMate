import { lazy, Suspense, type ReactNode } from 'react'
import { BrowserRouter, Link, Navigate, Route, Routes } from 'react-router-dom'
import { AdminAccessGate } from '../../components/AdminAccessGate'
import { LoadingState } from '../../components/AccessState'
import { RequirePermission } from '../../components/RequirePermission'
import { useAdminAuth } from '../providers/auth-context'

const AdminLogin = lazy(() => import('../../pages/AdminLogin'))
const AdminHome = lazy(() => import('../../pages/AdminHome'))
const AdminModule = lazy(() => import('../../pages/AdminModule'))
const AdminVerificationQueue = lazy(() => import('../../pages/AdminVerificationQueue'))
const AdminVerificationDetail = lazy(() => import('../../pages/AdminVerificationDetail'))

function GuestOnly({ children }: { children: ReactNode }) {
  const { user, loading } = useAdminAuth()
  if (loading) return <LoadingState label="Restoring secure session…" />
  return user ? <Navigate to="/admin" replace /> : <>{children}</>
}

function ModuleRoute({ title, description, permission, requiredApi, note }: {
  title: string
  description: string
  permission: string
  requiredApi: string
  note?: string
}) {
  return <RequirePermission permission={permission}><AdminModule title={title} description={description} permission={permission} requiredApi={requiredApi} note={note} /></RequirePermission>
}

function NotFound() {
  return <main className="access-state"><p className="eyebrow">ADMIN CONSOLE</p><h1>Page not found</h1><Link className="button button-secondary" to="/admin">Return to dashboard</Link></main>
}

export function AdminRouter() {
  return <BrowserRouter><Suspense fallback={<LoadingState label="Loading admin console…" />}><Routes>
    <Route path="/" element={<Navigate to="/admin" replace />} />
    <Route path="/admin/login" element={<GuestOnly><AdminLogin /></GuestOnly>} />
    <Route path="/admin" element={<AdminAccessGate />}>
      <Route index element={<AdminHome />} />
      <Route path="users" element={<ModuleRoute title="Users" description="User records and account actions require dedicated admin APIs." permission="users.read" requiredApi="GET /api/v1/admin/users" />} />
      <Route path="users/:userId" element={<ModuleRoute title="User detail" description="Account, profile, session, and audit sections require scoped detail APIs." permission="users.read" requiredApi="GET /api/v1/admin/users/{user_id}" />} />
      <Route path="verification" element={<RequirePermission permission="verification.read"><AdminVerificationQueue /></RequirePermission>} />
      <Route path="verification/:id" element={<RequirePermission permission="verification.read"><AdminVerificationDetail /></RequirePermission>} />
      <Route path="moderation" element={<ModuleRoute title="Moderation" description="Review reports and safety queues through the backend workflow." permission="moderation.read" requiredApi="GET /api/v1/admin/moderation" />} />
      <Route path="reports" element={<ModuleRoute title="Reports" description="Report triage and outcomes are controlled by backend moderation workflows." permission="moderation.read" requiredApi="GET /api/v1/admin/reports" />} />
      <Route path="trips" element={<ModuleRoute title="Trips" description="Trip operations will appear when TravelMate trip APIs are available." permission="travel.read" requiredApi="GET /api/v1/admin/trips" />} />
      <Route path="destinations" element={<ModuleRoute title="Destinations" description="Destination content management requires a server-backed catalog." permission="travel.manage" requiredApi="GET /api/v1/admin/destinations" />} />
      <Route path="payments" element={<ModuleRoute title="Payments" description="Only safe provider transaction metadata will be shown when available." permission="payments.read" requiredApi="GET /api/v1/admin/payments" />} />
      <Route path="support" element={<ModuleRoute title="Support" description="Support queues require a connected ticket workflow." permission="support.read" requiredApi="GET /api/v1/admin/support" />} />
      <Route path="grievances" element={<ModuleRoute title="Grievances" description="Complaint handling requires backend-owned assignment, acknowledgement, and resolution state." permission="support.manage" requiredApi="GET /api/v1/admin/grievances" />} />
      <Route path="analytics" element={<ModuleRoute title="Analytics" description="Metrics will be shown only after an authenticated analytics API is available." permission="analytics.read" requiredApi="GET /api/v1/admin/analytics" />} />
      <Route path="security" element={<ModuleRoute title="Security center" description="Security events and incident controls require a backend security API." permission="security.read" requiredApi="GET /api/v1/admin/security/events" />} />
      <Route path="security/sessions" element={<ModuleRoute title="Admin sessions" description="Privileged session review and revocation are not exposed yet." permission="security.manage" requiredApi="GET /api/v1/admin/security/sessions" />} />
      <Route path="audit" element={<ModuleRoute title="Audit logs" description="Audit records will be rendered only from the protected audit API." permission="audit.read" requiredApi="GET /api/v1/admin/audit" />} />
      <Route path="settings" element={<ModuleRoute title="Settings" description="System configuration is backend-controlled and is not exposed for editing." permission="system.manage" requiredApi="GET /api/v1/admin/settings" />} />
      <Route path="settings/roles" element={<ModuleRoute title="Roles & permissions" description="Role changes are unavailable until a backend-managed, super-admin-only workflow exists." permission="system.manage" requiredApi="GET /api/v1/admin/roles" />} />
    </Route>
    <Route path="*" element={<NotFound />} />
  </Routes></Suspense></BrowserRouter>
}
