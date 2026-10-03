import { afterEach, describe, expect, it, vi } from 'vitest'
import { clientsApi } from './api'

afterEach(() => vi.unstubAllGlobals())

describe('Shop client API', () => {
  it('scopes search and pagination to the explicit Shop', async () => {
    const fetchMock = vi.fn().mockResolvedValue(new Response(JSON.stringify({ count:0,next:null,previous:null,results:[] }), { status:200 }))
    vi.stubGlobal('fetch', fetchMock)
    await clientsApi.list('shop/a', 'Noura', 2)
    expect(fetchMock.mock.calls[0][0]).toBe('/api/v1/shops/shop%2Fa/clients/?search=Noura&page=2')
  })

  it('uses nested Related Person routes and does not send parent identity in the body', async () => {
    const fetchMock = vi.fn().mockResolvedValue(new Response(JSON.stringify({ id:'rp-1' }), { status:201 }))
    vi.stubGlobal('fetch', fetchMock)
    await clientsApi.createRelated('shop-1', 'client-1', { name:'  Noor  ', phone:' +974 123 ', email:'' })
    expect(fetchMock.mock.calls[0][0]).toBe('/api/v1/shops/shop-1/clients/client-1/related-persons/')
    expect(JSON.parse(fetchMock.mock.calls[0][1].body as string)).toEqual({ name:'Noor', phone:'+974 123', email:'' })
  })
})
