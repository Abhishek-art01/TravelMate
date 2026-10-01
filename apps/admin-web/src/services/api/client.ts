import { adminConfig } from '../../app/config/env'
import { supabase } from '../auth/supabase'

const STATUS_MESSAGES: Record<number, string> = {
  400: 'The request could not be validated.',
  401: 'Your session expired. Sign in again.',
  403: 'You do not have permission to access the administration console.',
  404: 'This admin API is not available yet.',
  429: 'Too many requests. Try again shortly.',
  500: 'The service had a problem. Try again later.',
  503: 'The service is temporarily unavailable.',
}

export class AdminApiError extends Error {
  readonly status: number
  readonly code: string
  readonly requestId?: string

  constructor(
    message: string,
    status: number,
    code: string,
    requestId?: string,
  ) {
    super(message)
    this.name = 'AdminApiError'
    this.status = status
    this.code = code
    this.requestId = requestId
  }
}

export async function adminApiRequest<T>(path: string, init: RequestInit = {}): Promise<T> {
  const { data, error: sessionError } = await supabase.auth.getSession()
  if (sessionError) throw new Error('Could not restore your secure session. Sign in again.')
  const headers = new Headers(init.headers)
  headers.set('Accept', 'application/json')
  if (init.body && !(init.body instanceof FormData)) headers.set('Content-Type', 'application/json')
  if (data.session?.access_token) headers.set('Authorization', `Bearer ${data.session.access_token}`)

  const controller = new AbortController()
  const timer = window.setTimeout(() => controller.abort(), 12_000)
  const externalSignal = init.signal
  const cancelFromCaller = () => controller.abort()
  externalSignal?.addEventListener('abort', cancelFromCaller)
  if (externalSignal?.aborted) controller.abort()

  let response: Response
  try {
    response = await fetch(`${adminConfig.apiBaseUrl}${path}`, {
      ...init,
      headers,
      signal: controller.signal,
    })
  } catch {
    if (externalSignal?.aborted) throw new DOMException('Request cancelled.', 'AbortError')
    if (controller.signal.aborted) throw new Error('Request timed out. Try again.')
    throw new Error('Could not reach the TravelMate API. Check your connection and retry.')
  } finally {
    window.clearTimeout(timer)
    externalSignal?.removeEventListener('abort', cancelFromCaller)
  }

  if (!response.ok) {
    const body = await response.json().catch(() => null) as { error?: { code?: string } } | null
    const apiError = new AdminApiError(
      STATUS_MESSAGES[response.status] ?? 'The request failed. Try again later.',
      response.status,
      body?.error?.code ?? 'ADMIN_API_ERROR',
      response.headers.get('X-Request-ID') ?? undefined,
    )
    if (response.status === 401) window.dispatchEvent(new Event('admin:unauthorized'))
    throw apiError
  }
  if (response.status === 204) return undefined as T
  return await response.json() as T
}
