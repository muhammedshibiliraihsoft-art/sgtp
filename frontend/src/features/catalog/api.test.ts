import { afterEach, describe, expect, it, vi } from 'vitest'
import { createShopStyleOption, createShopVariant, getAllShopVariants, uploadShopStyleOptionImages } from './api'

function stubJsonFetch(responses: unknown[]) {
  const fetchMock = vi.fn()
  responses.forEach(body => fetchMock.mockResolvedValueOnce(new Response(JSON.stringify(body), {
    status: 200,
    headers: { 'Content-Type': 'application/json' },
  })))
  vi.stubGlobal('fetch', fetchMock)
  return fetchMock
}

afterEach(() => vi.unstubAllGlobals())

describe('Catalog API contract', () => {
  it('sends the backend variant payload and shop route', async () => {
    const fetchMock = stubJsonFetch([{ id: 'variant-1', family: 'family-1', code: 'kurta', name: 'Kurta', is_default: false }])
    const payload = { family_id: 'family-1', code: 'kurta', translations: [{ locale: 'en' as const, name: 'Kurta' }] }

    await createShopVariant('shop-1', payload)

    expect(fetchMock.mock.calls[0][0]).toBe('/api/v1/shops/shop-1/catalog/variants/')
    expect(JSON.parse(String(fetchMock.mock.calls[0][1]?.body))).toEqual(payload)
  })

  it('sends the backend style-option field names', async () => {
    const fetchMock = stubJsonFetch([{ id: 'style-1', option_group: 'group-1', tenant: 'shop-1', code: 'round', name: 'Round', is_active: true, is_global: false, reference_images: [] }])
    const payload = { option_group_id: 'group-1', code: 'round', translations: [{ locale: 'en' as const, name: 'Round' }] }

    await createShopStyleOption('shop-1', payload)

    expect(fetchMock.mock.calls[0][0]).toBe('/api/v1/shops/shop-1/catalog/style-options/')
    expect(JSON.parse(String(fetchMock.mock.calls[0][1]?.body))).toEqual(payload)
  })

  it('keeps pagination calls on the frontend origin while following backend next links', async () => {
    const fetchMock = stubJsonFetch([
      { count: 2, next: 'https://birky-staging-api.onrender.com/api/v1/shops/shop-1/catalog/variants/?page=2', previous: null, results: [{ id: 'v1' }] },
      { count: 2, next: null, previous: null, results: [{ id: 'v2' }] },
    ])

    const result = await getAllShopVariants('shop-1')

    expect(result.map(item => item.id)).toEqual(['v1', 'v2'])
    expect(fetchMock.mock.calls.map(call => call[0])).toEqual([
      '/api/v1/shops/shop-1/catalog/variants/',
      '/api/v1/shops/shop-1/catalog/variants/?page=2',
    ])
  })

  it('uploads style images under the backend images field', async () => {
    const fetchMock = stubJsonFetch([[]])
    const file = new File(['image'], 'reference.png', { type: 'image/png' })

    await uploadShopStyleOptionImages('shop-1', 'style-1', [file])

    const body = fetchMock.mock.calls[0][1]?.body as FormData
    expect(body.getAll('images')).toEqual([file])
    expect(body.get('file')).toBeNull()
  })
})
