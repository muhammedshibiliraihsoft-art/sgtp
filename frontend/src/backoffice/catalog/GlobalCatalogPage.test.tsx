import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { cleanup, fireEvent, render, screen, waitFor } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { GlobalCatalogPage } from './GlobalCatalogPage'
import i18n from '../../i18n'

const api = vi.hoisted(() => ({
  createGlobalFamily: vi.fn(), createGlobalStyleOption: vi.fn(), createGlobalVariant: vi.fn(), getAllGlobalVariants: vi.fn(), getAllGlobalStyleOptions: vi.fn(), getGlobalVariant: vi.fn(), getGlobalVariantsPage: vi.fn(),
  getAllFamilies: vi.fn(), getFamilyDetail: vi.fn(), getFamilies: vi.fn(), getOptionGroups: vi.fn(), removeGlobalFamilyImage: vi.fn(),
  setGlobalFamilyStatus: vi.fn(), updateFamilyOptionGroups: vi.fn(), updateGlobalFamily: vi.fn(), uploadGlobalFamilyImage: vi.fn(), uploadGlobalStyleOptionImages: vi.fn(),
}))

vi.mock('../../features/catalog/api', () => api)
vi.mock('../../hooks/usePrivateImage', () => ({ usePrivateImage: () => ({ objectUrl: null, isLoading: false, error: null }) }))
vi.mock('../../services/useAuth', () => ({ useAuth: () => ({ user: { is_main_supplier_admin: true } }) }))

const family = { id: 'family-1', code: 'shirt', name: 'Shirt', status: 'ACTIVE' as const, has_image: false, image_content_url: null }
const group1 = { id: 'group-1', name: 'Collar', code: 'collar', families: ['family-1'] }
const group2 = { id: 'group-2', name: 'Cuff', code: 'cuff', families: ['family-1'] }
const styleOption = { id: 'style-1', option_group: 'group-1', tenant: null, code: 'band-collar', name: 'Band Collar', is_active: true, is_global: true, reference_images: [] }
const variant = { id: 'variant-1', family: 'family-1', name: 'Men’s Shirt', code: 'mens-shirt', is_default: true, is_global: true, is_active: true }

