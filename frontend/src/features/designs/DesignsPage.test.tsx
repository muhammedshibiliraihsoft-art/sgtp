import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { cleanup, fireEvent, render, screen, waitFor, within } from '@testing-library/react'
import { MemoryRouter, Route, Routes, useLocation, useNavigate } from 'react-router-dom'
import { DesignsPage } from './DesignsPage'
import type { Design } from './types'

const api = vi.hoisted(() => ({
  archiveShopDesign: vi.fn(),
  createShopDesign: vi.fn(),
  getAllShopDesigns: vi.fn(),
  createShopFamily: vi.fn(),
  getAllShopFamilies: vi.fn(),
  role: 'ADMIN' as 'ADMIN' | 'STAFF' | 'VIEWER',
}))

vi.mock('./api', () => ({
  archiveShopDesign: api.archiveShopDesign,
  createShopDesign: api.createShopDesign,
  getAllShopDesigns: api.getAllShopDesigns,
}))
vi.mock('../catalog/api', () => ({
  createShopFamily: api.createShopFamily,
  getAllShopFamilies: api.getAllShopFamilies,
}))
vi.mock('../../hooks/useCurrentShop', () => ({
  useCurrentShop: () => ({ shopId: 'shop-1', role: api.role, isLoading: false }),
}))

const families = [
  { id: 'family-1', name: 'Men’s Shirt', code: 'mens-shirt' },
  { id: 'family-2', name: 'Abaya', code: 'abaya' },
  { id: 'family-3', name: 'Darraa', code: 'darraa' },
  { id: 'family-4', name: 'Dishga', code: 'dishga' },
  { id: 'family-5', name: 'Coat', code: 'coat' },
  { id: 'family-6', name: 'Trousers', code: 'trousers' },
]
function makeDesign(id: string, family: string, variant: string | null, name: string, status: Design['status'] = 'ACTIVE', versionStatus: 'DRAFT' | 'PUBLISHED' | 'ARCHIVED' = 'DRAFT'): Design {
  return {
    id, tenant: 'shop-1', family, variant, name, status,
    latest_version: { id: `version-${id}`, number: 6, name, translations: [], status: versionStatus, published_at: null, selections: [], references: [] },
    created_at: '', updated_at: '',
  }
}

function renderPage(initialEntries: string[] = ['/designs']) {
  return render(<MemoryRouter initialEntries={initialEntries}><DesignsPage /></MemoryRouter>)
}

function CatalogHandoffRoute() {
  const location = useLocation()
  const navigate = useNavigate()
  const state = location.state as { returnToDesignDraft?: { designName: string; familyId: string } } | null
  return <div><span>Catalog family {new URLSearchParams(location.search).get('family')}</span><button type="button" onClick={() => navigate('/designs?family=family-new', { state: { resumeDesignDraft: state?.returnToDesignDraft } })}>Return draft</button></div>
}

