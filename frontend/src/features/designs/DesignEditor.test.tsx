import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { cleanup, fireEvent, render, screen, waitFor } from '@testing-library/react'
import { MemoryRouter, Route, Routes } from 'react-router-dom'
import { DesignEditor } from './DesignEditor'

const api = vi.hoisted(() => ({
  addShopDesignSelection: vi.fn(), getShopDesign: vi.fn(), getAllShopStyleOptions: vi.fn(),
  getShopFamilyOptionGroups: vi.fn(), publishShopDesignVersion: vi.fn(), updateShopDesignSelection: vi.fn(), uploadShopDesignReferences: vi.fn(),
  usePrivateImage: vi.fn(),
}))

vi.mock('./api', () => ({
  addShopDesignSelection: api.addShopDesignSelection,
  updateShopDesignSelection: api.updateShopDesignSelection,
  getShopDesign: api.getShopDesign,
  publishShopDesignVersion: api.publishShopDesignVersion,
  uploadShopDesignReferences: api.uploadShopDesignReferences,
}))
vi.mock('../catalog/api', () => ({ getShopFamilyOptionGroups: api.getShopFamilyOptionGroups, getAllShopStyleOptions: api.getAllShopStyleOptions }))
vi.mock('../../hooks/useCurrentShop', () => ({ useCurrentShop: () => ({ shopId: 'shop-1', isLoading: false }) }))
vi.mock('../../services/useAuth', () => ({ useAuth: () => ({ user: { is_main_supplier_admin: false } }) }))
vi.mock('../../hooks/usePrivateImage', () => ({ usePrivateImage: api.usePrivateImage }))

const optionImage = {
  id: 'image-1', content_url: '/private/curve-collar/', mime_type: 'image/webp',
  byte_size: 1200, width: 120, height: 120, sort_order: 0, alt_text: 'Curve Collar',
}
const selection = {
  id: 'selection-1', option_group: 'group-1', style_option: 'style-1', selected_code: 'curve-collar',
  selected_name_en: 'Curve Collar', style_option_name: 'Curve Collar', style_option_translations: [],
  style_option_images: [],
}
const design = {
  id: 'design-1', tenant: 'shop-1', family: 'shirt', variant: '', name: 'Test design', status: 'ACTIVE',
  created_at: '', updated_at: '', latest_version: {
    id: 'version-1', number: 1, name: 'Test design', translations: [], status: 'DRAFT', published_at: null,
    selections: [selection], references: [],
  },
}
const emptyDesign = { ...design, latest_version: { ...design.latest_version, selections: [] } }
const familyGroups = [
  { id: 'mapping-1', option_group: { id: 'group-1', name: 'Collar', code: 'collar', families: ['shirt'] }, sort_order: 1, selection_mode: 'SINGLE' as const, is_required: true },
  { id: 'mapping-2', option_group: { id: 'group-2', name: 'Cuff', code: 'cuff', families: ['shirt'] }, sort_order: 2, selection_mode: 'MULTI' as const, is_required: false },
]
const styleOptions = [
  { id: 'style-1', option_group: 'group-1', tenant: null, code: 'curve-collar', name: 'Curve Collar', is_active: true, is_global: true, reference_images: [optionImage] },
  { id: 'style-2', option_group: 'group-1', tenant: null, code: 'band-collar', name: 'Band Collar', is_active: true, is_global: true, reference_images: [] },
  { id: 'style-3', option_group: 'group-2', tenant: 'shop-1', code: 'button-cuff', name: 'Button Cuff', is_active: true, is_global: false, reference_images: [] },
  { id: 'style-4', option_group: 'group-2', tenant: null, code: 'round-cuff', name: 'Round Cuff', is_active: true, is_global: true, reference_images: [] },
  { id: 'style-5', option_group: 'group-2', tenant: null, code: 'barrel-cuff', name: 'Barrel Cuff', is_active: true, is_global: true, reference_images: [] },
]

function openEditor(initialDesign = design) {
  api.getShopDesign.mockResolvedValue(initialDesign)
  render(<MemoryRouter initialEntries={['/designs/design-1']}><Routes><Route path="/designs/:designId" element={<DesignEditor />} /></Routes></MemoryRouter>)
}

