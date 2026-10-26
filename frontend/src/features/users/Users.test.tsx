import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { cleanup, render, screen, fireEvent, waitFor, within } from '@testing-library/react'
import { BrowserRouter } from 'react-router-dom'
import { UsersPage } from './UsersPage'
import { usersApi } from './api'

// Mock i18n
vi.mock('react-i18next', () => ({
  useTranslation: () => ({
    t: (key: string, fallback: string) => fallback || key,
    i18n: { language: 'en' }
  })
}))

vi.mock('./api', () => ({ usersApi: { memberships: vi.fn(), stats: vi.fn(), createUser: vi.fn(), setRole: vi.fn(), deactivate: vi.fn(), reactivate: vi.fn(), remove: vi.fn(), functions: vi.fn(), setFunctions: vi.fn(), findCreatedMembership: vi.fn() } }))
vi.mock('../../hooks/useCurrentShop', () => ({ useCurrentShop: () => ({ shopId: 't1', role: 'ADMIN', isLoading: false }) }))

const mockStats = { user_count: 5, max_users: 15, is_at_user_limit: false }
const mockMembers = [
  {
    id: 'm1',
    tenant: 't1',
    tenant_name: 'Shop',
    user_code: 'USR-1',
    display_name: 'Admin User',
    user_email: 'admin@test.com',
    role: 'ADMIN',
    is_active: true,
    created_at: '2023-01-01T00:00:00Z',
    updated_at: '2023-01-01T00:00:00Z'
  },
  {
    id: 'm2',
    tenant: 't1',
    tenant_name: 'Shop',
    user_code: 'USR-2',
    display_name: 'Staff User',
    user_email: null,
    role: 'STAFF',
    is_active: true,
    created_at: '2023-01-01T00:00:00Z',
    updated_at: '2023-01-01T00:00:00Z'
  }
]

describe('UsersPage', () => {
  afterEach(cleanup)

  beforeEach(() => {
    vi.clearAllMocks()
    vi.mocked(usersApi.memberships).mockResolvedValue({ count: mockMembers.length, next: null, previous: null, results: mockMembers } as any)
    vi.mocked(usersApi.stats).mockResolvedValue(mockStats)
  })

  it('renders page and backend-aligned Membership fields', async () => {
    render(<BrowserRouter><UsersPage /></BrowserRouter>)
    await screen.findAllByText('Admin User') // Wait for data to load
    
    // Check fields
    expect(screen.getByText('Team')).toBeInTheDocument()
    expect(screen.getAllByText('USR-1').length).toBeGreaterThan(0)
    expect(screen.getAllByText('admin@test.com').length).toBeGreaterThan(0)
    
    expect(screen.getAllByText('Staff User').length).toBeGreaterThan(0)
    expect(screen.getAllByText('USR-2').length).toBeGreaterThan(0)
  })

  it('debounces member search and does not refetch Shop capacity for search changes', async () => {
    render(<BrowserRouter><UsersPage /></BrowserRouter>)
    await screen.findAllByText('Admin User')
    vi.mocked(usersApi.memberships).mockClear()
    vi.mocked(usersApi.stats).mockClear()
    const search = screen.getByPlaceholderText('Search by name or User ID')
    fireEvent.change(search, { target: { value: 'A' } })
    fireEvent.change(search, { target: { value: 'Ad' } })
    fireEvent.change(search, { target: { value: 'Admin' } })
    await waitFor(() => expect(usersApi.memberships).toHaveBeenCalledTimes(1))
    expect(usersApi.memberships).toHaveBeenCalledWith('t1', { search: 'Admin', role: 'ALL', active: 'ALL', page: 1 })
    expect(usersApi.stats).not.toHaveBeenCalled()
  })

  it('Shop Admin Create User exposes STAFF/VIEWER only and no Shop selector', async () => {
    render(<BrowserRouter><UsersPage /></BrowserRouter>)
    await screen.findAllByText('Admin User') // Wait for data to load
    
    const addButton = screen.getAllByRole('button', { name: /Add user/i })[0]
    fireEvent.click(addButton)
    
    // Check roles using CustomSelect
    // Find the dropdown button containing "Staff (Operational access)" (the default selected option)
    const roleSelectButton = screen.getAllByRole('button', { name: /Staff \(Operational access\)/i })[0]
    expect(roleSelectButton).toHaveAttribute('aria-pressed', 'true')
    expect(screen.getByRole('button', { name: /Viewer \(Read-only\)/i })).toBeInTheDocument()
    
    // Check that ADMIN is NOT available
    expect(within(screen.getByRole('dialog')).queryByRole('button', { name: /^Admin$/i })).not.toBeInTheDocument()
    
    // Check no shop selector
    expect(screen.queryByLabelText(/Shop/i)).not.toBeInTheDocument()
  })

  it('Role change does not offer ADMIN', async () => {
    render(<BrowserRouter><UsersPage /></BrowserRouter>)
    await screen.findAllByText('Admin User') // Wait for data to load
    
    // Open action menu for a STAFF member
    const manageButtons = screen.getAllByTitle('Manage Member')
    fireEvent.click(manageButtons[0]) // Click first non-admin member's manage button

    // The "Demote to Viewer" action should exist
    expect(screen.getAllByText('Demote to Viewer').length).toBeGreaterThan(0)
    expect(screen.queryAllByText(/Promote to ADMIN/i).length).toBe(0)
  })
})
