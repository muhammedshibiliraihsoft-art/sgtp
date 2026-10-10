import { afterEach, describe, expect, it, vi } from 'vitest'
import { authService } from './auth'
import { apiRequest, clearCredentials, setAccessToken } from './apiClient'

function json(data: unknown, status = 200) {
  return new Response(JSON.stringify(data), { status, headers: { 'Content-Type': 'application/json' } })
}

const user = {
  id: 'uuid-1', user_code: 'SGTP-USER-1', email: 'member@example.test', first_name: 'Member', last_name: '',
  is_active: true, date_joined: '2026-01-01T00:00:00Z', phone: null,
  preferred_locale: 'en' as const, appearance_preference: 'system' as const, must_change_password: false, is_main_supplier_admin: false,
}

afterEach(() => { clearCredentials(); authService.setSessionExpiredHandler(null); vi.unstubAllGlobals() })

describe('auth service contract', () => {
  it('bootstraps CSRF, logs in with identifier, and returns the backend user state', async () => {
    const fetchMock = vi.fn()
      .mockResolvedValueOnce(json({ csrf_token: 'csrf-before' }))
      .mockResolvedValueOnce(json({ access: 'access-token', user }))
    vi.stubGlobal('fetch', fetchMock)
    const session = await authService.login({ identifier: 'SGTP-USER-1', password: 'secret' })
    expect(session).toEqual({ user, passwordChangeRequired: false })
    expect(JSON.parse(fetchMock.mock.calls[1][1].body)).toEqual({ identifier: 'SGTP-USER-1', password: 'secret' })
    expect(fetchMock.mock.calls[1][1].credentials).toBe('include')
    expect(fetchMock).toHaveBeenCalledTimes(2)
  })

  it('keeps invalid-login failures distinct and does not continue to session setup', async () => {
    const fetchMock = vi.fn()
      .mockResolvedValueOnce(json({ csrf_token: 'csrf' }))
      .mockResolvedValueOnce(json({ errors: { detail: 'Invalid credentials.' } }, 401))
    vi.stubGlobal('fetch', fetchMock)
    await expect(authService.login({ identifier: 'unknown', password: 'bad' })).rejects.toMatchObject({ status: 401, message: 'Invalid credentials.' })
    expect(fetchMock).toHaveBeenCalledTimes(2)
  })

  it('restores the current user from the HttpOnly refresh response without a follow-up request', async () => {
    const fetchMock = vi.fn()
      .mockResolvedValueOnce(json({ csrf_token: 'csrf' }))
      .mockResolvedValueOnce(json({ access: 'new-access', user }))
    vi.stubGlobal('fetch', fetchMock)
    await expect(authService.restore()).resolves.toEqual({ user, passwordChangeRequired: false })
    expect(String(fetchMock.mock.calls[1][0])).toContain('/auth/token/refresh/')
    expect(fetchMock.mock.calls[1][1]).toMatchObject({ method: 'POST', credentials: 'include' })
    expect(fetchMock.mock.calls[1][1].body).toBeUndefined()
    expect(fetchMock).toHaveBeenCalledTimes(2)
    expect(String(fetchMock.mock.calls[1][0])).not.toContain('/users/me/')
  })

  it('preserves password-change-required state from the refreshed user', async () => {
    const fetchMock = vi.fn()
      .mockResolvedValueOnce(json({ csrf_token: 'csrf' }))
      .mockResolvedValueOnce(json({ access: 'new-access', user: { ...user, must_change_password: true } }))
    vi.stubGlobal('fetch', fetchMock)
    await expect(authService.restore()).resolves.toEqual({ user: { ...user, must_change_password: true }, passwordChangeRequired: true })
    expect(fetchMock).toHaveBeenCalledTimes(2)
  })

  it('returns unauthenticated when refresh fails without requesting current user', async () => {
    const fetchMock = vi.fn()
      .mockResolvedValueOnce(json({ csrf_token: 'csrf' }))
      .mockResolvedValueOnce(json({ detail: 'Token is invalid or revoked.' }, 401))
    vi.stubGlobal('fetch', fetchMock)
    await expect(authService.restore()).resolves.toBeNull()
    expect(fetchMock).toHaveBeenCalledTimes(2)
  })

  it('rejects the old access-only refresh contract without requesting current user', async () => {
    const fetchMock = vi.fn()
      .mockResolvedValueOnce(json({ csrf_token: 'csrf' }))
      .mockResolvedValueOnce(json({ access: 'new-access' }))
    vi.stubGlobal('fetch', fetchMock)
    await expect(authService.restore()).resolves.toBeNull()
    expect(fetchMock).toHaveBeenCalledTimes(2)
    expect(String(fetchMock.mock.calls[1][0])).not.toContain('/users/me/')
  })

  it('clears local credentials after logout, including a terminal server error', async () => {
    const fetchMock = vi.fn()
      .mockResolvedValueOnce(json({ csrf_token: 'csrf' }))
      .mockResolvedValueOnce(json({ errors: { detail: 'Server error.' } }, 500))
      .mockResolvedValueOnce(json({ ok: true }))
    vi.stubGlobal('fetch', fetchMock)
    setAccessToken('existing-access')
    await expect(authService.logout()).rejects.toMatchObject({ status: 500 })
    expect(fetchMock.mock.calls[1][1]).toMatchObject({ method: 'POST', credentials: 'include' })
    await apiRequest('/api/v1/private/')
    expect(new Headers(fetchMock.mock.calls[2][1].headers).get('Authorization')).toBeNull()
  })

  it('changes password using the backend field names and clears the revoked access token', async () => {
    const fetchMock = vi.fn()
      .mockResolvedValueOnce(json({ detail: 'Password changed. Sign in again.' }))
      .mockResolvedValueOnce(json({ ok: true }))
    vi.stubGlobal('fetch', fetchMock)
    setAccessToken('revoked-access')
    await authService.changePassword('old', 'new', 'new')
    expect(JSON.parse(fetchMock.mock.calls[0][1].body)).toEqual({ current_password: 'old', new_password: 'new', new_password_confirm: 'new' })
    await apiRequest('/api/v1/private/')
    expect(new Headers(fetchMock.mock.calls[1][1].headers).get('Authorization')).toBeNull()
  })

  it('clears frontend state after successful logout', async () => {
    const fetchMock = vi.fn()
      .mockResolvedValueOnce(json({ csrf_token: 'csrf' }))
      .mockResolvedValueOnce(json({ message: 'Logout successful' }))
      .mockResolvedValueOnce(json({ ok: true }))
    vi.stubGlobal('fetch', fetchMock)
    setAccessToken('live-access')
    await authService.logout()
    expect(new Headers(fetchMock.mock.calls[1][1].headers).get('Authorization')).toBe('Bearer live-access')
    await apiRequest('/api/v1/private/')
    expect(new Headers(fetchMock.mock.calls[2][1].headers).get('Authorization')).toBeNull()
  })
})
