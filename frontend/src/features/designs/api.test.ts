import { afterEach, describe, expect, it, vi } from 'vitest'
import { addShopDesignSelection, createShopDesign, getAllShopDesigns, getShopDesigns, uploadShopDesignReferences } from './api'

function stubJsonFetch(body: unknown) {
  const fetchMock = vi.fn().mockResolvedValue(new Response(JSON.stringify(body), {
    status: 201,
    headers: { 'Content-Type': 'application/json' },
  }))
  vi.stubGlobal('fetch', fetchMock)
  return fetchMock
}

afterEach(() => {
  vi.unstubAllGlobals()
  vi.unstubAllEnvs()
})

describe('Design API contract', () => {
  it('creates a Shop design with the backend-required name and identifiers', async () => {
    const fetchMock = stubJsonFetch({ id: 'design-1' })
    const payload = { family_id: 'family-1', variant_id: 'variant-1', name: 'Blue Shirt' }

    await createShopDesign('shop-1', payload)

    expect(fetchMock.mock.calls[0][0]).toBe('/api/v1/shops/shop-1/designs/')
    expect(JSON.parse(String(fetchMock.mock.calls[0][1]?.body))).toEqual(payload)
  })

  it('adds a style selection to the draft version route', async () => {
    const fetchMock = stubJsonFetch({ id: 'selection-1' })
    const payload = { style_option_id: 'style-1' }

    await addShopDesignSelection('shop-1', 'version-1', payload)

    expect(fetchMock.mock.calls[0][0]).toBe('/api/v1/shops/shop-1/design-versions/version-1/selections/')
    expect(JSON.parse(String(fetchMock.mock.calls[0][1]?.body))).toEqual(payload)
  })

  it('uploads reference files using the backend images field', async () => {
    vi.stubEnv('VITE_ENABLE_LEGACY_PRIVATE_MEDIA_FALLBACK', 'true')
    const fetchMock = vi.fn()
      .mockResolvedValueOnce(new Response(JSON.stringify({ detail: 'Private direct upload is not configured.' }), { status: 503, headers: { 'Content-Type': 'application/json' } }))
      .mockResolvedValueOnce(new Response(JSON.stringify([]), { status: 201, headers: { 'Content-Type': 'application/json' } }))
    vi.stubGlobal('fetch', fetchMock)
    const file = new File(['image'], 'reference.png', { type: 'image/png' })

    await uploadShopDesignReferences('shop-1', 'version-1', [file])

    expect(fetchMock.mock.calls[0][0]).toBe('/api/v1/shops/shop-1/catalog/media/uploads/')
    const body = fetchMock.mock.calls[1][1]?.body as FormData
    expect(body.getAll('images')).toEqual([file])
    expect(body.get('file')).toBeNull()
  })

  it('passes the selected Family to the Shop Designs list API', async () => {
    const fetchMock = vi.fn().mockResolvedValue(new Response(JSON.stringify({ count: 0, next: null, previous: null, results: [] }), {
      status: 200, headers: { 'Content-Type': 'application/json' },
    }))
    vi.stubGlobal('fetch', fetchMock)
    await getShopDesigns('shop-1', 1, 'family-1')
    expect(fetchMock.mock.calls[0][0]).toBe('/api/v1/shops/shop-1/designs/?page=1&locale=en&family=family-1')
  })

  it('composes the exact Family and Variant filters for Design listing', async () => {
    const fetchMock = vi.fn().mockResolvedValue(new Response(JSON.stringify({ count: 0, next: null, previous: null, results: [] }), {
      status: 200, headers: { 'Content-Type': 'application/json' },
    }))
    vi.stubGlobal('fetch', fetchMock)
    await getAllShopDesigns('shop-1', { family: 'family-1', variant: 'variant-1' })
    expect(fetchMock.mock.calls[0][0]).toBe('/api/v1/shops/shop-1/designs/?page=1&locale=en&family=family-1&variant=variant-1')
  })
})
