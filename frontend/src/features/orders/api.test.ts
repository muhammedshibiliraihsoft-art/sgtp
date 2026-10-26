import { beforeEach, describe, expect, it, vi } from 'vitest'
import { ordersApi } from './api'

const request = vi.hoisted(() => vi.fn())
vi.mock('../../services/apiClient', () => ({ apiRequest: request }))

describe('orders API contract', () => {
  beforeEach(() => request.mockReset())

  it('lists Shop Work with safe search and stage filters', () => {
    ordersApi.list('shop/one', { page: 2, search: 'ORD-000001', status: 'REQUEST' })
    expect(request).toHaveBeenCalledWith('/api/v1/shops/shop%2Fone/works/?page=2&search=ORD-000001&status=REQUEST')
  })

  it('requests only the Shop deleted-order archive with date filters', () => {
    ordersApi.deletedList('shop/one', { page: 2, search: 'ORD-000001', deletedFrom: '2026-10-01', deletedTo: '2026-10-18' })
    expect(request).toHaveBeenCalledWith('/api/v1/shops/shop%2Fone/works/deleted/?page=2&search=ORD-000001&deleted_from=2026-10-01&deleted_to=2026-10-18')
  })

  it('creates one garment from saved references and uses fixed workflow actions', () => {
    const input = { client_id: 'client-1', design_version_id: 'design-version-1', measurement_set_id: 'set-1', priority: 'URGENT' as const }
    ordersApi.create('shop-1', input)
    expect(request).toHaveBeenCalledWith('/api/v1/shops/shop-1/works/', { method: 'POST', body: input })
    ordersApi.assign('shop-1', 'work-1', null)
    expect(request).toHaveBeenCalledWith('/api/v1/shops/shop-1/works/work-1/assign/', { method: 'POST', body: { membership_id: null } })
    ordersApi.advance('shop-1', 'work-1', 'REQUEST')
    expect(request).toHaveBeenCalledWith('/api/v1/shops/shop-1/works/work-1/advance/', { method: 'POST', body: { expected_status: 'REQUEST' } })
  })
})
