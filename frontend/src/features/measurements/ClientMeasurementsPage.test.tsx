import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { cleanup, fireEvent, render, screen, waitFor } from '@testing-library/react'
import { MemoryRouter, Route, Routes } from 'react-router-dom'
import i18n from '../../i18n'
import { ClientMeasurementsPage } from './ClientMeasurementsPage'

const mock = vi.hoisted(() => ({
  context: { shopId: 'shop-1' as string | undefined, role: 'ADMIN' as string | null, workFunctions: [] as string[], isLoading: false },
  user: { is_main_supplier_admin: false },
  apiRequest: vi.fn(),
  shopsList: vi.fn(),
  clientList: vi.fn(), clientDetail: vi.fn(),
  getAllFamilies: vi.fn(), getAllShopVariants: vi.fn(), getOptionGroups: vi.fn(), getAllShopStyleOptions: vi.fn(),
  getAllShopDesigns: vi.fn(), getAllGlobalDesigns: vi.fn(), createShopDesign: vi.fn(), getShopDesign: vi.fn(), addShopDesignSelection: vi.fn(),
  definitions: vi.fn(), profiles: vi.fn(), createProfile: vi.fn(), sets: vi.fn(), saveSet: vi.fn(), copySet: vi.fn(), compare: vi.fn(), fabrics: vi.fn(), exportWorksheet: vi.fn(),
}))

vi.mock('../../hooks/useCurrentShop', () => ({ useCurrentShop: () => mock.context }))
vi.mock('../../services/useAuth', () => ({ useAuth: () => ({ user: mock.user }) }))
vi.mock('../../services/shops', () => ({ shopsService: { list: mock.shopsList } }))
vi.mock('../../services/apiClient', () => ({ apiRequest: mock.apiRequest, binaryRequest: vi.fn() }))
vi.mock('../clients/api', () => ({ clientsApi: { list: mock.clientList, detail: mock.clientDetail } }))
vi.mock('../catalog/api', () => ({
  getAllFamilies: mock.getAllFamilies, getAllShopVariants: mock.getAllShopVariants,
  getOptionGroups: mock.getOptionGroups, getAllShopStyleOptions: mock.getAllShopStyleOptions,
}))
vi.mock('../designs/api', () => ({
  getAllShopDesigns: mock.getAllShopDesigns, createShopDesign: mock.createShopDesign,
  getShopDesign: mock.getShopDesign, addShopDesignSelection: mock.addShopDesignSelection,
}))
vi.mock('../../backoffice/designs/api', () => ({ getAllGlobalDesigns: mock.getAllGlobalDesigns }))
vi.mock('./api', () => ({ measurementApi: {
  definitions: mock.definitions, profiles: mock.profiles, createProfile: mock.createProfile,
  sets: mock.sets, saveSet: mock.saveSet, copySet: mock.copySet, compare: mock.compare, fabrics: mock.fabrics,
  exportWorksheet: mock.exportWorksheet,
} }))
vi.mock('../../hooks/usePrivateImage', () => ({ usePrivateImage: () => ({ objectUrl: null, isLoading: false, error: null }) }))

