import { apiRequest } from '../../services/apiClient'
import type { MembershipDTO, CreateShopUserRequest, CreateShopUserResult, WorkFunctionCode, WorkFunctionSetResponse, ShopStats } from './types'

type Page<T> = { count: number; next: string | null; previous: string | null; results: T[] }
const membershipsPath = '/api/v1/memberships/'
const shopPath = (shopId: string) => `/api/v1/shops/${encodeURIComponent(shopId)}`

export const usersApi = {
  memberships(shopId: string, options: { search?: string; role?: string; active?: string; page?: number } = {}) {
    const query = new URLSearchParams({ tenant: shopId })
    if (options.search?.trim()) query.set('search', options.search.trim())
    if (options.role && options.role !== 'ALL') query.set('role', options.role)
    if (options.active && options.active !== 'ALL') query.set('is_active', options.active === 'ACTIVE' ? 'true' : 'false')
    if (options.page && options.page > 1) query.set('page', String(options.page))
    return apiRequest<Page<MembershipDTO>>(`${membershipsPath}?${query}`)
  },
  stats(shopId: string) {
    return apiRequest<ShopStats>(`/api/v1/tenants/${encodeURIComponent(shopId)}/stats/`)
  },
  createUser(shopId: string, request: CreateShopUserRequest) {
    return apiRequest<CreateShopUserResult>(`${shopPath(shopId)}/users/`, { method: 'POST', body: request })
  },
  setRole(id: string, role: 'STAFF' | 'VIEWER') {
    return apiRequest<MembershipDTO>(`${membershipsPath}${encodeURIComponent(id)}/`, { method: 'PATCH', body: { role } })
  },
  deactivate(id: string) {
    return apiRequest(`${membershipsPath}${encodeURIComponent(id)}/deactivate/`, { method: 'POST', body: {} })
  },
  reactivate(id: string) {
    return apiRequest(`${membershipsPath}${encodeURIComponent(id)}/reactivate/`, { method: 'POST', body: {} })
  },
  remove(id: string) {
    return apiRequest<void>(`${membershipsPath}${encodeURIComponent(id)}/`, { method: 'DELETE' })
  },
  functions(shopId: string, membershipId: string) {
    return apiRequest<WorkFunctionSetResponse>(`${shopPath(shopId)}/memberships/${encodeURIComponent(membershipId)}/functions/`)
  },
  setFunctions(shopId: string, membershipId: string, functions: WorkFunctionCode[]) {
    return apiRequest<WorkFunctionSetResponse>(`${shopPath(shopId)}/memberships/${encodeURIComponent(membershipId)}/functions/`, { method: 'PUT', body: { functions } })
  },
  findCreatedMembership(shopId: string, userCode: string) {
    return apiRequest<Page<MembershipDTO>>(`${membershipsPath}?tenant=${encodeURIComponent(shopId)}&search=${encodeURIComponent(userCode)}`)
  },
}
