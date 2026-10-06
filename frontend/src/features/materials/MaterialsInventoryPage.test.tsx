import { afterEach, describe, expect, it, vi } from 'vitest'
import { cleanup, fireEvent, render, screen, waitFor } from '@testing-library/react'
import { MaterialsInventoryPage } from './MaterialsInventoryPage'

const mock = vi.hoisted(() => ({ apiRequest: vi.fn() }))
vi.mock('../../hooks/useCurrentShop', () => ({ useCurrentShop: () => ({ shopId: 'shop-1', role: 'ADMIN', isLoading: false }) }))
vi.mock('../../services/apiClient', () => ({ apiRequest: mock.apiRequest }))

const page = { count: 0, next: null, previous: null, results: [] }

describe('Shop inventory request flow', () => {
  afterEach(() => { cleanup(); vi.clearAllMocks() })

  it('debounces inventory search and reuses the material list during search', async () => {
    mock.apiRequest.mockResolvedValue(page)
    render(<MaterialsInventoryPage />)
    await waitFor(() => expect(mock.apiRequest).toHaveBeenCalledTimes(2))

    fireEvent.change(screen.getByRole('textbox', { name: 'Search' }), { target: { value: 'c' } })
    fireEvent.change(screen.getByRole('textbox', { name: 'Search' }), { target: { value: 'co' } })
    fireEvent.change(screen.getByRole('textbox', { name: 'Search' }), { target: { value: 'cotton' } })
    expect(mock.apiRequest).toHaveBeenCalledTimes(2)
    await waitFor(() => expect(mock.apiRequest).toHaveBeenCalledWith('/api/v1/shops/shop-1/inventory/items/?search=cotton'))
    expect(mock.apiRequest).toHaveBeenCalledTimes(3)
    expect(mock.apiRequest).toHaveBeenCalledWith('/api/v1/shops/shop-1/materials/')

    fireEvent.click(screen.getByRole('button', { name: 'Materials' }))
    fireEvent.change(screen.getByRole('textbox', { name: 'Search' }), { target: { value: 'silk' } })
    await new Promise(resolve => window.setTimeout(resolve, 300))
    expect(mock.apiRequest).toHaveBeenCalledTimes(3)

    fireEvent.click(screen.getByRole('button', { name: /Refresh/ }))
    await waitFor(() => expect(mock.apiRequest).toHaveBeenCalledTimes(5))
  })
})
