import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { cleanup, fireEvent, render, screen, waitFor } from '@testing-library/react'
import { MemoryRouter, Route, Routes } from 'react-router-dom'
import { DesignEditor } from './DesignEditor'

const mocks = vi.hoisted(() => ({
  familyGroups: vi.fn(), options: vi.fn(), design: vi.fn(), add: vi.fn(), update: vi.fn(),
  publish: vi.fn(), upload: vi.fn(),
}))

vi.mock('../../hooks/useCurrentShop', () => ({ useCurrentShop: () => ({ shopId: 'shop-1', role: 'ADMIN', isLoading: false }) }))
vi.mock('../../hooks/usePrivateImage', () => ({ usePrivateImage: () => ({ objectUrl: null, isLoading: false, error: null }) }))
vi.mock('../../services/useAuth', () => ({ useAuth: () => ({ user: { is_main_supplier_admin: false } }) }))
vi.mock('../catalog/api', () => ({ getShopFamilyOptionGroups: mocks.familyGroups, getAllShopStyleOptions: mocks.options }))
vi.mock('./api', () => ({
  addShopDesignSelection: mocks.add, getShopDesign: mocks.design,
  publishShopDesignVersion: mocks.publish, updateShopDesignDraft: vi.fn(),
  updateShopDesignSelection: mocks.update, uploadShopDesignReferences: mocks.upload,
}))

const group = { id: 'group-cuff', tenant: null, name: 'Cuff', code: 'cuff', families: ['family-shirt'], is_global: true }
const selection = {
  id: 'selection-1', option_group: group.id, style_option: 'option-1', selected_code: 'normal-cuff',
  selected_name_en: 'Normal Cuff', style_option_name: 'Normal Cuff', style_option_translations: [], style_option_images: [],
}
const design = {
  id: 'design-1', tenant: 'shop-1', family: 'family-shirt', variant: 'variant-shirt', name: 'Classic Formal Shirt',
  status: 'ACTIVE', is_default_seeded: false, created_at: '', updated_at: '',
  latest_version: { id: 'version-1', number: 1, name: 'Classic Formal Shirt', translations: [], status: 'DRAFT', published_at: null, selections: [selection], references: [] },
}
const options = [
  { id: 'option-1', tenant: null, option_group: group.id, code: 'normal-cuff', name: 'Normal Cuff', is_active: true, is_global: true, reference_images: [] },
  { id: 'option-2', tenant: null, option_group: group.id, code: 'open-cuff', name: 'Open Cuff', is_active: true, is_global: true, reference_images: [] },
]

describe('Shop Design editor catalog integration', () => {
  beforeEach(() => {
    mocks.familyGroups.mockResolvedValue([{ option_group: group, sort_order: 0, selection_mode: 'SINGLE', is_required: false }])
    mocks.options.mockResolvedValue(options)
    mocks.design.mockResolvedValue(design)
    mocks.update.mockResolvedValue({ ...selection, style_option: 'option-2', style_option_name: 'Open Cuff' })
  })
  afterEach(() => { cleanup(); vi.clearAllMocks() })

  function renderEditor() {
    return render(<MemoryRouter initialEntries={['/designs/design-1']}><Routes><Route path="/designs/:designId" element={<DesignEditor />} /></Routes></MemoryRouter>)
  }

  it('loads this garment’s configured parts and options from the shared Shop Catalog', async () => {
    renderEditor()
    expect(await screen.findByText('Normal Cuff')).toBeInTheDocument()
    expect(mocks.familyGroups).toHaveBeenCalledWith('shop-1', 'family-shirt')
    expect(mocks.options).toHaveBeenCalledWith('shop-1')
  })

  it('lets the user edit a Draft selection and persists the replacement', async () => {
    renderEditor()
    fireEvent.click(await screen.findByRole('button', { name: 'Edit' }))
    fireEvent.click(screen.getByRole('radio', { name: /Open Cuff/ }))
    fireEvent.click(screen.getByRole('button', { name: 'Save selection' }))
    await waitFor(() => expect(mocks.update).toHaveBeenCalledWith('shop-1', 'version-1', 'selection-1', { style_option_id: 'option-2' }))
  })
})
