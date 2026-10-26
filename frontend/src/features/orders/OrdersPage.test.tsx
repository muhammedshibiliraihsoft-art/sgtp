import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { cleanup, fireEvent, render, screen, waitFor } from '@testing-library/react'
import { MemoryRouter, Route, Routes } from 'react-router-dom'
import { ApiError } from '../../services/apiClient'
import { OrdersPage } from './OrdersPage'
import i18n from '../../i18n'

const mock = vi.hoisted(() => ({
  context: { shopId: 'shop-1', role: 'ADMIN' as 'ADMIN' | 'STAFF' | 'VIEWER', workFunctions: ['SALES'], isLoading: false },
  list: vi.fn(), detail: vi.fn(), create: vi.fn(), update: vi.fn(), assign: vi.fn(), advance: vi.fn(), remove: vi.fn(),
  clientList: vi.fn(), clientDetail: vi.fn(), relatedAll: vi.fn(), designs: vi.fn(), globalDesigns: vi.fn(), familyOptionGroups: vi.fn(), profiles: vi.fn(), sets: vi.fn(), fabrics: vi.fn(), members: vi.fn(),
  billingForWork: vi.fn(),
}))
vi.mock('../../hooks/useCurrentShop', () => ({ useCurrentShop: () => mock.context }))
vi.mock('./api', () => ({ ordersApi: { list: mock.list, detail: mock.detail, create: mock.create, update: mock.update, assign: mock.assign, advance: mock.advance, remove: mock.remove } }))
vi.mock('../clients/api', () => ({ clientsApi: { list: mock.clientList, detail: mock.clientDetail, relatedAll: mock.relatedAll } }))
vi.mock('../designs/api', () => ({ getAllShopDesigns: mock.designs }))
vi.mock('../../backoffice/designs/api', () => ({ getAllGlobalDesigns: mock.globalDesigns }))
vi.mock('../catalog/api', () => ({ getShopFamilyOptionGroups: mock.familyOptionGroups }))
vi.mock('../measurements/api', () => ({ measurementApi: { profiles: mock.profiles, sets: mock.sets, fabrics: mock.fabrics } }))
vi.mock('../../services/memberships', () => ({ getShopMembers: mock.members }))
vi.mock('../billing/api', () => ({ billingApi: { listForWork: mock.billingForWork } }))

const order = { id: 'order-1', work_number: 'ORD-000001', client_id: 'client-1', related_person_id: null, design_version_id: 'version-1', measurement_set_id: 'set-1', material_id: null, assigned_membership_id: null, status: 'REQUEST', priority: 'NORMAL', due_date: null, due_indicator: null, notes: '', created_at: '', updated_at: '' }
const client = { id: 'client-1', name: 'Amina', phone: '', email: '' }
const design = { id: 'design-1', name: 'Classic Abaya', status: 'ACTIVE', family: 'family-1', family_status: 'ACTIVE', variant: null, latest_published_version: { id: 'version-1', number: 2, status: 'PUBLISHED', selections: [{ id: 'selection-1', option_group: 'group-1', style_option: 'option-1', selected_code: 'CLOSED', selected_name_en: 'Closed Front', style_option_name: 'Closed Front', style_option_translations: [], style_option_images: [] }] } }
const profile = { id: 'profile-1', family: 'family-1', variant: null }
const set = { id: 'set-1', profile: 'profile-1', version: 2, created_at: '2026-10-20T12:00:00Z', values: [{ id: 'value-1', definition: 'definition-1', definition_code_snapshot: 'CHEST', label_snapshot: 'Bust/Chest', label: 'Bust/Chest', translations: {}, value: '40', unit: 'INCH' as const }] }
const optionGroups = [{ id: 'family-group-1', option_group: { id: 'group-1', name: 'Closure', code: 'CLOSURE', families: ['family-1'] }, sort_order: 0, selection_mode: 'SINGLE' as const, is_required: true }]
const dueIndicatorCases = [
  ['OVERDUE', 'Overdue'],
  ['DUE_TODAY', 'Due today'],
  ['DUE_SOON', 'Due soon'],
  ['UPCOMING', 'Upcoming'],
] as const

