import { ApiError, apiRequest, bootstrapCsrf, clearCredentials, refreshSession, setAccessToken, setUnauthorizedHandler } from './apiClient'

export type BackendUser = {
  id: string
  user_code: string
  email: string | null
  first_name: string
  last_name: string
  is_active: boolean
  date_joined: string
  phone: string | null
  preferred_locale: 'en' | 'ar-KW' | 'bn' | 'ur' | null
  appearance_preference: 'system' | 'light' | 'dark'
  must_change_password: boolean
  is_main_supplier_admin: boolean
}

export type AuthSession = { user: BackendUser | null; passwordChangeRequired: boolean }
export type LoginCredentials = { identifier: string; password: string }

export const authService = {
  setSessionExpiredHandler(handler: (() => void) | null) {
    setUnauthorizedHandler(handler)
  },

  async login(credentials: LoginCredentials): Promise<AuthSession> {
    await bootstrapCsrf()
    const data = await apiRequest<{ access: string; user: BackendUser }>('/api/v1/auth/login/', {
      method: 'POST', body: credentials, authenticated: false, retryUnauthorized: false,
    })
    if (!data.access || !data.user) throw new ApiError('The sign-in response was incomplete.', 502, 'invalid_login_response')
    setAccessToken(data.access)
    // Login does not rotate the CSRF cookie. Keep using the masked token from the
    // pre-login bootstrap instead of making a redundant second round trip.
    return { user: data.user, passwordChangeRequired: data.user.must_change_password }
  },

  async requestPasswordReset(email: string): Promise<void> {
    await apiRequest('/api/v1/auth/password/reset/', {
      method: 'POST', body: { email }, authenticated: false, retryUnauthorized: false,
    })
  },

  async confirmPasswordReset(uid: string, token: string, newPassword: string, newPasswordConfirm: string): Promise<void> {
    await apiRequest('/api/v1/auth/password/reset/confirm/', {
      method: 'POST',
      body: { uid, token, new_password: newPassword, new_password_confirm: newPasswordConfirm },
      authenticated: false,
      retryUnauthorized: false,
    })
    clearCredentials()
  },

  async restore(): Promise<AuthSession | null> {
    try {
      await refreshSession()
      const user = await apiRequest<BackendUser>('/api/v1/auth/users/me/')
      return { user, passwordChangeRequired: user.must_change_password }
    } catch (error) {
      if (error instanceof ApiError && error.status === 403 && (error.code === 'password_change_required' || error.message === 'Change the initial password before using this operation.')) {
        return { user: null, passwordChangeRequired: true }
      }
      clearCredentials()
      if (error instanceof ApiError && error.status === 401) return null
      if (error instanceof ApiError && error.code === 'network_unavailable') throw error
      return null
    }
  },

  async changePassword(currentPassword: string, newPassword: string, newPasswordConfirm: string): Promise<void> {
    await apiRequest('/api/v1/auth/users/password/change/', {
      method: 'POST', body: { current_password: currentPassword, new_password: newPassword, new_password_confirm: newPasswordConfirm },
    })
    clearCredentials()
  },

  async logout(): Promise<void> {
    try {
      await bootstrapCsrf()
      await apiRequest('/api/v1/auth/logout/', { method: 'POST', body: {} })
    } finally {
      clearCredentials()
    }
  },
}
