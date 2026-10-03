import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { cleanup, fireEvent, render, screen, waitFor } from '@testing-library/react'
import { MemoryRouter, Route, Routes, useLocation } from 'react-router-dom'
import { CatalogPage } from './CatalogPage'
import i18n from '../../i18n'

const api = vi.hoisted(() => ({
  createShopStyleOption: vi.fn(), createShopVariant: vi.fn(), getAllFamilies: vi.fn(), getAllShopStyleOptions: vi.fn(),
  getAllShopVariants: vi.fn(), getShopVariantsPage: vi.fn(), getFamilyDetail: vi.fn(), getFamilies: vi.fn(), getOptionGroups: vi.fn(),
}))

vi.mock('./api', () => api)
vi.mock('../../hooks/useCurrentShop', () => ({ useCurrentShop: () => ({ shopId: 'shop-1', isLoading: false }) }))
vi.mock('../../hooks/usePrivateImage', () => ({ usePrivateImage: () => ({ objectUrl: null, isLoading: false, error: null }) }))
vi.mock('../../services/useAuth', () => ({ useAuth: () => ({ user: { is_main_supplier_admin: false } }) }))

const family = { id: 'family-1', code: 'shirt', name: 'Shirt', status: 'ACTIVE' as const, has_image: false, image_content_url: null }
const group = { id: 'group-1', name: 'Collar', code: 'collar', families: ['family-1'] }

function DesignRoute() {
  const location = useLocation()
  return <div>Design route {location.search}</div>
}

describe('Shop Catalog garment families', () => {
  beforeEach(async () => {
    await i18n.changeLanguage('en')
    api.getFamilies.mockResolvedValue({ count: 1, next: null, previous: null, results: [family] })
    api.getAllFamilies.mockResolvedValue([family])
    api.getOptionGroups.mockResolvedValue([group])
    api.getAllShopVariants.mockResolvedValue([])
    api.getShopVariantsPage.mockResolvedValue({ count: 0, next: null, previous: null, results: [] })
    api.getAllShopStyleOptions.mockResolvedValue([])
    api.getFamilyDetail.mockResolvedValue({ ...family, translations: [{ locale: 'en', name: 'Shirt', description: '' }], option_groups: [group] })
  })
  afterEach(() => { cleanup(); vi.clearAllMocks() })

  it('searches the live Family list and exposes browse-only details to a Shop', async () => {
    render(<MemoryRouter initialEntries={['/catalog']}><Routes><Route path="/catalog" element={<CatalogPage />} /></Routes></MemoryRouter>)
    expect(await screen.findByRole('button', { name: /Shirt.*shirt/i })).toBeInTheDocument()
    fireEvent.change(screen.getByPlaceholderText('Search families by name or code'), { target: { value: 'shirt' } })
    await waitFor(() => expect(api.getFamilies).toHaveBeenCalledWith(1, 'shirt'))
    fireEvent.click(screen.getByRole('button', { name: /Shirt.*shirt/i }))
    expect(await screen.findByRole('heading', { name: 'Shirt' })).toBeInTheDocument()
    expect(screen.getByRole('heading', { name: 'Applicable style groups' })).toBeInTheDocument()
    expect(screen.queryByRole('button', { name: /Archive|Edit family|New Family/i })).not.toBeInTheDocument()
  })

  it('filters variants by Family and opens that Family’s Designs route', async () => {
    render(<MemoryRouter initialEntries={['/catalog']}><Routes><Route path="/catalog" element={<CatalogPage />} /><Route path="/designs" element={<DesignRoute />} /></Routes></MemoryRouter>)
    fireEvent.click(await screen.findByRole('button', { name: /Shirt.*shirt/i }))
    fireEvent.click(await screen.findByRole('button', { name: 'View Variants' }))
    await waitFor(() => expect(api.getShopVariantsPage).toHaveBeenCalledWith('shop-1', expect.objectContaining({ family: 'family-1' })))
    fireEvent.click(screen.getByRole('tab', { name: 'Garment Families' }))
    fireEvent.click(await screen.findByRole('button', { name: /Shirt.*shirt/i }))
    fireEvent.click(await screen.findByRole('button', { name: 'View Designs' }))
    expect(await screen.findByText('Design route ?family=family-1')).toBeInTheDocument()
  })

  it('shows the backend total and follows pagination from the current Family search', async () => {
    api.getFamilies.mockReset()
    api.getFamilies.mockResolvedValueOnce({ count: 21, next: '/api/v1/catalog/families/?page=2', previous: null, results: [family] })
    api.getFamilies.mockResolvedValueOnce({ count: 21, next: null, previous: '/api/v1/catalog/families/?page=1', results: [{ ...family, id: 'family-2', name: 'Trousers' }] })
    render(<MemoryRouter initialEntries={['/catalog']}><Routes><Route path="/catalog" element={<CatalogPage />} /></Routes></MemoryRouter>)
    expect(await screen.findByText('21 families')).toBeInTheDocument()
    fireEvent.click(screen.getByRole('button', { name: 'Next' }))
    expect(await screen.findByRole('button', { name: /Trousers/ })).toBeInTheDocument()
    expect(api.getFamilies).toHaveBeenLastCalledWith(2, '')
  })
})
