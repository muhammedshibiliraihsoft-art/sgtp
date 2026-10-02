import { afterEach, describe, expect, it, vi } from 'vitest'
import { apiRequest, bootstrapCsrf, clearCredentials, setAccessToken, setUnauthorizedHandler } from './apiClient'

function json(data: unknown, status = 200) {
  return new Response(JSON.stringify(data), { status, headers: { 'Content-Type': 'application/json' } })
}

afterEach(() => { clearCredentials(); setUnauthorizedHandler(null); vi.unstubAllGlobals() })

describe('shared API client authentication', () => {
  it('bootstraps CSRF with credentialed cookies and returns only the masked token', async () => {
    const fetchMock = vi.fn().mockResolvedValue(json({ csrf_token: 'masked-csrf' }))
    vi.stubGlobal('fetch', fetchMock)
    await expect(bootstrapCsrf()).resolves.toBe('masked-csrf')
    expect(fetchMock.mock.calls[0][1]).toMatchObject({ method: 'GET', credentials: 'include' })
  })

  it('reports an HTML fallback instead of throwing when the CSRF proxy route is missing', async () => {
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue(new Response('<!doctype html><html></html>', {
      status: 200,
      headers: { 'Content-Type': 'text/html' },
    })))
    await expect(bootstrapCsrf()).rejects.toMatchObject({
      status: 502,
      code: 'invalid_csrf_response',
      message: 'The API proxy returned a webpage instead of the CSRF response. Check the frontend API proxy configuration.',
    })
  })

  it('sends the access token in memory and never persists it', async () => {
    const fetchMock = vi.fn().mockResolvedValue(json({ ok: true }))
    vi.stubGlobal('fetch', fetchMock)
    setAccessToken('access-secret')
    await apiRequest('/api/v1/private/')
    expect(new Headers(fetchMock.mock.calls[0][1].headers).get('Authorization')).toBe('Bearer access-secret')
    expect(localStorage.getItem('access-token')).toBeNull()
    expect(sessionStorage.getItem('access-token')).toBeNull()
  })

  it('shares concurrent refresh attempts and retries each request once', async () => {
    const fetchMock = vi.fn()
      .mockResolvedValueOnce(json({ detail: 'expired' }, 401))
      .mockResolvedValueOnce(json({ detail: 'expired' }, 401))
      .mockResolvedValueOnce(json({ csrf_token: 'csrf' }))
      .mockResolvedValueOnce(json({ access: 'fresh-access' }))
      .mockResolvedValueOnce(json({ value: 1 }))
      .mockResolvedValueOnce(json({ value: 2 }))
    vi.stubGlobal('fetch', fetchMock)
    const results = await Promise.all([
      apiRequest<{ value: number }>('/api/v1/one/'),
      apiRequest<{ value: number }>('/api/v1/two/'),
    ])
    expect(results.map((result) => result.value)).toEqual([1, 2])
    expect(fetchMock.mock.calls.filter(([url]) => String(url).includes('/token/refresh/'))).toHaveLength(1)
  })

  it('keeps backend error status and message available to callers', async () => {
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue(json({ errors: { detail: 'Invalid credentials.' } }, 401)))
    await expect(apiRequest('/api/v1/private/', { authenticated: false })).rejects.toMatchObject({
      status: 401, message: 'Invalid credentials.',
    })
  })

  it('does not retry a request more than once after refresh', async () => {
    const expired = vi.fn()
    setUnauthorizedHandler(expired)
    const fetchMock = vi.fn()
      .mockResolvedValueOnce(json({ detail: 'expired' }, 401))
      .mockResolvedValueOnce(json({ csrf_token: 'csrf' }))
      .mockResolvedValueOnce(json({ access: 'fresh-access' }))
      .mockResolvedValueOnce(json({ detail: 'still unauthorized' }, 401))
    vi.stubGlobal('fetch', fetchMock)
    await expect(apiRequest('/api/v1/private/')).rejects.toMatchObject({ status: 401 })
    expect(fetchMock).toHaveBeenCalledTimes(4)
    expect(expired).toHaveBeenCalledOnce()
  })

  it('clears auth and signals the app when a revoked refresh cookie fails', async () => {
    const expired = vi.fn()
    setUnauthorizedHandler(expired)
    const fetchMock = vi.fn()
      .mockResolvedValueOnce(json({ detail: 'expired' }, 401))
      .mockResolvedValueOnce(json({ csrf_token: 'csrf' }))
      .mockResolvedValueOnce(json({ errors: { detail: 'Token is invalid or revoked.' } }, 401))
    vi.stubGlobal('fetch', fetchMock)
    setAccessToken('expired-access')
    await expect(apiRequest('/api/v1/private/')).rejects.toMatchObject({ status: 401 })
    expect(expired).toHaveBeenCalledOnce()
  })

  it('discards private responses that arrive after the account session changes', async () => {
    let resolveResponse!: (response: Response) => void
    const fetchMock = vi.fn().mockReturnValue(new Promise<Response>((resolve) => { resolveResponse = resolve }))
    vi.stubGlobal('fetch', fetchMock)
    setAccessToken('account-a-access')
    const pending = apiRequest('/api/v1/private/')
    setAccessToken('account-b-access')
    resolveResponse(json({ privateData: 'account A' }))
    await expect(pending).rejects.toMatchObject({ code: 'session_changed' })
  })
})
