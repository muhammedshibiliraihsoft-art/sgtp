import { ApiError, apiRequest } from './apiClient'

export type ShopSummary = {
  id: string
  name: string
  is_active: boolean
  max_users: number
  user_count: number
  is_at_user_limit: boolean
  default_locale: string | null
  default_timezone: string | null
  default_currency: string | null
}

export type ShopDetail = ShopSummary & {
  slug: string
  domain: string | null
  contact_email: string
  contact_phone: string
  address_line1: string
  address_line2: string
  city: string
  state: string
  postal_code: string
  country: string
  created_at: string
  updated_at: string
}

export type CreateShopInput = {
  name: string
  slug: string
  max_users: number
  first_admin: {
    first_name: string
    last_name?: string
    email: string
    phone: string
  }
  contact_email?: string
  contact_phone?: string
  address_line1?: string
  address_line2?: string
  city?: string
  state?: string
  postal_code?: string
  country?: string
  default_locale?: string | null
  default_timezone?: string | null
  default_currency?: string | null
}

export type CreatedShop = ShopDetail & {
  first_admin_user_code: string
  initial_password: string
}

export type ShopPage = {
  count: number
  next: string | null
  previous: string | null
  results: ShopSummary[]
}

export type ShopRequestContext = {
  shop_id: string
  role: 'ADMIN' | 'STAFF' | 'VIEWER' | null
  is_main_supplier: boolean
  work_functions: string[]
}

const basePath = '/api/v1/tenants/'

export const shopsService = {
  list(search = '', page = 1, filters: { active?: 'all' | 'true' | 'false'; ordering?: 'name' | '-name' | 'created_at' | '-created_at' } = {}): Promise<ShopPage> {
    const query = new URLSearchParams()
    if (search.trim()) query.set('search', search.trim())
    if (page > 1) query.set('page', String(page))
    if (filters.active && filters.active !== 'all') query.set('is_active', filters.active)
    if (filters.ordering) query.set('ordering', filters.ordering)
    return apiRequest<ShopPage>(`${basePath}${query.size ? `?${query}` : ''}`)
  },
  context(id: string): Promise<ShopRequestContext> {
    return apiRequest<ShopRequestContext>(`/api/v1/shops/${encodeURIComponent(id)}/context/`)
  },
  detail(id: string): Promise<ShopDetail> {
    return apiRequest<ShopDetail>(`${basePath}${encodeURIComponent(id)}/`)
  },
  create(input: CreateShopInput): Promise<CreatedShop> {
    return apiRequest<CreatedShop>(basePath, { method: 'POST', body: input })
  },
  update(id: string, changes: Partial<ShopDetail>): Promise<ShopDetail> {
    return apiRequest<ShopDetail>(`${basePath}${encodeURIComponent(id)}/`, { method: 'PATCH', body: changes })
  },
  setActive(id: string, active: boolean): Promise<{ status: string; is_active: boolean }> {
    return apiRequest(`${basePath}${encodeURIComponent(id)}/${active ? 'activate' : 'deactivate'}/`, {
      method: 'POST', body: {},
    })
  },
}

export function shopFieldErrors(error: unknown): Record<string, string> {
  if (!(error instanceof ApiError) || !error.payload || typeof error.payload !== 'object') return {}
  const payload = error.payload as Record<string, unknown>
  const errors = payload.errors && typeof payload.errors === 'object'
    ? payload.errors as Record<string, unknown>
    : payload
  const messages: Record<string, string> = {}
  for (const [key, value] of Object.entries(errors)) {
    if (typeof value === 'string') messages[key] = value
    else if (Array.isArray(value) && typeof value[0] === 'string') messages[key] = value[0]
    else if (value && typeof value === 'object') {
      for (const [nestedKey, nestedValue] of Object.entries(value)) {
        if (typeof nestedValue === 'string') messages[`${key}.${nestedKey}`] = nestedValue
        else if (Array.isArray(nestedValue) && typeof nestedValue[0] === 'string') messages[`${key}.${nestedKey}`] = nestedValue[0]
      }
    }
  }
  return messages
}
