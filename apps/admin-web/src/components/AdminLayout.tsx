import { useState } from 'react'
import { Link, NavLink, Outlet, useNavigate } from 'react-router-dom'
import { useAdminAccess } from '../app/permissions/useAdminAccess'
import { useAdminAuth } from '../app/providers/auth-context'
import { Button } from './Button'

const navigation = [
  { label: 'Dashboard', to: '/admin', permission: null },
  { label: 'Users', to: '/admin/users', permission: 'users.read' },
  { label: 'Verification', to: '/admin/verification', permission: 'verification.read' },
  { label: 'Moderation', to: '/admin/moderation', permission: 'moderation.read' },
  { label: 'Reports', to: '/admin/reports', permission: 'moderation.read' },
  { label: 'Trips', to: '/admin/trips', permission: 'travel.read' },
  { label: 'Destinations', to: '/admin/destinations', permission: 'travel.manage' },
  { label: 'Payments', to: '/admin/payments', permission: 'payments.read' },
  { label: 'Support', to: '/admin/support', permission: 'support.read' },
  { label: 'Grievances', to: '/admin/grievances', permission: 'support.manage' },
  { label: 'Analytics', to: '/admin/analytics', permission: 'analytics.read' },
  { label: 'Security', to: '/admin/security', permission: 'security.read' },
  { label: 'Admin sessions', to: '/admin/security/sessions', permission: 'security.manage' },
  { label: 'Audit logs', to: '/admin/audit', permission: 'audit.read' },
  { label: 'Settings', to: '/admin/settings', permission: 'system.manage' },
  { label: 'Roles & permissions', to: '/admin/settings/roles', permission: 'system.manage' },
]

export function AdminLayout() {
  const access = useAdminAccess()
  const { signOut } = useAdminAuth()
  const navigate = useNavigate()
  const [drawerOpen, setDrawerOpen] = useState(false)
  const available = navigation.filter((item) => item.permission === null || access.data?.permissions.includes(item.permission))

  async function logout() {
    await signOut()
    navigate('/admin/login', { replace: true })
  }

  return (
    <div className="admin-shell">
      <header className="topbar">
        <button className="menu-toggle" type="button" aria-expanded={drawerOpen} aria-controls="admin-sidebar" aria-label={drawerOpen ? 'Close navigation' : 'Open navigation'} onClick={() => setDrawerOpen((open) => !open)}>{drawerOpen ? '×' : '☰'}</button>
        <Link className="admin-brand" to="/admin"><span className="admin-mark">TM</span><span><strong>TravelMate</strong><small>ADMIN CONSOLE</small></span></Link>
        <label className="global-search"><span aria-hidden="true">⌕</span><input aria-label="Global admin search" disabled placeholder="Search resources" /><span className="search-note">Not connected</span></label>
        <div className="topbar-actions"><span className="admin-session-label">Verified session</span><Button variant="quiet" onClick={() => void logout()}>Sign out <span aria-hidden="true">↗</span></Button></div>
      </header>
      {drawerOpen && <button className="drawer-scrim" aria-label="Close navigation" onClick={() => setDrawerOpen(false)} />}
      <aside id="admin-sidebar" className={`sidebar ${drawerOpen ? 'sidebar-open' : ''}`} aria-label="Administration navigation">
        <p className="sidebar-caption">OPERATIONS</p>
        <nav>{available.map((item) => <NavLink key={item.to} to={item.to} end={item.to === '/admin'} onClick={() => setDrawerOpen(false)}>{item.label}</NavLink>)}</nav>
        <div className="sidebar-bottom"><span className="session-indicator" />Authorization checked by TravelMate API</div>
      </aside>
      <main className="main-panel"><Outlet /></main>
    </div>
  )
}
