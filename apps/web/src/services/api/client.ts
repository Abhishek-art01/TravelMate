import { appConfig } from '../../app/config/env'
import { supabase } from '../auth/auth'

export type ApiErrorPayload = {
  error?: {
    code?: string
    message?: string
  }
  detail?: string | { message?: string }
}

const statusMessages: Record<number, string> = {
  400: 'Some details need checking. Review the form and try again.',
  401: 'Your session has ended. Sign in again.',
  403: 'You don’t have access to this action.',
  404: 'We couldn’t find what you were looking for.',
  409: 'This change conflicts with the latest account state. Refresh and try again.',
  422: 'Some details aren’t valid yet. Review the form and try again.',
  429: 'Too many attempts. Wait a moment before trying again.',
  500: 'Something went wrong on our side. Try again shortly.',
  503: 'TravelMate is temporarily unavailable. Try again soon.',
}

export class ApiRequestError extends Error {
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
    this.name = 'ApiRequestError'
    this.status = status
    this.code = code
    this.requestId = requestId
  }
}

const API_BASE_URL = appConfig.apiBaseUrl
const REQUEST_TIMEOUT_MS = 12_000

export async function apiRequest<T>(path: string, init: RequestInit = {}): Promise<T> {
  const url = path.startsWith('http') ? path : `${API_BASE_URL}${path.startsWith('/') ? path : `/${path}`}`
  const { data } = await supabase.auth.getSession()
  const token = data.session?.access_token
  const controller = new AbortController()
  const timeout = window.setTimeout(() => controller.abort(), REQUEST_TIMEOUT_MS)
  const externalSignal = init.signal
  const abortFromExternal = () => controller.abort()
  externalSignal?.addEventListener('abort', abortFromExternal)
  if (externalSignal?.aborted) controller.abort()

  const headers = new Headers(init.headers)
  headers.set('Accept', 'application/json')

  if (!(init.body instanceof FormData)) {
    headers.set('Content-Type', 'application/json')
  }

  if (token) {
    headers.set('Authorization', `Bearer ${token}`)
  }

  let response: Response
  try {
    response = await fetch(url, {
      ...init,
      headers,
      signal: controller.signal,
    })
  } catch (error) {
    if (controller.signal.aborted && !externalSignal?.aborted) {
      throw new Error('The request timed out. Please try again.')
    }
    throw error
  } finally {
    window.clearTimeout(timeout)
    externalSignal?.removeEventListener('abort', abortFromExternal)
  }

  if (!response.ok) {
    const payload = (await response.json().catch(() => null)) as ApiErrorPayload | null
    const error = new ApiRequestError(
      statusMessages[response.status] ?? 'The request could not be completed. Please try again.',
      response.status,
      payload?.error?.code ?? 'API_ERROR',
      response.headers.get('X-Request-ID') ?? undefined,
    )
    if (response.status === 401) window.dispatchEvent(new Event('travelmate:unauthorized'))
    throw error
  }

  if (response.status === 204) return undefined as T
  return (await response.json()) as T
}
