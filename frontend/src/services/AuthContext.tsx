import { useEffect, useMemo, useState } from 'react'
import type { ReactNode } from 'react'
import { authService, type AuthSession } from './auth'
import { clearCredentials } from './apiClient'
import { AuthContext, type AuthSessionState } from './auth-context'

export function AuthProvider({ children }: { children: ReactNode }) {
  const [ready, setReady] = useState(false)
  const [session, setSession] = useState<AuthSession | null>(null)

  useEffect(() => {
    let active = true
    authService.setSessionExpiredHandler(() => {
      clearCredentials()
      if (active) setSession(null)
    })
    void authService.restore().then((restored) => {
      if (active) setSession(restored)
    }).catch(() => {
      if (active) setSession(null)
    }).finally(() => {
      if (active) setReady(true)
    })
    return () => {
      active = false
      authService.setSessionExpiredHandler(null)
    }
  }, [])

  const value = useMemo<AuthSessionState>(() => ({
    ready,
    user: session?.user ?? null,
    passwordChangeRequired: session?.passwordChangeRequired ?? false,
    signIn: async (identifier, password) => {
      const next = await authService.login({ identifier, password })
      setSession(next)
      return next.passwordChangeRequired
    },
    changePassword: async (current, next, confirm) => {
      await authService.changePassword(current, next, confirm)
      setSession(null)
    },
    signOut: async () => {
      try { await authService.logout() } finally { setSession(null) }
    },
  }), [ready, session])

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}