function page(path: string) {
  return render(<MemoryRouter initialEntries={[path]}><Routes><Route path="/orders" element={<OrdersPage />} /><Route path="/orders/new" element={<OrdersPage />} /><Route path="/orders/:id" element={<OrdersPage />} /></Routes></MemoryRouter>)
}

describe('Order page', () => {
  beforeEach(async () => {
    await i18n.changeLanguage('en')
    mock.context = { shopId: 'shop-1', role: 'ADMIN', workFunctions: ['SALES'], isLoading: false }
    mock.list.mockResolvedValue({ count: 1, next: null, previous: null, results: [order] })
    mock.detail.mockResolvedValue(order)
    mock.create.mockResolvedValue(order)
    mock.clientList.mockResolvedValue({ results: [client], count: 1, next: null, previous: null })
    mock.clientDetail.mockResolvedValue(client)
    mock.relatedAll.mockResolvedValue([])
    mock.designs.mockResolvedValue([design])
    mock.globalDesigns.mockResolvedValue([])
    mock.familyOptionGroups.mockResolvedValue(optionGroups)
    mock.profiles.mockResolvedValue([profile])
    mock.sets.mockResolvedValue([set])
    mock.fabrics.mockResolvedValue([])
    mock.members.mockResolvedValue([])
    mock.billingForWork.mockResolvedValue([])
  })
  afterEach(() => { cleanup(); vi.clearAllMocks() })

  it('shows real API list records rather than mock Work cards', async () => {
    page('/orders')
    expect(await screen.findByText('ORD-000001')).toBeInTheDocument()
    expect(mock.list).toHaveBeenCalledWith('shop-1', expect.objectContaining({ page: 1 }))
    expect(screen.queryByText('#ORD-1024')).not.toBeInTheDocument()
    expect(screen.queryByRole('link', { name: 'New Order' })).not.toBeInTheDocument()
    expect(screen.getByRole('link', { name: 'Deleted Orders' })).toHaveAttribute('href', '/orders/deleted')
  })

  it.each(dueIndicatorCases)('renders the %s indicator on an Order list card', async (indicator, label) => {
    mock.list.mockResolvedValueOnce({ count: 1, next: null, previous: null, results: [{ ...order, due_date: '2026-10-21', due_indicator: indicator }] })

    const { container } = page('/orders')

    const badge = await screen.findByText(label)
    expect(badge).toHaveClass('orders-due', `orders-due-${indicator.toLowerCase()}`)
    expect(container.querySelectorAll('.orders-due')).toHaveLength(1)
  })

  it.each(dueIndicatorCases)('renders the %s indicator in the Order detail summary', async (indicator, label) => {
    mock.detail.mockResolvedValueOnce({ ...order, due_date: '2026-10-21', due_indicator: indicator })
    mock.context = { shopId: 'shop-1', role: 'VIEWER', workFunctions: [], isLoading: false }

    page('/orders/order-1')

    expect(await screen.findByText(`2026-10-21 · ${label}`)).toBeInTheDocument()
  })

  it('does not render an indicator when the API returns no due date and no indicator', async () => {
    mock.list.mockResolvedValueOnce({ count: 1, next: null, previous: null, results: [{ ...order, due_date: null, due_indicator: null }] })

    const { container } = page('/orders')

    expect(await screen.findByText('No due date')).toBeInTheDocument()
    expect(container.querySelector('.orders-due')).not.toBeInTheDocument()
    expect(screen.queryByText(/Overdue|Due today|Due soon|Upcoming/)).not.toBeInTheDocument()
  })

  it('does not add a due label to the detail summary when the due date is absent', async () => {
    mock.detail.mockResolvedValueOnce({ ...order, due_date: null, due_indicator: null })
    mock.context = { shopId: 'shop-1', role: 'VIEWER', workFunctions: [], isLoading: false }

    page('/orders/order-1')

    expect(await screen.findByText('Due date')).toBeInTheDocument()
    const dueRow = screen.getByText('Due date').parentElement
    expect(dueRow?.querySelector('dd')).toHaveTextContent('—')
    expect(screen.queryByText(/Overdue|Due today|Due soon|Upcoming/)).not.toBeInTheDocument()
  })

  it('shows a load error without also claiming the order list is empty', async () => {
    mock.list.mockRejectedValueOnce(new Error('Internal server error.'))
    page('/orders')
    expect(await screen.findByRole('alert')).toHaveTextContent('Internal server error.')
    expect(screen.queryByText('No orders found.')).not.toBeInTheDocument()
  })

  it('advances to the next stage by selecting its workflow step and marks it current after the API succeeds', async () => {
    mock.context = { shopId: 'shop-1', role: 'STAFF', workFunctions: ['SALES'], isLoading: false }
    mock.advance.mockResolvedValueOnce({ ...order, status: 'CUTTING' })
    page('/orders/order-1')

    expect(await screen.findByText('ORD-000001')).toBeInTheDocument()
    fireEvent.click(screen.getByRole('button', { name: 'Cutting' }))

    await waitFor(() => expect(mock.advance).toHaveBeenCalledWith('shop-1', 'order-1', 'REQUEST'))
    expect(await screen.findByText('Moved to the next stage.')).toBeInTheDocument()
    expect(screen.getByText('Cutting', { selector: 'span' })).toHaveAttribute('aria-current', 'step')
    expect(screen.getByText('Stitching').closest('li')).not.toHaveClass('current')
  })

  it('keeps the workflow unchanged when the advance request fails', async () => {
    mock.context = { shopId: 'shop-1', role: 'STAFF', workFunctions: ['SALES'], isLoading: false }
    mock.advance.mockRejectedValueOnce(new Error('Current stage Work Function required.'))
    page('/orders/order-1')

    await screen.findByText('ORD-000001')
    fireEvent.click(screen.getByRole('button', { name: 'Cutting' }))

    expect(await screen.findByRole('alert')).toHaveTextContent('Current stage Work Function required.')
    expect(screen.getByText('Request', { selector: 'span' })).toHaveAttribute('aria-current', 'step')
    expect(screen.getByRole('button', { name: 'Cutting' })).toBeEnabled()
  })

  it('refreshes the order after a stale-stage conflict', async () => {
    mock.context = { shopId: 'shop-1', role: 'STAFF', workFunctions: ['SALES'], isLoading: false }
    page('/orders/order-1')

    await screen.findByText('ORD-000001')
    mock.advance.mockRejectedValueOnce(new ApiError('Work changed since it was loaded. Refresh and try again.', 409, 'stale_work'))
    mock.detail.mockResolvedValueOnce({ ...order, status: 'CUTTING' })
    fireEvent.click(screen.getByRole('button', { name: 'Cutting' }))

    expect(await screen.findByRole('alert')).toHaveTextContent('Work changed since it was loaded.')
    await waitFor(() => expect(screen.getByText('Cutting', { selector: 'span' })).toHaveAttribute('aria-current', 'step'))
  })

  it('disables stage selection while a transition is saving to prevent duplicate advances', async () => {
    mock.context = { shopId: 'shop-1', role: 'STAFF', workFunctions: ['SALES'], isLoading: false }
    let finishAdvance: ((value: typeof order) => void) | undefined
    mock.advance.mockImplementationOnce(() => new Promise(resolve => { finishAdvance = resolve }))
    page('/orders/order-1')

    await screen.findByText('ORD-000001')
    const cutting = screen.getByRole('button', { name: 'Cutting' })
    fireEvent.click(cutting)
    fireEvent.click(cutting)

    expect(mock.advance).toHaveBeenCalledTimes(1)
    expect(cutting).toBeDisabled()
    finishAdvance?.({ ...order, status: 'CUTTING' })
    await screen.findByText('Moved to the next stage.')
  })

  it('does not enable stage transitions without the current stage Work Function', async () => {
    mock.context = { shopId: 'shop-1', role: 'STAFF', workFunctions: [], isLoading: false }
    page('/orders/order-1')

    await screen.findByText('ORD-000001')
    expect(screen.getByRole('button', { name: 'Cutting' })).toBeDisabled()
    expect(mock.advance).not.toHaveBeenCalled()
  })

  it('prefills saved references from final review and creates the Work', async () => {
    page('/orders/new?client=client-1&measurement=set-1&design=version-1')
    await waitFor(() => expect(screen.getByRole('option', { name: /Classic Abaya/ })).toBeInTheDocument())
    await waitFor(() => expect(screen.getByRole('option', { name: /Version 2/ })).toBeInTheDocument())
    expect(await screen.findByText('Bust/Chest')).toBeInTheDocument()
    expect(screen.getByText('40 INCH')).toBeInTheDocument()
    expect(await screen.findByText('Closure')).toBeInTheDocument()
    expect(screen.getByText('Closed Front')).toBeInTheDocument()
    expect(screen.queryByRole('textbox', { name: 'Bust/Chest' })).not.toBeInTheDocument()
    fireEvent.click(screen.getByRole('button', { name: 'Create order' }))
    await waitFor(() => expect(mock.create).toHaveBeenCalledWith('shop-1', expect.objectContaining({ client_id: 'client-1', design_version_id: 'version-1', measurement_set_id: 'set-1' })))
    await waitFor(() => expect(mock.detail).toHaveBeenCalledWith('shop-1', 'order-1'))
  })

  it('does not offer an archived Design for a new order', async () => {
    mock.designs.mockResolvedValueOnce([{ ...design, status: 'ARCHIVED' }])
    page('/orders/new?client=client-1')

    expect(await screen.findByText(/No published design is available/)).toBeInTheDocument()
    expect(screen.queryByRole('option', { name: /Classic Abaya/ })).not.toBeInTheDocument()
  })

  it('does not offer a Design whose parent Family is archived', async () => {
    mock.designs.mockResolvedValueOnce([{ ...design, family_status: 'ARCHIVED' }])
    page('/orders/new?client=client-1')

    expect(await screen.findByText(/No published design is available/)).toBeInTheDocument()
    expect(screen.queryByRole('option', { name: /Classic Abaya/ })).not.toBeInTheDocument()
  })

  it('preserves a preselected Material when the loaded catalog contains it', async () => {
    mock.fabrics.mockResolvedValueOnce([{ material_id: 'material-1', name: 'Linen' }])
    page('/orders/new?client=client-1&measurement=set-1&design=version-1&material=material-1')
    const material = await screen.findByRole('combobox', { name: 'Fabric / material (optional)' })
    await waitFor(() => expect(material).toHaveValue('material-1'))
    await waitFor(() => expect(screen.getByRole('button', { name: 'Create order' })).toBeEnabled())

    fireEvent.click(screen.getByRole('button', { name: 'Create order' }))

    await waitFor(() => expect(mock.create).toHaveBeenCalledWith('shop-1', expect.objectContaining({ material_id: 'material-1' })))
  })

  it('blocks an unresolved preselected Material until the user explicitly clears it', async () => {
    mock.fabrics.mockResolvedValueOnce([])
    page('/orders/new?client=client-1&measurement=set-1&design=version-1&material=missing-material')

    expect(await screen.findByRole('alert')).toHaveTextContent('The preselected material is unavailable.')
    const createButton = screen.getByRole('button', { name: 'Create order' })
    expect(createButton).toBeDisabled()
    fireEvent.click(createButton)
    expect(mock.create).not.toHaveBeenCalled()

    fireEvent.change(screen.getByRole('combobox', { name: 'Fabric / material (optional)' }), { target: { value: '' } })
    expect(createButton).toBeEnabled()
    fireEvent.click(createButton)

    await waitFor(() => expect(mock.create).toHaveBeenCalledWith('shop-1', expect.objectContaining({ material_id: null })))
  })

  it('blocks a preselected Material when the lookup fails but permits an explicit no-material choice', async () => {
    mock.fabrics.mockRejectedValueOnce(new Error('Material service unavailable'))
    page('/orders/new?client=client-1&measurement=set-1&design=version-1&material=material-1')

    expect(await screen.findByRole('alert')).toHaveTextContent('The preselected material could not be verified.')
    const createButton = screen.getByRole('button', { name: 'Create order' })
    expect(createButton).toBeDisabled()

    fireEvent.change(screen.getByRole('combobox', { name: 'Fabric / material (optional)' }), { target: { value: '' } })
    await waitFor(() => expect(createButton).toBeEnabled())
    fireEvent.click(createButton)
    await waitFor(() => expect(mock.create).toHaveBeenCalledWith('shop-1', expect.objectContaining({ material_id: null })))
  })

  it('allows an order with no selected Material when the optional catalog lookup fails', async () => {
    mock.fabrics.mockRejectedValueOnce(new Error('Material service unavailable'))
    page('/orders/new?client=client-1&measurement=set-1&design=version-1')

    expect(await screen.findByRole('status')).toHaveTextContent('Material options could not be loaded.')
    const createButton = screen.getByRole('button', { name: 'Create order' })
    await waitFor(() => expect(createButton).toBeEnabled())
    fireEvent.click(createButton)

    await waitFor(() => expect(mock.create).toHaveBeenCalledWith('shop-1', expect.objectContaining({ material_id: null })))
  })

  it('clears wearer and saved measurements when the Client changes', async () => {
    const wearer = { id: 'person-1', name: 'Amina wearer' }
    const nextClient = { id: 'client-2', name: 'Nadia', phone: '', email: '' }
    mock.relatedAll.mockResolvedValueOnce([wearer])
    mock.clientList.mockResolvedValueOnce({ results: [nextClient], count: 1, next: null, previous: null })
    page('/orders/new?client=client-1&wearer=person-1&measurement=set-1&design=version-1')

    await waitFor(() => expect(screen.getByRole('combobox', { name: 'Wearer' })).toHaveValue('person-1'))
    await waitFor(() => expect(screen.getByRole('combobox', { name: 'Saved measurement version' })).toHaveValue('set-1'))
    fireEvent.click(screen.getByRole('button', { name: 'Change' }))
    fireEvent.change(screen.getByRole('textbox', { name: 'Find client' }), { target: { value: 'Nadia' } })
    fireEvent.click(await screen.findByRole('button', { name: 'Nadia' }))

    await waitFor(() => expect(screen.getByRole('combobox', { name: 'Wearer' })).toHaveValue(''))
    await waitFor(() => expect(screen.getByRole('combobox', { name: 'Saved measurement version' })).toHaveValue(''))
  })

  it('preserves the compatible saved measurement on same-family design change and clears it across families', async () => {
    const wearer = { id: 'person-1', name: 'Amina wearer' }
    const secondDesign = { ...design, id: 'design-2', name: 'Second Abaya', latest_published_version: { id: 'version-2', number: 3, status: 'PUBLISHED', selections: [] } }
    const otherFamilyDesign = { ...design, id: 'design-3', family: 'family-2', name: 'Dress', latest_published_version: { id: 'version-3', number: 1, status: 'PUBLISHED', selections: [] } }
    mock.relatedAll.mockResolvedValueOnce([wearer])
    mock.designs.mockResolvedValueOnce([design, secondDesign, otherFamilyDesign])
    page('/orders/new?client=client-1&wearer=person-1&measurement=set-1&design=version-1')

    await waitFor(() => expect(screen.getByRole('combobox', { name: 'Saved measurement version' })).toHaveValue('set-1'))
    fireEvent.change(screen.getByRole('combobox', { name: 'Wearer' }), { target: { value: '' } })
    await waitFor(() => expect(screen.getByRole('combobox', { name: 'Saved measurement version' })).toHaveValue(''))
    fireEvent.change(screen.getByRole('combobox', { name: 'Saved measurement version' }), { target: { value: 'set-1' } })
    await waitFor(() => expect(screen.getByRole('combobox', { name: 'Saved measurement version' })).toHaveValue('set-1'))

    fireEvent.change(screen.getByRole('combobox', { name: 'Published design' }), { target: { value: 'version-2' } })
    await waitFor(() => expect(screen.getByRole('combobox', { name: 'Saved measurement version' })).toHaveValue('set-1'))
    fireEvent.change(screen.getByRole('combobox', { name: 'Published design' }), { target: { value: 'version-3' } })
    await waitFor(() => expect(screen.getByRole('combobox', { name: 'Saved measurement version' })).toHaveValue(''))
  })

  it('keeps the create form usable when the backend rejects a stale Design', async () => {
    mock.create.mockRejectedValueOnce(new Error('The selected Design is archived.'))
    page('/orders/new?client=client-1&measurement=set-1&design=version-1')
    await waitFor(() => expect(screen.getByRole('option', { name: /Classic Abaya/ })).toBeInTheDocument())
    await waitFor(() => expect(screen.getByRole('combobox', { name: 'Saved measurement version' })).toHaveValue('set-1'))
    await waitFor(() => expect(screen.getByRole('button', { name: 'Create order' })).toBeEnabled())

    fireEvent.click(screen.getByRole('button', { name: 'Create order' }))

    await waitFor(() => expect(mock.create).toHaveBeenCalledTimes(1))
    expect(await screen.findByRole('alert')).toHaveTextContent('The selected Design is archived.')
    expect(screen.getByRole('heading', { name: 'New Order' })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Create order' })).toBeEnabled()
  })

  it('blocks duplicate create submissions while the first request is pending', async () => {
    let finishCreate: ((value: typeof order) => void) | undefined
    mock.create.mockImplementationOnce(() => new Promise(resolve => { finishCreate = resolve }))
    page('/orders/new?client=client-1&measurement=set-1&design=version-1')
    await waitFor(() => expect(screen.getByRole('option', { name: /Classic Abaya/ })).toBeInTheDocument())
    await waitFor(() => expect(screen.getByRole('combobox', { name: 'Saved measurement version' })).toHaveValue('set-1'))

    const createButton = screen.getByRole('button', { name: 'Create order' })
    fireEvent.click(createButton)
    fireEvent.click(createButton)

    await waitFor(() => expect(mock.create).toHaveBeenCalledTimes(1))
    await waitFor(() => expect(screen.getByRole('button', { name: 'Creating…' })).toBeDisabled())
    finishCreate?.(order)
  })

  it('matches a legacy variant-linked measurement profile by family for a published design', async () => {
    mock.designs.mockResolvedValueOnce([{ ...design, variant: null }])
    mock.profiles.mockResolvedValueOnce([{ ...profile, variant: 'legacy-variant' }])
    page('/orders/new?client=client-1&measurement=set-1&design=version-1')
    await waitFor(() => expect(screen.getByRole('option', { name: /Version 2/ })).toBeInTheDocument())
    expect(screen.getByRole('button', { name: 'Create order' })).toBeEnabled()
  })

  it('does not offer creation to a viewer', async () => {
    mock.context.role = 'VIEWER'
    page('/orders')
    await screen.findByText('ORD-000001')
    expect(screen.queryByRole('link', { name: 'New Order' })).not.toBeInTheDocument()
    expect(screen.queryByRole('link', { name: 'Deleted Orders' })).not.toBeInTheDocument()
  })
})
