import { lazy, Suspense } from 'react'
import { BrowserRouter, Link, Navigate, Route, Routes, useLocation } from 'react-router-dom'
import { useAuth } from '../providers/auth-context'

const AuthPage = lazy(() => import('../../pages/AuthPage'))
const OnboardingPage = lazy(() => import('../../pages/OnboardingPage'))
const HomePage = lazy(() => import('../../pages/HomePage'))
const ProfilePage = lazy(() => import('../../pages/ProfilePage'))
const PrivacyPage = lazy(() => import('../../pages/PrivacyPage'))

function RouteLoading() {
  return <main className="route-loading" aria-live="polite"><span className="spinner" />Loading TravelMate</main>
}

function Protected({ children }: { children: React.ReactNode }) {
  const { user, loading } = useAuth()
  const location = useLocation()
  if (loading) return <RouteLoading />
  return user ? <>{children}</> : <Navigate to="/login" replace state={{ from: location.pathname }} />
}

function GuestOnly({ children }: { children: React.ReactNode }) {
  const { user, loading } = useAuth()
  if (loading) return <RouteLoading />
  return user ? <Navigate to="/home" replace /> : <>{children}</>
}

function NotFound() {
  return <main className="not-found"><p className="eyebrow">404 · OFF THE MAP</p><h1>This page isn’t here.</h1><Link to="/home">Return to your travels</Link></main>
}

export function AppRouter() {
  return (
    <BrowserRouter>
      <Suspense fallback={<RouteLoading />}>
        <Routes>
          <Route path="/" element={<Navigate to="/home" replace />} />
          <Route path="/login" element={<GuestOnly><AuthPage mode="login" /></GuestOnly>} />
          <Route path="/signup" element={<GuestOnly><AuthPage mode="signup" /></GuestOnly>} />
          <Route path="/forgot-password" element={<GuestOnly><AuthPage mode="forgot" /></GuestOnly>} />
          <Route path="/auth/callback" element={<AuthPage mode="callback" />} />
          <Route path="/onboarding/*" element={<Protected><OnboardingPage /></Protected>} />
          <Route path="/home" element={<Protected><HomePage /></Protected>} />
          <Route path="/profile" element={<Protected><ProfilePage /></Protected>} />
          <Route path="/privacy" element={<Protected><PrivacyPage /></Protected>} />
          <Route path="*" element={<NotFound />} />
        </Routes>
      </Suspense>
    </BrowserRouter>
  )
}
