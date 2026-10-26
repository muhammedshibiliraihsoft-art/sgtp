import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { act, cleanup, fireEvent, render, screen, waitFor, within } from '@testing-library/react'
import { MemoryRouter, Route, Routes } from 'react-router-dom'
import { CatalogPage } from './CatalogPage'
import i18n from '../../i18n'
import { ApiError } from '../../services/apiClient'

const api = vi.hoisted(() => ({
  createShopStyleOption: vi.fn(), getAllShopStyleOptions: vi.fn(), getAllShopFamilies: vi.fn(), getAllShopOptionGroups: vi.fn(), getShopFamilyOptionGroups: vi.fn(), createShopFamilyOptionGroup: vi.fn(), updateShopFamilyOptionGroups: vi.fn(), materializeShopDefaultFamily: vi.fn(),
  getAllShopVariants: vi.fn(), getShopVariant: vi.fn(), getShopVariantsPage: vi.fn(), getFamilyDetail: vi.fn(), getFamilies: vi.fn(), getOptionGroups: vi.fn(),
  uploadShopStyleOptionImages: vi.fn(), updateShopStyleOptionTranslations: vi.fn(),
}))
const privateImage = vi.hoisted(() => ({ usePrivateImage: vi.fn() }))
const shopContext = vi.hoisted(() => ({ role: 'VIEWER' as 'ADMIN' | 'STAFF' | 'VIEWER', workFunctions: [] as string[] }))
const measurements = vi.hoisted(() => ({ allDefinitions: vi.fn(), definitions: vi.fn(), attachDefinitionMapping: vi.fn(), createDefinition: vi.fn() }))

vi.mock('./api', () => api)
vi.mock('../../hooks/useCurrentShop', () => ({ useCurrentShop: () => ({ shopId: 'shop-1', role: shopContext.role, workFunctions: shopContext.workFunctions, isLoading: false }) }))
vi.mock('../../hooks/usePrivateImage', () => privateImage)
vi.mock('../../services/useAuth', () => ({ useAuth: () => ({ user: { is_main_supplier_admin: false } }) }))
vi.mock('../measurements/api', () => ({ measurementApi: measurements }))

const family = { id: 'family-1', tenant: null, code: 'shirt', name: 'Shirt', status: 'ACTIVE' as const, has_image: false, image_content_url: null }
const group = { id: 'group-1', name: 'Collar', code: 'collar', families: ['family-1'] }
const variant = { id: 'variant-1', family: 'family-1', name: 'Men’s Shirt', code: 'mens-shirt', is_default: true, is_global: true, is_active: true }
const variantDetail = { ...variant, description: '', translations: [{ locale: 'en' as const, name: 'Men’s Shirt', description: '' }], created_at: '', updated_at: '' }

function deferred<T>() {
  let resolve!: (value: T) => void
  const promise = new Promise<T>(done => { resolve = done })
  return { promise, resolve }
}

