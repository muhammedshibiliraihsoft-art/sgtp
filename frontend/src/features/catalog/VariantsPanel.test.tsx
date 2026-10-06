import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { cleanup, fireEvent, render, screen, waitFor } from '@testing-library/react'
import { MemoryRouter, Route, Routes, useLocation } from 'react-router-dom'
import i18n from '../../i18n'
import { VariantsPanel } from './VariantsPanel'

const api = vi.hoisted(() => ({
  createGlobalVariant: vi.fn(), createShopVariant: vi.fn(), getAllGlobalVariants: vi.fn(), getAllShopVariants: vi.fn(), getGlobalVariant: vi.fn(), getGlobalVariantsPage: vi.fn(),
  getShopVariant: vi.fn(), getShopVariantsPage: vi.fn(), setGlobalVariantDefault: vi.fn(), setGlobalVariantStatus: vi.fn(),
  setShopVariantStatus: vi.fn(), updateGlobalVariant: vi.fn(), updateShopVariant: vi.fn(),
}))
const auth = vi.hoisted(() => ({ isMain: false, pathname: '/' }))
vi.mock('./api', () => api)
vi.mock('../../services/useAuth', () => ({ useAuth: () => ({ user: { is_main_supplier_admin: auth.isMain } }) }))

const family = { id: 'family-1', name: 'Abaya', code: 'abaya', status: 'ACTIVE' as const }
const variant = { id: 'variant-1', family: 'family-1', name: 'Classic', code: 'classic', is_default: false, is_global: false, is_active: true }
const detail = { ...variant, description: '', translations: [{ locale: 'en' as const, name: 'Classic', description: '' }], created_at: '', updated_at: '' }
const page = { count: 12, next: '/next', previous: null, results: [variant] }

function LocationText() {
  const location = useLocation()
  return <p>Design location {location.search}</p>
}

