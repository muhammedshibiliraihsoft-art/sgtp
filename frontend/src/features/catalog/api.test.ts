import { afterEach, describe, expect, it, vi } from 'vitest'
import { createGlobalFamily, createGlobalVariant, createShopFamilyOptionGroup, createShopGarmentFamily, createShopOptionGroup, createShopStyleOption, createShopVariant, getAllGlobalVariants, getAllShopGarmentFamilies, getAllShopOptionGroups, getAllShopVariants, getFamilies, getFamilyDetail, getGlobalVariant, getGlobalVariantsPage, getShopFamilyOptionGroups, getShopVariantsPage, materializeShopDefaultFamily, removeGlobalFamilyImage, setGlobalFamilyStatus, setGlobalVariantDefault, setGlobalVariantStatus, setShopVariantStatus, updateGlobalFamily, updateGlobalVariant, updateShopFamilyOptionGroups, updateShopStyleOptionTranslations, updateShopVariant, uploadGlobalFamilyImage, uploadShopStyleOptionImages } from './api'

function stubJsonFetch(responses: unknown[]) {
  const fetchMock = vi.fn()
  responses.forEach(body => fetchMock.mockResolvedValueOnce(new Response(JSON.stringify(body), {
    status: 200,
    headers: { 'Content-Type': 'application/json' },
  })))
  vi.stubGlobal('fetch', fetchMock)
  return fetchMock
}

function stubResponses(responses: Array<{ body: unknown; status: number }>) {
  const fetchMock = vi.fn()
  responses.forEach(({ body, status }) => fetchMock.mockResolvedValueOnce(new Response(JSON.stringify(body), {
    status,
    headers: { 'Content-Type': 'application/json' },
  })))
  vi.stubGlobal('fetch', fetchMock)
  return fetchMock
}

afterEach(() => {
  vi.unstubAllGlobals()
  vi.unstubAllEnvs()
})