describe('DesignsPage inline garment creation', () => {
  beforeEach(() => {
    api.role = 'ADMIN'
    api.archiveShopDesign.mockResolvedValue({})
    api.createShopDesign.mockResolvedValue({})
    api.getAllShopDesigns.mockResolvedValue([])
    api.getAllShopFamilies.mockResolvedValue(families)
    api.createShopFamily.mockResolvedValue({ id: 'family-new', name: 'Evening Coat', code: 'evening-coat', tenant: 'shop-1' })
  })

  afterEach(() => {
    cleanup()
    vi.clearAllMocks()
    vi.restoreAllMocks()
  })

  it('shows only data-driven Shop Garment Family cards at the top level, including Garments with zero Designs', async () => {
    renderPage()

    for (const family of families) expect(await screen.findByRole('button', { name: family.name })).toBeInTheDocument()
    expect(screen.queryByRole('link', { name: /Design/ })).not.toBeInTheDocument()
    expect(screen.queryByRole('button', { name: /Archive/ })).not.toBeInTheDocument()
    expect(api.getAllShopFamilies).toHaveBeenCalledWith('shop-1')
    expect(api.getAllShopDesigns).not.toHaveBeenCalled()
  })

  it('opens a Garment-specific view with only that Family’s Designs and Family details on each card', async () => {
    api.getAllShopDesigns.mockResolvedValueOnce([
      makeDesign('shirt-a', 'family-1', 'variant-1', 'Shirt Design A'),
      makeDesign('shirt-b', 'family-1', 'variant-1', 'Shirt Design B'),
      makeDesign('shirt-family', 'family-1', null, 'Family-level Shirt Design'),
      makeDesign('abaya-a', 'family-2', 'variant-2', 'Abaya Design A'),
    ])
    renderPage()
    fireEvent.click(await screen.findByRole('button', { name: 'Men’s Shirt' }))

    expect(await screen.findByRole('heading', { name: 'Men’s Shirt' })).toBeInTheDocument()
    expect(screen.getByText('Manage designs for this garment')).toBeInTheDocument()
    expect(screen.getByRole('link', { name: 'Shirt Design A' })).toHaveAttribute('href', '/designs/shirt-a')
    expect(screen.getByRole('link', { name: 'Shirt Design B' })).toBeInTheDocument()
    expect(screen.getByRole('link', { name: 'Family-level Shirt Design' })).toBeInTheDocument()
    expect(screen.getByRole('link', { name: 'Shirt Design A' }).closest('article')).toHaveTextContent('Men’s Shirt')
    expect(screen.getByRole('link', { name: 'Family-level Shirt Design' }).closest('article')).toHaveTextContent('Men’s Shirt')
    expect(screen.queryByRole('link', { name: 'Abaya Design A' })).not.toBeInTheDocument()
    expect(api.getAllShopDesigns).toHaveBeenCalledWith('shop-1', { family: 'family-1' })

    fireEvent.click(screen.getByRole('button', { name: 'Designs' }))
    expect(await screen.findByRole('button', { name: 'Abaya' })).toBeInTheDocument()
    expect(screen.queryByRole('link', { name: /Shirt Design/ })).not.toBeInTheDocument()
    expect(api.getAllShopDesigns).toHaveBeenCalledTimes(1)
  })

  it('restores a Garment-specific Design view directly from its refresh-safe Family query', async () => {
    api.getAllShopDesigns.mockResolvedValueOnce([makeDesign('abaya-a', 'family-2', 'variant-2', 'Abaya Design A')])
    renderPage(['/designs?family=family-2'])

    expect(await screen.findByRole('heading', { name: 'Abaya' })).toBeInTheDocument()
    expect(await screen.findByRole('link', { name: 'Abaya Design A' })).toBeInTheDocument()
    expect(screen.queryByRole('button', { name: 'Men’s Shirt' })).not.toBeInTheDocument()
    expect(api.getAllShopDesigns).toHaveBeenCalledWith('shop-1', { family: 'family-2' })
  })

  it('creates a Design in the selected Garment context and shows it after the existing refresh', async () => {
    const created = makeDesign('shirt-new', 'family-1', 'variant-1', 'New Shirt Design')
    api.getAllShopDesigns.mockResolvedValueOnce([]).mockResolvedValueOnce([created])
    renderPage(['/designs?family=family-1'])
    fireEvent.click(await screen.findByRole('button', { name: 'New Design' }))
    expect(screen.getByRole('heading', { name: 'Men’s Shirt' })).toBeInTheDocument()
    fireEvent.change(screen.getByLabelText('Design name'), { target: { value: 'New Shirt Design' } })
    fireEvent.click(screen.getByRole('button', { name: 'Create' }))

    await waitFor(() => expect(api.createShopDesign).toHaveBeenCalledWith('shop-1', {
      family_id: 'family-1', name: 'New Shirt Design',
    }))
    expect(await screen.findByRole('link', { name: 'New Shirt Design' })).toBeInTheDocument()
    expect(api.getAllShopDesigns).toHaveBeenCalledTimes(2)
    expect(api.getAllShopDesigns).toHaveBeenNthCalledWith(2, 'shop-1', { family: 'family-1' })
  })

  it('preserves Design open, status, version, and archive behavior inside a Garment view', async () => {
    api.getAllShopDesigns.mockResolvedValueOnce([makeDesign('published-shirt', 'family-1', 'variant-1', 'Published Shirt', 'ACTIVE', 'PUBLISHED')])
    const confirmSpy = vi.spyOn(window, 'confirm').mockReturnValue(true)
    renderPage(['/designs?family=family-1'])
    await screen.findByRole('heading', { name: 'Men’s Shirt' })
    const designLink = await screen.findByRole('link', { name: 'Published Shirt' })
    expect(designLink).toHaveAttribute('href', '/designs/published-shirt')
    expect(screen.getByText('ACTIVE')).toBeInTheDocument()
    expect(screen.getByText('Version 6 · published')).toBeInTheDocument()

    fireEvent.click(screen.getByRole('button', { name: 'Archive Published Shirt' }))
    await waitFor(() => expect(api.archiveShopDesign).toHaveBeenCalledWith('shop-1', 'published-shirt'))
    expect(screen.queryByRole('link', { name: 'Published Shirt' })).not.toBeInTheDocument()
    confirmSpy.mockRestore()
  })

  it('keeps the existing family More picker available and creates a Shop family inline, selecting it immediately', async () => {
    renderPage()
    fireEvent.click(await screen.findByRole('button', { name: 'New Design' }))
    expect(screen.getByRole('button', { name: 'Browse all 6 choices' })).toBeInTheDocument()
    fireEvent.click(screen.getByRole('button', { name: 'Browse all 6 choices' }))
    expect(await screen.findByRole('dialog', { name: 'Garment family' })).toBeInTheDocument()
    expect(within(screen.getByRole('dialog', { name: 'Garment family' })).getByRole('button', { name: 'Trousers' })).toBeInTheDocument()
    fireEvent.click(screen.getByRole('button', { name: 'Close choices' }))
    fireEvent.change(screen.getByLabelText('Design name'), { target: { value: 'Evening Coat Design' } })
    fireEvent.click(screen.getByRole('button', { name: 'Add garment' }))
    fireEvent.change(screen.getByLabelText('Garment name (English)'), { target: { value: 'Evening Coat' } })
    fireEvent.change(screen.getByLabelText('Code'), { target: { value: 'evening-coat' } })

    fireEvent.click(screen.getByRole('button', { name: 'Create garment' }))

    await waitFor(() => expect(api.createShopFamily).toHaveBeenCalledWith('shop-1', {
      code: 'evening-coat', translations: [{ locale: 'en', name: 'Evening Coat' }],
    }))
    expect(await screen.findByRole('button', { name: 'Evening Coat', pressed: true })).toBeInTheDocument()
    expect(screen.getByLabelText('Design name')).toHaveValue('Evening Coat Design')

    fireEvent.click(screen.getByRole('button', { name: 'Create' }))
    await waitFor(() => expect(api.createShopDesign).toHaveBeenCalledWith('shop-1', {
      family_id: 'family-new', name: 'Evening Coat Design',
    }))
  })

  it('creates a family-level Design from the selected garment', async () => {
    renderPage()
    fireEvent.click(await screen.findByRole('button', { name: 'New Design' }))
    fireEvent.change(screen.getByLabelText('Design name'), { target: { value: 'Classic Shirt' } })

    fireEvent.click(screen.getByRole('button', { name: 'Create' }))

    await waitFor(() => expect(api.createShopDesign).toHaveBeenCalledWith('shop-1', {
      family_id: 'family-1', name: 'Classic Shirt',
    }))
  })

  it('opens Catalog configuration for a newly created garment and restores the Design draft when returning', async () => {
    api.getAllShopFamilies.mockResolvedValue([...families, { id: 'family-new', name: 'Evening Coat', code: 'evening-coat', tenant: 'shop-1' }])
    render(<MemoryRouter initialEntries={['/designs']}><Routes><Route path="/designs" element={<DesignsPage />} /><Route path="/catalog" element={<CatalogHandoffRoute />} /></Routes></MemoryRouter>)
    fireEvent.click(await screen.findByRole('button', { name: 'New Design' }))
    fireEvent.change(screen.getByLabelText('Design name'), { target: { value: 'Saved Garment Draft' } })
    fireEvent.click(screen.getByRole('button', { name: 'Add garment' }))
    fireEvent.change(screen.getByLabelText('Garment name (English)'), { target: { value: 'Evening Coat' } })
    fireEvent.change(screen.getByLabelText('Code'), { target: { value: 'evening-coat' } })
    fireEvent.click(screen.getByRole('button', { name: 'Create garment' }))
    fireEvent.click(await screen.findByRole('button', { name: 'Configure garment' }))

    expect(await screen.findByText('Catalog family family-new')).toBeInTheDocument()
    fireEvent.click(screen.getByRole('button', { name: 'Return draft' }))
    expect(await screen.findByRole('heading', { name: 'Create design' })).toBeInTheDocument()
    expect(screen.getByLabelText('Design name')).toHaveValue('Saved Garment Draft')
    expect(screen.getByRole('button', { name: 'Evening Coat' })).toHaveAttribute('aria-pressed', 'true')
    expect(screen.getByRole('button', { name: 'Configure garment' })).toBeInTheDocument()
  })

  it('retains the open Design flow and entered values when garment creation fails', async () => {
    api.createShopFamily.mockRejectedValueOnce(new Error('This Shop garment family code is already in use.'))
    renderPage()
    fireEvent.click(await screen.findByRole('button', { name: 'New Design' }))
    fireEvent.change(screen.getByLabelText('Design name'), { target: { value: 'Saved Design Name' } })
    fireEvent.click(screen.getByRole('button', { name: 'Add garment' }))
    fireEvent.change(screen.getByLabelText('Garment name (English)'), { target: { value: 'Duplicate Coat' } })
    fireEvent.change(screen.getByLabelText('Code'), { target: { value: 'duplicate-coat' } })
    fireEvent.click(screen.getByRole('button', { name: 'Create garment' }))

    expect(await screen.findByRole('alert')).toHaveTextContent('This Shop garment family code is already in use.')
    expect(screen.getByRole('heading', { name: 'Create design' })).toBeInTheDocument()
    expect(screen.getByLabelText('Design name')).toHaveValue('Saved Design Name')
    expect(screen.getByLabelText('Garment name (English)')).toHaveValue('Duplicate Coat')
    expect(api.createShopDesign).not.toHaveBeenCalled()
  })

  it('preserves Staff access and hides Shop family creation from Viewers', async () => {
    api.role = 'STAFF'
    const { rerender } = renderPage()
    fireEvent.click(await screen.findByRole('button', { name: 'New Design' }))
    expect(screen.getByRole('button', { name: 'Add garment' })).toBeInTheDocument()
    fireEvent.click(screen.getByRole('button', { name: 'Cancel' }))

    api.role = 'VIEWER'
    rerender(<MemoryRouter><DesignsPage /></MemoryRouter>)
    fireEvent.click(await screen.findByRole('button', { name: 'New Design' }))
    expect(screen.queryByRole('button', { name: 'Add garment' })).not.toBeInTheDocument()
  })
})