describe('VariantsPanel', () => {
  beforeEach(async () => {
    await i18n.changeLanguage('en')
    api.getAllShopVariants.mockResolvedValue([variant])
    api.getAllGlobalVariants.mockResolvedValue([variant])
    auth.isMain = false
    api.getShopVariantsPage.mockResolvedValue(page)
    api.getGlobalVariantsPage.mockResolvedValue(page)
    api.getShopVariant.mockResolvedValue(detail)
    api.getGlobalVariant.mockResolvedValue({ ...detail, is_global: true })
    api.createShopVariant.mockResolvedValue(detail)
    vi.spyOn(window, 'confirm').mockReturnValue(true)
  })
  afterEach(() => { cleanup(); vi.restoreAllMocks(); vi.clearAllMocks() })

  it('loads a paginated Shop list, filters by source and advances pages', async () => {
    render(<MemoryRouter><VariantsPanel shopId="shop-1" families={[family]} canManageVariants /></MemoryRouter>)
    expect(await screen.findByRole('button', { name: /Classic/ })).toBeInTheDocument()
    expect(screen.getByText('12 variants')).toBeInTheDocument()
    fireEvent.click(screen.getByRole('button', { name: 'Global' }))
    await waitFor(() => expect(api.getShopVariantsPage).toHaveBeenLastCalledWith('shop-1', expect.objectContaining({ source: 'global' })))
    fireEvent.click(screen.getByRole('button', { name: 'Next' }))
    await waitFor(() => expect(api.getShopVariantsPage).toHaveBeenLastCalledWith('shop-1', expect.objectContaining({ page: 2, source: 'global' })))
  })

  it('sends debounced search to the backend and creates a translated Shop Variant', async () => {
    render(<MemoryRouter><VariantsPanel shopId="shop-1" families={[family]} canManageVariants /></MemoryRouter>)
    await screen.findByRole('button', { name: /Classic/ })
    fireEvent.change(screen.getByPlaceholderText('Search variants...'), { target: { value: 'classic' } })
    await waitFor(() => expect(api.getShopVariantsPage).toHaveBeenLastCalledWith('shop-1', expect.objectContaining({ search: 'classic' })), { timeout: 1500 })
    fireEvent.click(screen.getByRole('button', { name: 'New Variant' }))
    fireEvent.change(screen.getByLabelText('Name (English)'), { target: { value: 'Modern' } })
    fireEvent.change(screen.getByLabelText('Code'), { target: { value: 'modern' } })
    fireEvent.click(screen.getByRole('button', { name: /Add translations/ }))
    fireEvent.change(screen.getAllByLabelText('Name', { selector: 'input' })[0], { target: { value: 'كلاسيكي' } })
    fireEvent.click(screen.getByRole('button', { name: 'Create' }))
    await waitFor(() => expect(api.createShopVariant).toHaveBeenCalledWith('shop-1', expect.objectContaining({
      family_id: 'family-1', code: 'modern', translations: expect.arrayContaining([expect.objectContaining({ locale: 'en', name: 'Modern' })]),
    })))
  })

  it('edits and archives a Shop-owned Variant without changing its code', async () => {
    api.updateShopVariant.mockResolvedValue({ ...detail, translations: [{ locale: 'en', name: 'Updated', description: '' }] })
    api.setShopVariantStatus.mockResolvedValue({ ...detail, is_active: false })
    render(<MemoryRouter><VariantsPanel shopId="shop-1" families={[family]} canManageVariants /></MemoryRouter>)
    fireEvent.click(await screen.findByRole('button', { name: /Classic/ }))
    fireEvent.click(await screen.findByRole('button', { name: 'Edit' }))
    fireEvent.change(screen.getByLabelText('Name (English)'), { target: { value: 'Updated' } })
    expect(screen.getByLabelText('Code')).toHaveValue('classic')
    fireEvent.click(screen.getByRole('button', { name: 'Save changes' }))
    await waitFor(() => expect(api.updateShopVariant).toHaveBeenCalledWith('shop-1', 'variant-1', expect.arrayContaining([expect.objectContaining({ locale: 'en', name: 'Updated' })])))
    fireEvent.click(screen.getByRole('button', { name: 'Archive' }))
    await waitFor(() => expect(api.setShopVariantStatus).toHaveBeenCalledWith('shop-1', 'variant-1', false))
  })

  it('keeps Global Shop Variants read-only and navigates with an exact Variant filter', async () => {
    api.getShopVariantsPage.mockResolvedValue({ ...page, results: [{ ...variant, is_global: true }] })
    api.getShopVariant.mockResolvedValue({ ...detail, is_global: true })
    render(<MemoryRouter initialEntries={['/']}><Routes><Route path="/" element={<VariantsPanel shopId="shop-1" families={[family]} canManageVariants />} /><Route path="/designs" element={<LocationText />} /></Routes></MemoryRouter>)
    fireEvent.click(await screen.findByRole('button', { name: /Classic/ }))
    expect(await screen.findByText('Global variants are managed by Main Supplier.')).toBeInTheDocument()
    expect(screen.queryByRole('button', { name: 'Edit' })).not.toBeInTheDocument()
    fireEvent.click(screen.getByRole('button', { name: 'View Designs' }))
    expect(await screen.findByText('Design location ?family=family-1&variant=variant-1')).toBeInTheDocument()
  })

  it('provides Global create and default management for Main Supplier', async () => {
    auth.isMain = true
    api.setGlobalVariantDefault.mockResolvedValue({ ...detail, is_global: true, is_default: true })
    render(<MemoryRouter><VariantsPanel families={[family]} /></MemoryRouter>)
    fireEvent.click(await screen.findByRole('button', { name: /Classic/ }))
    fireEvent.click(await screen.findByRole('button', { name: 'Set as Default' }))
    await waitFor(() => expect(api.setGlobalVariantDefault).toHaveBeenCalledWith('variant-1'))
    expect(screen.getByRole('button', { name: 'New Variant' })).toBeInTheDocument()
  })

  it('keeps Shop Variant mutation controls hidden for read-only members', async () => {
    render(<MemoryRouter><VariantsPanel shopId="shop-1" families={[family]} /></MemoryRouter>)
    fireEvent.click(await screen.findByRole('button', { name: /Classic/ }))
    expect(screen.queryByRole('button', { name: 'New Variant' })).not.toBeInTheDocument()
    expect(screen.queryByRole('group', { name: 'Status' })).not.toBeInTheDocument()
    expect(screen.queryByRole('button', { name: 'Edit' })).not.toBeInTheDocument()
  })

  it('shows only the embedded Family variants and completes selection to Designs without a nested drawer', async () => {
    const nextVariant = { ...variant, id: 'variant-2', name: 'Slim', code: 'slim' }
    api.getAllShopVariants.mockResolvedValue([variant, nextVariant])
    api.getShopVariant.mockResolvedValue({ ...detail, id: 'variant-2', name: 'Slim', code: 'slim' })
    render(<MemoryRouter initialEntries={['/catalog']}><Routes><Route path="/catalog" element={<VariantsPanel shopId="shop-1" families={[family]} embeddedFamilyId="family-1" canManageVariants />} /><Route path="/designs" element={<LocationText />} /></Routes></MemoryRouter>)
    const options = await screen.findAllByRole('button', { name: /Classic|Slim/ })
    const [firstOption, option] = options
    expect(api.getAllShopVariants).toHaveBeenCalledWith('shop-1', 'family-1', 'en', 'all')
    expect(screen.queryByPlaceholderText('Search variants...')).not.toBeInTheDocument()
    expect(screen.queryByRole('navigation', { name: 'Variant pages' })).not.toBeInTheDocument()

    firstOption.getBoundingClientRect = () => ({ x: 0, y: 0, left: 0, top: 0, right: 100, bottom: 50, width: 100, height: 50, toJSON: () => ({}) })
    option.getBoundingClientRect = () => ({ x: 120, y: 0, left: 120, top: 0, right: 220, bottom: 50, width: 100, height: 50, toJSON: () => ({}) })
    firstOption.focus()
    fireEvent.keyDown(firstOption, { key: 'ArrowRight' })
    expect(option).toHaveFocus()
    fireEvent.click(option)
    const nextStep = await screen.findByRole('button', { name: 'Continue to Designs' })
    expect(screen.getByRole('region', { name: /Slim/ })).toBeInTheDocument()
    expect(screen.queryByRole('dialog', { name: /Slim/ })).not.toBeInTheDocument()
    expect(nextStep).toHaveFocus()
    fireEvent.click(nextStep)
    expect(await screen.findByText('Design location ?family=family-1&variant=variant-2')).toBeInTheDocument()
  })

  it('creates a Global Variant with the selected Family and English translation', async () => {
    auth.isMain = true
    render(<MemoryRouter><VariantsPanel families={[family]} /></MemoryRouter>)
    fireEvent.click(await screen.findByRole('button', { name: 'New Variant' }))
    fireEvent.change(screen.getByLabelText('Name (English)'), { target: { value: 'Formal' } })
    fireEvent.change(screen.getByLabelText('Code'), { target: { value: 'formal' } })
    fireEvent.click(screen.getByRole('button', { name: 'Create' }))
    await waitFor(() => expect(api.createGlobalVariant).toHaveBeenCalledWith(expect.objectContaining({ family_id: 'family-1', code: 'formal', translations: [expect.objectContaining({ locale: 'en', name: 'Formal' })] })))
  })
})
