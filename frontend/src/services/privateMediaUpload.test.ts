import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { ApiError, apiRequest } from './apiClient'
import { uploadPrivateMediaBatch } from './privateMediaUpload'

vi.mock('./apiClient', () => ({
  ApiError: class ApiError extends Error {
    status: number
    code: string

    constructor(message: string, status: number, code: string) {
      super(message)
      this.status = status
      this.code = code
    }
  },
  apiRequest: vi.fn(),
}))

describe('private image upload fallback', () => {
  afterEach(() => vi.unstubAllEnvs())

  beforeEach(() => {
    vi.mocked(apiRequest).mockReset()
    vi.stubEnv('VITE_ENABLE_LEGACY_PRIVATE_MEDIA_FALLBACK', '')
  })

  it.each([404, 503])('does not fall back to ephemeral legacy storage after API %s', async status => {
    vi.mocked(apiRequest).mockRejectedValue(new ApiError('unavailable', status, 'unavailable'))
    const fallback = vi.fn().mockResolvedValue([])

    await expect(uploadPrivateMediaBatch({
      path: '/api/v1/catalog/media/uploads/',
      kind: 'style_option',
      targetId: 'style-1',
      files: [new File(['image'], 'style.webp', { type: 'image/webp' })],
      fallback,
    })).rejects.toMatchObject({ code: 'private_storage_unavailable', status })

    expect(fallback).not.toHaveBeenCalled()
  })

  it('uses the legacy route only when explicitly enabled for local development', async () => {
    vi.stubEnv('VITE_ENABLE_LEGACY_PRIVATE_MEDIA_FALLBACK', 'true')
    vi.mocked(apiRequest).mockRejectedValue(new ApiError('unavailable', 404, 'unavailable'))
    const fallback = vi.fn().mockResolvedValue([{ id: 'legacy-image' }])

    await expect(uploadPrivateMediaBatch({
      path: '/api/v1/catalog/media/uploads/',
      kind: 'style_option',
      targetId: 'style-1',
      files: [new File(['image'], 'style.webp', { type: 'image/webp' })],
      fallback,
    })).resolves.toEqual([{ id: 'legacy-image' }])

    expect(fallback).toHaveBeenCalledOnce()
  })
})
