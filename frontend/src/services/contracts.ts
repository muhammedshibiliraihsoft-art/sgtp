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

export type AuthenticatedUser = {
  id: string
  firstName: string
  lastName?: string
  role: 'MAIN_SUPPLIER' | 'SHOP_ADMIN' | 'STAFF'
  owningShopId?: string
}

export interface AuthAdapter {
  signIn(identifier: string, password: string): Promise<Result<AuthenticatedUser>>
  signOut(): Promise<Result<void>>
  currentUser(): Promise<Result<AuthenticatedUser | null>>
}

export interface ShopContextAdapter {
  /** Ordinary account context is resolved by the backend, never user-selected. */
  currentShop(): Promise<Result<{ id: string; name: string } | null>>
}
