import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { cleanup, fireEvent, render, screen, waitFor, within } from '@testing-library/react'
import { MemoryRouter, Route, Routes } from 'react-router-dom'
import { GlobalDesignTemplatesPage } from './GlobalDesignTemplatesPage'

const api = vi.hoisted(() => ({
  archiveGlobalDesign: vi.fn(), createGlobalDesign: vi.fn(), getAllGlobalDesigns: vi.fn(),
  getAllFamilies: vi.fn(), getAllGlobalVariants: vi.fn(),
}))

vi.mock('./api', () => ({
  archiveGlobalDesign: api.archiveGlobalDesign,
  createGlobalDesign: api.createGlobalDesign,
  getAllGlobalDesigns: api.getAllGlobalDesigns,
}))
vi.mock('../../features/catalog/api', () => ({
  getAllFamilies: api.getAllFamilies,
  getAllGlobalVariants: api.getAllGlobalVariants,
}))

const templates = [{
  id: 'template-1', tenant: null, family: 'family-shirt', variant: 'variant-shirt',
  name: 'Published Shirt', status: 'ACTIVE', is_default_seeded: false,
  latest_version: { id: 'version-1', number: 1, name: 'Published Shirt', translations: [], status: 'PUBLISHED', published_at: null, selections: [], references: [] },
  created_at: '', updated_at: '',
}]

function renderPage() {
  return render(<MemoryRouter initialEntries={['/backoffice/designs']}><Routes>
    <Route path="/backoffice/designs" element={<GlobalDesignTemplatesPage />} />
    <Route path="/backoffice/designs/:designId" element={<div>Template editor route</div>} />
  </Routes></MemoryRouter>)
}

describe('Back Office Global Design Templates', () => {
  beforeEach(() => {
    api.getAllGlobalDesigns.mockResolvedValue(templates)
    api.getAllFamilies.mockResolvedValue([
      { id: 'family-shirt', name: 'Men’s Shirt', code: 'mens-shirt', status: 'ACTIVE', tenant: null },
      { id: 'family-abaya', name: 'Abaya', code: 'abaya', status: 'ACTIVE', tenant: null },
    ])
    api.getAllGlobalVariants.mockImplementation(async (familyId: string) => familyId === 'family-shirt'
      ? [
        { id: 'variant-shirt', family: 'family-shirt', name: 'Standard Shirt', code: 'standard', is_default: true, is_global: true, is_active: true },
        { id: 'variant-abaya', family: 'family-abaya', name: 'Long Dress', code: 'long-dress', is_default: false, is_global: true, is_active: true },
      ]
      : [])
    api.createGlobalDesign.mockResolvedValue({ id: 'new-template' })
  })

  afterEach(() => { cleanup(); vi.clearAllMocks() })

  it('loads existing templates and offers authoritative global family/variant data for creation', async () => {
    renderPage()
    expect(await screen.findByText('Published Shirt')).toBeTruthy()
    fireEvent.click(screen.getByRole('button', { name: /New Global Design/i }))

    const familySelect = await screen.findByLabelText('Garment family')
    await waitFor(() => expect(api.getAllGlobalVariants).toHaveBeenCalledWith('family-shirt'))
    expect(within(familySelect).getByRole('option', { name: 'Men’s Shirt' })).toBeTruthy()
    const variantSelect = screen.getByLabelText(/Variant \(optional\)/)
    expect(within(variantSelect).getByRole('option', { name: 'Standard Shirt (standard)' })).toBeTruthy()
    expect(within(variantSelect).queryByRole('option', { name: 'Long Dress (long-dress)' })).toBeNull()

    fireEvent.change(screen.getByLabelText('Design name'), { target: { value: 'Formal Shirt' } })
    fireEvent.change(variantSelect, { target: { value: 'variant-shirt' } })
    fireEvent.click(screen.getByRole('button', { name: 'Create draft' }))

    await waitFor(() => expect(api.createGlobalDesign).toHaveBeenCalledWith({
      family_id: 'family-shirt', variant_id: 'variant-shirt', name: 'Formal Shirt',
    }))
    expect(await screen.findByText('Template editor route')).toBeTruthy()
  })

  it('uses family-level scope when no variant is selected', async () => {
    renderPage()
    fireEvent.click(await screen.findByRole('button', { name: /New Global Design/i }))
    await screen.findByLabelText('Design name')
    fireEvent.change(screen.getByLabelText('Design name'), { target: { value: 'Family design' } })
    await waitFor(() => expect(screen.getByRole('button', { name: 'Create draft' })).toHaveProperty('disabled', false))
    fireEvent.click(screen.getByRole('button', { name: 'Create draft' }))
    await waitFor(() => expect(api.createGlobalDesign).toHaveBeenCalledWith({
      family_id: 'family-shirt', variant_id: null, name: 'Family design',
    }))
  })

  it('keeps creation unavailable when no active global family exists', async () => {
    api.getAllFamilies.mockResolvedValue([])
    renderPage()
    fireEvent.click(await screen.findByRole('button', { name: /New Global Design/i }))
    expect(await screen.findByText(/No active global garment families/)).toBeTruthy()
    expect(screen.getByRole('button', { name: 'Create draft' })).toHaveProperty('disabled', true)
  })
})