const client = { id: 'client-1', name: 'Amina', phone: '+97450000000', email: 'amina@example.test', created_at: '2026-01-01T00:00:00Z', updated_at: '2026-01-01T00:00:00Z' }
const relatedPerson = { id: 'person-1', name: 'Sara', phone: '', phone_normalized: '', email: '', created_at: '2026-01-01T00:00:00Z', updated_at: '2026-01-01T00:00:00Z', primary_client_id: client.id }
const family = { id: 'family-1', name: "Men's Shirt", code: 'mens-shirt' }
const secondFamily = { id: 'family-2', name: 'Kuwaiti Dishdasha', code: 'kuwaiti-dishdasha' }
const variant = { id: 'variant-1', family: family.id, name: 'Standard Shirt', code: 'standard-shirt', is_default: true, is_global: true, is_active: true }
const group = { id: 'group-sleeve', name: 'Sleeve', code: 'sleeve', families: [family.id] }
const option = { id: 'option-full-sleeve', option_group: group.id, tenant: null, code: 'full-sleeve', name: 'Full Sleeve', is_active: true, is_global: true, reference_images: [] }
const profile = { id: 'profile-1', client: client.id, related_person: null, family: family.id, variant: variant.id, created_at: '2026-01-01T00:00:00Z' }
const definition = { id: 'definition-chest', code: 'CHEST', group_code: 'BODY', sort_order: 1, is_active: true, is_global: true, translations: [{ locale: 'en', name: 'Chest', description: 'Around the chest' }], mappings: [{ family_id: family.id, variant_id: variant.id, sort_order: 1 }] }
const makeSet = (id: string, version: number, value: string, unit: 'CM' | 'INCH' = 'CM') => ({
  id, profile: profile.id, version, copied_from: null, created_at: `2026-01-0${version}T10:00:00Z`,
  values: [{ id: `${id}-value`, definition: definition.id, definition_code_snapshot: 'CHEST', label_snapshot: 'Chest', label: 'Chest', translations: {}, value, unit }],
})

function renderPage(path = `/clients/${client.id}/measurements`) {
  return render(<MemoryRouter initialEntries={[path]}><Routes>
    <Route path="/clients/:clientId/measurements" element={<ClientMeasurementsPage />} />
    <Route path="/backoffice/measurements" element={<ClientMeasurementsPage />} />
    <Route path="/measurements" element={<ClientMeasurementsPage />} />
</Routes></MemoryRouter>)
}

async function chooseDropdownOption(label: string, optionValue: string) {
  const optionLabels: Record<string, string> = {
    [family.id]: family.name,
    [secondFamily.id]: secondFamily.name,
    [variant.id]: 'Standard Shirt · Default',
    'variant-2': 'Slim Shirt · Default',
    [relatedPerson.id]: 'Related Person - Sara',
    'shop-1': 'Test Shop',
  }
  fireEvent.click(await screen.findByLabelText(label))
  fireEvent.click(await screen.findByRole('option', { name: optionLabels[optionValue] }))
}

