import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { act, renderHook, waitFor } from '@testing-library/react'
import { ApiError } from '../services/apiClient'
import { usePrivateImage } from './usePrivateImage'

const mock = vi.hoisted(() => ({ binaryRequest: vi.fn() }))
vi.mock('../services/apiClient', async importOriginal => ({ ...(await importOriginal<typeof import('../services/apiClient')>()), binaryRequest: mock.binaryRequest }))

const image = () => new Blob(['image bytes'], { type: 'image/webp' })

describe('private image loading', () => {
  beforeEach(() => {
    vi.stubGlobal('URL', { ...URL, createObjectURL: vi.fn(() => 'blob:private-image'), revokeObjectURL: vi.fn() })
  })
  afterEach(() => { vi.unstubAllGlobals(); vi.clearAllMocks() })

  it('does not retry server failures automatically, but supports an explicit retry and revokes the URL', async () => {
    mock.binaryRequest.mockRejectedValueOnce(new ApiError('Unavailable', 503)).mockResolvedValueOnce(image())
    const { result, unmount } = renderHook(() => usePrivateImage('/api/image/'))
    await waitFor(() => expect(result.current.error).toMatchObject({ status: 503 }))
    expect(mock.binaryRequest).toHaveBeenCalledTimes(1)
    act(() => result.current.retry())
    await waitFor(() => expect(result.current.objectUrl).toBe('blob:private-image'))
    expect(mock.binaryRequest).toHaveBeenCalledTimes(2)
    expect(result.current.error).toBeNull()
    unmount()
    expect(URL.revokeObjectURL).toHaveBeenCalledWith('blob:private-image')
  })

  it('does not repeatedly request denied images, but permits an explicit retry', async () => {
    mock.binaryRequest.mockRejectedValueOnce(new ApiError('Not found', 404)).mockResolvedValueOnce(image())
    const { result } = renderHook(() => usePrivateImage('/api/image/'))
    await waitFor(() => expect(result.current.error).toMatchObject({ status: 404 }))
    expect(mock.binaryRequest).toHaveBeenCalledTimes(1)
    act(() => result.current.retry())
    await waitFor(() => expect(result.current.objectUrl).toBe('blob:private-image'))
    expect(mock.binaryRequest).toHaveBeenCalledTimes(2)
  })

  it('rejects an HTML fallback instead of treating it as a successful image', async () => {
    mock.binaryRequest.mockResolvedValue(new Blob(['<html>Not Found</html>'], { type: 'text/html' }))
    const { result } = renderHook(() => usePrivateImage('/api/image/'))
    await waitFor(() => expect(result.current.error?.message).toContain('not an image'))
    expect(result.current.objectUrl).toBeNull()
    expect(URL.createObjectURL).not.toHaveBeenCalled()
  })
})
