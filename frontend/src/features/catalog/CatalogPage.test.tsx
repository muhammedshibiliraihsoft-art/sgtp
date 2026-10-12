import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { act, cleanup, fireEvent, render, screen, waitFor } from '@testing-library/react'
import { MemoryRouter, Route, Routes, useLocation } from 'react-router-dom'
import { CatalogPage } from './CatalogPage'
import i18n from '../../i18n'
import { ApiError } from '../../services/apiClient'

const api = vi.hoisted(() => ({
  createShopStyleOption: vi.fn(), createShopVariant: vi.fn(), createShopGarmentFamily: vi.fn(), createShopOptionGroup: vi.fn(), createShopFamilyOptionGroup: vi.fn(), getAllShopGarmentFamilies: vi.fn(), getAllShopOptionGroups: vi.fn(), getShopFamilyOptionGroups: vi.fn(), getAllShopStyleOptions: vi.fn(),
  getAllShopVariants: vi.fn(), getShopVariantsPage: vi.fn(), getFamilyDetail: vi.fn(), getFamilies: vi.fn(), getOptionGroups: vi.fn(), updateShopFamilyOptionGroups: vi.fn(),
  setShopDefaultFamilyStatus: vi.fn(), materializeShopDefaultFamily: vi.fn(),
  uploadShopStyleOptionImages: vi.fn(), updateShopStyleOptionTranslations: vi.fn(),
}))

vi.mock('./api', () => api)
vi.mock('../../hooks/useCurrentShop', () => ({ useCurrentShop: () => ({ shopId: 'shop-1', isLoading: false }) }))
vi.mock('../../hooks/usePrivateImage', () => ({ usePrivateImage: () => ({ objectUrl: null, isLoading: false, error: null }) }))
vi.mock('../../services/useAuth', () => ({ useAuth: () => ({ user: { is_main_supplier_admin: false } }) }))

const family = { id: 'family-1', tenant: 'shop-1', code: 'shirt', name: 'Shirt', status: 'ACTIVE' as const, has_image: false, image_content_url: null }
const group = { id: 'group-1', name: 'Collar', code: 'collar', families: ['family-1'] }

function DesignRoute() {
  const location = useLocation()
  return <div>Design route {location.search}</div>
}