describe('Shop Catalog garment families', () => {
  beforeEach(async () => {
    privateImage.usePrivateImage.mockReturnValue({ objectUrl: null, isLoading: false, error: null, retry: vi.fn() })
    shopContext.role = 'ADMIN'
    shopContext.workFunctions = []
    await i18n.changeLanguage('en')
    api.getAllShopFamilies.mockResolvedValue([family])
    api.getAllShopOptionGroups.mockResolvedValue([group])
    api.getShopFamilyOptionGroups.mockResolvedValue([])
    api.createShopFamilyOptionGroup.mockResolvedValue({ id: 'family-group-2', option_group: { ...group, id: 'group-2', name: 'Cuff', code: 'cuff' }, sort_order: 0, selection_mode: 'SINGLE', is_required: false })
    api.updateShopFamilyOptionGroups.mockImplementation(async (_shop: string, _family: string, items: Array<{ option_group_id: string; selection_mode: 'SINGLE' | 'MULTI'; is_required: boolean; sort_order: number }>) => items.map((item, index) => ({ id: `family-group-${index}`, option_group: [group, { ...group, id: 'group-2', name: 'Cuff', code: 'cuff' }].find(entry => entry.id === item.option_group_id)!, ...item })))
    api.materializeShopDefaultFamily.mockResolvedValue({ ...family, id: 'family-local', tenant: 'shop-1' })
    api.getOptionGroups.mockResolvedValue([group])
    api.getAllShopVariants.mockResolvedValue([])
    api.getShopVariantsPage.mockResolvedValue({ count: 0, next: null, previous: null, results: [] })
    api.getShopVariant.mockResolvedValue(variantDetail)
    api.getAllShopStyleOptions.mockResolvedValue([])
    api.getFamilyDetail.mockRejectedValue(new ApiError('Page not found', 404, 'not_found'))
    measurements.allDefinitions.mockResolvedValue([])
    measurements.definitions.mockResolvedValue([])
    measurements.attachDefinitionMapping.mockResolvedValue({})
    measurements.createDefinition.mockResolvedValue({})
  })
  afterEach(() => { cleanup(); vi.clearAllMocks() })

  it('searches the live Family list and exposes browse-only details to a Shop', async () => {
    shopContext.role = 'VIEWER'
    render(<MemoryRouter initialEntries={['/catalog']}><Routes><Route path="/catalog" element={<CatalogPage />} /></Routes></MemoryRouter>)
    expect(await screen.findByRole('button', { name: /Shirt.*shirt/i })).toBeInTheDocument()
    fireEvent.change(screen.getByPlaceholderText('Search families by name or code'), { target: { value: 'shirt' } })
    await waitFor(() => expect(screen.getByRole('button', { name: /Shirt.*shirt/i })).toBeInTheDocument())
    fireEvent.click(screen.getByRole('button', { name: /Shirt.*shirt/i }))
    expect(await screen.findByRole('heading', { name: 'Shirt' })).toBeInTheDocument()
    expect(api.getShopFamilyOptionGroups).toHaveBeenCalledWith('shop-1', 'family-1')
    expect(api.getFamilyDetail).not.toHaveBeenCalled()
    expect(measurements.allDefinitions).not.toHaveBeenCalled()
    expect(measurements.definitions).not.toHaveBeenCalled()
    expect(screen.getByRole('heading', { name: 'Applicable style groups' })).toBeInTheDocument()
    expect(screen.queryByRole('button', { name: /Archive|Edit family|New Family/i })).not.toBeInTheDocument()
  })

  it('opens the Family drawer without loading retired Variants', async () => {
    render(<MemoryRouter initialEntries={['/catalog']}><Routes><Route path="/catalog" element={<CatalogPage />} /></Routes></MemoryRouter>)
    const familyCard = await screen.findByRole('button', { name: /Shirt.*shirt/i })
    expect(api.getAllShopVariants).not.toHaveBeenCalled()
    fireEvent.click(familyCard)
    expect(await screen.findByRole('heading', { name: 'Shirt' })).toBeInTheDocument()
    expect(api.getAllShopVariants).not.toHaveBeenCalled()
    expect(screen.queryByRole('tab', { name: 'Variants' })).not.toBeInTheDocument()
  })

  it('starts independent family and measurement reads in parallel when opening a garment', async () => {
    render(<MemoryRouter initialEntries={['/catalog']}><Routes><Route path="/catalog" element={<CatalogPage />} /></Routes></MemoryRouter>)
    const familyCard = await screen.findByRole('button', { name: /Shirt.*shirt/i })
    vi.clearAllMocks()

    const configs = deferred<never[]>()
    const groups = deferred<never[]>()
    const definitions = deferred<never[]>()
    const familyDefinitions = deferred<never[]>()
    api.getShopFamilyOptionGroups.mockReturnValueOnce(configs.promise)
    api.getAllShopOptionGroups.mockReturnValueOnce(groups.promise)
    measurements.allDefinitions.mockReturnValueOnce(definitions.promise)
    measurements.definitions.mockReturnValueOnce(familyDefinitions.promise)

    fireEvent.click(familyCard)

    await waitFor(() => expect(measurements.allDefinitions).toHaveBeenCalledWith('shop-1'))
    expect(api.getShopFamilyOptionGroups).toHaveBeenCalledWith('shop-1', 'family-1')
    expect(api.getAllShopOptionGroups).toHaveBeenCalledWith('shop-1')
    expect(api.getAllShopVariants).not.toHaveBeenCalled()
    expect(measurements.definitions).toHaveBeenCalledWith('shop-1', 'family-1', 'en')
    expect(api.getShopFamilyOptionGroups).toHaveBeenCalledOnce()
    expect(api.getAllShopOptionGroups).toHaveBeenCalledOnce()
    expect(measurements.allDefinitions).toHaveBeenCalledOnce()
    expect(measurements.definitions).toHaveBeenCalledOnce()

    await act(async () => {
      configs.resolve([])
      groups.resolve([])
      definitions.resolve([])
      familyDefinitions.resolve([])
      await Promise.all([configs.promise, groups.promise, definitions.promise, familyDefinitions.promise])
    })
    expect(await screen.findByRole('dialog', { name: 'Shirt' })).toBeInTheDocument()
  })

  it('does not reopen a family drawer when a pending request finishes after the user closes it', async () => {
    render(<MemoryRouter initialEntries={['/catalog']}><Routes><Route path="/catalog" element={<CatalogPage />} /></Routes></MemoryRouter>)
    const familyCard = await screen.findByRole('button', { name: /Shirt.*shirt/i })
    vi.clearAllMocks()

    const configs = deferred<never[]>()
    const groups = deferred<never[]>()
    const definitions = deferred<never[]>()
    const familyDefinitions = deferred<never[]>()
    api.getShopFamilyOptionGroups.mockReturnValueOnce(configs.promise)
    api.getAllShopOptionGroups.mockReturnValueOnce(groups.promise)
    measurements.allDefinitions.mockReturnValueOnce(definitions.promise)
    measurements.definitions.mockReturnValueOnce(familyDefinitions.promise)

    fireEvent.click(familyCard)
    expect(await screen.findByRole('dialog', { name: 'Garment family' })).toBeInTheDocument()
    fireEvent.click(screen.getByRole('button', { name: 'Close' }))
    expect(screen.queryByRole('dialog')).not.toBeInTheDocument()

    await act(async () => {
      configs.resolve([])
      groups.resolve([])
      definitions.resolve([])
      familyDefinitions.resolve([])
      await Promise.all([configs.promise, groups.promise, definitions.promise, familyDefinitions.promise])
    })
    expect(screen.queryByRole('dialog')).not.toBeInTheDocument()
  })

  it('filters the fully loaded Shop Family list locally', async () => {
    api.getAllShopFamilies.mockResolvedValue([family, { ...family, id: 'family-2', name: 'Trousers', code: 'trousers' }])
    render(<MemoryRouter initialEntries={['/catalog']}><Routes><Route path="/catalog" element={<CatalogPage />} /></Routes></MemoryRouter>)
    expect(await screen.findByRole('button', { name: /Trousers/ })).toBeInTheDocument()
    fireEvent.change(screen.getByPlaceholderText('Search families by name or code'), { target: { value: 'shirt' } })
    await waitFor(() => expect(screen.queryByRole('button', { name: /Trousers/ })).not.toBeInTheDocument())
    expect(screen.getByRole('button', { name: /Shirt.*shirt/i })).toBeInTheDocument()
  })

  it('configures a Shop family with style groups and preserves SINGLE/MULTI plus required settings', async () => {
    shopContext.role = 'ADMIN'
    api.getAllShopFamilies.mockResolvedValue([{ ...family, tenant: 'shop-1' }])
    api.getAllShopOptionGroups.mockResolvedValue([group, { ...group, id: 'group-2', name: 'Cuff', code: 'cuff' }])
    render(<MemoryRouter initialEntries={['/catalog']}><Routes><Route path="/catalog" element={<CatalogPage />} /></Routes></MemoryRouter>)

    fireEvent.click(await screen.findByRole('button', { name: /Shirt.*shirt/i }))
    await screen.findByRole('heading', { name: 'Shirt' })
    fireEvent.click(await screen.findByRole('checkbox', { name: /Cuff/ }))
    const selectionMode = screen.getByLabelText('Cuff Selection')
    expect(selectionMode).toHaveValue('SINGLE')
    fireEvent.change(selectionMode, { target: { value: 'MULTI' } })
    expect(selectionMode).toHaveValue('MULTI')
    fireEvent.change(selectionMode, { target: { value: 'SINGLE' } })
    expect(selectionMode).toHaveValue('SINGLE')
    fireEvent.change(selectionMode, { target: { value: 'MULTI' } })
    fireEvent.click(screen.getByLabelText('Required'))
    fireEvent.click(screen.getByRole('button', { name: 'Save style groups' }))

    await waitFor(() => expect(api.updateShopFamilyOptionGroups).toHaveBeenCalledWith('shop-1', 'family-1', [{
      option_group_id: 'group-2', selection_mode: 'MULTI', is_required: true, sort_order: 0,
    }]))
  })

  it('keeps the family drawer open and restores its trigger when the nested style-group dialog closes with Escape', async () => {
    api.getAllShopFamilies.mockResolvedValue([{ ...family, tenant: 'shop-1' }])
    render(<MemoryRouter initialEntries={['/catalog']}><Routes><Route path="/catalog" element={<CatalogPage />} /></Routes></MemoryRouter>)

    fireEvent.click(await screen.findByRole('button', { name: /Shirt.*shirt/i }))
    const drawer = await screen.findByRole('dialog', { name: 'Shirt' })
    const openDialogButton = within(drawer).getByRole('button', { name: 'Add Shop-local style group' })
    openDialogButton.focus()
    fireEvent.click(openDialogButton)

    const dialog = await screen.findByRole('dialog', { name: 'Create style group' })
    expect(drawer).toBeInTheDocument()
    expect(within(dialog).getByRole('button', { name: 'Close' })).toHaveFocus()
    fireEvent.keyDown(document, { key: 'Escape' })

    await waitFor(() => expect(screen.queryByRole('dialog', { name: 'Create style group' })).not.toBeInTheDocument())
    expect(screen.getByRole('dialog', { name: 'Shirt' })).toBeInTheDocument()
    expect(openDialogButton).toHaveFocus()
  })

  it('creates a Shop-local style group from above the drawer without losing drawer state', async () => {
    api.getAllShopFamilies.mockResolvedValue([{ ...family, tenant: 'shop-1' }])
    render(<MemoryRouter initialEntries={['/catalog']}><Routes><Route path="/catalog" element={<CatalogPage />} /></Routes></MemoryRouter>)

    fireEvent.click(await screen.findByRole('button', { name: /Shirt.*shirt/i }))
    const drawer = await screen.findByRole('dialog', { name: 'Shirt' })
    const addGroupButton = within(drawer).getByRole('button', { name: 'Add Shop-local style group' })
    expect(addGroupButton).toHaveClass('primary-button')
    fireEvent.click(addGroupButton)
    const dialog = await screen.findByRole('dialog', { name: 'Create style group' })
    fireEvent.change(within(dialog).getByLabelText('Name (English)'), { target: { value: 'New Cuff' } })
    fireEvent.change(within(dialog).getByLabelText('Code', { exact: false }), { target: { value: 'new-cuff' } })
    fireEvent.click(within(dialog).getByRole('button', { name: 'Create' }))

    await waitFor(() => expect(api.createShopFamilyOptionGroup).toHaveBeenCalledWith('shop-1', 'family-1', {
      code: 'new-cuff', translations: [{ locale: 'en', name: 'New Cuff' }],
    }))
    await waitFor(() => expect(screen.queryByRole('dialog', { name: 'Create style group' })).not.toBeInTheDocument())
    expect(screen.getByRole('dialog', { name: 'Shirt' })).toBeInTheDocument()
    expect(within(screen.getByRole('dialog', { name: 'Shirt' })).getByRole('checkbox', { name: /Cuff/ })).toBeInTheDocument()
  })

  it('maps an existing Shop measurement to a family and creates mapped definitions', async () => {
    shopContext.role = 'STAFF'
    shopContext.workFunctions = ['MEASUREMENT']
    const shopFamily = { ...family, tenant: 'shop-1' }
    const existing = { id: 'measurement-1', code: 'shoulder', group_code: 'upper', sort_order: 0, is_active: true, is_global: false, translations: [{ locale: 'en', name: 'Shoulder width', description: '' }], mappings: [] }
    const familyField = { ...existing, id: 'family-field', code: 'length', translations: [{ locale: 'en', name: 'Length', description: '' }], mappings: [{ family_id: 'family-1', sort_order: 0 }] }
    api.getAllShopFamilies.mockResolvedValue([shopFamily])
    measurements.allDefinitions.mockResolvedValue([existing])
    measurements.definitions.mockResolvedValue([familyField])
    measurements.attachDefinitionMapping.mockResolvedValue(existing)
    measurements.createDefinition.mockResolvedValue(existing)
    render(<MemoryRouter initialEntries={['/catalog']}><Routes><Route path="/catalog" element={<CatalogPage />} /></Routes></MemoryRouter>)

    fireEvent.click(await screen.findByRole('button', { name: /Shirt.*shirt/i }))
    expect(await screen.findByText('Length')).toBeInTheDocument()
    fireEvent.click(await screen.findByRole('button', { name: /Shoulder width \(shoulder\)/ }))
    fireEvent.click(screen.getByRole('button', { name: 'Add mapping' }))
    await waitFor(() => expect(measurements.attachDefinitionMapping).toHaveBeenCalledWith('shop-1', 'measurement-1', 'family-1'))

    fireEvent.click(screen.getByRole('button', { name: 'Create a measurement field' }))
    fireEvent.change(screen.getByLabelText('Name (English)'), { target: { value: 'Sleeve opening' } })
    fireEvent.change(screen.getByLabelText(/^Code/), { target: { value: 'sleeve-opening' } })
    fireEvent.click(screen.getByRole('button', { name: 'Create and map' }))
    await waitFor(() => expect(measurements.createDefinition).toHaveBeenCalledWith('shop-1', expect.objectContaining({
      code: 'sleeve-opening',
      translations: [{ locale: 'en', name: 'Sleeve opening' }],
      mappings: [{ family_id: 'family-1' }],
    })))
  })

  it('materializes a global family in this Shop before enabling measurement setup', async () => {
    shopContext.role = 'ADMIN'
    render(<MemoryRouter initialEntries={['/catalog']}><Routes><Route path="/catalog" element={<CatalogPage />} /></Routes></MemoryRouter>)
    fireEvent.click(await screen.findByRole('button', { name: /Shirt.*shirt/i }))
    await screen.findByRole('heading', { name: 'Shirt' })
    fireEvent.click(screen.getByRole('button', { name: 'Edit in this Shop' }))
    await waitFor(() => expect(api.materializeShopDefaultFamily).toHaveBeenCalledWith('shop-1', 'family-1'))
    await waitFor(() => expect(screen.getByText('Measurements')).toBeInTheDocument())
  })

  it('uploads optional private reference images after creating a Shop style option', async () => {
    api.createShopStyleOption.mockResolvedValue({ id: 'style-1' })
    api.uploadShopStyleOptionImages.mockResolvedValue([])
    render(<MemoryRouter initialEntries={['/catalog?tab=styles']}><Routes><Route path="/catalog" element={<CatalogPage />} /></Routes></MemoryRouter>)

    fireEvent.click(await screen.findByRole('button', { name: 'New Style option' }))
    fireEvent.change(screen.getByLabelText('Name (English)'), { target: { value: 'Band Collar' } })
    fireEvent.change(screen.getByLabelText(/Code/), { target: { value: 'band-collar' } })
    const file = new File(['image'], 'band-collar.jpg', { type: 'image/jpeg' })
    fireEvent.change(screen.getByLabelText(/Reference images/), { target: { files: [file] } })
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
    fireEvent.change(screen.getByLabelText(/Reference images/), {
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

    fireEvent.change(screen.getByLabelText('Add reference images'), { target: { files: [new File(['image'], 'collar.png', { type: 'image/png' })] } })
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
    expect(screen.queryByLabelText('Add reference images')).not.toBeInTheDocument()
  })

  it('shows a retry control when an uploaded reference cannot be read', async () => {
    const retry = vi.fn()
    const reference = { id: 'image-1', content_url: '/api/v1/shops/shop-1/catalog/style-options/style-1/reference-images/image-1/', mime_type: 'image/webp', byte_size: 100, width: 40, height: 40, sort_order: 0, alt_text: 'Band Collar' }
    api.getAllShopStyleOptions.mockResolvedValue([{ id: 'style-1', option_group: 'group-1', tenant: 'shop-1', code: 'band-collar', name: 'Band Collar', is_active: true, is_global: false, reference_images: [reference] }])
    privateImage.usePrivateImage.mockImplementation((url: string | null) => url === reference.content_url
      ? { objectUrl: null, isLoading: false, error: new ApiError('Not found', 404), retry }
      : { objectUrl: null, isLoading: false, error: null, retry: vi.fn() })
    render(<MemoryRouter initialEntries={['/catalog?tab=styles']}><Routes><Route path="/catalog" element={<CatalogPage />} /></Routes></MemoryRouter>)
    fireEvent.click(await screen.findByRole('button', { name: /Collar.*collar/i }))
    fireEvent.click(await screen.findByRole('button', { name: /Band Collar.*band-collar.*Shop/i }))
    expect(screen.getByText('Image unavailable')).toBeInTheDocument()
    fireEvent.click(screen.getByRole('button', { name: 'Retry image' }))
    expect(retry).toHaveBeenCalledOnce()
  })

  it('shows a retry control when an image response cannot be decoded', async () => {
    const retry = vi.fn()
    const reference = { id: 'image-2', content_url: '/api/image-2/', mime_type: 'image/webp', byte_size: 100, width: 40, height: 40, sort_order: 0, alt_text: 'Cuff' }
    api.getAllShopStyleOptions.mockResolvedValue([{ id: 'style-2', option_group: 'group-1', tenant: 'shop-1', code: 'cuff', name: 'Cuff', is_active: true, is_global: false, reference_images: [reference] }])
    privateImage.usePrivateImage.mockImplementation((url: string | null) => url === reference.content_url
      ? { objectUrl: 'blob:bad-image', isLoading: false, error: null, retry }
      : { objectUrl: null, isLoading: false, error: null, retry: vi.fn() })
    render(<MemoryRouter initialEntries={['/catalog?tab=styles']}><Routes><Route path="/catalog" element={<CatalogPage />} /></Routes></MemoryRouter>)
    fireEvent.click(await screen.findByRole('button', { name: /Collar.*collar/i }))
    fireEvent.click(await screen.findByRole('button', { name: /Cuff.*cuff.*Shop/i }))
    fireEvent.error(screen.getByRole('img', { name: 'Cuff' }))
    expect(screen.getByText('Image unavailable')).toBeInTheDocument()
    fireEvent.click(screen.getByRole('button', { name: 'Retry image' }))
    expect(retry).toHaveBeenCalledOnce()
  })
})
