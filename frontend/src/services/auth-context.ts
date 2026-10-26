import { createContext } from 'react'
import type { BackendUser } from './auth'

export type AuthSessionState = {
  ready: boolean
  user: BackendUser | null
  passwordChangeRequired: boolean
  signIn: (identifier: string, password: string) => Promise<boolean>
  changePassword: (current: string, next: string, confirm: string) => Promise<void>
  confirmPasswordReset: (uid: string, token: string, next: string, confirm: string) => Promise<void>
  requestPasswordReset: (email: string) => Promise<void>
  signOut: () => Promise<void>
}

export const AuthContext = createContext<AuthSessionState | null>(null)
