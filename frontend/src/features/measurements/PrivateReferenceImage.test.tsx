import { act, cleanup, fireEvent, render, screen, waitFor } from '@testing-library/react'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { ApiError } from '../../services/apiClient'
import i18n from '../../i18n'
import { PrivateReferenceImage } from './PrivateReferenceImage'

const mock = vi.hoisted(() => ({ binaryRequest: vi.fn() }))
vi.mock('../../services/apiClient', async importOriginal => ({
  ...(await importOriginal<typeof import('../../services/apiClient')>()),
  binaryRequest: mock.binaryRequest,
}))

let notifyIntersection: IntersectionObserverCallback

class TestIntersectionObserver {
  constructor(callback: IntersectionObserverCallback) { notifyIntersection = callback }
  observe() {}
  disconnect() {}
  unobserve() {}
  takeRecords(): IntersectionObserverEntry[] { return [] }
  root = null
  rootMargin = '0px'
  thresholds = []
}

function enterViewport() {
  act(() => notifyIntersection([{ isIntersecting: true } as IntersectionObserverEntry], {} as IntersectionObserver))
}

describe('private style reference images', () => {
  beforeEach(async () => {
    await i18n.changeLanguage('en')
    vi.stubGlobal('IntersectionObserver', TestIntersectionObserver)
    vi.stubGlobal('URL', { ...URL, createObjectURL: vi.fn(() => 'blob:style-reference'), revokeObjectURL: vi.fn() })
    mock.binaryRequest.mockReset()
  })

  afterEach(() => {
    cleanup()
    vi.unstubAllGlobals()
  })

  it('waits until the thumbnail approaches the viewport before requesting its private image', async () => {
    mock.binaryRequest.mockResolvedValue(new Blob(['image'], { type: 'image/webp' }))
    render(<PrivateReferenceImage image={{ content_url: '/api/private/style-image/' }} alt="Collar reference" />)
    expect(mock.binaryRequest).not.toHaveBeenCalled()
    enterViewport()
    await waitFor(() => expect(mock.binaryRequest).toHaveBeenCalledOnce())
    expect(await screen.findByRole('img', { name: 'Collar reference' })).toHaveAttribute('src', 'blob:style-reference')
  })

  it('shows an explicit retry after a failed private-image request', async () => {
    mock.binaryRequest.mockRejectedValueOnce(new ApiError('Unavailable', 503))
      .mockResolvedValueOnce(new Blob(['image'], { type: 'image/webp' }))
    render(<PrivateReferenceImage image={{ content_url: '/api/private/style-image/' }} alt="Collar reference" />)
    enterViewport()
    await screen.findByText('Reference image unavailable')
    expect(mock.binaryRequest).toHaveBeenCalledOnce()
    fireEvent.click(screen.getByRole('button', { name: 'Retry image loading' }))
    expect(await screen.findByRole('img', { name: 'Collar reference' })).toHaveAttribute('src', 'blob:style-reference')
    expect(mock.binaryRequest).toHaveBeenCalledTimes(2)
  })
})
