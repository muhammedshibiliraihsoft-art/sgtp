import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { cleanup, fireEvent, render, screen, waitFor } from '@testing-library/react'
import { MemoryRouter, Route, Routes, useLocation } from 'react-router-dom'
import { CatalogPage } from './CatalogPage'
import i18n from '../../i18n'
import { ApiError } from '../../services/apiClient'

const api = vi.hoisted(() => ({
  createShopStyleOption: vi.fn(), createShopVariant: vi.fn(), getAllFamilies: vi.fn(), getAllShopStyleOptions: vi.fn(),
  getAllShopVariants: vi.fn(), getShopVariantsPage: vi.fn(), getFamilyDetail: vi.fn(), getFamilies: vi.fn(), getOptionGroups: vi.fn(),
  uploadShopStyleOptionImages: vi.fn(), updateShopStyleOptionTranslations: vi.fn(),
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

  it('uploads optional private reference images after creating a Shop style option', async () => {
    api.createShopStyleOption.mockResolvedValue({ id: 'style-1' })
    api.uploadShopStyleOptionImages.mockResolvedValue([])
    render(<MemoryRouter initialEntries={['/catalog?tab=styles']}><Routes><Route path="/catalog" element={<CatalogPage />} /></Routes></MemoryRouter>)

    fireEvent.click(await screen.findByRole('button', { name: 'New Style option' }))
    fireEvent.change(screen.getByLabelText('Name (English)'), { target: { value: 'Band Collar' } })
    fireEvent.change(screen.getByLabelText(/Code/), { target: { value: 'band-collar' } })
    const file = new File(['image'], 'band-collar.jpg', { type: 'image/jpeg' })
    fireEvent.change(screen.getByLabelText(/Reference image/), { target: { files: [file] } })
    fireEvent.click(screen.getByRole('button', { name: 'Create' }))

    await waitFor(() => expect(api.createShopStyleOption).toHaveBeenCalledWith('shop-1', {
      option_group_id: 'group-1', code: 'band-collar', translations: [{ locale: 'en', name: 'Band Collar' }],
    }))
    await waitFor(() => expect(api.uploadShopStyleOptionImages).toHaveBeenCalledWith('shop-1', 'style-1', [file]))
  })

  it('creates a Shop style option without attempting an image upload when no file is selected', async () => {
    api.createShopStyleOption.mockResolvedValue({ id: 'style-2' })
    render(<MemoryRouter initialEntries={['/catalog?tab=styles']}><Routes><Route path="/catalog" element={<CatalogPage />} /></Routes></MemoryRouter>)

    fireEvent.click(await screen.findByRole('button', { name: 'New Style option' }))
    fireEvent.change(screen.getByLabelText('Name (English)'), { target: { value: 'Spread Collar' } })
    fireEvent.change(screen.getByLabelText(/Code/), { target: { value: 'spread-collar' } })
    fireEvent.click(screen.getByRole('button', { name: 'Create' }))

    await waitFor(() => expect(api.createShopStyleOption).toHaveBeenCalled())
    expect(api.uploadShopStyleOptionImages).not.toHaveBeenCalled()
  })

  it('reports image upload failure and retries the upload without hiding the created option', async () => {
    api.createShopStyleOption.mockResolvedValue({ id: 'style-3' })
    api.uploadShopStyleOptionImages
      .mockRejectedValueOnce(new ApiError('Storage is unavailable.', 503, 'storage_unavailable'))
      .mockResolvedValueOnce([])
    render(<MemoryRouter initialEntries={['/catalog?tab=styles']}><Routes><Route path="/catalog" element={<CatalogPage />} /></Routes></MemoryRouter>)

    fireEvent.click(await screen.findByRole('button', { name: 'New Style option' }))
    fireEvent.change(screen.getByLabelText('Name (English)'), { target: { value: 'Button Collar' } })
    fireEvent.change(screen.getByLabelText(/Code/), { target: { value: 'button-collar' } })
    fireEvent.change(screen.getByLabelText(/Reference image/), {
      target: { files: [new File(['image'], 'button-collar.jpg', { type: 'image/jpeg' })] },
    })
    fireEvent.click(screen.getByRole('button', { name: 'Create' }))

    expect(await screen.findByRole('alert')).toHaveTextContent('Style option was created, but its image upload failed: Storage is unavailable.')
    expect(api.createShopStyleOption).toHaveBeenCalled()
    fireEvent.click(screen.getByRole('button', { name: 'Retry' }))
    await waitFor(() => expect(api.uploadShopStyleOptionImages).toHaveBeenCalledTimes(2))
    await waitFor(() => expect(screen.queryByRole('alert')).not.toBeInTheDocument())
  })

  it('opens the style editor, saves a Shop-owned name, and adds reference images', async () => {
    const style = { id: 'style-1', option_group: 'group-1', tenant: 'shop-1', code: 'band-collar', name: 'Band Collar', is_active: true, is_global: false, reference_images: [] }
    api.getAllShopStyleOptions.mockResolvedValue([style])
    api.updateShopStyleOptionTranslations.mockResolvedValue({ ...style, name: 'Classic Band Collar' })
    api.uploadShopStyleOptionImages.mockResolvedValue([{ id: 'image-1', content_url: '/private/image-1', mime_type: 'image/webp', byte_size: 100, width: 40, height: 40, sort_order: 0, alt_text: 'Band Collar' }])
    render(<MemoryRouter initialEntries={['/catalog?tab=styles']}><Routes><Route path="/catalog" element={<CatalogPage />} /></Routes></MemoryRouter>)

    fireEvent.click(await screen.findByRole('button', { name: /Collar.*collar/i }))
    fireEvent.click(await screen.findByRole('button', { name: /Band Collar.*band-collar.*Shop/i }))
    expect(screen.getByRole('complementary', { name: 'Style option preview and editor' })).toBeInTheDocument()
    fireEvent.change(screen.getByLabelText('Name (English)'), { target: { value: 'Classic Band Collar' } })
    fireEvent.click(screen.getByRole('button', { name: 'Save name' }))
    await waitFor(() => expect(api.updateShopStyleOptionTranslations).toHaveBeenCalledWith('shop-1', 'style-1', [{ locale: 'en', name: 'Classic Band Collar' }]))
    expect(await screen.findByRole('status')).toHaveTextContent('Style option name saved.')

    fireEvent.change(screen.getByLabelText('Add or replace image'), { target: { files: [new File(['image'], 'collar.png', { type: 'image/png' })] } })
    await waitFor(() => expect(api.uploadShopStyleOptionImages).toHaveBeenCalledWith('shop-1', 'style-1', expect.any(Array), expect.any(Function)))
    expect(await screen.findByText('Reference images uploaded successfully.')).toBeInTheDocument()
  })

  it('keeps Global options preview-only', async () => {
    api.getAllShopStyleOptions.mockResolvedValue([{ id: 'global-1', option_group: 'group-1', tenant: null, code: 'spread', name: 'Spread Collar', is_active: true, is_global: true, reference_images: [] }])
    render(<MemoryRouter initialEntries={['/catalog?tab=styles']}><Routes><Route path="/catalog" element={<CatalogPage />} /></Routes></MemoryRouter>)
    fireEvent.click(await screen.findByRole('button', { name: /Collar.*collar/i }))
    fireEvent.click(await screen.findByRole('button', { name: /Spread Collar.*spread.*Global/i }))
    expect(screen.getByText('Global style defaults are managed by the Main Supplier.')).toBeInTheDocument()
    expect(screen.queryByLabelText('Name (English)')).not.toBeInTheDocument()
    expect(screen.queryByLabelText('Add or replace image')).not.toBeInTheDocument()
  })
})
