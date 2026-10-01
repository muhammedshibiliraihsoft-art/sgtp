type ApiEnvelope = { errors?: unknown; detail?: unknown; code?: unknown }

export class ApiError extends Error {
  readonly status: number
  readonly code?: string
  readonly payload?: unknown

  constructor(
    message: string,
    status: number,
    code?: string,
    payload?: unknown,
  ) {
    super(message)
    this.name = 'ApiError'
    this.status = status
    this.code = code
    this.payload = payload
  }
}

let accessToken: string | null = null
let csrfToken: string | null = null
let refreshPromise: Promise<string> | null = null
let unauthorizedHandler: (() => void) | null = null
let authGeneration = 0

export function setAccessToken(token: string | null) {
  authGeneration += 1
  accessToken = token
}

export function setUnauthorizedHandler(handler: (() => void) | null) {
  unauthorizedHandler = handler
}

export function clearCredentials() {
  authGeneration += 1
  accessToken = null
  csrfToken = null
}

function apiUrl(path: string) {
  return path.startsWith('/') ? path : `/${path}`
}

function extractMessage(payload: unknown, fallback: string): { message: string; code?: string } {
  const outer = payload && typeof payload === 'object' ? payload as ApiEnvelope : {}
  const errors = outer.errors && typeof outer.errors === 'object' ? outer.errors as ApiEnvelope : outer
  const code = typeof errors.code === 'string' ? errors.code : undefined
  const detail = errors.detail
  if (typeof detail === 'string') return { message: detail, code }
  if (Array.isArray(detail) && typeof detail[0] === 'string') return { message: detail[0], code }
  if (errors && typeof errors === 'object') {
    for (const value of Object.values(errors)) {
      if (Array.isArray(value) && typeof value[0] === 'string') return { message: value[0], code }
    }
  }
  return { message: fallback, code }
}

async function readResponse<T>(response: Response): Promise<T> {
  let payload: unknown
  try {
    payload = await response.json()
  } catch {
    payload = undefined
  }
  if (!response.ok) {
    const parsed = extractMessage(payload, response.status >= 500 ? 'The service is unavailable. Please try again.' : 'The request could not be completed.')
    throw new ApiError(parsed.message, response.status, parsed.code, payload)
  }
  return payload as T
}

export async function bootstrapCsrf(): Promise<string> {
  let response: Response
  try {
    response = await fetch(apiUrl('/api/v1/auth/csrf/'), { method: 'GET', credentials: 'include', headers: { Accept: 'application/json' } })
  } catch {
    throw new ApiError('Unable to reach the service. Check your connection and try again.', 0, 'network_unavailable')
  }
  const data = await readResponse<{ csrf_token: string }>(response)
  if (!data || typeof data !== 'object' || typeof data.csrf_token !== 'string' || !data.csrf_token) {
    throw new ApiError(
      'The API proxy returned a webpage instead of the CSRF response. Check the frontend API proxy configuration.',
      502,
      'invalid_csrf_response',
    )
  }
  csrfToken = data.csrf_token
  return csrfToken
}

async function refreshAccessToken(): Promise<string> {
  if (!refreshPromise) {
    refreshPromise = (async () => {
      const csrf = await bootstrapCsrf()
      let response: Response
      try {
        response = await fetch(apiUrl('/api/v1/auth/token/refresh/'), {
          method: 'POST', credentials: 'include',
          headers: { Accept: 'application/json', 'X-CSRFToken': csrf },
        })
      } catch {
        throw new ApiError('Unable to reach the service. Check your connection and try again.', 0, 'network_unavailable')
      }
      const data = await readResponse<{ access: string }>(response)
      accessToken = data.access
      return data.access
    })().catch((error: unknown) => {
      clearCredentials()
      unauthorizedHandler?.()
      throw error
    }).finally(() => { refreshPromise = null })
  }
  return refreshPromise
}

type RequestOptions = Omit<RequestInit, 'body'> & { body?: unknown; authenticated?: boolean; retryUnauthorized?: boolean }

export async function apiRequest<T>(path: string, options: RequestOptions = {}): Promise<T> {
  const { authenticated = true, retryUnauthorized = true, headers: suppliedHeaders, body, ...init } = options
  const requestGeneration = authGeneration
  const tokenUsed = authenticated ? accessToken : null
  const headers = new Headers(suppliedHeaders)
  headers.set('Accept', 'application/json')
  if (body !== undefined) headers.set('Content-Type', 'application/json')
  if (authenticated && accessToken) headers.set('Authorization', `Bearer ${accessToken}`)
  if (csrfToken && ['POST', 'PUT', 'PATCH', 'DELETE'].includes((init.method ?? 'GET').toUpperCase())) headers.set('X-CSRFToken', csrfToken)

  let response: Response
  try {
    response = await fetch(apiUrl(path), {
      ...init, headers, credentials: 'include',
      ...(body !== undefined ? { body: JSON.stringify(body) } : {}),
    })
  } catch {
    throw new ApiError('Unable to reach the service. Check your connection and try again.', 0, 'network_unavailable')
  }

  if (authenticated && requestGeneration !== authGeneration) {
    throw new ApiError('Your session changed. Please retry the request.', 401, 'session_changed')
  }
  if (response.status === 401 && authenticated && retryUnauthorized) {
    if (accessToken && accessToken !== tokenUsed) {
      return apiRequest<T>(path, { ...options, headers: { ...Object.fromEntries(headers.entries()), Authorization: `Bearer ${accessToken}` }, retryUnauthorized: false })
    }
    const token = await refreshAccessToken()
    return apiRequest<T>(path, { ...options, headers: { ...Object.fromEntries(headers.entries()), Authorization: `Bearer ${token}` }, retryUnauthorized: false })
  }
  if (response.status === 401 && authenticated) {
    clearCredentials()
    unauthorizedHandler?.()
  }
  return readResponse<T>(response)
}

export async function refreshSession(): Promise<string> {
  return refreshAccessToken()
}
