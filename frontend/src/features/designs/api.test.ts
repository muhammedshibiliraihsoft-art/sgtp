import { afterEach, describe, expect, it, vi } from 'vitest'
import { addShopDesignSelection, createShopDesign, uploadShopDesignReferences } from './api'

function stubJsonFetch(body: unknown) {
  const fetchMock = vi.fn().mockResolvedValue(new Response(JSON.stringify(body), {
    status: 201,
    headers: { 'Content-Type': 'application/json' },
  }))
  vi.stubGlobal('fetch', fetchMock)
  return fetchMock
}

afterEach(() => vi.unstubAllGlobals())

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
    const fetchMock = stubJsonFetch([])
    const file = new File(['image'], 'reference.png', { type: 'image/png' })

    await uploadShopDesignReferences('shop-1', 'version-1', [file])

    const body = fetchMock.mock.calls[0][1]?.body as FormData
    expect(body.getAll('images')).toEqual([file])
    expect(body.get('file')).toBeNull()
  })
})
