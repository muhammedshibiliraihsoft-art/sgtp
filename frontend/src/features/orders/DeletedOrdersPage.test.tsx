import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { cleanup, fireEvent, render, screen, waitFor } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { DeletedOrdersPage } from './DeletedOrdersPage'
import i18n from '../../i18n'

const mock = vi.hoisted(() => ({
  context: { shopId: 'shop-1', role: 'ADMIN' as 'ADMIN' | 'STAFF', isLoading: false },
  deletedList: vi.fn(),
}))
vi.mock('../../hooks/useCurrentShop', () => ({ useCurrentShop: () => mock.context }))
vi.mock('./api', () => ({ ordersApi: { deletedList: mock.deletedList } }))

const record = {
  id: 'work-1', work_number: 'ORD-000001', client_name: 'Amina', design_name: 'Classic Abaya',
  status: 'REQUEST', priority: 'NORMAL', due_date: null, created_at: '2026-10-15T08:00:00Z',
  deleted: '2026-10-18T08:00:00Z', deleted_date: '2026-10-18',
}

function page() {
  return render(<MemoryRouter><DeletedOrdersPage /></MemoryRouter>)
}

describe('Deleted Orders page', () => {
  beforeEach(async () => {
    await i18n.changeLanguage('en')
    mock.context = { shopId: 'shop-1', role: 'ADMIN', isLoading: false }
    mock.deletedList.mockResolvedValue({ count: 1, next: null, previous: null, results: [record] })
  })
  afterEach(() => { cleanup(); vi.clearAllMocks() })

  it('shows only read-only archive records with the Shop-local deleted date', async () => {
    page()
    expect(await screen.findByText('ORD-000001')).toBeInTheDocument()
    expect(screen.getByText('Classic Abaya')).toBeInTheDocument()
    expect(screen.getByText('2026-10-18')).toBeInTheDocument()
    expect(screen.queryByRole('button', { name: /restore|delete permanently/i })).not.toBeInTheDocument()
    expect(mock.deletedList).toHaveBeenCalledWith('shop-1', { page: 1, search: '', deletedFrom: '', deletedTo: '' })
  })

  it('applies an explicit deleted-date range to the API', async () => {
    page()
    await screen.findByText('ORD-000001')
    fireEvent.change(screen.getByLabelText('Deleted from'), { target: { value: '2026-10-17' } })
    fireEvent.change(screen.getByLabelText('Deleted to'), { target: { value: '2026-10-18' } })
    fireEvent.click(screen.getByRole('button', { name: 'Apply filters' }))
    await waitFor(() => expect(mock.deletedList).toHaveBeenCalledWith('shop-1', { page: 1, search: '', deletedFrom: '2026-10-17', deletedTo: '2026-10-18' }))
  })

  it('does not call the archive API for non-admin staff', () => {
    mock.context.role = 'STAFF'
    page()
    expect(screen.getByRole('alert')).toHaveTextContent('Only a Shop Admin')
    expect(mock.deletedList).not.toHaveBeenCalled()
  })
})
