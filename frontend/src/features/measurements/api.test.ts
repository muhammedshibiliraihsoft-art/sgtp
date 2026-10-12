import { beforeEach, describe, expect, it, vi } from 'vitest'

const api = vi.hoisted(() => ({ apiRequest: vi.fn(), binaryRequest: vi.fn() }))
vi.mock('../../services/apiClient', () => ({ apiRequest: api.apiRequest, binaryRequest: api.binaryRequest }))

import { measurementApi } from './api'

describe('Measurement API contract adapter', () => {
  beforeEach(() => vi.clearAllMocks())

  it('loads every page of filtered definitions with an explicit locale', async () => {
    api.apiRequest
      .mockResolvedValueOnce({ count: 2, next: '/api/v1/shops/shop-1/measurement-definitions/?page=2', previous: null, results: [{ id: 'definition-1' }] })
      .mockResolvedValueOnce({ count: 2, next: null, previous: '/api/v1/shops/shop-1/measurement-definitions/?page=1', results: [{ id: 'definition-2' }] })

    const result = await measurementApi.definitions('shop-1', 'family-1', 'variant-1', 'ar-KW')

    expect(result.map(item => item.id)).toEqual(['definition-1', 'definition-2'])
    expect(api.apiRequest.mock.calls.map(([path]) => path)).toEqual([
      '/api/v1/shops/shop-1/measurement-definitions/?family_id=family-1&locale=ar-KW&variant_id=variant-1',
      '/api/v1/shops/shop-1/measurement-definitions/?page=2',
    ])
  })

  it('creates a Shop measurement definition mapped to the selected garment', async () => {
    api.apiRequest.mockResolvedValueOnce({ id: 'definition-custom', code: 'sleeve-length' })
    const payload = {
      code: 'sleeve-length', group_code: 'BODY', sort_order: 2,
      translations: [{ locale: 'en' as const, name: 'Sleeve Length' }],
      mappings: [{ family_id: 'family-1', variant_id: 'variant-1' }],
    }

    await measurementApi.createDefinition('shop-1', payload)

    expect(api.apiRequest).toHaveBeenCalledWith('/api/v1/shops/shop-1/measurement-definitions/', { method: 'POST', body: payload })
  })

  it('keeps body-value units explicit and saves through the owner-specific immutable-set path', async () => {
    api.apiRequest.mockResolvedValueOnce({ id: 'set-1', version: 1 })

    await measurementApi.saveSet('shop-1', 'client-1', { kind: 'related_person', id: 'person-1' }, 'profile-1', [
      { definition_id: 'definition-1', value: '61.2500', unit: 'INCH' },
    ])

    expect(api.apiRequest).toHaveBeenCalledWith(
      '/api/v1/shops/shop-1/clients/client-1/related-persons/person-1/measurement-profiles/profile-1/sets/',
      { method: 'POST', body: { values: [{ definition_id: 'definition-1', value: '61.2500', unit: 'INCH' }] } },
    )
  })

  it('links the selected published design version to the measurement snapshot when provided', async () => {
    api.apiRequest.mockResolvedValueOnce({ id: 'set-2', version: 2, design_version: 'design-version-1' })
    await measurementApi.saveSet('shop-1', 'client-1', { kind: 'client' }, 'profile-1', [
      { definition_id: 'definition-1', value: '39', unit: 'INCH' },
    ], 'design-version-1')

    expect(api.apiRequest).toHaveBeenCalledWith(
      '/api/v1/shops/shop-1/clients/client-1/measurement-profiles/profile-1/sets/',
      { method: 'POST', body: { values: [{ definition_id: 'definition-1', value: '39', unit: 'INCH' }], design_version_id: 'design-version-1' } },
    )
  })

  it('uses the immutable copy, compare, and Fabric inventory endpoints', async () => {
    api.apiRequest
      .mockResolvedValueOnce({ id: 'copy-1' })
      .mockResolvedValueOnce({ from_set_id: 'set-1', to_set_id: 'set-2', results: [] })
      .mockResolvedValueOnce({ count: 0, next: null, previous: null, results: [] })

    await measurementApi.copySet('shop-1', 'client-1', { kind: 'client' }, 'profile-1', 'set-1')
    await measurementApi.compare('shop-1', 'client-1', { kind: 'client' }, 'profile-1', 'set-1', 'set-2')
    await measurementApi.fabrics('shop-1')

    expect(api.apiRequest.mock.calls.map(([path]) => path)).toEqual([
      '/api/v1/shops/shop-1/clients/client-1/measurement-profiles/profile-1/sets/set-1/copy/',
      '/api/v1/shops/shop-1/clients/client-1/measurement-profiles/profile-1/compare/?from_set_id=set-1&to_set_id=set-2',
      '/api/v1/shops/shop-1/inventory/items/?category=FABRIC',
    ])
  })

  it('loads measurement history one backend page at a time and opens exact saved set detail', async () => {
    api.apiRequest
      .mockResolvedValueOnce({ count: 21, next: '/api/v1/shops/shop-1/clients/client-1/measurement-profiles/profile-1/sets/?page=2', previous: null, results: [{ id: 'set-1' }] })
      .mockResolvedValueOnce({ id: 'set-1', profile: 'profile-1', version: 1, values: [] })

    const first = await measurementApi.setsPage('shop-1', 'client-1', { kind: 'client' }, 'profile-1')
    const detail = await measurementApi.setDetail('shop-1', 'client-1', { kind: 'client' }, 'profile-1', 'set-1')

    expect(first.next).toContain('page=2')
    expect(detail.id).toBe('set-1')
    expect(api.apiRequest.mock.calls.map(([path]) => path)).toEqual([
      '/api/v1/shops/shop-1/clients/client-1/measurement-profiles/profile-1/sets/?page=1',
      '/api/v1/shops/shop-1/clients/client-1/measurement-profiles/profile-1/sets/set-1/',
    ])
  })

  it('deletes a version through its owner-scoped detail endpoint', async () => {
    api.apiRequest.mockResolvedValueOnce(undefined)
    await measurementApi.deleteSet('shop-1', 'client-1', { kind: 'client' }, 'profile-1', 'set-1')
    expect(api.apiRequest).toHaveBeenCalledWith(
      '/api/v1/shops/shop-1/clients/client-1/measurement-profiles/profile-1/sets/set-1/',
      { method: 'DELETE' },
    )
  })

  it('requests a secured worksheet for the chosen version and optional design', async () => {
    const blob = new Blob(['%PDF-1.4'])
    api.binaryRequest.mockResolvedValue(blob)

    const result = await measurementApi.exportWorksheet(
      'shop-1', 'client-1', { kind: 'related_person', id: 'person-1' },
      'profile-1', 'set-2', 'design-3',
    )

    expect(api.binaryRequest).toHaveBeenCalledWith(
      '/api/v1/shops/shop-1/clients/client-1/related-persons/person-1/measurement-profiles/profile-1/worksheet.pdf?measurement_set_id=set-2&design_id=design-3',
    )
    expect(result).toBe(blob)
  })
})
