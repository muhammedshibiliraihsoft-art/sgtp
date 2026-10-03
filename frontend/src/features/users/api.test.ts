import { afterEach, describe, expect, it, vi } from 'vitest'
import { usersApi } from './api'

afterEach(() => vi.unstubAllGlobals())

describe('Shop membership API', () => {
  it('requests only the explicit Shop memberships with backend filters', async () => {
    const fetchMock = vi.fn().mockResolvedValue(new Response(JSON.stringify({ count:0,next:null,previous:null,results:[] }), { status:200 }))
    vi.stubGlobal('fetch', fetchMock)
    await usersApi.memberships('shop-1', { search:'USR-ABCD', role:'STAFF', active:'ACTIVE', page:2 })
    expect(fetchMock.mock.calls[0][0]).toBe('/api/v1/memberships/?tenant=shop-1&search=USR-ABCD&role=STAFF&is_active=true&page=2')
  })

  it('creates a Shop user only through the Shop URL context', async () => {
    const fetchMock = vi.fn().mockResolvedValue(new Response(JSON.stringify({ id:'user-1' }), { status:201 }))
    vi.stubGlobal('fetch', fetchMock)
    await usersApi.createUser('shop-1', { first_name:'Sam', role:'STAFF' })
    expect(fetchMock.mock.calls[0][0]).toBe('/api/v1/shops/shop-1/users/')
    expect(JSON.parse(fetchMock.mock.calls[0][1].body as string)).toEqual({ first_name:'Sam', role:'STAFF' })
  })
})
