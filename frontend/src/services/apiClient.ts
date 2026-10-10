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
type RefreshResponse<TUser = unknown> = { access: string; user: TUser }
let refreshPromise: Promise<RefreshResponse> | null = null
let unauthorizedHandler: (() => void) | null = null
let authGeneration = 0
const inFlightReads = new Map<string, Promise<unknown>>()

export function setAccessToken(token: string | null) {
  authGeneration += 1
  accessToken = token
  inFlightReads.clear()
}

export function setUnauthorizedHandler(handler: (() => void) | null) {
  unauthorizedHandler = handler
}

export function clearCredentials() {
  authGeneration += 1
  accessToken = null
  csrfToken = null
  inFlightReads.clear()
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

async function refreshAccessToken(): Promise<RefreshResponse> {
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
      const data = await readResponse<RefreshResponse>(response)
      if (
        !data
        || typeof data.access !== 'string'
        || !data.access
        || !data.user
        || typeof data.user !== 'object'
        || Array.isArray(data.user)
      ) {
        throw new ApiError(
          'The session refresh response was incomplete.',
          502,
          'invalid_refresh_response',
        )
      }
      accessToken = data.access
      return data
    })().catch((error: unknown) => {
      clearCredentials()
      unauthorizedHandler?.()
      throw error
    }).finally(() => { refreshPromise = null })
  }
  return refreshPromise
}

type RequestOptions = Omit<RequestInit, 'body'> & { authenticated?: boolean; retryUnauthorized?: boolean }

async function coreRequest(path: string, options: RequestOptions, body?: BodyInit | null): Promise<Response> {
  const { authenticated = true, retryUnauthorized = true, headers: suppliedHeaders, ...init } = options
  const requestGeneration = authGeneration
  const tokenUsed = authenticated ? accessToken : null
  const headers = new Headers(suppliedHeaders)
  if (authenticated && accessToken) headers.set('Authorization', `Bearer ${accessToken}`)
  if (csrfToken && ['POST', 'PUT', 'PATCH', 'DELETE'].includes((init.method ?? 'GET').toUpperCase())) headers.set('X-CSRFToken', csrfToken)

  let response: Response
  try {
    response = await fetch(apiUrl(path), {
      ...init, headers, credentials: 'include', body
    })
  } catch {
    throw new ApiError('Unable to reach the service. Check your connection and try again.', 0, 'network_unavailable')
  }

  if (authenticated && requestGeneration !== authGeneration) {
    throw new ApiError('Your session changed. Please retry the request.', 401, 'session_changed')
  }
  if (response.status === 401 && authenticated && retryUnauthorized) {
    if (accessToken && accessToken !== tokenUsed) {
      return coreRequest(path, { ...options, retryUnauthorized: false }, body)
    }
    await refreshAccessToken()
    return coreRequest(path, { ...options, retryUnauthorized: false }, body)
  }
  if (response.status === 401 && authenticated) {
    clearCredentials()
    unauthorizedHandler?.()
  }
  return response
}

type JsonRequestOptions = RequestOptions & { body?: unknown }

export async function apiRequest<T>(path: string, options: JsonRequestOptions = {}): Promise<T> {
  if (Object.keys(options).length === 0) {
    const key = `${authGeneration}:${apiUrl(path)}`
    const pending = inFlightReads.get(key)
    if (pending) return pending as Promise<T>
    const read = coreRequest(path, { headers: { Accept: 'application/json' } })
      .then(response => readResponse<T>(response))
    inFlightReads.set(key, read)
    try {
      return await read
    } finally {
      if (inFlightReads.get(key) === read) inFlightReads.delete(key)
    }
  }
  const { body, headers, ...rest } = options
  if ((rest.method ?? 'GET').toUpperCase() !== 'GET') inFlightReads.clear()
  const requestHeaders = new Headers(headers)
  requestHeaders.set('Accept', 'application/json')
  let requestBody: BodyInit | undefined = undefined
  if (body !== undefined) {
    requestHeaders.set('Content-Type', 'application/json')
    requestBody = JSON.stringify(body)
  }
  const response = await coreRequest(path, { ...rest, headers: requestHeaders }, requestBody)
  return readResponse<T>(response)
}

export async function multipartRequest<T>(path: string, formData: FormData, options: RequestOptions = {}): Promise<T> {
  const { headers, ...rest } = options
  const requestHeaders = new Headers(headers)
  requestHeaders.set('Accept', 'application/json')
  const response = await coreRequest(path, { ...rest, method: 'POST', headers: requestHeaders }, formData)
  return readResponse<T>(response)
}

export async function binaryRequest(path: string, options: RequestOptions = {}): Promise<Blob> {
  const response = await coreRequest(path, { ...options, method: 'GET' })
  if (!response.ok) {
    let payload: unknown
    try { payload = await response.json() } catch {}
    const parsed = extractMessage(payload, response.status >= 500 ? 'The service is unavailable. Please try again.' : 'The request could not be completed.')
    throw new ApiError(parsed.message, response.status, parsed.code, payload)
  }
  return response.blob()
}

export async function refreshSession<TUser = unknown>(): Promise<RefreshResponse<TUser>> {
  return await refreshAccessToken() as RefreshResponse<TUser>
}
