/** UI-facing contracts only. These are not claims about live API endpoints. */
export type ApiProblem = {
  code: string
  message: string
  fieldErrors?: Record<string, string[]>
  requestId?: string
}

export type Result<T> =
  | { ok: true; data: T }
  | { ok: false; error: ApiProblem }

export type ShopRole = 'ADMIN' | 'STAFF' | 'VIEWER' | null
export type WorkFunction = 'SALES' | 'MEASUREMENT' | 'CUTTING' | 'STITCHING' | 'FINISHING' | 'QC' | 'CASHIER'
export type Locale = 'en' | 'ar-KW' | 'bn' | 'ur'
export type Appearance = 'system' | 'light' | 'dark'

export type AuthenticatedUser = {
  id: string // UUID
  userCode: string // human-facing User ID
  email: string | null
  firstName: string
  lastName?: string
  isActive: boolean
  dateJoined: string
  phone: string | null
  preferredLocale: Locale
  appearancePreference: Appearance
  mustChangePassword: boolean

  // Shop context
  role: ShopRole
  isMainSupplier: boolean
  owningShopId?: string
}

export interface AuthAdapter {
  signIn(identifier: string, password: string): Promise<Result<AuthenticatedUser>>
  signOut(): Promise<Result<void>>
  currentUser(): Promise<Result<AuthenticatedUser | null>>
}

export interface ShopContextAdapter {
  /** Ordinary account context is resolved by the backend, never user-selected. */
  currentShop(): Promise<Result<{ id: string; name: string; isMainSupplier: boolean; role: ShopRole } | null>>
}

export type MockWorkRecord = {
  id: string
  title: string
  customerName: string
  status: string
  statusType: 'new' | 'active' | 'review' | 'ready'
}

export interface MockWorkAdapter {
  getWorkPreview(stage: string): Promise<Result<{ records: MockWorkRecord[], total: number }>>
}
