import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { cleanup, fireEvent, render, screen, waitFor } from '@testing-library/react'
import { MemoryRouter, Route, Routes } from 'react-router-dom'
import { GlobalTemplateEditor } from './GlobalTemplateEditor'

const api = vi.hoisted(() => ({
  addGlobalDesignSelection: vi.fn(), getGlobalDesign: vi.fn(), getGlobalDesignReferences: vi.fn(),
  publishGlobalDesignVersion: vi.fn(), uploadGlobalDesignReferences: vi.fn(),
  getAllGlobalStyleOptions: vi.fn(), getOptionGroups: vi.fn(), uploadGlobalStyleOptionImages: vi.fn(),
}))

vi.mock('./api', () => ({
  addGlobalDesignSelection: api.addGlobalDesignSelection,
  getGlobalDesign: api.getGlobalDesign,
  getGlobalDesignReferences: api.getGlobalDesignReferences,
  publishGlobalDesignVersion: api.publishGlobalDesignVersion,
  uploadGlobalDesignReferences: api.uploadGlobalDesignReferences,
}))
vi.mock('../../features/catalog/api', () => ({
  getAllGlobalStyleOptions: api.getAllGlobalStyleOptions,
  getOptionGroups: api.getOptionGroups,
  uploadGlobalStyleOptionImages: api.uploadGlobalStyleOptionImages,
}))
vi.mock('../../hooks/usePrivateImage', () => ({ usePrivateImage: () => ({ objectUrl: null, isLoading: false, error: null }) }))

const selection = {
  id: 'selection-1', option_group: 'group-1', style_option: 'style-1', selected_code: 'band-collar',
  selected_name_en: 'Band Collar', style_option_name: 'Band Collar', style_option_translations: [], style_option_images: [],
}
const design = {
  id: 'design-1', tenant: null, family: 'shirt', variant: '', name: 'Shirt template', status: 'ACTIVE',
  created_at: '', updated_at: '', latest_version: {
    id: 'version-1', number: 1, name: 'Shirt template', translations: [], status: 'DRAFT', published_at: null,
    selections: [selection], references: [],
  },
}

describe('Global template reusable style references', () => {
  beforeEach(() => {
    api.getGlobalDesign.mockResolvedValue(design)
    api.getOptionGroups.mockResolvedValue([{ id: 'group-1', name: 'Collar', code: 'collar', families: ['shirt'] }])
    api.getAllGlobalStyleOptions.mockResolvedValue([{ id: 'style-1', option_group: 'group-1', tenant: null, code: 'band-collar', name: 'Band Collar', is_active: true, is_global: true, reference_images: [] }])
    api.uploadGlobalStyleOptionImages.mockResolvedValue([])
  })

  afterEach(() => { cleanup(); vi.clearAllMocks() })

  it('uploads a reusable Style Option image from the Design template page', async () => {
    render(<MemoryRouter initialEntries={['/templates/design-1']}><Routes><Route path="/templates/:designId" element={<GlobalTemplateEditor />} /></Routes></MemoryRouter>)
    const file = new File(['image'], 'band-collar.jpg', { type: 'image/jpeg' })
    fireEvent.change(await screen.findByLabelText('Add or replace reusable image for Band Collar'), { target: { files: [file] } })
    await waitFor(() => expect(api.uploadGlobalStyleOptionImages).toHaveBeenCalledWith('style-1', [file]))
    expect(api.getAllGlobalStyleOptions).toHaveBeenCalledTimes(2)
  })
})
