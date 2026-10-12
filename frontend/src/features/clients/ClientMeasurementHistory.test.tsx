import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { cleanup, fireEvent, render, screen, waitFor } from '@testing-library/react'

const mocks = vi.hoisted(() => ({
  profiles: vi.fn(), setsPage: vi.fn(), setDetail: vi.fn(), copySet: vi.fn(), deleteSet: vi.fn(),
  compare: vi.fn(), exportWorksheet: vi.fn(), getFamilyDetail: vi.fn(), getAllShopVariants: vi.fn(),
}))

vi.mock('react-i18next', () => ({ useTranslation: () => ({ t: (key: string) => key }) }))
vi.mock('../measurements/api', () => ({ measurementApi: {
  profiles: mocks.profiles, setsPage: mocks.setsPage, setDetail: mocks.setDetail,
  copySet: mocks.copySet, deleteSet: mocks.deleteSet, compare: mocks.compare, exportWorksheet: mocks.exportWorksheet,
} }))
vi.mock('../catalog/api', () => ({ getFamilyDetail: mocks.getFamilyDetail, getAllShopVariants: mocks.getAllShopVariants }))

import { ClientMeasurementHistory } from './ClientMeasurementHistory'

const profile = { id: 'profile-1', client: 'client-1', related_person: null, family: 'family-1', variant: null, created_at: '2026-01-01T00:00:00Z' }
const set = { id: 'set-1', profile: profile.id, version: 3, copied_from: null, is_active: true, created_at: '2026-02-01T00:00:00Z', values: [] }

describe('Client measurement history workspace', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    vi.mocked(mocks.profiles).mockResolvedValue([profile])
    vi.mocked(mocks.setsPage).mockResolvedValue({ count: 1, next: null, previous: null, results: [set] })
    vi.mocked(mocks.setDetail).mockResolvedValue({ ...set, values: [{ id: 'value-1', definition: 'def-1', definition_code_snapshot: 'CHEST', label_snapshot: 'Chest', label: 'Chest', translations: {}, value: '98.5', unit: 'CM' }] })
    vi.mocked(mocks.copySet).mockResolvedValue({ ...set, id: 'set-copy', version: 4, copied_from: set.id })
    vi.mocked(mocks.deleteSet).mockResolvedValue(undefined)
    vi.mocked(mocks.getFamilyDetail).mockResolvedValue({ id: 'family-1', name: 'Shirt', code: 'shirt', translations: [], option_groups: [] })
    vi.mocked(mocks.getAllShopVariants).mockResolvedValue([])
    vi.stubGlobal('confirm', vi.fn(() => true))
  })
  afterEach(() => { cleanup(); vi.unstubAllGlobals() })

  it('loads profile cards first, then lazily pages and opens an immutable version by its exact id', async () => {
    render(<ClientMeasurementHistory shopId="shop-1" clientId="client-1" locale="en" />)

    await screen.findByRole('button', { name: /measurements\.profile/ })
    expect(mocks.profiles).toHaveBeenCalledWith('shop-1', 'client-1', { kind: 'client' })
    expect(mocks.setsPage).not.toHaveBeenCalled()

    fireEvent.click(screen.getByRole('button', { name: /measurements\.profile/ }))
    await screen.findByText('Shirt')
    await screen.findByText('clients.latestMeasurement')
    expect(mocks.setsPage).toHaveBeenCalledWith('shop-1', 'client-1', { kind: 'client' }, 'profile-1', 1)

    fireEvent.click(screen.getByRole('button', { name: /measurements\.version/ }))
    expect(await screen.findByText('98.5 CM')).toBeInTheDocument()
    expect(mocks.setDetail).toHaveBeenCalledWith('shop-1', 'client-1', { kind: 'client' }, 'profile-1', 'set-1')
    expect(screen.getByText('clients.measurementVersionDetail')).toBeInTheDocument()
  })

  it('confirms copies and refreshes from the authoritative new version response', async () => {
    render(<ClientMeasurementHistory shopId="shop-1" clientId="client-1" locale="en" />)
    await screen.findByRole('button', { name: /measurements\.profile/ })
    fireEvent.click(screen.getByRole('button', { name: /measurements\.profile/ }))
    await screen.findByText('Shirt')
    await screen.findByText('clients.latestMeasurement')
    fireEvent.click(screen.getByRole('button', { name: 'measurements.copyVersion' }))

    await waitFor(() => expect(mocks.copySet).toHaveBeenCalledWith('shop-1', 'client-1', { kind: 'client' }, 'profile-1', 'set-1'))
    await waitFor(() => expect(mocks.setsPage).toHaveBeenCalledTimes(2))
    expect(window.confirm).toHaveBeenCalled()
  })

  it('protects the final version and confirms deletion when another active version exists', async () => {
    const older = { ...set, id: 'set-older', version: 2 }
    vi.mocked(mocks.setsPage)
      .mockResolvedValueOnce({ count: 2, next: null, previous: null, results: [set, older] })
      .mockResolvedValueOnce({ count: 1, next: null, previous: null, results: [older] })
    render(<ClientMeasurementHistory shopId="shop-1" clientId="client-1" locale="en" />)
    await screen.findByRole('button', { name: /measurements\.profile/ })
    fireEvent.click(screen.getByRole('button', { name: /measurements\.profile/ }))
    await screen.findByText('clients.latestMeasurement')
    const deleteButtons = screen.getAllByRole('button', { name: 'measurements.deleteVersion' })
    fireEvent.click(deleteButtons[0])
    await waitFor(() => expect(mocks.deleteSet).toHaveBeenCalledWith('shop-1', 'client-1', { kind: 'client' }, 'profile-1', 'set-1'))
    expect(window.confirm).toHaveBeenCalled()
    await waitFor(() => expect(mocks.setsPage).toHaveBeenCalledTimes(2))
  })

  it('disables delete when only one active version remains', async () => {
    render(<ClientMeasurementHistory shopId="shop-1" clientId="client-1" locale="en" />)
    await screen.findByRole('button', { name: /measurements\.profile/ })
    fireEvent.click(screen.getByRole('button', { name: /measurements\.profile/ }))
    expect(await screen.findByRole('button', { name: 'measurements.lastVersionProtected' })).toBeDisabled()
    expect(mocks.deleteSet).not.toHaveBeenCalled()
  })
})