describe('Shop Catalog garment families', () => {
  beforeEach(async () => {
    await i18n.changeLanguage('en')
    api.getFamilies.mockResolvedValue({ count: 1, next: null, previous: null, results: [family] })
    api.getAllShopGarmentFamilies.mockResolvedValue([family])
    api.getAllShopOptionGroups.mockResolvedValue([group])
    api.getShopFamilyOptionGroups.mockResolvedValue([{ option_group: group, sort_order: 0, selection_mode: 'SINGLE', is_required: false }])
    api.updateShopFamilyOptionGroups.mockResolvedValue([{ option_group: group, sort_order: 0, selection_mode: 'SINGLE', is_required: true }])
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
    expect(api.getAllShopGarmentFamilies).toHaveBeenCalledWith('shop-1', 'en', 'ACTIVE')
    fireEvent.click(screen.getByRole('button', { name: /Shirt.*shirt/i }))
    expect(await screen.findByRole('heading', { name: 'Shirt' })).toBeInTheDocument()
    expect(screen.getByRole('heading', { name: 'Applicable style groups' })).toBeInTheDocument()
    expect(screen.queryByRole('button', { name: /Remove from this Shop|Edit family|New Family/i })).not.toBeInTheDocument()
  })

  it('creates a Shop-local copy when a Shop user chooses to edit a global family', async () => {
    const globalFamily = { ...family, tenant: null }
    const globalGroup = { ...group, tenant: null, is_global: true }
    api.getAllShopGarmentFamilies.mockResolvedValue([globalFamily])
    api.getAllShopOptionGroups.mockResolvedValue([globalGroup])
    api.getShopFamilyOptionGroups.mockResolvedValue([{ option_group: globalGroup, sort_order: 0, selection_mode: 'SINGLE', is_required: false }])
    api.materializeShopDefaultFamily.mockResolvedValue({ ...family, id: 'family-shop-copy', tenant: 'shop-1', template_source: 'family-1' })
    render(<MemoryRouter initialEntries={['/catalog']}><Routes><Route path="/catalog" element={<CatalogPage />} /></Routes></MemoryRouter>)

    fireEvent.click(await screen.findByRole('button', { name: /Shirt.*shirt/i }))
    expect(await screen.findByRole('heading', { name: 'Applicable style groups' })).toBeInTheDocument()
    expect(screen.getByText('This is a Back Office default. Create a Shop-local copy to edit it without changing other Shops.')).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Collar' })).toBeInTheDocument()
    expect(screen.getAllByRole('checkbox')[0]).toBeDisabled()
    expect(screen.getByRole('combobox', { name: 'Selection' })).toBeDisabled()
    expect(screen.getByRole('checkbox', { name: 'Required' })).toBeDisabled()
    expect(screen.queryByRole('button', { name: 'Save style groups' })).not.toBeInTheDocument()

    fireEvent.click(screen.getByRole('button', { name: 'Edit in this Shop' }))
    await waitFor(() => expect(api.materializeShopDefaultFamily).toHaveBeenCalledWith('shop-1', 'family-1'))
    expect(await screen.findByRole('button', { name: 'Save style groups' })).toBeEnabled()
    expect(screen.getAllByRole('checkbox')[0]).toBeEnabled()
    expect(api.updateShopFamilyOptionGroups).not.toHaveBeenCalled()
  })

  it('keeps the family detail loading state while Shop configuration is pending', async () => {
    let resolveConfiguration!: (value: Array<{ option_group: typeof group; sort_order: number; selection_mode: 'SINGLE'; is_required: boolean }>) => void
    const configuration = [{ option_group: group, sort_order: 0, selection_mode: 'SINGLE' as const, is_required: false }]
    api.getShopFamilyOptionGroups.mockImplementationOnce(() => new Promise(resolve => { resolveConfiguration = resolve }))
    render(<MemoryRouter initialEntries={['/catalog']}><Routes><Route path="/catalog" element={<CatalogPage />} /></Routes></MemoryRouter>)

    fireEvent.click(await screen.findByRole('button', { name: /Shirt.*shirt/i }))
    expect(await screen.findByRole('status')).toHaveTextContent('Loading family details…')
    await act(async () => { resolveConfiguration(configuration) })
    expect(await screen.findByRole('heading', { name: 'Applicable style groups' })).toBeInTheDocument()
  })

  it('keeps the family detail error visible when configuration cannot load', async () => {
    api.getShopFamilyOptionGroups.mockRejectedValueOnce(new ApiError('Family configuration is unavailable.', 503, 'catalog_unavailable'))
    render(<MemoryRouter initialEntries={['/catalog']}><Routes><Route path="/catalog" element={<CatalogPage />} /></Routes></MemoryRouter>)

    fireEvent.click(await screen.findByRole('button', { name: /Shirt.*shirt/i }))
    expect(await screen.findByRole('alert')).toHaveTextContent('Family configuration is unavailable.')
    expect(screen.getByRole('button', { name: /Shirt/ })).toBeInTheDocument()
  })

  it('creates a Shop-owned garment family through the existing Catalog flow', async () => {
    api.createShopGarmentFamily.mockResolvedValue({ ...family, id: 'family-shop', tenant: 'shop-1', name: 'Custom Thobe', code: 'custom-thobe' })
    render(<MemoryRouter initialEntries={['/catalog']}><Routes><Route path="/catalog" element={<CatalogPage />} /></Routes></MemoryRouter>)
    fireEvent.click(await screen.findByRole('button', { name: 'New Garment family' }))
    fireEvent.change(screen.getByLabelText('Name (English)'), { target: { value: 'Custom Thobe' } })
    fireEvent.change(screen.getByLabelText(/Code/), { target: { value: 'custom-thobe' } })
    fireEvent.click(screen.getByRole('button', { name: 'Create' }))
    await waitFor(() => expect(api.createShopGarmentFamily).toHaveBeenCalledWith('shop-1', {
      code: 'custom-thobe', translations: [{ locale: 'en', name: 'Custom Thobe' }],
    }))
  })

  it('saves family option-group configuration with selection and required rules', async () => {
    render(<MemoryRouter initialEntries={['/catalog']}><Routes><Route path="/catalog" element={<CatalogPage />} /></Routes></MemoryRouter>)
    fireEvent.click(await screen.findByRole('button', { name: /Shirt.*shirt/i }))
    await screen.findByRole('heading', { name: 'Applicable style groups' })
    expect(screen.getAllByRole('checkbox')[0]).toBeEnabled()
    expect(screen.getByRole('combobox', { name: 'Selection' })).toBeEnabled()
    fireEvent.click(await screen.findByLabelText('Required'))
    fireEvent.click(screen.getByRole('button', { name: 'Save style groups' }))
    await waitFor(() => expect(api.updateShopFamilyOptionGroups).toHaveBeenCalledWith('shop-1', 'family-1', [
      { option_group_id: 'group-1', selection_mode: 'SINGLE', is_required: true, sort_order: 0 },
    ]))
  })

  it('creates a new style group locally and attaches it to the open Shop family', async () => {
    const newGroup = { id: 'group-new', tenant: 'shop-1', name: 'Fastening detail', code: 'fastening-detail', families: ['family-1'], is_global: false }
    api.createShopFamilyOptionGroup.mockResolvedValue({ option_group: newGroup, sort_order: 1, selection_mode: 'MULTI', is_required: false })
    render(<MemoryRouter initialEntries={['/catalog']}><Routes><Route path="/catalog" element={<CatalogPage />} /></Routes></MemoryRouter>)
    fireEvent.click(await screen.findByRole('button', { name: /Shirt.*shirt/i }))
    fireEvent.click(await screen.findByRole('button', { name: 'Add Shop-local style group' }))
    expect(screen.getByText('This group will be created for this Shop only and attached to this garment family.')).toBeInTheDocument()
    fireEvent.keyDown(document, { key: 'Escape' })
    expect(screen.queryByRole('dialog', { name: 'Add a Shop-local style group' })).not.toBeInTheDocument()
    expect(screen.getByRole('heading', { name: 'Applicable style groups' })).toBeInTheDocument()
    fireEvent.click(screen.getByRole('button', { name: 'Add Shop-local style group' }))
    fireEvent.change(screen.getByLabelText('Name (English)'), { target: { value: 'Fastening detail' } })
    fireEvent.change(screen.getByLabelText(/Code/), { target: { value: 'fastening-detail' } })
    fireEvent.click(screen.getByRole('button', { name: 'Create' }))
    await waitFor(() => expect(api.createShopFamilyOptionGroup).toHaveBeenCalledWith('shop-1', 'family-1', {
      code: 'fastening-detail', translations: [{ locale: 'en', name: 'Fastening detail' }],
    }))
    expect(await screen.findByRole('button', { name: 'Fastening detail' })).toBeInTheDocument()
  })

  it('lets Staff restore an archived Shop default without editing the Back Office source', async () => {
    const archived = { ...family, status: 'ARCHIVED' as const, template_source: 'global-family' }
    api.getAllShopGarmentFamilies.mockImplementation((_shop: string, _locale: string, state: string) => Promise.resolve(state === 'ARCHIVED' ? [archived] : [family]))
    api.setShopDefaultFamilyStatus.mockResolvedValue({ ...family, template_source: 'global-family' })
    render(<MemoryRouter initialEntries={['/catalog']}><Routes><Route path="/catalog" element={<CatalogPage />} /></Routes></MemoryRouter>)

    fireEvent.click(await screen.findByRole('button', { name: 'Show archived defaults' }))
    fireEvent.click(await screen.findByRole('button', { name: /Shirt.*Archived/i }))
    expect(await screen.findByRole('heading', { name: 'Applicable style groups' })).toBeInTheDocument()
    fireEvent.click(screen.getByRole('button', { name: 'Restore latest default' }))
    await waitFor(() => expect(api.setShopDefaultFamilyStatus).toHaveBeenCalledWith('shop-1', 'family-1', true))
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

  it('filters the combined Shop-visible family list and paginates it locally', async () => {
    api.getAllShopGarmentFamilies.mockResolvedValue(Array.from({ length: 21 }, (_, index) => ({ ...family, id: `family-${index}`, name: `Family ${index}`, code: `family-${index}` })))
    render(<MemoryRouter initialEntries={['/catalog']}><Routes><Route path="/catalog" element={<CatalogPage />} /></Routes></MemoryRouter>)
    expect(await screen.findByRole('button', { name: /Family 0/ })).toBeInTheDocument()
    fireEvent.click(screen.getByRole('button', { name: 'Next' }))
    expect(await screen.findByRole('button', { name: /Family 20/ })).toBeInTheDocument()
    expect(screen.queryByRole('button', { name: /Family 0/ })).not.toBeInTheDocument()
    expect(api.getAllShopGarmentFamilies).toHaveBeenCalledTimes(1)
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
