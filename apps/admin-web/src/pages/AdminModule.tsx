import { Link } from 'react-router-dom'

type AdminModuleProps = {
  title: string
  description: string
  permission: string
  requiredApi: string
  note?: string
}

export default function AdminModule({ title, description, permission, requiredApi, note }: AdminModuleProps) {
  return (
    <div className="page-content">
      <div className="page-heading"><div><p className="eyebrow">ADMIN MODULE</p><h1>{title}</h1><p className="page-subtitle">{description}</p></div><span className="permission-label"><span className="permission-dot" /> {permission}</span></div>
      <section className="module-empty"><div className="empty-mark" aria-hidden="true">—</div><p className="eyebrow">BACKEND INTEGRATION PENDING</p><h2>This module is not connected yet.</h2><p>{note ?? `TravelMate does not currently expose a ${requiredApi} API. This console will not show fabricated records or accept client-only changes.`}</p>
        {title === 'Verification' && <p className="sensitive-note">Secure verification media access is not available yet.</p>}
        <div className="module-contract"><span>REQUIRED API</span><code>{requiredApi}</code></div><Link className="back-link" to="/admin">← Back to workspace</Link>
      </section>
    </div>
  )
}