describe('Catalog API contract', () => {
  it('creates and attaches a Shop-local group through the family-scoped endpoint', async () => {
    const config = { option_group: { id: 'group-1', tenant: 'shop-1' }, sort_order: 2, selection_mode: 'MULTI', is_required: false }
    const fetchMock = stubJsonFetch([config])
    const payload = { code: 'fastening-detail', translations: [{ locale: 'en' as const, name: 'Fastening detail' }] }
    await createShopFamilyOptionGroup('shop-1', 'family-1', payload)
    expect(fetchMock.mock.calls[0][0]).toBe('/api/v1/shops/shop-1/catalog/garment-families/family-1/option-groups/create/')
    expect(fetchMock.mock.calls[0][1]?.method).toBe('POST')
    expect(JSON.parse(String(fetchMock.mock.calls[0][1]?.body))).toEqual(payload)
  })

  it('uses Shop-scoped family/group creation and family configuration endpoints', async () => {
    const fetchMock = stubJsonFetch([
      { count: 1, next: null, previous: null, results: [{ id: 'family-1' }] },
      { count: 1, next: null, previous: null, results: [{ id: 'group-1' }] },
      { id: 'family-2' },
      { id: 'group-2' },
      [{ id: 'config-1', option_group: { id: 'group-1' }, sort_order: 0, selection_mode: 'SINGLE', is_required: false }],
      [{ id: 'config-1', option_group: { id: 'group-1' }, sort_order: 0, selection_mode: 'MULTI', is_required: true }],
    ])
    const payload = { code: 'custom-shirt', translations: [{ locale: 'en' as const, name: 'Custom Shirt' }] }

    await getAllShopGarmentFamilies('shop-1')
    await getAllShopOptionGroups('shop-1')
    await createShopGarmentFamily('shop-1', payload)
    await createShopOptionGroup('shop-1', { code: 'collar', translations: [{ locale: 'en', name: 'Collar' }] })
    await getShopFamilyOptionGroups('shop-1', 'family-2')
    await updateShopFamilyOptionGroups('shop-1', 'family-2', [{ option_group_id: 'group-1', sort_order: 0, selection_mode: 'MULTI', is_required: true }])

    expect(fetchMock.mock.calls.map(([path]) => path)).toEqual([
      '/api/v1/shops/shop-1/catalog/garment-families/?locale=en&status=ACTIVE',
      '/api/v1/shops/shop-1/catalog/option-groups/?locale=en',
      '/api/v1/shops/shop-1/catalog/garment-families/',
      '/api/v1/shops/shop-1/catalog/option-groups/',
      '/api/v1/shops/shop-1/catalog/garment-families/family-2/option-groups/?locale=en',
      '/api/v1/shops/shop-1/catalog/garment-families/family-2/option-groups/',
    ])
    expect(JSON.parse(String(fetchMock.mock.calls[5][1]?.body))).toEqual({ option_groups: [{ option_group_id: 'group-1', sort_order: 0, selection_mode: 'MULTI', is_required: true }] })
  })

  it('materializes one selected global default through the Shop-scoped endpoint', async () => {
    const fetchMock = stubJsonFetch([{ id: 'family-local', tenant: 'shop-1', template_source: 'family-global' }])
    await materializeShopDefaultFamily('shop-1', 'family-global')
    expect(fetchMock.mock.calls[0][0]).toBe('/api/v1/shops/shop-1/catalog/garment-families/family-global/materialize-default/')
    expect(fetchMock.mock.calls[0][1]?.method).toBe('POST')
  })
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

  it('PATCHes only supplied Shop style-option translations on the Shop-context route', async () => {
    const fetchMock = stubJsonFetch([{ id: 'style-1', name: 'Classic Collar' }])
    const translations = [{ locale: 'en' as const, name: 'Classic Collar' }]
    await updateShopStyleOptionTranslations('shop-1', 'style-1', translations)
    expect(fetchMock.mock.calls[0][0]).toBe('/api/v1/shops/shop-1/catalog/style-options/style-1/')
    expect(fetchMock.mock.calls[0][1]?.method).toBe('PATCH')
    expect(JSON.parse(String(fetchMock.mock.calls[0][1]?.body))).toEqual({ translations })
  })

  it('keeps pagination calls on the frontend origin while following backend next links', async () => {
    const fetchMock = stubJsonFetch([
      { count: 2, next: 'https://birky-staging-api.onrender.com/api/v1/shops/shop-1/catalog/variants/?page=2', previous: null, results: [{ id: 'v1' }] },
      { count: 2, next: null, previous: null, results: [{ id: 'v2' }] },
    ])

    const result = await getAllShopVariants('shop-1')

    expect(result.map(item => item.id)).toEqual(['v1', 'v2'])
    expect(fetchMock.mock.calls.map(call => call[0])).toEqual([
      '/api/v1/shops/shop-1/catalog/variants/?locale=en',
      '/api/v1/shops/shop-1/catalog/variants/?page=2',
    ])
  })

  it('loads all variants for one Family and requests archived rows only when asked', async () => {
    const fetchMock = stubJsonFetch([{ count: 1, next: null, previous: null, results: [{ id: 'variant-1' }] }])
    const result = await getAllGlobalVariants('family-1', 'en', 'all')
    expect(result).toEqual([{ id: 'variant-1' }])
    expect(fetchMock.mock.calls[0][0]).toBe('/api/v1/catalog/variants/?family=family-1&locale=en&status=all')
  })

  it('uploads style images under the backend images field', async () => {
    vi.stubEnv('VITE_ENABLE_LEGACY_PRIVATE_MEDIA_FALLBACK', 'true')
    const fetchMock = vi.fn()
      .mockResolvedValueOnce(new Response('<!doctype html><title>Not Found</title>', { status: 404, headers: { 'Content-Type': 'text/html' } }))
      .mockResolvedValueOnce(new Response(JSON.stringify([]), { status: 201, headers: { 'Content-Type': 'application/json' } }))
    vi.stubGlobal('fetch', fetchMock)
    const file = new File(['image'], 'reference.png', { type: 'image/png' })

    await uploadShopStyleOptionImages('shop-1', 'style-1', [file])

    const body = fetchMock.mock.calls[1][1]?.body as FormData
    expect(body.getAll('images')).toEqual([file])
    expect(body.get('file')).toBeNull()
    expect(fetchMock.mock.calls[0][0]).toBe('/api/v1/shops/shop-1/catalog/media/uploads/')
    expect(fetchMock.mock.calls[1][0]).toBe('/api/v1/shops/shop-1/catalog/style-options/style-1/reference-images/')
  })

  it('uses the Family list search, status, and pagination query contract', async () => {
    const fetchMock = stubJsonFetch([{ count: 1, next: null, previous: null, results: [] }])
    await getFamilies(2, 'shirt', 'ARCHIVED')
    expect(fetchMock.mock.calls[0][0]).toBe('/api/v1/catalog/families/?page=2&status=ARCHIVED&search=shirt')
  })

  it('uses paginated server filters for Shop and Main Supplier variants', async () => {
    const page = { count: 1, next: null, previous: null, results: [] }
    const fetchMock = stubJsonFetch([page, page])
    await getShopVariantsPage('shop-1', { page: 2, search: 'abaya', family: 'family-1', status: 'ARCHIVED', source: 'shop' })
    await getGlobalVariantsPage({ page: 3, search: 'kurta', family: 'family-2', status: 'all' })
    expect(fetchMock.mock.calls.map(call => call[0])).toEqual([
      '/api/v1/shops/shop-1/catalog/variants/?page=2&family=family-1&search=abaya&status=ARCHIVED&source=shop',
      '/api/v1/catalog/variants/?page=3&family=family-2&search=kurta&status=all',
    ])
  })

  it('uses the existing Shop and Global Variant lifecycle and translation routes', async () => {
    const fetchMock = stubJsonFetch([{}, {}, {}, {}, {}, {}, {}])
    const translations = [{ locale: 'en' as const, name: 'Abaya' }]
    await updateShopVariant('shop-1', 'variant-1', translations)
    await setShopVariantStatus('shop-1', 'variant-1', false)
    await setShopVariantStatus('shop-1', 'variant-1', true)
    await updateGlobalVariant('variant-2', translations)
    await setGlobalVariantStatus('variant-2', false)
    await setGlobalVariantStatus('variant-2', true)
    await setGlobalVariantDefault('variant-2')
    expect(fetchMock.mock.calls.map(call => [call[0], call[1]?.method])).toEqual([
      ['/api/v1/shops/shop-1/catalog/variants/variant-1/', 'PATCH'],
      ['/api/v1/shops/shop-1/catalog/variants/variant-1/archive/', 'POST'],
      ['/api/v1/shops/shop-1/catalog/variants/variant-1/reactivate/', 'POST'],
      ['/api/v1/catalog/variants/variant-2/', 'PATCH'],
      ['/api/v1/catalog/variants/variant-2/archive/', 'POST'],
      ['/api/v1/catalog/variants/variant-2/reactivate/', 'POST'],
      ['/api/v1/catalog/variants/variant-2/set-default/', 'POST'],
    ])
  })

  it('uses the Main Supplier Global Variant create and detail endpoints', async () => {
    const fetchMock = stubJsonFetch([{ id: 'variant-1' }, { id: 'variant-1' }])
    const data = { family_id: 'family-1', code: 'abaya-classic', translations: [{ locale: 'en' as const, name: 'Classic Abaya' }] }
    await createGlobalVariant(data)
    await getGlobalVariant('variant-1')
    expect(fetchMock.mock.calls.map(call => [call[0], call[1]?.method])).toEqual([
      ['/api/v1/catalog/variants/', 'POST'],
      ['/api/v1/catalog/variants/variant-1/', undefined],
    ])
    expect(JSON.parse(String(fetchMock.mock.calls[0][1]?.body))).toEqual(data)
  })

  it('creates a global Family with translated names and an immutable code', async () => {
    const fetchMock = stubJsonFetch([{ id: 'family-1', code: 'shirt', name: 'Shirt' }])
    const payload = { code: 'shirt', translations: [{ locale: 'en' as const, name: 'Shirt' }, { locale: 'ar-KW' as const, name: 'قميص' }] }
    await createGlobalFamily(payload)
    expect(fetchMock.mock.calls[0][0]).toBe('/api/v1/catalog/families/')
    expect(JSON.parse(String(fetchMock.mock.calls[0][1]?.body))).toEqual(payload)
  })

  it('updates family translations and ordered option groups through one request', async () => {
    const fetchMock = stubJsonFetch([{}])
    const translations = [{ locale: 'en' as const, name: 'Shirt' }]
    await updateGlobalFamily('family-1', { translations, option_group_ids: ['group-2', 'group-1'] })
    expect(fetchMock.mock.calls.map(call => [call[0], call[1]?.method, call[1]?.body])).toEqual([
      ['/api/v1/catalog/families/family-1/', 'PATCH', JSON.stringify({ translations, option_group_ids: ['group-2', 'group-1'] })],
    ])
  })

  it('uses the family lifecycle and private image routes with the image field', async () => {
    vi.stubEnv('VITE_ENABLE_LEGACY_PRIVATE_MEDIA_FALLBACK', 'true')
    const fetchMock = stubResponses([
      { body: { id: 'family-1', translations: [], option_groups: [] }, status: 200 },
      { body: { id: 'family-1', status: 'ARCHIVED' }, status: 200 },
      { body: { id: 'family-1', status: 'ACTIVE' }, status: 200 },
      { body: { detail: 'Private direct upload is not configured.' }, status: 503 },
      { body: { has_image: true }, status: 200 },
      { body: undefined, status: 204 },
    ])
    await getFamilyDetail('family-1')
    await setGlobalFamilyStatus('family-1', false)
    await setGlobalFamilyStatus('family-1', true)
    const file = new File(['image'], 'shirt.png', { type: 'image/png' })
    await uploadGlobalFamilyImage('family-1', file)
    await removeGlobalFamilyImage('family-1')
    expect(fetchMock.mock.calls[0][0]).toBe('/api/v1/catalog/families/family-1/')
    expect(fetchMock.mock.calls[1][0]).toBe('/api/v1/catalog/families/family-1/archive/')
    expect(fetchMock.mock.calls[1][1]?.method).toBe('POST')
    expect(fetchMock.mock.calls[2][0]).toBe('/api/v1/catalog/families/family-1/reactivate/')
    const body = fetchMock.mock.calls[4][1]?.body as FormData
    expect(body.get('image')).toBe(file)
    expect(fetchMock.mock.calls[3][0]).toBe('/api/v1/catalog/media/uploads/')
    expect(fetchMock.mock.calls[4][0]).toBe('/api/v1/catalog/families/family-1/image/')
    expect(fetchMock.mock.calls[5][0]).toBe('/api/v1/catalog/families/family-1/image/')
    expect(fetchMock.mock.calls[5][1]?.method).toBe('DELETE')
  })
})
