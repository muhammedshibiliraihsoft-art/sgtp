import { afterEach, describe, expect, it, vi } from 'vitest'
import { onRequest } from './[[path]]'

const apiOrigin = 'https://birky-staging-api.onrender.com'
const frontendOrigin = 'https://example.pages.dev'

afterEach(() => vi.unstubAllGlobals())

describe('Cloudflare Pages API proxy', () => {
  it('forwards same-origin auth requests and preserves cookie/CSRF headers', async () => {
    const fetchMock = vi.fn().mockResolvedValue(new Response(JSON.stringify({ ok: true }), {
      status: 200,
      headers: [
        ['Content-Type', 'application/json'],
        ['Set-Cookie', 'refresh=opaque; Path=/; HttpOnly; Secure; SameSite=Lax; Domain=birky-staging-api.onrender.com'],
        ['Set-Cookie', 'csrftoken=opaque; Path=/; Secure; SameSite=Lax; Domain=birky-staging-api.onrender.com'],
      ],
    }))
    vi.stubGlobal('fetch', fetchMock)
    const request = new Request(`${frontendOrigin}/api/v1/auth/token/refresh/`, {
      method: 'POST',
      headers: {
        Origin: frontendOrigin,
        Cookie: 'refresh=opaque; csrftoken=opaque',
        'X-CSRFToken': 'masked-token',
        'Content-Type': 'application/json',
      },
      body: '{}',
    })

    const response = await onRequest({ request, env: { STAGING_API_ORIGIN: apiOrigin, FRONTEND_ORIGIN: frontendOrigin } })
    const forwarded = fetchMock.mock.calls[0][0] as Request

    expect(response.status).toBe(200)
    expect(forwarded.url).toBe(`${apiOrigin}/api/v1/auth/token/refresh/`)
    expect(forwarded.headers.get('Origin')).toBe(apiOrigin)
    expect(forwarded.headers.get('Cookie')).toBe('refresh=opaque; csrftoken=opaque')
    expect(forwarded.headers.get('X-CSRFToken')).toBe('masked-token')
    expect(await forwarded.text()).toBe('{}')
    expect(response.headers.get('Cache-Control')).toBe('private, no-store')
    expect(response.headers.getSetCookie()).toEqual([
      'refresh=opaque; Path=/; HttpOnly; Secure; SameSite=Lax',
      'csrftoken=opaque; Path=/; Secure; SameSite=Lax',
    ])
  })

  it('rejects untrusted origins and refuses an invalid configured upstream', async () => {
    const fetchMock = vi.fn()
    vi.stubGlobal('fetch', fetchMock)
    const badOriginRequest = new Request(`${frontendOrigin}/api/v1/auth/login/`, {
      method: 'POST', headers: { Origin: 'https://attacker.example' }, body: '{}',
    })
    const badOrigin = await onRequest({
      request: badOriginRequest,
      env: { STAGING_API_ORIGIN: apiOrigin, FRONTEND_ORIGIN: frontendOrigin },
    })
    const badUpstream = await onRequest({
      request: new Request(`${frontendOrigin}/api/v1/auth/csrf/`),
      env: { STAGING_API_ORIGIN: 'http://insecure.example', FRONTEND_ORIGIN: frontendOrigin },
    })

    expect(badOrigin.status).toBe(403)
    expect(badUpstream.status).toBe(503)
    expect(fetchMock).not.toHaveBeenCalled()
  })
})