describe('Client Measurement workflow', () => {
  beforeEach(async () => {
    vi.clearAllMocks()
    await i18n.changeLanguage('en')
    mock.context = { shopId: 'shop-1', role: 'ADMIN', workFunctions: [], isLoading: false }
    mock.user = { is_main_supplier_admin: false }
    mock.shopsList.mockResolvedValue({ count: 1, next: null, previous: null, results: [{ id: 'shop-1', name: 'Test Shop', is_active: true }] })
    mock.clientList.mockResolvedValue({ count: 1, next: null, previous: null, results: [client] })
    mock.clientDetail.mockResolvedValue(client)
    mock.apiRequest.mockResolvedValue({ count: 0, next: null, previous: null, results: [] })
    mock.getAllFamilies.mockResolvedValue([family])
    mock.getAllShopVariants.mockResolvedValue([variant])
    mock.getOptionGroups.mockResolvedValue([group])
    mock.getAllShopStyleOptions.mockResolvedValue([option])
    mock.getAllShopDesigns.mockResolvedValue([])
    mock.getAllGlobalDesigns.mockResolvedValue([])
    mock.definitions.mockResolvedValue([definition])
    mock.profiles.mockResolvedValue([])
    mock.createProfile.mockResolvedValue(profile)
    mock.sets.mockResolvedValue([])
    mock.saveSet.mockImplementation(async (_shop: string, _client: string, _owner: unknown, _profile: string, values: Array<{ value: string; unit: 'CM' | 'INCH' }>) => ({
      ...makeSet('set-created', 1, values[0].value, values[0].unit),
    }))
    mock.copySet.mockResolvedValue(makeSet('set-copy', 3, '102.5'))
    mock.compare.mockResolvedValue({ from_set_id: 'set-1', to_set_id: 'set-2', results: [{ definition_id: definition.id, code: 'CHEST', label: 'Chest', from_value: '100', from_unit: 'CM', to_value: '42', to_unit: 'INCH', difference: null, unit_mismatch: true }] })
    mock.fabrics.mockResolvedValue([])
    mock.exportWorksheet.mockResolvedValue(new Blob(['%PDF-1.4']))
  })

  afterEach(cleanup)

  it('filters family designs locally when variant changes without repeating design requests', async () => {
    const otherVariant = { ...variant, id: 'variant-2', name: 'Slim Shirt', code: 'slim-shirt' }
    mock.getAllShopVariants.mockResolvedValue([variant, otherVariant])
    mock.getAllShopDesigns.mockResolvedValue([
      { id: 'design-1', name: 'Standard design', variant: variant.id },
      { id: 'design-2', name: 'Slim design', variant: otherVariant.id },
    ])
    renderPage()
    await chooseDropdownOption('Garment family', family.id)
    await waitFor(() => expect(mock.getAllShopDesigns).toHaveBeenCalledTimes(1))
    await chooseDropdownOption('Variant', otherVariant.id)
    fireEvent.click(screen.getByLabelText('Shop design / Global template'))
    expect(await screen.findByRole('option', { name: /Slim design/ })).toBeInTheDocument()
    expect(screen.queryByRole('option', { name: /Standard design/ })).not.toBeInTheDocument()
    expect(mock.getAllShopDesigns).toHaveBeenCalledTimes(1)
    expect(mock.getAllGlobalDesigns).toHaveBeenCalledTimes(1)
  })

  it('loads real catalog data and saves a new version with an explicit per-field unit', async () => {
    renderPage()
    expect(await screen.findByRole('heading', { name: /Measurements · Amina/ })).toBeInTheDocument()
    expect(mock.clientDetail).toHaveBeenCalledWith('shop-1', client.id)

    await chooseDropdownOption('Garment family', family.id)
    await waitFor(() => expect(mock.getOptionGroups).toHaveBeenCalledWith(family.id, 'en'))
    await chooseDropdownOption('Variant', variant.id)
    fireEvent.click(await screen.findByRole('button', { name: /Sleeve/ }))
    fireEvent.click(await screen.findByRole('button', { name: /Full Sleeve/ }))

    expect(await screen.findByRole('button', { name: /Create profile/ })).toBeInTheDocument()
    expect(mock.definitions).toHaveBeenCalledWith('shop-1', family.id, variant.id, 'en')
    fireEvent.click(screen.getByRole('button', { name: /Create profile/ }))
    const chestInput = await screen.findByLabelText('Chest')
    fireEvent.change(chestInput, { target: { value: '61.2500' } })
    fireEvent.click(screen.getByRole('button', { name: 'Chest unit: INCH' }))
    fireEvent.click(screen.getByRole('button', { name: 'Save new version' }))

    expect((await screen.findAllByText('Version 1')).length).toBeGreaterThan(0)
    expect(mock.saveSet).toHaveBeenCalledWith('shop-1', client.id, { kind: 'client' }, profile.id, [
      { definition_id: definition.id, value: '61.2500', unit: 'INCH' },
    ])
    expect(mock.saveSet).toHaveBeenCalledTimes(1)
    expect(screen.getAllByRole('button', { name: /^Version 1/ })).toHaveLength(1)
    expect(screen.getAllByText('61.2500 INCH').length).toBeGreaterThan(0)
    expect(screen.getAllByText(/Sleeve/).length).toBeGreaterThan(0)
  })

  it('exports the selected authorized Measurement version as a PDF', async () => {
    const first = makeSet('set-1', 1, '95.25')
    mock.profiles.mockResolvedValue([profile])
    mock.sets.mockResolvedValue([first])
    const createObjectUrl = vi.spyOn(URL, 'createObjectURL').mockReturnValue('blob:worksheet')
    const revokeObjectUrl = vi.spyOn(URL, 'revokeObjectURL').mockImplementation(() => {})
    const click = vi.spyOn(HTMLAnchorElement.prototype, 'click').mockImplementation(() => {})

    renderPage()
    await chooseDropdownOption('Garment family', family.id)
    await chooseDropdownOption('Variant', variant.id)
    fireEvent.click(await screen.findByRole('button', { name: /Open existing profile/ }))
    const exportButton = await screen.findByRole('button', { name: 'Export Version 1 PDF' })
    fireEvent.click(exportButton)

    await waitFor(() => expect(mock.exportWorksheet).toHaveBeenCalledWith(
      'shop-1', client.id, { kind: 'client' }, profile.id, first.id, undefined,
    ))
    expect(click).toHaveBeenCalledOnce()
    expect(createObjectUrl).toHaveBeenCalledOnce()
    expect(revokeObjectUrl).toHaveBeenCalledOnce()

    createObjectUrl.mockRestore()
    revokeObjectUrl.mockRestore()
    click.mockRestore()
  })

  it('creates exactly one Measurement version when Save is activated rapidly twice', async () => {
    mock.profiles.mockResolvedValue([profile])
    let finishSave: ((value: ReturnType<typeof makeSet>) => void) | undefined
    mock.saveSet.mockImplementationOnce(() => new Promise(resolve => { finishSave = resolve }))

    renderPage()
    await chooseDropdownOption('Garment family', family.id)
    await chooseDropdownOption('Variant', variant.id)
    fireEvent.click(await screen.findByRole('button', { name: /Open existing profile/ }))
    fireEvent.change(await screen.findByLabelText('Chest'), { target: { value: '100' } })
    fireEvent.click(screen.getByRole('button', { name: 'Chest unit: CM' }))

    const saveButton = screen.getByRole('button', { name: 'Save new version' })
    fireEvent.click(saveButton)
    fireEvent.click(saveButton)
    expect(mock.saveSet).toHaveBeenCalledTimes(1)

    finishSave?.(makeSet('set-once', 1, '100', 'CM'))
    expect(await screen.findByText('New measurement version saved.')).toBeInTheDocument()
    expect(screen.getAllByRole('button', { name: /^Version 1/ })).toHaveLength(1)
  })

  it('creates a persisted Shop Design from the selected group-based styles', async () => {
    const draft = { id: 'design-1', tenant: 'shop-1', family: family.id, variant: variant.id, name: 'Amina Shirt', status: 'ACTIVE', latest_version: { id: 'version-1', selections: [] }, created_at: '', updated_at: '' }
    const saved = { ...draft, latest_version: { ...draft.latest_version, selections: [{ option_group: group.id, style_option: option.id, selected_code: option.code, selected_name_en: option.name, style_option_name: option.name, style_option_translations: [], style_option_images: [] }] } }
    mock.createShopDesign.mockResolvedValue(draft)
    mock.addShopDesignSelection.mockResolvedValue({})
    mock.getShopDesign.mockResolvedValue(saved)

    renderPage()
    await chooseDropdownOption('Garment family', family.id)
    await chooseDropdownOption('Variant', variant.id)
    fireEvent.click(await screen.findByRole('button', { name: /Sleeve/ }))
    fireEvent.click(await screen.findByRole('button', { name: /Full Sleeve/ }))
    fireEvent.change(screen.getByLabelText('Design name'), { target: { value: 'Amina Shirt' } })
    fireEvent.click(screen.getByRole('button', { name: 'Save current selections as a Shop Design' }))

    expect(await screen.findByText('Design saved in Shop Designs.')).toBeInTheDocument()
    expect(mock.createShopDesign).toHaveBeenCalledWith('shop-1', { family_id: family.id, variant_id: variant.id, name: 'Amina Shirt' })
    expect(mock.addShopDesignSelection).toHaveBeenCalledWith('shop-1', 'version-1', { style_option_id: option.id })
    expect(mock.getShopDesign).toHaveBeenCalledWith('shop-1', 'design-1')
  })

  it('keeps measurement profiles and saves scoped to the selected Related Person', async () => {
    mock.apiRequest.mockResolvedValue({ count: 1, next: null, previous: null, results: [relatedPerson] })
    mock.createProfile.mockResolvedValue({ ...profile, id: 'related-profile', client: null, related_person: relatedPerson.id })
    renderPage()

    await chooseDropdownOption('Person being measured', relatedPerson.id)
    await waitFor(() => expect(mock.profiles).toHaveBeenCalledWith('shop-1', client.id, { kind: 'related_person', id: relatedPerson.id }))
    await chooseDropdownOption('Garment family', family.id)
    fireEvent.click(await screen.findByRole('button', { name: 'Create profile' }))

    await waitFor(() => expect(mock.createProfile).toHaveBeenCalledWith('shop-1', client.id, { kind: 'related_person', id: relatedPerson.id }, family.id, null))
    await waitFor(() => expect(mock.sets).toHaveBeenCalledWith('shop-1', client.id, { kind: 'related_person', id: relatedPerson.id }, 'related-profile'))
    fireEvent.change(await screen.findByLabelText('Chest'), { target: { value: '88.5' } })
    fireEvent.click(screen.getByRole('button', { name: 'Chest unit: CM' }))
    fireEvent.click(screen.getByRole('button', { name: 'Save new version' }))
    await waitFor(() => expect(mock.saveSet).toHaveBeenCalledWith('shop-1', client.id, { kind: 'related_person', id: relatedPerson.id }, 'related-profile', [
      { definition_id: definition.id, value: '88.5', unit: 'CM' },
    ]))
  })

  it('requires a user-selected unit before it saves a measurement version', async () => {
    renderPage()
    await chooseDropdownOption('Garment family', family.id)
    fireEvent.click(await screen.findByRole('button', { name: 'Create profile' }))
    fireEvent.change(await screen.findByLabelText('Chest'), { target: { value: '61.2500' } })
    fireEvent.click(screen.getByRole('button', { name: 'Save new version' }))

    expect(await screen.findByRole('alert')).toHaveTextContent('Enter at least one valid measurement value before saving.')
    expect(mock.saveSet).not.toHaveBeenCalled()
  })

  it('clears unsaved values when the selected garment family changes', async () => {
    mock.getAllFamilies.mockResolvedValue([family, secondFamily])
    const confirm = vi.spyOn(window, 'confirm').mockReturnValue(true)
    renderPage()
    await chooseDropdownOption('Garment family', family.id)
    fireEvent.click(await screen.findByRole('button', { name: 'Create profile' }))
    fireEvent.change(await screen.findByLabelText('Chest'), { target: { value: '61.2500' } })
    fireEvent.click(screen.getByRole('button', { name: 'Chest unit: INCH' }))

    await chooseDropdownOption('Garment family', secondFamily.id)
    await waitFor(() => expect(mock.definitions).toHaveBeenCalledWith('shop-1', secondFamily.id, null, 'en'))
    expect(confirm).toHaveBeenCalledWith('Discard unsaved measurement values?')
    fireEvent.click(await screen.findByRole('button', { name: 'Create profile' }))

    expect((await screen.findByLabelText('Chest') as HTMLInputElement).value).toBe('')
    expect(screen.getByRole('button', { name: 'Chest unit: CM' })).toHaveAttribute('aria-pressed', 'false')
    expect(screen.getByRole('button', { name: 'Chest unit: INCH' })).toHaveAttribute('aria-pressed', 'false')
    confirm.mockRestore()
  })

  it('prevents a second copy request while the first one is pending', async () => {
    mock.profiles.mockResolvedValue([profile])
    mock.sets.mockResolvedValue([makeSet('set-1', 1, '100', 'CM')])
    let completeCopy: ((value: ReturnType<typeof makeSet>) => void) | undefined
    mock.copySet.mockImplementation(() => new Promise(resolve => { completeCopy = resolve }))
    renderPage()
    await chooseDropdownOption('Garment family', family.id)
    await chooseDropdownOption('Variant', variant.id)
    fireEvent.click(await screen.findByRole('button', { name: /Open existing profile/ }))

    const copyButton = await screen.findByRole('button', { name: /Copy as a new immutable version/ })
    fireEvent.click(copyButton)
    fireEvent.click(copyButton)
    expect(mock.copySet).toHaveBeenCalledTimes(1)
    completeCopy?.(makeSet('set-copy', 2, '100', 'CM'))
    await waitFor(() => expect(screen.getByText('Copied measurement version created.')).toBeInTheDocument())
  })

  it('defaults comparison to the latest two adjacent versions', async () => {
    mock.profiles.mockResolvedValue([profile])
    mock.sets.mockResolvedValue([
      makeSet('set-3', 3, '102', 'CM'),
      makeSet('set-2', 2, '101', 'CM'),
      makeSet('set-1', 1, '100', 'CM'),
    ])
    renderPage()
    await chooseDropdownOption('Garment family', family.id)
    await chooseDropdownOption('Variant', variant.id)
    fireEvent.click(await screen.findByRole('button', { name: /Open existing profile/ }))
    fireEvent.click(await screen.findByRole('button', { name: 'Compare versions' }))

    await waitFor(() => expect(mock.compare).toHaveBeenCalledWith('shop-1', client.id, { kind: 'client' }, profile.id, 'set-2', 'set-3'))
  })

  it('shows history, copies a previous set through the backend, and reports unit mismatch on compare', async () => {
    mock.profiles.mockResolvedValue([profile])
    mock.sets.mockResolvedValue([makeSet('set-2', 2, '42', 'INCH'), makeSet('set-1', 1, '100', 'CM')])
    renderPage()
    await chooseDropdownOption('Garment family', family.id)
    await chooseDropdownOption('Variant', variant.id)
    fireEvent.click(await screen.findByRole('button', { name: /Open existing profile/ }))

    expect(await screen.findByRole('heading', { name: 'Measurement history' })).toBeInTheDocument()
    fireEvent.click(screen.getAllByRole('button', { name: /Copy as a new immutable version/ })[0])
    await waitFor(() => expect(mock.copySet).toHaveBeenCalledWith('shop-1', client.id, { kind: 'client' }, profile.id, 'set-2'))
    fireEvent.click(screen.getByRole('button', { name: 'Compare versions' }))
    expect(await screen.findByText('Unit mismatch')).toBeInTheDocument()
    expect(mock.compare).toHaveBeenCalledWith('shop-1', client.id, { kind: 'client' }, profile.id, 'set-1', 'set-2')
  })

  it('requires explicit Shop context for Main Supplier and denies STAFF without MEASUREMENT', async () => {
    mock.user = { is_main_supplier_admin: true }
    mock.context = { shopId: undefined, role: null, workFunctions: [], isLoading: false }
    mock.shopsList.mockResolvedValue({ count: 1, next: null, previous: null, results: [{ id: 'shop-1', name: 'Test Shop', is_active: true }] })
    const supplierView = renderPage('/backoffice/measurements')
    expect(await screen.findByLabelText('Choose a Shop')).toBeInTheDocument()
    expect(mock.definitions).not.toHaveBeenCalled()
    await chooseDropdownOption('Choose a Shop', 'shop-1')
    expect(await screen.findByPlaceholderText('Search clients by name or phone')).toBeInTheDocument()
    supplierView.unmount()

    mock.user = { is_main_supplier_admin: false }
    mock.context = { shopId: 'shop-1', role: 'STAFF', workFunctions: [], isLoading: false }
    renderPage()
    expect(await screen.findByText('Your account does not have access to measurement history.')).toBeInTheDocument()
    expect(mock.clientDetail).not.toHaveBeenCalled()
    expect(mock.definitions).not.toHaveBeenCalled()
  })

  it('shows a visible error instead of demo data when a real catalog request fails', async () => {
    mock.getAllFamilies.mockRejectedValue(new Error('Catalog temporarily unavailable.'))
    renderPage()
    expect(await screen.findByRole('alert')).toHaveTextContent('Catalog temporarily unavailable.')
    expect(screen.queryByRole('option', { name: "Men's Shirt" })).not.toBeInTheDocument()
  })
})