describe('DesignEditor guided style selection', () => {
  beforeEach(() => {
    vi.stubGlobal('IntersectionObserver', undefined)
    api.getShopDesign.mockResolvedValue(design)
    api.getShopFamilyOptionGroups.mockResolvedValue(familyGroups)
    api.getAllShopStyleOptions.mockResolvedValue(styleOptions)
    api.addShopDesignSelection.mockResolvedValue({})
    api.updateShopDesignSelection.mockResolvedValue({})
    api.publishShopDesignVersion.mockResolvedValue({})
    api.uploadShopDesignReferences.mockResolvedValue([])
    api.usePrivateImage.mockImplementation((url: string | null) => ({ objectUrl: url ? 'blob:curve-collar' : null, isLoading: false, error: null }))
  })

  afterEach(() => { cleanup(); vi.clearAllMocks(); vi.unstubAllGlobals() })

  it('loads ordered group config and shows saved option thumbnails with a compact preview', async () => {
    openEditor()
    expect(await screen.findByText('Curve Collar')).toBeInTheDocument()
    await waitFor(() => expect(document.querySelectorAll('.design-selection-list .design-option-thumbnail img')).toHaveLength(1))

    fireEvent.click(screen.getByRole('button', { name: /Add selection/ }))
    expect(await screen.findByRole('heading', { name: 'Add style selection' })).toBeInTheDocument()
    expect(screen.getByText('Step 1 of 2 · Collar')).toBeInTheDocument()
    expect(screen.getByRole('radio', { name: /Band Collar/ })).toBeDisabled()
    expect(screen.getByRole('heading', { name: 'Design preview' })).toBeInTheDocument()
    expect(api.getShopFamilyOptionGroups).toHaveBeenCalledWith('shop-1', 'shirt')
    fireEvent.click(screen.getByRole('button', { name: 'Continue' }))
    expect(await screen.findByText('Step 2 of 2 · Cuff')).toBeInTheDocument()
    expect(screen.getByRole('checkbox', { name: /Button Cuff/ })).toBeInTheDocument()
    expect(screen.getByRole('checkbox', { name: /Round Cuff/ })).toBeInTheDocument()
    expect(document.querySelector('.design-choice-option .design-option-thumbnail svg')).toBeInTheDocument()
  })

  it('selects multiple multi-group options, revises on back, previews them, and writes only at final confirmation', async () => {
    openEditor(emptyDesign)
    fireEvent.click(await screen.findByRole('button', { name: /Add selection/ }))
    fireEvent.click(screen.getByRole('radio', { name: /Band Collar/ }))
    const bandCollarCard = screen.getByRole('radio', { name: /Band Collar/ }).closest('label')!
    fireEvent.pointerDown(bandCollarCard, { pointerType: 'mouse', button: 0, isPrimary: true })
    fireEvent.pointerDown(bandCollarCard, { pointerType: 'mouse', button: 0, isPrimary: true })
    expect(await screen.findByText('Step 2 of 2 · Cuff')).toBeInTheDocument()
    fireEvent.click(screen.getByRole('button', { name: 'Back' }))
    expect(screen.getByRole('radio', { name: /Band Collar/ })).toBeChecked()
    fireEvent.click(screen.getByRole('button', { name: 'Continue' }))

    fireEvent.click(await screen.findByRole('checkbox', { name: /Button Cuff/ }))
    fireEvent.click(screen.getByRole('checkbox', { name: /Round Cuff/ }))
    expect(screen.getAllByText('Button Cuff').length).toBeGreaterThan(1)
    expect(screen.getAllByText('Round Cuff').length).toBeGreaterThan(1)
    expect(api.addShopDesignSelection).not.toHaveBeenCalled()
    fireEvent.click(screen.getByRole('button', { name: 'Review selections' }))
    expect(await screen.findByRole('heading', { name: 'Review selections' })).toBeInTheDocument()
    fireEvent.click(screen.getByRole('button', { name: 'Add 3 selections' }))
    await waitFor(() => expect(api.addShopDesignSelection).toHaveBeenCalledTimes(3))
    expect(api.addShopDesignSelection).toHaveBeenNthCalledWith(1, 'shop-1', 'version-1', { style_option_id: 'style-2' })
    expect(api.addShopDesignSelection).toHaveBeenNthCalledWith(2, 'shop-1', 'version-1', { style_option_id: 'style-3' })
    expect(api.addShopDesignSelection).toHaveBeenNthCalledWith(3, 'shop-1', 'version-1', { style_option_id: 'style-4' })
  })

  it('double taps a multi-select option after retaining earlier choices and advances with the full draft', async () => {
    openEditor(emptyDesign)
    fireEvent.click(await screen.findByRole('button', { name: /Add selection/ }))
    fireEvent.click(screen.getByRole('radio', { name: /Band Collar/ }))
    fireEvent.click(screen.getByRole('button', { name: 'Continue' }))

    fireEvent.click(await screen.findByRole('checkbox', { name: /Button Cuff/ }))
    fireEvent.click(screen.getByRole('checkbox', { name: /Round Cuff/ }))
    const barrelCuff = screen.getByRole('checkbox', { name: /Barrel Cuff/ })
    const barrelCuffCard = barrelCuff.closest('label')!
    fireEvent.pointerDown(barrelCuffCard, { pointerType: 'touch', button: 0, isPrimary: true })
    fireEvent.click(barrelCuff)
    fireEvent.pointerDown(barrelCuffCard, { pointerType: 'touch', button: 0, isPrimary: true })

    expect(await screen.findByRole('heading', { name: 'Review selections' })).toBeInTheDocument()
    expect(screen.getAllByText('Button Cuff').length).toBeGreaterThan(1)
    expect(screen.getAllByText('Round Cuff').length).toBeGreaterThan(1)
    expect(screen.getAllByText('Barrel Cuff').length).toBeGreaterThan(1)
    expect(api.addShopDesignSelection).not.toHaveBeenCalled()
  })

  it('enforces required groups and allows optional groups to be skipped', async () => {
    openEditor(emptyDesign)
    fireEvent.click(await screen.findByRole('button', { name: /Add selection/ }))
    expect(screen.getByRole('button', { name: 'Choose a required option' })).toBeDisabled()
    fireEvent.click(screen.getByRole('radio', { name: /Band Collar/ }))
    fireEvent.click(screen.getByRole('button', { name: 'Continue' }))
    expect(await screen.findByText('Step 2 of 2 · Cuff')).toBeInTheDocument()
    fireEvent.click(screen.getByRole('button', { name: 'Skip group' }))
    expect(await screen.findByRole('heading', { name: 'Review selections' })).toBeInTheDocument()
    fireEvent.click(screen.getByRole('button', { name: 'Add 1 selection' }))
    await waitFor(() => expect(api.addShopDesignSelection).toHaveBeenCalledTimes(1))
    expect(api.addShopDesignSelection).toHaveBeenCalledWith('shop-1', 'version-1', { style_option_id: 'style-2' })
  })

  it('edits an existing option and keeps the single-selection update contract', async () => {
    openEditor()
    fireEvent.click(await screen.findByRole('button', { name: 'Edit' }))
    expect(await screen.findByRole('heading', { name: 'Edit Collar selection' })).toBeInTheDocument()
    expect(screen.getByRole('radio', { name: /Curve Collar/ })).toBeChecked()
    fireEvent.click(screen.getByRole('radio', { name: /Band Collar/ }))
    fireEvent.click(screen.getByRole('button', { name: 'Review selections' }))
    expect(await screen.findByRole('button', { name: 'Save selection' })).toBeInTheDocument()
    fireEvent.click(screen.getByRole('button', { name: 'Save selection' }))
    await waitFor(() => expect(api.updateShopDesignSelection).toHaveBeenCalledWith('shop-1', 'version-1', 'selection-1', { style_option_id: 'style-2' }))
    expect(api.addShopDesignSelection).not.toHaveBeenCalled()
  })

  it('keeps cancellation local and resets unconfirmed selections when reopened', async () => {
    openEditor(emptyDesign)
    fireEvent.click(await screen.findByRole('button', { name: /Add selection/ }))
    fireEvent.click(screen.getByRole('radio', { name: /Band Collar/ }))
    fireEvent.click(screen.getByRole('button', { name: 'Cancel' }))
    expect(api.addShopDesignSelection).not.toHaveBeenCalled()
    fireEvent.click(screen.getByRole('button', { name: /Add selection/ }))
    expect(await screen.findByRole('radio', { name: /Band Collar/ })).not.toBeChecked()
  })

  it('keeps group choices and progression controls usable at a narrow viewport', async () => {
    Object.defineProperty(window, 'innerWidth', { configurable: true, value: 390 })
    openEditor(emptyDesign)
    fireEvent.click(await screen.findByRole('button', { name: /Add selection/ }))
    expect(document.querySelector('.design-guided-dialog')).toBeInTheDocument()
    expect(screen.getByRole('radio', { name: /Band Collar/ })).toBeVisible()
    fireEvent.click(screen.getByRole('radio', { name: /Band Collar/ }))
    fireEvent.click(screen.getByRole('button', { name: 'Continue' }))
    expect(await screen.findByText('Step 2 of 2 · Cuff')).toBeVisible()
    expect(screen.getByRole('button', { name: 'Back' })).toBeVisible()
  })
})
