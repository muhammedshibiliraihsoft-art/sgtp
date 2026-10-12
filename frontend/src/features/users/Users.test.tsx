import { afterEach, describe, it, expect, vi, beforeEach } from 'vitest'
import { act, cleanup, render, screen, fireEvent, waitFor } from '@testing-library/react'
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

vi.mock('./api', () => ({ usersApi: { memberships: vi.fn(), stats: vi.fn(), createUser: vi.fn(), resetPin: vi.fn(), setRole: vi.fn(), deactivate: vi.fn(), reactivate: vi.fn(), remove: vi.fn(), functions: vi.fn(), setFunctions: vi.fn(), findCreatedMembership: vi.fn() } }))
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
    user_id: 'u2',
    login_id: 'staff_user',
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

function deferred<T>() {
  let resolve!: (value: T) => void
  const promise = new Promise<T>(res => { resolve = res })
  return { promise, resolve }
}

describe('UsersPage', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    vi.mocked(usersApi.memberships).mockResolvedValue({ count: mockMembers.length, next: null, previous: null, results: mockMembers } as any)
    vi.mocked(usersApi.stats).mockResolvedValue(mockStats)
  })
  afterEach(() => cleanup())

  it('renders page and backend-aligned Membership fields', async () => {
    render(<BrowserRouter><UsersPage /></BrowserRouter>)
    await screen.findAllByText('Admin User') // Wait for data to load
    
    // Check fields
    expect(screen.getByText('Team')).toBeInTheDocument()
    expect(screen.queryByText('USR-1')).not.toBeInTheDocument()
    expect(screen.getAllByText('admin@test.com').length).toBeGreaterThan(0)
    
    expect(screen.getAllByText('Staff User').length).toBeGreaterThan(0)
    expect(screen.getAllByText('staff_user').length).toBeGreaterThan(0)
  })

  it('debounces membership search without reloading Shop stats and loads the full list when cleared', async () => {
    render(<BrowserRouter><UsersPage /></BrowserRouter>)
    await screen.findAllByText('Admin User')
    expect(usersApi.memberships).toHaveBeenCalledTimes(1)

    const search = screen.getAllByPlaceholderText('Search by name or User ID')[0]
    fireEvent.change(search, { target: { value: 'A' } })
    fireEvent.change(search, { target: { value: 'Adm' } })
    fireEvent.change(search, { target: { value: 'Admin' } })
    expect(usersApi.memberships).toHaveBeenCalledTimes(1)
    await waitFor(() => expect(usersApi.memberships).toHaveBeenLastCalledWith('t1', { search: 'Admin', role: 'ALL', active: 'ALL', page: 1 }))
    expect(usersApi.memberships).toHaveBeenCalledTimes(2)
    expect(usersApi.stats).toHaveBeenCalledTimes(1)

    fireEvent.change(search, { target: { value: '' } })
    await waitFor(() => expect(usersApi.memberships).toHaveBeenLastCalledWith('t1', { search: '', role: 'ALL', active: 'ALL', page: 1 }))
    expect(usersApi.memberships).toHaveBeenCalledTimes(3)
    expect(usersApi.stats).toHaveBeenCalledTimes(1)
  })

  it('keeps Shop stats independent of role filters and pagination', async () => {
    vi.mocked(usersApi.memberships).mockResolvedValue({ count: 40, next: null, previous: null, results: mockMembers } as any)
    render(<BrowserRouter><UsersPage /></BrowserRouter>)
    await screen.findAllByText('Admin User')
    fireEvent.click(screen.getAllByRole('button', { name: 'All Roles' })[0])
    fireEvent.click(screen.getAllByRole('option', { name: 'Staff' })[0])
    await waitFor(() => expect(usersApi.memberships).toHaveBeenLastCalledWith('t1', { search: '', role: 'STAFF', active: 'ALL', page: 1 }))
    fireEvent.click(document.querySelector('.pagination button:last-child')!)
    await waitFor(() => expect(usersApi.memberships).toHaveBeenLastCalledWith('t1', { search: '', role: 'STAFF', active: 'ALL', page: 2 }))
    expect(usersApi.stats).toHaveBeenCalledTimes(1)
  })

  it('keeps the member list usable and retries a failed capacity request', async () => {
    vi.mocked(usersApi.stats).mockRejectedValueOnce(new Error('Capacity service unavailable')).mockResolvedValueOnce(mockStats)
    render(<BrowserRouter><UsersPage /></BrowserRouter>)
    await screen.findAllByText('Admin User')
    expect(screen.getByRole('alert')).toHaveTextContent('Capacity service unavailable')
    expect(usersApi.memberships).toHaveBeenCalledTimes(1)
    fireEvent.click(screen.getByRole('button', { name: 'Retry' }))
    await waitFor(() => expect(screen.getByText('Users: 5 / 15')).toBeInTheDocument())
    expect(usersApi.stats).toHaveBeenCalledTimes(2)
  })

  it('ignores a stale membership response after a newer search is entered', async () => {
    const stale = deferred<Awaited<ReturnType<typeof usersApi.memberships>>>()
    const latest = deferred<Awaited<ReturnType<typeof usersApi.memberships>>>()
    vi.mocked(usersApi.memberships).mockImplementation((_shopId, options) => {
      if (options?.search === 'Old') return stale.promise
      if (options?.search === 'New') return latest.promise
      return Promise.resolve({ count: mockMembers.length, next: null, previous: null, results: mockMembers } as Awaited<ReturnType<typeof usersApi.memberships>>)
    })
    render(<BrowserRouter><UsersPage /></BrowserRouter>)
    await screen.findAllByText('Admin User')
    const search = screen.getAllByPlaceholderText('Search by name or User ID')[0]
    fireEvent.change(search, { target: { value: 'Old' } })
    await waitFor(() => expect(usersApi.memberships).toHaveBeenLastCalledWith('t1', { search: 'Old', role: 'ALL', active: 'ALL', page: 1 }))
    fireEvent.change(search, { target: { value: 'New' } })
    await waitFor(() => expect(usersApi.memberships).toHaveBeenLastCalledWith('t1', { search: 'New', role: 'ALL', active: 'ALL', page: 1 }))

    const latestMember = { ...mockMembers[0], id: 'latest', display_name: 'New result' }
    await act(async () => latest.resolve({ count: 1, next: null, previous: null, results: [latestMember] } as Awaited<ReturnType<typeof usersApi.memberships>>))
    expect(await screen.findAllByText('New result')).not.toHaveLength(0)
    const staleMember = { ...mockMembers[0], id: 'stale', display_name: 'Old result' }
    await act(async () => stale.resolve({ count: 1, next: null, previous: null, results: [staleMember] } as Awaited<ReturnType<typeof usersApi.memberships>>))
    expect(screen.queryByText('Old result')).not.toBeInTheDocument()
  })

  it('ignores a stale search error and loading completion after a newer result', async () => {
    let rejectStale!: (reason: Error) => void
    const stale = new Promise<Awaited<ReturnType<typeof usersApi.memberships>>>((_, reject) => { rejectStale = reject })
    const latest = deferred<Awaited<ReturnType<typeof usersApi.memberships>>>()
    vi.mocked(usersApi.memberships).mockImplementation((_shopId, options) => {
      if (options?.search === 'Old') return stale
      if (options?.search === 'New') return latest.promise
      return Promise.resolve({ count: mockMembers.length, next: null, previous: null, results: mockMembers } as Awaited<ReturnType<typeof usersApi.memberships>>)
    })
    render(<BrowserRouter><UsersPage /></BrowserRouter>)
    await screen.findAllByText('Admin User')
    const search = screen.getAllByPlaceholderText('Search by name or User ID')[0]
    fireEvent.change(search, { target: { value: 'Old' } })
    await waitFor(() => expect(usersApi.memberships).toHaveBeenLastCalledWith('t1', { search: 'Old', role: 'ALL', active: 'ALL', page: 1 }))
    fireEvent.change(search, { target: { value: 'New' } })
    await waitFor(() => expect(usersApi.memberships).toHaveBeenLastCalledWith('t1', { search: 'New', role: 'ALL', active: 'ALL', page: 1 }))

    const latestMember = { ...mockMembers[0], id: 'latest', display_name: 'New result' }
    await act(async () => latest.resolve({ count: 1, next: null, previous: null, results: [latestMember] } as Awaited<ReturnType<typeof usersApi.memberships>>))
    expect(await screen.findAllByText('New result')).not.toHaveLength(0)
    await act(async () => rejectStale(new Error('Stale search failed')))
    expect(screen.queryByRole('alert')).not.toBeInTheDocument()
    expect(screen.queryByText('Loading...')).not.toBeInTheDocument()
    expect(screen.getAllByText('New result')).not.toHaveLength(0)
  })

  it('Shop Admin Create User exposes STAFF/VIEWER only and no Shop selector', async () => {
    render(<BrowserRouter><UsersPage /></BrowserRouter>)
    await screen.findAllByText('Admin User') // Wait for data to load
    
    const addButton = screen.getAllByRole('button', { name: /Add user/i })[0]
    fireEvent.click(addButton)
    
    // Check roles using CustomSelect
    // Find the dropdown button containing "Staff (Operational access)" (the default selected option)
    const roleSelectButton = screen.getAllByRole('button', { name: /Staff \(Operational access\)/i })[0]
    fireEvent.click(roleSelectButton) // Open dropdown
    
    // Check that STAFF and VIEWER are available options
    expect(screen.getAllByRole('option', { name: /Staff \(Operational access\)/i }).length).toBeGreaterThan(0)
    expect(screen.getAllByRole('option', { name: /Viewer \(Read-only\)/i }).length).toBeGreaterThan(0)
    
    // Check that ADMIN is NOT available
    expect(screen.queryByRole('button', { name: /Admin/i })).not.toBeInTheDocument()
    
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

  it('resets only eligible member PIN and displays the one-time result', async () => {
    vi.mocked(usersApi.resetPin).mockResolvedValue({ login_id: 'staff_user', temporary_password: '048731' })
    render(<BrowserRouter><UsersPage /></BrowserRouter>)
    await screen.findAllByText('Staff User')
    fireEvent.click(screen.getAllByTitle('Manage Member')[0])
    fireEvent.click(screen.getByRole('button', { name: 'Reset PIN' }))
    expect(screen.getByText(/revokes existing sessions/)).toBeInTheDocument()
    fireEvent.click(screen.getAllByRole('button', { name: 'Reset PIN' })[0])
    await waitFor(() => expect(usersApi.resetPin).toHaveBeenCalledWith('u2'))
    expect(await screen.findByText('048731')).toBeInTheDocument()
  })

  it('keeps the one-time credentials visible when Work Function setup fails', async () => {
    vi.mocked(usersApi.createUser).mockResolvedValue({
      user_code: 'USR-3', login_id: 'new_staff', initial_password: '048731'
    } as any)
    vi.mocked(usersApi.findCreatedMembership).mockRejectedValue(new Error('Service unavailable'))
    render(<BrowserRouter><UsersPage /></BrowserRouter>)
    await screen.findAllByText('Admin User')
    fireEvent.click(screen.getAllByRole('button', { name: /Add user/i })[0])

    const dialog = screen.getByRole('heading', { name: 'Add Team Member' }).closest('[role="dialog"]')!
    const inputs = dialog.querySelectorAll('input')
    fireEvent.change(inputs[0], { target: { value: 'New Staff' } })
    fireEvent.change(inputs[2], { target: { value: 'new_staff' } })
    fireEvent.click(screen.getByRole('button', { name: 'Cutting' }))
    fireEvent.click(screen.getByRole('button', { name: 'Create User' }))

    expect(await screen.findByText('048731')).toBeInTheDocument()
    expect(await screen.findByRole('alert')).toHaveTextContent(/Work Functions were not assigned/)
    expect(usersApi.createUser).toHaveBeenCalledTimes(1)
  })
})
