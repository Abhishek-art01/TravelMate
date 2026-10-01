import { useNavigate } from 'react-router-dom'
import { useAdminAuth } from '../app/providers/auth-context'
import { Button } from './Button'

export function AccessDenied() {
  const { signOut } = useAdminAuth()
  const navigate = useNavigate()
  async function leaveConsole() {
    await signOut()
    navigate('/admin/login', { replace: true })
  }
  return <main className="access-state"><p className="eyebrow">ADMIN ACCESS</p><h1>Access not permitted</h1><p>You don’t have permission to access the administration console.</p><Button variant="secondary" onClick={() => void leaveConsole()}>Sign out</Button></main>
}

export function AccessUnavailable({ retry }: { retry: () => void }) {
  return <main className="access-state"><p className="eyebrow">ADMIN ACCESS</p><h1>Couldn’t verify access</h1><p>The authorization service could not be reached. Admin tools remain locked until access can be verified.</p><Button onClick={retry}>Retry authorization</Button></main>
}

export function LoadingState({ label = 'Checking secure access…' }: { label?: string }) {
  return <main className="loading-state" aria-live="polite"><span className="spinner" /><p>{label}</p></main>
}
