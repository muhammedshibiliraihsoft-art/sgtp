import { apiRequest } from '../../services/apiClient'
import type { CreateOrderInput, DeletedOrderPage, Order, OrderPage, OrderPriority, OrderStatus, UpdateOrderInput } from './types'

const base = (shopId: string) => `/api/v1/shops/${encodeURIComponent(shopId)}/works/`
const detail = (shopId: string, id: string) => `${base(shopId)}${encodeURIComponent(id)}/`

export const ordersApi = {
  deletedList(shopId: string, options: { page?: number; search?: string; deletedFrom?: string; deletedTo?: string } = {}) {
    const query = new URLSearchParams()
    if (options.page && options.page > 1) query.set('page', String(options.page))
    if (options.search?.trim()) query.set('search', options.search.trim())
    if (options.deletedFrom) query.set('deleted_from', options.deletedFrom)
    if (options.deletedTo) query.set('deleted_to', options.deletedTo)
    return apiRequest<DeletedOrderPage>(`${base(shopId)}deleted/${query.size ? `?${query}` : ''}`)
  },
  list(shopId: string, options: { page?: number; search?: string; status?: OrderStatus | ''; priority?: OrderPriority | '' } = {}) {
    const query = new URLSearchParams()
    if (options.page && options.page > 1) query.set('page', String(options.page))
    if (options.search?.trim()) query.set('search', options.search.trim())
    if (options.status) query.set('status', options.status)
    if (options.priority) query.set('priority', options.priority)
    return apiRequest<OrderPage>(`${base(shopId)}${query.size ? `?${query}` : ''}`)
  },
  detail(shopId: string, id: string) {
    return apiRequest<Order>(detail(shopId, id))
  },
  create(shopId: string, input: CreateOrderInput) {
    return apiRequest<Order>(base(shopId), { method: 'POST', body: input })
  },
  update(shopId: string, id: string, input: UpdateOrderInput) {
    return apiRequest<Order>(detail(shopId, id), { method: 'PATCH', body: input })
  },
  assign(shopId: string, id: string, membershipId: string | null) {
    return apiRequest<Order>(`${detail(shopId, id)}assign/`, { method: 'POST', body: { membership_id: membershipId } })
  },
  advance(shopId: string, id: string, expectedStatus: OrderStatus) {
    return apiRequest<Order>(`${detail(shopId, id)}advance/`, { method: 'POST', body: { expected_status: expectedStatus } })
  },
  remove(shopId: string, id: string) {
    return apiRequest<void>(detail(shopId, id), { method: 'DELETE' })
  },
}
