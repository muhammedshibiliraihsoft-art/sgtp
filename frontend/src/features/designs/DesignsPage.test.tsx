import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { cleanup, fireEvent, render, screen, waitFor } from '@testing-library/react'
import { MemoryRouter, Route, Routes } from 'react-router-dom'
import i18n from '../../i18n'
import { DesignsPage } from './DesignsPage'

const mocks = vi.hoisted(() => ({
  families: vi.fn(), variants: vi.fn(), designs: vi.fn(), create: vi.fn(), archive: vi.fn(), restore: vi.fn(),
}))

vi.mock('../../hooks/useCurrentShop', () => ({ useCurrentShop: () => ({ shopId: 'shop-1', isLoading: false }) }))
vi.mock('../catalog/api', () => ({ getAllShopGarmentFamilies: mocks.families, getAllShopVariants: mocks.variants }))
vi.mock('./api', () => ({ getAllShopDesigns: mocks.designs, createShopDesign: mocks.create, archiveShopDesign: mocks.archive, restoreShopDefaultDesign: mocks.restore }))

describe('Designs page family-level workflow', () => {
  beforeEach(async () => {
    await i18n.changeLanguage('en')
    mocks.families.mockResolvedValue([{ id: 'family-1', name: 'Custom Thobe', code: 'custom-thobe', tenant: 'shop-1' }])
    mocks.variants.mockResolvedValue([])
    mocks.designs.mockResolvedValue([])
    mocks.create.mockResolvedValue({ id: 'design-1' })
  })
  afterEach(() => { cleanup(); vi.clearAllMocks() })

  it('allows a design on a garment family without forcing a Variant', async () => {
    render(<MemoryRouter initialEntries={['/designs?family=family-1']}><Routes><Route path="/designs" element={<DesignsPage />} /></Routes></MemoryRouter>)
    fireEvent.click(await screen.findByRole('button', { name: 'New Design' }))
    fireEvent.change(screen.getByLabelText('Design name'), { target: { value: 'Classic Thobe' } })
    expect(screen.getByRole('combobox', { name: /Variant \(optional\)/ })).toHaveValue('')
    fireEvent.click(screen.getByRole('button', { name: 'Create' }))
    await waitFor(() => expect(mocks.create).toHaveBeenCalledWith('shop-1', {
      family_id: 'family-1', variant_id: null, name: 'Classic Thobe',
    }))
  })

  it('starts with garment families and opens only the selected family designs', async () => {
    const design = { id: 'design-1', tenant: 'shop-1', family: 'family-1', variant: null, name: 'Classic Thobe', status: 'ACTIVE', is_default_seeded: false, latest_version: { number: 1, status: 'DRAFT' }, created_at: '', updated_at: '' }
    const secondFamily = { id: 'family-2', name: 'Abaya', code: 'abaya', tenant: 'shop-1' }
    mocks.families.mockResolvedValue([
      { id: 'family-1', name: 'Men’s Shirt', code: 'mens-shirt', tenant: 'shop-1' },
      secondFamily,
    ])
    mocks.designs.mockImplementation((_shop: string, filters: { family?: string }) => Promise.resolve(!filters.family || filters.family === 'family-1' ? [design] : []))
    render(<MemoryRouter initialEntries={['/designs']}><Routes><Route path="/designs" element={<DesignsPage />} /></Routes></MemoryRouter>)
    expect(await screen.findByRole('button', { name: /Men’s Shirt.*1 design/i })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /Abaya.*0 designs/i })).toBeInTheDocument()
    expect(screen.queryByRole('button', { name: 'New Design' })).not.toBeInTheDocument()
    fireEvent.click(screen.getByRole('button', { name: /Men’s Shirt.*1 design/i }))
    expect(await screen.findByRole('link', { name: 'Classic Thobe' })).toBeInTheDocument()
    expect(screen.getByRole('heading', { name: 'Men’s Shirt' })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'New Design' })).toBeInTheDocument()
  })

  it('offers restore only for an archived default design', async () => {
    const archived = { id: 'seed-design', tenant: 'shop-1', family: 'family-1', variant: null, name: 'Default Thobe', status: 'ARCHIVED', is_default_seeded: true, latest_version: null, created_at: '', updated_at: '' }
    mocks.designs.mockImplementation((_shop: string, _filters: unknown, _locale: string, state: string) => Promise.resolve(state === 'ARCHIVED' ? [archived] : []))
    mocks.restore.mockResolvedValue({ ...archived, status: 'ACTIVE' })
    render(<MemoryRouter initialEntries={['/designs']}><Routes><Route path="/designs" element={<DesignsPage />} /></Routes></MemoryRouter>)
    fireEvent.click(await screen.findByRole('button', { name: 'Show archived designs' }))
    fireEvent.click(await screen.findByRole('button', { name: /Custom Thobe.*1 archived design/i }))
    fireEvent.click(await screen.findByRole('button', { name: 'Restore Default Thobe from latest default' }))
    await waitFor(() => expect(mocks.restore).toHaveBeenCalledWith('shop-1', 'seed-design'))
  })
})