describe('Main Supplier Global Catalog Families', () => {
  beforeEach(async () => {
    await i18n.changeLanguage('en')
    api.getFamilies.mockResolvedValue({ count: 1, next: null, previous: null, results: [family] })
    api.getAllFamilies.mockResolvedValue([family])
    api.getOptionGroups.mockResolvedValue([group1, group2])
    api.getAllGlobalStyleOptions.mockResolvedValue([])
    api.getAllGlobalVariants.mockResolvedValue([variant])
    api.getGlobalVariant.mockResolvedValue({ ...variant, description: '', translations: [{ locale: 'en', name: 'Men’s Shirt', description: '' }], created_at: '', updated_at: '' })
    api.getGlobalVariantsPage.mockResolvedValue({ count: 0, next: null, previous: null, results: [] })
    api.createGlobalFamily.mockResolvedValue(family)
    api.updateGlobalFamily.mockResolvedValue({ ...family, translations: [{ locale: 'en', name: 'Shirt', description: '' }], option_groups: [group1] })
    api.updateFamilyOptionGroups.mockResolvedValue([group1])
    api.uploadGlobalFamilyImage.mockResolvedValue({ has_image: true, image_content_url: '/api/v1/catalog/families/family-1/image/' })
    api.removeGlobalFamilyImage.mockResolvedValue(undefined)
    api.getFamilyDetail.mockResolvedValue({ ...family, translations: [{ locale: 'en', name: 'Shirt', description: '' }], option_groups: [group1] })
    api.setGlobalFamilyStatus.mockResolvedValue({ ...family, status: 'ARCHIVED' })
    vi.spyOn(window, 'confirm').mockReturnValue(true)
  })
  afterEach(() => { cleanup(); vi.clearAllMocks(); vi.restoreAllMocks() })

  it('loads only data needed by the active catalog tab', async () => {
    render(<MemoryRouter><GlobalCatalogPage /></MemoryRouter>)
    await screen.findByRole('button', { name: /Shirt.*shirt/i })
    expect(api.getFamilies).toHaveBeenCalledTimes(1)
    expect(api.getOptionGroups).toHaveBeenCalledTimes(1)
    expect(api.getAllFamilies).not.toHaveBeenCalled()
    expect(api.getAllGlobalStyleOptions).not.toHaveBeenCalled()

    fireEvent.click(screen.getByRole('tab', { name: 'Style Options' }))
    await waitFor(() => expect(api.getAllGlobalStyleOptions).toHaveBeenCalledTimes(1))
    expect(api.getAllFamilies).not.toHaveBeenCalled()
    expect(api.getFamilies).toHaveBeenCalledTimes(1)

    expect(screen.queryByRole('tab', { name: 'Variants' })).not.toBeInTheDocument()
    expect(api.getAllFamilies).not.toHaveBeenCalled()
  })

  it('does not expose retired Variants in the selected Family drawer', async () => {
    render(<MemoryRouter><GlobalCatalogPage /></MemoryRouter>)
    fireEvent.click(await screen.findByRole('button', { name: /Shirt.*shirt/i }))
    expect(await screen.findByRole('heading', { name: 'Shirt' })).toBeInTheDocument()
    expect(screen.queryByRole('heading', { name: 'Variants' })).not.toBeInTheDocument()
    expect(screen.queryByRole('button', { name: /Men’s Shirt/ })).not.toBeInTheDocument()
    expect(api.getAllGlobalVariants).not.toHaveBeenCalled()
    expect(screen.queryByRole('tab', { name: 'Variants' })).not.toBeInTheDocument()
  })

  it('creates an English Family through the real global-family API contract', async () => {
    render(<MemoryRouter><GlobalCatalogPage /></MemoryRouter>)
    fireEvent.click(await screen.findByRole('button', { name: /New Family/ }))
    fireEvent.change(screen.getByLabelText(/Code/), { target: { value: 'jacket' } })
    fireEvent.change(screen.getByLabelText('Name (English)'), { target: { value: 'Jacket' } })
    fireEvent.click(screen.getByRole('button', { name: 'Create Family' }))
    await waitFor(() => expect(api.createGlobalFamily).toHaveBeenCalledWith({ code: 'jacket', translations: [{ locale: 'en', name: 'Jacket' }] }))
  })

  it('edits translations, applies ordered groups, and archives without deleting the Family', async () => {
    render(<MemoryRouter><GlobalCatalogPage /></MemoryRouter>)
    fireEvent.click(await screen.findByRole('button', { name: /Shirt.*shirt/i }))
    expect(await screen.findByRole('heading', { name: 'Shirt' })).toBeInTheDocument()
    fireEvent.change(screen.getByLabelText('Name (English)'), { target: { value: 'Dress Shirt' } })
    fireEvent.click(screen.getByRole('button', { name: 'Cuff · cuff' }))
    fireEvent.click(screen.getByRole('button', { name: 'Save changes' }))
    await waitFor(() => expect(api.updateGlobalFamily).toHaveBeenCalledWith('family-1', [{ locale: 'en', name: 'Dress Shirt' }]))
    expect(api.updateFamilyOptionGroups).toHaveBeenCalledWith('family-1', ['group-1', 'group-2'])
    fireEvent.click(screen.getByRole('button', { name: 'Archive' }))
    await waitFor(() => expect(api.setGlobalFamilyStatus).toHaveBeenCalledWith('family-1', false))
  })

  it('reactivates an archived Family through the reversible lifecycle action', async () => {
    const archived = { ...family, status: 'ARCHIVED' as const }
    api.getFamilies.mockResolvedValue({ count: 1, next: null, previous: null, results: [archived] })
    api.getFamilyDetail.mockResolvedValue({ ...archived, translations: [{ locale: 'en', name: 'Shirt', description: '' }], option_groups: [] })
    api.setGlobalFamilyStatus.mockResolvedValue(family)
    render(<MemoryRouter><GlobalCatalogPage /></MemoryRouter>)
    fireEvent.click(await screen.findByRole('button', { name: /Shirt.*shirt/i }))
    fireEvent.click(await screen.findByRole('button', { name: 'Reactivate' }))
    await waitFor(() => expect(api.setGlobalFamilyStatus).toHaveBeenCalledWith('family-1', true))
  })

  it('uploads and removes one optional private Family image', async () => {
    render(<MemoryRouter><GlobalCatalogPage /></MemoryRouter>)
    fireEvent.click(await screen.findByRole('button', { name: /Shirt.*shirt/i }))
    const file = new File(['image'], 'shirt.png', { type: 'image/png' })
    fireEvent.change(await screen.findByLabelText('Upload image'), { target: { files: [file] } })
    await waitFor(() => expect(api.uploadGlobalFamilyImage).toHaveBeenCalledWith('family-1', file))
    fireEvent.click(await screen.findByRole('button', { name: 'Remove image' }))
    await waitFor(() => expect(api.removeGlobalFamilyImage).toHaveBeenCalledWith('family-1'))
  })

  it('uploads a private reusable image to an existing global Style Option', async () => {
    api.getAllGlobalStyleOptions.mockResolvedValue([styleOption])
    render(<MemoryRouter><GlobalCatalogPage /></MemoryRouter>)
    fireEvent.click(await screen.findByRole('tab', { name: 'Style Options' }))
    const file = new File(['image'], 'band-collar.jpg', { type: 'image/jpeg' })
    fireEvent.change(await screen.findByLabelText('Add image for Band Collar'), { target: { files: [file] } })
    await waitFor(() => expect(api.uploadGlobalStyleOptionImages).toHaveBeenCalledWith('style-1', [file]))
  })

  it('allows optional private R2 images when creating a new global Style Option', async () => {
    api.createGlobalStyleOption.mockResolvedValue(styleOption)
    api.uploadGlobalStyleOptionImages.mockResolvedValue([])
    render(<MemoryRouter><GlobalCatalogPage /></MemoryRouter>)
    fireEvent.click(await screen.findByRole('tab', { name: 'Style Options' }))
    fireEvent.click(screen.getByRole('button', { name: 'New Style Option' }))
    fireEvent.change(screen.getByLabelText('Name (English)'), { target: { value: 'Band Collar' } })
    fireEvent.change(screen.getByLabelText('Code'), { target: { value: 'band-collar' } })
    fireEvent.click(screen.getByRole('button', { name: 'Collar' }))
    const file = new File(['image'], 'band-collar.jpg', { type: 'image/jpeg' })
    fireEvent.change(screen.getByLabelText(/Reference images/), { target: { files: [file] } })
    fireEvent.click(screen.getByRole('button', { name: 'Create' }))
    await waitFor(() => expect(api.createGlobalStyleOption).toHaveBeenCalledWith({ option_group_id: 'group-1', code: 'band-collar', translations: [{ locale: 'en', name: 'Band Collar' }] }))
    await waitFor(() => expect(api.uploadGlobalStyleOptionImages).toHaveBeenCalledWith('style-1', [file]))
  })
})
