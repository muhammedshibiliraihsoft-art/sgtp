import { ApiError, apiRequest, bootstrapCsrf, clearCredentials, refreshSession, setAccessToken, setUnauthorizedHandler } from './apiClient'

export type BackendUser = {
  id: string
  user_code: string
  login_id?: string | null
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

function isBackendUser(value: unknown): value is BackendUser {
  if (!value || typeof value !== 'object' || Array.isArray(value)) return false
  const user = value as Record<string, unknown>
  return typeof user.id === 'string'
    && typeof user.user_code === 'string'
    && (user.login_id === undefined || user.login_id === null || typeof user.login_id === 'string')
    && (user.email === null || typeof user.email === 'string')
    && typeof user.first_name === 'string'
    && typeof user.last_name === 'string'
    && typeof user.is_active === 'boolean'
    && typeof user.date_joined === 'string'
    && (user.phone === null || typeof user.phone === 'string')
    && (user.preferred_locale === null || ['en', 'ar-KW', 'bn', 'ur'].includes(user.preferred_locale as string))
    && ['system', 'light', 'dark'].includes(user.appearance_preference as string)
    && typeof user.must_change_password === 'boolean'
    && typeof user.is_main_supplier_admin === 'boolean'
}

export const authService = {
  setSessionExpiredHandler(handler: (() => void) | null) {
    setUnauthorizedHandler(handler)
  },

  async login(credentials: LoginCredentials): Promise<AuthSession> {
    await bootstrapCsrf()
    const data = await apiRequest<{ access: string; user: BackendUser }>('/api/v1/auth/login/', {
      method: 'POST', body: credentials, authenticated: false, retryUnauthorized: false,
    })
    if (typeof data.access !== 'string' || !data.access || !isBackendUser(data.user)) {
      throw new ApiError('The sign-in response was incomplete.', 502, 'invalid_login_response')
    }
    setAccessToken(data.access)
    return { user: data.user, passwordChangeRequired: data.user.must_change_password }
  },

  async restore(): Promise<AuthSession | null> {
    try {
      const { user } = await refreshSession<BackendUser>()
      if (!isBackendUser(user)) {
        throw new ApiError('The session refresh response was incomplete.', 502, 'invalid_refresh_response')
      }
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
